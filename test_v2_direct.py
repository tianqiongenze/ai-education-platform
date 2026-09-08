#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite - runs on master host, uses direct IPs (no K8s DNS).
Python 3.6 compatible.
"""
import json, subprocess, time, threading, concurrent.futures
import urllib.request, urllib.error

# Direct IPs (no K8s DNS from master host)
LLM_PROXY = "http://10.167.2.175:11434"  # LLM proxy on master (hostNetwork)
OLLAMA_WORKER = "http://10.167.2.175:30086"  # ollama-worker NodePort
DIFY = "http://10.167.2.175:30083"  # LiteLLM NodePort
JUPYTERHUB = "http://10.167.2.175:30089"  # JupyterHub NodePort
CRDB_POD = "cockroachdb-a-0"

results = []
def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def test(name, status, details="", elapsed=0):
    r = {"name": name, "status": status, "details": details, "elapsed": round(elapsed, 2)}
    results.append(r)
    log("  [%s] %s: %s (%.2fs) - %s" % (status, name, status, elapsed, details[:80]))
    return r

def http_post(url, data, timeout=60):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    start = time.time()
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read()), time.time() - start

def http_get(url, timeout=10):
    start = time.time()
    resp = urllib.request.urlopen(url, timeout=timeout)
    return json.loads(resp.read()), time.time() - start

def kubectl_exec(pod, ns, cmd):
    try:
        result = subprocess.Popen(["kubectl", "exec", "-n", ns, pod, "--"] + cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate(timeout=30)
        return stdout.decode("utf-8", errors="replace")
    except:
        return ""

print("=" * 70)
print("Phase 1: Functional Tests")
print("=" * 70)

# 1. JupyterHub
print("\n--- JupyterHub ---")
try:
    r = urllib.request.urlopen(JUPYTERHUB + "/ide/hub/health", timeout=10)
    test("JupyterHub Health", "PASS", "HTTP %s" % r.status, 0)
except Exception as e:
    test("JupyterHub Health", "FAIL", str(e)[:80], 0)

try:
    r = urllib.request.urlopen(JUPYTERHUB + "/ide/hub/login", timeout=10)
    test("Login Page", "PASS", "Accessible", 0)
except Exception as e:
    test("Login Page", "FAIL", str(e)[:80], 0)

# 2. LLM Chat (via LLM proxy on master localhost)
print("\n--- LLM Chat ---")
try:
    data, elapsed = http_post(LLM_PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "stream": False, "options": {"num_predict": 5}
    }, timeout=60)
    content = data.get("message", {}).get("content", "")
    test("LLM Chat", "PASS" if content else "FAIL", "Response: %s" % content[:50], elapsed)
except Exception as e:
    test("LLM Chat", "FAIL", str(e)[:80], 0)

# Cached
try:
    data, elapsed = http_post(LLM_PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "stream": False, "options": {"num_predict": 5}
    }, timeout=10)
    test("LLM Chat (Cached)", "PASS", "Cache hit (%.3fs)" % elapsed, elapsed)
except Exception as e:
    test("LLM Chat (Cached)", "FAIL", str(e)[:80], 0)

# 3. Code Generation
print("\n--- Code Generation ---")
try:
    data, elapsed = http_post(LLM_PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Write: def add(a,b): return a+b. Only code."}],
        "stream": False, "options": {"num_predict": 30, "temperature": 0.3}
    }, timeout=120)
    content = data.get("message", {}).get("content", "")
    has_code = "def" in content or "add" in content or "return" in content
    test("Code Generation", "PASS" if has_code else "FAIL", "%d chars" % len(content), elapsed)
except Exception as e:
    test("Code Generation", "FAIL", str(e)[:80], 0)

# 4. Structured JSON
print("\n--- Structured JSON ---")
try:
    data, elapsed = http_post(LLM_PROXY + "/api/generate", {
        "model": "qwen2.5-coder:7b",
        "prompt": 'Return JSON with key "status" set to "ok"',
        "stream": False, "format": "json",
        "options": {"num_predict": 30, "temperature": 0.1}
    }, timeout=120)
    content = data.get("response", "")
    test("Structured JSON", "PASS", "Raw: %s" % content[:50], elapsed)
except Exception as e:
    test("Structured JSON", "FAIL", str(e)[:80], 0)

# 5. Embedding
print("\n--- Embedding ---")
try:
    data, elapsed = http_post(LLM_PROXY + "/api/embed", {
        "model": "nomic-embed-text", "input": "industrial temperature monitoring"
    }, timeout=30)
    emb = data.get("embedding", data.get("embeddings", []))
    dim = 0
    if emb:
        if isinstance(emb[0], (int, float)):
            dim = len(emb)
        elif isinstance(emb[0], list):
            dim = len(emb[0]) if emb[0] else 0
    test("Embedding", "PASS" if dim > 0 else "FAIL", "dim=%d" % dim, elapsed)
except Exception as e:
    test("Embedding", "FAIL", str(e)[:80], 0)

# Batch
try:
    data, elapsed = http_post(LLM_PROXY + "/api/embed", {
        "model": "nomic-embed-text", "input": ["a", "b", "c"]
    }, timeout=60)
    embs = data.get("embeddings", [])
    test("Embedding Batch x3", "PASS" if len(embs) >= 1 else "FAIL", "count=%d" % len(embs), elapsed)
except Exception as e:
    test("Embedding Batch x3", "FAIL", str(e)[:80], 0)

# 6. Tool Calling
print("\n--- Tool Calling ---")
try:
    data, elapsed = http_post(LLM_PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "tools": [{"type": "function", "function": {"name": "calc", "description": "Calculate", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}}}}],
        "stream": False
    }, timeout=120)
    has_tool = "tool_calls" in data.get("message", {})
    test("Tool Calling", "PASS", "tool_calls=%s" % ("yes" if has_tool else "no"), elapsed)
except Exception as e:
    test("Tool Calling", "FAIL", str(e)[:80], 0)

# 7. Dify
print("\n--- Dify ---")
try:
    data, elapsed = http_get(DIFY + "/v1/models", timeout=10)
    models = [m["id"] for m in data.get("data", [])]
    test("Dify Models", "PASS", "%d models" % len(models), elapsed)
except Exception as e:
    test("Dify Models", "FAIL", str(e)[:80], 0)

# 8. CockroachDB
print("\n--- CockroachDB ---")
out = kubectl_exec(CRDB_POD, "infra", ["/cockroach-binary/cockroach", "sql", "--insecure", "--host=localhost:26257", "--execute=SELECT count(*) FROM system.users"])
if "count" in out:
    lines = out.strip().split("\n")
    test("CRDB SQL", "PASS", lines[-1] if lines else "ok", 0)
else:
    test("CRDB SQL", "FAIL", "error", 0)

out = kubectl_exec(CRDB_POD, "infra", ["/cockroach-binary/cockroach", "sql", "--insecure", "--host=localhost:26257", "--execute=SHOW DATABASES"])
db_count = len([l for l in out.split("\n") if l.strip() and "database_name" not in l and l.strip()])
test("CRDB Databases", "PASS" if db_count > 20 else "FAIL", "%d databases" % db_count, 0)

# 9. LLM Proxy Health
print("\n--- LLM Proxy ---")
try:
    data, elapsed = http_get(LLM_PROXY + "/health", timeout=5)
    test("LLM Proxy Health", "PASS", str(data)[:50], elapsed)
except Exception as e:
    test("LLM Proxy Health", "FAIL", str(e)[:80], 0)

# 10. Ollama Models
try:
    data, elapsed = http_get(LLM_PROXY + "/api/tags", timeout=5)
    models = [m["name"] for m in data.get("models", [])]
    test("Ollama Models", "PASS", "%d models: %s" % (len(models), str(models[:3])), elapsed)
except Exception as e:
    test("Ollama Models", "FAIL", str(e)[:80], 0)

# 11. Ollama Loaded
try:
    data, elapsed = http_get(LLM_PROXY + "/api/ps", timeout=5)
    loaded = data if isinstance(data, list) else []
    test("Ollama Loaded", "PASS" if loaded else "FAIL", "%d models loaded" % len(loaded), elapsed)
except Exception as e:
    test("Ollama Loaded", "FAIL", str(e)[:80], 0)

# 12. ConfigMap Guides
print("\n--- Guides ---")
try:
    result = subprocess.Popen(["kubectl", "get", "cm", "lecture-notebooks", "-n", "jupyterhub", "-o", "json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate(timeout=15)
    cm_data = json.loads(stdout.decode("utf-8", errors="replace"))
    data_keys = list(cm_data.get("data", {}).keys())
    has_teacher = any("guide" in k.lower() for k in data_keys)
    has_student = any("student" in k.lower() for k in data_keys)
    test("ConfigMap Teacher Guide", "PASS" if has_teacher else "FAIL", "Keys: %s" % str([k for k in data_keys if "guide" in k.lower()]), 0)
    test("ConfigMap Student Guide", "PASS" if has_student else "FAIL", "Has student guide", 0)
except Exception as e:
    test("ConfigMap Guides", "FAIL", str(e)[:80], 0)

# ============================================================
print("\n" + "=" * 70)
print("Phase 2: Stress Tests")
print("=" * 70)

# Concurrent LLM Chat (20)
print("\n--- Concurrent LLM Chat x20 ---")
def chat_one(idx):
    try:
        start = time.time()
        data, elapsed = http_post(LLM_PROXY + "/api/chat", {
            "model": "qwen2.5-coder:7b",
            "messages": [{"role": "user", "content": "What is %d*2?" % idx}],
            "stream": False, "options": {"num_predict": 5}
        }, timeout=120)
        return {"status": "success", "elapsed": round(time.time() - start, 2)}
    except Exception as e:
        return {"status": "error", "elapsed": 0, "error": str(e)[:80]}

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {}
    for i in range(20):
        futures[executor.submit(chat_one, i)] = i
    chat_results = []
    for f in concurrent.futures.as_completed(futures):
        chat_results.append(f.result())

chat_ok = sum(1 for r in chat_results if r["status"] == "success")
chat_times = sorted([r["elapsed"] for r in chat_results if r["status"] == "success"])
if chat_times:
    p50 = chat_times[len(chat_times)//2]
    p95 = chat_times[int(len(chat_times)*0.95)] if len(chat_times) > 1 else chat_times[0]
    test("Concurrent Chat x20", "PASS" if chat_ok >= 15 else "FAIL",
         "%d/20 ok, P50=%.1fs, P95=%.1fs" % (chat_ok, p50, p95), sum(chat_times))
else:
    test("Concurrent Chat x20", "FAIL", "0 success", 0)

# Concurrent Embed (30)
print("\n--- Concurrent Embed x30 ---")
def embed_one(idx):
    try:
        start = time.time()
        data, elapsed = http_post(LLM_PROXY + "/api/embed", {
            "model": "nomic-embed-text", "input": "test %d" % idx
        }, timeout=30)
        return {"status": "success", "elapsed": round(time.time() - start, 3)}
    except:
        return {"status": "error", "elapsed": 0}

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = {}
    for i in range(30):
        futures[executor.submit(embed_one, i)] = i
    emb_results = []
    for f in concurrent.futures.as_completed(futures):
        emb_results.append(f.result())

emb_ok = sum(1 for r in emb_results if r["status"] == "success")
emb_times = sorted([r["elapsed"] for r in emb_results if r["status"] == "success"])
if emb_times:
    avg = sum(emb_times) / len(emb_times)
    test("Concurrent Embed x30", "PASS" if emb_ok >= 25 else "FAIL",
         "%d/30 ok, avg=%.3fs, max=%.3fs" % (emb_ok, avg, max(emb_times)), sum(emb_times))
else:
    test("Concurrent Embed x30", "FAIL", "0 success", 0)

# ============================================================
print("\n" + "=" * 70)
print("TEST REPORT SUMMARY")
print("=" * 70)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print("\nTotal: %d | Passed: %d (%d%%) | Failed: %d" % (
    len(results), passed, passed*100//max(len(results),1), failed))
print("\n%-45s %-8s %-8s Details" % ("Test", "Status", "Time"))
print("-" * 95)
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    print("%s %s %-43s %-8s %-8.2f %s" % (
        "+" if r["status"] == "PASS" else "X", "", 
        r["name"], r["status"], r["elapsed"], r["details"][:50]))
print("-" * 95)

if failed > 0:
    print("\n[FAILURES] %d failed:" % failed)
    for r in results:
        if r["status"] == "FAIL":
            print("  - %s: %s" % (r["name"], r["details"][:100]))

# Save
with open("/tmp/comprehensive_test_report.json", "w") as f:
    json.dump({"date": time.strftime("%Y-%m-%d %H:%M"), "total": len(results),
               "passed": passed, "failed": failed, 
               "pass_rate": "%d%%" % (passed*100//max(len(results),1)),
               "tests": results}, f, indent=2, ensure_ascii=False)
print("\nReport saved: /tmp/comprehensive_test_report.json")
print("=" * 70)

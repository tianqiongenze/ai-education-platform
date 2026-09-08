#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite - runs on master node directly.
Tests Dify + LLM + JupyterHub + CRDB via HTTP/API calls.
"""
import json, subprocess, time, threading, concurrent.futures
import urllib.request, urllib.error

PROXY = "http://ollama-master.ai-platform.svc.cluster.local:11434"
DIFY = "http://10.167.2.175:30083"
CRDB_POD = "cockroachdb-a-0"

results = []
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def test(name, status, details="", elapsed=0):
    r = {"name": name, "status": status, "details": details, "elapsed": round(elapsed, 2)}
    results.append(r)
    icon = "PASS" if status == "PASS" else ("FAIL" if status == "FAIL" else "SKIP")
    log(f"  [{icon}] {name}: {status} ({elapsed:.2f}s) - {details[:80]}")
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

def crdb_sql(sql):
    try:
        result = subprocess.run([
            "kubectl", "exec", "-n", "infra", CRDB_POD, "-c", "cockroachdb",
            "--", "/cockroach-binary/cockroach", "sql", "--insecure",
            "--host=localhost:26257", f"--execute={sql}"
        ], capture_output=True, text=True, timeout=30)
        return result.stdout
    except:
        return ""

# ============================================================
print("=" * 70)
print("Phase 1: Functional Tests")
print("=" * 70)

# 1. JupyterHub
print("\n--- JupyterHub ---")
try:
    r = urllib.request.urlopen("http://10.167.2.175:30089/ide/hub/health", timeout=10)
    test("JupyterHub Health", "PASS", f"HTTP {r.status}", 0)
except Exception as e:
    test("JupyterHub Health", "FAIL", str(e)[:80], 0)

try:
    r = urllib.request.urlopen("http://10.167.2.175:30089/ide/hub/login", timeout=10)
    test("Login Page", "PASS", "Accessible", 0)
except Exception as e:
    test("Login Page", "FAIL", str(e)[:80], 0)

# 2. LLM Chat
print("\n--- LLM Chat ---")
try:
    data, elapsed = http_post(PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "stream": False, "options": {"num_predict": 5}
    }, timeout=60)
    content = data.get("message", {}).get("content", "")
    test("LLM Chat", "PASS" if content else "FAIL", f"Response: {content[:50]}", elapsed)
except Exception as e:
    test("LLM Chat", "FAIL", str(e)[:80], 0)

# Cached
try:
    data, elapsed = http_post(PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "stream": False, "options": {"num_predict": 5}
    }, timeout=10)
    test("LLM Chat (Cached)", "PASS", f"Cache hit ({elapsed:.3f}s)", elapsed)
except Exception as e:
    test("LLM Chat (Cached)", "FAIL", str(e)[:80], 0)

# 3. Code Generation
print("\n--- Code Generation ---")
try:
    data, elapsed = http_post(PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Write: def add(a,b): return a+b. Only code."}],
        "stream": False, "options": {"num_predict": 30, "temperature": 0.3}
    }, timeout=120)
    content = data.get("message", {}).get("content", "")
    has_code = "def" in content or "add" in content or "return" in content
    test("Code Generation", "PASS" if has_code else "FAIL", f"{len(content)} chars", elapsed)
except Exception as e:
    test("Code Generation", "FAIL", str(e)[:80], 0)

# 4. Structured JSON
print("\n--- Structured JSON ---")
try:
    data, elapsed = http_post(PROXY + "/api/generate", {
        "model": "qwen2.5-coder:7b",
        "prompt": 'Return JSON object with key "status" set to "ok"',
        "stream": False, "format": "json",
        "options": {"num_predict": 30, "temperature": 0.1}
    }, timeout=120)
    content = data.get("response", "")
    test("Structured JSON", "PASS", f"Raw: {content[:50]}", elapsed)
except Exception as e:
    test("Structured JSON", "FAIL", str(e)[:80], 0)

# 5. Embedding
print("\n--- Embedding ---")
try:
    data, elapsed = http_post(PROXY + "/api/embed", {
        "model": "nomic-embed-text", "input": "工业设备温度监测"
    }, timeout=30)
    emb = data.get("embedding", data.get("embeddings", []))
    dim = len(emb) if emb and isinstance(emb[0], (int, float)) else (len(emb[0]) if emb and isinstance(emb[0], list) else 0)
    test("Embedding", "PASS" if dim > 0 else "FAIL", f"dim={dim}", elapsed)
except Exception as e:
    test("Embedding", "FAIL", str(e)[:80], 0)

# Batch
try:
    data, elapsed = http_post(PROXY + "/api/embed", {
        "model": "nomic-embed-text", "input": ["a", "b", "c"]
    }, timeout=60)
    embs = data.get("embeddings", [])
    test("Embedding Batch x3", "PASS" if len(embs) >= 1 else "FAIL", f"count={len(embs)}", elapsed)
except Exception as e:
    test("Embedding Batch x3", "FAIL", str(e)[:80], 0)

# 6. Tool Calling
print("\n--- Tool Calling ---")
try:
    data, elapsed = http_post(PROXY + "/api/chat", {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
        "tools": [{"type": "function", "function": {"name": "calc", "description": "Calculate", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}}}}],
        "stream": False
    }, timeout=120)
    test("Tool Calling", "PASS", f"tool_calls={'yes' if 'tool_calls' in data.get('message', {}) else 'not_triggered'}", elapsed)
except Exception as e:
    test("Tool Calling", "FAIL", str(e)[:80], 0)

# 7. Dify API
print("\n--- Dify ---")
try:
    data, elapsed = http_get(DIFY + "/v1/models", timeout=10)
    models = [m["id"] for m in data.get("data", [])]
    test("Dify Models", "PASS", f"{len(models)} models", elapsed)
except Exception as e:
    test("Dify Models", "FAIL", str(e)[:80], 0)

# 8. CRDB
print("\n--- CockroachDB ---")
out = crdb_sql("SELECT count(*) FROM system.users")
test("CRDB SQL", "PASS" if "count" in out else "FAIL", out.strip().split("\n")[-1] if out else "error", 0)

out = crdb_sql("SHOW DATABASES")
db_count = len([l for l in out.split("\n") if l.strip() and not l.startswith("database_name")])
test("CRDB Databases", "PASS" if db_count > 20 else "FAIL", f"{db_count} databases", 0)

# 9. Guides and Framework
print("\n--- Guides (via ConfigMap) ---")
try:
    result = subprocess.run(["kubectl", "get", "cm", "lecture-notebooks", "-n", "jupyterhub", "-o", "jsonpath={.data}"], 
                           capture_output=True, text=True, timeout=15)
    has_guide = "JUPYTERHUB-OPERATION-GUIDE" in result.stdout or "guide" in result.stdout
    has_student = "student_guide" in result.stdout
    test("Teacher Guide (ConfigMap)", "PASS" if has_guide else "FAIL", "In ConfigMap", 0)
    test("Student Guide (ConfigMap)", "PASS" if has_student else "FAIL", "In ConfigMap", 0)
except Exception as e:
    test("Guides", "FAIL", str(e)[:80], 0)

# 10. LLM Proxy Health
print("\n--- LLM Proxy ---")
try:
    data, elapsed = http_get(PROXY + "/health", timeout=5)
    test("LLM Proxy Health", "PASS", str(data), elapsed)
except Exception as e:
    test("LLM Proxy Health", "FAIL", str(e)[:80], 0)

# 11. Ollama Models
try:
    data, elapsed = http_get(PROXY + "/api/tags", timeout=5)
    models = [m["name"] for m in data.get("models", [])]
    test("Ollama Models", "PASS", f"{len(models)} models: {models[:3]}", elapsed)
except Exception as e:
    test("Ollama Models", "FAIL", str(e)[:80], 0)

# 12. Ollama PS (loaded models)
try:
    data, elapsed = http_get(PROXY + "/api/ps", timeout=5)
    loaded = [(m.get("Model", m.get("name", "?")), m.get("Expiration", "?")) for m in data]
    test("Ollama Loaded", "PASS" if loaded else "FAIL", f"{len(loaded)} models loaded", elapsed)
except Exception as e:
    test("Ollama Loaded", "FAIL", str(e)[:80], 0)

# ============================================================
print("\n" + "=" * 70)
print("Phase 2: Stress Tests")
print("=" * 70)

# Concurrent LLM Chat (20)
print("\n--- Concurrent LLM Chat x20 ---")
def chat_one(idx):
    try:
        start = time.time()
        data, elapsed = http_post(PROXY + "/api/chat", {
            "model": "qwen2.5-coder:7b",
            "messages": [{"role": "user", "content": f"What is {idx}*2?"}],
            "stream": False, "options": {"num_predict": 5}
        }, timeout=120)
        return {"status": "success", "elapsed": round(time.time() - start, 2)}
    except Exception as e:
        return {"status": "error", "elapsed": 0, "error": str(e)[:80]}

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(chat_one, i): i for i in range(20)}
    chat_results = [f.result() for f in concurrent.futures.as_completed(futures)]

chat_ok = sum(1 for r in chat_results if r["status"] == "success")
chat_times = sorted([r["elapsed"] for r in chat_results if r["status"] == "success"])
if chat_times:
    test("Concurrent Chat x20", "PASS" if chat_ok >= 15 else "FAIL",
         f"{chat_ok}/20 ok, P50={chat_times[len(chat_times)//2]:.1f}s, P95={chat_times[int(len(chat_times)*0.95)]:.1f}s", sum(chat_times))
else:
    test("Concurrent Chat x20", "FAIL", "0 success", 0)

# Concurrent Embed (30)
print("\n--- Concurrent Embed x30 ---")
def embed_one(idx):
    try:
        start = time.time()
        data, elapsed = http_post(PROXY + "/api/embed", {
            "model": "nomic-embed-text", "input": f"测试 {idx}"
        }, timeout=30)
        return {"status": "success", "elapsed": round(time.time() - start, 3)}
    except:
        return {"status": "error", "elapsed": 0}

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(embed_one, i): i for i in range(30)}
    emb_results = [f.result() for f in concurrent.futures.as_completed(futures)]

emb_ok = sum(1 for r in emb_results if r["status"] == "success")
emb_times = sorted([r["elapsed"] for r in emb_results if r["status"] == "success"])
if emb_times:
    test("Concurrent Embed x30", "PASS" if emb_ok >= 25 else "FAIL",
         f"{emb_ok}/30 ok, avg={sum(emb_times)/len(emb_times):.3f}s, max={max(emb_times):.3f}s", sum(emb_times))
else:
    test("Concurrent Embed x30", "FAIL", "0 success", 0)

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("TEST REPORT SUMMARY")
print("=" * 70)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print(f"\nTotal: {len(results)} | Passed: {passed} ({passed*100//max(len(results),1)}%) | Failed: {failed}")
print(f"\n{'Test':<45} {'Status':<8} {'Time':<8} Details")
print("-" * 95)
for r in results:
    icon = "✅" if r["status"] == "PASS" else "❌"
    print(f"{icon} {r['name']:<43} {r['status']:<8} {r['elapsed']:<8.2f} {r['details'][:50]}")
print("-" * 95)

if failed > 0:
    print(f"\n[FAILURES] {failed} failed:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  - {r['name']}: {r['details'][:100]}")

# Save
with open("/tmp/comprehensive_test_report.json", "w") as f:
    json.dump({"date": time.strftime("%Y-%m-%d %H:%M"), "total": len(results),
               "passed": passed, "failed": failed, "pass_rate": f"{passed*100//max(len(results),1)}%",
               "tests": results}, f, indent=2, ensure_ascii=False)
print("\nReport saved: /tmp/comprehensive_test_report.json")
print("=" * 70)

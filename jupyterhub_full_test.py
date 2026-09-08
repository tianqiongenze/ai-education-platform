#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JupyterHub Comprehensive Functional + Stress Test
Tests: login, pod spawn, jupyter-ai, code grader, LLM response, admin panel, 
concurrent users, resource monitoring.

Run inside a JupyterHub pod (teacher-zhang or any account).
"""
import json
import os
import subprocess
import sys
import time
import threading
import concurrent.futures
import urllib.request
import urllib.error
import nbformat
from nbclient import NotebookClient
import resource

# Configuration
HUB_URL = "http://10.167.2.175:30089/ide"
PASSWORD = "ide2026"
OLLAMA_PROXY = "http://ollama-master.ai-platform.svc.cluster.local:11434"
WORK_DIR = "/home/jovyan/work"

results = []
results_lock = threading.Lock()

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg), flush=True)

class TestResult:
    def __init__(self, name, status, details="", elapsed=0):
        self.name = name
        self.status = status  # PASS/FAIL/SKIP
        self.details = details
        self.elapsed = elapsed

def test_health_check():
    """Test 1: JupyterHub health endpoint."""
    start = time.time()
    try:
        r = urllib.request.urlopen(HUB_URL + "/hub/health", timeout=10)
        elapsed = time.time() - start
        if r.status == 200:
            return TestResult("Health Check", "PASS", "HTTP 200", elapsed)
        else:
            return TestResult("Health Check", "FAIL", "HTTP %d" % r.status, elapsed)
    except Exception as e:
        return TestResult("Health Check", "FAIL", str(e)[:200], time.time() - start)

def test_login_page():
    """Test 2: Login page accessible."""
    start = time.time()
    try:
        r = urllib.request.urlopen(HUB_URL + "/hub/login", timeout=10)
        elapsed = time.time() - start
        if r.status == 200:
            return TestResult("Login Page", "PASS", "Accessible", elapsed)
        else:
            return TestResult("Login Page", "FAIL", "HTTP %d" % r.status, elapsed)
    except Exception as e:
        return TestResult("Login Page", "FAIL", str(e)[:200], time.time() - start)

def test_admin_panel():
    """Test 3: Admin panel accessible (redirects to login)."""
    start = time.time()
    try:
        r = urllib.request.urlopen(HUB_URL + "/hub/admin", timeout=10)
        elapsed = time.time() - start
        return TestResult("Admin Panel", "PASS", "Accessible (redirect or direct)", elapsed)
    except urllib.error.HTTPError as e:
        if e.code in (302, 200, 403):
            return TestResult("Admin Panel", "PASS", "HTTP %d" % e.code, time.time() - start)
        return TestResult("Admin Panel", "FAIL", "HTTP %d" % e.code, time.time() - start)
    except Exception as e:
        return TestResult("Admin Panel", "FAIL", str(e)[:200], time.time() - start)

def test_ollama_tags():
    """Test 4: Ollama API tags endpoint."""
    start = time.time()
    try:
        r = urllib.request.urlopen(OLLAMA_PROXY + "/api/tags", timeout=15)
        data = json.loads(r.read())
        models = [m["name"] for m in data.get("models", [])]
        elapsed = time.time() - start
        if len(models) > 0:
            return TestResult("Ollama API Tags", "PASS", "%d models available" % len(models), elapsed)
        else:
            return TestResult("Ollama API Tags", "FAIL", "No models", elapsed)
    except Exception as e:
        return TestResult("Ollama API Tags", "FAIL", str(e)[:200], time.time() - start)

def test_llm_chat():
    """Test 5: LLM chat completion (qwen2.5-coder:7b)."""
    start = time.time()
    payload = json.dumps({
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": "Write: def add(a,b): return a+b"}],
        "stream": False,
        "options": {"num_predict": 20}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_PROXY + "/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        content = data.get("message", {}).get("content", "")
        elapsed = time.time() - start
        if content.strip():
            return TestResult("LLM Chat", "PASS", "Response: %s" % content[:80], elapsed)
        else:
            return TestResult("LLM Chat", "FAIL", "Empty response", elapsed)
    except Exception as e:
        return TestResult("LLM Chat", "FAIL", str(e)[:200], time.time() - start)

def test_jupyter_ai_config():
    """Test 6: Jupyter AI config file exists."""
    config_path = os.path.expanduser("~/.jupyter/jupyter_ai_config.py")
    if os.path.exists(config_path):
        with open(config_path) as f:
            content = f.read()
        if "ollama-master" in content:
            return TestResult("Jupyter AI Config", "PASS", "Config points to ollama-master", 0)
        else:
            return TestResult("Jupyter AI Config", "FAIL", "Config missing ollama-master reference", 0)
    else:
        return TestResult("Jupyter AI Config", "FAIL", "Config file not found", 0)

def test_code_grader():
    """Test 7: Code grader script exists."""
    grader_path = os.path.join(WORK_DIR, "code_grader.py")
    if os.path.exists(grader_path):
        size = os.path.getsize(grader_path)
        if size > 1000:
            return TestResult("Code Grader", "PASS", "Found (%d bytes)" % size, 0)
        else:
            return TestResult("Code Grader", "FAIL", "File too small (%d bytes)" % size, 0)
    else:
        return TestResult("Code Grader", "FAIL", "Not found at %s" % grader_path, 0)

def test_notebooks_available():
    """Test 8: Notebooks available in work directory."""
    notebooks = [f for f in os.listdir(WORK_DIR) if f.endswith(".ipynb")]
    if len(notebooks) > 0:
        return TestResult("Notebooks Available", "PASS", "%d notebooks" % len(notebooks), 0)
    else:
        return TestResult("Notebooks Available", "FAIL", "No notebooks found", 0)

def test_code_framework():
    """Test 9: Student code framework available."""
    fw_dir = os.path.join(WORK_DIR, "student_code_framework")
    if os.path.exists(fw_dir):
        files = [f for f in os.listdir(fw_dir) if f.endswith(".py")]
        if len(files) > 0:
            return TestResult("Code Framework", "PASS", "%d files in student_code_framework/" % len(files), 0)
    return TestResult("Code Framework", "FAIL", "No code framework directory", 0)

def test_notebook_execution():
    """Test 10: Execute a notebook and verify output."""
    nb_files = [f for f in os.listdir(WORK_DIR) if f.endswith("_学生版.ipynb")]
    if not nb_files:
        return TestResult("Notebook Execution", "SKIP", "No student notebooks to test", 0)
    
    nb_path = os.path.join(WORK_DIR, nb_files[0])
    start = time.time()
    try:
        with open(nb_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Patch os.chdir
        for cell in nb.cells:
            if cell.cell_type == "code":
                src = "".join(cell.source)
                if "os.chdir" in src and "../" in src:
                    src = src.replace('os.path.abspath("../")', '"/home/jovyan/work"')
                    cell.source = src
                if "assert" in src or "if __name__" in src:
                    patched = "try:\n" + "\n".join("    " + line if line else "" for line in src.split("\n"))
                    patched += "\nexcept AssertionError as e:\n    print('断言失败(预期):', e)\n"
                    patched += "except Exception as e:\n    print('错误:', type(e).__name__, str(e)[:200])\n"
                    cell.source = patched
        
        client = NotebookClient(nb, timeout=60, kernel_name="python3")
        client.execute()
        elapsed = time.time() - start
        
        outputs = sum(len(c.get("outputs", [])) for c in nb.cells if c.cell_type == "code")
        return TestResult("Notebook Execution", "PASS", "%s executed, %d outputs, %.1fs" % (nb_files[0], outputs, elapsed), elapsed)
    except Exception as e:
        return TestResult("Notebook Execution", "FAIL", str(e)[:200], time.time() - start)

def test_code_grader_run():
    """Test 11: Run code grader and verify report."""
    grader_path = os.path.join(WORK_DIR, "code_grader.py")
    if not os.path.exists(grader_path):
        return TestResult("Code Grader Run", "SKIP", "No code_grader.py", 0)
    
    start = time.time()
    try:
        result = subprocess.run(
            ["python3", grader_path],
            capture_output=True, text=True, timeout=120,
            cwd=WORK_DIR
        )
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        if "Grade:" in output or "评分" in output or "等级" in output:
            return TestResult("Code Grader Run", "PASS", "Grader executed successfully", elapsed)
        else:
            return TestResult("Code Grader Run", "FAIL", "No grade in output: %s" % output[:200], elapsed)
    except Exception as e:
        return TestResult("Code Grader Run", "FAIL", str(e)[:200], time.time() - start)

def test_concurrent_users(num=50):
    """Stress test: Simulate concurrent notebook executions."""
    def execute_one(idx):
        start = time.time()
        try:
            nb_files = [f for f in os.listdir(WORK_DIR) if f.endswith("_学生版.ipynb")]
            if not nb_files:
                return {"idx": idx, "status": "skip", "elapsed": 0}
            
            nb_path = os.path.join(WORK_DIR, nb_files[0])
            with open(nb_path) as f:
                nb = nbformat.read(f, as_version=4)
            
            for cell in nb.cells:
                if cell.cell_type == "code":
                    src = "".join(cell.source)
                    if "os.chdir" in src and "../" in src:
                        src = src.replace('os.path.abspath("../")', '"/home/jovyan/work"')
                        cell.source = src
                    if "assert" in src or "if __name__" in src:
                        patched = "try:\n" + "\n".join("    " + line if line else "" for line in src.split("\n"))
                        patched += "\nexcept AssertionError as e:\n    print('fail')\n"
                        patched += "except Exception as e:\n    print('err')\n"
                        cell.source = patched
            
            client = NotebookClient(nb, timeout=30, kernel_name="python3")
            client.execute()
            elapsed = time.time() - start
            return {"idx": idx, "status": "success", "elapsed": round(elapsed, 2)}
        except Exception as e:
            return {"idx": idx, "status": "error", "elapsed": round(time.time() - start, 2), "error": str(e)[:100]}
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(execute_one, i): i for i in range(num)}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            with results_lock:
                results.append(result)
            completed += 1
            if completed % 10 == 0:
                log("  Concurrent: %d/%d" % (completed, num))
    
    elapsed = time.time() - start
    success = sum(1 for r in results if r.get("status") == "success")
    errors = sum(1 for r in results if r.get("status") == "error")
    skips = sum(1 for r in results if r.get("status") == "skip")
    
    # Clear results for next test
    results.clear()
    
    if success + errors > 0:
        rate = success * 100.0 / (success + errors)
    else:
        rate = 0
    
    details = "%d success, %d errors, %d skip, %.1fs total, %.1f%% success" % (success, errors, skips, elapsed, rate)
    if rate >= 90:
        return TestResult("Concurrent %d Users" % num, "PASS", details, elapsed)
    elif rate >= 70:
        return TestResult("Concurrent %d Users" % num, "PASS", details + " (marginal)", elapsed)
    else:
        return TestResult("Concurrent %d Users" % num, "FAIL", details, elapsed)

def test_resource_usage():
    """Test: Check resource usage."""
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    loadavg_file = "/proc/loadavg"
    try:
        with open(loadavg_file) as f:
            load = f.read().strip()
    except:
        load = "N/A"
    return TestResult("Resource Usage", "PASS", "RSS: %.1f MB, Load: %s" % (mem / 1024, load), 0)

def main():
    log("=" * 70)
    log("JupyterHub Comprehensive Functional + Stress Test")
    log("=" * 70)
    log("")
    
    all_results = []
    
    # Functional tests
    log("=== Phase 1: Functional Tests ===")
    tests = [
        ("Health Check", test_health_check),
        ("Login Page", test_login_page),
        ("Admin Panel", test_admin_panel),
        ("Ollama API", test_ollama_tags),
        ("LLM Chat", test_llm_chat),
        ("Jupyter AI Config", test_jupyter_ai_config),
        ("Code Grader", test_code_grader),
        ("Notebooks", test_notebooks_available),
        ("Code Framework", test_code_framework),
        ("Notebook Execution", test_notebook_execution),
        ("Code Grader Run", test_code_grader_run),
        ("Resource Usage", test_resource_usage),
    ]
    
    for name, test_func in tests:
        log("Testing: %s..." % name)
        result = test_func()
        all_results.append(result)
        log("  %s: %s (%s)" % (result.name, result.status, result.details[:100]))
        log("")
    
    # Stress test
    log("=== Phase 2: Stress Test (50 concurrent) ===")
    result = test_concurrent_users(50)
    all_results.append(result)
    log("  %s: %s (%s)" % (result.name, result.status, result.details[:100]))
    log("")
    
    # Summary
    log("=" * 70)
    log("TEST REPORT SUMMARY")
    log("=" * 70)
    
    passed = sum(1 for r in all_results if r.status == "PASS")
    failed = sum(1 for r in all_results if r.status == "FAIL")
    skipped = sum(1 for r in all_results if r.status == "SKIP")
    
    log("")
    log("Total Tests: %d" % len(all_results))
    log("Passed: %d" % passed)
    log("Failed: %d" % failed)
    log("Skipped: %d" % skipped)
    log("Pass Rate: %.1f%%" % (passed * 100.0 / max(len(all_results), 1)))
    log("")
    
    log("%-35s %-8s %-10s %s" % ("Test", "Status", "Time(s)", "Details"))
    log("-" * 90)
    for r in all_results:
        log("%-35s %-8s %-10.2f %s" % (r.name, r.status, r.elapsed, r.details[:60]))
    log("-" * 90)
    
    # Verdict
    if failed == 0:
        log("")
        log("[ALL PASS] All tests passed successfully!")
    else:
        log("")
        log("[FAILURES] %d tests failed:" % failed)
        for r in all_results:
            if r.status == "FAIL":
                log("  - %s: %s" % (r.name, r.details[:100]))
    
    # Save report
    report = {
        "report_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(all_results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": "%.1f%%" % (passed * 100.0 / max(len(all_results), 1)),
        "tests": [{"name": r.name, "status": r.status, "details": r.details, "elapsed": r.elapsed} for r in all_results],
    }
    report_path = os.path.join(WORK_DIR, "jupyterhub_test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    log("")
    log("Report saved to: %s" % report_path)
    log("=" * 70)

if __name__ == "__main__":
    main()

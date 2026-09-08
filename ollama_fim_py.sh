#!/bin/sh
# Test qwen2.5-coder FIM latency using Python (curl not available in pod)
python3 -c '
import json, time, urllib.request

base = "http://localhost:11434"

# Test 1: FIM completion
payload = {
    "model": "qwen2.5-coder:7b",
    "prompt": "<|fim_begin|>def fibonacci(n):\n    if n <= 1:\n        return n\n    return<|fim_hole|>\n\n# Test\nprint(fibonacci(10))<|fim_end|>",
    "raw": True,
    "stream": False,
    "options": {"num_predict": 32, "temperature": 0.2, "stop": ["\n\n"]}
}

print("=== FIM TEST 1 ===")
req = urllib.request.Request(base + "/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
start = time.time()
try:
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    elapsed = (time.time() - start) * 1000
    print(f"Response: {data.get(\"response\", \"\").strip()}")
    print(f"ELAPSED_MS: {elapsed:.0f}")
    print(f"eval_count: {data.get(\"eval_count\", \"?\")}")
    print(f"eval_duration_s: {data.get(\"eval_duration\", 0)/1e9:.2f}")
except Exception as e:
    elapsed = (time.time() - start) * 1000
    print(f"ERROR: {e}")
    print(f"ELAPSED_MS: {elapsed:.0f}")

# Test 2: simpler
payload2 = {
    "model": "qwen2.5-coder:7b",
    "prompt": "<|fim_begin|>import pandas as pd\n\ndef load_csv(path):\n    df = pd.read_csv(path)\n    return df.<|fim_hole|>\n\ndf = load_csv(\"data.csv\")<|fim_end|>",
    "raw": True,
    "stream": False,
    "options": {"num_predict": 24, "temperature": 0.2, "stop": ["\n"]}
}

print("\n=== FIM TEST 2 ===")
req2 = urllib.request.Request(base + "/api/generate", data=json.dumps(payload2).encode(), headers={"Content-Type": "application/json"})
start2 = time.time()
try:
    resp2 = urllib.request.urlopen(req2, timeout=60)
    data2 = json.loads(resp2.read())
    elapsed2 = (time.time() - start2) * 1000
    print(f"Response: {data2.get(\"response\", \"\").strip()}")
    print(f"ELAPSED_MS: {elapsed2:.0f}")
    print(f"eval_count: {data2.get(\"eval_count\", \"?\")}")
except Exception as e:
    elapsed2 = (time.time() - start2) * 1000
    print(f"ERROR: {e}")
    print(f"ELAPSED_MS: {elapsed2:.0f}")

# Test 3: chat completion (OpenAI-compatible)
payload3 = {
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Write a Python function to check if a number is prime. Only return the code."}],
    "stream": False,
    "options": {"num_predict": 48, "temperature": 0.2}
}

print("\n=== CHAT TEST 3 ===")
req3 = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(payload3).encode(), headers={"Content-Type": "application/json"})
start3 = time.time()
try:
    resp3 = urllib.request.urlopen(req3, timeout=60)
    data3 = json.loads(resp3.read())
    elapsed3 = (time.time() - start3) * 1000
    print(f"Response: {data3.get(\"choices\", [{}])[0].get(\"message\", {}).get(\"content\", \"\").strip()[:200]}")
    print(f"ELAPSED_MS: {elapsed3:.0f}")
except Exception as e:
    elapsed3 = (time.time() - start3) * 1000
    print(f"ERROR: {e}")
    print(f"ELAPSED_MS: {elapsed3:.0f}")

print("\n=== LOADAVG ===")
with open("/proc/loadavg") as f:
    print(f.read().strip())
'

#!/bin/bash
# Test the inline completion server endpoint and also check jlpm
echo "=== Check jlpm ==="
which jlpm 2>&1 || echo "jlpm not found"
jupyter lab --version 2>&1

echo ""
echo "=== Test: start a quick jupyter server in background ==="
# Start jupyter server in background to test the endpoint
python3 -c "
import subprocess, time, sys, os, signal

# Start jupyter server
proc = subprocess.Popen(
    ['jupyter', 'server', '--no-browser', '--port=8899', '--ServerApp.token=', '--ServerApp.password='],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

# Wait for server to start
time.sleep(8)

# Test the endpoint
import urllib.request, json

# Test health/stats endpoint
try:
    resp = urllib.request.urlopen('http://localhost:8899/inline-completion/v1/stats', timeout=5)
    data = json.loads(resp.read())
    print('STATS endpoint:', json.dumps(data, indent=2))
except Exception as e:
    print('STATS endpoint error:', e)

# Test completion endpoint
try:
    payload = json.dumps({
        'prefix': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return',
        'suffix': '\n\n# Test\nprint(fibonacci(10))',
        'language': 'python',
        'max_tokens': 32
    }).encode()
    req = urllib.request.Request('http://localhost:8899/inline-completion/v1/completion',
        data=payload, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print('COMPLETION endpoint:', json.dumps(data, indent=2))
except Exception as e:
    print('COMPLETION endpoint error:', e)

# Test cache hit (same request again)
try:
    req2 = urllib.request.Request('http://localhost:8899/inline-completion/v1/completion',
        data=payload, headers={'Content-Type': 'application/json'})
    resp2 = urllib.request.urlopen(req2, timeout=10)
    data2 = json.loads(resp2.read())
    print('COMPLETION (cache hit):', json.dumps(data2, indent=2))
except Exception as e:
    print('COMPLETION cache hit error:', e)

# Kill server
proc.terminate()
proc.wait()
print('Server stopped')
" 2>&1

echo "=== DONE ==="

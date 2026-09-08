import json, urllib.request, time, sys

# Attempt minimal raw generate; ollama has 2 slots, 4 models loaded.
# Previous failures may be OLLAMA_NUM_PARALLEL+queue contention with embed traffic.
# Try api/chat (recommended) and short timeout to see if we at least get queued quickly.
URL = 'http://ollama-worker.ai-platform.svc.cluster.local:11434'

def post(path, payload, timeout=120):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(URL + path, data=body, headers={'Content-Type': 'application/json'})
    t = time.time()
    r = urllib.request.urlopen(req, timeout=timeout)
    d = json.loads(r.read())
    return time.time() - t, d

# 1) test tinyllama (tiny, fast, always loads fast) to isolate whether generation works at all
try:
    dt, d = post('/api/generate', {'model': 'tinyllama:latest', 'prompt': '1+1=', 'stream': False,
                                   'raw': True, 'options': {'num_predict': 8}})
    print(f'tinyllama: {dt:.2f}s -> {d.get("response", "")[:80]!r}')
except Exception as e:
    print('tinyllama failed:', e)

# 2) test qwen2.5-coder:7b with small ctx and keep_alive refresh
try:
    dt, d = post('/api/generate', {'model': 'qwen2.5-coder:7b', 'prompt': 'def add(a,b): return', 'stream': False,
                                   'raw': True, 'options': {'num_predict': 16, 'num_ctx': 2048}})
    print(f'qwen-coder: {dt:.2f}s -> {d.get("response", "")[:80]!r}')
except Exception as e:
    print('qwen-coder failed:', e)

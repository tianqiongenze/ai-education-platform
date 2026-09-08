import json, urllib.request, time, threading

# qwen2.5-coder:7b is loaded (CPU). Previous 3m timeout was likely model-load
# or scheduling contention with embedding models. Test now that it shows loaded.
URL = 'http://ollama-worker.ai-platform.svc.cluster.local:11434/api/generate'

def gen(payload, label, timeout=300):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(URL, data=body, headers={'Content-Type': 'application/json'})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        d = json.loads(r.read())
        dt = time.time() - t
        eval_d = d.get('eval_duration', 0) / 1e9 or 1
        n = d.get('eval_count', 1)
        print(f'{label}: wall={dt:.2f}s tokens={n} tok/s={n/eval_d:.1f}')
        print('  out:', d.get('response', '').replace(chr(10), ' | ')[:160])
    except Exception as e:
        print(f'{label}: FAILED {e}')

# warm, tiny FIM-ish request
gen({'model': 'qwen2.5-coder:7b', 'prompt': 'def add(a, b):\n    return', 'stream': False,
     'raw': True, 'options': {'num_predict': 24, 'temperature': 0}}, 'warm-tiny')

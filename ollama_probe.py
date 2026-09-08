import json, urllib.request, time

# The earlier request likely queued behind ollama model load (7b cold start).
# Retry with generous timeout and also hit ollama directly via service DNS.
def try_direct_ollama(model, prefix, max_tokens=48, timeout=180):
    body = json.dumps({
        'model': model,
        'prompt': f'def fibo(n):',
        'stream': False,
        'raw': True,
        'options': {'num_predict': max_tokens, 'temperature': 0, 'stop': ['\n\n']},
    }).encode()
    req = urllib.request.Request('http://ollama-worker.ai-platform.svc.cluster.local:11434/api/generate',
                                 data=body, headers={'Content-Type': 'application/json'})
    t = time.time()
    r = urllib.request.urlopen(req, timeout=timeout)
    d = json.loads(r.read())
    dt = time.time() - t
    return dt, d.get('response', '')

try:
    dt, txt = try_direct_ollama('qwen2.5-coder:7b', 'def fibo(n):')
    print(f'direct ollama: {dt:.2f}s ->', txt.replace(chr(10), ' | ')[:150])
except Exception as e:
    print('direct ollama failed:', e)

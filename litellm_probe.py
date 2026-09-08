import json, urllib.request, time

# 1) Which coder models does litellm expose?
req = urllib.request.Request('http://10.108.11.54:4000/v1/models', headers={'Authorization': 'Bearer sk-1234'})
try:
    r = urllib.request.urlopen(req, timeout=15)
    models = [m['id'] for m in json.loads(r.read())['data']]
    coders = [m for m in models if 'coder' in m or 'code' in m]
    print('litellm total models:', len(models))
    print('coder models:', coders[:10])
except Exception as e:
    print('litellm /v1/models failed:', e)

# 2) Try a small completion via litellm OpenAI endpoint with a coder model
for m in ['qwen2.5-coder:7b', 'qwen2.5-coder:14b']:
    try:
        t = time.time()
        body = json.dumps({
            'model': m,
            'messages': [{'role': 'user', 'content': 'Complete this Python function, output code only:\ndef fibo(n):\n'}],
            'max_tokens': 48, 'temperature': 0, 'stream': False,
        }).encode()
        req2 = urllib.request.Request('http://10.108.11.54:4000/v1/chat/completions', data=body,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer sk-1234'})
        r2 = urllib.request.urlopen(req2, timeout=60)
        d = json.loads(r2.read())
        dt = time.time() - t
        txt = d['choices'][0]['message']['content'][:120]
        print(f'{m}: {dt:.2f}s ->', txt.replace(chr(10), ' | ')[:120])
    except Exception as e:
        print(f'{m}: failed - {e}')

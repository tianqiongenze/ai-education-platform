import json, urllib.request, time

BASE = 'http://10.108.11.54:4000'
# The 400 earlier was auth-related; try without auth header and with common keys
def chat(model, prefix, max_tokens=48):
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': f'Complete this code, output only the continuation:\n\n{prefix}'}],
        'max_tokens': max_tokens, 'temperature': 0, 'stream': False,
    }).encode()
    req = urllib.request.Request(BASE + '/v1/chat/completions', data=body,
        headers={'Content-Type': 'application/json'})
    t = time.time()
    r = urllib.request.urlopen(req, timeout=90)
    d = json.loads(r.read())
    dt = time.time() - t
    return dt, d['choices'][0]['message']['content']

# No auth header first
for m in ['qwen2.5-coder:7b']:
    try:
        dt, txt = chat(m, 'def fibo(n):')
        print(f'noauth {m}: {dt:.2f}s ->', txt.replace(chr(10), ' | ')[:100])
    except Exception as e:
        print(f'noauth {m}: failed - {e}')
        # read error body
        try:
            print('  body:', e.read()[:200])
        except Exception:
            pass

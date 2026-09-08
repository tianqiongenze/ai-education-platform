#!/usr/bin/env python3
"""Test Ollama with correct model names."""
import urllib.request, json, urllib.error

# First get the exact model names
print("=== Getting model list ===")
req = urllib.request.Request(
    'http://ollama-worker.ai-platform.svc.cluster.local:11434/api/tags',
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
models = [m['name'] for m in data.get('models', [])]
print("Available models:")
for m in models:
    print("  ", m)

# Test with each chat-capable model (skip embedding models)
chat_models = [m for m in models if 'embed' not in m.lower() and 'bge' not in m.lower()]
print("\nChat-capable models:", chat_models)

# Try the first few
for model_name in chat_models[:5]:
    print("\n=== Testing: %s ===" % model_name)
    payload = json.dumps({
        'model': model_name,
        'messages': [{'role': 'user', 'content': 'Say hello in one word'}],
        'stream': False,
        'options': {'num_predict': 10}
    }).encode()
    req = urllib.request.Request(
        'http://ollama-worker.ai-platform.svc.cluster.local:11434/api/chat',
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        content = data.get('message', {}).get('content', '')
        print('SUCCESS:', content[:100])
        break  # Found a working model
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')[:200]
        print('FAILED: HTTP', e.code, body)
    except Exception as e:
        print('FAILED:', e)

# Also test OpenAI-compatible endpoint with the working model
print("\n=== Testing OpenAI-compatible endpoint ===")
for model_name in chat_models[:3]:
    print("  Trying: %s" % model_name)
    payload = json.dumps({
        'model': model_name,
        'messages': [{'role': 'user', 'content': 'Say hello'}],
        'max_tokens': 10
    }).encode()
    req = urllib.request.Request(
        'http://ollama-worker.ai-platform.svc.cluster.local:11434/v1/chat/completions',
        data=payload,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ollama'}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print('  SUCCESS:', content[:100])
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')[:200]
        print('  FAILED: HTTP', e.code, body)
    except Exception as e:
        print('  FAILED:', e)

print("\n=== Done ===")

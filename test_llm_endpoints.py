#!/usr/bin/env python3
"""Test all LLM endpoint variants."""
import urllib.request, json, urllib.error, sys

print("=== Test 1: Ollama native /api/chat ===")
payload = json.dumps({
    'model': 'qwen2.5:7b',
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
    print('SUCCESS:', data.get('message', {}).get('content', '')[:100])
except urllib.error.HTTPError as e:
    print('FAILED: HTTP', e.code, e.read().decode('utf-8', errors='replace')[:300])
except Exception as e:
    print('FAILED:', e)

print("\n=== Test 2: Ollama /api/generate ===")
payload2 = json.dumps({
    'model': 'qwen2.5:7b',
    'prompt': 'Say hello in one word',
    'stream': False,
    'options': {'num_predict': 10}
}).encode()
req2 = urllib.request.Request(
    'http://ollama-worker.ai-platform.svc.cluster.local:11434/api/generate',
    data=payload2,
    headers={'Content-Type': 'application/json'}
)
try:
    resp2 = urllib.request.urlopen(req2, timeout=120)
    data2 = json.loads(resp2.read())
    print('SUCCESS:', data2.get('response', '')[:100])
except urllib.error.HTTPError as e:
    print('FAILED: HTTP', e.code, e.read().decode('utf-8', errors='replace')[:300])
except Exception as e:
    print('FAILED:', e)

print("\n=== Test 3: LiteLLM /v1/chat/completions ===")
payload3 = json.dumps({
    'model': 'qwen2.5:7b',
    'messages': [{'role': 'user', 'content': 'Say hello in one word'}],
    'max_tokens': 10
}).encode()
req3 = urllib.request.Request(
    'http://10.108.11.54:4000/v1/chat/completions',
    data=payload3,
    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer sk-anything'}
)
try:
    resp3 = urllib.request.urlopen(req3, timeout=120)
    data3 = json.loads(resp3.read())
    print('SUCCESS:', data3.get('choices', [{}])[0].get('message', {}).get('content', '')[:100])
except urllib.error.HTTPError as e:
    print('FAILED: HTTP', e.code, e.read().decode('utf-8', errors='replace')[:500])
except Exception as e:
    print('FAILED:', e)

print("\n=== Test 4: Ollama OpenAI-compatible /v1/chat/completions ===")
payload5 = json.dumps({
    'model': 'qwen2.5:7b',
    'messages': [{'role': 'user', 'content': 'Say hello in one word'}],
    'max_tokens': 10
}).encode()
req5 = urllib.request.Request(
    'http://ollama-worker.ai-platform.svc.cluster.local:11434/v1/chat/completions',
    data=payload5,
    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ollama'}
)
try:
    resp5 = urllib.request.urlopen(req5, timeout=120)
    data5 = json.loads(resp5.read())
    print('SUCCESS:', data5.get('choices', [{}])[0].get('message', {}).get('content', '')[:100])
except urllib.error.HTTPError as e:
    print('FAILED: HTTP', e.code, e.read().decode('utf-8', errors='replace')[:500])
except Exception as e:
    print('FAILED:', e)

print("\n=== Test 5: LiteLLM with tinyllama ===")
payload4 = json.dumps({
    'model': 'tinyllama',
    'messages': [{'role': 'user', 'content': 'Say hello in one word'}],
    'max_tokens': 10
}).encode()
req4 = urllib.request.Request(
    'http://10.108.11.54:4000/v1/chat/completions',
    data=payload4,
    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer sk-anything'}
)
try:
    resp4 = urllib.request.urlopen(req4, timeout=60)
    data4 = json.loads(resp4.read())
    print('SUCCESS:', data4.get('choices', [{}])[0].get('message', {}).get('content', '')[:100])
except urllib.error.HTTPError as e:
    print('FAILED: HTTP', e.code, e.read().decode('utf-8', errors='replace')[:500])
except Exception as e:
    print('FAILED:', e)

print("\n=== All tests done ===")

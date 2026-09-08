import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

password = 'difyai123456'
encoded = base64.b64encode(password.encode()).decode()
data = json.dumps({'email': 'myuwei@126.com', 'password': encoded}).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)
resp = opener.open(req)
result = json.load(resp)
token = result.get('access_token', '')
print(f'Login OK.')

# Extract CSRF token from cookies
csrf_token = None
for cookie in cj:
    if cookie.name == 'csrf_token':
        csrf_token = cookie.value
        break
print(f'CSRF token: {csrf_token[:40]}...')

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': csrf_token
}

# Get model providers
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers',
    headers=headers
)
resp = opener.open(req)
providers = json.load(resp)
print(f'\nModel providers ({len(providers.get("data", []))}):')
for p in providers.get('data', []):
    provider = p.get('provider', '')
    name = p.get('provider_name', '')
    configured = p.get('is_configured', False)
    print(f'  {provider} ({name}) - configured: {configured}')

# Save credentials for openai_api_compatible
print('\n--- Saving credentials ---')
creds = {
    'credentials': {
        'api_key': 'sk-ai-platform-master',
        'endpoint_url': 'http://litellm.ai-platform.svc.cluster.local:4000/v1'
    }
}
data = json.dumps(creds).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers/openai_api_compatible/credentials',
    data=data,
    headers=headers
)
try:
    resp = opener.open(req)
    print(f'Credentials saved: {resp.read().decode()[:300]}')
except urllib.error.HTTPError as e:
    print(f'Credentials error: {e.code}')
    print(e.read().decode()[:500])

# List available models
print('\n--- Available models ---')
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers/openai_api_compatible/models',
    headers=headers
)
try:
    resp = opener.open(req)
    models = json.load(resp)
    print(f'Models: {json.dumps(models, indent=2)[:1500]}')
except urllib.error.HTTPError as e:
    print(f'Models error: {e.code}')
    print(e.read().decode()[:500])

# Add custom models
print('\n--- Adding custom models ---')
models_to_add = [
    {"model": "qwen2.5:14b", "model_type": "llm"},
    {"model": "deepseek-r1:14b", "model_type": "llm"},
    {"model": "qwen2.5:7b", "model_type": "llm"},
    {"model": "qwen2.5-coder:14b", "model_type": "llm"},
    {"model": "bge-m3", "model_type": "text-embedding"},
]

for m in models_to_add:
    data = json.dumps(m).encode()
    req = urllib.request.Request(
        'http://localhost:5001/console/api/workspaces/current/model-providers/openai_api_compatible/models',
        data=data,
        headers=headers,
        method='POST'
    )
    try:
        resp = opener.open(req)
        result = json.load(resp)
        print(f'  Added {m["model"]}: {result.get("result", "unknown")}')
    except urllib.error.HTTPError as e:
        print(f'  Failed {m["model"]}: {e.code} - {e.read().decode()[:200]}')

print('\nDone!')
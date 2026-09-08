#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import urllib.request, json, base64

# Login via localhost
password = 'difyai123456'
encoded = base64.b64encode(password.encode()).decode()
data = json.dumps({'email': 'myuwei@126.com', 'password': encoded}).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
result = json.load(resp)
token = result.get('access_token', '')
print(f'Login OK. Token: {token[:40]}...')

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get model providers
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers',
    headers=headers
)
resp = urllib.request.urlopen(req)
providers = json.load(resp)
print(f'Providers: {len(providers.get(\"data\", []))}')
for p in providers.get('data', []):
    print(f'  - {p.get(\"provider\")}: {p.get(\"provider_name\")}')

# Save credentials for openai_api_compatible
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
    resp = urllib.request.urlopen(req)
    print(f'Credentials saved: {resp.read().decode()[:300]}')
except urllib.error.HTTPError as e:
    print(f'Credentials error: {e.code}')
    print(e.read().decode()[:500])

# List models
print()
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers/openai_api_compatible/models',
    headers=headers
)
try:
    resp = urllib.request.urlopen(req)
    models = json.load(resp)
    print(f'Models response: {json.dumps(models, indent=2)[:1000]}')
except urllib.error.HTTPError as e:
    print(f'Models error: {e.code}')
    print(e.read().decode()[:500])
" 2>/dev/null
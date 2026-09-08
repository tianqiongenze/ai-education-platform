#!/bin/bash
kubectl exec -n dify deploy/dify-api -- python3 -c "
import urllib.request, json, base64

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
print('Model providers:')
for p in providers.get('data', []):
    provider = p.get('provider', '')
    name = p.get('provider_name', '')
    configured = p.get('is_configured', False)
    print(f'  {provider} ({name}) - configured: {configured}')
" 2>/dev/null
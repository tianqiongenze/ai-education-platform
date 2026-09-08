#!/bin/bash
# Login from within the dify-api pod itself (bypasses network issues)
kubectl exec -n dify deploy/dify-api -- python3 -c "
import urllib.request, json

# Login via localhost
data = json.dumps({'email': 'myuwei@126.com', 'password': 'difyai123456'}).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print('Login SUCCESS!')
    token = result.get('access_token', '')
    print(f'Token: {token[:60]}...')
    
    # Get model providers
    req2 = urllib.request.Request(
        'http://localhost:5001/console/api/workspaces/current/model-providers',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp2 = urllib.request.urlopen(req2)
    providers = json.load(resp2)
    print(f'Providers: {len(providers.get(\"data\", []))}')
    for p in providers.get('data', []):
        print(f'  - {p.get(\"provider\")}')
except urllib.error.HTTPError as e:
    print(f'Failed: {e.code}')
    print(e.read().decode()[:500])
" 2>/dev/null
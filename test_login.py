import urllib.request, json

base = "http://10.167.2.176:30501"

# Login
data = json.dumps({"email": "myuwei@126.com", "password": "Admin123!"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("Login SUCCESS!")
    token = result.get('access_token', '')
    print(f"Access token: {token[:60]}...")
    
    # Get model providers
    req2 = urllib.request.Request(
        f"{base}/console/api/workspaces/current/model-providers",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp2 = urllib.request.urlopen(req2)
    providers = json.load(resp2)
    print(f"\nModel providers count: {len(providers.get('data', []))}")
    for p in providers.get('data', []):
        print(f"  - {p.get('provider', 'unknown')}: {p.get('provider_name', 'unknown')}")
    
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
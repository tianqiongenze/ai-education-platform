import urllib.request, json

base = "http://10.167.2.176:30501"

# Login
data = json.dumps({"email": "myuwei@126.com", "password": "admin123"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("Login SUCCESS!")
    print(f"Access token: {result.get('access_token', 'N/A')[:50]}...")
    
    # Now get model providers
    token = result.get('access_token', '')
    req2 = urllib.request.Request(
        f"{base}/console/api/workspaces/current/model-providers",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp2 = urllib.request.urlopen(req2)
    providers = json.load(resp2)
    print(f"\nModel providers: {json.dumps(providers, indent=2)[:1000]}")
    
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code} {e.reason}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
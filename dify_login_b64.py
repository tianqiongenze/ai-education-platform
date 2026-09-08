import urllib.request, json, base64

base_url = "http://10.167.2.176:30501"
email = "myuwei@126.com"
password = "difyai123456"

# Base64 encode the password (Dify frontend does this)
encoded_password = base64.b64encode(password.encode()).decode()
print(f"Encoded password: {encoded_password}")

# Login
data = json.dumps({"email": email, "password": encoded_password}).encode()
req = urllib.request.Request(
    f"{base_url}/console/api/login",
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
        f"{base_url}/console/api/workspaces/current/model-providers",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp2 = urllib.request.urlopen(req2)
    providers = json.load(resp2)
    print(f"\nModel providers count: {len(providers.get('data', []))}")
    for p in providers.get('data', []):
        print(f"  - {p.get('provider', 'unknown')}: {p.get('provider_name', 'unknown')}")
    
    # Save token for later use
    with open('/tmp/dify_token.txt', 'w') as f:
        f.write(token)
    
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
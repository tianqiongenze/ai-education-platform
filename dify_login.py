import urllib.request, json

# Try to login with the first admin email
# Dify uses email + password login
# Let's try common passwords or check if there's a way to reset

# First, let's check what auth endpoints are available
base = "http://10.167.2.176:30501"

# Try the login endpoint
data = json.dumps({"email": "myuwei@126.com", "password": "difyai123456"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("Login result:", json.dumps(result, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code} {e.reason}")
    body = e.read().decode()
    print(f"Body: {body[:300]}")

# Also try setup endpoint
try:
    req = urllib.request.Request(f"{base}/console/api/setup")
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("\nSetup status:", json.dumps(result, indent=2)[:300])
except urllib.error.HTTPError as e:
    print(f"\nSetup check: {e.code}")
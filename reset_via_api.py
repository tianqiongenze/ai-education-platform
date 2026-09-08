import urllib.request, json

base = "http://10.167.2.176:30501"

# Try the password reset endpoint
data = json.dumps({"email": "myuwei@126.com"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/reset-password",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("Reset password result:", json.dumps(result, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"Reset failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Try forgot-password endpoint
data2 = json.dumps({"email": "myuwei@126.com"}).encode()
req2 = urllib.request.Request(
    f"{base}/console/api/forgot-password",
    data=data2,
    headers={"Content-Type": "application/json"}
)
try:
    resp2 = urllib.request.urlopen(req2)
    result2 = json.load(resp2)
    print("\nForgot password result:", json.dumps(result2, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"\nForgot password failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Try to create a new admin via setup
data3 = json.dumps({
    "email": "admin@local.ai",
    "name": "AI Admin",
    "password": "admin123456"
}).encode()
req3 = urllib.request.Request(
    f"{base}/console/api/setup",
    data=data3,
    headers={"Content-Type": "application/json"}
)
try:
    resp3 = urllib.request.urlopen(req3)
    result3 = json.load(resp3)
    print("\nSetup result:", json.dumps(result3, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"\nSetup failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
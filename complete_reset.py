import urllib.request, json

base = "http://10.167.2.176:30501"
token = "58fa585c-d478-46b2-8230-ea5e21b70023"
new_password = "admin123"

# Complete the password reset
data = json.dumps({
    "token": token,
    "new_password": new_password,
    "password_confirm": new_password
}).encode()
req = urllib.request.Request(
    f"{base}/console/api/reset-password",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    print("Reset result:", json.dumps(result, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"Reset failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Now try to login
print("\n--- Trying login ---")
data2 = json.dumps({"email": "myuwei@126.com", "password": new_password}).encode()
req2 = urllib.request.Request(
    f"{base}/console/api/login",
    data=data2,
    headers={"Content-Type": "application/json"}
)
try:
    resp2 = urllib.request.urlopen(req2)
    result2 = json.load(resp2)
    print("Login SUCCESS!")
    print(f"Access token: {result2.get('access_token', 'N/A')[:60]}...")
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
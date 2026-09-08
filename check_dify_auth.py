import urllib.request, json

base = "http://10.167.2.176:30501"

# Try to get a new reset token
data = json.dumps({"email": "myuwei@126.com"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/reset-password",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    token = result.get("data", "")
    print(f"Reset token: {token}")
    
    # Now use the token with the correct endpoint
    # Dify's reset flow: POST /reset-password with {token, new_password, password_confirm}
    # But the token from the email reset might need a different endpoint
    
    # Try the email-based reset confirmation
    data2 = json.dumps({
        "email": "myuwei@126.com",
        "code": token,
        "new_password": "Admin123!",
        "password_confirm": "Admin123!"
    }).encode()
    
    # Try different endpoints
    for endpoint in ["/console/api/reset-password", "/console/api/email-code-login"]:
        req2 = urllib.request.Request(
            f"{base}{endpoint}",
            data=data2,
            headers={"Content-Type": "application/json"}
        )
        try:
            resp2 = urllib.request.urlopen(req2)
            result2 = json.load(resp2)
            print(f"\n{endpoint} result: {json.dumps(result2, indent=2)[:300]}")
        except urllib.error.HTTPError as e:
            print(f"\n{endpoint} failed: {e.code} - {e.read().decode()[:200]}")
            
except urllib.error.HTTPError as e:
    print(f"Reset failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
import requests, re

s = requests.Session()
r = s.get("http://10.167.2.175:30089/ide/hub/login", timeout=15)
xsrf_cookie = s.cookies.get("_xsrf", "")
print("XSRF cookie:", xsrf_cookie[:30] if xsrf_cookie else "NONE")

r = s.post("http://10.167.2.175:30089/ide/hub/login", data={
    "username": "student-alice",
    "password": "ide2026",
    "_xsrf": xsrf_cookie
}, allow_redirects=True, timeout=120)
print("Login URL:", r.url)
print("Status:", r.status_code)

# Get all XSRF cookies (hub and user server have different ones)
xsrf_cookies = [c for c in s.cookies if c.name == "_xsrf"]
print("XSRF cookies:", len(xsrf_cookies))
for c in xsrf_cookies:
    print(f"  domain={c.domain} path={c.path} value={c.value[:30]}")

# Use the user-server XSRF token (domain contains 'student-alice' or the user path)
xsrf_jupyter = ""
for c in xsrf_cookies:
    if "student-alice" in c.domain or c.path.startswith("/ide/user"):
        xsrf_jupyter = c.value
        break
if not xsrf_jupyter and xsrf_cookies:
    xsrf_jupyter = xsrf_cookies[-1].value  # last one is likely the user server
print("Using XSRF:", xsrf_jupyter[:30] if xsrf_jupyter else "NONE")

# Test with XSRF header
r2 = s.get("http://10.167.2.175:30089/ide/user/student-alice/api/contents/work",
    headers={"X-XSRFToken": xsrf_jupyter, "X-CSRFToken": xsrf_jupyter}, timeout=30)
print("Contents API (with XSRF header):", r2.status_code)

if r2.status_code == 200:
    data = r2.json()
    print("Files:", [f["name"] for f in data.get("content", [])])
else:
    print("Response:", r2.text[:200])

# Test PUT
r3 = s.put("http://10.167.2.175:30089/ide/user/student-alice/api/contents/work/test_xsrf.txt",
    json={"type": "file", "format": "text", "content": "XSRF_TEST_OK"},
    headers={"X-XSRFToken": xsrf_jupyter, "X-CSRFToken": xsrf_jupyter}, timeout=30)
print("PUT test:", r3.status_code)

if r3.status_code in (200, 201):
    print("XSRF header fix works!")

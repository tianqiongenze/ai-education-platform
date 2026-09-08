import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

password = 'difyai123456'
encoded = base64.b64encode(password.encode()).decode()
data = json.dumps({'email': 'myuwei@126.com', 'password': encoded}).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)
resp = opener.open(req)
result = json.load(resp)
token = result.get('access_token', '')

csrf_token = None
for cookie in cj:
    if cookie.name == 'csrf_token':
        csrf_token = cookie.value
        break

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': csrf_token
}

# Get provider details to see the credential schema
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers/langgenius/openai_api_compatible/openai_api_compatible',
    headers=headers
)
resp = opener.open(req)
detail = json.load(resp)
print(json.dumps(detail, indent=2)[:3000])
import urllib.request, json, base64, http.cookiejar

# Use cookie jar to handle cookies
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
print(f'Login OK. Token: {token[:40]}...')

# Check cookies
print(f'Cookies: {list(cj)}')

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get model providers
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers',
    headers=headers
)
try:
    resp = opener.open(req)
    providers = json.load(resp)
    print(f'\nModel providers ({len(providers.get("data", []))}):')
    for p in providers.get('data', []):
        provider = p.get('provider', '')
        name = p.get('provider_name', '')
        configured = p.get('is_configured', False)
        print(f'  {provider} ({name}) - configured: {configured}')
except urllib.error.HTTPError as e:
    print(f'Providers error: {e.code}')
    print(e.read().decode()[:500])
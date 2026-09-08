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

# List existing apps
print('--- Existing Apps ---')
req = urllib.request.Request(
    'http://localhost:5001/console/api/apps?page=1&limit=10',
    headers=headers
)
resp = opener.open(req)
apps = json.load(resp)
print(f'Total: {apps.get("total", 0)}')
for app in apps.get('data', []):
    print(f'  {app.get("id")}: {app.get("name")} (mode={app.get("mode")})')

# Check if there's an existing app we can use
if apps.get('data'):
    app_id = apps['data'][0]['id']
    print(f'\n--- Using existing app: {app_id} ---')
    
    # Get model config
    req = urllib.request.Request(
        f'http://localhost:5001/console/api/apps/{app_id}/model-config',
        headers=headers
    )
    try:
        resp = opener.open(req)
        config = json.load(resp)
        print(f'Model config: {json.dumps(config, indent=2)[:1000]}')
    except urllib.error.HTTPError as e:
        print(f'Config error: {e.code} - {e.read().decode()[:300]}')
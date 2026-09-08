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

app_id = '275c955d-0418-4a23-bd08-f042c3a73ed1'

# First, get the app's API key
print('--- Getting app API key ---')
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}/api-keys',
    headers=headers
)
try:
    resp = opener.open(req)
    keys = json.load(resp)
    print(f'API keys: {json.dumps(keys, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    print(f'Keys error: {e.code} - {e.read().decode()[:300]}')

# Try to get app parameters (public endpoint)
print('\n--- Getting app parameters ---')
req = urllib.request.Request(
    f'http://localhost:5001/v1/apps/{app_id}/parameters',
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    params = json.load(resp)
    print(f'Parameters: {json.dumps(params, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    print(f'Params error: {e.code} - {e.read().decode()[:300]}')

# Try chat with the public API (no auth needed for public apps)
print('\n--- Testing public chat ---')
chat_data = {
    "query": "Say hello in exactly 3 words",
    "inputs": {},
    "response_mode": "blocking",
    "user": "test-user-1"
}
data = json.dumps(chat_data).encode()
req = urllib.request.Request(
    f'http://localhost:5001/v1/chat-messages',
    data=data,
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.load(resp)
    answer = result.get('answer', 'NO ANSWER')
    print(f'Chat response: {answer[:300]}')
except urllib.error.HTTPError as e:
    print(f'Chat error: {e.code} - {e.read().decode()[:300]}')
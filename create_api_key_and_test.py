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

# Create API key for the app
print('--- Creating API key ---')
key_data = {"name": "test-key"}
data = json.dumps(key_data).encode()
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}/api-keys',
    data=data,
    headers=headers
)
try:
    resp = opener.open(req)
    key_result = json.load(resp)
    print(f'API key created: {json.dumps(key_result, indent=2)[:500]}')
    api_key = key_result.get('token', '')
except urllib.error.HTTPError as e:
    print(f'Key creation error: {e.code} - {e.read().decode()[:300]}')
    api_key = None

if api_key:
    # Test chat with API key
    print(f'\n--- Testing chat with API key ---')
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
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.load(resp)
        answer = result.get('answer', 'NO ANSWER')
        print(f'Chat response: {answer[:300]}')
        print(f'Full result keys: {list(result.keys())}')
    except urllib.error.HTTPError as e:
        print(f'Chat error: {e.code} - {e.read().decode()[:500]}')
    except Exception as e:
        print(f'Error: {e}')
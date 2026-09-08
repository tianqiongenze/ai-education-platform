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

# Use the Website Generator app (chat mode)
app_id = '275c955d-0418-4a23-bd08-f042c3a73ed1'
print(f'Using app: {app_id}')

# Get app detail
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}',
    headers=headers
)
resp = opener.open(req)
app = json.load(resp)
print(f'App: {app.get("name")} (mode={app.get("mode")})')

# Get model config - try PUT
print('\n--- Getting model config ---')
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}/model-config?model_config_id=',
    headers=headers
)
try:
    resp = opener.open(req)
    config = json.load(resp)
    print(f'Current config: {json.dumps(config, indent=2)[:1000]}')
except urllib.error.HTTPError as e:
    print(f'GET config error: {e.code} - {e.read().decode()[:300]}')

# Try to update model config via PUT
print('\n--- Updating model config ---')
model_config = {
    "pre_prompt": "",
    "prompt_type": "simple",
    "model": {
        "provider": "langgenius/openai_api_compatible/openai_api_compatible",
        "name": "qwen2.5:7b",
        "mode": "chat",
        "completion_params": {}
    }
}
data = json.dumps(model_config).encode()
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}/model-config',
    data=data,
    headers=headers,
    method='POST'
)
try:
    resp = opener.open(req)
    result = json.load(resp)
    print(f'Update result: {json.dumps(result, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    print(f'Update error: {e.code} - {e.read().decode()[:300]}')

# Test chat
print('\n--- Testing chat ---')
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
    headers=headers
)
try:
    resp = opener.open(req)
    result = json.load(resp)
    answer = result.get('answer', 'NO ANSWER')
    print(f'Chat response: {answer[:200]}')
except urllib.error.HTTPError as e:
    print(f'Chat error: {e.code} - {e.read().decode()[:300]}')
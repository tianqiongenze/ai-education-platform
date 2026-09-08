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

# Step 1: Create a new Chatbot app
print('--- Creating Chatbot App ---')
app_data = {
    "name": "Test Local Model Chat",
    "description": "Testing local LLM via litellm",
    "mode": "chat",
    "icon_type": "emoji",
    "icon": "🤖",
    "icon_background": "#FFEAD5"
}
data = json.dumps(app_data).encode()
req = urllib.request.Request(
    'http://localhost:5001/console/api/apps',
    data=data,
    headers=headers
)
try:
    resp = opener.open(req)
    app = json.load(resp)
    app_id = app.get('id', '')
    print(f'App created: {app_id}')
    print(f'App: {json.dumps(app, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    print(f'Create app failed: {e.code}')
    print(e.read().decode()[:500])
    app_id = None

if app_id:
    # Step 2: Get the app's model config
    print(f'\n--- Getting model config for app {app_id} ---')
    req = urllib.request.Request(
        f'http://localhost:5001/console/api/apps/{app_id}/model-config',
        headers=headers
    )
    try:
        resp = opener.open(req)
        config = json.load(resp)
        print(f'Model config: {json.dumps(config, indent=2)[:1000]}')
    except urllib.error.HTTPError as e:
        print(f'Get config failed: {e.code}')
        print(e.read().decode()[:500])

    # Step 3: Update model config to use our local model
    print(f'\n--- Updating model config ---')
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
        headers=headers
    )
    try:
        resp = opener.open(req)
        result = json.load(resp)
        print(f'Model config updated: {json.dumps(result, indent=2)[:500]}')
    except urllib.error.HTTPError as e:
        print(f'Update config failed: {e.code}')
        print(e.read().decode()[:500])

    # Step 4: Test chat with the app
    print(f'\n--- Testing chat ---')
    chat_data = {
        "query": "Say hello in 3 words",
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
        print(f'Chat response: {json.dumps(result, indent=2)[:500]}')
    except urllib.error.HTTPError as e:
        print(f'Chat failed: {e.code}')
        print(e.read().decode()[:500])
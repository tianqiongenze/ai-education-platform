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

provider_id = 'langgenius/openai_api_compatible/openai_api_compatible'

# 1. Get full model list
print('=' * 60)
print('1. FULL MODEL LIST')
print('=' * 60)
req = urllib.request.Request(
    f'http://localhost:5001/console/api/workspaces/current/model-providers/{provider_id}/models',
    headers=headers
)
resp = opener.open(req)
models_data = json.load(resp)
for m in models_data.get('data', []):
    print(f'  model: {m["model"]}')
    print(f'  model_type: {m["model_type"]}')
    print(f'  model_properties: {json.dumps(m.get("model_properties", {}))}')
    print(f'  features: {m.get("features", [])}')
    print()

# 2. Try POST to model-config endpoint
print('=' * 60)
print('2. POST MODEL CONFIG')
print('=' * 60)
app_id = '275c955d-0418-4a23-bd08-f042c3a73ed1'

# Try the format that matches the model listing structure
model_config = {
    "model": {
        "provider": provider_id,
        "name": "qwen2.5:7b",
        "mode": "chat",
        "completion_params": {}
    },
    "pre_prompt": "",
    "prompt_type": "simple",
    "chat_prompt_config": {},
    "completion_prompt_config": {},
    "dataset_configs": {},
    "opening_statement": "",
    "suggested_questions": [],
    "suggested_questions_after_answer": {"enabled": False},
    "speech_to_text": {"enabled": False},
    "text_to_speech": {"enabled": False},
    "retriever_resource": {"enabled": False},
    "sensitive_word_avoidance": {"enabled": False},
    "agent_mode": {"enabled": False},
    "more_like_this": {"enabled": False}
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
    print(f'POST result: {json.dumps(result, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f'POST error: {e.code} - {body}')

# 3. Test chat
print('\n' + '=' * 60)
print('3. TEST CHAT')
print('=' * 60)
api_key = 'app-rtnalxnfoWyczPhPBUbgbRGf'
chat_data = {
    "query": "Say hello in exactly 3 words",
    "inputs": {},
    "response_mode": "blocking",
    "user": "test-user-1"
}
data = json.dumps(chat_data).encode()
req = urllib.request.Request(
    'http://localhost:5001/v1/chat-messages',
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
    print(f'Chat response: {answer[:500]}')
    print(f'Full response keys: {list(result.keys())}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:800]
    print(f'Chat error: {e.code} - {body}')
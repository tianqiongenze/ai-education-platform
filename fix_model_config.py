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

# Get the app detail to see current model config
print('--- App detail ---')
req = urllib.request.Request(
    f'http://localhost:5001/console/api/apps/{app_id}',
    headers=headers
)
resp = opener.open(req)
app = json.load(resp)
print(f'App mode: {app.get("mode")}')
print(f'Model config: {json.dumps(app.get("model_config", {}), indent=2)[:1000]}')

# Try to update with proper model config for chat mode
print('\n--- Fixing model config ---')
# For chat mode, the model config needs specific fields
model_config = {
    "model": {
        "provider": "langgenius/openai_api_compatible/openai_api_compatible",
        "name": "qwen2.5:7b",
        "mode": "chat",
        "completion_params": {
            "temperature": 0.7,
            "max_tokens": 512
        }
    },
    "pre_prompt": "You are a helpful assistant.",
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
    print(f'Update result: {json.dumps(result, indent=2)[:500]}')
except urllib.error.HTTPError as e:
    print(f'Update error: {e.code} - {e.read().decode()[:500]}')

# Test chat again
print('\n--- Testing chat ---')
api_key = 'app-rtnalxnfoWyczPhPBUbgbRGf'
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
except urllib.error.HTTPError as e:
    print(f'Chat error: {e.code} - {e.read().decode()[:500]}')
import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
data = json.dumps({'email': 'myuwei@126.com', 'password': base64.b64encode('difyai123456'.encode()).decode()}).encode()
req = urllib.request.Request('http://localhost:5001/console/api/login', data=data, headers={'Content-Type': 'application/json'})
resp = opener.open(req)
token = json.load(resp).get('access_token', '')
csrf = None
for c in cj:
    if c.name == 'csrf_token':
        csrf = c.value
        break
h = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf}
provider_id = 'langgenius/openai_api_compatible/openai_api_compatible'
app_id = '275c955d-0418-4a23-bd08-f042c3a73ed1'
api_key = 'app-rtnalxnfoWyczPhPBUbgbRGf'

models = [
    ('qwen2.5:72b', 600),
    ('qwen2.5:32b', 300),
    ('deepseek-r1:32b', 600),
    ('qwen2.5:14b', 180),
    ('deepseek-r1:14b', 300),
    ('qwen2.5:7b', 120),
    ('qwen2.5-coder:14b', 180),
    ('deepseek-ai/deepseek-v4-pro', 180),
    ('z-ai/glm-5.1', 180),
]

print('=== TESTING ALL DIFY MODELS ===')
passed = 0
failed = 0
for model_name, timeout in models:
    model_config = {
        'model': {'provider': provider_id, 'name': model_name, 'mode': 'chat', 'completion_params': {}},
        'pre_prompt': '', 'prompt_type': 'simple',
        'chat_prompt_config': {}, 'completion_prompt_config': {}, 'dataset_configs': {},
        'opening_statement': '', 'suggested_questions': [],
        'suggested_questions_after_answer': {'enabled': False},
        'speech_to_text': {'enabled': False}, 'text_to_speech': {'enabled': False},
        'retriever_resource': {'enabled': False}, 'sensitive_word_avoidance': {'enabled': False},
        'agent_mode': {'enabled': False}, 'more_like_this': {'enabled': False}
    }
    req = urllib.request.Request('http://localhost:5001/console/api/apps/' + app_id + '/model-config', data=json.dumps(model_config).encode(), headers=h, method='POST')
    opener.open(req)
    
    chat_data = {'query': 'Say hello in exactly 3 words', 'inputs': {}, 'response_mode': 'blocking', 'user': 'test-user-1'}
    req = urllib.request.Request('http://localhost:5001/v1/chat-messages', data=json.dumps(chat_data).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        result = json.load(resp)
        answer = result.get('answer', 'NO ANSWER')
        print('[PASS] %-35s %s' % (model_name, answer[:80]))
        passed += 1
    except Exception as e:
        print('[FAIL] %-35s %s' % (model_name, str(e)[:100]))
        failed += 1

print()
print('=== RESULTS: %d passed, %d failed ===' % (passed, failed))
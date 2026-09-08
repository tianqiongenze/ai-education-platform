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

# 1. List ALL apps with their model configs
print('=' * 60)
print('1. ALL APPS WITH MODEL CONFIGS')
print('=' * 60)
req = urllib.request.Request(
    'http://localhost:5001/console/api/apps?page=1&limit=20',
    headers=headers
)
resp = opener.open(req)
apps = json.load(resp)
print(f'Total apps: {apps.get("total", 0)}')

for app in apps.get('data', []):
    app_id = app['id']
    app_name = app['name']
    app_mode = app['mode']
    print(f'\n--- {app_name} (id={app_id}, mode={app_mode}) ---')
    
    # Get model config for each app
    try:
        req2 = urllib.request.Request(
            f'http://localhost:5001/console/api/apps/{app_id}/model-config',
            headers=headers
        )
        resp2 = opener.open(req2)
        config = json.load(resp2)
        # Show the model part specifically
        model = config.get('model', {})
        print(f'  model.provider: {model.get("provider")}')
        print(f'  model.name: {model.get("name")}')
        print(f'  model.mode: {model.get("mode")}')
        print(f'  model.completion_params: {json.dumps(model.get("completion_params", {}))}')
        print(f'  Full model: {json.dumps(model, indent=2)}')
        # Show top-level keys
        print(f'  Top-level keys: {list(config.keys())}')
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f'  Config error: {e.code} - {body}')

# 2. Check provider detail
print('\n' + '=' * 60)
print('2. PROVIDER DETAIL')
print('=' * 60)
provider_id = 'langgenius/openai_api_compatible/openai_api_compatible'
req = urllib.request.Request(
    f'http://localhost:5001/console/api/workspaces/current/model-providers/{provider_id}',
    headers=headers
)
try:
    resp = opener.open(req)
    provider = json.load(resp)
    print(f'Provider keys: {list(provider.keys())}')
    # Show credential schema
    cred_schema = provider.get('provider_credential_schema', {})
    print(f'Credential schema: {json.dumps(cred_schema, indent=2)[:500]}')
    # Show model list
    models = provider.get('models', [])
    print(f'Models count: {len(models)}')
    for m in models[:5]:
        print(f'  Model: {json.dumps(m, indent=2)[:300]}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f'Provider detail error: {e.code} - {body}')

# 3. Try to get model config from a WORKING app (not our test app)
print('\n' + '=' * 60)
print('3. WORKING APP MODEL CONFIG (deep dive)')
print('=' * 60)
# Find a chat-mode app that's NOT our test app
for app in apps.get('data', []):
    if app['mode'] == 'chat' and app['id'] != '275c955d-0418-4a23-bd08-f042c3a73ed1':
        app_id = app['id']
        print(f'Examining: {app["name"]} ({app_id})')
        req = urllib.request.Request(
            f'http://localhost:5001/console/api/apps/{app_id}/model-config',
            headers=headers
        )
        try:
            resp = opener.open(req)
            config = json.load(resp)
            print(f'Full config: {json.dumps(config, indent=2)}')
        except urllib.error.HTTPError as e:
            print(f'Error: {e.code} - {e.read().decode()[:300]}')
        break

# 4. Try the model config endpoint with different methods
print('\n' + '=' * 60)
print('4. TESTING MODEL CONFIG ENDPOINT')
print('=' * 60)
test_app_id = '275c955d-0418-4a23-bd08-f042c3a73ed1'

# Try GET with model_config_id
for suffix in ['', '?model_config_id=', '?model_config_id=default']:
    try:
        req = urllib.request.Request(
            f'http://localhost:5001/console/api/apps/{test_app_id}/model-config{suffix}',
            headers=headers
        )
        resp = opener.open(req)
        config = json.load(resp)
        print(f'GET {suffix!r}: OK - keys={list(config.keys())}, model={json.dumps(config.get("model", {}))[:200]}')
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f'GET {suffix!r}: {e.code} - {body}')

# 5. Check if there's a model-provider endpoint for listing models
print('\n' + '=' * 60)
print('5. MODEL PROVIDER MODELS')
print('=' * 60)
req = urllib.request.Request(
    f'http://localhost:5001/console/api/workspaces/current/model-providers/{provider_id}/models',
    headers=headers
)
try:
    resp = opener.open(req)
    models = json.load(resp)
    print(f'Models: {json.dumps(models, indent=2)[:1000]}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f'Models error: {e.code} - {body}')

# 6. Try to get the model parameter rules
print('\n' + '=' * 60)
print('6. MODEL PARAMETER RULES')
print('=' * 60)
req = urllib.request.Request(
    f'http://localhost:5001/console/api/workspaces/current/model-providers/{provider_id}/models/parameter-rules',
    headers=headers
)
try:
    resp = opener.open(req)
    rules = json.load(resp)
    print(f'Rules: {json.dumps(rules, indent=2)[:1000]}')
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print(f'Rules error: {e.code} - {body}')
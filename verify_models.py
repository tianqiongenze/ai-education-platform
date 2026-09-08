import urllib.request, json, base64, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

password = 'difyai123456'
encoded = base64.b64encode(password.encode()).decode()
data = json.dumps({'email': 'myuwei@126.com', 'password': encoded}).encode()
req = urllib.request.Request('http://localhost:5001/console/api/login', data=data, headers={'Content-Type': 'application/json'})
resp = opener.open(req)
result = json.load(resp)
token = result.get('access_token', '')

csrf_token = None
for cookie in cj:
    if cookie.name == 'csrf_token':
        csrf_token = cookie.value
        break

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf_token}

provider_id = 'langgenius/openai_api_compatible/openai_api_compatible'

# Get all models for this provider
req = urllib.request.Request(
    f'http://localhost:5001/console/api/workspaces/current/model-providers/{provider_id}/models',
    headers=headers
)
resp = opener.open(req)
models_data = json.load(resp)

print('=== MODELS IN OPENAI_API_COMPATIBLE PROVIDER ===')
print(f'Total: {len(models_data.get("data", []))}')
for m in models_data.get('data', []):
    status = m.get('status', 'unknown')
    model_type = m.get('model_type', 'unknown')
    mode = m.get('model_properties', {}).get('mode', 'N/A')
    ctx = m.get('model_properties', {}).get('context_size', 'N/A')
    print(f'  [{status}] {m["model"]} (type={model_type}, mode={mode}, ctx={ctx})')

# Also check if provider has credentials configured
print()
print('=== PROVIDER STATUS ===')
req = urllib.request.Request(
    'http://localhost:5001/console/api/workspaces/current/model-providers',
    headers=headers
)
resp = opener.open(req)
providers = json.load(resp)
for p in providers.get('data', []):
    if 'openai_api_compatible' in p.get('provider', ''):
        print(f'Provider: {p["provider"]}')
        print(f'  configured: {p.get("is_valid", False)}')
        print(f'  system_configuration_status: {p.get("system_configuration_status", "N/A")}')
        print(f'  quota_configuration_status: {p.get("quota_configuration_status", "N/A")}')
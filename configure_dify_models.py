import urllib.request, json, base64

base_url = "http://10.167.2.176:30501"
email = "myuwei@126.com"
password = "difyai123456"

# Login
encoded_password = base64.b64encode(password.encode()).decode()
data = json.dumps({"email": email, "password": encoded_password}).encode()
req = urllib.request.Request(
    f"{base_url}/console/api/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
result = json.load(resp)
token = result.get('access_token', '')
print(f"Login OK. Token: {token[:40]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 1: Get model providers to find the correct provider name
req = urllib.request.Request(
    f"{base_url}/console/api/workspaces/current/model-providers",
    headers=headers
)
resp = urllib.request.urlopen(req)
providers = json.load(resp)
print(f"\nAvailable providers ({len(providers.get('data', []))}):")
openai_compat = None
for p in providers.get('data', []):
    name = p.get('provider', '')
    print(f"  - {name}: {p.get('provider_name', '')}")
    if 'openai_api_compatible' in name:
        openai_compat = p
        print(f"    -> THIS IS OUR TARGET")

if not openai_compat:
    print("\nNo openai_api_compatible provider found! Checking alternatives...")
    for p in providers.get('data', []):
        if 'openai' in p.get('provider', '').lower():
            print(f"  Candidate: {p.get('provider')}")

# Step 2: Save credentials for the provider
print("\n--- Saving credentials ---")
creds = {
    "credentials": {
        "api_key": "sk-ai-platform-master",
        "endpoint_url": "http://litellm.ai-platform.svc.cluster.local:4000/v1"
    }
}
data = json.dumps(creds).encode()
req = urllib.request.Request(
    f"{base_url}/console/api/workspaces/current/model-providers/openai_api_compatible/credentials",
    data=data,
    headers=headers
)
try:
    resp = urllib.request.urlopen(req)
    print(f"Credentials saved: {resp.read().decode()[:300]}")
except urllib.error.HTTPError as e:
    print(f"Credentials error: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Step 3: List available models from the provider
print("\n--- Available models from provider ---")
req = urllib.request.Request(
    f"{base_url}/console/api/workspaces/current/model-providers/openai_api_compatible/models",
    headers=headers
)
try:
    resp = urllib.request.urlopen(req)
    models = json.load(resp)
    print(f"Models: {json.dumps(models, indent=2)[:1000]}")
except urllib.error.HTTPError as e:
    print(f"Models error: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Step 4: Try to add custom models
print("\n--- Adding custom models ---")
models_to_add = [
    {"model": "qwen2.5:14b", "model_type": "llm"},
    {"model": "deepseek-r1:14b", "model_type": "llm"},
    {"model": "qwen2.5:7b", "model_type": "llm"},
    {"model": "qwen2.5-coder:14b", "model_type": "llm"},
    {"model": "bge-m3", "model_type": "text-embedding"},
]

for m in models_to_add:
    data = json.dumps(m).encode()
    req = urllib.request.Request(
        f"{base_url}/console/api/workspaces/current/model-providers/openai_api_compatible/models",
        data=data,
        headers=headers,
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.load(resp)
        print(f"  Added {m['model']}: {result.get('result', 'unknown')}")
    except urllib.error.HTTPError as e:
        print(f"  Failed {m['model']}: {e.code} - {e.read().decode()[:200]}")
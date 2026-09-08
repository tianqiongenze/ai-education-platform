import urllib.request, json, ssl

# Disable SSL verification for internal cluster communication
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = "http://10.167.2.176:30501"

# Login
data = json.dumps({"email": "myuwei@126.com", "password": "difyai123456"}).encode()
req = urllib.request.Request(
    f"{base}/console/api/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
result = json.load(resp)
print("Login SUCCESS!")
token = result.get('access_token', '')
print(f"Access token: {token[:60]}...")

# Get model providers
req2 = urllib.request.Request(
    f"{base}/console/api/workspaces/current/model-providers",
    headers={"Authorization": f"Bearer {token}"}
)
resp2 = urllib.request.urlopen(req2)
providers = json.load(resp2)
print(f"\nModel providers count: {len(providers.get('data', []))}")
for p in providers.get('data', []):
    print(f"  - {p.get('provider', 'unknown')}: {p.get('provider_name', 'unknown')}")

# Now configure the OpenAI-compatible provider
# The provider name for OpenAI API-compatible is "openai_api_compatible"
print("\n--- Configuring OpenAI API-compatible provider ---")

# First, get the provider details
req3 = urllib.request.Request(
    f"{base}/console/api/workspaces/current/model-providers/openai_api_compatible",
    headers={"Authorization": f"Bearer {token}"}
)
try:
    resp3 = urllib.request.urlopen(req3)
    provider_detail = json.load(resp3)
    print(f"Provider detail: {json.dumps(provider_detail, indent=2)[:1000]}")
except urllib.error.HTTPError as e:
    print(f"Get provider failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")

# Save credentials for the provider
credentials_data = json.dumps({
    "credentials": {
        "api_key": "sk-ai-platform-master",
        "endpoint_url": "http://litellm.ai-platform.svc.cluster.local:4000/v1"
    }
}).encode()

req4 = urllib.request.Request(
    f"{base}/console/api/workspaces/current/model-providers/openai_api_compatible/credentials",
    data=credentials_data,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)
try:
    resp4 = urllib.request.urlopen(req4)
    cred_result = json.load(resp4)
    print(f"\nCredentials saved: {json.dumps(cred_result, indent=2)[:500]}")
except urllib.error.HTTPError as e:
    print(f"\nSave credentials failed: {e.code}")
    body = e.read().decode()
    print(f"Body: {body[:500]}")
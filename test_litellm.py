import urllib.request, json
API_KEY = "sk-ai-platform-master"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

# Test models endpoint
req = urllib.request.Request(
    "http://10.167.2.175:30083/v1/models",
    headers=HEADERS
)
resp = urllib.request.urlopen(req)
data = json.load(resp)
print("Available models:")
for m in data.get("data", []):
    print(f"  - {m['id']}")

# Test a simple completion (qwen2.5:7b is small, should be fast)
print("\nTesting chat completion (qwen2.5:7b)...")
req = urllib.request.Request(
    "http://10.167.2.175:30083/v1/chat/completions",
    data=json.dumps({
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": "Say hello in 3 words"}],
        "max_tokens": 20
    }).encode(),
    headers=HEADERS
)
resp = urllib.request.urlopen(req, timeout=120)
result = json.load(resp)
print(f"Response: {result['choices'][0]['message']['content']}")
print("LITELLM TEST PASSED!")

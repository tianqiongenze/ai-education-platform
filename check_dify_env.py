import os
for k in sorted(os.environ.keys()):
    kl = k.lower()
    if any(x in kl for x in ['openai', 'model', 'llm', 'provider', 'ollama', 'litellm', 'api_base', 'api_key']):
        v = os.environ[k]
        print(f'{k}={v[:80]}')
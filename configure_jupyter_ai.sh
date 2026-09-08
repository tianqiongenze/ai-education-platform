#!/bin/bash
# Configure jupyter-ai to use Ollama/LiteLLM as the LLM backend
set -e

echo "=== 1. Create jupyter-ai config ==="

# jupyter-ai 3.x uses a config file to specify the model
# Format: c.ChatOpenAI.model = "..." etc.
# Since we have Ollama and LiteLLM, we'll configure both

# Create the config file
cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'EOF'
# Jupyter AI Configuration
# Using LiteLLM proxy as OpenAI-compatible endpoint
# LiteLLM provides access to all models (qwen2.5, deepseek-r1, etc.)

# OpenAI-compatible endpoint via LiteLLM
import os

# Set API key for LiteLLM (LiteLLM doesn't require a real key, but jupyter-ai needs one)
os.environ["OPENAI_API_KEY"] = "sk-anything"
os.environ["OPENAI_API_BASE"] = "http://10.108.11.54:4000/v1"

# Configure the chat model
c = get_config()  # noqa: F821

# Use qwen2.5:7b via LiteLLM (OpenAI-compatible)
c.AiProvider.model_id = "qwen2.5:7b"
c.AiProvider.api_base = "http://10.108.11.54:4000/v1"
c.AiProvider.api_key = "sk-anything"
EOF

echo "Config file created: /home/jovyan/.jupyter/jupyter_ai_config.py"
cat /home/jovyan/.jupyter/jupyter_ai_config.py

echo ""
echo "=== 2. Also create JSON config (fallback) ==="
cat > /home/jovyan/.jupyter/jupyter_ai_config.json << 'EOF'
{
  "model_id": "qwen2.5:7b",
  "model_provider": "openai",
  "api_base": "http://10.108.11.54:4000/v1",
  "api_key": "sk-anything",
  "send_with_shift_enter": true,
  "auto_scroll": true,
  "system_prompt": "You are an expert Python programming teacher. Help students write clean, well-documented code. When asked to create projects, generate complete file structures with all necessary code."
}
EOF

echo "JSON config created"
cat /home/jovyan/.jupyter/jupyter_ai_config.json

echo ""
echo "=== 3. Test LiteLLM chat completion ==="
python3 << 'PYEOF'
import urllib.request, json

# Test chat completion via LiteLLM
payload = json.dumps({
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "Say 'Hello, Jupyter AI is working!' in one sentence."}],
    "max_tokens": 50,
    "temperature": 0.7
}).encode()

req = urllib.request.Request(
    "http://10.108.11.54:4000/v1/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-anything"
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("LiteLLM chat test: SUCCESS")
    print("Response:", content[:200])
except Exception as e:
    print("LiteLLM chat test FAILED:", e)

# Also test direct Ollama
print("\n--- Testing direct Ollama ---")
payload2 = json.dumps({
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "Say 'Hello!' in one sentence."}],
    "stream": False
}).encode()

req2 = urllib.request.Request(
    "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1/chat/completions",
    data=payload2,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-anything"
    }
)

try:
    resp2 = urllib.request.urlopen(req2, timeout=60)
    data2 = json.loads(resp2.read())
    content2 = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("Ollama chat test: SUCCESS")
    print("Response:", content2[:200])
except Exception as e:
    print("Ollama chat test FAILED:", e)
PYEOF

echo ""
echo "=== 4. Verify jupyter-ai can load the config ==="
python3 << 'PYEOF'
try:
    import jupyter_ai
    print("jupyter-ai version:", jupyter_ai.__version__)
    
    # Check if config is loadable
    import os
    config_path = os.path.expanduser("~/.jupyter/jupyter_ai_config.py")
    if os.path.exists(config_path):
        print("Config file exists at:", config_path)
    else:
        print("Config file NOT found at:", config_path)
    
    # Check available providers
    from jupyter_ai import MODELS  # noqa
    print("Available model providers loaded")
except Exception as e:
    print("jupyter-ai check error:", e)
PYEOF

echo ""
echo "=== DONE ==="
echo "Please restart the JupyterLab server (Kernel -> Restart, or log out and back in)"
echo "Then try typing a message in the jupyter-ai chat panel."

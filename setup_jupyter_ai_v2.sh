#!/bin/bash
# Configure jupyter-ai for the teacher pod
# Points to Ollama OpenAI-compatible endpoint with correct model names
# Sets environment variables for proper jupyter-ai 3.x configuration
set -e

echo "=== 1. Set environment variables for jupyter-ai ==="

# jupyter-ai 3.x reads model config from environment
# Ollama provides an OpenAI-compatible endpoint at /v1/chat/completions
cat >> /home/jovyan/.bashrc << 'EOF'

# Jupyter AI configuration
export OPENAI_API_KEY="ollama"
export OPENAI_API_BASE="http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
export OPENAI_BASE_URL="http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
export JUPYTER_AI_MODEL_ID="qwen2.5-coder:7b"
export JUPYTER_AI_MODEL_PROVIDER="openai"
EOF

echo "Environment variables added to .bashrc"

echo ""
echo "=== 2. Create jupyter_ai_config.py (proper format for jupyter-ai 3.x) ==="

cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'PYEOF'
import os

# Ollama OpenAI-compatible endpoint
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_API_BASE"] = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
os.environ["OPENAI_BASE_URL"] = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"

c = get_config()  # noqa: F821

# Configure the AI provider to use Ollama via OpenAI-compatible API
# Model: qwen2.5-coder:7b (good for code generation)
c.AiProvider.model_id = "qwen2.5-coder:7b"
c.AiProvider.api_base = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
c.AiProvider.api_key = "ollama"
PYEOF

echo "Config written: /home/jovyan/.jupyter/jupyter_ai_config.py"
cat /home/jovyan/.jupyter/jupyter_ai_config.py

echo ""
echo "=== 3. Create alternative config with smaller model ==="
cat > /home/jovyan/.jupyter/jupyter_ai_config_tiny.py << 'PYEOF'
import os
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_API_BASE"] = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
c = get_config()  # noqa: F821
# Use tinyllama for faster response (lower quality but works on busy CPU)
c.AiProvider.model_id = "tinyllama:latest"
c.AiProvider.api_base = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
c.AiProvider.api_key = "ollama"
PYEOF
echo "Alternative config (tinyllama) written"

echo ""
echo "=== 4. Also create LiteLLM-based config ==="
cat > /home/jovyan/.jupyter/jupyter_ai_config_litellm.py << 'PYEOF'
import os
os.environ["OPENAI_API_KEY"] = "sk-ai-platform-master"
os.environ["OPENAI_API_BASE"] = "http://10.108.11.54:4000/v1"
c = get_config()  # noqa: F821
c.AiProvider.model_id = "qwen2.5-coder:7b"
c.AiProvider.api_base = "http://10.108.11.54:4000/v1"
c.AiProvider.api_key = "sk-ai-platform-master"
PYEOF
echo "LiteLLM config written"

echo ""
echo "=== 5. Test the OpenAI-compatible endpoint ==="
python3 << 'PYTEST'
import urllib.request, json, urllib.error

# Test Ollama OpenAI-compat endpoint with correct model name
model = "qwen2.5-coder:7b"
print("Testing model: %s" % model)
payload = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Write a Python function that adds two numbers. Return only the code."}],
    "max_tokens": 100,
    "temperature": 0.7
}).encode()

req = urllib.request.Request(
    "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1/chat/completions",
    data=payload,
    headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"}
)

try:
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("SUCCESS! Response (%d chars):" % len(content))
    print(content[:300])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")[:300]
    print("FAILED: HTTP %d - %s" % (e.code, body))
except Exception as e:
    print("FAILED: %s" % str(e)[:200])
PYTEST

echo ""
echo "=== DONE ==="
echo ""
echo "IMPORTANT: To use jupyter-ai:"
echo "1. Log out and log back in (or restart the JupyterLab server)"
echo "2. The AI chat panel should now be configured"
echo "3. If Ollama is busy, responses may take 30-60 seconds or fail"
echo "4. Use the alternative config (tinyllama) for faster but lower quality responses:"
echo "   cp ~/.jupyter/jupyter_ai_config_tiny.py ~/.jupyter/jupyter_ai_config.py"
echo "5. Use the LiteLLM config if Ollama is unavailable:"
echo "   cp ~/.jupyter/jupyter_ai_config_litellm.py ~/.jupyter/jupyter_ai_config.py"

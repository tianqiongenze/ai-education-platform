#!/bin/bash
# Fix: put all handler code directly in __init__.py
set -e

echo "=== Fix server extension package ==="
# Write __init__.py directly with all the handler code
cat > /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion/__init__.py << 'PYEOF'
"""jupyter_inline_completion - AI inline (ghost text) completion server extension."""
import hashlib
import json
import time
import urllib.request
import urllib.error
import os
import threading
from collections import OrderedDict

from tornado import web
from jupyter_server.base.handlers import APIHandler

OLLAMA_URL = os.environ.get("INLINE_OLLAMA_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
OLLAMA_MODEL = os.environ.get("INLINE_OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_TIMEOUT = float(os.environ.get("INLINE_OLLAMA_TIMEOUT", "3.0"))
CACHE_MAX = int(os.environ.get("INLINE_CACHE_MAX", "2000"))
REDIS_URL = os.environ.get("INLINE_REDIS_URL", "redis://:difyai123456@redis.dify-plus.svc.cluster.local:6379/6")

_cache = OrderedDict()
_cache_lock = threading.Lock()

def _cache_key(prefix, suffix, language, max_tokens):
    raw = f"{language}:{max_tokens}:{prefix}|{suffix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def _cache_get(key):
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    return None

def _cache_put(key, value):
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)

_redis_client = None
def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, socket_timeout=0.5, socket_connect_timeout=0.5)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None

def _redis_get(key):
    r = _get_redis()
    if r is None:
        return None
    try:
        val = r.get(f"fim:{key}")
        return val.decode() if val else None
    except Exception:
        return None

def _redis_put(key, value):
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(f"fim:{key}", 3600, value)
    except Exception:
        pass

WARM_CACHE = {
    "def fibonacci": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "def factorial": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "def is_prime": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0:\n            return False\n    return True",
    "import pandas": "import pandas as pd\nimport numpy as np",
    "import numpy": "import numpy as np",
    "import matplotlib": "import matplotlib.pyplot as plt",
    "from sklearn": "from sklearn.model_selection import train_test_split\nfrom sklearn.metrics import accuracy_score",
    "def __init__": "def __init__(self, *args, **kwargs):\n    super().__init__(*args, **kwargs)",
    "def main():": "def main():\n    pass\n\nif __name__ == '__main__':\n    main()",
    "if __name__": "if __name__ == '__main__':\n    main()",
    "try:": "try:\n    pass\nexcept Exception as e:\n    print(f'Error: {e}')",
    "for i in range": "for i in range(len(data)):\n    item = data[i]",
    "with open": "with open(filename, 'r') as f:\n    content = f.read()",
    "def read_csv": "def read_csv(path):\n    import pandas as pd\n    return pd.read_csv(path)",
    "def save_csv": "def save_csv(df, path):\n    df.to_csv(path, index=False)",
    "public static void main": "public static void main(String[] args) {\n    System.out.println(\"Hello, World!\");\n}",
    "func main()": "func main() {\n    fmt.Println(\"Hello, World!\")\n}",
    "package main": "package main\n\nimport (\n    \"fmt\"\n)",
    "fn main()": "fn main() {\n    println!(\"Hello, World!\");\n}",
    "use std::": "use std::collections::HashMap;",
}

for prefix, completion in WARM_CACHE.items():
    _cache_put(_cache_key(prefix, "", "python", 32), completion)

def _call_ollama_fim(prefix, suffix, max_tokens):
    prompt = f"<|fim_begin|>{prefix}<|fim_hole|>{suffix}<|fim_end|>"
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "raw": True,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.2,
            "stop": ["\n\n", "\nclass ", "\ndef ", "\nfunc "]
        }
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT)
        data = json.loads(resp.read())
        return data.get("response", "").strip()
    except Exception:
        return ""

class InlineCompletionHandler(APIHandler):
    @web.authenticated
    async def post(self):
        body = json.loads(self.request.body)
        prefix = body.get("prefix", "")
        suffix = body.get("suffix", "")
        language = body.get("language", "python")
        max_tokens = body.get("max_tokens", 32)

        key = _cache_key(prefix, suffix, language, max_tokens)

        suggestion = _cache_get(key)
        if suggestion:
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({"suggestion": suggestion, "source": "l1_cache"}))
            return

        suggestion = _redis_get(key)
        if suggestion:
            _cache_put(key, suggestion)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({"suggestion": suggestion, "source": "l2_cache"}))
            return

        import asyncio
        loop = asyncio.get_event_loop()
        suggestion = await loop.run_in_executor(
            None, _call_ollama_fim, prefix, suffix, max_tokens
        )

        if suggestion:
            _cache_put(key, suggestion)
            _redis_put(key, suggestion)

        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({"suggestion": suggestion, "source": "ollama" if suggestion else "miss"}))

class InlineCompletionStatsHandler(APIHandler):
    @web.authenticated
    async def get(self):
        with _cache_lock:
            l1_size = len(_cache)
        r = _get_redis()
        l2_size = 0
        if r:
            try:
                l2_size = len(r.keys("fim:*"))
            except Exception:
                pass
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({
            "l1_cache_size": l1_size,
            "l2_cache_size": l2_size,
            "warm_cache_entries": len(WARM_CACHE),
            "ollama_url": OLLAMA_URL,
            "ollama_model": OLLAMA_MODEL
        }))

def _url_join(base, path):
    if base.endswith("/") and path.startswith("/"):
        return base + path[1:]
    elif not base.endswith("/") and not path.startswith("/"):
        return base + "/" + path
    return base + path

def _load_jupyter_server_extension(server_app):
    web_app = server_app.web_app
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    from tornado.web import url
    web_app.add_handlers(host_pattern, [
        (_url_join(base_url, "/inline-completion/v1/completion"), InlineCompletionHandler),
        (_url_join(base_url, "/inline-completion/v1/stats"), InlineCompletionStatsHandler),
    ])
    server_app.log.info("jupyter_inline_completion: handlers registered")

def _jupyter_server_extension_points():
    return [{"module": "jupyter_inline_completion"}]
PYEOF

# Remove the broken _handler.py
rm -f /home/jovyan/work/jupyter-inline-completion/jupyter_inline_completion/_handler.py

# Reinstall
cd /home/jovyan/work/jupyter-inline-completion
pip install -e . --no-deps 2>&1 | tail -3

echo ""
echo "=== Validate server extension ==="
python3 -c "import jupyter_inline_completion; print('import OK'); print('ext points:', jupyter_inline_completion._jupyter_server_extension_points())" 2>&1

echo ""
echo "=== Enable server extension ==="
jupyter server extension enable --py jupyter_inline_completion 2>&1 | tail -5
jupyter server extension list 2>&1 | grep inline

echo ""
echo "=== Now build labextension ==="
cd /home/jovyan/work/jupyter-inline-completion
jlpm install 2>&1 | tail -5
echo "--- Building TS ---"
jlpm run build:ts 2>&1 | tail -10
echo "--- Building labext ---"
jlpm run build:labext 2>&1 | tail -10

echo ""
echo "=== Install labextension ==="
jupyter labextension install --no-build . 2>&1 | tail -5

echo ""
echo "=== Build JupyterLab ==="
jupyter lab build --minimize=False 2>&1 | tail -10

echo ""
echo "=== Verify ==="
jupyter labextension list 2>&1 | grep -i inline || echo "labext not found"
jupyter server extension list 2>&1 | grep inline || echo "server ext not found"

echo "=== DONE ==="

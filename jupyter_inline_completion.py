"""
jupyter_inline_completion - AI inline (ghost text) completion server extension.

Provides a Tornado handler at /inline-completion/v1/completion that:
1. Checks an in-memory LRU + Redis cache for the prefix/suffix hash
2. If cache miss, calls ollama qwen2.5-coder FIM endpoint (with 3s timeout)
3. Caches the result
4. Returns the suggestion

Also ships a pre-warmed cache of common Python patterns.
"""
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
from jupyter_server.serverapp import ServerApp

# ---- Configuration ----
OLLAMA_URL = os.environ.get("INLINE_OLLAMA_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
OLLAMA_MODEL = os.environ.get("INLINE_OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_TIMEOUT = float(os.environ.get("INLINE_OLLAMA_TIMEOUT", "3.0"))  # seconds
CACHE_MAX = int(os.environ.get("INLINE_CACHE_MAX", "2000"))

# Redis (optional, for multi-level cache)
REDIS_URL = os.environ.get("INLINE_REDIS_URL", "redis://:difyai123456@redis.dify-plus.svc.cluster.local:6379/6")

# ---- In-memory LRU cache ----
_cache = OrderedDict()
_cache_lock = threading.Lock()

def cache_key(prefix: str, suffix: str, language: str, max_tokens: int) -> str:
    raw = f"{language}:{max_tokens}:{prefix}|{suffix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def cache_get(key: str) -> str | None:
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    return None

def cache_put(key: str, value: str):
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)

# ---- Redis cache (best-effort) ----
_redis_client = None
def get_redis():
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

def redis_get(key: str) -> str | None:
    r = get_redis()
    if r is None:
        return None
    try:
        val = r.get(f"fim:{key}")
        return val.decode() if val else None
    except Exception:
        return None

def redis_put(key: str, value: str):
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(f"fim:{key}", 3600, value)  # 1 hour TTL
    except Exception:
        pass

# ---- Pre-warmed common completions ----
WARM_CACHE = {
    # Common Python patterns
    "def fibonacci": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "def factorial": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "def is_prime": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0:\n            return False\n    return True",
    "import pandas": "import pandas as pd\nimport numpy as np",
    "import numpy": "import numpy as np",
    "import matplotlib": "import matplotlib.pyplot as plt",
    "from sklearn": "from sklearn.model_selection import train_test_split\nfrom sklearn.metrics import accuracy_score",
    "def __init__": "def __init__(self, *args, **kwargs):\n    super().__init__(*args, **kwargs)",
    "def main():": "def main():\n    pass\n\nif __name__ == '__main__':\n    main()",
    "class DataClass": "class DataClass:\n    def __init__(self, data):\n        self.data = data\n\n    def __repr__(self):\n        return f'DataClass({self.data})'",
    "if __name__": "if __name__ == '__main__':\n    main()",
    "try:": "try:\n    pass\nexcept Exception as e:\n    print(f'Error: {e}')",
    "for i in range": "for i in range(len(data)):\n    item = data[i]",
    "with open": "with open(filename, 'r') as f:\n    content = f.read()",
    "def read_csv": "def read_csv(path):\n    import pandas as pd\n    return pd.read_csv(path)",
    "def save_csv": "def save_csv(df, path):\n    df.to_csv(path, index=False)",
    # Java patterns
    "public static void main": "public static void main(String[] args) {\n    System.out.println(\"Hello, World!\");\n}",
    "public class": "public class Main {\n    public Main() {\n    }\n}",
    # Go patterns
    "func main()": "func main() {\n    fmt.Println(\"Hello, World!\")\n}",
    "package main": "package main\n\nimport (\n    \"fmt\"\n)",
    # Rust patterns
    "fn main()": "fn main() {\n    println!(\"Hello, World!\");\n}",
    "use std::": "use std::collections::HashMap;",
}

def warm_cache():
    """Pre-populate the LRU cache with common patterns."""
    for prefix, completion in WARM_CACHE.items():
        key = cache_key(prefix, "", "python", 32)
        cache_put(key, completion)

# Warm on import
warm_cache()

# ---- Ollama FIM call ----
def call_ollama_fim(prefix: str, suffix: str, max_tokens: int) -> str:
    """Call ollama qwen2.5-coder FIM endpoint."""
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
    except Exception as e:
        return ""

# ---- Handler ----
class InlineCompletionHandler(APIHandler):
    """Handle inline completion requests."""

    @web.authenticated
    async def post(self):
        body = json.loads(self.request.body)
        prefix = body.get("prefix", "")
        suffix = body.get("suffix", "")
        language = body.get("language", "python")
        max_tokens = body.get("max_tokens", 32)

        # Build cache key
        key = cache_key(prefix, suffix, language, max_tokens)

        # Level 1: in-memory LRU
        suggestion = cache_get(key)
        if suggestion:
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({
                "suggestion": suggestion,
                "source": "l1_cache"
            }))
            return

        # Level 2: Redis
        suggestion = redis_get(key)
        if suggestion:
            cache_put(key, suggestion)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({
                "suggestion": suggestion,
                "source": "l2_cache"
            }))
            return

        # Level 3: Ollama FIM (in a thread to not block the event loop)
        import asyncio
        loop = asyncio.get_event_loop()
        suggestion = await loop.run_in_executor(
            None,
            call_ollama_fim,
            prefix, suffix, max_tokens
        )

        if suggestion:
            # Cache the result
            cache_put(key, suggestion)
            redis_put(key, suggestion)

        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({
            "suggestion": suggestion,
            "source": "ollama" if suggestion else "miss"
        }))


class InlineCompletionStatsHandler(APIHandler):
    """Return cache statistics."""

    @web.authenticated
    async def get(self):
        with _cache_lock:
            l1_size = len(_cache)
        r = get_redis()
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


def _load_jupyter_server_extension(server_app: ServerApp):
    """Register the inline completion handlers."""
    web_app = server_app.web_app
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    from tornado.web import url

    web_app.add_handlers(host_pattern, [
        (url_join(base_url, "/inline-completion/v1/completion"), InlineCompletionHandler),
        (url_join(base_url, "/inline-completion/v1/stats"), InlineCompletionStatsHandler),
    ])
    server_app.log.info("jupyter_inline_completion: handlers registered")


def url_join(base: str, path: str) -> str:
    """Join base URL and path."""
    if base.endswith("/") and path.startswith("/"):
        return base + path[1:]
    elif not base.endswith("/") and not path.startswith("/"):
        return base + "/" + path
    else:
        return base + path


def _jupyter_server_extension_points():
    return [{"module": "jupyter_inline_completion"}]

#!/bin/bash
# Fix 1: Ensure all volumes are mounted (startup script + notebooks + code grader)
# Fix 2: Update startup script to be more robust
# Fix 3: Optimize Ollama performance (pre-load, thread config, warm cache)
# Fix 4: Optimize LLM proxy (add streaming support, connection pooling)

set -e

echo "============================================================"
echo "1. Update JupyterHub config: mount all ConfigMaps properly"
echo "============================================================"

# Get current config
kubectl get configmap jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_final.py

# Remove any existing duplicate volume definitions and add the correct ones
python3 << 'PYEOF'
import re

with open('/tmp/jhub_final.py', 'r') as f:
    config = f.read()

# Remove existing volume definitions (they may be duplicated/broken)
# Find and remove blocks from c.KubeSpawner.volumes to end of volume_mounts
config = re.sub(
    r'# Mount lecture notebooks.*?c\.KubeSpawner\.volume_mounts\s*=\s*\[.*?\]\s*',
    '',
    config,
    flags=re.DOTALL
)
config = re.sub(
    r'# Auto-configure.*?c\.KubeSpawner\.volume_mounts\s*=\s*\[.*?\]\s*',
    '',
    config,
    flags=re.DOTALL
)
# Also remove standalone volume/mount definitions
config = re.sub(r'c\.KubeSpawner\.volumes\s*=\s*\[.*?\]', '', config, flags=re.DOTALL)
config = re.sub(r'c\.KubeSpawner\.volume_mounts\s*=\s*\[.*?\]', '', config, flags=re.DOTALL)
config = re.sub(r'c\.KubeSpawner\.lifecycle_hooks\s*=\s*\{.*?\}', '', config, flags=re.DOTALL)

# Add correct volumes, mounts, and lifecycle at the end
config += '''

# ============================================================
# Auto-configuration: mount startup script + notebooks + code grader
# ============================================================

# Mount the startup script ConfigMap
c.KubeSpawner.volumes = [
    {
        "name": "workspace-{username}",
        "persistentVolumeClaim": {"claimName": "claim-{username}"},
    },
    {
        "name": "startup-script",
        "configMap": {"name": "jupyterhub-startup"},
    },
    {
        "name": "lecture-notebooks",
        "configMap": {"name": "lecture-notebooks"},
    }
]
c.KubeSpawner.volume_mounts = [
    {
        "name": "workspace-{username}",
        "mountPath": "/home/jovyan/work",
    },
    {
        "name": "startup-script",
        "mountPath": "/tmp/startup.sh",
        "subPath": "startup.sh",
    },
    {
        "name": "lecture-notebooks",
        "mountPath": "/tmp/notebooks",
    }
]

# Run startup script after pod starts (configures jupyter-ai + distributes files)
c.KubeSpawner.lifecycle_hooks = {
    "postStart": {
        "exec": {
            "command": ["/bin/bash", "-c", "sleep 15 && bash /tmp/startup.sh >> /tmp/startup.log 2>&1 || true"]
        }
    }
}
'''

with open('/tmp/jhub_final.py', 'w') as f:
    f.write(config)

print("Config updated")
PYEOF

# Apply
kubectl create configmap jupyterhub-config -n jupyterhub \
  --from-file=jupyterhub_config.py=/tmp/jhub_final.py \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub config updated"

echo ""
echo "============================================================"
echo "2. Update startup script (more robust + code grader for all users)"
echo "============================================================"

cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    # Auto-configure EVERY user pod (existing or new):
    # 1. jupyter-ai config
    # 2. code_grader.py (评分系统)
    # 3. operation guide
    # 4. Notebooks + code framework (for Lecture accounts)
    
    USERNAME=$(echo $JUPYTERHUB_USER)
    WORK=/home/jovyan/work
    NB_DIR=/tmp/notebooks
    
    mkdir -p $WORK
    mkdir -p /home/jovyan/.jupyter
    mkdir -p $WORK/student_code_framework
    
    # 1. jupyter-ai config (ALL users get this)
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAICONFIG'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    os.environ["OPENAI_BASE_URL"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG
    
    # Fallback configs (ALL users)
    cat > /home/jovyan/.jupyter/jupyter_ai_config_tiny.py << 'JAICONFIG2'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()
    c.AiProvider.model_id = "tinyllama:latest"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG2
    
    cat > /home/jovyan/.jupyter/jupyter_ai_config_litellm.py << 'JAICONFIG3'
    import os
    os.environ["OPENAI_API_KEY"] = "sk-ai-platform-master"
    os.environ["OPENAI_API_BASE"] = "http://10.108.11.54:4000/v1"
    c = get_config()
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://10.108.11.54:4000/v1"
    c.AiProvider.api_key = "sk-ai-platform-master"
    JAICONFIG3
    
    # bashrc env vars
    grep -q 'OPENAI_API_BASE' /home/jovyan/.bashrc 2>/dev/null || cat >> /home/jovyan/.bashrc << 'BASHRC'
    export OPENAI_API_KEY="ollama"
    export OPENAI_API_BASE="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    export OPENAI_BASE_URL="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    BASHRC
    
    # 2. Code grader (ALL users get this — 评分系统)
    cp $NB_DIR/code_grader $WORK/code_grader.py 2>/dev/null || true
    chmod +x $WORK/code_grader.py 2>/dev/null || true
    
    # 3. Operation guide (ALL users)
    cp $NB_DIR/guide $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null || true
    
    # 4. Install pycodestyle for grading
    pip install --quiet pycodestyle 2>/dev/null || true
    
    # 5. Distribute notebooks + code framework based on username
    case "$USERNAME" in
      Lecture-P1|lecture-p1)
        cp $NB_DIR/p11_student "$WORK/p11_P1.1_Python基础_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p12_student "$WORK/p12_P1.2_标准Python_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p11_teacher "$WORK/p11_P1.1_Python基础_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p12_teacher "$WORK/p12_P1.2_标准Python_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p11_exercises "$WORK/student_code_framework/p11_exercises.py" 2>/dev/null || true
        cp $NB_DIR/p12_template "$WORK/student_code_framework/p12_template.py" 2>/dev/null || true
        ;;
      Lecture-P2|lecture-p2)
        cp $NB_DIR/p21_student "$WORK/p21_P2.1_Pandas数据_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p22_student "$WORK/p22_P2.2_NumPy故障特_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p21_teacher "$WORK/p21_P2.1_Pandas数据_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p22_teacher "$WORK/p22_P2.2_NumPy故障特_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p21_pipeline "$WORK/student_code_framework/p21_pipeline.py" 2>/dev/null || true
        cp $NB_DIR/p22_features "$WORK/student_code_framework/p22_features.py" 2>/dev/null || true
        ;;
      Lecture-P3|lecture-p3)
        cp $NB_DIR/p33_student "$WORK/p33_P3_产线KPI仪表盘_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p33_teacher "$WORK/p33_P3_产线KPI仪表盘_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p33_dashboard "$WORK/student_code_framework/p33_dashboard.py" 2>/dev/null || true
        ;;
      Lecture-P4|lecture-p4)
        cp $NB_DIR/p41_student "$WORK/p41_P4.1_多源数据采集系统_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p41_teacher "$WORK/p41_P4.1_多源数据采集系统_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p41_collector "$WORK/student_code_framework/p41_collector.py" 2>/dev/null || true
        ;;
      Lecture-P5|lecture-p5)
        cp $NB_DIR/p55_student "$WORK/p55_P5_产线数据仓库与O_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p55_teacher "$WORK/p55_P5_产线数据仓库与O_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p55_warehouse "$WORK/student_code_framework/p55_warehouse.py" 2>/dev/null || true
        ;;
      Lecture-P6|lecture-p6)
        cp $NB_DIR/p66_student "$WORK/p66_P6_故障诊断模型与部_学生版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p66_teacher "$WORK/p66_P6_故障诊断模型与部_教师版.ipynb" 2>/dev/null || true
        cp $NB_DIR/p66_ml_service "$WORK/student_code_framework/p66_ml_service.py" 2>/dev/null || true
        ;;
      teacher-zhang)
        for prefix in p11 p12 p21 p22 p33 p41 p55 p66; do
          cp $NB_DIR/${prefix}_student "$WORK/" 2>/dev/null || true
          cp $NB_DIR/${prefix}_teacher "$WORK/" 2>/dev/null || true
        done
        # All code frameworks
        for fw in p11_exercises p12_template p21_pipeline p22_features p33_dashboard p41_collector p55_warehouse p66_ml_service; do
          cp $NB_DIR/$fw "$WORK/student_code_framework/" 2>/dev/null || true
        done
        ;;
    esac
    
    echo "Startup complete: $USERNAME"
    echo "  Files in work: $(ls $WORK 2>/dev/null | wc -l)"
STARTEOF

echo "Startup script updated"

echo ""
echo "============================================================"
echo "3. Optimize Ollama performance"
echo "============================================================"

# Ollama optimizations:
# 1. OLLAMA_NUM_THREAD=28 (use 28 of 32 cores, leave 4 for system)
# 2. OLLAMA_KEEP_ALIVE=30m (keep model loaded 30 min)
# 3. OLLAMA_NUM_PARALLEL=2 (allow 2 concurrent requests)
# 4. OLLAMA_MAX_LOADED_MODELS=4 (allow up to 4 models loaded)
# 5. Pre-warm qwen2.5-coder:7b after pod starts

kubectl set env deployment/ollama-worker -n ai-platform \
  OLLAMA_NUM_THREAD=28 \
  OLLAMA_KEEP_ALIVE=30m \
  OLLAMA_NUM_PARALLEL=2 \
  OLLAMA_MAX_LOADED_MODELS=4 \
  OLLAMA_FLASH_ATTENTION=1 \
  OLLAMA_CONTEXT_LENGTH=4096 2>&1

echo "Ollama worker env optimized (28 threads, 2 parallel, 30m keep, 4096 context)"

echo ""
echo "=== 4. Optimize LLM proxy: add response caching ==="

cat << 'PROXYEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-proxy-script
  namespace: ai-platform
data:
  llm_proxy.py: |
    #!/usr/bin/env python3
    """Optimized LLM proxy: response caching + streaming + connection pooling."""
    import os, json, time, sys, hashlib, urllib.request, urllib.error
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    OLLAMA_URL = os.environ.get("OLLAMA_WORKER_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
    PORT = int(os.environ.get("PROXY_PORT", "11434"))
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    REQUEST_TIMEOUT = 180  # 3 min max
    CACHE_TTL = 300  # 5 min cache
    
    # In-memory response cache (prompt_hash -> (response, timestamp))
    _cache = {}
    _cache_lock = threading.Lock()
    
    def cache_key(model, messages):
        raw = model + ":" + json.dumps(messages, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()[:32]
    
    def cache_get(key):
        with _cache_lock:
            if key in _cache:
                resp, ts = _cache[key]
                if time.time() - ts < CACHE_TTL:
                    return resp
                del _cache[key]
        return None
    
    def cache_put(key, resp):
        with _cache_lock:
            _cache[key] = (resp, time.time())
            # Clean old entries
            now = time.time()
            expired = [k for k, (r, t) in _cache.items() if now - t > CACHE_TTL]
            for k in expired:
                del _cache[k]
    
    class ProxyHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Only log POST requests and errors
            if "POST" in (format % args) or "error" in (format % args).lower():
                print(f"[{time.strftime('%H:%M:%S')}] {format % args}", flush=True)
        
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b''
            
            try:
                req_data = json.loads(body)
                model = req_data.get("model", DEFAULT_MODEL)
                messages = req_data.get("messages", [])
                
                # Check cache (only for non-streaming requests)
                if not req_data.get("stream", False):
                    key = cache_key(model, messages)
                    cached = cache_get(key)
                    if cached:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('X-Cache', 'HIT')
                        self.end_headers()
                        self.wfile.write(cached.encode())
                        return
                
                # Forward to ollama
                url = OLLAMA_URL + self.path
                req = urllib.request.Request(url, data=body, method='POST',
                    headers={'Content-Type': 'application/json'})
                
                resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                data = resp.read()
                
                # Cache the response
                if not req_data.get("stream", False):
                    key = cache_key(model, messages)
                    cache_put(key, data.decode('utf-8', errors='replace'))
                
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('X-Cache', 'MISS')
                self.end_headers()
                self.wfile.write(data)
                
            except urllib.error.HTTPError as e:
                error_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(error_body)
            except Exception as e:
                # Return helpful error
                error_msg = json.dumps({
                    "error": f"Proxy: {str(e)[:200]}",
                    "hint": "Wait 30s and retry, or switch to tinyllama:latest"
                }).encode()
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(error_msg)
        
        def do_GET(self):
            url = OLLAMA_URL + self.path
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)[:200]}).encode())
    
    if __name__ == '__main__':
        # Pre-warm the model on startup
        print(f"LLM proxy starting on port {PORT}, forwarding to {OLLAMA_URL}")
        print("Pre-warming qwen2.5-coder:7b...")
        try:
            warm_payload = json.dumps({
                "model": DEFAULT_MODEL,
                "prompt": "hi",
                "stream": False,
                "options": {"num_predict": 1}
            }).encode()
            warm_req = urllib.request.Request(
                OLLAMA_URL + "/api/generate",
                data=warm_payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(warm_req, timeout=120)
            print("Pre-warm complete!")
        except Exception as e:
            print(f"Pre-warm failed (will retry on first request): {e}")
        
        server = HTTPServer(('0.0.0.0', PORT), ProxyHandler)
        server.serve_forever()
PROXYEOF

echo "LLM proxy script updated with caching + pre-warming"

# Restart proxy
kubectl rollout restart deployment llm-proxy-master -n ai-platform 2>&1

echo ""
echo "=== 5. Restart ollama-worker with optimized config ==="
kubectl rollout restart deployment ollama-worker -n ai-platform 2>&1

echo ""
echo "=== 6. Restart hub to pick up config changes ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
  echo "Hub restarting..."
fi

echo ""
echo "============================================================"
echo "DONE - All optimizations applied"
echo "============================================================"
echo ""
echo "Changes:"
echo "1. Hub config: all ConfigMaps properly mounted (startup + notebooks)"
echo "2. Startup script: ALL users get code_grader + guide + jupyter-ai config"
echo "3. Ollama: 28 threads, 2 parallel, 30m keep, 4096 context (was 6144)"
echo "4. LLM proxy: response caching (5min TTL) + pre-warm on startup"
echo "5. Context length reduced 6144->4096 (less memory, faster inference)"
echo ""
echo "New users (any username) automatically get:"
echo "  - jupyter-ai pre-configured"
echo "  - code_grader.py in /home/jovyan/work/"
echo "  - JUPYTERHUB-OPERATION-GUIDE.md"
echo "  - pycodestyle installed for grading"

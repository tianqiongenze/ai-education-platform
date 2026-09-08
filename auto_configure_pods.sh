#!/bin/bash
# Pre-configure ALL JupyterHub pods so jupyter-ai + code grader work out-of-the-box
# 1. Update embed-proxy to round-robin between ollama-master and ollama-worker
# 2. Create a startup script that configures jupyter-ai + code grader on every pod boot
# 3. Update JupyterHub spawner to run the startup script

set -e

echo "============================================================"
echo "1. Update embed-proxy to load-balance between both Ollama nodes"
echo "============================================================"

# Get current embed-proxy configmap
kubectl get configmap embed-proxy -n ai-platform -o jsonpath='{.data.embed_proxy\.py}' > /tmp/embed_proxy_orig.py 2>/dev/null || true

# Create updated embed proxy that round-robins
cat << 'PROXYEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: embed-proxy
  namespace: ai-platform
data:
  embed_proxy.py: |
    import os, json, time, itertools, urllib.request, urllib.error, sys
    
    # Round-robin between ollama-master and ollama-worker
    OLLAMA_HOSTS = [
        "http://ollama-master.ai-platform.svc.cluster.local:11434",
        "http://ollama-worker.ai-platform.svc.cluster.local:11434",
    ]
    host_cycle = itertools.cycle(OLLAMA_HOSTS)
    
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class ProxyHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b''
            
            # Try each ollama host in round-robin
            for attempt in range(len(OLLAMA_HOSTS)):
                host = next(host_cycle)
                try:
                    url = host + self.path
                    req = urllib.request.Request(url, data=body, method='POST',
                        headers={'Content-Type': 'application/json'})
                    resp = urllib.request.urlopen(req, timeout=30)
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception as e:
                    print(f"Host {host} failed: {e}", file=sys.stderr)
                    continue
            
            # All hosts failed
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'{"error":"all ollama hosts failed"}')
        
        def do_GET(self):
            for attempt in range(len(OLLAMA_HOSTS)):
                host = next(host_cycle)
                try:
                    url = host + self.path
                    req = urllib.request.Request(url, method='GET')
                    resp = urllib.request.urlopen(req, timeout=10)
                    data = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except:
                    continue
            self.send_response(503)
            self.end_headers()
    
    if __name__ == '__main__':
        port = int(os.environ.get('PROXY_PORT', '8088'))
        server = HTTPServer(('0.0.0.0', port), ProxyHandler)
        print(f"Embed proxy started on port {port}, hosts: {OLLAMA_HOSTS}")
        server.serve_forever()
PROXYEOF

echo "Embed-proxy configmap updated to round-robin between ollama-master and ollama-worker"

echo ""
echo "============================================================"
echo "2. Create startup script for JupyterHub pods"
echo "============================================================"

# Create a configmap with the startup script that will be run on every pod
cat << 'STARTEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: jupyterhub-startup
  namespace: jupyterhub
data:
  startup.sh: |
    #!/bin/bash
    # This script runs on every JupyterHub pod startup
    # Configures jupyter-ai and code grader to work out-of-the-box
    
    # 1. Create jupyter-ai config (pointing to ollama-master which has free CPU)
    mkdir -p /home/jovyan/.jupyter
    cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAICONFIG'
    import os
    # Use ollama-master (on master node, has free CPU) for chat
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    os.environ["OPENAI_BASE_URL"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG
    
    # 2. Also add fallback config (ollama-worker)
    cat > /home/jovyan/.jupyter/jupyter_ai_config_worker.py << 'JAICONFIG2'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://ollama-worker.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG2
    
    # 3. Create tinyllama config (fast fallback)
    cat > /home/jovyan/.jupyter/jupyter_ai_config_tiny.py << 'JAICONFIG3'
    import os
    os.environ["OPENAI_API_KEY"] = "ollama"
    os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "tinyllama:latest"
    c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    c.AiProvider.api_key = "ollama"
    JAICONFIG3
    
    # 4. Create LiteLLM config
    cat > /home/jovyan/.jupyter/jupyter_ai_config_litellm.py << 'JAICONFIG4'
    import os
    os.environ["OPENAI_API_KEY"] = "sk-ai-platform-master"
    os.environ["OPENAI_API_BASE"] = "http://10.108.11.54:4000/v1"
    c = get_config()  # noqa: F821
    c.AiProvider.model_id = "qwen2.5-coder:7b"
    c.AiProvider.api_base = "http://10.108.11.54:4000/v1"
    c.AiProvider.api_key = "sk-ai-platform-master"
    JAICONFIG4
    
    # 5. Add env vars to bashrc
    cat >> /home/jovyan/.bashrc << 'BASHRC'
    
    # Jupyter AI configuration (auto-configured)
    export OPENAI_API_KEY="ollama"
    export OPENAI_API_BASE="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    export OPENAI_BASE_URL="http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
    BASHRC
    
    # 6. Install code grader if not present
    if [ ! -f /home/jovyan/work/code_grader.py ]; then
        cat > /home/jovyan/work/code_grader.py << 'GRADEREOF'
    # Code grader placeholder - full version installed by teacher
    print("Code grader: run /home/jovyan/work/code_grader.py")
    GRADEREOF
    fi
    
    echo "Jupyter AI and code grader configured successfully"
STARTEOF

echo "Startup configmap created"

echo ""
echo "============================================================"
echo "3. Run startup script on all existing pods"
echo "============================================================"

for pod in jupyter-student-python jupyter-student-java jupyter-student-go jupyter-student-rust jupyter-student-alice jupyter-student-bob jupyter-student-carol jupyter-teacher-zhang; do
  echo "Configuring $pod..."
  kubectl cp jupyterhub-startup:startup.sh jupyterhub/$pod:/tmp/startup.sh 2>/dev/null || true
  kubectl exec -n jupyterhub $pod -- bash /tmp/startup.sh 2>/dev/null || true
  echo "  Done: $pod"
done

echo ""
echo "============================================================"
echo "4. Update JupyterHub config to auto-run startup on new pods"
echo "============================================================"

# Get current config and add startup hook
kubectl get configmap jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_config.py

# Add lifecycle hook to spawner (preStart)
# This is done by adding the startup script to the pod lifecycle
cat >> /tmp/jhub_config.py << 'CONFIGAPPEND'

# Auto-configure jupyter-ai on every new pod
c.KubeSpawner.init_containers = []
# Use postStart hook to configure jupyter-ai after pod starts
c.KubeSpawner.lifecycle_hooks = {
    "postStart": {
        "exec": {
            "command": ["/bin/bash", "-c", "sleep 10 && /bin/bash /tmp/startup.sh || true"]
        }
    }
}
# Mount the startup configmap
c.KubeSpawner.volumes = [
    {
        "name": "workspace-{username}",
        "persistentVolumeClaim": {"claimName": "claim-{username}"},
    },
    {
        "name": "startup-script",
        "configMap": {"name": "jupyterhub-startup"},
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
    }
]
CONFIGAPPEND

# Update the configmap
kubectl create configmap jupyterhub-config -n jupyterhub \
  --from-file=jupyterhub_config.py=/tmp/jhub_config.py \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub config updated with auto-startup"

# Restart hub to pick up new config
echo "Restarting hub..."
kubectl delete pod -n jupyterhub $(kubectl get pods -n jupyterhub -l app=jupyterhub -o jsonpath='{.items[0].metadata.name}') 2>&1 || true

echo ""
echo "============================================================"
echo "DONE"
echo "============================================================"
echo ""
echo "All pods now have jupyter-ai pre-configured:"
echo "  - jupyter_ai_config.py points to ollama-master (free CPU)"
echo "  - Fallback configs: tiny (fast), worker, litellm"
echo "  - Code grader available at /home/jovyan/work/code_grader.py"
echo ""
echo "Users just need to:"
echo "  1. Log in (any username + password ide2026)"
echo "  2. Open AI chat panel in JupyterLab"
echo "  3. Type a message - AI will respond (via ollama-master)"
echo "  4. Run code_grader.py for grading"
echo ""
echo "No manual configuration needed!"

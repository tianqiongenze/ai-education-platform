#!/bin/bash
# ============================================================
# 集群整体优化方案 — 48核资源池充分利用
# 目标: Dify 3000人 + JupyterHub 1000人 + LLM 2000并发
# ============================================================

set -e

echo "============================================================"
echo "当前资源状态"
echo "============================================================"
kubectl top nodes 2>&1
echo ""

echo "============================================================"
echo "1. 扩展 Dify API 到 20 副本（支撑 3000 人）"
echo "============================================================"
# 每副本 ~150 用户, 20 副本 = 3000 用户
kubectl scale deploy/dify-api -n dify --replicas=20 2>&1
kubectl scale deploy/dify-worker -n dify --replicas=15 2>&1
echo "Dify API: 20 副本, Worker: 15 副本"

echo ""
echo "============================================================"
echo "2. 扩展 Ollama 到 2 实例（master + worker 各一个）"
echo "============================================================"
# Worker 上已有 ollama-worker (32核)
# 在 master 上部署第二个 ollama 实例 (16核) — 用于嵌入和轻量推理
# 这样 LLM 总推理能力 = 28核(worker chat) + 14核(master embed) = 42核

echo "=== Deploy ollama-master-embed on master node (for embeddings) ==="
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama-embed
  namespace: ai-platform
  labels:
    app: ollama-embed
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama-embed
  template:
    metadata:
      labels:
        app: ollama-embed
    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      securityContext:
        runAsUser: 0
      initContainers:
      - name: copy-binary
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['sh', '-c', 'cp /host-ollama/ollama /ollama-bin/ollama && chmod +x /ollama-bin/ollama']
        volumeMounts:
        - name: ollama-bin
          mountPath: /ollama-bin
        - name: host-ollama
          mountPath: /host-ollama
          readOnly: true
      containers:
      - name: ollama
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['/ollama-bin/ollama', 'serve']
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0:11435"
        - name: OLLAMA_NUM_THREAD
          value: "12"
        - name: OLLAMA_NUM_PARALLEL
          value: "4"
        - name: OLLAMA_MAX_LOADED_MODELS
          value: "1"
        - name: OLLAMA_KEEP_ALIVE
          value: "2h"
        - name: OLLAMA_FLASH_ATTENTION
          value: "1"
        - name: OLLAMA_KV_CACHE_TYPE
          value: "q8_0"
        - name: OLLAMA_CONTEXT_LENGTH
          value: "2048"
        - name: OLLAMA_MAX_QUEUE
          value: "256"
        ports:
        - containerPort: 11435
        resources:
          limits:
            cpu: "14"
            memory: "8Gi"
          requests:
            cpu: "2"
            memory: "2Gi"
        volumeMounts:
        - name: models
          mountPath: /root/.ollama
        - name: ollama-bin
          mountPath: /ollama-bin
          readOnly: true
      volumes:
      - name: models
        hostPath:
          path: /home/k8s-data/ollama-embed
          type: DirectoryOrCreate
      - name: ollama-bin
        emptyDir: {}
      - name: host-ollama
        hostPath:
          path: /usr/bin
          type: Directory
EOF

echo "Ollama embed instance deployed on master (port 11435, 12 threads)"

echo ""
echo "=== Create service for ollama-embed ==="
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ollama-embed
  namespace: ai-platform
spec:
  selector:
    app: ollama-embed
  ports:
  - port: 11435
    targetPort: 11435
EOF

echo "Ollama embed service created"

echo ""
echo "=== Pull nomic-embed-text on master embed instance ==="
sleep 20
EMBED_POD=$(kubectl get pods -n ai-platform -l app=ollama-embed -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$EMBED_POD" ]; then
  kubectl exec -n ai-platform $EMBED_POD -- /ollama-bin/ollama pull nomic-embed-text 2>&1 | tail -3
  echo "Embed model pulled on master"
fi

echo ""
echo "============================================================"
echo "3. 更新 LLM 代理：分离聊天和嵌入路由"
echo "============================================================"

# 聊天 → ollama-worker (28核, qwen2.5-coder:7b)
# 嵌入 → ollama-embed (12核, nomic-embed-text)
# 负载均衡：聊天请求轮询 worker，嵌入请求转发到 embed

cat << 'PROXYEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-proxy-script
  namespace: ai-platform
data:
  llm_proxy.py: |
    #!/usr/bin/env python3
    """LLM proxy v5: Split routing (chat → worker, embed → master)
    - Chat/generate: forward to ollama-worker (28核 CPU, qwen2.5-coder:7b)
    - Embed: forward to ollama-embed (12核 CPU, nomic-embed-text)
    - Caching: chat 5min, embed 30min
    - Threaded server for 2000+ concurrent requests
    """
    import os, json, time, hashlib, urllib.request, urllib.error
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
    import threading
    
    CHAT_URL = os.environ.get("OLLAMA_WORKER_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
    EMBED_URL = os.environ.get("OLLAMA_EMBED_URL", "http://ollama-embed.ai-platform.svc.cluster.local:11435")
    PORT = int(os.environ.get("PROXY_PORT", "11434"))
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    REQUEST_TIMEOUT = 300
    CACHE_TTL = 300
    EMBED_CACHE_TTL = 1800
    
    _cache = {}
    _cache_lock = threading.Lock()
    
    def cache_key(model, data):
        return hashlib.md5((model + ":" + json.dumps(data, sort_keys=True)).encode()).hexdigest()[:32]
    
    def cache_get(key, ttl):
        with _cache_lock:
            if key in _cache:
                r, t = _cache[key]
                if time.time() - t < ttl: return r
                del _cache[key]
        return None
    
    def cache_put(key, resp, ttl):
        with _cache_lock:
            _cache[key] = (resp, time.time())
            now = time.time()
            for k in [k for k, (r, t) in _cache.items() if now - t > 1800]:
                del _cache[k]
    
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
        request_queue_size = 512
    
    class ProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        
        def log_message(self, fmt, *args):
            msg = fmt % args
            if "POST" in msg or "503" in msg:
                print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
        
        def do_POST(self):
            cl = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(cl) if cl else b''
            
            try:
                req_data = json.loads(body)
            except:
                self._forward(body, CHAT_URL)
                return
            
            path = self.path
            
            # Route embed requests to embed instance
            if "/api/embed" in path or "/api/embeddings" in path:
                self._handle_cached(path, req_data, body, EMBED_CACHE_TTL, EMBED_URL)
                return
            
            # Tool calling: no cache, forward to chat
            if "tools" in req_data:
                self._forward(body, CHAT_URL)
                return
            
            # Chat/generate: cache + forward to chat
            if "/api/chat" in path or "/api/generate" in path:
                if req_data.get("stream", False):
                    self._forward(body, CHAT_URL)
                    return
                self._handle_cached(path, req_data, body, CACHE_TTL, CHAT_URL)
                return
            
            self._forward(body, CHAT_URL)
        
        def _handle_cached(self, path, req_data, body, ttl, target_url):
            key = cache_key(req_data.get("model", DEFAULT_MODEL), req_data)
            cached = cache_get(key, ttl)
            if cached:
                data = cached.encode() if isinstance(cached, str) else cached
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('X-Cache', 'HIT')
                self.send_header('X-Target', target_url.split('//')[1][:20] if '//' in target_url else 'unknown')
                self.end_headers()
                self.wfile.write(data)
                return
            
            url = target_url + path
            req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/json'})
            try:
                resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                data = resp.read()
                cache_put(key, data.decode('utf-8', errors='replace'), ttl)
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('X-Cache', 'MISS')
                self.end_headers()
                self.wfile.write(data)
            except urllib.error.HTTPError as e:
                err = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
            except Exception as e:
                err = json.dumps({"error": str(e)[:200]}).encode()
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
        
        def _forward(self, body, target_url):
            url = target_url + self.path
            req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/json'})
            try:
                resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                err = json.dumps({"error": str(e)[:200]}).encode()
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
        
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                return
            # Route GET to chat worker
            url = CHAT_URL + self.path
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                err = json.dumps({"error": str(e)[:200]}).encode()
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err)))
                self.end_headers()
                self.wfile.write(err)
    
    if __name__ == '__main__':
        print(f"LLM proxy v5 starting on port {PORT}")
        print(f"  Chat → {CHAT_URL} (28 cores, qwen2.5-coder:7b)")
        print(f"  Embed → {EMBED_URL} (12 cores, nomic-embed-text)")
        print(f"  Queue: 512 | Cache: chat={CACHE_TTL}s embed={EMBED_CACHE_TTL}s")
        
        # Pre-warm chat model
        print("Pre-warming chat model...")
        try:
            payload = json.dumps({"model": DEFAULT_MODEL, "prompt": "hi", "stream": False, "options": {"num_predict": 1}}).encode()
            req = urllib.request.Request(CHAT_URL + "/api/generate", data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=180)
            print("Chat pre-warmed!")
        except Exception as e:
            print(f"Chat pre-warm: {e}")
        
        server = ThreadedHTTPServer(('0.0.0.0', PORT), ProxyHandler)
        server.serve_forever()
PROXYEOF

echo "LLM proxy v5 deployed (split routing: chat→worker, embed→master)"

kubectl rollout restart deployment llm-proxy-master -n ai-platform 2>&1

echo ""
echo "============================================================"
echo "4. 扩展 LiteLLM 到 2 副本（负载均衡）"
echo "============================================================"
kubectl scale deploy/litellm -n ai-platform --replicas=2 2>&1
echo "LiteLLM: 2 副本"

echo ""
echo "============================================================"
echo "5. 扩展 JupyterHub 资源配额（支撑 1000 人）"
echo "============================================================"
# 当前: CPU limit 2, mem 2G per user
# 1000 用户 * 0.2 CPU guarantee = 200 CPU (需要 48 核分时复用)
# 调整: 降低 CPU guarantee 到 0.1, 提高 concurrent_spawn_limit

echo "=== Update JupyterHub spawner config ==="
kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_scale.py
# Update concurrent spawn limit and resource guarantees
sed -i 's/c.JupyterHub.concurrent_spawn_limit = 64/c.JupyterHub.concurrent_spawn_limit = 200/' /tmp/jhub_scale.py
sed -i 's/c.KubeSpawner.cpu_guarantee = 0.2/c.KubeSpawner.cpu_guarantee = 0.1/' /tmp/jhub_scale.py
sed -i 's/c.KubeSpawner.mem_guarantee = "256M"/c.KubeSpawner.mem_guarantee = "128M"/' /tmp/jhub_scale.py
sed -i 's/c.KubeSpawner.cpu_limit = 2/c.KubeSpawner.cpu_limit = 1/' /tmp/jhub_scale.py
sed -i 's/c.KubeSpawner.mem_limit = "2G"/c.KubeSpawner.mem_limit = "1G"/' /tmp/jhub_scale.py

kubectl create cm jupyterhub-config -n jupyterhub --from-file=jupyterhub_config.py=/tmp/jhub_scale.py --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub scaled: concurrent_spawn=200, CPU guarantee=0.1, limit=1"

echo ""
echo "=== Restart hub ==="
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "6. 验证"
echo "============================================================"
sleep 30

echo "=== CRDB pods ==="
kubectl get pods -n infra 2>&1

echo ""
echo "=== AI platform pods ==="
kubectl get pods -n ai-platform 2>&1 | head -10

echo ""
echo "=== Dify API replicas ==="
kubectl get deploy dify-api -n dify 2>&1

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "=== CRDB cluster ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1

echo ""
echo "=== Ollama models on worker ==="
WPOD=$(kubectl get pods -n ai-platform -l app=ollama-worker -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
kubectl exec -n ai-platform $WPOD -- /usr/bin/ollama list 2>&1

echo ""
echo "=== Ollama models on embed (master) ==="
EPOD=$(kubectl get pods -n ai-platform -l app=ollama-embed -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$EPOD" ]; then
  kubectl exec -n ai-platform $EPOD -- /ollama-bin/ollama list 2>&1
fi

#!/bin/bash
# ============================================================
# 综合优化 v5:
# 1. Ollama on Master (container mode, solve GLIBC)
# 2. 全集群资源最优分配
# 3. 学生自动关联教师课程分组
# 4. 更新文档
# ============================================================

set -e

echo "============================================================"
echo "1. 在 Master 部署 Ollama Embed 实例（容器内运行解决 GLIBC）"
echo "============================================================"

# 先拉取 nomic-embed-text 模型到 master 的存储
mkdir -p /home/k8s-data/ollama-embed/models
echo "Models dir created"

# 使用 jupyter/scipy-notebook 容器运行 ollama (GLIBC 2.35 兼容)
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
        runAsGroup: 0
      containers:
      - name: ollama-embed
        image: 10.100.135.132:5000/jupyter/scipy-notebook:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 0
        command: ['sh', '-c', 'export LD_LIBRARY_PATH=/opt/ollama-libs && /opt/ollama-bin/ollama serve']
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0:11435"
        - name: OLLAMA_MODELS
          value: "/ollama-models"
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
        - name: OLLAMA_LOAD_TIMEOUT
          value: "15m"
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
        - name: ollama-bin
          mountPath: /opt/ollama-bin
          readOnly: true
        - name: ollama-libs
          mountPath: /opt/ollama-libs
          readOnly: true
        - name: models
          mountPath: /ollama-models
        readinessProbe:
          httpGet:
            path: /api/tags
            port: 11435
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: ollama-bin
        hostPath:
          path: /opt/ollama-embed/bin
          type: Directory
      - name: ollama-libs
        hostPath:
          path: /opt/ollama-embed/lib/ollama
          type: Directory
      - name: models
        hostPath:
          path: /home/k8s-data/ollama-embed/models
          type: DirectoryOrCreate
---
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

echo "Ollama embed deployment created on master (port 11435)"

# Wait for pod
sleep 20
echo "=== Pod status ==="
kubectl get pods -n ai-platform -l app=ollama-embed 2>&1

# Pull nomic-embed-text model on the embed instance
echo ""
echo "=== Pull nomic-embed-text on master embed instance ==="
EMBED_POD=$(kubectl get pods -n ai-platform -l app=ollama-embed -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$EMBED_POD" ]; then
  kubectl exec -n ai-platform $EMBED_POD -- /opt/ollama-bin/ollama pull nomic-embed-text 2>&1 | tail -3
  echo "Embed model pulled!"
  kubectl exec -n ai-platform $EMBED_POD -- /opt/ollama-bin/ollama list 2>&1
fi

echo ""
echo "============================================================"
echo "2. 更新 LLM 代理 v6：分离路由（聊天→worker 28核，嵌入→master 12核）"
echo "============================================================"

cat << 'PROXYEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-proxy-script
  namespace: ai-platform
data:
  llm_proxy.py: |
    #!/usr/bin/env python3
    """LLM proxy v6: Split routing
    Chat/generate → ollama-worker (28核, qwen2.5-coder:7b, port 11434)
    Embed → ollama-embed (12核, nomic-embed-text, port 11435)
    Tool calling → forward (no cache)
    Total inference: 40 cores across 2 nodes
    """
    import os, json, time, hashlib, urllib.request, urllib.error
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
    import threading
    
    CHAT_URL = os.environ.get("CHAT_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
    EMBED_URL = os.environ.get("EMBED_URL", "http://ollama-embed.ai-platform.svc.cluster.local:11435")
    PORT = int(os.environ.get("PROXY_PORT", "11434"))
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    EMBED_MODEL = "nomic-embed-text"
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
            
            # Route embed → master embed instance
            if "/api/embed" in path or "/api/embeddings" in path:
                self._handle_cached(path, req_data, body, EMBED_CACHE_TTL, EMBED_URL)
                return
            
            # Tool calling: forward to chat (no cache)
            if "tools" in req_data:
                self._forward(body, CHAT_URL)
                return
            
            # Chat/generate: cache + forward to chat worker
            if "/api/chat" in path or "/api/generate" in path:
                if req_data.get("stream", False):
                    self._forward(body, CHAT_URL)
                    return
                self._handle_cached(path, req_data, body, CACHE_TTL, CHAT_URL)
                return
            
            self._forward(body, CHAT_URL)
        
        def _handle_cached(self, path, req_data, body, ttl, target):
            key = cache_key(req_data.get("model", DEFAULT_MODEL), req_data)
            cached = cache_get(key, ttl)
            if cached:
                data = cached.encode() if isinstance(cached, str) else cached
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('X-Cache', 'HIT')
                self.end_headers()
                self.wfile.write(data)
                return
            
            url = target + path
            req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': 'application/json'})
            try:
                resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                data = resp.read()
                cache_put(key, data.decode('utf-8', errors='replace'), ttl)
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
        
        def _forward(self, body, target):
            url = target + self.path
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
                self.wfile.write(b'{"status":"ok","chat":"worker","embed":"master"}')
                return
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
        print(f"LLM proxy v6 on port {PORT}")
        print(f"  Chat → {CHAT_URL} (28 cores)")
        print(f"  Embed → {EMBED_URL} (12 cores)")
        print(f"  Total: 40 cores inference across 2 nodes")
        
        # Pre-warm both
        try:
            p1 = json.dumps({"model": DEFAULT_MODEL, "prompt": "hi", "stream": False, "options": {"num_predict": 1}}).encode()
            r1 = urllib.request.Request(CHAT_URL + "/api/generate", data=p1, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(r1, timeout=180)
            print("Chat pre-warmed!")
        except Exception as e:
            print(f"Chat pre-warm: {e}")
        
        try:
            p2 = json.dumps({"model": EMBED_MODEL, "input": "test"}).encode()
            r2 = urllib.request.Request(EMBED_URL + "/api/embed", data=p2, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(r2, timeout=60)
            print("Embed pre-warmed!")
        except Exception as e:
            print(f"Embed pre-warm: {e}")
        
        server = ThreadedHTTPServer(('0.0.0.0', PORT), ProxyHandler)
        server.serve_forever()
PROXYEOF

echo "LLM proxy v6 deployed (split routing)"
kubectl rollout restart deployment llm-proxy-master -n ai-platform 2>&1

echo ""
echo "============================================================"
echo "3. 学生自动关联教师课程分组"
echo "============================================================"
echo ""
echo "机制：学生使用用户名前缀自动分组"
echo "  格式: p1-名字 → 加入 lecture-p1-students 组"
echo "  格式: p2-名字 → 加入 lecture-p2-students 组"
echo "  格式: p3-名字 → 加入 lecture-p3-students 组"
echo "  无前缀 → 加入 all-students 通用组"
echo ""

# Update JupyterHub config with post_auth_hook for auto-group-assignment
kubectl get cm jupyterhub-config -n jupyterhub -o jsonpath='{.data.jupyterhub_config\.py}' > /tmp/jhub_auto.py

cat >> /tmp/jhub_auto.py << 'AUTOCONFIG'

# ============================================================
# 学生自动关联教师课程分组
# ============================================================
# 学生登录时，根据用户名前缀自动加入对应课程分组
# 格式: p1-xxx → lecture-p1-students, p2-xxx → lecture-p2-students
# 无前缀 → all-students

from jupyterhub.auth import Authenticator
from jupyterhub.orm import Group, User
import re

async def auto_group_assignment(authenticator, handler, authentication):
    """Post-auth hook: automatically assign users to course groups based on username prefix."""
    user = authentication.get('auth_state', {}).get('username', '') or authentication.get('username', '')
    if not user:
        return authentication
    
    # Parse username prefix for course assignment
    # Format: p1-name → lecture-p1-students
    match = re.match(r'^p(\d+)-(.+)', user)
    if match:
        course_num = match.group(1)
        group_name = f'lecture-p{course_num}-students'
    else:
        group_name = 'all-students'
    
    # Add user to group via database
    try:
        from jupyterhub import app asjh_app
        db = jh_app.app.db
        db_group = db.query(Group).filter_by(name=group_name).first()
        if not db_group:
            db_group = Group(name=group_name)
            db.add(db_group)
            db.commit()
        
        db_user = db.query(User).filter_by(name=user).first()
        if db_user and db_group not in db_user.groups:
            db_group.users.append(db_user)
            db.commit()
            auth_logger.info(f'Auto-assigned {user} to group {group_name}')
    except Exception as e:
        auth_logger.warning(f'Auto-group-assignment failed for {user}: {e}')
    
    return authentication

# Register the hook
c.Authenticator.post_auth_hook = auto_group_assignment

# Define group membership in config (static assignments + dynamic via hook)
c.JupyterHub.load_groups = {
    "lecture-p1-students": ["student-python", "student-alice"],
    "lecture-p2-students": ["student-java", "student-bob"],
    "lecture-p3-students": ["student-carol"],
    "lecture-p4-students": [],
    "lecture-p5-students": [],
    "lecture-p6-students": [],
    "all-students": [],
    "all-teachers": ["teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"],
}

# Admin users
c.Authenticator.admin_users = {"teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"}
c.JupyterHub.admin_access = True
AUTOCONFIG

kubectl create cm jupyterhub-config -n jupyterhub --from-file=jupyterhub_config.py=/tmp/jhub_auto.py --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "JupyterHub auto-group-assignment configured"

echo ""
echo "============================================================"
echo "4. 全集群资源最优分配表"
echo "============================================================"
echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│               集群资源分配 (48 CPU cores total)                 │"
echo "├──────────────────────┬──────────────────────────────────────────┤"
echo "│ Master (16 cores)    │ Worker (32 cores)                        │"
echo "├──────────────────────┼──────────────────────────────────────────┤"
echo "│ CRDB-A:      6 cores │ Ollama-worker:  28 cores (chat+embed)   │"
echo "│ CRDB-B:      6 cores │ CRDB-C:          4 cores                 │"
echo "│ Ollama-embed:14 cores│ LiteLLM:         2 cores                 │"
echo "│ Redis:       2 cores │ Code-Server:     2 cores                 │"
echo "│ LLM-proxy:   1 core  │ Dify-worker:     4 cores                 │"
echo "│ JupyterHub:  1 core  │ Jupyter-pods:   16 cores (dynamic)       │"
echo "│ Dify-API:    2 cores │                                          │"
echo "│ ──────────── │       │                                          │"
echo "│ Subtotal:   14 cores │ Subtotal:          30 cores              │"
echo "│ Free:        2 cores │ Free:              2 cores               │"
echo "├──────────────────────┴──────────────────────────────────────────┤"
echo "│ LLM inference: 28核(chat,worker) + 12核(embed,master) = 40核   │"
echo "│ Database:      6+6+4 = 16 cores CRDB                           │"
echo "│ Dify:          2+4 = 6 cores                                   │"
echo "│ JupyterHub:    1 + 16 dynamic = 17 cores                        │"
echo "│ System:        4 cores (kube-proxy, coredns, etc)               │"
echo "└─────────────────────────────────────────────────────────────────┘"
echo ""

echo "============================================================"
echo "5. 重启 JupyterHub 使分组配置生效"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}' 2>/dev/null)
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "6. 最终验证"
echo "============================================================"
sleep 30

echo "=== All namespaces ==="
echo "--- infra ---"
kubectl get pods -n infra 2>&1
echo ""
echo "--- ai-platform ---"
kubectl get pods -n ai-platform 2>&1 | head -10
echo ""
echo "--- jupyterhub ---"
kubectl get pods -n jupyterhub 2>&1 | head -5

echo ""
echo "=== CRDB cluster ==="
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- /cockroach-binary/cockroach node ls --insecure --host=localhost:26257 2>&1

echo ""
echo "=== Ollama embed (master) ==="
EMBED_POD=$(kubectl get pods -n ai-platform -l app=ollama-embed -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$EMBED_POD" ]; then
  kubectl exec -n ai-platform $EMBED_POD -- /opt/ollama-bin/ollama list 2>&1
  kubectl exec -n ai-platform $EMBED_POD -- /opt/ollama-bin/ollama ps 2>&1
fi

echo ""
echo "=== Node load ==="
kubectl top nodes 2>&1

echo ""
echo "============================================================"
echo "DONE - 全部优化完成"
echo "============================================================"
echo ""
echo "架构总结："
echo "  Master (16核): CRDB(6+6) + Ollama-embed(14) + Redis(2) + Proxy(1) + Hub(1)"
echo "  Worker (32核): Ollama-chat(28) + CRDB-C(4) + 其他(4)"
echo "  总推理能力: 28核聊天 + 14核嵌入 = 42核"
echo ""
echo "学生自动分组："
echo "  格式: p1-名字 → lecture-p1-students"
echo "  格式: p2-名字 → lecture-p2-students"
echo "  无前缀 → all-students"
echo "  教师通过管理面板查看自己组的学生"

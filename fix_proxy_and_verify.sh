#!/bin/bash
set -e

echo "=== 1. Create LLM proxy script ConfigMap ==="
cat << 'PROXYEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-proxy-script
  namespace: ai-platform
data:
  llm_proxy.py: |
    #!/usr/bin/env python3
    """Lightweight LLM proxy: forwards to ollama-worker with timeout handling."""
    import os, json, time, sys, urllib.request, urllib.error
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    OLLAMA_URL = os.environ.get("OLLAMA_WORKER_URL", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
    PORT = int(os.environ.get("PROXY_PORT", "11434"))
    
    # Default model and timeout
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    REQUEST_TIMEOUT = 120  # 2 min max per request
    
    class ProxyHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            print(f"[{time.strftime('%H:%M:%S')}] {format % args}", flush=True)
        
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b''
            
            # Forward to ollama-worker
            url = OLLAMA_URL + self.path
            req = urllib.request.Request(url, data=body, method='POST',
                headers={'Content-Type': 'application/json'})
            
            try:
                resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                # On timeout, return a helpful error
                error_msg = json.dumps({
                    "error": f"LLM proxy: {str(e)[:200]}",
                    "model": DEFAULT_MODEL,
                    "hint": "If Ollama is busy, wait 30s and try again, or switch to tinyllama:latest"
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
        server = HTTPServer(('0.0.0.0', PORT), ProxyHandler)
        print(f"LLM proxy started on port {PORT}, forwarding to {OLLAMA_URL}")
        server.serve_forever()
PROXYEOF

echo "Proxy script configmap created"

echo ""
echo "=== 2. Restart llm-proxy-master to pick up the configmap ==="
kubectl rollout restart deployment llm-proxy-master -n ai-platform 2>&1
sleep 10
kubectl get pods -n ai-platform -l app=llm-proxy-master 2>&1

echo ""
echo "=== 3. Verify ollama-master service resolves ==="
kubectl get svc ollama-master -n ai-platform 2>&1

echo ""
echo "=== 4. Test the proxy ==="
# Wait for pod to be ready
for i in $(seq 1 10); do
  STATUS=$(kubectl get pod -n ai-platform -l app=llm-proxy-master -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$STATUS" = "Running" ]; then break; fi
  sleep 5
done

echo "Proxy pod status: $STATUS"

echo ""
echo "=== 5. Re-create teacher-zhang pod ==="
# The teacher pod was deleted. JupyterHub should recreate it when user logs in.
# For now, let's verify the hub is running and pods can be spawned
kubectl get pods -n jupyterhub 2>&1

echo ""
echo "=== 6. Verify Dify scaling ==="
kubectl get deploy -n dify 2>&1 | head -10

echo ""
echo "=== 7. Final node load ==="
kubectl top nodes 2>&1

echo ""
echo "=== DONE ==="

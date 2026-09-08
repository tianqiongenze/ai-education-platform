#!/usr/bin/env python3
"""
Lightweight OpenAI-compatible embedding proxy for Ollama.
Converts OpenAI /v1/embeddings format to Ollama /api/embeddings format.
No external dependencies beyond Python stdlib.
"""
import json
import http.server
import socketserver
import urllib.request
import sys
import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama-worker.ai-platform.svc.cluster.local:11434")
LISTEN_PORT = int(os.environ.get("PROXY_PORT", "8088"))

class EmbedProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ("/v1/embeddings", "/embeddings"):
            self.send_error(404, "Not Found")
            return
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.read_body(content_length)
        
        try:
            req_data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        model = req_data.get("model", "bge-m3")
        inputs = req_data.get("input", "")
        if isinstance(inputs, str):
            inputs = [inputs]
        
        # Call Ollama native API for each input
        all_embeddings = []
        total_tokens = 0
        for text in inputs:
            ollama_req = json.dumps({"model": model, "prompt": text}).encode("utf-8")
            ollama_url = OLLAMA_HOST + "/api/embeddings"
            req = urllib.request.Request(ollama_url, data=ollama_req, method="POST")
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    embedding = result.get("embedding", [])
                    all_embeddings.append(embedding)
                    total_tokens += len(text.split())
            except Exception as e:
                print(f"Error calling Ollama: {e}", file=sys.stderr)
                self.send_error(500, f"Ollama error: {e}")
                return
        
        # Return OpenAI-compatible response
        response = {
            "object": "list",
            "data": [
                {"object": "embedding", "index": i, "embedding": emb}
                for i, emb in enumerate(all_embeddings)
            ],
            "model": model,
            "usage": {"prompt_tokens": total_tokens, "total_tokens": total_tokens}
        }
        
        resp_body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)
    
    def do_GET(self):
        if self.path == "/health":
            resp = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        elif self.path == "/v1/models":
            # Return a minimal models list
            models = {
                "object": "list",
                "data": [
                    {"id": "qwen3-embedding:0.6b", "object": "model"},
                    {"id": "bge-m3", "object": "model"},
                ]
            }
            resp = json.dumps(models).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404, "Not Found")
    
    def read_body(self, content_length):
        body = b""
        remaining = content_length
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)
        return body.decode("utf-8")
    
    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}", file=sys.stderr)

if __name__ == "__main__":
    # Use ThreadingHTTPServer for concurrent request handling
    server = http.server.ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), EmbedProxyHandler)
    print(f"Embedding proxy (threaded) listening on :{LISTEN_PORT}, forwarding to {OLLAMA_HOST}")
    server.serve_forever()

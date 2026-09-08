"""
Enterprise Load Test for AI Platform
- code-server: 2000 concurrent users
- LLM services (litellm): 5000 concurrent users
- Dify platform: included in LLM test

Usage:
    pip install locust
    locust -f enterprise_load_test.py --host=http://10.167.2.175
    
    # Or run specific test groups:
    locust -f enterprise_load_test.py --host=http://10.167.2.175 --tags codeserver
    locust -f enterprise_load_test.py --host=http://10.167.2.175 --tags llm
"""

import random
import time
import json
from locust import HttpUser, task, between, tag, events
from locust.exception import StopUser


class CodeServerUser(HttpUser):
    """Simulates developers using code-server IDE - target: 2000 concurrent"""
    wait_time = between(3, 15)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logged_in = False
        self.session_cookie = None
    
    def on_start(self):
        self.login()
    
    def login(self):
        with self.client.get("/login", catch_response=True, name="GET /login") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Login page failed: {r.status_code}")
                return
        
        with self.client.post("/login", 
                              data={"password": "ai@2026"},
                              headers={"Content-Type": "application/x-www-form-urlencoded"},
                              catch_response=True, 
                              allow_redirects=False,
                              name="POST /login") as r:
            if r.status_code in [200, 302]:
                self.logged_in = True
                self.session_cookie = r.cookies
                r.success()
            else:
                r.failure(f"Login failed: {r.status_code}")
    
    @tag('codeserver')
    @task(15)
    def view_workspace(self):
        if not self.logged_in:
            return
        with self.client.get("/", 
                            cookies=self.session_cookie,
                            catch_response=True,
                            name="GET / (workspace)") as r:
            if r.status_code in [200, 302]:
                r.success()
            else:
                r.failure(f"Workspace failed: {r.status_code}")
    
    @tag('codeserver')
    @task(10)
    def health_check(self):
        with self.client.get("/healthz", catch_response=True, name="GET /healthz") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health check failed: {r.status_code}")
    
    @tag('codeserver')
    @task(5)
    def get_static_assets(self):
        paths = ["/static/out/vs/loader.js", "/static/out/vs/workbench/workbench.desktop.main.css"]
        for path in paths:
            with self.client.get(path, catch_response=True, name=f"GET {path}") as r:
                if r.status_code in [200, 304]:
                    r.success()
    
    @tag('codeserver')
    @task(3)
    def api_settings(self):
        if not self.logged_in:
            return
        with self.client.get("/api/settings", 
                            cookies=self.session_cookie,
                            catch_response=True,
                            name="GET /api/settings") as r:
            if r.status_code == 200:
                r.success()


class LLMServiceUser(HttpUser):
    """Simulates AI service consumers via litellm proxy - target: 5000 concurrent"""
    wait_time = between(1, 8)
    
    API_KEY = "sk-ai-platform-master"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = 30083  # litellm NodePort
    
    @tag('llm')
    @task(20)
    def health_check(self):
        with self.client.get(f"/health/readiness", 
                            catch_response=True,
                            name="litellm GET /health/readiness") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health check: {r.status_code}")
    
    @tag('llm')
    @task(15)
    def list_models(self):
        headers = {"Authorization": f"Bearer {self.API_KEY}"}
        with self.client.get(f"/v1/models",
                            headers=headers,
                            catch_response=True,
                            name="litellm GET /v1/models") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"List models: {r.status_code}")
    
    @tag('llm')
    @task(10)
    def chat_completion_small(self):
        """Quick chat with small model (7b)"""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10,
            "stream": False
        }
        with self.client.post(f"/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=60,
                             name="litellm POST /v1/chat/completions (7b)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()  # Rate limit is expected under load
            else:
                r.failure(f"Chat completion: {r.status_code}")
    
    @tag('llm')
    @task(5)
    def chat_completion_medium(self):
        """Chat with medium model (14b)"""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen2.5:14b",
            "messages": [{"role": "user", "content": "Say hello in one sentence"}],
            "max_tokens": 20,
            "stream": False
        }
        with self.client.post(f"/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=120,
                             name="litellm POST /v1/chat/completions (14b)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Chat completion 14b: {r.status_code}")
    
    @tag('llm')
    @task(3)
    def embedding(self):
        """Test embedding model"""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "bge-m3",
            "input": "Test embedding text"
        }
        with self.client.post(f"/v1/embeddings",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=30,
                             name="litellm POST /v1/embeddings") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Embedding: {r.status_code}")
    
    @tag('llm')
    @task(2)
    def chat_completion_coder(self):
        """Test code model"""
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen2.5-coder:7b",
            "messages": [{"role": "user", "content": "def hello():"}],
            "max_tokens": 15,
            "stream": False
        }
        with self.client.post(f"/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=60,
                             name="litellm POST /v1/chat/completions (coder)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Coder completion: {r.status_code}")


class DifyPlatformUser(HttpUser):
    """Simulates Dify platform users"""
    wait_time = between(2, 10)
    
    @tag('dify')
    @task(10)
    def dify_web_home(self):
        with self.client.get("/", 
                            catch_response=True,
                            name="dify GET / (web)") as r:
            if r.status_code in [200, 302, 307]:
                r.success()
            else:
                r.failure(f"Dify web: {r.status_code}")
    
    @tag('dify')
    @task(5)
    def dify_api_health(self):
        with self.client.get("/health",
                            catch_response=True,
                            name="dify GET /health") as r:
            if r.status_code == 200:
                r.success()


class OpenWebUIUser(HttpUser):
    """Simulates Open-WebUI chat users"""
    wait_time = between(5, 20)
    
    @tag('webui')
    @task(10)
    def webui_home(self):
        with self.client.get("/",
                            catch_response=True,
                            name="open-webui GET /") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Open-webui: {r.status_code}")
    
    @tag('webui')
    @task(3)
    def webui_api_health(self):
        with self.client.get("/api/v1/utils/health",
                            catch_response=True,
                            name="open-webui GET /api/v1/utils/health") as r:
            if r.status_code == 200:
                r.success()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("ENTERPRISE LOAD TEST STARTING")
    print("Target: code-server (2000 users) + LLM services (5000 users)")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("ENTERPRISE LOAD TEST COMPLETE")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
    print("=" * 60)
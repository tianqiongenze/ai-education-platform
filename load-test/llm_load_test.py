"""
LLM Services Enterprise Load Test (via litellm proxy)
Target: 5000 concurrent users
Usage: locust -f llm_load_test.py --host=http://10.167.2.175:30083 --headless -u 5000 -r 200 -t 600s --html=report_llm.html
"""

import random
from locust import HttpUser, task, between, events


class LLMServiceUser(HttpUser):
    """Simulates AI service consumers via litellm proxy"""
    wait_time = between(1, 8)
    
    API_KEY = "sk-ai-platform-master"
    
    @task(20)
    def health_check(self):
        with self.client.get("/health/readiness", 
                            catch_response=True,
                            name="GET /health/readiness") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health check: {r.status_code}")
    
    @task(15)
    def list_models(self):
        headers = {"Authorization": f"Bearer {self.API_KEY}"}
        with self.client.get("/v1/models",
                            headers=headers,
                            catch_response=True,
                            name="GET /v1/models") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"List models: {r.status_code}")
    
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
        with self.client.post("/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=60,
                             name="POST /v1/chat/completions (7b)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()  # Rate limit is expected under load
            else:
                r.failure(f"Chat completion: {r.status_code}")
    
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
        with self.client.post("/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=120,
                             name="POST /v1/chat/completions (14b)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Chat completion 14b: {r.status_code}")
    
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
        with self.client.post("/v1/embeddings",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=30,
                             name="POST /v1/embeddings") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Embedding: {r.status_code}")
    
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
        with self.client.post("/v1/chat/completions",
                             json=payload,
                             headers=headers,
                             catch_response=True,
                             timeout=60,
                             name="POST /v1/chat/completions (coder)") as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 429:
                r.success()
            else:
                r.failure(f"Coder completion: {r.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("LLM SERVICES LOAD TEST STARTING")
    print("Target: 5000 concurrent users")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print("=" * 60)
    print("LLM SERVICES LOAD TEST COMPLETE")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures}")
    print(f"Failure rate: {(stats.num_failures / max(stats.num_requests, 1)) * 100:.2f}%")
    print(f"Average response time: {stats.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"RPS: {stats.total_rps:.2f}")
    print("=" * 60)
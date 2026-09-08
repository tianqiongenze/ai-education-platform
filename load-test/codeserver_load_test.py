"""
Code-Server Enterprise Load Test
Target: 2000 concurrent users
Usage: locust -f codeserver_load_test.py --host=http://10.167.2.175:32231 --headless -u 2000 -r 100 -t 300s --html=report_codeserver.html
"""

import random
from locust import HttpUser, task, between, events


class CodeServerUser(HttpUser):
    """Simulates developers using code-server IDE"""
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
    
    @task(10)
    def health_check(self):
        with self.client.get("/healthz", catch_response=True, name="GET /healthz") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Health check failed: {r.status_code}")
    
    @task(5)
    def get_static_assets(self):
        paths = ["/static/out/vs/loader.js", "/static/out/vs/workbench/workbench.desktop.main.css"]
        for path in paths:
            with self.client.get(path, catch_response=True, name=f"GET {path}") as r:
                if r.status_code in [200, 304]:
                    r.success()
    
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


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("CODE-SERVER LOAD TEST STARTING")
    print("Target: 2000 concurrent users")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print("=" * 60)
    print("CODE-SERVER LOAD TEST COMPLETE")
    print(f"Total requests: {stats.num_requests}")
    print(f"Total failures: {stats.num_failures}")
    print(f"Failure rate: {(stats.num_failures / max(stats.num_requests, 1)) * 100:.2f}%")
    print(f"Average response time: {stats.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"RPS: {stats.total_rps:.2f}")
    print("=" * 60)
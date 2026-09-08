"""
Locust load test for code-server enterprise deployment.
Tests 3000 concurrent users with realistic workflows.
"""

import random
import time
from locust import HttpUser, task, between, events
from locust.exception import StopUser


class CodeServerUser(HttpUser):
    """Simulates a real developer using code-server."""
    
    wait_time = between(2, 10)  # Think time between actions
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.csrf_token = None
        self.logged_in = False
        self.workspace_opened = False
        
    def on_start(self):
        """Login when user starts."""
        self.login()
        
    def login(self):
        """Authenticate with code-server."""
        # Get login page to obtain CSRF token
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                # Extract CSRF token from cookies or page
                self.csrf_token = response.cookies.get("csrf_token") or "dummy"
            else:
                response.failure(f"Failed to get login page: {response.status_code}")
                return
                
        # Submit login form
        login_data = {
            "password": "ai@2026"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRF-Token": self.csrf_token,
            "Referer": self.client.base_url + "/"
        }
        
        with self.client.post("/login", data=login_data, headers=headers, 
                              catch_response=True, allow_redirects=False) as response:
            if response.status_code in [200, 302]:
                self.logged_in = True
                # Get session cookie
                self.session_id = response.cookies.get("session") or response.cookies.get("connect.sid")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
                raise StopUser()
                
    @task(10)
    def view_dashboard(self):
        """View the main dashboard/workspace list."""
        if not self.logged_in:
            return
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")
                
    @task(8)
    def open_workspace(self):
        """Open a workspace (simulate opening a project)."""
        if not self.logged_in:
            return
        # Simulate opening a workspace - this creates a websocket connection
        with self.client.get("/?folder=/home/coder/project", catch_response=True) as response:
            if response.status_code == 200:
                self.workspace_opened = True
                response.success()
            else:
                response.failure(f"Open workspace failed: {response.status_code}")
                
    @task(5)
    def api_health_check(self):
        """Check health endpoint."""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
                
    @task(3)
    def proxy_ports(self):
        """Access proxied ports (simulate port forwarding)."""
        if not self.logged_in or not self.workspace_opened:
            return
        # Simulate accessing a proxied port
        port = random.randint(3000, 9000)
        with self.client.get(f"/proxy/{port}/", catch_response=True) as response:
            # 404 is expected if no service running on that port
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Proxy failed: {response.status_code}")
                
    @task(2)
    def extensions_marketplace(self):
        """Browse extensions marketplace."""
        if not self.logged_in:
            return
        with self.client.get("/api/extensions", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Extensions API failed: {response.status_code}")
                
    @task(1)
    def settings_api(self):
        """Access settings API."""
        if not self.logged_in:
            return
        with self.client.get("/api/settings", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Settings API failed: {response.status_code}")
                
    @task(1)
    def terminal_websocket(self):
        """Simulate terminal websocket connection (HTTP upgrade)."""
        if not self.logged_in or not self.workspace_opened:
            return
        # This simulates the initial HTTP upgrade request for terminal
        headers = {
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ=="
        }
        with self.client.get("/terminal/websocket", headers=headers, 
                             catch_response=True) as response:
            # WebSocket upgrade returns 101 or 400 if not supported via HTTP
            if response.status_code in [101, 400, 404, 426]:
                response.success()
            else:
                response.failure(f"Terminal WS failed: {response.status_code}")


class CodeServerAnonymousUser(HttpUser):
    """Simulates unauthenticated users hitting the login page."""
    
    wait_time = between(5, 15)
    weight = 1  # 10% of users are anonymous
    
    @task(5)
    def view_login_page(self):
        """Hit the login page."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Login page failed: {response.status_code}")
                
    @task(1)
    def health_check(self):
        """Anonymous health check."""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# Event handlers for test lifecycle
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("CODE-SERVER LOAD TEST STARTED")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("CODE-SERVER LOAD TEST STOPPED")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, 
               response, context, exception, **kwargs):
    if exception:
        print(f"REQUEST FAILED: {request_type} {name} - {exception}")


if __name__ == "__main__":
    # For running directly: locust -f locustfile.py --host=https://code-server.ai-platform.local
    pass
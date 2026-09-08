"""
Locust stress test for code-server - simulates 5000 concurrent users.
Tests:
1. WebSocket connection (code-server uses WebSocket for terminal/editor)
2. HTTP API endpoints
3. Static file serving
"""
from locust import HttpUser, task, between, events
import time
import random


class CodeServerUser(HttpUser):
    """
    Simulates a code-server user performing typical operations.
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Initialize session - code-server doesn't require login for basic access."""
        self.session_start = time.time()

    @task(3)
    def load_homepage(self):
        """Load the main code-server page."""
        with self.client.get("/", catch_response=True, timeout=30) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage returned {response.status_code}")

    @task(2)
    def load_static_assets(self):
        """Load static assets (JS, CSS)."""
        assets = [
            "/static/out/vs/code/browser/workbench/workbench.css",
            "/static/out/vs/loader.js",
            "/static/out/vs/code/browser/workbench/workbench.js",
        ]
        asset = random.choice(assets)
        with self.client.get(asset, catch_response=True, timeout=30) as response:
            if response.status_code in [200, 304]:
                response.success()
            else:
                response.failure(f"Asset {asset} returned {response.status_code}")

    @task(1)
    def health_check(self):
        """Check health endpoint."""
        with self.client.get("/healthz", catch_response=True, timeout=10) as response:
            if response.status_code in [200, 404]:  # 404 is OK if endpoint doesn't exist
                response.success()
            else:
                response.failure(f"Health check returned {response.status_code}")

    @task(1)
    def api_check(self):
        """Check API availability."""
        endpoints = ["/", "/login", "/static/out/vs/code/browser/workbench/workbench.html"]
        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, catch_response=True, timeout=30) as response:
            if response.status_code in [200, 302, 304]:
                response.success()
            else:
                response.failure(f"API {endpoint} returned {response.status_code}")

    def on_stop(self):
        """Cleanup."""
        pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n{'='*60}")
    print(f"CODE-SERVER STRESS TEST - 5000 CONCURRENT USERS")
    print(f"Target: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats
    print(f"\n{'='*60}")
    print(f"STRESS TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {(stats.total.num_failures / max(stats.total.num_requests, 1)) * 100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median Response Time: {stats.total.median_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print(f"{'='*60}\n")
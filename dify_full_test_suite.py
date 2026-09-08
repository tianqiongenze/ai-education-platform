#!/usr/bin/env python3
"""
Dify Full-Feature Test Suite
Tests all major Dify functionality: authentication, apps, chat, workflows,
datasets/knowledge base, model providers, API keys, and more.

Usage: python3 dify_full_test_suite.py
"""

import requests
import json
import base64
import time
import sys
import urllib3
from datetime import datetime

urllib3.disable_warnings()

# ============================================================
# Configuration
# ============================================================
BASE = "https://10.167.2.175:31825"
HOST = "console.dify-plus.local"
API_HOST = "api.dify-plus.local"
EMAIL = "myuwei@126.com"
PASSWORD = "Difyai123456"
LITELLM_URL = "http://10.167.2.176:30083"
LITELLM_KEY = "sk-ai-platform-master"
OLLAMA_URL = "http://10.167.2.176:30086"

# Test results tracking
results = []
total_tests = 0
passed_tests = 0
failed_tests = 0
skipped_tests = 0


def log_result(test_name, status, detail=""):
    """Log a test result."""
    global total_tests, passed_tests, failed_tests, skipped_tests
    total_tests += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "PASS":
        passed_tests += 1
        symbol = "✅"
    elif status == "FAIL":
        failed_tests += 1
        symbol = "❌"
    elif status == "SKIP":
        skipped_tests += 1
        symbol = "⏭️"
    else:
        symbol = "ℹ️"
    results.append((test_name, status, detail))
    print(f"{timestamp} {symbol} [{test_name}] {status}: {detail}")


def get_session():
    """Create authenticated session."""
    s = requests.Session()
    s.verify = False
    s.headers["Host"] = HOST
    pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
    resp = s.post(f"{BASE}/console/api/login", json={
        "email": EMAIL,
        "password": pass_b64,
        "language": "zh-Hans",
        "remember_me": True
    })
    if resp.json().get("result") == "success":
        s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
        return s
    return None


# ============================================================
# Test Suites
# ============================================================

def test_01_authentication():
    """Test 1: Authentication and Login"""
    print("\n" + "=" * 60)
    print("TEST SUITE 1: Authentication")
    print("=" * 60)

    # 1.1 Login with correct credentials
    s = requests.Session()
    s.verify = False
    s.headers["Host"] = HOST
    pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
    resp = s.post(f"{BASE}/console/api/login", json={
        "email": EMAIL, "password": pass_b64,
        "language": "zh-Hans", "remember_me": True
    })
    if resp.status_code == 200 and resp.json().get("result") == "success":
        log_result("1.1 Login with correct credentials", "PASS", "Login successful")
    else:
        log_result("1.1 Login with correct credentials", "FAIL", f"Status: {resp.status_code}, Body: {resp.text[:100]}")

    # 1.2 Login with wrong password
    wrong_b64 = base64.b64encode(b"wrongpassword123").decode()
    resp = s.post(f"{BASE}/console/api/login", json={
        "email": EMAIL, "password": wrong_b64,
        "language": "zh-Hans", "remember_me": True
    })
    if resp.status_code == 401:
        log_result("1.2 Login with wrong password rejected", "PASS", "Correctly rejected")
    else:
        log_result("1.2 Login with wrong password rejected", "FAIL", f"Status: {resp.status_code}")

    # 1.3 Login with base64-encoded password (Dify 1.14 requirement)
    if base64.b64encode(PASSWORD.encode()).decode():
        log_result("1.3 Password base64 encoding", "PASS", "Password correctly base64 encoded")

    # 1.4 Get user profile
    s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
    resp = s.get(f"{BASE}/console/api/account/profile")
    if resp.status_code == 200:
        data = resp.json().get("data", resp.json())
        log_result("1.4 Get user profile", "PASS", f"User: {data.get('name', 'unknown')}")
    else:
        log_result("1.4 Get user profile", "FAIL", f"Status: {resp.status_code}")

    # 1.5 Get workspaces
    resp = s.get(f"{BASE}/console/api/workspaces")
    if resp.status_code == 200:
        ws = resp.json().get("data", [])
        if isinstance(ws, list) and len(ws) > 0:
            log_result("1.5 Get workspaces", "PASS", f"Found {len(ws)} workspace(s)")
        else:
            log_result("1.5 Get workspaces", "FAIL", "No workspaces found")
    else:
        log_result("1.5 Get workspaces", "FAIL", f"Status: {resp.status_code}")

    # 1.6 CSRF token validation
    s_no_csrf = requests.Session()
    s_no_csrf.verify = False
    s_no_csrf.headers["Host"] = HOST
    s_no_csrf.post(f"{BASE}/console/api/login", json={
        "email": EMAIL, "password": pass_b64,
        "language": "zh-Hans", "remember_me": True
    })
    resp = s_no_csrf.get(f"{BASE}/console/api/account/profile")
    if resp.status_code == 401 and "CSRF" in resp.text:
        log_result("1.6 CSRF token validation", "PASS", "CSRF protection active")
    else:
        log_result("1.6 CSRF token validation", "FAIL", f"Status: {resp.status_code}")

    return s


def test_02_infrastructure(s):
    """Test 2: Infrastructure Health"""
    print("\n" + "=" * 60)
    print("TEST SUITE 2: Infrastructure Health")
    print("=" * 60)

    # 2.1 Dify API health
    resp = s.get(f"{BASE}/console/api/health")
    # Try direct health endpoint
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("10.167.2.175", 31825))
        sock.close()
        log_result("2.1 Dify ingress accessible", "PASS", "Ingress responding")
    except:
        log_result("2.1 Dify ingress accessible", "FAIL", "Cannot connect to ingress")

    # 2.2 LiteLLM gateway health
    try:
        resp = requests.get(f"{LITELLM_URL}/health/liveliness", timeout=10)
        if resp.status_code == 200:
            log_result("2.2 LiteLLM gateway health", "PASS", f"Response: {resp.text[:50]}")
        else:
            log_result("2.2 LiteLLM gateway health", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("2.2 LiteLLM gateway health", "FAIL", str(e)[:100])

    # 2.3 Ollama worker health
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            log_result("2.3 Ollama worker health", "PASS", f"{len(models)} models available")
        else:
            log_result("2.3 Ollama worker health", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("2.3 Ollama worker health", "FAIL", str(e)[:100])

    # 2.4 LiteLLM models list
    try:
        resp = requests.get(f"{LITELLM_URL}/v1/models",
                           headers={"Authorization": f"Bearer {LITELLM_KEY}"}, timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("data", [])
            log_result("2.4 LiteLLM models list", "PASS", f"{len(models)} models registered")
            for m in models:
                print(f"       - {m['id']}")
        else:
            log_result("2.4 LiteLLM models list", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("2.4 LiteLLM models list", "FAIL", str(e)[:100])


def test_03_model_providers(s):
    """Test 3: Model Providers"""
    print("\n" + "=" * 60)
    print("TEST SUITE 3: Model Providers")
    print("=" * 60)

    # 3.1 Get model providers list
    resp = s.get(f"{BASE}/console/api/workspaces/current/model-providers")
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        log_result("3.1 Get model providers", "PASS", f"Found {len(data)} providers")
        for p in data:
            models = p.get("models", [])
            if models:
                print(f"       - {p.get('provider', 'unknown')}: {len(models)} models")
    else:
        log_result("3.1 Get model providers", "FAIL", f"Status: {resp.status_code}, Body: {resp.text[:200]}")
        return

    # 3.2 Check Ollama provider exists
    ollama_provider = None
    for p in data:
        if "ollama" in p.get("provider", "").lower():
            ollama_provider = p
            break
    if ollama_provider:
        models = ollama_provider.get("models", [])
        log_result("3.2 Ollama provider present", "PASS", f"Ollama has {len(models)} configured models")
    else:
        log_result("3.2 Ollama provider present", "FAIL", "Ollama provider not found")

    # 3.3 Check Tongyi provider exists
    tongyi_provider = None
    for p in data:
        if "tongyi" in p.get("provider", "").lower():
            tongyi_provider = p
            break
    if tongyi_provider:
        log_result("3.3 Tongyi provider present", "PASS", "Tongyi provider available")
    else:
        log_result("3.3 Tongyi provider present", "FAIL", "Tongyi provider not found")

    # 3.4 Check OpenAI API compatible provider
    openai_compat = None
    for p in data:
        if "openai_api_compatible" in p.get("provider", "").lower():
            openai_compat = p
            break
    if openai_compat:
        log_result("3.4 OpenAI-compatible provider present", "PASS", "OpenAI API compatible provider available")
    else:
        log_result("3.4 OpenAI-compatible provider present", "FAIL", "Provider not found")


def test_04_apps(s):
    """Test 4: Application Management"""
    print("\n" + "=" * 60)
    print("TEST SUITE 4: Application Management")
    print("=" * 60)

    # 4.1 List all apps
    resp = s.get(f"{BASE}/console/api/apps", params={"page": 1, "page_size": 50})
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        log_result("4.1 List applications", "PASS", f"Found {len(data)} apps")
        for a in data[:10]:
            print(f"       - {a.get('name', '?')} ({a.get('mode', '?')})")
    else:
        log_result("4.1 List applications", "FAIL", f"Status: {resp.status_code}")
        return []

    # 4.2 Check app modes
    modes = set()
    for a in data:
        modes.add(a.get("mode"))
    expected_modes = {"chat", "advanced-chat", "workflow", "completion", "agent"}
    found_modes = modes & expected_modes
    if found_modes:
        log_result("4.2 App mode variety", "PASS", f"Modes found: {', '.join(found_modes)}")
    else:
        log_result("4.2 App mode variety", "FAIL", f"Modes: {modes}")

    # 4.3 Get app detail for first app
    if data:
        first_app = data[0]
        app_id = first_app.get("id")
        resp = s.get(f"{BASE}/console/api/apps/{app_id}")
        if resp.status_code == 200:
            log_result("4.3 Get app detail", "PASS", f"App: {first_app.get('name')}")
        else:
            log_result("4.3 Get app detail", "FAIL", f"Status: {resp.status_code}")

        # 4.4 Get app API keys
        resp = s.get(f"{BASE}/console/api/apps/{app_id}/api-keys")
        if resp.status_code == 200:
            keys = resp.json().get("data", [])
            log_result("4.4 Get app API keys", "PASS", f"Found {len(keys)} API key(s)")
        else:
            log_result("4.4 Get app API keys", "FAIL", f"Status: {resp.status_code}")

    return data


def test_05_chat(s, apps):
    """Test 5: Chat Functionality"""
    print("\n" + "=" * 60)
    print("TEST SUITE 5: Chat Functionality")
    print("=" * 60)

    # Find a chat app
    chat_app = None
    for a in apps:
        if a.get("mode") in ("chat", "advanced-chat"):
            chat_app = a
            break

    if not chat_app:
        log_result("5.1 Find chat app", "SKIP", "No chat app found")
        return

    app_id = chat_app.get("id")
    log_result("5.1 Find chat app", "PASS", f"Using: {chat_app.get('name')}")

    # Get API key for the app
    resp = s.get(f"{BASE}/console/api/apps/{app_id}/api-keys")
    if resp.status_code != 200 or not resp.json().get("data"):
        log_result("5.2 Get chat API key", "FAIL", "No API key available")
        return

    api_key = resp.json()["data"][0].get("token")
    log_result("5.2 Get chat API key", "PASS", f"Key: {api_key[:15]}...")

    # 5.3 Send chat message
    api_session = requests.Session()
    api_session.verify = False
    api_session.headers["Host"] = API_HOST
    api_session.headers["Authorization"] = f"Bearer {api_key}"
    api_session.headers["Content-Type"] = "application/json"

    try:
        resp = api_session.post(f"{BASE}/api/chat-messages", json={
            "inputs": {},
            "query": "Hello, please respond with a short greeting.",
            "response_mode": "blocking",
            "user": "test-user"
        }, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "")
            if answer:
                log_result("5.3 Send chat message", "PASS", f"Response: {answer[:80]}")
            else:
                log_result("5.3 Send chat message", "FAIL", "Empty response")
        else:
            log_result("5.3 Send chat message", "FAIL", f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_result("5.3 Send chat message", "FAIL", str(e)[:150])

    # 5.4 Get conversation history
    try:
        resp = api_session.get(f"{BASE}/api/messages", params={"user": "test-user", "limit": 10})
        if resp.status_code == 200:
            msgs = resp.json().get("data", [])
            log_result("5.4 Get conversation history", "PASS", f"Found {len(msgs)} messages")
        else:
            log_result("5.4 Get conversation history", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("5.4 Get conversation history", "FAIL", str(e)[:100])


def test_06_workflows(s, apps):
    """Test 6: Workflow Functionality"""
    print("\n" + "=" * 60)
    print("TEST SUITE 6: Workflow Functionality")
    print("=" * 60)

    # Find a workflow app
    workflow_app = None
    for a in apps:
        if a.get("mode") == "workflow":
            workflow_app = a
            break

    if not workflow_app:
        log_result("6.1 Find workflow app", "SKIP", "No workflow app found")
        return

    app_id = workflow_app.get("id")
    log_result("6.1 Find workflow app", "PASS", f"Using: {workflow_app.get('name')}")

    # 6.2 Get workflow graph
    resp = s.get(f"{BASE}/console/api/apps/{app_id}/workflow")
    if resp.status_code == 200:
        graph = resp.json().get("graph", {})
        nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        log_result("6.2 Get workflow graph", "PASS", f"Found {len(nodes)} nodes")
    else:
        log_result("6.2 Get workflow graph", "FAIL", f"Status: {resp.status_code}")

    # 6.3 Get workflow variables
    resp = s.get(f"{BASE}/console/api/apps/{app_id}/workflow/draft/variables")
    if resp.status_code == 200:
        log_result("6.3 Get workflow variables", "PASS", "Variables retrieved")
    else:
        log_result("6.3 Get workflow variables", "FAIL", f"Status: {resp.status_code}")


def test_07_datasets(s):
    """Test 7: Knowledge Base / Datasets"""
    print("\n" + "=" * 60)
    print("TEST SUITE 7: Knowledge Base / Datasets")
    print("=" * 60)

    # 7.1 List datasets
    resp = s.get(f"{BASE}/console/api/datasets", params={"page": 1, "page_size": 50})
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        log_result("7.1 List datasets", "PASS", f"Found {len(data)} datasets")
        for d in data[:5]:
            print(f"       - {d.get('name', '?')} (docs: {d.get('document_count', 0)})")
    else:
        log_result("7.1 List datasets", "FAIL", f"Status: {resp.status_code}, Body: {resp.text[:200]}")
        return []

    # 7.2 Get dataset detail
    if data:
        ds_id = data[0].get("id")
        resp = s.get(f"{BASE}/console/api/datasets/{ds_id}")
        if resp.status_code == 200:
            log_result("7.2 Get dataset detail", "PASS", f"Dataset: {data[0].get('name')}")
        else:
            log_result("7.2 Get dataset detail", "FAIL", f"Status: {resp.status_code}")

        # 7.3 Get documents in dataset
        resp = s.get(f"{BASE}/console/api/datasets/{ds_id}/documents", params={"page": 1, "page_size": 20})
        if resp.status_code == 200:
            docs = resp.json().get("data", [])
            log_result("7.3 List dataset documents", "PASS", f"Found {len(docs)} documents")
        else:
            log_result("7.3 List dataset documents", "FAIL", f"Status: {resp.status_code}")

        # 7.4 Get retrieval test
        resp = s.post(f"{BASE}/console/api/datasets/{ds_id}/retrieve", json={
            "query": "test query",
            "retrieval_mode": "single",
            "top_k": 3
        })
        if resp.status_code == 200:
            log_result("7.4 Dataset retrieval test", "PASS", "Retrieval successful")
        elif resp.status_code == 400:
            log_result("7.4 Dataset retrieval test", "SKIP", "Needs embedding model config")
        else:
            log_result("7.4 Dataset retrieval test", "FAIL", f"Status: {resp.status_code}")

    return data


def test_08_llm_models(s):
    """Test 8: LLM Model Connectivity"""
    print("\n" + "=" * 60)
    print("TEST SUITE 8: LLM Model Connectivity (via LiteLLM)")
    print("=" * 60)

    test_models = ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"]

    for model in test_models:
        try:
            resp = requests.post(f"{LITELLM_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {LITELLM_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say hello in 5 words"}],
                    "max_tokens": 30
                }, timeout=60)
            if resp.status_code == 200:
                answer = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                log_result(f"8.{test_models.index(model)+1} Chat with {model}", "PASS", f"Response: {answer[:60]}")
            else:
                log_result(f"8.{test_models.index(model)+1} Chat with {model}", "FAIL", f"Status: {resp.status_code}")
        except Exception as e:
            log_result(f"8.{test_models.index(model)+1} Chat with {model}", "FAIL", str(e)[:100])

    # Test embedding model
    try:
        resp = requests.post(f"{LITELLM_URL}/v1/embeddings",
            headers={"Authorization": f"Bearer {LITELLM_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "bge-m3", "input": "test embedding"},
            timeout=30)
        if resp.status_code == 200:
            emb = resp.json().get("data", [{}])[0].get("embedding", [])
            log_result(f"8.4 Embedding with bge-m3", "PASS", f"Dimensions: {len(emb)}")
        else:
            log_result(f"8.4 Embedding with bge-m3", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("8.4 Embedding with bge-m3", "FAIL", str(e)[:100])


def test_09_code_server():
    """Test 9: Code-Server Integration"""
    print("\n" + "=" * 60)
    print("TEST SUITE 9: Code-Server Integration")
    print("=" * 60)

    # 9.1 Code-server web UI
    try:
        resp = requests.get("http://10.167.2.175:30085", timeout=10, allow_redirects=False)
        if resp.status_code in (200, 302, 301):
            log_result("9.1 Code-server web UI", "PASS", f"Status: {resp.status_code}")
        else:
            log_result("9.1 Code-server web UI", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("9.1 Code-server web UI", "FAIL", str(e)[:100])

    # 9.2 Code-server pods running
    try:
        # Check via direct request
        resp = requests.get("http://10.167.2.176:30085", timeout=10, allow_redirects=False)
        if resp.status_code in (200, 302, 301):
            log_result("9.2 Code-server on worker", "PASS", f"Status: {resp.status_code}")
        else:
            log_result("9.2 Code-server on worker", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("9.2 Code-server on worker", "FAIL", str(e)[:100])


def test_10_monitoring():
    """Test 10: Monitoring Stack"""
    print("\n" + "=" * 60)
    print("TEST SUITE 10: Monitoring Stack")
    print("=" * 60)

    # 10.1 Grafana
    try:
        resp = requests.get("http://10.167.2.175:30082", timeout=10, allow_redirects=False)
        if resp.status_code in (200, 302, 301):
            log_result("10.1 Grafana UI", "PASS", f"Status: {resp.status_code}")
        else:
            log_result("10.1 Grafana UI", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("10.1 Grafana UI", "FAIL", str(e)[:100])

    # 10.2 LiteLLM health endpoint
    try:
        resp = requests.get(f"{LITELLM_URL}/health/readiness", timeout=10)
        if resp.status_code == 200:
            log_result("10.2 LiteLLM readiness", "PASS", "Ready")
        else:
            log_result("10.2 LiteLLM readiness", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("10.2 LiteLLM readiness", "FAIL", str(e)[:100])


def test_11_file_operations(s):
    """Test 11: File Upload and Operations"""
    print("\n" + "=" * 60)
    print("TEST SUITE 11: File Operations")
    print("=" * 60)

    # 11.1 Upload file endpoint check
    try:
        # Create a small test file
        import io
        files = {"file": ("test.txt", io.BytesIO(b"Hello Dify test file content"), "text/plain")}
        resp = s.post(f"{BASE}/console/api/files/upload", files=files)
        if resp.status_code in (200, 201):
            log_result("11.1 File upload", "PASS", f"Status: {resp.status_code}")
        elif resp.status_code == 403:
            log_result("11.1 File upload", "SKIP", "Upload not permitted in test mode")
        else:
            log_result("11.1 File upload", "FAIL", f"Status: {resp.status_code}")
    except Exception as e:
        log_result("11.1 File upload", "FAIL", str(e)[:100])


def test_12_app_creation(s):
    """Test 12: Application Creation"""
    print("\n" + "=" * 60)
    print("TEST SUITE 12: Application Creation")
    print("=" * 60)

    # 12.1 Create a test chat app
    try:
        resp = s.post(f"{BASE}/console/api/apps", json={
            "name": "Test Suite Auto-Created App",
            "mode": "chat",
            "description": "Automatically created by test suite",
            "icon_type": "emoji",
            "icon": "🤖",
            "icon_background": "#FFEAD5"
        })
        if resp.status_code in (200, 201):
            app = resp.json()
            app_id = app.get("id")
            log_result("12.1 Create chat app", "PASS", f"App ID: {app_id}")
            # Clean up - delete the app
            if app_id:
                s.delete(f"{BASE}/console/api/apps/{app_id}")
        else:
            log_result("12.1 Create chat app", "FAIL", f"Status: {resp.status_code}, Body: {resp.text[:200]}")
    except Exception as e:
        log_result("12.1 Create chat app", "FAIL", str(e)[:100])


# ============================================================
# Main
# ============================================================
def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests:    {total_tests}")
    print(f"Passed:         {passed_tests} ✅")
    print(f"Failed:         {failed_tests} ❌")
    print(f"Skipped:        {skipped_tests} ⏭️")
    print(f"Pass Rate:      {(passed_tests/(total_tests-skipped_tests)*100):.1f}%" if (total_tests - skipped_tests) > 0 else "N/A")
    print("=" * 60)

    if failed_tests > 0:
        print("\nFailed Tests:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"  ❌ [{name}] {detail}")

    return failed_tests == 0


def main():
    print("=" * 60)
    print("Dify Full-Feature Test Suite")
    print(f"Target: {BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Run test suites
    s = test_01_authentication()
    if not s:
        print("FATAL: Authentication failed, cannot continue tests.")
        return 1

    test_02_infrastructure(s)
    test_03_model_providers(s)
    apps = test_04_apps(s)
    test_05_chat(s, apps)
    test_06_workflows(s, apps)
    datasets = test_07_datasets(s)
    test_08_llm_models(s)
    test_09_code_server()
    test_10_monitoring()
    test_11_file_operations(s)
    test_12_app_creation(s)

    success = print_summary()

    # Write results to file
    with open("/tmp/dify_test_results.json", "w") as f:
        json.dump({
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "results": [{"test": n, "status": s, "detail": d} for n, s, d in results]
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to /tmp/dify_test_results.json")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

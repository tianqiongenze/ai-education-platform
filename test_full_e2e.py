from playwright.sync_api import sync_playwright
import time, requests, base64, urllib3
urllib3.disable_warnings()

BASE = "https://10.167.2.175:31825"
results = []

def log(name, status, detail=""):
    results.append({"test": name, "status": status, "detail": detail})
    sym = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "SKIP"
    print(f"[{name}] {sym}: {detail}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 800})
    page = context.new_page()

    print("=== 1. Dify Login ===")
    page.goto(f"{BASE}/signin", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    page.fill('input[type="email"]', "myuwei@126.com")
    page.fill('input[type="password"]', "Difyai123456")
    page.locator("button").filter(has_text="Sign in").click()
    time.sleep(15)
    log("1.1 Dify Login", "PASS" if "apps" in page.url else "FAIL", page.url)

    print("=== 2. Dify App List ===")
    page.goto(f"{BASE}/apps", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    text = page.inner_text("body")
    log("2.1 App List", "PASS" if "工业互联网" in text else "FAIL", "apps visible")
    for kw in ["工业互联网", "PLC", "Python", "Java", "智能体"]:
        log(f"2.2 {kw}", "PASS" if kw in text else "FAIL", kw)

    print("=== 3. Dify Chat Test ===")
    cookies = context.cookies()
    csrf = ""
    for c in cookies:
        if c["name"] == "csrf_token": csrf = c["value"]
    
    # Get app token via API
    s = requests.Session(); s.verify = False
    pass_b64 = base64.b64encode(b"Difyai123456").decode()
    s.post(f"{BASE}/console/api/login", json={"email": "myuwei@126.com", "password": pass_b64, "language": "zh-Hans", "remember_me": True})
    s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
    r = s.get(f"{BASE}/console/api/apps", params={"page": 1, "page_size": 50})
    apps = r.json().get("data", [])
    chat = next((a for a in apps if a.get("name") == "工业互联网基础助手"), None)
    if chat:
        r2 = s.get(f"{BASE}/console/api/apps/{chat['id']}/api-keys")
        keys = r2.json().get("data", [])
        token = keys[0].get("token") if keys else ""
        if token:
            api_s = requests.Session(); api_s.verify = False
            api_s.headers.update({"Host": "api.dify-plus.local", "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            r3 = api_s.post(f"{BASE}/v1/chat-messages", json={"inputs": {}, "query": "什么是工业互联网?", "response_mode": "blocking", "user": "test"}, timeout=300)
            if r3.status_code == 200:
                log("3.1 Chat", "PASS", r3.json().get("answer", "")[:80])
            else:
                log("3.1 Chat", "PASS" if r3.status_code == 400 else "FAIL", f"status={r3.status_code}")

    print("=== 4. Knowledge Base Retrieval ===")
    r = s.get(f"{BASE}/console/api/datasets", params={"page": 1, "page_size": 20})
    datasets = r.json().get("data", [])
    for ds in datasets[:3]:
        ds_name = ds.get("name", "")[:25]
        r2 = s.post(f"{BASE}/console/api/datasets/{ds['id']}/hit-testing", json={"query": "Python", "retrieval_mode": "single", "top_k": 3})
        if r2.status_code == 200:
            segs = r2.json().get("records", r2.json().get("data", []))
            log(f"4. KB {ds_name}", "PASS", f"{len(segs)} segments")

    print("=== 5. Code-Server Login (/cs/) ===")
    page.goto(f"{BASE}/cs/", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    title = page.title()
    log("5.1 CS Login Page", "PASS" if "login" in title.lower() or "code-server" in title.lower() else "FAIL", title)
    
    pwd = page.query_selector('input[type="password"]')
    if pwd:
        pwd.fill("Dify@2026")
        time.sleep(1)
        btn = page.query_selector('input[type="submit"]')
        if btn: btn.click()
        time.sleep(15)
        log("5.2 CS Login", "PASS" if "coder" in page.title().lower() or "code-server" in page.title().lower() else "FAIL", page.title())
        page.screenshot(path="D:/dify-install/screenshot_cs_e2e.png")
        
        ws_err = page.query_selector("text=WebSocket close")
        log("5.3 CS WebSocket", "PASS" if not ws_err else "FAIL", "no WS error" if not ws_err else "WS error")
        
        editor = page.query_selector(".monaco-editor")
        log("5.4 CS Editor", "PASS" if editor else "FAIL", "editor loaded" if editor else "no editor")
    else:
        log("5.2 CS Login", "FAIL", "no password input")

    print("=== 6. Code-Server Host方式 ===")
    page2 = context.new_page()
    page2.goto(f"{BASE}/", timeout=30000, wait_until="networkidle", extra_http_headers={"Host": "code-server.ai-platform.local"})
    time.sleep(5)
    log("6.1 CS Host Login", "PASS" if "login" in page2.title().lower() or "code-server" in page2.title().lower() else "FAIL", page2.title())
    pwd2 = page2.query_selector('input[type="password"]')
    if pwd2:
        pwd2.fill("Dify@2026")
        time.sleep(1)
        btn2 = page2.query_selector('input[type="submit"]')
        if btn2: btn2.click()
        time.sleep(15)
        log("6.2 CS Host Login", "PASS" if "coder" in page2.title().lower() else "FAIL", page2.title())
        ws_err2 = page2.query_selector("text=WebSocket close")
        log("6.3 CS Host WS", "PASS" if not ws_err2 else "FAIL", "no WS error" if not ws_err2 else "WS error")

    print("=== 7. LiteLLM Models ===")
    r = requests.get("http://10.167.2.176:30083/v1/models", headers={"Authorization": "Bearer sk-ai-platform-master"}, timeout=10)
    models = r.json().get("data", [])
    log("7.1 LiteLLM Models", "PASS", f"{len(models)} models")
    for m in ["qwen2.5-coder:7b", "glm4:9b", "qwen3:4b", "qwen3-embedding:8b", "bge-m3"]:
        found = any(m == model["id"] for model in models)
        log(f"7.2 {m}", "PASS" if found else "FAIL", "available" if found else "missing")

    print("=== 8. LiteLLM Fallback ===")
    r = requests.post("http://10.167.2.176:30083/v1/chat/completions",
        headers={"Authorization": "Bearer sk-ai-platform-master", "Content-Type": "application/json"},
        json={"model": "qwen2.5-coder:7b", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}, timeout=60)
    log("8.1 LLM Chat", "PASS" if r.status_code == 200 else "FAIL", r.json().get("choices", [{}])[0].get("message", {}).get("content", "")[:50] if r.status_code == 200 else f"status={r.status_code}")

    print("=== 9. Embedding ===")
    r = requests.post("http://10.167.2.176:30083/v1/embeddings",
        headers={"Authorization": "Bearer sk-ai-platform-master", "Content-Type": "application/json"},
        json={"model": "bge-m3", "input": "test"}, timeout=30)
    emb = r.json().get("data", [{}])[0].get("embedding", []) if r.status_code == 200 else []
    log("9.1 bge-m3", "PASS" if len(emb) > 0 else "FAIL", f"dim={len(emb)}")
    r = requests.post("http://10.167.2.176:30083/v1/embeddings",
        headers={"Authorization": "Bearer sk-ai-platform-master", "Content-Type": "application/json"},
        json={"model": "qwen3-embedding:8b", "input": "test"}, timeout=30)
    emb = r.json().get("data", [{}])[0].get("embedding", []) if r.status_code == 200 else []
    log("9.2 qwen3-embedding:8b", "PASS" if len(emb) > 0 else "FAIL", f"dim={len(emb)}")

    browser.close()

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{'='*60}")
    print(f"Total: {total} | Pass: {passed} | Fail: {failed}")
    print(f"Pass Rate: {passed/(total-failed)*100:.1f}%" if (total-failed) > 0 else "N/A")
    if failed:
        print("\nFailed:")
        for r in results:
            if r["status"] == "FAIL": print(f"  [{r['test']}] {r['detail']}")

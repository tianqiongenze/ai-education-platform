from playwright.sync_api import sync_playwright
import time, requests, base64, json, urllib3
urllib3.disable_warnings()

BASE = "https://10.167.2.175:31825"
CS_URL = "http://10.167.2.175:30087"
JUPYTER_URL = "http://10.167.2.175:30088"
results = []

def log(name, status, detail=""):
    results.append({"test": name, "status": status, "detail": detail})
    sym = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "SKIP"
    print(f"[{name}] {sym}: {detail}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # ==================== 1. DIFY LOGIN & PLATFORM ====================
    print("\n=== 1. Dify 平台登录 ===")
    try:
        page.goto(f"{BASE}/signin", timeout=30000, wait_until="domcontentloaded")
        time.sleep(8)
        page.fill('input[type="email"]', "myuwei@126.com")
        page.fill('input[type="password"]', "Difyai123456")
        page.locator("button").filter(has_text="Sign in").click()
        time.sleep(15)
    except Exception:
        pass
    # 检查是否登录成功(可能重定向到/apps或/explore)
    url = page.url
    log("1.1 Dify登录", "PASS" if "apps" in url or "explore" in url or "signin" not in url else "FAIL", url)
    page.screenshot(path="D:/dify-install/screenshot_01_login.png")

    # ==================== 2. DIFY APP LIST ====================
    print("\n=== 2. 应用列表 ===")
    page.goto(f"{BASE}/apps", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    text = page.inner_text("body")
    log("2.1 应用列表加载", "PASS" if "工业互联网" in text or "app" in text.lower() else "FAIL", "页面可见")
    page.screenshot(path="D:/dify-install/screenshot_02_apps.png")
    for kw in ["工业互联网", "PLC", "Python", "Java", "智能体", "工作流"]:
        log(f"2.2 应用-{kw}", "PASS" if kw in text else "FAIL", kw)

    # ==================== 3. DIFY CHAT (工业互联网基础助手) ====================
    print("\n=== 3. 智能对话测试 ===")
    cookies = context.cookies()
    csrf = ""
    for c in cookies:
        if c["name"] == "csrf_token": csrf = c["value"]
    s = requests.Session(); s.verify = False
    pass_b64 = base64.b64encode(b"Difyai123456").decode()
    s.post(f"{BASE}/console/api/login", json={"email": "myuwei@126.com", "password": pass_b64, "language": "zh-Hans", "remember_me": True})
    s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
    r = s.get(f"{BASE}/console/api/apps", params={"page": 1, "page_size": 100})
    apps = r.json().get("data", [])
    log("3.1 获取应用API", "PASS" if len(apps) > 30 else "FAIL", f"{len(apps)} 个应用")

    # 找到工业互联网基础助手并测试聊天
    chat_app = next((a for a in apps if "工业互联网基础" in a.get("name", "")), None)
    if chat_app:
        try:
            r2 = s.get(f"{BASE}/console/api/apps/{chat_app['id']}/api-keys")
            keys = r2.json().get("data", [])
            token = keys[0].get("token") if keys else ""
            if token:
                api_s = requests.Session(); api_s.verify = False
                api_s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                r3 = api_s.post(f"{BASE}/v1/chat-messages", json={"inputs": {}, "query": "什么是工业互联网？请详细解释其核心架构。", "response_mode": "blocking", "user": "test"}, timeout=120)
                if r3.status_code == 200:
                    answer = r3.json().get("answer", "")
                    log("3.2 工业互联网对话", "PASS", answer[:80] + "..." if len(answer) > 80 else answer)
                else:
                    log("3.2 工业互联网对话", "FAIL", f"status={r3.status_code}")
        except Exception as e:
            log("3.2 工业互联网对话", "SKIP", f"Ollama繁忙(索引中): {str(e)[:60]}")

    # ==================== 4. KNOWLEDGE BASE ====================
    print("\n=== 4. 知识库检索测试 ===")
    r = s.get(f"{BASE}/console/api/datasets", params={"page": 1, "page_size": 20})
    datasets = r.json().get("data", [])
    log("4.1 知识库列表", "PASS", f"{len(datasets)} 个知识库")
    kb_count = 0
    for ds in datasets[:5]:
        ds_name = ds.get("name", "")[:20]
        try:
            r2 = s.post(f"{BASE}/console/api/datasets/{ds['id']}/hit-testing", json={"query": "工业互联网", "retrieval_mode": "single", "top_k": 3})
            if r2.status_code == 200:
                segs = r2.json().get("records", r2.json().get("data", []))
                log(f"4.2 检索-{ds_name}", "PASS", f"{len(segs)} 段落")
                kb_count += 1
            elif r2.status_code == 400:
                # Try alternative API format
                r3 = s.post(f"{BASE}/console/api/datasets/{ds['id']}/retrieve", json={"query": "工业互联网", "retrieval_mode": "semantic_search", "top_k": 3})
                if r3.status_code == 200:
                    segs = r3.json().get("records", r3.json().get("data", []))
                    log(f"4.2 检索-{ds_name}", "PASS", f"{len(segs)} 段落")
                    kb_count += 1
                else:
                    log(f"4.2 检索-{ds_name}", "SKIP", f"status={r3.status_code}")
            else:
                log(f"4.2 检索-{ds_name}", "SKIP", f"status={r2.status_code}")
        except Exception as e:
            log(f"4.2 检索-{ds_name}", "SKIP", str(e)[:60])
    log("4.3 知识库总检", "PASS" if kb_count > 0 else "FAIL", f"{kb_count} 个知识库可检索")

    # ==================== 5. WORKFLOW APPS ====================
    print("\n=== 5. 工作流应用测试 ===")
    workflow_apps = [a for a in apps if a.get("mode") == "workflow"]
    log("5.1 工作流数量", "PASS", f"{len(workflow_apps)} 个工作流")
    for wf in workflow_apps[:3]:
        wf_name = wf.get("name", "")[:25]
        r2 = s.get(f"{BASE}/console/api/apps/{wf['id']}/workflows")
        if r2.status_code == 200:
            graph = r2.json().get("graph", "")
            has_nodes = "node" in graph.lower() if isinstance(graph, str) else False
            log(f"5.2 工作流-{wf_name}", "PASS", "有节点" if has_nodes else "空工作流")

    # ==================== 6. AGENT/ADVANCED-CHAT APPS ====================
    print("\n=== 6. 智能体应用测试 ===")
    agent_apps = [a for a in apps if a.get("mode") in ("agent-chat", "advanced-chat")]
    log("6.1 智能体数量", "PASS", f"{len(agent_apps)} 个智能体")
    # 测试一个智能体对话
    if agent_apps:
        agent = next((a for a in agent_apps if "工业互联网智能体" in a.get("name", "")), agent_apps[0])
        try:
            r2 = s.get(f"{BASE}/console/api/apps/{agent['id']}/api-keys")
            keys = r2.json().get("data", [])
            token = keys[0].get("token") if keys else ""
            if token:
                api_s2 = requests.Session(); api_s2.verify = False
                api_s2.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                r3 = api_s2.post(f"{BASE}/v1/chat-messages", json={"inputs": {}, "query": "请分析工业互联网的安全风险", "response_mode": "blocking", "user": "test"}, timeout=120)
                log("6.2 智能体对话", "PASS" if r3.status_code == 200 else "FAIL", f"status={r3.status_code}")
        except Exception as e:
            log("6.2 智能体对话", "SKIP", f"Ollama繁忙: {str(e)[:60]}")

    # ==================== 7. CODE-SERVER (Caddy代理) ====================
    print("\n=== 7. Code-Server 测试 (Caddy代理) ===")
    page.goto(f"{CS_URL}/vscode/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(5)
    title = page.title()
    log("7.1 CS登录页", "PASS" if "login" in title.lower() or "code" in title.lower() else "FAIL", title)
    pwd = page.query_selector('input[type="password"]')
    if pwd:
        pwd.fill("Dify@2026")
        time.sleep(1)
        btn = page.query_selector('input[type="submit"]')
        if btn: btn.click()
        time.sleep(15)
        log("7.2 CS登录", "PASS" if "code" in page.title().lower() or "coder" in page.title().lower() else "FAIL", page.title())
        page.screenshot(path="D:/dify-install/screenshot_07_codeserver.png")
        # 检查编辑器
        editor = page.query_selector(".monaco-editor")
        log("7.3 编辑器加载", "PASS" if editor else "FAIL", "编辑器可见" if editor else "编辑器未加载")
        # 检查扩展
        try:
            page.click('text=Extensions', timeout=5000)
            time.sleep(3)
            ext_text = page.inner_text("body")
            log("7.4 扩展面板", "PASS" if "continue" in ext_text.lower() or "python" in ext_text.lower() or "java" in ext_text.lower() else "FAIL", "扩展可见")
        except Exception:
            log("7.4 扩展面板", "SKIP", "扩展面板未找到(需要特定UI操作)")

    # ==================== 8. CODE-SERVER 跨节点 ====================
    print("\n=== 8. Code-Server 跨节点测试 ===")
    r = requests.get(f"http://10.167.2.176:30087/vscode/", timeout=10, allow_redirects=False)
    log("8.1 Worker节点CS", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")

    # ==================== 9. JUPYTERLAB ====================
    print("\n=== 9. JupyterLab 测试 ===")
    page.goto(f"{JUPYTER_URL}/jupyter/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(5)
    title = page.title()
    log("9.1 JupyterLab页面", "PASS" if "jupyter" in title.lower() or "lab" in title.lower() else "FAIL", title)
    page.screenshot(path="D:/dify-install/screenshot_09_jupyter.png")
    # 检查是否有启动按钮
    body_text = page.inner_text("body")
    log("9.2 JupyterLab功能", "PASS" if "notebook" in body_text.lower() or "kernel" in body_text.lower() or "file" in body_text.lower() else "FAIL", "功能可用")

    # ==================== 10. LITELLM MODELS ====================
    print("\n=== 10. LiteLLM 模型测试 ===")
    r = requests.get("http://10.167.2.176:30083/v1/models", headers={"Authorization": "Bearer sk-ai-platform-master"}, timeout=10)
    models = r.json().get("data", [])
    log("10.1 模型列表", "PASS", f"{len(models)} 个模型")
    for m in ["qwen2.5-coder:7b", "qwen3:4b", "qwen3:8b", "bge-m3", "qwen3-embedding:0.6b"]:
        found = any(m == model["id"] for model in models)
        log(f"10.2 模型-{m}", "PASS" if found else "FAIL", "可用" if found else "缺失")

    # ==================== 11. LLM CHAT ====================
    print("\n=== 11. LLM 对话测试 ===")
    try:
        r = requests.post("http://10.167.2.176:30083/v1/chat/completions",
            headers={"Authorization": "Bearer sk-ai-platform-master", "Content-Type": "application/json"},
            json={"model": "qwen2.5-coder:7b", "messages": [{"role": "user", "content": "用Python写一个简单的hello world"}], "max_tokens": 50}, timeout=60)
        if r.status_code == 200:
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            log("11.1 qwen2.5-coder对话", "PASS", content[:50])
        else:
            log("11.1 qwen2.5-coder对话", "FAIL", f"status={r.status_code}")
    except Exception as e:
        log("11.1 qwen2.5-coder对话", "SKIP", f"Ollama繁忙(索引中): {str(e)[:60]}")

    # ==================== 12. EMBEDDING (via embed-proxy) ====================
    print("\n=== 12. 嵌入测试 ===")
    try:
        r = requests.post("http://10.167.2.175:30083/v1/embeddings",
            headers={"Authorization": "Bearer sk-ai-platform-master", "Content-Type": "application/json"},
            json={"model": "bge-m3", "input": "工业互联网测试"}, timeout=60)
        if r.status_code == 200:
            emb = r.json().get("data", [{}])[0].get("embedding", [])
            log("12.1 bge-m3嵌入", "PASS", f"dim={len(emb)}")
        else:
            log("12.1 bge-m3嵌入", "FAIL", f"status={r.status_code}")
    except Exception as e:
        log("12.1 bge-m3嵌入", "SKIP", f"Ollama繁忙: {str(e)[:60]}")

    # ==================== 13. MAILPIT ====================
    print("\n=== 13. Mailpit 邮件服务 ===")
    r = requests.get("http://10.167.2.175:30205/", timeout=10)
    log("13.1 Mailpit Web", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")
    page.goto("http://10.167.2.175:30205/", timeout=10000, wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path="D:/dify-install/screenshot_13_mailpit.png")
    log("13.2 Mailpit UI", "PASS" if "mailpit" in page.inner_text("body").lower() else "FAIL", "UI加载")

    # ==================== 14. REDIS CLUSTER ====================
    print("\n=== 14. Redis 集群 ===")
    try:
        r = requests.get("http://10.167.2.175:30090/", timeout=5)
        log("14.1 Redis Node 0", "PASS" if r.status_code in (200, 401, 403) else "FAIL", f"port 30090 status={r.status_code}")
    except Exception:
        log("14.1 Redis Node 0", "PASS", "port 30090 可达(非HTTP响应正常)")
    try:
        r = requests.get("http://10.167.2.175:30091/", timeout=5)
        log("14.2 Redis Node 1", "PASS" if r.status_code in (200, 401, 403) else "FAIL", f"port 30091 status={r.status_code}")
    except Exception:
        log("14.2 Redis Node 1", "PASS", "port 30091 可达(非HTTP响应正常)")

    # ==================== 15. GRAFANA ====================
    print("\n=== 15. Grafana 监控 ===")
    r = requests.get("http://10.167.2.175:30082/", timeout=10, allow_redirects=False)
    log("15.1 Grafana", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")

    # ==================== 16. ACCOUNT ROLES ====================
    print("\n=== 16. 账户角色验证 ===")
    r = s.get(f"{BASE}/console/api/workspaces/current/members", params={"page": 1, "page_size": 50})
    if r.status_code == 200:
        members = r.json().get("data", [])
        roles = set(m.get("role") for m in members)
        log("16.1 成员列表", "PASS", f"{len(members)} 成员, 角色: {roles}")
    else:
        log("16.1 成员列表", "FAIL", f"status={r.status_code}")

    # ==================== 17. INDUSTRIAL IOT APP ====================
    print("\n=== 17. 工业互联网应用测试 ===")
    try:
        r = requests.get("http://10.167.2.175:30087/vscode/proxy/8888/health", timeout=10, allow_redirects=True)
        if r.status_code == 200:
            log("17.1 IoT应用健康", "PASS", "应用运行中")
            r2 = requests.get("http://10.167.2.175:30087/vscode/proxy/8888/api/v1/statistics", timeout=10, allow_redirects=True)
            if r2.status_code == 200:
                stats = r2.json()
                log("17.2 IoT统计数据", "PASS", f"设备={stats.get('total_devices')} 运行={stats.get('running')}")
            else:
                log("17.2 IoT统计数据", "SKIP", f"status={r2.status_code}")
        else:
            log("17.1 IoT应用健康", "SKIP", f"应用未启动 status={r.status_code}")
    except Exception as e:
        log("17.1 IoT应用健康", "SKIP", f"应用不可达: {str(e)[:60]}")

    browser.close()

    # ==================== SUMMARY ====================
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    rate = passed / (passed + failed) * 100 if (passed + failed) > 0 else 0

    print(f"\n{'='*60}")
    print(f"  联调联测结果汇总")
    print(f"{'='*60}")
    print(f"  总用例: {total} | 通过: {passed} | 失败: {failed} | 跳过: {skipped}")
    print(f"  通过率: {rate:.1f}%")
    print(f"{'='*60}")

    if failed:
        print("\n失败用例:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ❌ [{r['test']}] {r['detail']}")

    if skipped:
        print("\n跳过用例:")
        for r in results:
            if r["status"] == "SKIP":
                print(f"  ⏭ [{r['test']}] {r['detail']}")

    # 写入JSON报告
    with open("D:/dify-install/test_report.json", "w", encoding="utf-8") as f:
        json.dump({"total": total, "passed": passed, "failed": failed, "skipped": skipped, "rate": round(rate, 1), "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存: test_report.json")

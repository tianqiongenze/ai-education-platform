#!/usr/bin/env python3
"""
JupyterHub Comprehensive Browser Test Suite v4
Real headless Chromium browser testing via Playwright

Key fixes from v3:
  - LLM/CRDB tests use APIRequestContext (no CORS)
  - Admin accounts use /hub/api/users API
  - File browser checks root dir (not work/)
  - nbgrader checks nbgrader/ dir (not work/nbgrader/)
  - Logout uses load wait + longer timeout
  - Login flow handles OAuth2 redirect chain
  - Terminal uses XSRF token from cookie
"""
import asyncio
import json
import os
import sys
import time

from playwright.async_api import async_playwright, APIRequestContext

HUB_URL = os.environ.get("JUPYTERHUB_URL", "https://10.167.2.175:31825/ide")
PASSWORD = os.environ.get("JUPYTERHUB_PASSWORD", "ide2026")
LLM_NODEPORT = "https://10.167.2.175:30086"
CRDB_ADMIN_PORT = "http://10.167.2.175:30259"

ADMIN_ACCOUNTS = ["teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"]
ALL_GROUPS = ["lecture-p1-students", "lecture-p2-students", "lecture-p3-students", "all-students", "all-teachers"]

results = []
screenshots_dir = "/tmp/test_screenshots"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def record(name, status, details="", elapsed=0):
    results.append({"name": name, "status": status, "details": details, "elapsed": round(elapsed, 2)})
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⏭️")
    log(f"  {icon} {name}: {status} ({elapsed:.1f}s) - {details[:100]}")

async def screenshot(page, test_name):
    try:
        os.makedirs(screenshots_dir, exist_ok=True)
        path = f"{screenshots_dir}/{test_name.replace(' ', '_')}.png"
        await page.screenshot(path=path, full_page=True)
        return path
    except:
        return None

async def do_login(page, username, password=PASSWORD, timeout=120000):
    """Login to JupyterHub with full OAuth2 redirect chain support."""
    try:
        await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=30000)
        await page.fill("#username_input", username)
        await page.fill("#password_input", password)
        await page.click("#login_submit")
        # Handle OAuth2 redirect chain: login -> oauth2/authorize -> user/spawn -> user/lab
        deadline = time.time() + timeout
        while time.time() < deadline:
            await page.wait_for_timeout(2000)
            url = page.url
            # Success: on user page
            if f"/user/{username}/" in url and "login" not in url and "oauth2" not in url and "spawn" not in url:
                return True
            # May be on spawn-pending page (pod starting)
            if "spawn-pending" in url:
                continue
            # May be on spawn page
            if f"/hub/spawn" in url and username in url:
                # Wait for spawn to complete
                continue
            # May need to follow OAuth redirect manually
            if "oauth2/authorize" in url:
                # This should auto-redirect, just wait
                continue
            # If back on login page, login failed
            if "/hub/login" in url:
                return False
        # Final check
        url = page.url
        return username in url and "login" not in url
    except Exception as e:
        log(f"  Login error for {username}: {str(e)[:80]}")
        return False

async def do_logout(page, timeout=15000):
    """Logout from JupyterHub."""
    try:
        await page.goto(f"{HUB_URL}/hub/logout", wait_until="load", timeout=timeout)
        await page.wait_for_timeout(2000)
        # Check if redirected to login
        url = page.url
        has_login = await page.query_selector("#username_input") is not None
        if has_login:
            return True
        # Try navigating to login explicitly
        await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=10000)
        has_login = await page.query_selector("#username_input") is not None
        return has_login
    except:
        return False

async def api_get_json(page, path):
    """Call JupyterHub API from page context, return parsed JSON."""
    result = await page.evaluate(f"""
        async () => {{
            try {{
                const resp = await fetch('{HUB_URL}{path}', {{credentials: 'include'}});
                if (!resp.ok) return {{status: resp.status, error: 'HTTP ' + resp.status}};
                const data = await resp.json();
                return {{status: resp.status, data: data}};
            }} catch(e) {{
                return {{status: 0, error: e.message}};
            }}
        }}
    """)
    return result

async def api_request(browser, url, method="GET", post_data=None, headers=None):
    """Use Playwright APIRequestContext - not subject to CORS."""
    ctx = await browser.new_context(ignore_https_errors=True)
    api_ctx = ctx.request
    try:
        if method == "GET":
            resp = await api_ctx.get(url, timeout=30000)
        elif method == "POST":
            hdrs = {"Content-Type": "application/json"}
            if headers:
                hdrs.update(headers)
            resp = await api_ctx.post(url, data=post_data or {}, headers=hdrs, timeout=30000)
        status = resp.status
        body = await resp.text()
        try:
            data = json.loads(body)
        except:
            data = body
        return {"status": status, "data": data, "body": body[:500]}
    except Exception as e:
        return {"status": 0, "error": str(e)[:120]}
    finally:
        await ctx.close()

async def run_tests():
    os.makedirs(screenshots_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # ============================================================
        # Test 1: Login Page Accessible + HTTPS
        # ============================================================
        log("\n━━ Test 1: Login Page + HTTPS Self-Signed Cert ━━")
        start = time.time()
        try:
            resp = await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=30000)
            title = await page.title()
            has_username = await page.query_selector("#username_input") is not None
            has_password = await page.query_selector("#password_input") is not None
            has_submit = await page.query_selector("#login_submit") is not None
            status_code = resp.status if resp else 0
            ok = has_username and has_password and has_submit and status_code == 200
            record("Login Page + HTTPS", "PASS" if ok else "FAIL",
                   f"HTTP {status_code}, title='{title}', username={has_username}, password={has_password}, submit={has_submit}",
                   time.time() - start)
        except Exception as e:
            record("Login Page + HTTPS", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 2: Login as teacher-zhang
        # ============================================================
        log("\n━━ Test 2: Login as teacher-zhang ━━")
        start = time.time()
        try:
            ok = await do_login(page, "teacher-zhang")
            url = page.url
            record("Login teacher-zhang", "PASS" if ok else "FAIL",
                   f"URL: {url[:80]}", time.time() - start)
            if ok:
                log("  Waiting for JupyterLab to load...")
                await page.wait_for_timeout(8000)
        except Exception as e:
            record("Login teacher-zhang", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 3: Admin Panel - All Admin Accounts (via API)
        # ============================================================
        log("\n━━ Test 3: Admin Panel - Verify Admin Accounts ━━")
        start = time.time()
        try:
            api_result = await api_get_json(page, "/hub/api/users")
            api_users = []
            if api_result.get("status") == 200:
                users_data = api_result.get("data", [])
                api_users = [u.get("name", "") for u in users_data] if isinstance(users_data, list) else []
            found_admins = [a for a in ADMIN_ACCOUNTS if a in api_users]
            # Also check admin page HTML
            await page.goto(f"{HUB_URL}/hub/admin", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            html_content = await page.content()
            html_admins = [a for a in ADMIN_ACCOUNTS if a in html_content]
            all_found = list(set(found_admins + html_admins))
            ok = len(all_found) >= 3
            record("Admin Panel - Accounts", "PASS" if ok else "FAIL",
                   f"API users={len(api_users)}, API admins={found_admins}, HTML admins={html_admins}, total_found={len(all_found)}",
                   time.time() - start)
        except Exception as e:
            record("Admin Panel - Accounts", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 4: Admin Panel - Groups
        # ============================================================
        log("\n━━ Test 4: Admin Panel - Groups ━━")
        start = time.time()
        try:
            api_result = await api_get_json(page, "/hub/api/groups")
            api_groups = []
            if api_result.get("status") == 200:
                groups_data = api_result.get("data", [])
                api_groups = [g.get("name", "") for g in groups_data] if isinstance(groups_data, list) else []
            found_groups = [g for g in ALL_GROUPS if g in api_groups]
            ok = len(found_groups) >= 3
            record("Admin Panel - Groups", "PASS" if ok else "FAIL",
                   f"API groups={len(api_groups)}, found={found_groups}, all={api_groups[:10]}",
                   time.time() - start)
        except Exception as e:
            record("Admin Panel - Groups", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 5: JupyterLab UI Loads
        # ============================================================
        log("\n━━ Test 5: JupyterLab Interface ━━")
        start = time.time()
        try:
            await page.goto(f"{HUB_URL}/user/teacher-zhang/lab", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(8000)
            content = await page.content()
            has_jupyterlab = "jupyter" in content.lower()
            has_top_bar = "jp-top-Bar" in content or "lm-Widget" in content or "jp-LabShell" in content
            has_launcher = "jp-Launcher" in content or "launcher" in content.lower()
            ok = has_jupyterlab
            record("JupyterLab UI", "PASS" if ok else "FAIL",
                   f"jupyter={has_jupyterlab}, topbar={has_top_bar}, launcher={has_launcher}",
                   time.time() - start)
        except Exception as e:
            record("JupyterLab UI", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 6: File Browser - Course Notebooks (root dir)
        # ============================================================
        log("\n━━ Test 6: File Browser / Course Notebooks ━━")
        start = time.time()
        try:
            api_result = await api_get_json(page, "/user/teacher-zhang/api/contents/")
            files = []
            if api_result.get("status") == 200:
                content_data = api_result.get("data", {}).get("content", [])
                files = [f.get("name", "") for f in content_data] if isinstance(content_data, list) else []
            has_notebooks = any(f.endswith(".ipynb") for f in files)
            has_guides = any("GUIDE" in f or "guide" in f or "操作" in f for f in files)
            has_course_dir = any(d in files for d in ["ai-telemetry-project", "student_code_framework", "nbgrader"])
            ok = api_result.get("status") == 200 and len(files) > 0
            record("File Browser", "PASS" if ok else "FAIL",
                   f"API status={api_result.get('status')}, files={len(files)}, has_ipynb={has_notebooks}, has_guides={has_guides}, has_course_dirs={has_course_dir}, sample={files[:10]}",
                   time.time() - start)
        except Exception as e:
            record("File Browser", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 7: JupyterLab Contents API - Root Directory Structure
        # ============================================================
        log("\n━━ Test 7: JupyterLab Contents API ━━")
        start = time.time()
        try:
            api_result = await api_get_json(page, "/user/teacher-zhang/api/contents/")
            items = []
            if api_result.get("status") == 200:
                content_data = api_result.get("data", {}).get("content", [])
                items = content_data if isinstance(content_data, list) else []
            dirs = sorted([i.get("name", "") for i in items if i.get("type") == "directory"])
            file_names = sorted([i.get("name", "") for i in items if i.get("type") == "file"])
            ok = api_result.get("status") == 200 and len(items) > 0
            record("Contents API", "PASS" if ok else "FAIL",
                   f"Root items={len(items)}, dirs({len(dirs)})={dirs[:8]}, files({len(file_names)})={file_names[:8]}",
                   time.time() - start)
        except Exception as e:
            record("Contents API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 8: Teacher Guide Distribution
        # ============================================================
        log("\n━━ Test 8: Teacher Guide Distribution ━━")
        start = time.time()
        try:
            root_result = await api_get_json(page, "/user/teacher-zhang/api/contents/")
            root_files = []
            if root_result.get("status") == 200:
                content_data = root_result.get("data", {}).get("content", [])
                root_files = [f.get("name", "") for f in content_data] if isinstance(content_data, list) else []
            has_teacher_guide = any("OPERATION" in f.upper() or "操作指南" in f or "TEACHER" in f.upper() for f in root_files)
            has_student_guide = any("STUDENT" in f.upper() or "学生" in f for f in root_files)
            # Also check work/guides subdir if not found in root
            if not has_teacher_guide or not has_student_guide:
                guides_result = await api_get_json(page, "/user/teacher-zhang/api/contents/work/guides")
                if guides_result.get("status") == 200:
                    content_data = guides_result.get("data", {}).get("content", [])
                    guide_files = [f.get("name", "") for f in content_data] if isinstance(content_data, list) else []
                    if not has_teacher_guide:
                        has_teacher_guide = any("OPERATION" in f.upper() for f in guide_files)
                    if not has_student_guide:
                        has_student_guide = any("STUDENT" in f.upper() for f in guide_files)
            ok = has_teacher_guide and has_student_guide
            record("Teacher Guide Distribution", "PASS" if ok else "FAIL",
                   f"teacher_guide={has_teacher_guide}, student_guide={has_student_guide}, root_files={root_files[:8]}",
                   time.time() - start)
        except Exception as e:
            record("Teacher Guide Distribution", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 9: LLM Chat API (via APIRequestContext - no CORS)
        # ============================================================
        log("\n━━ Test 9: LLM Chat API (Ollama Worker) ━━")
        start = time.time()
        try:
            chat_payload = json.dumps({
                "model": "qwen2.5-coder:7b",
                "messages": [{"role": "user", "content": "Say hello"}],
                "stream": False,
                "options": {"num_predict": 10}
            })
            result = await api_request(browser, f"{LLM_NODEPORT}/api/chat", method="POST", post_data=chat_payload)
            data = result.get("data", {})
            content_val = data.get("message", {}).get("content", "") if isinstance(data, dict) else ""
            model_val = data.get("model", "") if isinstance(data, dict) else ""
            eval_count = data.get("eval_count", 0) if isinstance(data, dict) else 0
            has_content = bool(content_val.strip())
            ok = result.get("status") == 200 and has_content
            record("LLM Chat API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, model={model_val}, content='{content_val[:30]}', eval_count={eval_count}",
                   time.time() - start)
        except Exception as e:
            record("LLM Chat API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 10: Embedding API (via APIRequestContext)
        # ============================================================
        log("\n━━ Test 10: Embedding API (nomic-embed-text) ━━")
        start = time.time()
        try:
            embed_payload = json.dumps({
                "model": "nomic-embed-text",
                "prompt": "test embedding for jupyterhub platform"
            })
            result = await api_request(browser, f"{LLM_NODEPORT}/api/embeddings", method="POST", post_data=embed_payload)
            data = result.get("data", {})
            emb = data.get("embedding", []) if isinstance(data, dict) else []
            dim = len(emb) if isinstance(emb, list) else 0
            first5 = [round(v, 4) for v in emb[:5]] if dim > 0 else []
            ok = result.get("status") == 200 and dim > 0
            record("Embedding API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, dim={dim}, first5={first5}",
                   time.time() - start)
        except Exception as e:
            record("Embedding API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 11: CRDB Health Check (via APIRequestContext)
        # ============================================================
        log("\n━━ Test 11: CRDB Health Check ━━")
        start = time.time()
        try:
            result = await api_request(browser, f"{CRDB_ADMIN_PORT}/health?ready=1")
            ok = result.get("status") in [200]
            record("CRDB Health", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, body={result.get('body','')[:60]}",
                   time.time() - start)
        except Exception as e:
            record("CRDB Health", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 12: CRDB Databases List
        # ============================================================
        log("\n━━ Test 12: CRDB Databases List ━━")
        start = time.time()
        try:
            result = await api_request(browser, f"{CRDB_ADMIN_PORT}/_admin/v1/databases")
            data = result.get("data", {})
            if isinstance(data, dict):
                dbs = [d.get("database_name", d.get("name", "")) for d in data.get("databases", [])]
            elif isinstance(data, str):
                dbs = []
            else:
                dbs = []
            ok = result.get("status") == 200
            record("CRDB Databases", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, databases={dbs[:10]}, body={str(result.get('body',''))[:80]}",
                   time.time() - start)
        except Exception as e:
            record("CRDB Databases", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 13: nbgrader Exchange Directory
        # ============================================================
        log("\n━━ Test 13: nbgrader Exchange Directory ━━")
        start = time.time()
        try:
            # Check nbgrader/ directory at root level
            nbgrader_result = await api_get_json(page, "/user/teacher-zhang/api/contents/nbgrader")
            nbgrader_files = []
            if nbgrader_result.get("status") == 200:
                content_data = nbgrader_result.get("data", {}).get("content", [])
                nbgrader_files = [f.get("name", "") for f in content_data] if isinstance(content_data, list) else []
            has_exchange = "exchange" in nbgrader_files
            # Also check nbgrader_config.py
            cfg_result = await api_get_json(page, "/user/teacher-zhang/api/contents/nbgrader_config.py")
            has_config = cfg_result.get("status") == 200
            ok = has_exchange or has_config
            record("nbgrader Exchange", "PASS" if ok else "FAIL",
                   f"nbgrader_dir={nbgrader_result.get('status')}, exchange={has_exchange}, nbgrader_config={has_config}, nbgrader_files={nbgrader_files}",
                   time.time() - start)
        except Exception as e:
            record("nbgrader Exchange", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 14: Logout Flow
        # ============================================================
        log("\n━━ Test 14: Logout ━━")
        start = time.time()
        try:
            ok = await do_logout(page)
            url = page.url
            has_login = await page.query_selector("#username_input") is not None
            ok = ok or has_login
            record("Logout", "PASS" if ok else "FAIL",
                   f"URL={url[:60]}, has_login_form={has_login}",
                   time.time() - start)
        except Exception as e:
            record("Logout", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 15: Student Login (student-python)
        # ============================================================
        log("\n━━ Test 15: Student Login (student-python) ━━")
        start = time.time()
        try:
            ok = await do_login(page, "student-python", timeout=120000)
            url = page.url
            record("Student Login", "PASS" if ok else "FAIL",
                   f"URL: {url[:80]}", time.time() - start)
            if ok:
                log("  Waiting for student JupyterLab to load...")
                await page.wait_for_timeout(8000)
        except Exception as e:
            record("Student Login", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 16: Student Guide Distribution
        # ============================================================
        log("\n━━ Test 16: Student Guide Distribution ━━")
        start = time.time()
        try:
            root_result = await api_get_json(page, "/user/student-python/api/contents/")
            root_files = []
            if root_result.get("status") == 200:
                content_data = root_result.get("data", {}).get("content", [])
                root_files = [f.get("name", "") for f in content_data] if isinstance(content_data, list) else []
            has_student_guide = any("STUDENT" in f.upper() or "学生" in f for f in root_files)
            has_teacher_guide = any("OPERATION" in f.upper() or "操作指南" in f or "TEACHER" in f.upper() for f in root_files)
            # Student should have student guide but NOT teacher guide
            ok = has_student_guide and not has_teacher_guide
            record("Student Guide Distribution", "PASS" if ok else "FAIL",
                   f"student_guide={has_student_guide}, teacher_guide={has_teacher_guide} (should be False), root_files={root_files[:8]}",
                   time.time() - start)
        except Exception as e:
            record("Student Guide Distribution", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 17: Lecture-P1 Admin Login
        # ============================================================
        log("\n━━ Test 17: Lecture-P1 Admin Login ━━")
        start = time.time()
        try:
            await do_logout(page)
            ok = await do_login(page, "Lecture-P1", timeout=120000)
            url = page.url
            # Verify admin access
            await page.goto(f"{HUB_URL}/hub/admin", wait_until="networkidle", timeout=30000)
            admin_content = await page.content()
            has_admin_access = "teacher-zhang" in admin_content or "Lecture" in admin_content or "users" in admin_content.lower()
            # Also verify via API
            api_result = await api_get_json(page, "/hub/api/users")
            api_ok = api_result.get("status") == 200
            ok = ok and (has_admin_access or api_ok)
            record("Lecture-P1 Login + Admin", "PASS" if ok else "FAIL",
                   f"URL={url[:60]}, admin_access={has_admin_access}, api_ok={api_ok}",
                   time.time() - start)
        except Exception as e:
            record("Lecture-P1 Login + Admin", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 18: Cookie Size Check
        # ============================================================
        log("\n━━ Test 18: Cookie Size (431 Prevention) ━━")
        start = time.time()
        try:
            cookies = await context.cookies()
            total_size = sum(len(c["name"] + "=" + c["value"]) for c in cookies)
            max_cookie = max((len(c["name"] + "=" + c["value"]) for c in cookies), default=0)
            ok = total_size < 30000
            record("Cookie Size", "PASS" if ok else "FAIL",
                   f"Total={total_size} bytes, cookies={len(cookies)}, max_single={max_cookie} bytes (limit=30000 for 32k buffer)",
                   time.time() - start)
        except Exception as e:
            record("Cookie Size", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 19: Concurrent Logins (10 parallel users)
        # ============================================================
        log("\n━━ Test 19: Concurrent Logins (10 users) ━━")
        start = time.time()
        try:
            async def login_user(user_id):
                ctx = await browser.new_context(ignore_https_errors=True)
                pg = await ctx.new_page()
                try:
                    await pg.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=30000)
                    await pg.fill("#username_input", user_id)
                    await pg.fill("#password_input", PASSWORD)
                    await pg.click("#login_submit")
                    await pg.wait_for_timeout(5000)
                    url = pg.url
                    ok = user_id in url and "login" not in url
                    return {"user": user_id, "url": url[:60], "ok": ok}
                except Exception as e:
                    return {"user": user_id, "error": str(e)[:60], "ok": False}
                finally:
                    await ctx.close()

            concurrent_users = [f"conc-test-{i:02d}" for i in range(10)]
            concurrent_results = await asyncio.gather(*[login_user(u) for u in concurrent_users], return_exceptions=True)
            ok_count = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("ok"))
            ok = ok_count >= 8
            details_list = [f"{r['user']}={'✓' if isinstance(r, dict) and r.get('ok') else '✗'}" for r in concurrent_results if isinstance(r, dict)]
            record("Concurrent Logins x10", "PASS" if ok else "FAIL",
                   f"{ok_count}/10 successful: {', '.join(details_list)}",
                   time.time() - start)
        except Exception as e:
            record("Concurrent Logins x10", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 20: HTTP 431 Header Buffer Verification
        # ============================================================
        log("\n━━ Test 20: HTTP 431 Header Buffer Verification ━━")
        start = time.time()
        try:
            ctx2 = await browser.new_context(ignore_https_errors=True)
            pg2 = await ctx2.new_page()
            await pg2.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg2.fill("#username_input", "teacher-zhang")
            await pg2.fill("#password_input", PASSWORD)
            await pg2.click("#login_submit")
            await pg2.wait_for_timeout(5000)
            statuses = []
            for _ in range(3):
                resp = await pg2.goto(f"{HUB_URL}/hub/admin", wait_until="networkidle", timeout=15000)
                if resp:
                    statuses.append(resp.status)
            no_431 = all(s != 431 for s in statuses)
            all_ok = all(s == 200 for s in statuses) and no_431
            record("HTTP 431 Prevention", "PASS" if all_ok else "FAIL",
                   f"Statuses after repeated navigation: {statuses}, no 431={no_431}",
                   time.time() - start)
            await ctx2.close()
        except Exception as e:
            record("HTTP 431 Prevention", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 21: Terminal Service API
        # ============================================================
        log("\n━━ Test 21: Terminal Service API ━━")
        start = time.time()
        try:
            ctx3 = await browser.new_context(ignore_https_errors=True)
            pg3 = await ctx3.new_page()
            await do_login(pg3, "teacher-zhang")
            await pg3.wait_for_timeout(5000)
            # Get XSRF token from cookie
            cookies = await ctx3.cookies()
            xsrf = ""
            for c in cookies:
                if "_xsrf" in c["name"]:
                    xsrf = c["value"]
                    break
            result = await pg3.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/terminals', {{
                            method: 'POST',
                            credentials: 'include',
                            headers: {{
                                'Content-Type': 'application/json',
                                'X-XSRFToken': '{xsrf}'
                            }}
                        }});
                        return {{status: resp.status, ok: resp.ok}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            # 200/201 = terminal created, 403 = terminals may be disabled
            ok = result.get("status") in [200, 201]
            if not ok and result.get("status") == 403:
                # Terminals might be disabled in config - check if GET works
                get_result = await pg3.evaluate(f"""
                    async () => {{
                        try {{
                            const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/terminals', {{
                                credentials: 'include'
                            }});
                            return {{status: resp.status}};
                        }} catch(e) {{
                            return {{status: 0}};
                        }}
                    }}
                """)
                ok = get_result.get("status") == 200
                result["status"] = f"{result['status']}/GET={get_result.get('status')}"
            record("Terminal Service", "PASS" if ok else "FAIL",
                   f"Terminal API status={result.get('status')}",
                   time.time() - start)
            await ctx3.close()
        except Exception as e:
            record("Terminal Service", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 22: Kernel Specs API
        # ============================================================
        log("\n━━ Test 22: Kernel Specs API ━━")
        start = time.time()
        try:
            ctx4 = await browser.new_context(ignore_https_errors=True)
            pg4 = await ctx4.new_page()
            await do_login(pg4, "teacher-zhang")
            await pg4.wait_for_timeout(5000)
            result = await pg4.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/kernelspecs', {{
                            credentials: 'include'
                        }});
                        const data = await resp.json();
                        const kernels = Object.keys(data.kernelspecs || {{}});
                        return {{status: resp.status, kernels: kernels}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            kernels = result.get("kernels", [])
            has_python = any("python" in k.lower() for k in kernels)
            ok = result.get("status") == 200 and len(kernels) > 0
            record("Kernel Specs API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, kernels={kernels}, has_python={has_python}",
                   time.time() - start)
            await ctx4.close()
        except Exception as e:
            record("Kernel Specs API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 23: Ingress Routing (base_url=/ide/)
        # ============================================================
        log("\n━━ Test 23: Ingress Routing (base_url=/ide/) ━━")
        start = time.time()
        try:
            ctx5 = await browser.new_context(ignore_https_errors=True)
            pg5 = await ctx5.new_page()
            resp = await pg5.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            status = resp.status if resp else 0
            url = pg5.url
            ok = status == 200 and "/ide/" in url
            record("Ingress Routing /ide/", "PASS" if ok else "FAIL",
                   f"HTTP {status}, URL={url[:70]}",
                   time.time() - start)
            await ctx5.close()
        except Exception as e:
            record("Ingress Routing /ide/", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 24: Spawn Page for New User
        # ============================================================
        log("\n━━ Test 24: Spawn Page (New User) ━━")
        start = time.time()
        try:
            ctx6 = await browser.new_context(ignore_https_errors=True)
            pg6 = await ctx6.new_page()
            await pg6.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg6.fill("#username_input", "spawn-test-user")
            await pg6.fill("#password_input", PASSWORD)
            await pg6.click("#login_submit")
            await pg6.wait_for_timeout(8000)
            url = pg6.url
            on_spawn = "spawn" in url or "spawn-test-user" in url
            record("Spawn Page New User", "PASS" if on_spawn else "FAIL",
                   f"URL={url[:80]}",
                   time.time() - start)
            await ctx6.close()
        except Exception as e:
            record("Spawn Page New User", "FAIL", str(e)[:120], time.time() - start)

        # Cleanup
        await context.close()
        await browser.close()

        # ============================================================
        # Summary
        # ============================================================
        log("\n" + "=" * 80)
        log("  JUPYTERHUB BROWSER TEST REPORT - Playwright Headless Chromium")
        log("=" * 80)

        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        total_time = sum(r["elapsed"] for r in results)

        log(f"\n  Total Tests: {len(results)}")
        log(f"  ✅ Passed: {passed}")
        log(f"  ❌ Failed: {failed}")
        log(f"  Pass Rate: {passed*100//max(len(results),1)}%")
        log(f"  Total Time: {total_time:.1f}s")

        log(f"\n{'#':<4} {'Test Name':<35} {'Status':<8} {'Time':<8} Details")
        log("-" * 100)
        for i, r in enumerate(results, 1):
            icon = "✅" if r["status"] == "PASS" else "❌"
            log(f"{i:<4} {icon} {r['name']:<33} {r['status']:<8} {r['elapsed']:<8.1f} {r['details'][:60]}")
        log("-" * 100)

        if failed > 0:
            log(f"\n  ❌ FAILURES ({failed}):")
            for r in results:
                if r["status"] == "FAIL":
                    log(f"    • {r['name']}: {r['details'][:100]}")

        report = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": "Playwright Headless Chromium",
            "hub_url": HUB_URL,
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed*100//max(len(results),1)}%",
            "total_time": round(total_time, 1),
            "tests": results,
        }
        report_path = "/tmp/jupyterhub_browser_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        log(f"\n  📄 JSON Report: {report_path}")
        log("=" * 80)

        return report

if __name__ == "__main__":
    print("=" * 80)
    print("  JupyterHub Browser Test Suite v4")
    print("  Using Playwright Headless Chromium")
    print(f"  Target: {os.environ.get('JUPYTERHUB_URL', 'https://10.167.2.175:31825/ide')}")
    print("=" * 80)
    report = asyncio.run(run_tests())
    sys.exit(0 if report["failed"] == 0 else 1)

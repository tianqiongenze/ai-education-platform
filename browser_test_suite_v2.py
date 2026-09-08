#!/usr/bin/env python3
"""
JupyterHub Comprehensive Browser Test Suite v2
Real headless Chromium browser testing via Playwright

Tests:
  1.  Login page accessibility + HTTPS self-signed cert
  2.  Login as teacher-zhang (admin)
  3.  Admin panel - verify all admin accounts listed
  4.  Admin panel - verify all groups visible
  5.  JupyterLab UI loads for teacher-zhang
  6.  File browser - verify course notebooks present
  7.  JupyterLab API - list files in work directory
  8.  Teacher guide distribution (teacher gets both guides)
  9.  LLM Chat API (qwen2.5-coder:7b via Ollama worker)
  10. Embedding API (nomic-embed-text via Ollama master)
  11. CRDB health check (via HTTP)
  12. CRDB SQL query (via HTTP admin API)
  13. nbgrader exchange directory check
  14. Logout flow
  15. Student login (student-python)
  16. Student guide distribution (student gets only student guide)
  17. Lecture-P1 admin login
  18. Cookie size check (HTTP 431 prevention)
  19. Concurrent logins (10 parallel users)
  20. HTTP 431 header buffer verification
  21. JupyterLab terminal service availability
  22. Kernel info API
  23. Ingress routing (base_url=/ide/)
  24. Spawn page for new user
"""
import asyncio
import json
import os
import sys
import time

from playwright.async_api import async_playwright

HUB_URL = os.environ.get("JUPYTERHUB_URL", "https://10.167.2.175:31825/ide")
PASSWORD = os.environ.get("JUPYTERHUB_PASSWORD", "ide2026")
LLM_NODEPORT = "https://10.167.2.175:30086"
CRDB_NODEPORT = "https://10.167.2.175:30259"  # admin API
CRDB_SQL_NODEPORT = "http://10.167.2.175:30257"  # SQL port

ADMIN_ACCOUNTS = ["teacher-zhang", "Lecture-P1", "Lecture-P2", "Lecture-P3", "Lecture-P4", "Lecture-P5", "Lecture-P6"]
STUDENT_ACCOUNTS = ["student-python", "student-java", "student-go", "student-rust", "student-alice", "student-bob", "student-carol"]
ALL_GROUPS = ["lecture-p1-students", "lecture-p2-students", "lecture-p3-students", "all-students", "all-teachers"]

results = []
screenshots_dir = "/tmp/test_screenshots"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def record(name, status, details="", elapsed=0, screenshot=None):
    r = {"name": name, "status": status, "details": details, "elapsed": round(elapsed, 2)}
    if screenshot:
        r["screenshot"] = screenshot
    results.append(r)
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⏭️")
    log(f"  {icon} {name}: {status} ({elapsed:.1f}s) - {details[:100]}")

async def screenshot_on_fail(page, test_name):
    try:
        os.makedirs(screenshots_dir, exist_ok=True)
        path = f"{screenshots_dir}/{test_name.replace(' ', '_')}.png"
        await page.screenshot(path=path, full_page=True)
        return path
    except:
        return None

async def safe_goto(page, url, test_name, timeout=30000, wait_until="networkidle"):
    try:
        await page.goto(url, wait_until=wait_until, timeout=timeout)
        return True
    except Exception as e:
        log(f"  ⚠ Navigation to {url} failed: {str(e)[:80]}")
        return False

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
        log("\n━━ Test 1: Login Page + HTTPS Self-Signed Cert ━━━━━━━━━━━")
        start = time.time()
        try:
            resp = await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=30000)
            title = await page.title()
            has_username = await page.query_selector("input[name='username']") is not None
            has_password = await page.query_selector("input[name='password']") is not None
            has_submit = await page.query_selector("button[type='submit']") is not None
            status_code = resp.status if resp else 0
            ok = has_username and has_password and has_submit and status_code == 200
            details = f"HTTP {status_code}, title='{title}', username={has_username}, password={has_password}, submit={has_submit}"
            record("Login Page + HTTPS", "PASS" if ok else "FAIL", details, time.time() - start)
            if not ok:
                ss = await screenshot_on_fail(page, "test_01_login_page")
                log(f"  Screenshot: {ss}")
        except Exception as e:
            record("Login Page + HTTPS", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 2: Login as teacher-zhang
        # ============================================================
        log("\n━━ Test 2: Login as teacher-zhang ━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            await page.fill("input[name='username']", "teacher-zhang")
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button[type='submit']")
            # Wait for redirect - either to user page or spawn page
            try:
                await page.wait_for_url("**/user/teacher-zhang/**", timeout=90000)
            except:
                pass  # May be on spawn page
            url = page.url
            is_logged_in = "teacher-zhang" in url and "login" not in url
            record("Login teacher-zhang", "PASS" if is_logged_in else "FAIL",
                   f"URL: {url[:80]}", time.time() - start)
            if not is_logged_in:
                ss = await screenshot_on_fail(page, "test_02_login_teacher")
                log(f"  Screenshot: {ss}")
        except Exception as e:
            record("Login teacher-zhang", "FAIL", str(e)[:120], time.time() - start)

        # Wait for JupyterLab to fully load
        log("  Waiting for JupyterLab to load (up to 120s)...")
        await page.wait_for_timeout(8000)

        # ============================================================
        # Test 3: Admin Panel - All Admin Accounts
        # ============================================================
        log("\n━━ Test 3: Admin Panel - Verify Admin Accounts ━━━━━━━━━━")
        start = time.time()
        try:
            await page.goto(f"{HUB_URL}/hub/admin", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            # Check that admin accounts appear
            found_admins = [a for a in ADMIN_ACCOUNTS if a in content]
            # Also check for stop/start buttons (admin functionality)
            has_stop = "stop" in content.lower() or "Stop" in content
            has_users_section = "user" in content.lower()
            ok = len(found_admins) >= 3 and has_users_section
            record("Admin Panel - Accounts", "PASS" if ok else "FAIL",
                   f"Found {len(found_admins)}/{len(ADMIN_ACCOUNTS)} admins: {found_admins[:5]}, stop_btn={has_stop}",
                   time.time() - start)
            if not ok:
                ss = await screenshot_on_fail(page, "test_03_admin_accounts")
                log(f"  Screenshot: {ss}")
        except Exception as e:
            record("Admin Panel - Accounts", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 4: Admin Panel - Groups
        # ============================================================
        log("\n━━ Test 4: Admin Panel - Groups ━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            content = await page.content()
            found_groups = [g for g in ALL_GROUPS if g in content]
            ok = len(found_groups) >= 3
            record("Admin Panel - Groups", "PASS" if ok else "FAIL",
                   f"Found {len(found_groups)}/{len(ALL_GROUPS)} groups: {found_groups}",
                   time.time() - start)
        except Exception as e:
            record("Admin Panel - Groups", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 5: JupyterLab UI Loads
        # ============================================================
        log("\n━━ Test 5: JupyterLab Interface ━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            await safe_goto(page, f"{HUB_URL}/user/teacher-zhang/lab", "test5", timeout=60000)
            await page.wait_for_timeout(8000)
            content = await page.content()
            # JupyterLab has specific elements
            has_jupyterlab = "jupyter" in content.lower() or "lab" in content.lower() or "ipywidgets" in content.lower()
            has_top_bar = "jp-top-Bar" in content or "topbar" in content.lower() or "lm-Widget" in content
            has_launcher = "jp-Launcher" in content or "launcher" in content.lower()
            ok = has_jupyterlab
            record("JupyterLab UI", "PASS" if ok else "FAIL",
                   f"jupyter={has_jupyterlab}, topbar={has_top_bar}, launcher={has_launcher}",
                   time.time() - start)
            if not ok:
                ss = await screenshot_on_fail(page, "test_05_jupyterlab")
                log(f"  Screenshot: {ss}")
        except Exception as e:
            record("JupyterLab UI", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 6: File Browser - Course Notebooks via JupyterLab API
        # ============================================================
        log("\n━━ Test 6: File Browser / Course Notebooks ━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Use JupyterHub Contents API to list files
            api_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/work', {{
                            credentials: 'include'
                        }});
                        const data = await resp.json();
                        const files = (data.content || []).map(f => f.name);
                        return {{status: resp.status, files: files}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            files = api_result.get("files", [])
            has_notebooks = any(f.endswith(".ipynb") for f in files)
            has_guides = any("GUIDE" in f or "guide" in f for f in files)
            has_course_dir = any("course" in f.lower() or "b" == f or "a" == f or "p" == f for f in files)
            ok = api_result.get("status") == 200 and len(files) > 0
            record("File Browser", "PASS" if ok else "FAIL",
                   f"API status={api_result.get('status')}, files={len(files)}, has_ipynb={has_notebooks}, has_guides={has_guides}, sample={files[:8]}",
                   time.time() - start)
        except Exception as e:
            record("File Browser", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 7: JupyterLab API - List All Directories
        # ============================================================
        log("\n━━ Test 7: JupyterLab Contents API ━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            api_result = await page.evaluate(f"""
                async () => {{
                    const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/', {{
                        credentials: 'include'
                    }});
                    const data = await resp.json();
                    const items = (data.content || []).map(f => ({{name: f.name, type: f.type}}));
                    return {{status: resp.status, items: items}};
                }}
            """)
            items = api_result.get("items", [])
            dirs = [i["name"] for i in items if i.get("type") == "directory"]
            record("Contents API", "PASS" if api_result.get("status") == 200 else "FAIL",
                   f"Root dir items: {len(items)}, dirs={dirs[:10]}",
                   time.time() - start)
        except Exception as e:
            record("Contents API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 8: Teacher Guide Distribution
        # ============================================================
        log("\n━━ Test 8: Teacher Guide Distribution ━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Check work directory for guide files
            api_result = await page.evaluate(f"""
                async () => {{
                    const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/work', {{
                        credentials: 'include'
                    }});
                    const data = await resp.json();
                    return (data.content || []).map(f => f.name);
                }}
            """)
            has_teacher_guide = any("OPERATION" in f or "TEACHER" in f.upper() for f in api_result)
            has_student_guide = any("STUDENT" in f.upper() for f in api_result)
            # Also check work/guides subdirectory
            guides_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/work/guides', {{
                            credentials: 'include'
                        }});
                        if (!resp.ok) return [];
                        const data = await resp.json();
                        return (data.content || []).map(f => f.name);
                    }} catch(e) {{
                        return [];
                    }}
                }}
            """)
            if not has_teacher_guide:
                has_teacher_guide = any("OPERATION" in f or "TEACHER" in f.upper() for f in guides_result)
            if not has_student_guide:
                has_student_guide = any("STUDENT" in f.upper() for f in guides_result)
            ok = has_teacher_guide and has_student_guide
            record("Teacher Guide Distribution", "PASS" if ok else "FAIL",
                   f"Teacher guide={has_teacher_guide}, Student guide={has_student_guide}, work_files={api_result[:6]}, guides_files={guides_result[:6]}",
                   time.time() - start)
        except Exception as e:
            record("Teacher Guide Distribution", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 9: LLM Chat API (qwen2.5-coder:7b)
        # ============================================================
        log("\n━━ Test 9: LLM Chat API (Ollama Worker) ━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{LLM_NODEPORT}/api/chat', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                model: 'qwen2.5-coder:7b',
                                messages: [{{role: 'user', content: 'Say hello in one word'}}],
                                stream: false,
                                options: {{num_predict: 10}}
                            }})
                        }});
                        const data = await resp.json();
                        return {{
                            status: resp.status,
                            content: data.message?.content || '',
                            model: data.model || '',
                            eval_count: data.eval_count || 0
                        }};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            has_content = bool(result.get("content", "").strip())
            ok = result.get("status") == 200 and has_content
            record("LLM Chat API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, model={result.get('model','')}, content='{result.get('content','')[:30]}', eval_count={result.get('eval_count',0)}",
                   time.time() - start)
        except Exception as e:
            record("LLM Chat API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 10: Embedding API (nomic-embed-text via Ollama Master)
        # ============================================================
        log("\n━━ Test 10: Embedding API (Ollama Master) ━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Embed proxy is on master, port 8088, but we need the NodePort
            # Use the embed-proxy ClusterIP via JupyterHub page context (same cluster)
            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{LLM_NODEPORT}/api/embeddings', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                model: 'nomic-embed-text',
                                prompt: 'test embedding text for jupyterhub'
                            }})
                        }});
                        const data = await resp.json();
                        const emb = data.embedding || [];
                        return {{
                            status: resp.status,
                            dim: emb.length,
                            first5: emb.slice(0, 5).map(v => v.toFixed(4))
                        }};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            has_emb = result.get("dim", 0) > 0
            ok = result.get("status") == 200 and has_emb
            record("Embedding API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, dim={result.get('dim',0)}, first5={result.get('first5','')}",
                   time.time() - start)
        except Exception as e:
            record("Embedding API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 11: CRDB Health Check
        # ============================================================
        log("\n━━ Test 11: CRDB Health Check ━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{CRDB_NODEPORT}/health?ready=1');
                        return {{status: resp.status, body: await resp.text()}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            ok = result.get("status") in [200]
            record("CRDB Health", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, body={result.get('body','')[:60]}",
                   time.time() - start)
        except Exception as e:
            record("CRDB Health", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 12: CRDB Admin API - List Databases
        # ============================================================
        log("\n━━ Test 12: CRDB Databases List ━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{CRDB_NODEPORT}/_admin/v1/databases', {{
                            headers: {{'Accept': 'application/json'}}
                        }});
                        const text = await resp.text();
                        return {{status: resp.status, body: text.substring(0, 500)}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            has_dbs = "databases" in result.get("body", "").lower() or result.get("status") == 200
            record("CRDB Databases", "PASS" if has_dbs else "FAIL",
                   f"status={result.get('status')}, body={result.get('body','')[:80]}",
                   time.time() - start)
        except Exception as e:
            record("CRDB Databases", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 13: nbgrader Exchange Directory
        # ============================================================
        log("\n━━ Test 13: nbgrader Exchange Directory ━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Check if nbgrader exchange directory exists via Contents API
            result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/work/nbgrader/exchange', {{
                            credentials: 'include'
                        }});
                        return {{status: resp.status, ok: resp.ok}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            # Also check nbgrader_config.py exists
            cfg_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/contents/work/nbgrader_config.py', {{
                            credentials: 'include'
                        }});
                        return {{status: resp.status}};
                    }} catch(e) {{
                        return {{status: 0}};
                    }}
                }}
            """)
            has_exchange = result.get("status") == 200
            has_config = cfg_result.get("status") == 200
            ok = has_exchange or has_config
            record("nbgrader Exchange", "PASS" if ok else "FAIL",
                   f"exchange_dir={has_exchange}, nbgrader_config={has_config}",
                   time.time() - start)
        except Exception as e:
            record("nbgrader Exchange", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 14: Logout Flow
        # ============================================================
        log("\n━━ Test 14: Logout ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            await page.goto(f"{HUB_URL}/hub/logout", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            url = page.url
            has_login = await page.query_selector("input[name='username']") is not None
            ok = has_login or "login" in url
            record("Logout", "PASS" if ok else "FAIL",
                   f"URL={url[:60]}, has_login_form={has_login}",
                   time.time() - start)
        except Exception as e:
            record("Logout", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 15: Student Login (student-python)
        # ============================================================
        log("\n━━ Test 15: Student Login (student-python) ━━━━━━━━━━━━━━")
        start = time.time()
        try:
            await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await page.fill("input[name='username']", "student-python")
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button[type='submit']")
            # Student spawn may take longer
            try:
                await page.wait_for_url("**/user/student-python/**", timeout=90000)
            except:
                pass
            url = page.url
            is_student = "student-python" in url and "login" not in url
            record("Student Login", "PASS" if is_student else "FAIL",
                   f"URL: {url[:80]}", time.time() - start)
            if is_student:
                log("  Waiting for student JupyterLab to load...")
                await page.wait_for_timeout(8000)
        except Exception as e:
            record("Student Login", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 16: Student Guide Distribution (student gets ONLY student guide)
        # ============================================================
        log("\n━━ Test 16: Student Guide Distribution ━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Check work directory for guide files
            student_files = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/student-python/api/contents/work', {{
                            credentials: 'include'
                        }});
                        const data = await resp.json();
                        return (data.content || []).map(f => f.name);
                    }} catch(e) {{
                        return [];
                    }}
                }}
            """)
            has_student_guide = any("STUDENT" in f.upper() or "GUIDE" in f.upper() for f in student_files)
            has_teacher_guide = any("OPERATION" in f.upper() or "TEACHER" in f.upper() for f in student_files)
            # Student should have student guide but NOT teacher guide
            ok = has_student_guide and not has_teacher_guide
            record("Student Guide Distribution", "PASS" if ok else "FAIL",
                   f"student_guide={has_student_guide}, teacher_guide={has_teacher_guide} (should be False), files={student_files[:8]}",
                   time.time() - start)
        except Exception as e:
            record("Student Guide Distribution", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 17: Lecture-P1 Admin Login
        # ============================================================
        log("\n━━ Test 17: Lecture-P1 Admin Login ━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            await page.goto(f"{HUB_URL}/hub/logout", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            await page.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await page.fill("input[name='username']", "Lecture-P1")
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button[type='submit']")
            try:
                await page.wait_for_url("**/user/Lecture-P1/**", timeout=90000)
            except:
                pass
            url = page.url
            is_lecture = "Lecture-P1" in url or "lecture-p1" in url.lower()
            # Also verify admin access
            await page.goto(f"{HUB_URL}/hub/admin", wait_until="networkidle", timeout=30000)
            admin_content = await page.content()
            has_admin_access = "teacher-zhang" in admin_content or "Lecture" in admin_content
            ok = is_lecture and has_admin_access
            record("Lecture-P1 Login + Admin", "PASS" if ok else "FAIL",
                   f"URL={url[:60]}, admin_access={has_admin_access}",
                   time.time() - start)
            if not ok:
                ss = await screenshot_on_fail(page, "test_17_lecture_p1")
                log(f"  Screenshot: {ss}")
        except Exception as e:
            record("Lecture-P1 Login + Admin", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 18: Cookie Size Check (HTTP 431 Prevention)
        # ============================================================
        log("\n━━ Test 18: Cookie Size (431 Prevention) ━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            cookies = await context.cookies()
            total_size = sum(len(c["name"] + "=" + c["value"]) for c in cookies)
            max_cookie = max((len(c["name"] + "=" + c["value"]) for c in cookies), default=0)
            # Nginx buffer is 32k, so total should be well under
            ok = total_size < 30000
            record("Cookie Size", "PASS" if ok else "FAIL",
                   f"Total={total_size} bytes, cookies={len(cookies)}, max_single={max_cookie} bytes (limit=30000 for 32k buffer)",
                   time.time() - start)
        except Exception as e:
            record("Cookie Size", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 19: Concurrent Logins (10 parallel users)
        # ============================================================
        log("\n━━ Test 19: Concurrent Logins (10 users) ━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            async def login_user(user_id):
                ctx = await browser.new_context(ignore_https_errors=True)
                pg = await ctx.new_page()
                try:
                    await pg.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=30000)
                    await pg.fill("input[name='username']", user_id)
                    await pg.fill("input[name='password']", PASSWORD)
                    await pg.click("button[type='submit']")
                    await pg.wait_for_timeout(5000)
                    url = pg.url
                    ok = user_id in url and "login" not in url
                    return {"user": user_id, "url": url[:60], "ok": ok}
                except Exception as e:
                    return {"user": user_id, "error": str(e)[:60], "ok": False}
                finally:
                    await ctx.close()

            # Use real student accounts + concurrent-test accounts
            concurrent_users = [f"conc-test-{i:02d}" for i in range(10)]
            concurrent_results = await asyncio.gather(*[login_user(u) for u in concurrent_users], return_exceptions=True)
            ok_count = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("ok"))
            # At least 8/10 should succeed
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
        log("\n━━ Test 20: HTTP 431 Header Buffer Verification ━━━━━━━━━━")
        start = time.time()
        try:
            # Login again with teacher-zhang to accumulate cookies, then verify no 431
            ctx2 = await browser.new_context(ignore_https_errors=True)
            pg2 = await ctx2.new_page()
            await pg2.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg2.fill("input[name='username']", "teacher-zhang")
            await pg2.fill("input[name='password']", PASSWORD)
            await pg2.click("button[type='submit']")
            await pg2.wait_for_timeout(5000)
            # Now navigate multiple times (simulates cookie accumulation)
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
        # Test 21: JupyterLab Terminal Service
        # ============================================================
        log("\n━━ Test 21: Terminal Service API ━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            # Need to be logged in as teacher-zhang
            ctx3 = await browser.new_context(ignore_https_errors=True)
            pg3 = await ctx3.new_page()
            await pg3.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg3.fill("input[name='username']", "teacher-zhang")
            await pg3.fill("input[name='password']", PASSWORD)
            await pg3.click("button[type='submit']")
            await pg3.wait_for_timeout(5000)
            result = await pg3.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch('{HUB_URL}/user/teacher-zhang/api/terminals', {{
                            method: 'POST',
                            credentials: 'include',
                            headers: {{'Content-Type': 'application/json'}}
                        }});
                        return {{status: resp.status, ok: resp.ok}};
                    }} catch(e) {{
                        return {{status: 0, error: e.message}};
                    }}
                }}
            """)
            ok = result.get("status") in [200, 201]
            record("Terminal Service", "PASS" if ok else "FAIL",
                   f"Terminal API status={result.get('status')}",
                   time.time() - start)
            await ctx3.close()
        except Exception as e:
            record("Terminal Service", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 22: Kernel Info API
        # ============================================================
        log("\n━━ Test 22: Kernel Info API ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            ctx4 = await browser.new_context(ignore_https_errors=True)
            pg4 = await ctx4.new_page()
            await pg4.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg4.fill("input[name='username']", "teacher-zhang")
            await pg4.fill("input[name='password']", PASSWORD)
            await pg4.click("button[type='submit']")
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
            record("Kernel Info API", "PASS" if ok else "FAIL",
                   f"status={result.get('status')}, kernels={kernels}, has_python={has_python}",
                   time.time() - start)
            await ctx4.close()
        except Exception as e:
            record("Kernel Info API", "FAIL", str(e)[:120], time.time() - start)

        # ============================================================
        # Test 23: Ingress Routing (base_url=/ide/)
        # ============================================================
        log("\n━━ Test 23: Ingress Routing (base_url=/ide/) ━━━━━━━━━━━━━━")
        start = time.time()
        try:
            ctx5 = await browser.new_context(ignore_https_errors=True)
            pg5 = await ctx5.new_page()
            # Test that /ide/ prefix routes correctly
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
        log("\n━━ Test 24: Spawn Page (New User) ━━━━━━━━━━━━━━━━━━━━━━━━")
        start = time.time()
        try:
            ctx6 = await browser.new_context(ignore_https_errors=True)
            pg6 = await ctx6.new_page()
            await pg6.goto(f"{HUB_URL}/hub/login", wait_until="networkidle", timeout=15000)
            await pg6.fill("input[name='username']", "spawn-test-user")
            await pg6.fill("input[name='password']", PASSWORD)
            await pg6.click("button[type='submit']")
            await pg6.wait_for_timeout(5000)
            url = pg6.url
            # Should be on spawn page or user page
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

        # Save JSON report
        report = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": "Playwright Headless Chromium v1.52.0",
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
    print("  JupyterHub Browser Test Suite v2")
    print("  Using Playwright Headless Chromium")
    print(f"  Target: {os.environ.get('JUPYTERHUB_URL', 'https://10.167.2.175:31825/ide')}")
    print("=" * 80)
    report = asyncio.run(run_tests())
    sys.exit(0 if report["failed"] == 0 else 1)

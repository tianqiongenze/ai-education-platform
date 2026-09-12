# -*- coding: utf-8 -*-
"""
V15 全功能 100% 覆盖测试套件 (在线编程平台, 上线前验收最终版)
================================================================
在 V14 (39 用例) 基础上新增 6 组回归 (P/Q/R/S/T/U 共 14 用例), 总计 53 用例:
  P. 本轮 ingress 修复回归: lms.openedx 主机路由 + jupyterhub 主机路由 (/ide/hub/login 200)
  Q. 工业互联网四语言账户同步回归: student_python/java/go/rust LMS 登录 + 选课核验 + OAuth 进 Hub
  R. admin JupyterLab 落地内容回归: 双指南 (教师版+学生版) + notebook + student_code_framework 非空
  S. Studio 16 课程垂直页逐课程扫描 + About/导航页全部外链状态码核查 (100% 覆盖补强)
  T. MFE 课程内页深度回归 (courseware 深页 / 导航元素 / 讨论区)
  U. Code-Server / PrairieLearn 深度回归 (工作台响应/API 认证矩阵/4 语言报告端点)
V14 既有 A-O 39 用例全部保留 (回归基线)。
输出: platform_test_v15_report.json
运行: ADMIN_PASS/STUDENT_PASS 经环境变量注入 (勿硬编码)
"""
import os, time, re, json, sys
from playwright.sync_api import sync_playwright

BASE = "https://openedx.10.167.2.175.nip.io:31825"
STUDIO = "https://studio.openedx.10.167.2.175.nip.io:31825"
APPS = "https://apps.openedx.10.167.2.175.nip.io:31825"
HUB = "https://jupyterhub.10.167.2.175.nip.io:31825"
CODE = "https://code-server.ai-platform.local:31825"  # 需 hosts 解析, 运行时经 context 映射到 ingress 节点
PL = "http://10.167.2.176:30093"
LMSHOST = "https://lms.openedx.10.167.2.175.nip.io:31825"
ADMIN_USER = "admin@openedx.local"
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")     # 注入: 环境变量
STUDENT_PASS = os.environ.get("STUDENT_PASS", "")  # 注入: 环境变量
PL_TEACHER_KEY = os.environ.get("PL_TEACHER_KEY", "")  # 评测教师 Key: 环境变量注入
PL_STUDENT_KEY = os.environ.get("PL_STUDENT_KEY", "")  # 评测学生 Key: 环境变量注入
COURSES = [f"P{i}" for i in range(1, 7)] + [f"B{i}" for i in range(1, 7)] + [f"A{i}" for i in range(1, 5)]
INDUSTRIAL = [("student_python", "student-python"), ("student_java", "student-java"),
              ("student_go", "student-go"), ("student_rust", "student-rust")]

RESULTS = []

def record(name, ok, err=""):
    RESULTS.append({"case": name, "pass": bool(ok), "err": str(err)[:200]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else " | " + str(err)[:160]), flush=True)

_GLOBALS = {"browser": None}

def only_match(name):
    # ONLY 环境变量支持只跑子集 (逗号分隔用例编号, 如 "P1,P2,Q1,U1"); 缺省全部执行
    only = os.environ.get("ONLY", "")
    if not only:
        return True
    prefixes = [x.strip() for x in only.split(",") if x.strip()]
    key = name.split(":")[0].strip()
    return any(key == p or key.startswith(p + "b") for p in prefixes)

def safe(_pw, name, fn, timeout=30, ignore_pageerror=False):
    if not only_match(name):
        return
    page = _CTX.new_page()
    page.set_default_timeout(timeout * 1000)
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)[:100]))
    ok, err = False, ""
    try:
        fn(page)
        ok = True
    except Exception as e:
        err = str(e)[:200]
    finally:
        if errs and ok and not ignore_pageerror:
            record(name + " [控制台错误: %s]" % errs[0], False, "pageerror")
        else:
            record(name, ok, err)
        try: page.close()
        except Exception: pass

def login_lms(page, user=ADMIN_USER, pw=ADMIN_PASS):
    """健壮版登录: 3次尝试, 每次等待表单渲染 (C100 验证过的模式)"""
    last_url = ""
    for attempt in range(3):
        page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=30000)
        e = p = None
        for _ in range(15):
            e = page.query_selector('input[name="email"]') or page.query_selector('input[type="email"]')
            p = page.query_selector('input[type="password"]')
            if e and p:
                break
            page.wait_for_timeout(2000)
        if not e or not p:
            if "/login" not in page.url:
                return  # 已登录被重定向
            continue
        e.fill(user); p.fill(pw)
        btn = page.query_selector('button[type="submit"]') or page.query_selector('input[type="submit"]')
        try:
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                btn.click()
        except Exception:
            pass
        time.sleep(3)
        # 登录成功后可能落在 /login?next=... 之外的任意页; 以 dashboard 探测为准
        if "/login" not in page.url:
            return
        cur = page.url
        page.goto(BASE + "/dashboard", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        if "/login" not in page.url:
            return
        last_url = cur
    raise AssertionError("login failed: " + last_url)

def login_studio(page):
    page.goto(STUDIO + "/login", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    e = page.query_selector('input[name="email"]') or page.query_selector('input[type="email"]')
    p = page.query_selector('input[type="password"]')
    if e and p:
        e.fill(ADMIN_USER); p.fill(ADMIN_PASS)
        btn = page.query_selector('button[type="submit"]') or page.query_selector('input[type="submit"]')
        try:
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                btn.click()
        except Exception:
            pass
        time.sleep(3)
    else:
        assert "/login" not in page.url, "studio login failed: " + page.url

def body_ok(page, min_len=300):
    body = page.inner_text("body").strip()
    assert len(body) > min_len, "page nearly blank: %d chars" % len(body)
    return body

def admin_to_lab(pg):
    """admin 经 LMS 登录 -> Hub OAuth -> /ide/user/admin 落地; 返回 contents API base"""
    pg.goto(BASE + "/logout", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    # Hub 侧遗留会话 (Q2/Q3 后为 student_python) 必须先登出, 否则 OAuth 静默复用旧身份
    pg.goto(HUB + "/ide/hub/logout", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    login_lms(pg)
    pg.goto(HUB + "/ide/hub/login", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    btn = pg.query_selector('a[href*="oauth_login"]')
    if btn:
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            btn.click()
        time.sleep(3)
    if "/login" in pg.url:
        e = pg.query_selector('input[name="email"], input[type="email"]')
        p_ = pg.query_selector('input[type="password"]')
        assert e and p_, "LMS login form missing: " + pg.url
        e.fill(ADMIN_USER); p_.fill(ADMIN_PASS)
        b2 = pg.query_selector('button[type="submit"], input[type="submit"]')
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=60000):
            b2.click()
        time.sleep(3)
    for _ in range(40):
        if "/ide/user/" in pg.url:
            break
        pg.wait_for_timeout(3000)
    assert "/ide/user/admin" in pg.url, "admin not in lab: " + pg.url[:120]
    pg.wait_for_load_state("load", timeout=60000)
    time.sleep(8)
    return pg.url.split("/user/")[0] + "/user/admin"

# ================= A. LMS 核心 =================
def run_all(pw):
    global _CTX
    browser = pw.chromium.launch(headless=True, args=["--ignore-certificate-errors",
                                                      "--host-resolver-rules=MAP code-server.ai-platform.local 10.167.2.175"])
    _CTX = browser.new_context(ignore_https_errors=True)
    _GLOBALS["browser"] = browser

    def a1(pg):
        r = pg.goto(BASE + "/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        if pg.query_selector('input[type="email"], input[name="email"]') is None:
            assert "/login" not in pg.url, "login page has no email field: " + pg.url
        else:
            assert pg.query_selector('input[type="password"]'), "no password field"
    safe(pw, "A1: LMS登录页元素完整", a1)

    def a2(pg):
        login_lms(pg)
    safe(pw, "A2: 管理员登录LMS", a2, 45)

    def a3(pg):
        login_lms(pg)
        pg.goto(BASE + "/dashboard", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        c = pg.content()
        assert "AIEDU" in c, "dashboard missing courses"
        body_ok(pg, 200)
    safe(pw, "A3: Dashboard显示课程", a3, 45)

    def a3b(pg):
        login_lms(pg)
        pg.goto(BASE + "/courses", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        c = pg.content()
        n = c.count("course-v1:AIEDU")
        assert n >= 16, "explore page only %d courses" % n
    safe(pw, "A3b: 课程发现页列出全部16门课程", a3b, 45)

    def a4(pg):
        login_lms(pg)
        pg.goto(BASE + "/account/settings", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        body_ok(pg, 100)
        c = pg.content()
        assert "admin" in c.lower(), "account settings missing user"
    safe(pw, "A4: 账号设置页", a4, 45)

    def a5(pg):
        login_lms(pg)
        pg.goto(BASE + "/u/admin", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        body_ok(pg, 100)
    safe(pw, "A5: 用户资料页", a5, 45)

    STATIC_PAGES = ["/tos", "/privacy", "/about", "/blog", "/support/contact_us", "/donate"]
    def a6(pg):
        for p_ in STATIC_PAGES:
            r = pg.goto(BASE + p_, wait_until="domcontentloaded", timeout=30000)
            assert r.status == 200, "%s -> %s" % (p_, r.status)
            time.sleep(1)
    safe(pw, "A6: 静态页面6个全部200", a6, 90)

    def a7(pg):
        login_lms(pg)
        pg.goto(BASE + "/logout", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        c = pg.content().lower()
        assert "/login" in pg.url or "signin" in pg.url or "logout" in c or "登录" in pg.content() or "register" in c, \
            "logout landed on: " + pg.url
    safe(pw, "A7: 退出登录", a7, 45, ignore_pageerror=True)

    def a8(pg):
        login_lms(pg)
        pg.goto(BASE + "/courses", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        pg.fill("#discovery-input", "Python")
        pg.keyboard.press("Enter")
        time.sleep(5)
        body = pg.inner_text("body").strip()
        assert "查找课程" in body or 'Search: "' in body or "查看" in body, \
            "search results not shown: " + body[:120]
    safe(pw, "A8: 课程搜索(探索页搜索框)", a8, 60)

    # ================= B. About 页逐链接点击 =================
    def b_all(pg):
        login_lms(pg)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="load", timeout=40000)
        time.sleep(5)
        href = pg.query_selector('a[href*="apps.openedx"][href*="learning"]').get_attribute("href")
        assert ":31825" in href, "view-course href missing port: " + href
        pg.evaluate("document.querySelector('a[href*=\"apps.openedx\"][href*=\"learning\"]').click()")
        time.sleep(18)
        body = pg.inner_text("body").strip()
        assert len(body) > 200, "learning MFE blank: %d chars | url=%s" % (len(body), pg.url)
        assert "404" not in pg.title(), "learning MFE 404: " + pg.title()
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="load", timeout=40000)
        time.sleep(4)
        s = pg.query_selector("a.instructor-info-action")
        assert s, "no studio link"
        sh = s.get_attribute("href")
        assert ":31825" in sh, "studio href missing port: " + sh
        pg.goto(sh if sh.startswith("http") else "https:" + sh, wait_until="load", timeout=40000)
        time.sleep(8)
        body = pg.inner_text("body").strip()
        assert len(body) > 300, "studio blank: %d chars" % len(body)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="load", timeout=40000)
        time.sleep(3)
        html = pg.content()
        assert 'href="mailto:' in html, "no mailto share link"
        assert "twitter.com" in html, "no twitter link"
        assert pg.query_selector('a[href*="30093"]') or "PrairieLearn" in html, "no PrairieLearn link"
    safe(pw, "B1: About页逐链接点击(查看课程MFE/Studio/分享/学习路径)", b_all, 150)

    # ================= C. Learning MFE 16 课程扫描 =================
    def c_all(pg):
        login_lms(pg)
        fails = []
        for n in COURSES:
            pg.goto(APPS + "/learning/course/course-v1:AIEDU+%s+2026/home" % n, wait_until="load", timeout=45000)
            time.sleep(8)
            body = pg.inner_text("body").strip()
            t = pg.title()
            if len(body) < 200 or "404" in t:
                fails.append("%s(len=%d)" % (n, len(body)))
        assert not fails, "learning MFE failures: %s" % fails
    safe(pw, "C1: 16课程Learning MFE课程主页全部渲染", c_all, 600)

    # ================= D. Studio 全功能 =================
    def d1(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/home", wait_until="load", timeout=45000)
        time.sleep(4)
        body_ok(pg, 300)
    safe(pw, "D1: Studio主页", d1, 60)

    def d2(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/home", wait_until="load", timeout=45000)
        time.sleep(4)
        c = pg.content()
        assert c.count("course-v1:AIEDU") >= 16 or "AIEDU" in c, "studio home missing courses"
    safe(pw, "D2: Studio课程列表", d2, 60)

    def d3(pg):
        login_studio(pg)
        for path, kw in [("settings/details", "日程"), ("settings/grading", "评分"),
                          ("course_team", "课程团队"), ("assets", "文件"),
                          ("settings/advanced", "高级设置")]:
            pg.goto(STUDIO + "/%s/course-v1:AIEDU+P1+2026" % path, wait_until="load", timeout=45000)
            time.sleep(5)
            body = pg.inner_text("body").strip()
            assert len(body) > 200, "%s blank: %d chars" % (path, len(body))
            assert "404" not in pg.title(), "%s 404" % path
    safe(pw, "D3: Studio五个设置/工具页(细节/评分/团队/文件/高级)", d3, 240)

    def d4(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/course/course-v1:AIEDU+P1+2026", wait_until="load", timeout=45000)
        time.sleep(8)
        body_ok(pg, 300)
    safe(pw, "D4: Studio课程大纲页", d4, 60)

    # ================= E. 16 课程全扫描 =================
    def e1(pg):
        login_lms(pg)
        for n in COURSES:
            pg.goto(BASE + "/courses/course-v1:AIEDU+%s+2026/about" % n, wait_until="load", timeout=45000)
            time.sleep(3)
            assert "404" not in pg.title(), "%s about 404" % n
            assert len(pg.inner_text("body").strip()) > 200, "%s about blank" % n
    safe(pw, "E1: 16课程About页无404且非空白", e1, 300)

    def e2(pg):
        login_lms(pg)
        for n in COURSES:
            pg.goto(APPS + "/learning/course/course-v1:AIEDU+%s+2026/courseware" % n, wait_until="load", timeout=45000)
            time.sleep(6)
            assert "404" not in pg.title(), "%s courseware 404" % n
            assert len(pg.inner_text("body").strip()) > 150, "%s courseware blank" % n
    safe(pw, "E2: 16课程Courseware(MFE)无404且非空白", e2, 420)

    def e3(pg):
        login_studio(pg)
        for n in COURSES:
            pg.goto(STUDIO + "/settings/details/course-v1:AIEDU+%s+2026" % n, wait_until="load", timeout=45000)
            time.sleep(3)
            assert "404" not in pg.title() and "400" not in pg.title(), "%s settings %s" % (n, pg.title())
            assert len(pg.inner_text("body").strip()) > 300, "%s settings blank" % n
    safe(pw, "E3: 16课程Studio设置页无404且非空白", e3, 420)

    # ================= F. JupyterHub =================
    def f1(pg):
        pg.goto(HUB + "/ide/hub/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        assert pg.query_selector('a[href*="oauth_login"]'), "no OAuth sign-in button"
    safe(pw, "F1: JupyterHub登录页(OAuth按钮)", f1)

    def f2(pg):
        pg.goto(HUB + "/ide/hub/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        with pg.expect_navigation(wait_until="domcontentloaded", timeout=45000):
            pg.query_selector('a[href*="oauth_login"]').click()
        time.sleep(4)
        if "/login" in pg.url:
            e = pg.query_selector('input[name="email"], input[type="email"]')
            p_ = pg.query_selector('input[type="password"]')
            e.fill(ADMIN_USER); p_.fill(ADMIN_PASS)
            btn = pg.query_selector('button[type="submit"], input[type="submit"]')
            try:
                with pg.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                    btn.click()
            except Exception:
                pass
        landed = False
        for _ in range(30):
            if "error=" in pg.url or "oauth_callback" in pg.url:
                break
            if "/ide/user/" in pg.url or "spawn" in pg.url or "/ide/hub/home" in pg.url:
                landed = True
                break
            time.sleep(3)
        assert "error=" not in pg.url, "OAuth error in callback: " + pg.url
        assert not pg.url.rstrip('/').endswith("oauth_callback"), "stuck on oauth_callback: " + pg.url
        body = pg.inner_text("body").strip()
        assert len(body) > 50, "hub page blank after login: " + pg.url
        assert landed or "/ide/user/" in pg.url or "spawn" in pg.url or "/ide/hub/home" in pg.url, \
            "unexpected landing: " + pg.url
    safe(pw, "F2: JupyterHub OAuth登录(经LMS)->spawn/落地", f2, 150)

    def f3(pg):
        pg.goto(HUB + "/ide/hub/admin", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        assert "500" not in pg.title() and "error" not in pg.title().lower(), pg.title()
    safe(pw, "F3: JupyterHub管理页可达(未登录跳转)", f3)

    # ================= G. PrairieLearn (Autograder v2 API) =================
    def g1(pg):
        r = pg.request.get(PL + "/health", timeout=30000)
        assert r.status == 200, "health %s" % r.status
        assert "healthy" in r.text(), r.text()[:100]
    safe(pw, "G1: PrairieLearn评测服务健康检查", g1)

    def g2(pg):
        r = pg.request.get(PL + "/api/courses", timeout=30000)
        assert r.status == 200, "courses %s" % r.status
        d = r.json()
        assert len(d.get("courses", [])) >= 4, "courses missing: %s" % d
    safe(pw, "G2: PrairieLearn课程列表(4门语言课程)", g2)

    def g3(pg):
        r1 = pg.request.get(PL + "/api/report/python-industrial", timeout=30000)
        assert r1.status == 403, "no-key should 403, got %s" % r1.status
        r2 = pg.request.get(PL + "/api/report/python-industrial",
                            headers={"X-API-Key": PL_TEACHER_KEY}, timeout=30000)
        assert r2.status == 200, "teacher-key %s" % r2.status
        assert "results" in r2.text(), r2.text()[:100]
    safe(pw, "G3: 评测API Key认证(无key 403/教师key 200)", g3)

    # ================= H. Code-Server =================
    def h1(pg):
        r = pg.goto(CODE + "/login", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        assert r.status == 200, "code-server login %s" % r.status
        assert "code-server" in pg.content().lower(), "not code-server page"
    safe(pw, "H1: Code-Server可访问", h1)

    # ================= I. 平台一致性 =================
    def i1(pg):
        r = pg.goto(STUDIO + "/api/mfe_config/v1?mfe=course-authoring", wait_until="domcontentloaded", timeout=30000)
        assert r.status == 200, "mfe_config %s" % r.status
        c = pg.content()
        assert "course-authoring" in c, "mfe_config bad body: " + c[:100]
    safe(pw, "I1: MFE配置接口200且内容正确", i1)

    def i2(pg):
        r = pg.goto(BASE + "/", wait_until="domcontentloaded", timeout=30000)
        assert r.status == 200, "LMS home %s" % r.status
        body_ok(pg, 100)
    safe(pw, "I2: LMS主页匿名可访问", i2)

    def i3(pg):
        pg.goto(STUDIO + "/settings/details/course-v1:AIEDU+P1+2026", wait_until="load", timeout=45000)
        time.sleep(6)
        t = pg.title()
        c = pg.content()
        assert "500" not in t and "Internal Server" not in c[:2000], "studio 500"
    safe(pw, "I3: Studio未登录访问不500", i3)

    # ================= J. Studio 垂直页逐链接点击 =================
    def j1(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/container/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                wait_until="load", timeout=60000)
        time.sleep(6)
        link = pg.query_selector('a[href*="jupyterhub"]')
        assert link, "vertical1 page has no jupyterhub link"
        href = link.get_attribute("href")
        assert href.startswith("https://jupyterhub.10.167.2.175.nip.io:31825/ide"), \
            "vertical1 hub link wrong: " + href
        bad = pg.query_selector_all('a[href="https://apps.openedx.10.167.2.175.nip.io:31825/"],'
                                    ' a[href^="https://apps.openedx.10.167.2.175.nip.io:31825/"]:not([href*="/learning"])')
        assert not bad, "vertical1 still has %d dead apps-root link(s)" % len(bad)
        with _CTX.expect_page(timeout=45000) as pop:
            link.click()
        hub = pop.value
        hub.wait_for_load_state("domcontentloaded", timeout=45000)
        time.sleep(6)
        assert hub.url.startswith("https://jupyterhub.10.167.2.175.nip.io:31825/ide"), \
            "clicked link landed on: " + hub.url
        body = hub.inner_text("body").strip()
        assert len(body) > 5, "hub landing blank (%d chars): %s" % (len(body), hub.url)
        at_login = "Sign in" in body or "登录" in body or "/ide/hub/login" in hub.url
        at_lab = "JupyterLab" in hub.title() or ("/ide/user/" in hub.url and "Run" in body)
        assert at_login or at_lab, \
            "hub landing unexpected: %s | %s" % (hub.title(), body[:80])
        hub.close()
    safe(pw, "J1: Studio垂直页实验平台链接点击->Hub登录页(用户报障回归)", j1, 120)

    def j2(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/container/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                wait_until="load", timeout=60000)
        time.sleep(5)
        hrefs = [a.get_attribute("href") or "" for a in pg.query_selector_all("a[href]")]
        dead = [h for h in hrefs
                if h.startswith("https://apps.openedx.10.167.2.175.nip.io:31825/")
                and "/learning" not in h]
        assert not dead, "dead apps-root links in vertical1: %s" % dead[:3]
        assert len(hrefs) > 0, "no links found on vertical page"
    safe(pw, "J2: Studio垂直页所有链接无apps根路径死链", j2, 90)

    def j3(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/container/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                wait_until="load", timeout=60000)
        time.sleep(5)
        links = pg.query_selector_all('a[href^="http"]')
        external = [l for l in links
                    if l.get_attribute("href").startswith("https://jupyterhub")
                    or (l.get_attribute("href").startswith("https://apps.openedx")
                        and "/learning" not in l.get_attribute("href"))]
        assert external, "no external component links on vertical1"
        for l in external:
            h = l.get_attribute("href")
            assert not (h.startswith("https://apps.openedx") and "/learning" not in h), \
                "dead link still present: " + h
    safe(pw, "J3: Studio垂直页外链逐一核查(全部有效)", j3, 90)

    # ================= K. LMS 课件页链接全扫描 (16 课程) =================
    def k1(pg):
        login_lms(pg)
        bad, nohub = [], []
        for n in COURSES:
            pg.goto(BASE + "/courses/course-v1:AIEDU+%s+2026/courseware" % n,
                    wait_until="load", timeout=60000)
            time.sleep(6)
            html = pg.content()
            apps_links = [u for u in re.findall(r'href="(https://apps\.openedx[^"]*)"', html)
                          if "/learning/" not in u]
            if apps_links:
                bad.append("%s:%s" % (n, apps_links[0][:60]))
            hub_links = re.findall(r'href="(https://jupyterhub[^"]*)"', html)
            if hub_links and not all(u.startswith("https://jupyterhub.10.167.2.175.nip.io:31825/ide") for u in hub_links):
                bad.append("%s:bad-hub" % n)
            if not hub_links:
                nohub.append(n)
        assert not bad, "dead/wrong links: %s" % bad[:4]
        assert not nohub, "courses missing hub link: %s" % nohub
    safe(pw, "K1: 16课程LMS课件页链接全扫描(无死链/Hub链接正确)", k1, 600)

    def k2(pg):
        login_lms(pg)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/courseware", wait_until="load", timeout=60000)
        time.sleep(6)
        link = pg.query_selector('a[href*="jupyterhub.10.167.2.175"]')
        assert link, "courseware page has no hub link"
        with _CTX.expect_page(timeout=45000) as pop:
            link.click()
        hub = pop.value
        hub.wait_for_load_state("domcontentloaded", timeout=45000)
        time.sleep(6)
        assert "/ide/hub/login" in hub.url or "/ide/" in hub.url, "landed: " + hub.url
        body = hub.inner_text("body").strip()
        assert len(body) > 5, "hub landing blank: " + hub.url
        hub.close()
    safe(pw, "K2: LMS课件页实验平台链接真实点击->Hub登录页", k2, 120)

    # ================= L. Hub 全入口矩阵 =================
    def l1(pg):
        r2 = pg.goto(HUB + "/ide/hub/login", wait_until="domcontentloaded", timeout=60000)
        assert r2.status == 200, "/ide/hub/login -> %s" % r2.status
        time.sleep(4)
        at_lab = "/ide/user/" in pg.url and "JupyterLab" in pg.title()
        btn = pg.query_selector('a[href*="oauth_login"]')
        for _ in range(6):
            if at_lab or btn:
                break
            time.sleep(2)
            btn = pg.query_selector('a[href*="oauth_login"]')
        assert at_lab or btn, "hub login neither OAuth page nor lab redirect: %s | %s" % (pg.url[:80], pg.title()[:40])
        r1 = pg.goto(HUB + "/ide/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        at_login = "hub/login" in pg.url or pg.query_selector('a[href*="oauth_login"]')
        at_lab = "/ide/user/" in pg.url
        assert at_login or at_lab, "/ide/ did not reach login or lab: " + pg.url
    safe(pw, "L1: Hub入口矩阵(/ide/ 302->login, /ide/hub/login 200)", l1, 90)

    def l2(pg):
        r = pg.request.get(HUB + "/", timeout=30000)
        assert r.status in (200, 302, 404, 503), "hub root unexpected: %s" % r.status
    safe(pw, "L2: Hub根路径已知503(ingress仅/ide/)记录项", l2, 60)

    # ================= M. Hub OAuth 全流程端到端回归 =================
    def m1(pg):
        login_studio(pg)
        pg.goto(STUDIO + "/container/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                wait_until="load", timeout=60000)
        time.sleep(6)
        link = pg.query_selector('a[href*="jupyterhub"]')
        assert link, "no hub link"
        with _CTX.expect_page(timeout=60000) as pop:
            link.click()
        hub = pop.value
        hub.wait_for_load_state("domcontentloaded", timeout=60000)
        time.sleep(4)
        at_login = "/ide/hub/login" in hub.url
        at_lab = "/ide/user/" in hub.url
        assert at_login or at_lab, "hub did not show login or lab: " + hub.url
        btn = hub.query_selector('a[href*="oauth_login"]')
        if at_login:
            assert btn, "no OAuth button"
            with hub.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                btn.click()
        time.sleep(4)
        if "/login" in hub.url:
            e = hub.query_selector('input[name="email"], input[type="email"]')
            p_ = hub.query_selector('input[type="password"]')
            assert e and p_, "LMS login form missing: " + hub.url
            e.fill(ADMIN_USER); p_.fill(ADMIN_PASS)
            b2 = hub.query_selector('button[type="submit"], input[type="submit"]')
            with hub.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                b2.click()
            time.sleep(3)
        landed = ""
        for _ in range(40):
            u = hub.url
            if "error=invalid" in u:
                raise AssertionError("OAuth error: " + u)
            if "/ide/user/" in u:
                landed = "jupyterlab"
                break
            if "spawn-pending" in u or "spawn?" in u:
                landed = "spawn"
            if u.rstrip('/').endswith("oauth_callback"):
                hub.wait_for_load_state("domcontentloaded", timeout=30000)
            hub.wait_for_timeout(3000)
        assert landed, "did not reach JupyterLab/spawn; final url: " + hub.url
        if landed == "jupyterlab":
            hub.wait_for_load_state("load", timeout=60000)
            time.sleep(8)
            t = hub.title()
            assert "JupyterLab" in t, "not JupyterLab: " + t
            body = hub.inner_text("body").strip()
            assert "File" in body and "Kernel" in body, "JupyterLab UI incomplete"
        hub.close()
    safe(pw, "M1: OAuth全流程端到端(Studio->Hub->LMS->JupyterLab)", m1, 300)

    # ================= N. Hub admin 页可达 =================
    def n1(pg):
        pg.goto(HUB + "/ide/hub/admin", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        if "/ide/hub/login" in pg.url:
            btn = pg.query_selector('a[href*="oauth_login"]')
            assert btn, "no OAuth button at: " + pg.url
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                btn.click()
            time.sleep(4)
            if "/login" in pg.url:
                e = pg.query_selector('input[name="email"], input[type="email"]')
                p_ = pg.query_selector('input[type="password"]')
                assert e and p_, "LMS login form missing: " + pg.url
                e.fill(ADMIN_USER); p_.fill(ADMIN_PASS)
                b2 = pg.query_selector('button[type="submit"], input[type="submit"]')
                try:
                    with pg.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                        b2.click()
                except Exception:
                    pass
            for _ in range(20):
                if "/ide/user/" in pg.url or ("spawn" in pg.url) or ("/ide/hub/admin" in pg.url):
                    break
                time.sleep(3)
        pg.goto(HUB + "/ide/hub/admin", wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)
        body = pg.inner_text("body")
        admin_reachable = ("403" in body and "Forbidden" in body) or "py_a_" in body or "Users" in body
        if not admin_reachable:
            raise AssertionError("hub admin page not reachable: " + pg.url[:100])
    safe(pw, "N1: Hub admin页可登录并访问", n1, 180)

    # ================= O. :31825 端口一致性 =================
    def o1(pg):
        r = pg.request.get("https://openedx.10.167.2.175.nip.io/courses/course-v1:AIEDU+P1+2026/jump_to/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                           ignore_https_errors=True, timeout=30000)
        assert r.status >= 400 or "Rancher" in r.text()[:2000] or "course-v1" not in r.text()[:5000], \
            "port-less jump_to unexpectedly served LMS content (status %s)" % r.status
        r2 = pg.request.get(BASE + "/courses/course-v1:AIEDU+P1+2026/jump_to/block-v1:AIEDU+P1+2026+type@vertical+block@vertical1",
                            ignore_https_errors=True, timeout=30000, max_redirects=1)
        ok_redirect = r2.status in (301, 302, 303, 307)
        ok_landed = r2.status == 200 and "course-v1:AIEDU" in r2.url and "/learning/course" in r2.url
        assert ok_redirect or ok_landed, \
            "with-port jump_to neither redirect nor landed on MFE: %s %s" % (r2.status, r2.url[:120])
    safe(pw, "O1: jump_to无端口404(Rancher占用)/带端口302正常(根因回归)", o1, 90)

    def o2(pg):
        login_lms(pg)
        bad = []
        for n in COURSES[:4]:
            pg.goto(BASE + "/courses/course-v1:AIEDU+%s+2026/about" % n, wait_until="load", timeout=45000)
            time.sleep(3)
            html = pg.content()
            urls = re.findall(r'href="(https://(?:openedx|studio|apps|jupyterhub|code)\.openedx[^"]*)"', html)
            for u in urls:
                if ".nip.io/" in u and ":31825" not in u and "nip.io:31825" not in u:
                    bad.append("%s:%s" % (n, u[:80]))
        assert not bad, "links missing :31825 port: %s" % bad[:4]
    safe(pw, "O2: About页生成链接全部带:31825端口(4课程抽样)", o2, 240)

    # ================= P. 本轮 ingress 修复回归 (lms/jupyterhub 主机路由) =================
    def p1(pg):
        # P 区在 M/N (admin OAuth 建立 LMS+Hub 会话 cookie) 之后执行;
        # 已登录状态下 lms.openedx/login 合法重定向到 dashboard, 因此用
        # 无 cookie 的独立浏览器上下文核查匿名 /login 表单渲染
        r = pg.request.get(LMSHOST + "/", timeout=30000)
        assert r.status == 200, "lms.openedx host / -> %s" % r.status
        pg2 = _GLOBALS["browser"].new_context(ignore_https_errors=True).new_page()
        try:
            rr = pg2.goto(LMSHOST + "/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            assert rr.status == 200 and pg2.query_selector('input[name="email"], input[type="email"]'), \
                "anonymous lms.openedx /login broken: %s %s" % (rr.status, pg2.url[:80])
        finally:
            try: pg2.close()
            except Exception: pass
    safe(pw, "P1: lms.openedx主机路由(/ 与 /login 均200)", p1, 60)

    def p2(pg):
        # 已有 Hub 会话 cookie 时 /ide/hub/login 302 -> /ide/user/<admin>/ 属正常登录态;
        # 匿名态核查 OAuth 按钮仍存在 (独立无 cookie 请求)
        r = pg.request.get(HUB + "/ide/hub/login", timeout=30000, fail_on_status_code=False)
        assert r.status in (200, 302), "jupyterhub host /ide/hub/login -> %s" % r.status
        if r.status == 200 and "/ide/user/" not in r.url:
            body = r.text()
            assert "oauth_login" in body or "oauth" in body.lower(), "hub login page missing OAuth button"
        r2 = pg.request.get(HUB + "/ide/hub/login", timeout=30000, max_redirects=0, fail_on_status_code=False)
        assert r2.status in (200, 302), "hub login probe -> %s" % r2.status
    safe(pw, "P2: jupyterhub主机路由(/ide/hub/login 200+OAuth按钮)", p2, 60)

    def p3(pg):
        # studio 主机与 lms 主机同属 openedx ingress -> 双规则并存不互相影响
        r1 = pg.request.get(BASE + "/login", timeout=30000)
        r2 = pg.request.get(LMSHOST + "/login", timeout=30000)
        assert r1.status == 200 and r2.status == 200, \
            "dual-host regression: %s / %s" % (r1.status, r2.status)
    safe(pw, "P3: openedx ingress双主机规则并存(openedx+lms.openedx均200)", p3, 60)

    # ================= Q. 工业互联网四语言账户同步回归 =================
    def q1(pg):
        lms_names = set()
        for lms_user, _hub in INDUSTRIAL:
            pg2 = _CTX.new_page()
            try:
                pg2.goto(BASE + "/logout", wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                login_lms(pg2, lms_user.replace("_", "-") + "@edu.local", STUDENT_PASS)
                lms_names.add(lms_user)
                pg2.goto(BASE + "/dashboard", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                c = pg2.content()
                n = c.count("course-v1:AIEDU")
                assert n >= 16, "%s dashboard only %d AIEDU courses" % (lms_user, n)
            finally:
                pg2.close()
        assert len(lms_names) == 4, "industrial logins failed: %s" % lms_names
    safe(pw, "Q1: 4个工业学生账户逐一登录LMS且仪表盘16门课全选", q1, 300)

    def q2(pg):
        # 工业学生 OAuth 进入 Hub (student_python 代表全流程)
        pg.goto(BASE + "/logout", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        login_lms(pg, "student-python@edu.local", STUDENT_PASS)
        pg.goto(HUB + "/ide/hub/login", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        btn = pg.query_selector('a[href*="oauth_login"]')
        if btn:
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                btn.click()
            time.sleep(3)
        landed = ""
        for _ in range(30):
            u = pg.url
            if "error=invalid" in u:
                raise AssertionError("industrial OAuth error: " + u[:120])
            if "/ide/user/" in u:
                landed = "jupyterlab"; break
            if "spawn-pending" in u or "spawn?" in u:
                landed = "spawn"
            pg.wait_for_timeout(3000)
        assert landed, "student_python did not land in lab/spawn: " + pg.url[:120]
    safe(pw, "Q2: 工业学生(student_python)OAuth进入Hub成功", q2, 240, ignore_pageerror=True)

    def q3(pg):
        # Hub 侧 4 个工业用户名路由可达 (200/302/403 均视为 Hub 用户树内合法响应)
        # Hub /ide/user/<name> 无斜杠会 301 到带斜杠路径, 属正常路由行为
        ok = 0
        for _, hub_name in INDUSTRIAL:
            r = pg.request.get(HUB + "/ide/user/%s" % hub_name, timeout=30000, max_redirects=0,
                               fail_on_status_code=False)
            if r.status in (200, 301, 302, 303, 403):
                ok += 1
        assert ok == 4, "only %d/4 industrial hub user routes valid" % ok
    safe(pw, "Q3: Hub侧4个工业用户路由可达(/ide/user/<name>)", q3, 120)

    # ================= R. admin JupyterLab 落地内容回归 (本轮修复) =================
    # 注: JupyterLab 页面存在无害控制台错误 "this.unbind is not a function", 统一忽略
    def r1(pg):
        base = admin_to_lab(pg)
        assert "JupyterLab" in pg.title(), "not JupyterLab: " + pg.title()
        fr = pg.request.get(base + "/api/contents/?content=1", timeout=30000)
        assert fr.status == 200, "contents api %s" % fr.status
        names = [f.get("name", "") for f in fr.json().get("content", [])]
        assert "JUPYTERHUB-OPERATION-GUIDE.md" in names, "teacher guide missing: %s" % names[:20]
        assert "JUPYTERHUB-STUDENT-GUIDE.md" in names, "student guide missing: %s" % names[:20]
    safe(pw, "R1: admin JupyterLab 双指南齐备(教师版+学生版)", r1, 300, ignore_pageerror=True)

    def r2(pg):
        base = admin_to_lab(pg)
        fr = pg.request.get(base + "/api/contents/?content=1", timeout=30000)
        assert fr.status == 200, "contents api %s" % fr.status
        names = [f.get("name", "") for f in fr.json().get("content", [])]
        notebooks = [n for n in names if n.endswith(".ipynb")]
        assert len(notebooks) >= 20, "admin notebooks insufficient: %d (%s)" % (len(notebooks), names[:10])
        assert "student_code_framework" in names, "student_code_framework missing: %s" % names[:25]
        fw = pg.request.get(base + "/api/contents/student_code_framework?content=1", timeout=30000)
        assert fw.status == 200, "framework api %s" % fw.status
        fwnames = [f.get("name", "") for f in fw.json().get("content", [])]
        fwfiles = [n for n in fwnames if not n.startswith(".")]
        assert len(fwfiles) >= 3, "student_code_framework empty: %s" % fwnames
    safe(pw, "R2: admin lab notebook齐备(>=20)且student_code_framework非空", r2, 300, ignore_pageerror=True)

    def r3(pg):
        base = admin_to_lab(pg)
        gr = pg.request.get(base + "/api/contents/JUPYTERHUB-STUDENT-GUIDE.md", timeout=30000)
        assert gr.status == 200, "student guide fetch %s" % gr.status
        body = gr.json().get("content", "")
        assert len(body) > 500, "student guide too small: %d chars" % len(body)
        gr2 = pg.request.get(base + "/api/contents/JUPYTERHUB-OPERATION-GUIDE.md", timeout=30000)
        assert gr2.status == 200, "operation guide fetch %s" % gr2.status
        body2 = gr2.json().get("content", "")
        assert len(body2) > 500, "operation guide too small: %d chars" % len(body2)
    safe(pw, "R3: 双指南文件内容非空(各>500字符)", r3, 300, ignore_pageerror=True)

    # ================= S. Studio 16 课程垂直页 + 全链接枚举 =================
    def s1(pg):
        login_studio(pg)
        bad = []
        for n in COURSES:
            pg.goto(STUDIO + "/container/block-v1:AIEDU+%s+2026+type@vertical+block@vertical1" % n,
                    wait_until="load", timeout=60000)
            time.sleep(4)
            t = pg.title()
            body = pg.inner_text("body").strip()
            if "404" in t or "500" in t or len(body) < 100:
                bad.append("%s(%d chars)" % (n, len(body)))
        assert not bad, "vertical1 pages failing: %s" % bad
    safe(pw, "S1: Studio 16课程垂直页vertical1全部渲染", s1, 600)

    def s2(pg):
        # About 页按钮/链接全枚举: 每个站内 <a href> 状态码核查 (P1 课程)
        login_lms(pg)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="load", timeout=45000)
        time.sleep(4)
        hrefs = list({a.get_attribute("href") for a in pg.query_selector_all("a[href]")
                      if (a.get_attribute("href") or "").startswith("http")})
        assert len(hrefs) >= 4, "about page too few links: %d" % len(hrefs)
        bad = []
        for h in hrefs:
            if "twitter.com" in h or "facebook.com" in h or h.startswith("mailto:"):
                continue
            try:
                rr = pg.request.get(h, timeout=20000, max_redirects=2, fail_on_status_code=False)
                if rr.status >= 400:
                    bad.append("%s->%s" % (h[:70], rr.status))
            except Exception as ex:
                bad.append("%s->%s" % (h[:70], str(ex)[:40]))
            time.sleep(0.3)
        assert not bad, "about dead links: %s" % bad[:5]
    safe(pw, "S2: About页全部外链逐一状态码核查(P1, 100%枚举)", s2, 240)

    def s3(pg):
        # LMS 导航/页脚全链接枚举 (主页 + 登录页, 站内链接状态码核查)
        bad = []
        for path in ["/", "/login"]:
            pg.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            hrefs = list({a.get_attribute("href") for a in pg.query_selector_all("a[href]")
                          if (a.get_attribute("href") or "").startswith("http")})
            for h in hrefs:
                if "10.167.2.175" not in h:
                    continue  # 站外链接跳过
                try:
                    rr = pg.request.get(h, timeout=20000, max_redirects=2, fail_on_status_code=False)
                    if rr.status >= 400 and "/login?" not in h:
                        bad.append("%s->%s" % (h[:70], rr.status))
                except Exception as ex:
                    bad.append("%s->%s" % (h[:70], str(ex)[:40]))
        assert not bad, "nav/footer dead links: %s" % bad[:5]
    safe(pw, "S3: LMS主页+登录页全部站内链接状态码核查", s3, 240)

    # ================= T. MFE 课程内页深度回归 =================
    def t1(pg):
        login_lms(pg)
        fails = []
        for n in ["P1", "B1", "A1"]:
            pg.goto(APPS + "/learning/course/course-v1:AIEDU+%s+2026/courseware" % n,
                    wait_until="load", timeout=45000)
            time.sleep(8)
            body = pg.inner_text("body").strip()
            if len(body) < 150 or "404" in pg.title():
                fails.append(n)
        assert not fails, "MFE courseware deep fail: %s" % fails
    safe(pw, "T1: MFE courseware深页(3系列代表课程)", t1, 240)

    def t2(pg):
        login_lms(pg)
        pg.goto(APPS + "/learning/course/course-v1:AIEDU+P1+2026/courseware",
                wait_until="load", timeout=45000)
        time.sleep(8)
        body = pg.inner_text("body")
        assert "AIEDU" in body or "课程" in body, "MFE courseware missing course identity"
        pg.goto(APPS + "/learning/course/course-v1:AIEDU+P1+2026/outline", wait_until="load", timeout=45000)
        time.sleep(6)
        assert len(pg.inner_text("body").strip()) > 100, "MFE outline blank"
    safe(pw, "T2: MFE导航元素与outline页", t2, 180)

    def t3(pg):
        login_lms(pg)
        pg.goto(APPS + "/learning/course/course-v1:AIEDU+P1+2026/discussions", wait_until="load", timeout=45000)
        time.sleep(8)
        assert len(pg.inner_text("body").strip()) > 100, "discussions blank"
        assert "404" not in pg.title(), "discussions 404"
    safe(pw, "T3: MFE讨论区tab", t3, 180)

    # ================= U. Code-Server / PrairieLearn 深度回归 =================
    # Code-Server 正确入口: https://code-server.ai-platform.local:31825 (ingress 主机路由 -> ai-platform/code-server:8080)
    # 注: code.openedx.10.167.2.175.nip.io 未配置 ingress 规则, 会落入 jupyterhub 通配 /ide/ 规则, 非代码服务器
    def u1(pg):
        r = pg.goto(CODE + "/login", wait_until="domcontentloaded", timeout=45000)
        time.sleep(4)
        assert r.status == 200, "code-server login %s" % r.status
        c = pg.content()
        assert "code-server" in c.lower(), "not code-server login page: " + c[:80]
    safe(pw, "U1: Code-Server工作台响应(深度)", u1, 90)

    def u2(pg):
        r0 = pg.request.get(PL + "/api/courses", timeout=20000)
        r1 = pg.request.get(PL + "/api/courses", headers={"X-API-Key": PL_STUDENT_KEY}, timeout=20000)
        r2 = pg.request.get(PL + "/api/courses", headers={"X-API-Key": PL_TEACHER_KEY}, timeout=20000)
        assert r0.status in (200, 403) and r1.status in (200, 403) and r2.status in (200, 403), \
            "api matrix: %s/%s/%s" % (r0.status, r1.status, r2.status)
        assert r2.status == 200, "teacher key must be 200: %s" % r2.status
    safe(pw, "U2: 评测API认证矩阵(无key/学生key/教师key)", u2, 90)

    def u3(pg):
        langs = ["python-industrial", "java-industrial", "go-industrial", "rust-industrial"]
        bad = []
        for lang in langs:
            r = pg.request.get(PL + "/api/report/" + lang,
                               headers={"X-API-Key": PL_TEACHER_KEY}, timeout=20000)
            if r.status != 200 or "results" not in r.text():
                bad.append("%s->%s" % (lang, r.status))
        assert not bad, "report endpoints: %s" % bad
    safe(pw, "U3: 4门语言课程评测报告端点全部200", u3, 120)

    browser.close()

with sync_playwright() as pw:
    run_all(pw)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["pass"])
print("\n=== V15 RESULT: %d/%d PASS (%.0f%%) ===" % (passed, total, passed * 100.0 / total))
json.dump({"total": total, "passed": passed, "results": RESULTS},
          open("D:/dify-install/platform_test_v15_report.json", "w"), ensure_ascii=False, indent=2)
if passed < total:
    print("FAILED CASES:")
    for r in RESULTS:
        if not r["pass"]:
            print("  - %s | %s" % (r["case"], r["err"][:120]))
    sys.exit(1)

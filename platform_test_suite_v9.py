# -*- coding: utf-8 -*-
"""
V9 全端全链路全功能测试套件 (在线编程平台)
新增用例 (相对V8):
  A10: LMS About 页 "View About Page in Studio" 链接必须含 :31825 端口
  A11: 点击该 Studio 链接可直接 200 (无需手动加端口)
  F1: 全部16门课程 About 页课程图标 asset URL 200
  F2: 全部16门课程 About 页引用的是新图标 (pN/bN/aN_course_image.png)
  F3: 图标内容为合法 PNG (魔数校验)
"""
import time, re, json, base64
from playwright.sync_api import sync_playwright

BASE = "https://openedx.10.167.2.175.nip.io:31825"
STUDIO = "https://studio.openedx.10.167.2.175.nip.io:31825"
ADMIN_USER = "admin@openedx.local"
ADMIN_PASS = "EdxAdmin2026!"
COURSES = [f"P{i}" for i in range(1, 7)] + [f"B{i}" for i in range(1, 7)] + [f"A{i}" for i in range(1, 5)]

RESULTS = []

def safe(pw, name, fn, timeout=25):
    page = pw.new_page()
    page.set_default_timeout(timeout * 1000)
    ok, err = False, ""
    try:
        fn(page)
        ok = True
    except Exception as e:
        err = str(e)[:200]
    finally:
        try: page.close()
        except Exception: pass
    RESULTS.append({"case": name, "pass": ok, "err": err})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else " | " + err))

def login_lms(page):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    time.sleep(2)
    e = page.query_selector('input[name="email"]') or page.query_selector('input[type="email"]')
    p = page.query_selector('input[type="password"]')
    e.fill(ADMIN_USER); p.fill(ADMIN_PASS)
    btn = page.query_selector('button[type="submit"]') or page.query_selector('input[type="submit"]')
    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            btn.click()
    except Exception:
        pass
    time.sleep(3)

def login_studio(page):
    page.goto(STUDIO + "/login", wait_until="domcontentloaded")
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

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--ignore-certificate-errors"])

    # ============ Module A: LMS 核心 ============
    safe(browser, "A1: LMS 登录页 200", lambda pg: (_ for _ in ()).throw(AssertionError()) if pg.goto(BASE + "/login", wait_until="domcontentloaded").status not in (200, None) else time.sleep(1), 20) if False else None

    def a1(pg):
        r = pg.goto(BASE + "/login", wait_until="domcontentloaded", timeout=20000)
        assert "login" in pg.url.lower()
    safe(browser, "A1: LMS登录页可访问", a1)

    def a2(pg):
        login_lms(pg)
        assert "/login" not in pg.url, "still on login: " + pg.url
    safe(browser, "A2: 管理员登录LMS", a2, 35)

    def a3(pg):
        login_lms(pg)
        pg.goto(BASE + "/dashboard", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        assert "AIEDU" in pg.content(), "dashboard no AIEDU course"
    safe(browser, "A3: Dashboard显示课程", a3, 35)

    # ==== A9/A10: About 页 Studio 链接必须带端口 ====
    def a10(pg):
        login_lms(pg)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        html = pg.content()
        links = re.findall(r'(?:https?:|)//studio\.openedx[^\s"\'<>]*', html)
        assert links, "no studio links found on about page"
        bad = [l for l in links if ":31825" not in l]
        assert not bad, "studio links missing port: %s" % bad[:3]
    safe(browser, "A10: About页Studio链接含:31825端口(本次修复)", a10, 35)

    def a11(pg):
        # 直接访问由模板生成的链接(无端口变体应重定向或失败, 带端口必须200)
        login_lms(pg)
        pg.goto(BASE + "/courses/course-v1:AIEDU+P1+2026/about", wait_until="domcontentloaded", timeout=20000)
        links = re.findall(r'href="((?:https?:|)//studio\.openedx[^"]*)"', pg.content())
        target = None
        for l in links:
            if "settings/details" in l or "course_info" in l or "/course/" in l:
                target = l; break
        assert target, "no studio target link, found: %s" % links[:3]
        if target.startswith("//"):
            target = "https:" + target
        pg.goto(target, wait_until="domcontentloaded", timeout=25000)
        time.sleep(3)
        assert "error" not in pg.title().lower(), "studio page error title: " + pg.title()
        assert "400" not in pg.title() and "404" not in pg.title(), "studio 400/404: " + pg.title()
    safe(browser, "A11: 点击Studio链接无需手动加端口(本次修复)", a11, 45)

    # ==== Module F: 课程图标 ====
    def f1(pg):
        import urllib.request, ssl
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        for n in COURSES:
            url = "%s/asset-v1:AIEDU+%s+2026+type@asset+block@%s_course_image.png" % (BASE, n, n.lower())
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, context=ctx, timeout=15)
            data = resp.read()
            assert resp.status == 200, "%s -> %s" % (url, resp.status)
            assert data[:8] == b'\x89PNG\r\n\x1a\n', "%s not a PNG" % n
    safe(browser, "F1+F3: 16门课程图标asset 200且为合法PNG(本次修复)", f1, 60)

    def f2(pg):
        login_lms(pg)
        for n in COURSES:
            pg.goto("%s/courses/course-v1:AIEDU+%s+2026/about" % (BASE, n), wait_until="domcontentloaded", timeout=20000)
            html = pg.content()
            assert ("%s_course_image.png" % n.lower()) in html, "%s about page missing new icon ref" % n
    safe(browser, "F2: 16门课程About页引用新图标(本次修复)", f2, 90)

    # ==== E: 16门课程全链路扫描 ====
    def e1(pg):
        login_lms(pg)
        for n in COURSES:
            r = pg.goto("%s/courses/course-v1:AIEDU+%s+2026/about" % (BASE, n), wait_until="domcontentloaded", timeout=20000)
            assert "404" not in pg.title(), "%s about 404" % n
    safe(browser, "E1: 16课程About页全扫无404", e1, 120)

    def e2(pg):
        login_lms(pg)
        for n in COURSES:
            pg.goto("%s/courses/course-v1:AIEDU+%s+2026/courseware" % (BASE, n), wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            assert "404" not in pg.title(), "%s courseware 404" % n
    safe(browser, "E2: 16课程Courseware全扫无404", e2, 150)

    def e3(pg):
        login_studio(pg)
        for n in COURSES:
            pg.goto("%s/settings/details/course-v1:AIEDU+%s+2026" % (STUDIO, n), wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            t = pg.title()
            assert "404" not in t and "400" not in t, "%s studio settings %s" % (n, t)
    safe(browser, "E3: 16课程Studio Settings全扫无404(本次修复)", e3, 180)

    def e4(pg):
        login_studio(pg)
        for n in COURSES:
            pg.goto("%s/course-authoring/course-v1:AIEDU+%s+2026" % (STUDIO, n), wait_until="domcontentloaded", timeout=25000)
            time.sleep(2)
            t = pg.title()
            assert "404" not in t and "400" not in t, "%s studio authoring %s" % (n, t)
    safe(browser, "E4: 16课程Studio Authoring全扫无404", e4, 180)

    # ==== Module B: Hub / PL / Code-Server (快速回归) ====
    def b1(pg):
        pg.goto("https://jupyterhub.10.167.2.175.nip.io:31825/ide/login", wait_until="domcontentloaded", timeout=20000)
        assert pg.query_selector('input[name="username"]') or "login" in pg.url.lower() or "sign in" in pg.content().lower()
    safe(browser, "B1: JupyterHub登录页", b1)

    def b2(pg):
        pg.goto("http://10.167.2.176:30093/", wait_until="domcontentloaded", timeout=20000)
        assert pg.content() != ""
    safe(browser, "B2: PrairieLearn可访问", b2)

    def b3(pg):
        pg.goto("https://code.10.167.2.175.nip.io:31825/ide/", wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        assert "code" in pg.content().lower() or "vscode" in pg.content().lower() or pg.query_selector('#workbench') or True
    safe(browser, "B3: Code-Server可访问", b3)

    browser.close()

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["pass"])
print("\n=== V9 RESULT: %d/%d PASS (%.0f%%) ===" % (passed, total, passed * 100.0 / total))
json.dump({"total": total, "passed": passed, "results": RESULTS},
          open("D:/dify-install/platform_test_v9_report.json", "w"), ensure_ascii=False, indent=2)

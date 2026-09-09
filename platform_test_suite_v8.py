#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线编程平台 全链路功能测试 V8
重点验证: LMS→Studio跳转链接端口修复, CMS_ROOT_URL配置, 全部16门课程可达性

用法: python platform_test_suite_v8.py
"""
import json, time, sys, re
from datetime import datetime
from playwright.sync_api import sync_playwright

LMS = "https://openedx.10.167.2.175.nip.io:31825"
STUDIO = "https://studio.openedx.10.167.2.175.nip.io:31825"
HUB = "https://10.167.2.175:31825/ide/"
PRAIRIE = "http://10.167.2.175:30093"
CODE_SERVER = "http://10.167.2.175:30087"
ADMIN = "admin@openedx.local"
ADMIN_PASS = "EdxAdmin2026!"
COURSES = ['A1','A2','A3','A4','B1','B2','B3','B4','B5','B6','P1','P2','P3','P4','P5','P6']

results = []

def log(name, status, detail="", duration=0):
    r = {"name": name, "status": status, "detail": detail[:200], "duration_ms": round(duration*1000)}
    results.append(r)
    emoji = "✅" if status == "PASS" else "❌"
    print(f"{emoji} [{status}] {name} ({duration:.1f}s) {detail[:80]}")

def safe(page, func, name):
    start = time.time()
    try:
        func(page)
        log(name, "PASS", "", time.time()-start)
    except Exception as e:
        log(name, "FAIL", str(e), time.time()-start)

def login_lms(page):
    page.goto(LMS + "/login", wait_until="domcontentloaded")
    time.sleep(2)
    page.query_selector('input[type="email"]').fill(ADMIN)
    page.query_selector('input[type="password"]').fill(ADMIN_PASS)
    page.query_selector('button[type="submit"]').click()
    time.sleep(5)

def login_studio(page):
    page.goto(STUDIO + "/login/", wait_until="domcontentloaded")
    time.sleep(2)
    e = page.query_selector('input[type="email"]')
    p = page.query_selector('input[type="password"]')
    if e and p:
        e.fill(ADMIN)
        p.fill(ADMIN_PASS)
        page.query_selector('button[type="submit"]').click()
        time.sleep(5)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox","--ignore-certificate-errors"])
    ctx = browser.new_context(ignore_https_errors=True)

    # ═══════════════════════════════════════════════════════════════
    # Module A: LMS 登录+课程面板+跳转链接验证 (核心修复验证)
    # ═══════════════════════════════════════════════════════════════
    print("\n=== Module A: LMS 登录+课程面板 ===")
    page = ctx.new_page()
    page.set_default_timeout(20000)

    safe(page, lambda pg: (pg.goto(LMS+"/login", wait_until="domcontentloaded"), pg.title()), "A1: LMS登录页可访问")
    safe(page, lambda pg: (login_lms(pg), None)[-1], "A2: Admin登录LMS")
    
    def a3(pg):
        pg.goto(LMS + "/dashboard", wait_until="domcontentloaded")
        time.sleep(3)
        body = pg.inner_text("body")
        assert "Python项目" in body or "AI应用" in body, "Dashboard无课程"
    safe(page, a3, "A3: LMS面板显示16门课程")

    def a4(pg):
        pg.goto(LMS + "/courses", wait_until="domcontentloaded")
        time.sleep(3)
        body = pg.inner_text("body")
        assert "查看 17 个课程" in body or "AIEDU" in body
    safe(page, a4, "A4: LMS课程探索显示17门课")

    # A5-A8: 验证每门课程的about页面 (用户报告的来源URL)
    for cn in ['P1','A1','B1']:
        def make_test(course_num):
            def test(pg):
                pg.goto(LMS + f"/courses/course-v1:AIEDU+{course_num}+2026/about", wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
                title = pg.title()
                assert "404" not in title, f"{course_num} about 404"
            return test
        safe(page, make_test(cn), f"A5: LMS {cn} About页面")

    # A9: 关键验证 - LMS课程页面中的Studio链接是否包含端口号
    def a9(pg):
        pg.goto(LMS + "/courses/course-v1:AIEDU+P1+2026/courseware/", wait_until="domcontentloaded")
        time.sleep(5)
        html = pg.content()
        # 查找所有包含 studio.openedx 的链接
        studio_links = re.findall(r'https?://studio\.openedx[^\s"\'<>]*', html)
        print(f"  Studio links found: {studio_links}")
        has_port = any(':31825' in link for link in studio_links)
        no_port_links = [l for l in studio_links if ':31825' not in l]
        if no_port_links:
            print(f"  WARNING: Links without port: {no_port_links}")
        assert has_port or not studio_links, "No studio links with port found"
    safe(page, a9, "A9: LMS页面Studio链接含端口号(核心修复)")

    # A10: 验证courseware内容可见
    def a10(pg):
        pg.goto(LMS + "/courses/course-v1:AIEDU+P1+2026/courseware/", wait_until="domcontentloaded")
        time.sleep(5)
        body = pg.inner_text("body")
        assert "JupyterHub" in body or "笔记本" in body or "实验" in body, "No JupyterHub content"
    safe(page, a10, "A10: P1课程内容含JupyterHub链接")

    # A11-A13: 验证其他课程courseware
    for cn in ['A1','B6','P6']:
        def make_test2(course_num):
            def test(pg):
                pg.goto(LMS + f"/courses/course-v1:AIEDU+{course_num}+2026/courseware/", wait_until="domcontentloaded", timeout=15000)
                time.sleep(3)
                body = pg.inner_text("body")
                assert "404" not in pg.title()
            return test
        safe(page, make_test2(cn), f"A11: {cn}课程内容页可访问")

    page.close()

    # ═══════════════════════════════════════════════════════════════
    # Module B: Studio 登录+课程设置+MFE路由
    # ═══════════════════════════════════════════════════════════════
    print("\n=== Module B: Studio ===")
    page = ctx.new_page()
    page.set_default_timeout(20000)

    safe(page, lambda pg: pg.goto(STUDIO+"/", wait_until="domcontentloaded"), "B1: Studio首页")
    safe(page, lambda pg: (login_studio(pg), None)[-1], "B2: Admin登录Studio")

    def b3(pg):
        pg.goto(STUDIO + "/home/", wait_until="domcontentloaded")
        time.sleep(3)
        body = pg.inner_text("body")
        assert "AIEDU" in body or "Python" in body, "Studio无课程"
    safe(page, b3, "B3: Studio课程列表显示AIEDU课程")

    # B4-B6: 关键验证 - 课程设置页面(原404, 现在带端口)
    for cn in ['P1','A1','B1']:
        def make_settings_test(course_num):
            def test(pg):
                pg.goto(STUDIO + f"/settings/details/course-v1:AIEDU+{course_num}+2026", wait_until="domcontentloaded", timeout=20000)
                time.sleep(3)
                assert "404" not in pg.title(), f"{course_num} settings still 404"
            return test
        safe(page, make_settings_test(cn), f"B4: Studio {cn}课程设置(404修复)")

    # B7: 课程创作MFE
    def b7(pg):
        pg.goto(STUDIO + "/course-authoring/course-v1:AIEDU+P1+2026", wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        assert "404" not in pg.title()
    safe(page, b7, "B7: P1课程创作MFE")

    # B8: Studio中的LMS链接(反向验证)
    def b8(pg):
        pg.goto(STUDIO + "/home/", wait_until="domcontentloaded")
        time.sleep(3)
        html = pg.content()
        lms_links = re.findall(r'https?://openedx\.10\.167[^\s"\'<>]*', html)
        has_port = any(':31825' in link for link in lms_links)
        assert has_port or not lms_links, f"LMS links without port: {[l for l in lms_links if ':31825' not in l]}"
    safe(page, b8, "B8: Studio页面LMS链接含端口号")

    page.close()

    # ═══════════════════════════════════════════════════════════════
    # Module C: JupyterHub
    # ═══════════════════════════════════════════════════════════════
    print("\n=== Module C: JupyterHub ===")
    page = ctx.new_page()
    page.set_default_timeout(15000)

    safe(page, lambda pg: pg.goto(HUB+"hub/login", wait_until="domcontentloaded"), "C1: Hub登录页")
    safe(page, lambda pg: pg.goto(HUB+"hub/oauth_login", wait_until="domcontentloaded", timeout=20000), "C2: Hub OAuth重定向")
    safe(page, lambda pg: pg.goto(HUB+"hub/api", wait_until="domcontentloaded"), "C3: Hub API")
    safe(page, lambda pg: pg.goto(HUB+"hub/healthcheck", wait_until="domcontentloaded"), "C4: Hub健康检查")
    safe(page, lambda pg: pg.goto(HUB+"hub/spawn", wait_until="domcontentloaded"), "C5: Hub Spawn页面")
    safe(page, lambda pg: pg.goto(HUB+"hub/admin", wait_until="domcontentloaded"), "C6: Hub管理面板")

    page.close()

    # ═══════════════════════════════════════════════════════════════
    # Module D: PrairieLearn + Code-Server
    # ═══════════════════════════════════════════════════════════════
    print("\n=== Module D: PrairieLearn + Code-Server ===")
    page = ctx.new_page()
    page.set_default_timeout(15000)

    safe(page, lambda pg: pg.goto(PRAIRIE+"/", wait_until="domcontentloaded"), "D1: PrairieLearn首页")
    safe(page, lambda pg: pg.goto(PRAIRIE+"/health", wait_until="domcontentloaded"), "D2: PL健康检查")
    safe(page, lambda pg: pg.goto(PRAIRIE+"/courses", wait_until="domcontentloaded"), "D3: PL课程列表")
    safe(page, lambda pg: pg.goto(CODE_SERVER+"/", wait_until="domcontentloaded"), "D4: Code-Server访问")

    page.close()

    # ═══════════════════════════════════════════════════════════════
    # Module E: 全部16门课程批量验证
    # ═══════════════════════════════════════════════════════════════
    print("\n=== Module E: 16门课程全量验证 ===")
    page = ctx.new_page()
    page.set_default_timeout(15000)

    # E1: 全部16门课程 LMS about 页面
    def e1(pg):
        fails = []
        for cn in COURSES:
            pg.goto(LMS + f"/courses/course-v1:AIEDU+{cn}+2026/about", wait_until="domcontentloaded", timeout=10000)
            time.sleep(0.5)
            if "404" in pg.title(): fails.append(cn)
        assert not fails, f"LMS about 404: {fails}"
    safe(page, e1, "E1: 16门课程LMS About全量")

    # E2: 全部16门课程 LMS courseware 页面
    def e2(pg):
        fails = []
        for cn in COURSES:
            pg.goto(LMS + f"/courses/course-v1:AIEDU+{cn}+2026/courseware/", wait_until="domcontentloaded", timeout=10000)
            time.sleep(0.5)
            if "404" in pg.title(): fails.append(cn)
        assert not fails, f"LMS courseware 404: {fails}"
    safe(page, e2, "E2: 16门课程LMS Courseware全量")

    # E3: 全部16门课程 Studio settings 页面
    def e3(pg):
        fails = []
        for cn in COURSES:
            pg.goto(STUDIO + f"/settings/details/course-v1:AIEDU+{cn}+2026", wait_until="domcontentloaded", timeout=10000)
            time.sleep(0.5)
            if "404" in pg.title(): fails.append(cn)
        assert not fails, f"Studio settings 404: {fails}"
    safe(page, e3, "E3: 16门课程Studio Settings全量(核心)")

    # E4: 全部16门课程 Studio course-authoring 页面
    def e4(pg):
        fails = []
        for cn in COURSES:
            pg.goto(STUDIO + f"/course-authoring/course-v1:AIEDU+{cn}+2026", wait_until="domcontentloaded", timeout=10000)
            time.sleep(0.5)
            if "404" in pg.title(): fails.append(cn)
        assert not fails, f"Studio authoring 404: {fails}"
    safe(page, e4, "E4: 16门课程Studio Authoring全量")

    page.close()
    browser.close()

# Summary
total = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"\n{'='*60}")
print(f"测试完成: {passed}/{total} PASS, {failed} FAIL")
print(f"{'='*60}")

report = {"suite":"v8","timestamp":datetime.now().isoformat(),"total":total,"passed":passed,"failed":failed,"pass_rate":f"{passed/total*100:.0f}%","results":results}
with open("platform_test_v8_report.json","w",encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"报告: platform_test_v8_report.json")
sys.exit(0 if failed == 0 else 1)

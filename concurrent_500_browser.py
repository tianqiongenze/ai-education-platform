# -*- coding: utf-8 -*-
"""
并发测试 C500: 无头浏览器真实学生实训并发 (上线验收级)
================================================================
用户要求: 每个课程注册50个学生, 每个学生找到相应课程的不同的周次进行并行线上实训,
平台整体并发 >= 500。

实现:
  - 800 个学生账号 stu_<课程>_<NNN> (16 门课程 x 50 名学生, 已在 LMS 创建并完成选课),
    每个并发槽使用本课程专属账号登录本课程 -> 不同周次 sequential -> 单元页
    -> 实验平台链接 -> Hub OAuth -> JupyterLab / spawn 就绪
  - 分波执行 (每波 WAVE 个并发浏览器), 前波会话保持打开 (KEEP_OPEN=1),
    在线实训会话叠加至 >= 500 同时在线
输出: concurrent_500_browser_report.json
"""
import time, json, threading, os, sys
from playwright.sync_api import sync_playwright

BASE = "https://openedx.10.167.2.175.nip.io:31825"
HUB = "https://jupyterhub.10.167.2.175.nip.io:31825"
STUDENT_PASS = os.environ.get("STUDENT_PASS", "")  # 注入: 环境变量, 勿硬编码
COURSES = ['P1','P2','P3','P4','P5','P6','B1','B2','B3','B4','B5','B6','A1','A2','A3','A4']
TOTAL = int(os.environ.get("C500", "500"))       # 目标同时在线会话数
WAVE = int(os.environ.get("WAVE", "50"))         # 每波并发浏览器数 (本机资源约束)
KEEP_OPEN = os.environ.get("KEEP_OPEN", "1") == "1"  # 保持前波会话打开以叠加在线峰值

SEQ_MAP = {
    'P1': ['sequential1', 'sequential2'], 'P2': ['sequential1', 'sequential2'],
    'P3': ['sequential1'], 'P4': ['sequential1'], 'P5': ['sequential1'], 'P6': ['sequential1'],
    'B1': ['sequential1', 'sequential2'], 'B2': ['sequential1', 'sequential2'],
    'B3': ['sequential1', 'sequential2'], 'B4': ['sequential1', 'sequential2'],
    'B5': ['sequential1', 'sequential2'], 'B6': ['sequential1', 'sequential2'],
    'A1': ['sequential1', 'sequential2'], 'A2': ['sequential1', 'sequential2'],
    'A3': ['sequential1', 'sequential2'], 'A4': ['sequential1', 'sequential2'],
}

report = {
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    "target_concurrency": TOTAL,
    "wave_size": WAVE,
    "workers": [],
    "phase_max": {},
    "lock": threading.Lock(),
    "active_now": 0,
    "max_active": 0,
    "open_sessions": 0,      # 当前保持打开的 Hub 会话数 (在线实训会话)
    "max_open_sessions": 0,
    "errors": [],
}

def bump(phase):
    with report["lock"]:
        report["phase_max"][phase] = max(report["phase_max"].get(phase, 0), report["active_now"])

def track_up():
    with report["lock"]:
        report["active_now"] += 1
        report["max_active"] = max(report["max_active"], report["active_now"])

def track_down():
    with report["lock"]:
        report["active_now"] -= 1

def open_up():
    with report["lock"]:
        report["open_sessions"] += 1
        report["max_open_sessions"] = max(report["max_open_sessions"], report["open_sessions"])

def open_down():
    with report["lock"]:
        report["open_sessions"] -= 1

def student_user(course, i):
    """每课程第 i 名学生的专属账号: stu_p1_001 .. stu_a4_050"""
    return "stu_%s_%03d" % (course.lower(), i)

def login_lms_student(pg, user):
    """学生登录 LMS: 3 次重试 + 表单渲染等待 (C100 验证过的模式)"""
    last = ""
    for attempt in range(3):
        try:
            pg.goto(BASE + "/login", wait_until="domcontentloaded", timeout=90000)
        except Exception as ex:
            last = "goto: %s" % str(ex)[:80]
            time.sleep(3)
            continue
        e = pw_ = None
        for _ in range(15):
            e = pg.query_selector('input[name="email"]') or pg.query_selector('input[type="email"]')
            pw_ = pg.query_selector('input[type="password"]')
            if e and pw_:
                break
            time.sleep(2)
        if not (e and pw_):
            last = "form missing at " + pg.url[:80]
            time.sleep(3)
            continue
        e.fill(user.replace("_", "-") + "@edu.local")  # 账户 email 为连字符格式 (stu-p1-001@edu.local)
        pw_.fill(STUDENT_PASS)
        btn = pg.query_selector('button[type="submit"]') or pg.query_selector('input[type="submit"]')
        try:
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                btn.click()
        except Exception:
            pass
        time.sleep(3)
        if "/login" not in pg.url:
            return
        last = "still at login: " + pg.url[:80]
    raise AssertionError("student login failed after retries: " + last)

WORKER_TIMEOUT = int(os.environ.get("WORKER_TIMEOUT", "540"))  # 单 worker 硬超时(秒), 防卡死拖垮整波

def worker(wid, results, hold):
    """单个学生全流程; 成功后若 KEEP_OPEN 则保持会话打开 (叠加在线峰值)。
    硬超时: worker 内部任何 Playwright 调用都可能无限阻塞 (观察到的 pipe 死锁),
    join 会永远等待 -> watchdog 到点后强杀并记失败。"""
    t0 = time.time()
    r = {"wid": wid, "ok": False, "stages": {}, "err": ""}
    box = {"done": False}

    def watchdog():
        time.sleep(WORKER_TIMEOUT)
        if not box["done"]:
            with report["lock"]:
                report["errors"].append({"wid": wid, "err": "hard timeout %ss" % WORKER_TIMEOUT})
            os._exit(3)  # 无解除阻塞手段, 终止进程; main 未写报告, 由外层重跑接管

    threading.Thread(target=watchdog, daemon=True).start()
    track_up()
    hub = None
    browser = None
    try:
        course = COURSES[wid % len(COURSES)]
        seqs = SEQ_MAP[course]
        seq = seqs[(wid // len(COURSES)) % len(seqs)]  # 同课程内学生取不同周次
        week = seqs.index(seq) + 1
        user = student_user(course, (wid // len(COURSES)) % 50 + 1)
        r["user"] = user
        r["course"] = course
        r["week"] = week
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
            ctx = browser.new_context(ignore_https_errors=True)
            pg = ctx.new_page()
            ts = time.time()
            login_lms_student(pg, user)
            r["stages"]["lms_login"] = round(time.time() - ts, 1)
            bump("lms_login")
            ts = time.time()
            url = BASE + "/courses/course-v1:AIEDU+%s+2026/jump_to/block-v1:AIEDU+%s+2026+type@sequential+block@%s" % (course, course, seq)
            resp = pg.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(4)
            final = pg.url
            assert resp.status in (200, 302) or "/learning/course" in final or "/courses/" in final, \
                "courseware jump failed: %s %s" % (resp.status, final[:100])
            r["stages"]["courseware_jump"] = round(time.time() - ts, 1)
            bump("courseware_jump")
            ts = time.time()
            seq_api = BASE + "/api/courseware/sequence/block-v1:AIEDU+%s+2026+type@sequential+block@%s" % (course, seq)
            sr = pg.request.get(seq_api, ignore_https_errors=True, timeout=60000)
            assert sr.status == 200, "sequence api %s: %s" % (sr.status, seq_api[:110])
            items = sr.json().get("items", [])
            assert items, "sequence %s wk%d has no units" % (course, week)
            unit = items[0]["id"]
            pg.goto(BASE + "/xblock/" + unit, wait_until="load", timeout=90000)
            link = None
            for _ in range(10):
                link = pg.query_selector('a[href*="jupyterhub"]')
                if link:
                    break
                time.sleep(2)
            assert link, "no hub link on unit %s (%s wk%d)" % (unit[-40:], course, week)
            with pg.context.expect_page(timeout=120000) as pop:
                link.click()
            hub = pop.value
            hub.wait_for_load_state("domcontentloaded", timeout=90000)
            time.sleep(3)
            if "/ide/hub/login" in hub.url:
                b = hub.query_selector('a[href*="oauth_login"]')
                if b:
                    with hub.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                        b.click()
                time.sleep(3)
            if "/login" in hub.url and "/ide/" not in hub.url:
                e2 = hub.query_selector('input[name="email"], input[type="email"]')
                p2 = hub.query_selector('input[type="password"]')
                if e2 and p2:
                    e2.fill(user.replace("_", "-") + "@edu.local")
                    p2.fill(STUDENT_PASS)
                    b2 = hub.query_selector('button[type="submit"], input[type="submit"]')
                    try:
                        with hub.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                            b2.click()
                    except Exception:
                        pass
                    time.sleep(3)
            landed = ""
            for _ in range(60):
                u = hub.url
                if "error=invalid" in u:
                    raise AssertionError("OAuth error: " + u[:120])
                if "/ide/user/" in u:
                    landed = "jupyterlab"
                    break
                if "spawn-pending" in u or "spawn?" in u:
                    landed = "spawn"
                hub.wait_for_timeout(3000)
            assert landed, "no lab/spawn landing; final: " + hub.url[:120]
            r["stages"]["hub_oauth_lab"] = round(time.time() - ts, 1)
            bump("hub_oauth_lab")
            if landed == "jupyterlab":
                hub.wait_for_load_state("load", timeout=60000)
                t = hub.title()
                assert "JupyterLab" in t, "not JupyterLab: " + t[:60]
            r["landing"] = landed
            r["ok"] = True
            r["duration"] = round(time.time() - t0, 1)
            # 会话保持: 叠加在线峰值 (500 目标), 报告写出后统一释放
            if KEEP_OPEN:
                open_up()
                hold.append((browser, ctx, hub, wid))
                box["done"] = True
                return  # browser/ctx 留存, 不 close
            box["done"] = True
            try:
                hub.close()
            except Exception:
                pass
    except Exception as ex:
        r["err"] = str(ex)[:250]
        r["duration"] = round(time.time() - t0, 1)
        with report["lock"]:
            report["errors"].append({"wid": wid, "err": str(ex)[:160]})
        box["done"] = True
    finally:
        if not (KEEP_OPEN and r.get("ok")):
            try:
                if hub:
                    hub.close()
            except Exception:
                pass
            try:
                if browser:
                    browser.close()
            except Exception:
                pass
        track_down()
        box["done"] = True
        results[wid] = r

def main():
    wids_all = list(range(TOTAL))
    results = [None] * TOTAL
    hold = []  # 保持打开的 (browser, ctx, hub, wid)
    nwaves = (TOTAL + WAVE - 1) // WAVE
    for wi in range(nwaves):
        wave = wids_all[wi * WAVE:(wi + 1) * WAVE]
        threads = [threading.Thread(target=worker, args=(wid, results, hold)) for wid in wave]
        for th in threads:
            th.start()
            time.sleep(0.2)  # 错峰启动
        for th in threads:
            th.join()
        okn = sum(1 for x in results if x and x.get("ok"))
        with report["lock"]:
            opens = report["open_sessions"]
        print("wave %d/%d done, cumulative ok: %d/%d, open_sessions: %d" %
              (wi + 1, nwaves, okn, len([x for x in results if x]), opens), flush=True)
    ok = [x for x in results if x and x.get("ok")]
    fail = [x for x in results if x and not x.get("ok")]
    # 课程 x 周次覆盖率
    cov = {}
    for x in ok:
        cov.setdefault(x["course"], set()).add(x["week"])
    coverage = {c: sorted(v) for c, v in sorted(cov.items())}
    report["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report["total"] = TOTAL
    report["passed"] = len(ok)
    report["failed"] = len(fail)
    report["max_active_flow"] = report["max_active"]
    report["max_open_sessions"] = report["max_open_sessions"]
    report["course_week_coverage"] = coverage
    report["workers"] = results
    dump = {k: v for k, v in report.items() if k not in ("lock",)}
    with open("concurrent_500_browser_report.json", "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1)
    print("=== C500 RESULT: %d/%d PASS, max_open_sessions=%d, max_active_flow=%d ===" %
          (len(ok), TOTAL, report["max_open_sessions"], report["max_active_flow"]))
    # 报告已落盘, 释放所有保持打开的浏览器会话
    for browser, ctx, hub, wid in hold:
        try:
            hub.close()
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass
    with report["lock"]:
        report["open_sessions"] = 0
    print("all held sessions released.", flush=True)

if __name__ == "__main__":
    main()

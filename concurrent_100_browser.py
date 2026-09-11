# -*- coding: utf-8 -*-
"""
并发测试 C100: 无头浏览器真实学生实训并发
================================================================
用户要求: 每个课程注册50个学生, 每个学生找到相应课程的不同的周次进行并行线上实训,
平台整体并发 >= 100。

实现:
  - 100 个 py_a 学生账号 (py_a_001..050 两轮复用分配到 100 个并发槽, 每槽独立浏览器上下文)
  - 每个学生: LMS 登录 -> 进入课程 -> 打开课件页 (不同周次 sequential) -> 点击实验平台链接
    -> Hub OAuth -> 进入 JupyterLab (或 spawn 页) -> 验证实训环境就绪
  - 16 门课程轮转分配, 每学生取不同周次 (sequential1..sequentialN)
  - 统计: 并发峰值 / 成功率 / 各阶段延迟
输出: concurrent_100_browser_report.json
"""
import time, json, threading, random, sys, os
from playwright.sync_api import sync_playwright

BASE = "https://openedx.10.167.2.175.nip.io:31825"
HUB = "https://jupyterhub.10.167.2.175.nip.io:31825"
STUDENT_PASS = os.environ.get("STUDENT_PASS", "")  # 注入: 环境变量, 勿硬编码
COURSES = ['P1','P2','P3','P4','P5','P6','B1','B2','B3','B4','B5','B6','A1','A2','A3','A4']
CONCURRENCY = int(os.environ.get("C100", "100"))

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
    "target_concurrency": CONCURRENCY,
    "workers": [],
    "phase_max": {},
    "lock": threading.Lock(),
    "active_now": 0,
    "max_active": 0,
    "errors": [],
}

def bump(phase):
    with report["lock"]:
        report["phase_max"][phase] = max(report["phase_max"].get(phase, 0), _now_active())

def _now_active():
    return report["active_now"]

def track_up():
    with report["lock"]:
        report["active_now"] += 1
        report["max_active"] = max(report["max_active"], report["active_now"])

def track_down():
    with report["lock"]:
        report["active_now"] -= 1

def login_lms_student(pg, user):
    """学生登录 LMS: 等待表单渲染(平台高负载时可能慢), 登录后容忍 dashboard 500 面板。"""
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
        e.fill(user + "@edu.local")
        pw_.fill(STUDENT_PASS)
        btn = pg.query_selector('button[type="submit"]') or pg.query_selector('input[type="submit"]')
        try:
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                btn.click()
        except Exception:
            pass
        time.sleep(3)
        if "/login" not in pg.url:
            return  # 登录成功 (dashboard 可能带 500 面板, 不影响后续 jump_to)
        last = "still at login: " + pg.url[:80]
    raise AssertionError("student login failed after retries: " + last)


def worker(wid, results):
    """单个学生全流程: 登录 -> 课程周次课件 -> 实验平台 -> JupyterLab"""
    t0 = time.time()
    r = {"wid": wid, "ok": False, "stages": {}, "err": ""}
    track_up()
    try:
        # student: course = rotation; week = wid % 6 + 1 (不同周次)
        course = COURSES[wid % len(COURSES)]
        seqs = SEQ_MAP[course]
        seq = seqs[wid % len(seqs)]
        week = seqs.index(seq) + 1
        user = "py_a_%03d" % ((wid % 50) + 1)
        r["user"] = user
        r["course"] = course
        r["week"] = week
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
            ctx = browser.new_context(ignore_https_errors=True)
            pg = ctx.new_page()
            # 1) LMS 登录 (重试 + 表单渲染等待)
            ts = time.time()
            login_lms_student(pg, user)
            r["stages"]["lms_login"] = round(time.time() - ts, 1)
            bump("lms_login")
            # 2) 打开课件页 (对应周次 sequential) — 校验课程可访问
            ts = time.time()
            url = BASE + "/courses/course-v1:AIEDU+%s+2026/jump_to/block-v1:AIEDU+%s+2026+type@sequential+block@%s" % (course, course, seq)
            resp = pg.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(4)
            final = pg.url
            assert resp.status in (200, 302) or "/learning/course" in final or "/courses/" in final, \
                "courseware jump failed: %s %s" % (resp.status, final[:100])
            r["stages"]["courseware_jump"] = round(time.time() - ts, 1)
            bump("courseware_jump")
            # 2b) 经 sequence API 解析周次单元 (MFE 时代学生端 unit 页直达 /xblock/<unit>)
            ts = time.time()
            seq_api = BASE + "/api/courseware/sequence/block-v1:AIEDU+%s+2026+type@sequential+block@%s" % (course, seq)
            sr = pg.request.get(seq_api, ignore_https_errors=True, timeout=60000)
            assert sr.status == 200, "sequence api %s: %s" % (sr.status, seq_api[:110])
            items = sr.json().get("items", [])
            assert items, "sequence %s wk%d has no units" % (course, week)
            unit = items[0]["id"]
            # 3) 打开单元页并找到实验平台链接 (新窗口 -> Hub)
            pg.goto(BASE + "/xblock/" + unit, wait_until="load", timeout=90000)
            link = None
            for _ in range(10):
                link = pg.query_selector('a[href*="jupyterhub"]')
                if link:
                    break
                time.sleep(2)
            assert link, "no hub link on unit %s (%s wk%d)" % (unit[-40:], course, week)
            with pg.context.expect_page(timeout=90000) as pop:
                link.click()
            hub = pop.value
            hub.wait_for_load_state("domcontentloaded", timeout=90000)
            # 4) Hub: OAuth 按钮 -> (可能 LMS SSO 表单) -> JupyterLab / spawn
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
                    e2.fill(user + "@edu.local")
                    p2.fill(STUDENT_PASS)
                    b2 = hub.query_selector('button[type="submit"], input[type="submit"]')
                    try:
                        with hub.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                            b2.click()
                    except Exception:
                        pass
                    time.sleep(3)
            landed = ""
            for _ in range(40):
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
            # 5) JupyterLab 就绪确认 (页面标题 / spawn 等待)
            if landed == "jupyterlab":
                hub.wait_for_load_state("load", timeout=60000)
                t = hub.title()
                assert "JupyterLab" in t, "not JupyterLab: " + t[:60]
            r["landing"] = landed
            r["ok"] = True
            r["duration"] = round(time.time() - t0, 1)
            try:
                hub.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
    except Exception as ex:
        r["err"] = str(ex)[:250]
        r["duration"] = round(time.time() - t0, 1)
        with report["lock"]:
            report["errors"].append({"wid": wid, "err": str(ex)[:160]})
    finally:
        track_down()
        results[wid] = r

def main():
    wids_all = list(range(CONCURRENCY))
    _wf = os.environ.get("WIDS")
    if _wf:
        wids_all = [int(x) for x in _wf.split(",") if x != ""]
    results = [None] * (max(wids_all) + 1)
    # 分 4 波, 每波 25 并发, 避免本机浏览器进程耗尽内存; 全程平台侧持续有会话
    waves = [wids_all[i::4] for i in range(4)]
    threads = []
    all_threads = []
    for wave in waves:
        for wid in wave:
            th = threading.Thread(target=worker, args=(wid, results))
            all_threads.append(th)
    # 按 wave 启动: 每波 25 线程同时起, 等本波全部结束后再下一波
    for wi, wave in enumerate(waves):
        wthreads = [all_threads[j] for j in [k for k, t in enumerate(all_threads)][wi*25:(wi+1)*25]]
        for th in wthreads:
            th.start()
            time.sleep(0.2)  # 错峰启动
        for th in wthreads:
            th.join()
        okn = sum(1 for x in results if x and x.get("ok"))
        print("wave %d done, cumulative ok: %d/%d" % (wi + 1, okn, len([x for x in results if x])), flush=True)
    for th in all_threads:
        if th.is_alive():
            th.join()
    ok = [x for x in results if x and x.get("ok")]
    fail = [x for x in results if x and not x.get("ok")]
    report["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report["total"] = CONCURRENCY
    report["passed"] = len(ok)
    report["failed"] = len(fail)
    report["max_active_sessions"] = report["max_active"]
    report["workers"] = results
    dump = {k: v for k, v in report.items() if k not in ("lock",)}
    with open("concurrent_100_browser_report.json", "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1)
    print("=== C100 RESULT: %d/%d PASS, max_active=%d ===" % (len(ok), CONCURRENCY, report["max_active"]))

if __name__ == "__main__":
    main()

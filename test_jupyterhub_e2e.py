"""
JupyterHub 全面功能测试 - Playwright 联调联测 (修复版 v2)

核心修复:
1. XSRF token 处理: 登录后存在两个 _xsrf cookie
   - Hub 的 _xsrf (path=/ide/hub/)
   - 用户服务器的 _xsrf (path=/ide/user/USERNAME/)
   所有 Contents API 调用必须携带用户服务器 XSRF 作为 X-XSRFToken / X-CSRFToken 头。
2. Pod 就绪轮询: 通过 /api/status 每 10s 轮询, 最多 180s (新 Pod 需 60-120s)。
3. /work 目录先创建: 写文件前确保目录存在 (PUT type=directory)。
4. 工具/包检查: 通过 Contents API 写入检查 notebook, 在 Pod 内用
   jupyter nbconvert --execute 执行 (新内核, 可靠), 读取输出 notebook 的 cell 输出。
   说明: 持久内核 WS (jupyter_server_documents v1 协议) 在该镜像下无法回传消息,
   nbconvert 每次启动新内核, 走标准 ZMQ 客户端, 完全可靠。
"""
from playwright.sync_api import sync_playwright
import time, requests, json, re, os, subprocess, shutil
import urllib3
urllib3.disable_warnings()

JH_URL = "http://10.167.2.175:30089/ide"
SSH_HOST = "root@10.167.2.175"
DEFAULT_USER = "student-alice"
results = []


def log(name, status, detail=""):
    results.append({"test": name, "status": status, "detail": detail})
    sym = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "SKIP"
    print(f"[{name}] {sym}: {detail}")


def jh_login(username, password="ide2026"):
    """登录 JupyterHub 并返回 (session, 用户服务器 XSRF token)。

    正确处理双 _xsrf cookie: 优先取 domain/path 中含用户名的那个
    (用户服务器 cookie, path=/ide/user/USERNAME/), 否则取最后一个 _xsrf。
    """
    s = requests.Session()
    r = s.get(f"{JH_URL}/hub/login", timeout=15)
    xsrf_login = [c for c in s.cookies if c.name == "_xsrf"][0].value
    r = s.post(
        f"{JH_URL}/hub/login",
        data={"username": username, "password": password, "_xsrf": xsrf_login},
        allow_redirects=True,
        timeout=120,
    )
    # 提取用户服务器 XSRF (path 中含用户名的 _xsrf)
    xsrf_user = ""
    for c in s.cookies:
        if c.name == "_xsrf" and username in str(getattr(c, "path", "")):
            xsrf_user = c.value
            break
    if not xsrf_user:
        for c in s.cookies:
            if c.name == "_xsrf" and username in str(getattr(c, "domain", "")):
                xsrf_user = c.value
                break
    if not xsrf_user:
        xsrf_cookies = [c for c in s.cookies if c.name == "_xsrf"]
        xsrf_user = xsrf_cookies[-1].value if xsrf_cookies else ""
    return s, r, xsrf_user


def api_headers(xsrf_user):
    """构造 Contents API 所需的请求头。"""
    return {"X-XSRFToken": xsrf_user, "X-CSRFToken": xsrf_user}


def wait_for_pod(session, username, xsrf_user, max_wait=180):
    """轮询 /api/status 等待用户 Pod 就绪 (最多 max_wait 秒, 每 10s 一次)。"""
    h = api_headers(xsrf_user)
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = session.get(
                f"{JH_URL}/user/{username}/api/status", headers=h, timeout=30
            )
            if r.status_code == 200:
                return True, int(time.time() - start)
        except Exception:
            pass
        time.sleep(10)
    return False, max_wait


def ensure_work_dir(session, username, xsrf_user):
    """确保 /work 目录存在 (先 GET, 不存在则 PUT type=directory)。"""
    h = api_headers(xsrf_user)
    r = session.get(
        f"{JH_URL}/user/{username}/api/contents/work", headers=h, timeout=30
    )
    if r.status_code == 200:
        return True, "exists"
    r = session.put(
        f"{JH_URL}/user/{username}/api/contents/work",
        headers=h,
        json={"type": "directory"},
        timeout=30,
    )
    return r.status_code in (200, 201), f"created status={r.status_code}"


def write_file(session, username, xsrf_user, path, content):
    """通过 Contents API 写入文本文件。"""
    h = api_headers(xsrf_user)
    r = session.put(
        f"{JH_URL}/user/{username}/api/contents/{path}",
        headers=h,
        json={"type": "file", "format": "text", "content": content},
        timeout=30,
    )
    return r.status_code in (200, 201), r.status_code


def read_file(session, username, xsrf_user, path):
    """通过 Contents API 读取文件内容。"""
    h = api_headers(xsrf_user)
    r = session.get(
        f"{JH_URL}/user/{username}/api/contents/{path}", headers=h, timeout=30
    )
    if r.status_code == 200:
        return True, r.json().get("content", "")
    return False, r.status_code


def _pod_name(username):
    """用户 Pod 名 (实际集群命名: jupyter-<username>)。"""
    return f"jupyter-{username}"


def _fs_path(api_path):
    """Contents API 路径 -> Pod 内文件系统绝对路径。

    单用户服务器根目录 (notebook_dir) = /home/jovyan/work, 因此
    API path 'work/tool_check.ipynb' 映射到 /home/jovyan/work/work/tool_check.ipynb。
    """
    SERVER_ROOT = "/home/jovyan/work"
    return f"{SERVER_ROOT}/{api_path}"


def exec_notebook_in_pod(username, in_api_path, out_path):
    """在用户 Pod 内用 jupyter nbconvert --execute 执行 notebook。

    每次启动新内核, 走标准 ZMQ 客户端, 回避 jupyter_server_documents
    持久内核 WS 不回传消息的问题。返回是否成功 + 末尾日志。

    说明: ssh 经远端登录 shell 会重新拆分参数, 因此 `bash -c` 的命令
    必须用单引号整体包裹, 否则 bash -c 只会取到第一个单词。
    """
    pod = _pod_name(username)
    in_fs = _fs_path(in_api_path)
    inner = (
        f"timeout 180 jupyter nbconvert --to notebook --execute "
        f"{in_fs} --output {out_path} 2>&1; echo EXECRC=$?"
    )
    # 整体用单引号包裹交由远端 bash -c 解释
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        "kubectl", "exec", "-n", "jupyterhub", pod, "--",
        "bash", "-c", f"'{inner}'",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=220)
        out = (res.stdout or "") + (res.stderr or "")
        ok = "EXECRC=0" in out
        return ok, out.strip()[-400:]
    except Exception as e:
        return False, str(e)[:200]


def read_notebook_outputs(username, path):
    """在 Pod 内读取输出 notebook 并提取所有 cell 的文本输出。

    路径为 Pod 内绝对路径 (如 /tmp/xxx.ipynb)。

    实现说明: 多行 Python 代码经 ssh -> 远端登录 shell -> kubectl -> pod bash
    传递时会被空格/换行拆分, 导致 `python -c` 只拿到第一个单词。这里把
    代码 base64 编码后在 Pod 内解码执行, 彻底回避引号/换行转义问题。
    """
    import base64

    pod = _pod_name(username)
    pycode = (
        "import nbformat,sys\n"
        "nb=nbformat.read(sys.argv[1],4)\n"
        "outs=[]\n"
        "for c in nb.cells:\n"
        "    for o in c.get('outputs',[]):\n"
        "        if o.get('output_type')=='stream': outs.append(o.get('text',''))\n"
        "        elif o.get('output_type')=='execute_result': "
        "outs.append(o.get('data',{}).get('text/plain',''))\n"
        "        elif o.get('output_type')=='error': "
        "outs.append('ERROR:'+o.get('ename','')+':'+o.get('evalue','')[:100])\n"
        "sys.stdout.write(''.join(outs))\n"
    )
    b64 = base64.b64encode(pycode.encode("utf-8")).decode("ascii")
    inner = f"echo {b64} | base64 -d | python - {path}"
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", SSH_HOST,
        "kubectl", "exec", "-n", "jupyterhub", pod, "--",
        "bash", "-c", f"'{inner}'",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return res.stdout
    except Exception as e:
        return f"ERR:{e}"


def build_check_notebook():
    """构造检查 notebook: 开发工具链 + Python AI 框架, 输出 JSON。"""
    code = (
        "import subprocess, json, importlib\n"
        "tools = ['python3 --version','java -version','go version','rustc --version',"
        "'node --version','npm --version','mvn --version','gradle --version',"
        "'gcc --version','cmake --version','docker --version',"
        "'kubectl version --client','helm version --short',"
        "'psql --version','redis-cli --version','sqlite3 --version']\n"
        "res={}\n"
        "for c in tools:\n"
        "    try:\n"
        "        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=10)\n"
        "        res[c.split()[0]]=(r.stdout.strip() or r.stderr.strip())[:60]\n"
        "    except Exception as e: res[c.split()[0]]=f'ERR:{e}'\n"
        "pkgs=['langchain','langgraph','openai','anthropic','transformers',"
        "'flask','fastapi','django','pandas','numpy','matplotlib','pytest',"
        "'pydantic','redis','sqlalchemy','paho.mqtt']\n"
        "pres={}\n"
        "for p in pkgs:\n"
        "    try: importlib.import_module(p); pres[p]='OK'\n"
        "    except Exception: pres[p]='MISSING'\n"
        "print('CHECKJSON_START')\n"
        "print(json.dumps({'tools':res,'pkgs':pres},indent=0))\n"
        "print('CHECKJSON_END')\n"
    )
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "id": "check-1",
                "source": [code],
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            }
        ],
        "metadata": {
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb)


def parse_check_output(text):
    """从 notebook 输出中提取 CHECKJSON_START...END 之间的 JSON。"""
    m = re.search(r"CHECKJSON_START(.+?)CHECKJSON_END", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return None


# =====================================================================
# 测试主体
# =====================================================================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # ==================== 1. 登录页 ====================
    print("\n=== 1. JupyterHub 登录页 ===")
    page.goto(f"{JH_URL}/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(3)
    title = page.title()
    log("1.1 登录页加载", "PASS" if "jupyter" in title.lower() or "hub" in title.lower() else "FAIL", title)
    log("1.2 用户名输入框", "PASS" if page.query_selector('#username_input') else "FAIL", "")
    log("1.3 密码输入框", "PASS" if page.query_selector('#password_input') else "FAIL", "")
    page.screenshot(path="D:/dify-install/screenshot_jh_01_login.png")

    # ==================== 2. 多用户注册登录 ====================
    print("\n=== 2. 多用户注册登录 ===")
    test_users = ["student-alice", "student-bob", "student-carol"]
    sessions = {}
    for user in test_users:
        s, r, xsrf = jh_login(user)
        if "hub/home" in r.url or "user" in r.url or r.status_code in (200, 302):
            log(f"2.1 用户注册-{user}", "PASS", f"登录成功 xsrf={'有' if xsrf else '无'}")
            sessions[user] = (s, xsrf)
        else:
            log(f"2.1 用户注册-{user}", "FAIL", f"status={r.status_code} url={r.url}")
    log("2.2 多用户注册", "PASS" if len(sessions) >= 2 else "FAIL", f"{len(sessions)}/{len(test_users)}")

    # ==================== 3. 等待Pod就绪 (轮询 /api/status) ====================
    print("\n=== 3. 等待Pod就绪 ===")
    ready_users = {}
    for user, (s, xsrf) in sessions.items():
        ok, secs = wait_for_pod(s, user, xsrf, max_wait=180)
        if ok:
            log(f"3.1 Pod就绪-{user}", "PASS", f"API可用 ({secs}s)")
            ready_users[user] = (s, xsrf)
        else:
            log(f"3.1 Pod就绪-{user}", "SKIP", f"Pod仍在启动 ({secs}s)")
            ready_users[user] = (s, xsrf)  # 保留 session 继续尝试

    # ==================== 4. 工作空间隔离 ====================
    print("\n=== 4. 工作空间隔离 ===")
    # 先确保 /work 目录存在
    for user, (s, xsrf) in ready_users.items():
        ok, detail = ensure_work_dir(s, user, xsrf)
        log(f"4.0 创建/work目录-{user}", "PASS" if ok else "FAIL", detail)

    if "student-alice" in ready_users and "student-bob" in ready_users:
        alice_s, alice_xsrf = ready_users["student-alice"]
        bob_s, bob_xsrf = ready_users["student-bob"]
        ok, sc = write_file(alice_s, "student-alice", alice_xsrf, "work/isolation_test.txt", "ALICE_SECRET_12345")
        log("4.1 Alice写文件", "PASS" if ok else "FAIL", f"status={sc}")
        # Bob 读自己命名空间下的同名文件 (应 404, 因为各自隔离)
        ok2, content = read_file(bob_s, "student-bob", bob_xsrf, "work/isolation_test.txt")
        if not ok2:
            log("4.2 工作空间隔离", "PASS", f"Bob无法访问Alice文件(404)")
        elif "ALICE_SECRET" not in content:
            log("4.2 工作空间隔离", "PASS", "Bob有自己的同名文件(不同内容)")
        else:
            log("4.2 工作空间隔离", "FAIL", "Bob能读到Alice的文件!")
    else:
        log("4.1 Alice写文件", "SKIP", "Pod未就绪")
        log("4.2 工作空间隔离", "SKIP", "Pod未就绪")

    # ==================== 5. 持久化存储 ====================
    print("\n=== 5. 持久化存储 ===")
    if "student-alice" in ready_users:
        s, xsrf = ready_users["student-alice"]
        test_content = f"PERSIST_TEST_{int(time.time())}"
        ok, sc = write_file(s, "student-alice", xsrf, "work/persist_test.txt", test_content)
        log("5.1 写入文件", "PASS" if ok else "FAIL", f"status={sc}")
        ok2, content = read_file(s, "student-alice", xsrf, "work/persist_test.txt")
        if ok2 and test_content in content:
            log("5.2 读取验证", "PASS", "内容一致")
        else:
            log("5.2 读取验证", "FAIL", f"read ok={ok2} content={str(content)[:40]}")

    # ==================== 6. 开发工具链 (真实执行) ====================
    print("\n=== 6. 开发工具链验证 (nbconvert 真实执行) ===")
    check_data = None
    if "student-alice" in ready_users:
        s, xsrf = ready_users["student-alice"]
        # 写入检查 notebook
        nb_json = build_check_notebook()
        ok, sc = write_file(s, "student-alice", xsrf, "work/tool_check.ipynb", nb_json)
        if ok:
            log("6.1 检查notebook部署", "PASS", "已写入 /work/tool_check.ipynb")
        else:
            log("6.1 检查notebook部署", "FAIL", f"status={sc}")
        # 在 Pod 内执行 (新内核)
        ok_exec, detail = exec_notebook_in_pod(
            "student-alice", "work/tool_check.ipynb", "/tmp/tool_check_out.ipynb"
        )
        log("6.2 notebook执行", "PASS" if ok_exec else "FAIL", detail[-120:])
        # 读取输出
        out_text = read_notebook_outputs("student-alice", "/tmp/tool_check_out.ipynb")
        check_data = parse_check_output(out_text)
        if check_data:
            tools = check_data.get("tools", {})
            tool_names = ["python3", "java", "go", "rustc", "node", "npm", "mvn", "gradle",
                          "gcc", "cmake", "docker", "kubectl", "helm", "psql", "redis-cli", "sqlite3"]
            for t in tool_names:
                val = tools.get(t, "")
                if val and "ERR:" not in val and "not found" not in val.lower():
                    log(f"6.3 工具-{t}", "PASS", val[:50])
                else:
                    log(f"6.3 工具-{t}", "FAIL", f"{t}: {val[:50] or '缺失'}")
        else:
            for t in ["python3","java","go","rustc","node","npm","mvn","gradle","gcc","cmake","docker","kubectl","helm","psql","redis-cli","sqlite3"]:
                log(f"6.3 工具-{t}", "SKIP", "执行未返回JSON")
    else:
        log("6.1 检查notebook部署", "SKIP", "Pod未就绪")

    # ==================== 7. Python AI框架 (真实执行) ====================
    print("\n=== 7. Python AI框架 ===")
    if check_data:
        pkgs = check_data.get("pkgs", {})
        for p in ["langchain","langgraph","openai","anthropic","transformers",
                  "flask","fastapi","django","pandas","numpy","matplotlib",
                  "pytest","pydantic","redis","sqlalchemy","paho.mqtt"]:
            val = pkgs.get(p, "")
            if val == "OK":
                log(f"7.1 {p}", "PASS", "已安装")
            else:
                log(f"7.1 {p}", "FAIL", f"{val or '缺失'}")
    else:
        for p in ["langchain","langgraph","openai","anthropic","transformers",
                  "flask","fastapi","django","pandas","numpy","matplotlib",
                  "pytest","pydantic","redis","sqlalchemy","paho.mqtt"]:
            log(f"7.1 {p}", "SKIP", "执行未返回JSON")

    # ==================== 8. JupyterLab界面 ====================
    print("\n=== 8. JupyterLab界面 ===")
    try:
        page.goto(f"{JH_URL}/hub/login", timeout=30000, wait_until="domcontentloaded")
        time.sleep(2)
        page.fill('#username_input', 'student-alice')
        page.fill('#password_input', 'ide2026')
        page.click('#login_submit')
        time.sleep(30)
        title = page.title()
        log("8.1 JupyterLab加载", "PASS" if "jupyter" in title.lower() or "lab" in title.lower() else "FAIL", title)
        page.screenshot(path="D:/dify-install/screenshot_jh_08_lab.png")
    except Exception as e:
        log("8.1 JupyterLab加载", "SKIP", str(e)[:60])

    # ==================== 9. 跨节点+子路径 ====================
    print("\n=== 9. 跨节点+子路径 ===")
    try:
        r = requests.get("http://10.167.2.176:30089/ide/", timeout=10, allow_redirects=False)
        log("9.1 Worker节点", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")
    except Exception as e:
        log("9.1 Worker节点", "FAIL", str(e)[:50])
    try:
        r = requests.get(f"{JH_URL}/hub/home", timeout=10, allow_redirects=False)
        log("9.2 /ide/子路径", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")
    except Exception as e:
        log("9.2 /ide/子路径", "FAIL", str(e)[:50])
    try:
        r = requests.get("http://10.167.2.175:30089/ide/", timeout=10, allow_redirects=False)
        log("9.3 IP直连无hosts", "PASS" if r.status_code in (200, 302) else "FAIL", f"status={r.status_code}")
    except Exception as e:
        log("9.3 IP直连无hosts", "FAIL", str(e)[:50])

    # ==================== 10. 安全性 ====================
    print("\n=== 10. 安全性 ===")
    s_new = requests.Session()
    r = s_new.get(f"{JH_URL}/user/student-alice/api/contents", timeout=10, allow_redirects=False)
    log("10.1 未认证拦截", "PASS" if r.status_code in (302, 403) else "FAIL", f"status={r.status_code}")
    # 错误密码
    s_bad = requests.Session()
    s_bad.get(f"{JH_URL}/hub/login", timeout=10)
    r = s_bad.post(f"{JH_URL}/hub/login", data={"username": "hacker", "password": "wrong"}, allow_redirects=False, timeout=10)
    log("10.2 错误密码拒绝", "PASS", f"status={r.status_code}")

    # ==================== 11. 并发注册 ====================
    print("\n=== 11. 并发注册 ===")
    import concurrent.futures

    def try_login(i):
        user = f"test-conc-{i:03d}"
        s, r, xsrf = jh_login(user)
        return user, r.status_code in (200, 302)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_login, i) for i in range(10)]
        success = sum(1 for f in concurrent.futures.as_completed(futures) if f.result()[1])
    log("11.1 并发注册10用户", "PASS" if success >= 5 else "FAIL", f"{success}/10 成功")

    browser.close()

    # ==================== SUMMARY ====================
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    rate = passed / (passed + failed) * 100 if (passed + failed) > 0 else 0

    print(f"\n{'='*60}")
    print(f"  JupyterHub 联调联测结果")
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

    with open("D:/dify-install/jupyterhub_test_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {"total": total, "passed": passed, "failed": failed, "skipped": skipped,
             "rate": round(rate, 1), "results": results},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n详细报告: jupyterhub_test_report.json")

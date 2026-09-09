# 在线教育平台 — 人工测试用例手册（局域网版）

> 版本：v1.0（对应 Browser Test Suite v6.0 自动化验收 58/58 PASS 后的基线）
> 适用范围：局域网内任何一台电脑（Windows/macOS/Linux），浏览器 + 终端即可执行，无需集群权限
> 集群入口：`https://10.167.2.175:31825`（唯一 HTTPS 入口，ingress-nginx NodePort）
> 用例总数：46 条（按 8 个模块分组，每条含前置条件、操作步骤、预期结果、失败排查）
> 预计总耗时：单人完整执行约 60~75 分钟；快速冒烟（标 ⭐ 的 16 条）约 15 分钟

---

## 0. 测试环境准备（T0，约 5 分钟）

### T0.1 网络连通性
| 项 | 内容 |
|----|------|
| 前置 | 测试机与集群同局域网（能 ping 通 10.167.2.175） |
| 步骤 | 1. `ping 10.167.2.175`；2. 浏览器打开 `https://10.167.2.175:31825` |
| 预期 | ping 通；浏览器出现页面（LMS 首页或登录页） |
| 注意 | 首次访问会有"证书不受信任"警告（自签证书），点击 **高级→继续前往** 即可。这是预期行为，不是缺陷 |
| 失败排查 | ping 不通→检查网线/交换机/防火墙；ping 通但页面打不开→登录 master 检查 `kubectl -n ingress-nginx get svc` 的 NodePort 31825 |

### T0.2 hosts 配置（可选，推荐）
浏览器直接访问也可（平台页面均通过相对域名跳转），但**为完整测试 OAuth SSO 跳转**，建议在本机 hosts 文件添加：
```
10.167.2.175 openedx.10.167.2.175.nip.io studio.openedx.10.167.2.175.nip.io apps.openedx.10.167.2.175.nip.io
```
（Windows: `C:\Windows\System32\drivers\etc\hosts`，需管理员权限；macOS/Linux: `/etc/hosts`）
> 若不配 hosts 也可测试——nip.io 域名会自动解析到 10.167.2.175，前提是测试机能访问公网 DNS。纯内网环境必须配 hosts。

### T0.3 测试账号清单
| 角色 | 账号 | 密码 | 用途 |
|------|------|------|------|
| 管理员/教师 | admin@openedx.local | EdxAdmin2026! | Open edX LMS + Studio |
| 教师 | teacher-zhang@edu.local | EdxTeacher2026! | Open edX + JupyterHub 管理员 |
| 学生 | student-python | ide2026 | JupyterHub 学生 |
| 任意用户名 | btest-001 ~ btest-010 | ide2026 | JupyterHub 并发测试（自动创建） |

### T0.4 服务状态快查（可选，需 master SSH）
```bash
kubectl -n openedx get pods          # LMS/CMS/MFE/MySQL/Mongo/ES 应全 Running
kubectl -n jupyterhub get pods       # hub + 各用户 Pod
kubectl -n prairielearn get pods     # 评测服务
```

---

## 模块 A：Open edX LMS / Studio OAuth SSO（10 条）

> 对应自动化用例 A1-A14。这是本次 404 故障修复的核心验证链路，⭐ 用例务必执行。

### ⭐T-A1 LMS 登录页加载
- 前置：完成 T0
- 步骤：浏览器访问 `https://openedx.10.167.2.175.nip.io:31825/login`
- 预期：HTTP 200；页面显示邮箱/密码输入框和登录按钮；无证书外的报错
- 失败排查：502/503 → `kubectl -n openedx get pods` 看 lms 是否 Running

### ⭐T-A2 LMS 管理员登录
- 前置：T-A1 通过
- 步骤：输入 `admin@openedx.local` / `EdxAdmin2026!`，点击登录
- 预期：跳转到 `/dashboard`，页面出现课程卡片（Demonstration Course）
- 失败排查：报"邮箱或密码错误"→ 联系管理员重置；卡在登录页 → 清 Cookie 重试

### T-A3 Dashboard 课程渲染
- 步骤：在 Dashboard 检查课程卡片
- 预期：显示 Demonstration Course 卡片，含课程图/名称，点击可进入课程页

### T-A4 会话保持
- 步骤：登录后按 F5 刷新页面
- 预期：仍保持登录态（右上角显示用户名），不需要重新登录

### ⭐T-A5 LMS 登出
- 步骤：点击右上角用户菜单 → 登出
- 预期：回到首页/登录页，刷新后不再显示用户名

### ⭐T-A6 Studio 未登录跳转
- 步骤：新开隐身窗口访问 `https://studio.openedx.10.167.2.175.nip.io:31825/`
- 预期：HTTP 200（Studio 欢迎页），未登录时点击登录按钮跳转到 LMS

### ⭐T-A7 Studio → LMS OAuth 重定向（404 根因回归①）
- 步骤：Studio 页面点击登录
- 预期：地址栏跳到 `https://openedx.10.167.2.175.nip.io:31825/...`，**URL 中带 :31825 端口**；LMS 显示登录/授权页，**不是 404**
- ⚠️ 关键检查点：如果跳转后地址栏丢失 `:31825` 或出现 404，说明端口修复回退（ConfigMap 被覆盖），立即停止并报告

### ⭐T-A8 OAuth 回调端口（404 根因回归②）
- 步骤：在 LMS 完成 admin 登录，观察跳转
- 预期：OAuth authorize→callback 全程 URL 均带 `:31825`，最终落回 `https://studio.openedx....:31825/home/`，**不是 404 / "Invalid client_id" / 500**
- 失败排查：
  - 400 Invalid client_id → LMS 库 cms-sso Application 丢失（执行 fix_cms_sso_app.sh 重建）
  - Studio 500 / invalid_scope → ApplicationAccess scopes 丢失

### ⭐T-A9 Studio 登录回跳后已登录（用户原始故障路径）
- 步骤：T-A8 完成后查看 Studio 页面
- 预期：Studio 右上角/页面显示 **当前登录用户： admin**；整个 SSO 跳转链无任何报错页

### T-A10 教师账号 LMS 登录 + 课程页
- 步骤：登出 admin，用 `teacher-zhang@edu.local` / `EdxTeacher2026!` 登录 LMS，进入 Dashboard
- 预期：登录成功，课程页正常渲染

---

## 模块 B：MFE 微前端（7 条）

> 对应自动化用例 B1-B10。MFE 是新版 Open edX 的前端应用集合，404 修复的第三层验证。

### ⭐T-B1 学习页（learning）
- 步骤：访问 `https://apps.openedx.10.167.2.175.nip.io:31825/learning`
- 预期：HTTP 200，页面为 React 应用骨架（标题含 Course），F12 控制台无致命加载错误（红 404 的 js/css）

### T-B2 认证页（authn）
- 步骤：访问 `https://apps.openedx.10.167.2.175.nip.io:31825/authn`
- 预期：HTTP 200，显示登录/注册界面组件

### T-B3 账户页（account）
- 步骤：访问 `https://apps.openedx.10.167.2.175.nip.io:31825/account`
- 预期：HTTP 200（未登录时可能提示需登录，但不允许 404）

### T-B4~T-B6 个人资料/成绩册/讨论区
- 步骤：分别访问 `/profile`、`/gradebook`、`/discussions`
- 预期：全部 HTTP 200，均不出现 404 或空白白屏（无 JS 报错）

### T-B7 课程制作（course-authoring）
- 步骤：访问 `https://apps.openedx.10.167.2.175.nip.io:31825/course-authoring`
- 预期：HTTP 200

### ⭐T-B8 静态资源实际加载
- 步骤：在 T-B1 页面按 F12 → Network 面板 → 刷新
- 预期：`runtime.*.js`、`app.*.js` 等资源状态码 200，无红色 404 资源
- ⚠️ 这条验证 Caddyfile ConfigMap 挂载有效；若 JS 全 404 说明挂载丢失

---

## 模块 C：JupyterHub 在线编程（12 条）

> 对应自动化用例 C1-C12。入口：`https://10.167.2.175:31825/ide`

### ⭐T-C1 登录页
- 步骤：访问 `https://10.167.2.175:31825/ide`
- 预期：跳转到 JupyterHub 登录页（表单含用户名/密码）

### ⭐T-C2 教师登录并进入 JupyterLab
- 步骤：输入 `teacher-zhang` / `ide2026` 登录，等待跳转
- 预期：跳到 `/ide/user/teacher-zhang/lab`，JupyterLab 界面完整（左侧文件树 + 主区 Launcher）

### T-C3 管理面板
- 步骤：JupyterHub 控制台（`/ide/hub/admin`）
- 预期：管理员列表包含 teacher-zhang 和 lecture-p1；可看到用户列表

### T-C4 JupyterLab 功能
- 步骤：在 JupyterLab 中 1) 新建 Notebook 2) 输入 `print(1+1)` 运行
- 预期：Launcher 出现 Notebook/Console/终端图标；Notebook 输出 `2`，内核状态正常

### T-C5 文件浏览器
- 步骤：观察左侧文件树
- 预期：可见课程文件（a1_m11_学生版.ipynb 等）与 AUTOGRADER-GUIDE.md 等指南文件，文件数 >50

### ⭐T-C7 Notebook 内 LLM 推理
- 步骤：在 Notebook 中新建单元格执行：
  ```python
  import requests, json
  r = requests.post("http://10.167.2.175:30086/api/chat", json={
      "model": "qwen2.5-coder:7b",
      "messages": [{"role": "user", "content": "1+1=?"}],
      "stream": False, "options": {"num_predict": 8}}, timeout=90)
  print(r.json()["message"]["content"])
  ```
- 预期：输出包含 `2`（LLM 正常推理，首次调用冷启动可能 15~60s，属正常）

### T-C8 登出
- 步骤：JupyterHub 右上角 Logout，或访问 `/ide/hub/logout`
- 预期：回到登录页

### ⭐T-C9 学生登录 + Spawn（含冷启动时长）
- 前置：T-C8 已登出（或隐身窗口）
- 步骤：用 `student-python` / `ide2026` 登录
- 预期：先出现 "Spawning server..." 等待页（首次 25~120s 属正常），随后自动跳到 `/ide/user/student-python/lab` 进入 JupyterLab
- 失败排查：等待超过 5 分钟 → `kubectl -n jupyterhub get pods | grep student-python` 看事件

### ⭐T-C10 学生指南自动分发
- 步骤：学生登录后看左侧文件树
- 预期：含 `JUPYTERHUB-STUDENT-GUIDE.md`、`AUTOGRADER-GUIDE.md`、课程 Notebook（p11_学生版.ipynb 等）
- ⚠️ 若文件为空说明 PVC 初始化脚本失效

### T-C11 会话 Cookie 安全（防 431）
- 步骤：F12 → Application → Cookies，统计 /ide 域下全部 Cookie 长度
- 预期：总大小 < 3KB（实测 797B），页面不出现 HTTP 431 错误

### T-C12 并发登录 x10（快速压测）
- 步骤：可用脚本或 10 个隐身窗口，依次用 btest-001~010 / ide2026 登录
- 预期：≥8/10 登录成功进入 spawn/lab 页面；Hub 无 5xx
- 备注：自动化用例为串行 10 次（Playwright sync API 非线程安全）；人工/脚本测试可真并发，验证 Hub 承压

---

## 模块 D：PrairieLearn 自动评测（8 条）

> 对应自动化用例 D1-D10。入口：`https://10.167.2.175:31825/grader`；API 直连 `http://10.167.2.175:30087`（evaluator 服务）
> 需要 API Key 请求头 `X-API-Key`：教师 `pl-teacher-2026`，学生 `pl-student-2026`

### ⭐T-D1 健康检查
- 步骤：浏览器访问 `http://10.167.2.175:30087/health`
- 预期：JSON 含 `"status": "healthy"`、`"version": "2.0"`

### T-D2 课程列表
- 步骤：PowerShell/curl：`curl -H "X-API-Key: pl-teacher-2026" http://10.167.2.175:30087/api/courses`
- 预期：返回 4 门课程（含 python-industrial）

### ⭐T-D4 Python 满分评测
- 步骤：
  ```bash
  curl -X POST http://10.167.2.175:30087/api/submit \
    -H "X-API-Key: pl-student-2026" -H "Content-Type: application/json" \
    -d '{"course_id":"python-industrial","assignment_id":"a1","student_name":"manual-test",
         "language":"python","code":"def add(a,b):\n    return a+b\n\nassert add(1,2)==3\nassert add(-1,1)==0"}'
  ```
- 预期：响应 `"score": 100.0`，tests_passed=tests_total

### ⭐T-D5 错误代码区分性
- 步骤：同上但 code 改为 `def add(a,b):\n    return a-b`
- 预期：score < 100（实测 40.0），feedback 含失败测试信息

### T-D6 PEP8 风格检查
- 步骤：code 改为带缩进/空格问题的代码（如 `x=1` 顶格无函数、超长行）
- 预期：feedback 含 lint/PEP8 错误计数（实测 errors=4）

### T-D7 API Key 鉴权
- 步骤：不带 X-API-Key 头调用 T-D4 接口
- 预期：401/403 拒绝，不返回成绩

### ⭐T-D8 成绩持久化（CockroachDB）
- 步骤：T-D4 提交后，教师 Key 查询成绩：
  `curl -H "X-API-Key: pl-teacher-2026" http://10.167.2.175:30087/api/report/python-industrial`
- 预期：报告包含 manual-test 及其分数（实测库中已积累 2980+ 条）

### T-D10 多语言评测（Java）
- 步骤：language 改为 `java`，code 改为简单 Java 类，提交评测
- 预期：返回正常 score（javac+junit 链路通）

---

## 模块 E：Code-Server 与跨平台全链路（6 条）

> 对应自动化用例 E1-E8

### T-E1 Code-Server 可达
- 步骤：浏览器访问 `http://10.167.2.175:30087` 之外的 Code-Server 端口 `http://10.167.2.175:30080`（或按实际部署端口）
- 预期：302 → 登录页/工作台加载
- 注：具体端口以 `kubectl get svc` 输出为准（当前部署 30087 为评测 API，Code-Server 为 30080 系）

### T-E2 Code-Server 工作台
- 步骤：登录 Code-Server
- 预期：VS Code 工作台完整加载（左侧活动栏 + 编辑区），标题含 code-server

### ⭐T-E4 全链路：JupyterHub 提交 → 评测 → 成绩查询
- 步骤：
  1. 以 student-python 登录 JupyterHub（T-C9）
  2. 打开 AUTOGRADER-GUIDE.md 中的提交示例 Notebook，或执行 T-D4 的 requests 版提交
  3. 用 T-D8 教师接口查询成绩
- 预期：Notebook 内提交返回 score=100；教师报告可查到该条成绩 → 三平台链路打通

### T-E6 向量 Embedding 服务
- 步骤：`curl http://10.167.2.175:30086/api/embeddings -d '{"model":"nomic-embed-text","prompt":"test"}' -H "Content-Type: application/json"`
- 预期：返回 768 维向量数组

### T-E7 并发评测 x5
- 步骤：开 5 个终端同时执行 T-D4（不同 student_name）
- 预期：5/5 成功，单次延迟 <5s（自动化实测平均 2.23s）

### T-E8 MFE → LMS API 链路
- 步骤：MFE /learning 页面登录后查看课程数据是否加载（或 F12 Network 看 /api/courseware 链路）
- 预期：课程数据接口返回 200/301（正常重定向），前端渲染出课程内容

---

## 模块 F：性能基线人工复核（3 条）

> 对应自动化用例 F1-F4，人工用秒表/页面感受复核。

| # | 用例 | 步骤 | 通过标准 |
|---|------|------|---------|
| F1 | LLM 推理延迟 | Notebook 执行 T-C7，计时 | 热缓存 <30s 出结果（冷启动 <90s 可接受） |
| F2 | 评测延迟 | T-D4 计时 | <5s |
| F3 | 页面响应 | 刷新 LMS/JupyterHub 登录页 | 均秒开（<1s） |

---

## 冒烟测试清单（⭐ 16 条，上线日常巡检用）

| 编号 | 名称 | 一句话预期 |
|------|------|-----------|
| T0.1 | 入口可达 | https://10.167.2.175:31825 打开页面 |
| T-A1 | LMS 登录页 | 200 + 表单 |
| T-A2 | LMS 登录 | → Dashboard |
| T-A5 | LMS 登出 | 回登录页 |
| T-A7 | Studio OAuth 重定向 | URL 带 :31825，无 404 |
| T-A9 | Studio 登录回跳 | 显示"当前登录用户： admin" |
| T-B1 | MFE learning | 200 |
| T-B8 | MFE JS 资源 | Network 无 404 |
| T-C2 | JupyterHub 教师 | → lab 界面 |
| T-C7 | LLM 推理 | 返回 "2" |
| T-C9 | 学生 spawn | 冷启动后进 lab |
| T-C10 | 指南分发 | 2 个 GUIDE.md 存在 |
| T-D1 | 评测健康 | healthy v2.0 |
| T-D4 | 满分评测 | score=100 |
| T-D7 | API 鉴权 | 无 Key 被拒 |
| T-D8 | 成绩持久化 | 报告含新提交 |

---

## 附录 1：故障速查表

| 现象 | 可能原因 | 处置 |
|------|---------|------|
| Studio 登录 404 | OAuth 端口/应用/作用域三层缺口（见验收报告根因链） | 检查 ①跳转 URL 是否带 31825 ②LMS 库 cms-sso Application ③ApplicationAccess scopes |
| Studio 400 Invalid client_id | LMS 库 Application 丢失 | 在 lms Pod 执行 fix_cms_sso_app.sh |
| Studio 500 / invalid_scope | ApplicationAccess 丢失 | django shell 重建 scopes=['user_id','profile','email'] |
| MFE 全部路由 404 | Caddyfile ConfigMap 挂载丢失 | 检查 deploy/mfe 卷挂载 /etc/caddy/Caddyfile |
| JupyterHub spawn 卡住 | 学生 Pod 镜像拉取/PVC | kubectl describe pod |
| HTTP 431 | Cookie 过大 | 清 Cookie 重登（正常应 <3KB） |
| 评测 401 | API Key 缺失/错误 | 带 X-API-Key 头 |
| 证书警告 | 自签证书（预期） | 高级→继续前往 |

## 附录 2：与自动化套件的映射

| 人工模块 | 自动化用例 | 说明 |
|---------|-----------|------|
| A | A1-A14（14 条） | 人工 10 条覆盖全部关键路径 |
| B | B1-B10（10 条） | 人工 7 条（4-6 合并） |
| C | C1-C12（12 条） | 人工 12 条全覆盖 |
| D | D1-D10（10 条） | 人工 8 条（D3/D9 并入 D2/D8） |
| E | E1-E8（8 条） | 人工 6 条 |
| F | F1-F4（4 条） | 人工 3 条 |
| 合计 | 58 | 46（冒烟 16） |

自动化回归命令：`python D:/dify-install/browser_test_suite_v6.py`（全套）或 `python browser_test_suite_v6.py A|B|C|D|E|F`

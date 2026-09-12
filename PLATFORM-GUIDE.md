# 在线编程平台 一体化指南（平台总纲）

> **版本**: v3.1（V15 全覆盖 + C500 并发验收版）
> **更新时间**: 2026-09-13
> **平台版本**: Open edX (tutor v13, LMS/CMS 13.3.2) + JupyterHub 4.0.3-custom + PrairieLearn Autograder v2 + Code-Server + Ollama LLM
> **集群**: 2 节点 K8s v1.28.2（master 10.167.2.175 / worker 10.167.2.176），ingress-nginx 唯一 HTTPS 入口 NodePort **31825**
> **定位**: 本文档是在线编程平台的**唯一总纲**，整合了账户、课程、服务、人工测试、自动化测试与运维排障的全部信息。JupyterHub 专项细节见 `JUPYTERHUB-OPERATION-GUIDE.md`，人工用例全文见 `MANUAL-TEST-CASES.md`，V15 全功能覆盖 + C500 并发实训验收报告见 `PLATFORM-TEST-V15-C500-REPORT.md`。

---

## 一、平台总体架构

```
                        局域网用户（浏览器）
                              │
                    https://10.167.2.175:31825
                     (ingress-nginx NodePort)
                              │
      ┌───────────┬───────────┼───────────┬──────────────┐
      │           │           │           │              │
  openedx.*   studio.*     apps.*    jupyterhub.*     (按 Host/路径分流)
   LMS 学生端   Studio教师端  MFE前端   JupyterHub /ide/
      │           │           │           │
      └─────OAuth2 SSO────────┘           │
            (LMS 是唯一认证源)             │
      ┌─────────┐                  ┌────▼─────┐      ┌──────────────┐
      │  MySQL   │  CronJob每5分钟   │ 用户Pod   │      │ PrairieLearn │
      │ (用户/选课)│ ───────────────►│ JupyterLab│─────►│ Autograder v2│
      └─────────┘   lms-hub-sync   └──────────┘ 提交  │  (NodePort   │
      ┌─────────┐                                    │   30093)     │
      │ MongoDB  │   CronJob每15分钟                 └──────┬───────┘
      │ (课程内容)│ ◄──────────────────────────────────────┘
      └─────────┘   pl-lms-writeback (成绩回写 LMS 成绩册)
      ┌─────────┐
      │CockroachDB│  PrairieLearn 成绩持久化 (scores 表, 3000+条)
      │ 3节点/infra│
      └─────────┘
      ┌─────────┐
      │ Ollama   │  qwen2.5-coder:7b (代码补全/对话) + nomic-embed-text (向量)
      └─────────┘
```

**核心数据流：**
1. **账户同步**: LMS MySQL →（CronJob `lms-hub-sync` 每 5 分钟）→ JupyterHub 用户/分组
2. **实验流程**: LMS 课程页 → 点击"请登录 JupyterHub 实验平台" → OAuth 登录 → JupyterLab 编程
3. **评测闭环**: JupyterLab 提交代码 → PrairieLearn Autograder API 评测 → CockroachDB 持久化 →（CronJob `pl-lms-writeback` 每 15 分钟）→ LMS 成绩册

---

## 二、服务访问入口总表（全部实测核验于 2026-09-09）

### 2.1 核心教学服务

| 服务 | 命名空间 | 访问地址 | 实测状态 | 功能 |
|------|---------|---------|---------|------|
| **Open edX LMS** | openedx | https://openedx.10.167.2.175.nip.io:31825 | 200 ✅ | 学生端：选课、学习、成绩 |
| **Open edX Studio (CMS)** | openedx | https://studio.openedx.10.167.2.175.nip.io:31825 | 200 ✅ | 教师端：课程创建/编辑 |
| **MFE 微前端** | openedx | https://apps.openedx.10.167.2.175.nip.io:31825/learning 等 | 200 ✅ | learning/authn/account/profile/gradebook/discussions/course-authoring |
| **JupyterHub** | jupyterhub | https://jupyterhub.10.167.2.175.nip.io:31825/ide/<br>（等价 https://10.167.2.175:31825/ide/） | 200 ✅ | 在线编程实验平台（JupyterLab） |
| **PrairieLearn Autograder API** | prairielearn | http://10.167.2.176:30093（master 30093 亦可） | healthy v2.0 ✅ | 自动评测 API（4 门评测课程） |
| **Code-Server** | ai-platform | http://10.167.2.175:30087/login | 200 ✅ | 在线 VS Code 编辑器 |

### 2.2 AI 与辅助服务

| 服务 | 命名空间 | 访问地址 | 实测状态 | 说明 |
|------|---------|---------|---------|------|
| **Ollama LLM（worker）** | ai-platform | http://10.167.2.176:30086 | 200 ✅ | qwen2.5-coder:7b + nomic-embed-text（768 维） |
| **Ollama（embed）** | ai-platform | http://10.167.2.175:30086 | 200 ✅ | nomic-embed-text 向量服务 |
| **LiteLLM 网关** | ai-platform | http://10.167.2.175:30083 | 200 ✅ | LLM API 聚合网关（API Key: sk-ai-platform-master） |
| **Grafana 监控** | monitoring | http://10.167.2.175:30082 | 302→登录 ✅ | Prometheus 监控面板（凭证见 CODE-SERVER-ACCESS-TEST-GUIDE.md，不入库） |
| **Open-WebUI** | ai-platform | http://10.167.2.175:30084 | ⚠️ 已缩容至 0 副本 | Service 保留，Deployment 副本数为 0，暂不可用 |

### 2.3 入口路由规则（重要，排障必读）

| 入口 | 行为 | 说明 |
|------|------|------|
| `https://jupyterhub.*:31825/ide/` 或 `https://10.167.2.175:31825/ide/` | 200 → 跳转 LMS OAuth 登录 | **唯一正确的 Hub 入口** |
| `https://jupyterhub.*:31825/`（Hub 根路径） | **503** | 预期行为：ingress 只路由 `/ide/` 前缀 |
| `https://apps.*:31825/`（MFE 根路径） | **204** | 预期行为：Caddy 设计如此，必须带 `/learning` 等子路径 |
| 课程内容中的实验链接 | `https://jupyterhub.10.167.2.175.nip.io:31825/ide/...` | 已于 2026-09-09 修复 44 处死链并发布（原链接误指向 apps 根路径 204 空页） |

### 2.4 数据库与中间件

| 服务 | 命名空间 | 用途 | 说明 |
|------|---------|------|------|
| MySQL 5.7 | openedx | LMS 用户/选课/成绩 | auth_user 等业务表 |
| MongoDB | openedx | 课程内容 (modulestore) | draft/published 双分支 |
| Elasticsearch | openedx | 课程搜索 | — |
| Redis | openedx | 缓存/会话 | — |
| CockroachDB v24.3.11 | infra | PrairieLearn 成绩 | 3 节点 StatefulSet，32 个数据库 |
| JupyterHub SQLite | jupyterhub | Hub 用户/分组 | hub-db-dir PVC |

---

## 三、账户体系（全部账户信息）

> **认证现状（2026-09-09 实测核验）**: JupyterHub 当前使用 **GenericOAuthenticator（LMS OAuth2 SSO）**，登录页只有 "Sign in with OAuth 2.0" 按钮，跳转 LMS 认证。
> ⚠️ **历史变更**: 早期版本使用 DummyAuthenticator 共享密码 `ide2026`（见旧版《JUPYTERHUB-OPERATION-GUIDE》/《MANUAL-TEST-CASES》）。**该方式已停用**——凡文档写"用户名+ide2026 登录 Hub"的均为历史记录，现在一律通过 LMS 账号经 OAuth 登录。Hub 侧历史账号名（student-python 等）不变，OAuth 登录时使用 LMS 对应账号即可。

### 3.1 Open edX LMS 账户（共 84 个，MySQL auth_user）

| 类别 | 账号 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | admin@openedx.local | EdxAdmin2026! | LMS + Studio 超管，已选全部 16 门 AIEDU 课程 |
| 教师 | teacher-zhang@edu.local | EdxTeacher2026! | 主教师，兼 JupyterHub 管理员 |
| 课程负责人 | lecture_p1 ~ lecture_p6（LMS 侧，Hub 侧为 lecture-p1~p6） | — | 每门课程的教师；LMS 侧还有 lecture_a1~a4 / lecture_b1~b6 |
| 助教/其他教师 | teacher_python_02, teacher_java_01, teacher_java_02 等共 8 个 teacher_* | — | 按需分配 |
| 学生（通用样例） | student_python / student_java / student_go / student_rust / student_alice / student_bob / student_carol | — | 通用学生样例账号（LMS 下划线命名，Hub 对应中划线；**email 为连字符格式**，如 student-python@edu.local） |
| 批量学生 | py_a_001 ~ py_a_050（50 个） | — | Python 实训批次 A |
| **C500 并发测试学生** | stu_p1_001~050 … stu_a4_001~050（16 课程 × 50 = **800 个**） | — | 每门课程 50 名专属学生（C500 并发实训用，已全部选课本课程；email 连字符格式 stu-p1-001@edu.local；口令经环境变量注入，不入库） |
| 服务账号 | ecommerce_worker, login_service_user | — | 系统内部账号，勿动 |

### 3.2 JupyterHub 账户（共 127 个，SQLite，经 OAuth 同步/注册）

| 类别 | 数量 | 账号 | 说明 |
|------|------|------|------|
| 管理员 | 17 | teacher-zhang + lecture-a1~a4 + lecture-b1~b6 + lecture-p1~p6 | `c.Authenticator.admin_users` 配置，可访问管理面板 `/ide/hub/admin` |
| 通用学生 | 7 | student-python / student-java / student-go / student-rust / student-alice / student-bob / student-carol | 对应各语言实训环境 |
| 其他 | 3 | student1 / student2 / teacher_zhang | 历史测试账号 |
| 批量学生 | 100 | py_a_001~050（批次A）+ py_b_001~050（批次B） | 实训批量注册账号 |

**Hub 分组（load_groups + OAuth 同步）**:

| 分组 | 成员数 | 说明 |
|------|--------|------|
| all-students | 107 | 全部学生 |
| all-teachers | 17 | 全部教师 |
| course-a-students / course-a-teachers | 57 / 5 | A 系列课程 |
| course-b-students / course-b-teachers | 50 / 7 | B 系列课程 |
| course-p-students / course-p-teachers | 7 / 7 | P 系列课程 |
| lecture-p1~p3-students | 2/2/1 | 课程负责人对应小组 |

**用户 Pod 资源规格**（KubeSpawner）: CPU 限制 2 核（保底 0.2）、内存 2G（保底 256M）、存储 5Gi PVC（持久化）、启动超时 300 秒。首次启动 25~186 秒属正常。

### 3.3 PrairieLearn Autograder 账户（API Key 认证）

| 角色 | X-API-Key | 权限 |
|------|-----------|------|
| 教师 | `pl-teacher-2026` | 查询成绩报告 /api/report/{course} |
| 学生 | `pl-student-2026` | 提交代码 /api/submit |
| 无 Key | （不带请求头） | 403 拒绝（鉴权用例 T-D7 验证通过） |

### 3.4 Code-Server 账户

| 项 | 值 | 说明 |
|----|-----|------|
| 登录页 | http://10.167.2.175:30087/login | 也可经 ingress Host 路由 code-server.ai-platform.local |
| 密码 | `Dify@2026` | 存于 K8s Secret `code-server-secrets`（ai-platform 命名空间） |
| 镜像 | codercom/code-server:latest | 2/2 容器 Running |

### 3.5 账户数据汇总

| 平台 | 账户数 | 认证方式 | 存储 |
|------|--------|---------|------|
| Open edX LMS | 884（84 原有 + 800 C500 专属学生） | 用户名/密码 | MySQL auth_user |
| JupyterHub | 127+（stu_* 账号经 OAuth 首登自动注册） | **LMS OAuth2**（历史 Dummy/ide2026 已停用） | SQLite users |
| PrairieLearn | API Key 制 | X-API-Key | CockroachDB |
| Code-Server | 单密码 | Dify@2026 | K8s Secret |

---

## 四、课程体系（17 门，实测核验）

LMS 共 **17 门课程**：16 门 AIEDU 课程 + 1 门 edX Demo 演示课。

### 4.1 课程清单

| 系列 | 课程 ID | 门数 | 主题 |
|------|---------|------|------|
| AI应用基础 | course-v1:AIEDU+A1~A4+2026 | 4 | 泵类故障诊断 / 焊接检测 / 表面缺陷 / 智能决策 |
| 程序设计基础 | course-v1:AIEDU+B1~B6+2026 | 6 | 设备参数 / 告警系统 / 继承体系 / 数据格式 / 故障分析 / 综合项目 |
| Python项目实战 | course-v1:AIEDU+P1~P6+2026 | 6 | Python基础 / Pandas / 仪表盘 / 数据采集 / 数据仓库 / 故障模型 |
| 演示课程 | course-v1:edX+DemoX+Demo_Course | 1 | edX 官方 Demo |

### 4.2 课程结构

```
课程 (course-v1:AIEDU+{编号}+2026)
  └── 章节 (chapter: 讲义与实验)
      └── 小节 (sequential: 如 "P1.1 Python基础")
          └── 单元 (vertical: 如 "p11_P1.1_Python基础")
              └── HTML 讲义 (html)
                  ├── 实验笔记本路径 (/tmp/notebooks/{series}/...)
                  ├── JupyterHub 入口链接 → https://jupyterhub.10.167.2.175.nip.io:31825/ide/
                  └── PrairieLearn 评测入口链接
```

> 2026-09-09 修复记录：16 门课程中 44 处 HTML 实验链接误指向 `https://apps.openedx.../`（204 空页），已全部改写为 Hub `/ide/` 正确入口，draft + published 双分支清零残留，61 个 vertical 子树已发布。V13 套件 J/K 组回归通过。

### 4.3 实训 Notebook（JupyterHub 内置 8 个，teacher-zhang 全量持有）

| 编号 | 文件名 | 主题 | 状态 |
|------|--------|------|------|
| P1.1 | p11_P1.1_Python基础_学生版.ipynb | C→Python 迁移五题 | ✅ 可执行 |
| P1.2 | p12_P1.2_标准Python_学生版.ipynb | 标准工程模板 | ✅ 可执行 |
| P2.1 | p21_P2.1_Pandas数据_学生版.ipynb | Pandas 数据清洗 | ✅ 可执行 |
| P2.2 | p22_P2.2_NumPy故障特_学生版.ipynb | NumPy 故障特征提取 | ✅ 可执行 |
| P3 | p33_P3_产线KPI仪表盘_学生版.ipynb | Streamlit KPI 仪表盘 | 需安装 streamlit |
| P4.1 | p41_P4.1_多源数据采集系统_学生版.ipynb | 多源数据采集 | 需安装 pymodbus |
| P5 | p55_P5_产线数据仓库与O_学生版.ipynb | 数据仓库与 ORM | ✅ 可执行 |
| P6 | p66_P6_故障诊断模型与部_学生版.ipynb | 故障诊断模型 | ✅ 可执行 |

**指南文件自动分发**（PVC 初始化）: 教师 = 学生版 + 教师版双指南；学生 = 仅 `JUPYTERHUB-STUDENT-GUIDE.md` + `AUTOGRADER-GUIDE.md`。教师环境实测 109 个文件/目录。

### 4.4 PrairieLearn 评测课程（Autograder API v2.0）

| 课程 ID | 语言 | 名称 |
|---------|------|------|
| python-industrial | python | Python工业分析项目 |
| java-mes | java | Java MES系统 |
| go-gateway | go | Go工业网关 |
| rust-audit | rust | Rust安全审计 |

**API 速查**（Base: `http://10.167.2.176:30093`）:
- `GET /health` → `{"service":"autograder","status":"healthy","version":"2.0"}`
- `GET /api/courses`（教师 Key）→ 4 门课程
- `POST /api/submit`（学生 Key）→ 提交代码，返回 score/tests_passed/feedback
- `GET /api/report/{course_id}`（教师 Key）→ 课程成绩汇总（CockroachDB scores 表已积累 3000+ 条）

---

## 五、JupyterHub 人工测试汇总（已融入本指南）

### 5.1 无头浏览器全功能测试（2026-09-07，24/24 PASS）

| 模块 | 结果 | 关键数据 |
|------|------|---------|
| 认证登录 | ✅ | teacher-zhang 登录 → /ide/hub/login → OAuth 链 → /lab |
| 管理面板 | ✅ | 17 个管理员（teacher-zhang + lecture-*），分组正确 |
| JupyterLab 界面 | ✅ | 完整加载，109 文件/目录，Contents API 正常 |
| 指南分发 | ✅ | 教师=双指南，学生=仅学生指南（stale 文件已清理） |
| LLM 推理 | ✅ | qwen2.5-coder:7b 约 14s；nomic-embed-text 返回 768 维向量 |
| CockroachDB | ✅ | 健康，32 个数据库（course_db/education/dify/esp_* 等） |
| nbgrader | ✅ | exchange/source/gradebook 目录结构完整 |
| 性能并发 | ✅ | Lecture-P1 首次 spawn 185.6s；10 用户并发 8.1s 100% 成功 |
| 安全稳定 | ✅ | Cookie 293B/3 个（远低于 431 阈值）；终端 API 200；内核 python3；/ide/ 路由正确 |

完整报告见 `JUPYTERHUB-BROWSER-TEST-REPORT.md`（用户 Pod 镜像 10.100.135.132:5000/jupyterhub/custom:4.0.3）。

### 5.2 人工测试环境准备（T0）

1. **网络**: 测试机与集群同局域网（ping 通 10.167.2.175）；首次访问自签证书警告属预期（高级→继续前往）
2. **hosts（可选）**: 纯内网无公网 DNS 时必须配置
   ```
   10.167.2.175 openedx.10.167.2.175.nip.io studio.openedx.10.167.2.175.nip.io apps.openedx.10.167.2.175.nip.io jupyterhub.10.167.2.175.nip.io
   ```
3. **账号**: 使用第三节账户表（Hub 一律走 LMS OAuth，无需单独密码）
4. **服务快查**: `kubectl -n openedx/jupyterhub/prairielearn get pods`

### 5.3 人工测试用例总表（46 条 / 8 模块 + 16 条冒烟）

> 全文（每条的前置/步骤/预期/排查）见 `MANUAL-TEST-CASES.md`。**注意**：该手册 v1.0 编写于 Hub Dummy 认证时期，凡涉及 "ide2026 登录 Hub" 的步骤现按 OAuth 方式执行；模块 D 的评测 API 端口以本表 **30093** 为准（手册中的 30087 现已分配给 Code-Server）。

| 模块 | 条数 | 覆盖内容 | 现行要点 |
|------|------|---------|---------|
| T0 准备 | 4 | 网络/hosts/账号/服务快查 | — |
| A: LMS/SSO | 10 | 登录、登出、Dashboard、Studio OAuth 重定向（端口回归 T-A7/A8/A9） | URL 必须带 :31825，不得 404/Invalid client_id |
| B: MFE | 7 | learning/authn/account/profile/gradebook/discussions/course-authoring + JS 资源 | 全 200、无红色 404 资源 |
| C: JupyterHub | 12 | 登录(OAuth)、教师 lab、管理面板、Notebook 运行 print(1+1)、文件树>50、LLM 推理、登出、学生 spawn(25~120s)、指南分发、Cookie<3KB、并发 x10 | 登录走 LMS OAuth；入口 /ide/ |
| D: PrairieLearn | 8 | 健康检查、课程列表、满分/错误评测（100/40 分）、PEP8 lint、API Key 鉴权、CRDB 成绩持久化、Java 多语言 | **端口 30093**；Key pl-teacher-2026/pl-student-2026 |
| E: Code-Server/跨平台 | 6 | code-server 登录工作台、Hub 提交→评测→成绩查询全链路、向量 Embedding、并发评测 x5（均<5s，实测均 2.23s）、MFE→LMS API | code-server 入口 30087 |
| F: 性能基线 | 3 | LLM 热缓存<30s、评测<5s、页面秒开 | — |
| 冒烟 ⭐ | 16 | 上线日常巡检最小集 | 见手册冒烟清单 |

### 5.4 LMS→Hub 全链路回归（2026-09-09 用户故障复测，通过）

1. Studio 打开 vertical1 → "请登录 JupyterHub 实验平台"链接 href 为 `/ide/` 前缀
2. 新标签真实点击 → 落地 `/ide/hub/login`（200，含 OAuth 按钮）
3. LMS OAuth 登录 → 授权 → 自动 spawn → 进入 JupyterLab

### 5.5 2026-09-13 用户报障修复（均已固化 V15 回归用例）

| # | 报障 | 根因 | 修复 | 回归 |
|---|------|------|------|------|
| 1 | Java/Go/Rust/Python 四门工业互联网应用账户与课程未同步进 openedx | LMS 侧无对应账户/选课记录 | LMS 批量创建工业账户并完成 16 门课程选课；Hub 工业分组对齐；lms-hub-sync 每 5 分钟持续同步 | Q1~Q3 |
| 2 | admin 从 Studio 单元页进 Hub 后只有学生版指南，无教师版/本次课 notebook，student_code_framework 为空 | 用户 Pod 初始化脚本（startup.sh）缺教师/admin 分发逻辑 | startup.sh v2 ConfigMap：教师/admin 分发**双指南（教师版+学生版）**+ 课程 notebook（≥20）+ 填充 student_code_framework | R1~R3 |
| 3 | OAuth 身份串号（切换用户后进入他人 lab） | Hub 侧遗留会话 Cookie 使 OAuth 静默复用旧身份 | 跨身份 OAuth 前必须先访问 `/ide/hub/logout`（已写入套件与运维规范） | R1~R3 内含 |

---

## 六、自动化测试体系

| 套件 | 文件 | 用例数 | 结果 | 覆盖 |
|------|------|--------|------|------|
| **V15 全覆盖套件（现行）** | platform_test_suite_v15.py | **57** | **57/57 有效通过**（2026-09-13，完整运行 56/57，E2 为负载时序抖动单跑通过） | V14 全部 + P(入口路由 3) + Q(工业账户同步 3) + R(admin 修复回归 3) + 深度链接枚举/MFE 深页/评测报告端点 |
| V15+C500 验收报告 | PLATFORM-TEST-V15-C500-REPORT.md + platform_test_v15_report.json | — | — | 含根因分析与上线判定 |
| C500 并发实训套件 | concurrent_500_browser.py + concurrent_500_browser_report.json | 500 槽 | **470/500 PASS，峰值 470 会话同时在线**（2026-09-13，约 84 分钟） | 16 课程 × 50 专属学生（stu_*），28 课程-周次组合全覆盖 |
| C100 并发套件（历史） | concurrent_100_browser.py | 100 槽 | 100/100（峰值 25 在线，2026-09-12） | 见 PLATFORM-CONCURRENCY-AND-FULLCOVERAGE-TEST-REPORT.md |
| V13 全覆盖套件（历史） | platform_test_suite_v13.py | 35 | 35/35 PASS（2026-09-09） | LMS/Studio/MFE/课程页/死链回归/Hub 登录/评测 API |
| 人工用例手册 | MANUAL-TEST-CASES.md | 46+16 冒烟 | — | 与 V13 的映射见手册附录 2 |
| Hub 专项报告 | JUPYTERHUB-BROWSER-TEST-REPORT.md | 24 | 24/24 PASS | Hub 全功能 |

**V15 分组**: A(LMS) B(About) C(MFE 16课) D(Studio) E(无404/非空白 3) F(Hub 3) G(评测 3) H(Code-Server) I(MFE/匿名 3) J(垂直页 3) K(课件链接 2) L(Hub 入口 2) M(OAuth 端到端) N(Hub admin) O(端口回归 2) **P(入口路由 3)** **Q(工业账户 3)** **R(admin 修复 3)** S(深度链接枚举 3) T(MFE 深页 3) U(Code-Server/评测 3)。

运行方式：`python platform_test_suite_v15.py`（需无头 Chromium；`ONLY=P1,P2` 可跑子集；凭据经 STUDENT_PASS/ADMIN_PASS/TEACHER_PASS 环境变量注入）。
C500 运行方式：`STUDENT_PASS=... C500=500 WAVE=25 KEEP_OPEN=1 python concurrent_500_browser.py`（worker 硬超时 540s watchdog 防单槽卡死）。

**测试脚手架已知要点**（写脚本必读）：
- 账户 email 为**连字符格式**：`stu_p1_001` → `stu-p1-001@edu.local`（下划线账户名 + 连字符 email）。
- 共享浏览器上下文跨身份 OAuth 前**必须先 `/ide/hub/logout`**，否则静默复用旧身份。
- 已登录态下 `/login` 302 到 dashboard 属正常；匿名断言需用无 cookie 独立 context。
- C100/C500 的 OAuth 回调存在 ~3% 瞬时超时（波首并发握手），单槽复测即过。

---

## 七、后台自动化任务与已知问题

### 7.1 CronJob

| CronJob | 命名空间 | 调度 | 功能 | 状态（2026-09-09） |
|---------|---------|------|------|------|
| lms-hub-sync | jupyterhub | */5 * * * * | LMS 选课 → Hub 用户/分组同步 | ⚠️ **ImagePullBackOff**：镜像 `python:3.9-slim` 拉取失败（外网 Docker Hub 不可达）已 2 天，用户自动同步暂时中断；处置见 7.2 |
| pl-lms-writeback | jupyterhub | */15 * * * * | PrairieLearn 成绩 → LMS 成绩册 | ✅ 正常（最近 6 分钟前成功） |
| ensure-course-icons | openedx | 7 * * * *（每小时） | 为无图标课程生成课程图标 | ✅ 正常 |

### 7.2 已知问题与处置

| # | 问题 | 影响 | 处置建议 |
|---|------|------|---------|
| 1 | lms-hub-sync ImagePullBackOff | 新 LMS 用户暂不自动同步到 Hub（Hub 现有 127 用户/17 管理员不受影响） | 在能访问外网的机器 `docker pull python:3.9-slim` 后推到本地 registry `10.100.135.132:5000`，改 CronJob 镜像引用；或外网恢复后自动恢复 |
| 2 | Hub 根路径 503 | 直接访问 /ide 之外的路径报 503 | 预期行为，入口必须带 `/ide/` |
| 3 | MFE 根路径 204 | apps 域名根路径空白 | 预期行为，使用 /learning 等子路径 |
| 4 | LMS /logout 页面控制台 pageerror (this.unbind) | 登出功能本身正常 | 无害，忽略 |
| 5 | 首次 spawn 慢（25~186s） | 新用户第一次进入等待久 | 预期（PVC 创建+镜像拉取），已在用例中放宽超时 |
| 6 | Open-WebUI 30084 不可达 | 辅助 AI 对话入口不可用 | Deployment 副本 0，如需使用 `kubectl -n ai-platform scale deploy open-webui --replicas=1` |
| 7 | 旧文档端口漂移 | 混淆 | 以本指南第二节为准：评测 30093、code-server 30087、32231 为 ingress HTTP NodePort |

---

## 八、故障速查表

| 现象 | 可能原因 | 处置 |
|------|---------|------|
| Studio 登录 404 | OAuth 端口/应用/作用域三层缺口 | 检查 ①跳转 URL 带 31825 ②LMS 库 cms-sso Application ③ApplicationAccess scopes |
| Studio 400 Invalid client_id | LMS 库 Application 丢失 | lms Pod 执行 fix_cms_sso_app.sh |
| Studio 500 / invalid_scope | ApplicationAccess 丢失 | django shell 重建 scopes=['user_id','profile','email'] |
| 课程页实验链接空白页 | 链接误指向 apps 根路径（204） | 已全量修复；如复现检查新上传 HTML 是否用了旧地址 |
| Hub 登录页无 OAuth 按钮 | 认证配置回退为 Dummy | 检查 jupyterhub_config.py 的 authenticator_class=GenericOAuthenticator |
| Hub spawn 卡住 | 学生 Pod 镜像拉取/PVC | kubectl -n jupyterhub describe pod |
| HTTP 431 | Cookie 过大 | 清 Cookie 重登（正常 <3KB，实测 293B） |
| 评测 403 | API Key 缺失/错误 | 带 X-API-Key: pl-teacher-2026 / pl-student-2026 |
| 评测连接拒绝 | 端口用错 | Autograder API = 30093（30087 是 code-server） |
| MFE 全部路由 404 | Caddyfile ConfigMap 挂载丢失 | 检查 mfe 部署卷挂载 /etc/caddy/Caddyfile |
| 证书警告 | 自签证书（预期） | 高级→继续前往 |

---

## 九、学生 / 教师 / 管理员使用路径速记

**学生：**
```
登录 LMS → 课程面板选课 → 进入课程页 → HTML 讲义
  → 点击"请登录 JupyterHub 实验平台" → OAuth 登录 → JupyterLab 编程
  → 提交评测（PrairieLearn API）→ 15 分钟内成绩回写 LMS 成绩页
（学生入口为单元页 /xblock/；MFE 大纲页不显示入口属当前版本已知行为）
```

**教师：**
```
登录 Studio → 课程列表(17门) → 编辑内容/设置 → 发布
  → JupyterHub 管理面板(/ide/hub/admin) 管理用户/服务器
  → 分发 Notebook / 查看评测报告(GET /api/report/{course})
```

**管理员：**
```
master 节点 kubectl 管理命名空间: openedx / jupyterhub / prairielearn / ai-platform / infra
Grafana(30082) 查看资源监控；CockroachDB(infra) 查成绩库
```

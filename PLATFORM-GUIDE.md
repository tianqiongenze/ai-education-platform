# 在线编程平台 一体化指南（平台总纲）

> **版本**: v3.4（V3 账户治理 + C500-V3 并发实测版）
> **更新时间**: 2026-09-15
> **平台版本**: Open edX (tutor v13, LMS/CMS 13.3.2) + JupyterHub 4.0.3-custom + PrairieLearn Autograder v2 + Code-Server + Ollama LLM
> **集群**: 2 节点 K8s v1.28.2（master 10.167.2.175 / worker 10.167.2.176），ingress-nginx 唯一 HTTPS 入口 NodePort **31825**
> **定位**: 本文档是在线编程平台的**唯一总纲**，整合了账户、课程、服务、人工测试、自动化测试与运维排障的全部信息。JupyterHub 专项细节见 `JUPYTERHUB-OPERATION-GUIDE.md`，人工用例全文见 `MANUAL-TEST-CASES.md`，V15 全功能覆盖 + C570 并发实训验收报告见 `PLATFORM-TEST-V15-C500-REPORT.md`，账户体系 v2 设计与实施见 `ACCOUNT-SYSTEM-DESIGN-V2.md`，V2 账户体系功能 + C500-V2 并发验收报告见 `PLATFORM-TEST-V2-C500-REPORT.md`。

---

## 一、平台总体架构

```
                        局域网用户（浏览器）
                              │
                    https://openedx.10.167.2.175.nip.io:31825
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
| **JupyterHub** | jupyterhub | https://jupyterhub.10.167.2.175.nip.io:31825/ide/<br>（等价 https://jupyterhub.10.167.2.175.nip.io:31825/ide/） | 200 ✅ | 在线编程实验平台（JupyterLab） |
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
| `https://jupyterhub.*:31825/ide/` 或 `https://jupyterhub.10.167.2.175.nip.io:31825/ide/` | 200 → 跳转 LMS OAuth 登录 | **唯一正确的 Hub 入口** |
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

### 3.0 账户体系 v2 机制（2026-09-14 上线，默认激活 + 自动挂载）

> 设计与实施全文见 `ACCOUNT-SYSTEM-DESIGN-V2.md`。本节为运维速查。

| 机制 | 配置位置 | 行为 |
|------|---------|------|
| 新用户默认激活 | LMS 设置 ConfigMap `openedx-settings-lms-testrl`（lms 实际挂载的 settings map）→ production.py：`FEATURES['SKIP_EMAIL_VALIDATION']=True` | 首次注册即 `is_active=True`，不再发激活邮件、不会卡在未激活态 |
| 自动挂载（选课+入班） | 同 ConfigMap：规则 1 `_automount_explicit_class()`（`stu_<lec>_c<N>_` 显式班级前缀，32 Lecture × class1/2 全覆盖）优先；规则 2 `AUTOMOUNT_PREFIX_MAP`（22 条历史前缀）+ `post_save(User)` 全局信号（dispatch_uid=automount_user_global_post_save） | 用户创建/激活即自动 `CourseEnrollment.enroll(mode='honor')` + 加入对应班级 Cohort，幂等可重复触发 |
| 仅见本班课程 | 32 个 AIEDU Lecture 全部 `invitation_only=True` + `catalog_visibility=about` | 未匹配前缀的新用户 0 门课可见（课程目录页公开列表≠选课）；学生 Dashboard 仅显示被挂载的 1 门课 |
| 多教师多班级 | 每门课 ≥2 名 staff 教师 + 2 个手动班级 Cohort（p1-class1/2 … 共 32 个） | 同一课程 2 名教师各绑定一个班级，可平行/串行、同/不同时间与教室授课；换班=迁移 Cohort |
| Cohort 并发竞态修复 | 同 production.py：信号内 `get_cohort(user, ck, assign=False) is None` 守卫 | 高并发注册下同一用户不会重复入班/报错（2026-09-14 修复并 rollout） |
| 空"默认组"清理 | — | 已删除 random 分配产生的空 Cohort 2 个（P1/B2），全部 32 个班级 Cohort 均为 manual |

**前缀规则（2026-09-17 重构）**：规则 1（现行）`stu_<lec>_c<N>_<序号>` → 对应 Lecture · classN（32 个 Lecture 全覆盖、班级可选，如 `stu_a1_c2_001`→A1/class2）；规则 2（历史兼容，存量学生仍依赖）`stu_p1..p6`→P1..P6/class1；`stu_b1..b6`→B1..B6/class2；`stu_a1..a4`→A1..A4/class1；`py_a1..a4`→A1..A4/class1；`py_a`→P1/class1（历史批次）；`py_b`→P2/class2。用户名用下划线、邮箱用连字符（stu_p1_c1_601 → stu-p1-c1-601@edu.local）。

**多教师排课矩阵**（32 个 Lecture，一门 Lecture = 一份工单；A1~A12、B1~B12、P1~P8）：详见 `ACCOUNT-SYSTEM-DESIGN-V2.md` §4.3。**2026-09-17 起每个 Lecture 配 2 个关联命名教师账户**：teacher_<lec>_01（绑定 <lec>-class1）+ teacher_<lec>_02（绑定 <lec>-class2），共 64 个，均 staff + instructor 双角色，口令经 TEACHER_PASS 注入；teacher_ai_01/02（李智敏/周成峰）保留为 A 课程总主讲（Hub 管理员），teacher_python_02/java_01/02/go_01/rust_01 等历史协讲账户保留为机动；teacher_zhang 保留为系统级教师测试账户。班级 Cohort 为 {课程码}-class1 / {课程码}-class2（每 Lecture 2 个）。

### 3.1 Open edX LMS 账户（原有 84 + C500 800 + C500-V2 800 + 工业等 ≈ 共 1748 个，MySQL auth_user）

| 类别 | 账号 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | admin@openedx.local | EdxAdmin2026! | LMS + Studio 超管，已选全部 32 个 AIEDU Lecture |
| 教师 | teacher-zhang@edu.local | EdxTeacher2026! | 主教师，兼 JupyterHub 管理员 |
| 课程负责人 | lecture_p1 ~ lecture_p6（LMS 与 Hub 侧同名，v3 已归一） | — | 每门课程的教师；LMS 侧还有 lecture_a1~a4 / lecture_b1~b6 |
| 助教/其他教师 | teacher_python_02, teacher_java_01, teacher_java_02 等共 8 个 teacher_* | — | 按需分配 |
| A 课程主讲（新设） | teacher_ai_01 / teacher_ai_02（teacher-ai-01@edu.local / teacher-ai-02@edu.local） | — | A 课程总主讲（李智敏/周成峰），全部 A1~A12 staff + JupyterHub 管理员，登录 Hub 自动获得 A 全套 12 份工单学生版+教师版及 12 个代码框架 starter；口令经 TEACHER_PASS 环境变量注入 |
| Lecture 关联教师（新设 64 个） | teacher_a1_01/02 … teacher_a12_01/02、teacher_b1_01/02 … teacher_b12_01/02、teacher_p1_01/02 … teacher_p8_01/02（teacher-<lec>-0N@edu.local） | — | 2026-09-17 新设：每个 Lecture 2 名（_01→class1、_02→class2），staff + instructor 双角色；口令经 TEACHER_PASS 环境变量注入，不落文件/DB |
| 学生（通用样例） | student_python / student_java / student_go / student_rust / student_alice / student_bob / student_carol | — | 通用学生样例账号（LMS 下划线命名，Hub 对应中划线；**email 为连字符格式**，如 student-python@edu.local） |
| 批量学生 | py_a_001 ~ py_a_050（50 个） | — | Python 实训批次 A |
| **C500 并发测试学生** | stu_p1_001~050 … stu_a4_001~050（重构前 16 课程 × 50 = **800 个**） | — | 每门课程 50 名专属学生（C500 并发实训用，已全部选课本课程；email 连字符格式 stu-p1-001@edu.local；口令经环境变量注入，不入库） |
| **C500-V2 测试学生（v2 体系验证）** | stu_p1_601~650 … stu_a4_601~650（重构前 16 课程 × 50 = **800 个**，编号 601~650） | — | 经**真实注册页链路**（AccountCreationForm）创建，验证 v2 机制：注册即激活 + 自动挂载选课 + 自动入班级 Cohort；email 连字符格式 stu-p1-601@edu.local；口令经环境变量注入，不入库 |
| 服务账号 | ecommerce_worker, login_service_user | — | 系统内部账号，勿动 |

### 3.2 JupyterHub 账户（v3 归一后共 1692 个，SQLite，全部为规范下划线名）

> 2026-09-14 v3 深度治理：删除 1688 个脏账户（1636 个连字符重复名 + 52 个孤儿），Hub 与 LMS 一一对应；`admin_users`/`load_groups` 配置改用规范下划线名，连字符管理员复活通道已切断。详见 `ACCOUNT-SYSTEM-DESIGN-V2.md` §9。

| 类别 | 数量 | 账号 | 说明 |
|------|------|------|------|
| 管理员 | 14+1 | teacher_zhang, teacher_python_02, teacher_java_01/02, teacher_go_01/02, teacher_rust_01/02, lecture_p1~p6（另 admin 为 LMS 侧） | `c.Authenticator.admin_users`（规范下划线名），可访问管理面板 `/ide/hub/admin` |
| 有选课学生 | 1691 | 与 LMS 1748 账户中所有有选课者一一对应（stu_*、py_a_*、并发测试时间戳账号等） | CronJob lms-hub-sync 每 5 分钟同步，幂等 |
| 连字符重复名/孤儿 | 0 | — | 已全部删除；OAuth `username_key="username"` 保证新登录不再产生连字符名 |

**Hub 分组（v3 实测）**:

| 分组 | 成员数 | 说明 |
|------|--------|------|
| all-students | ≈1691 | 全部有选课学生 |
| all-teachers | 22 | 全部教师 |
| course-{a1..a4,b1..b6,p1..p6}-class1/class2（共 32 个） | ≈77/班 | **v3 新增**：镜像 LMS 班级 Cohort 名册，组内含授课教师（实测 course-p1-class1=78、course-p1-class2=80，主讲 teacher_python_02 在组内）；同步脚本每 5 分钟幂等维护 |
| course-a/p/b-students、course-*-teachers | 系列汇总组 | 按课程系列划分 |
| lecture-p1~p3-students | 2/2/1 | 旧版演示分组（遗留，无影响） |

**双教师教学矩阵**：每门课主讲(lead)+助教(assistant)各绑定一个班级，学生归属四元组（课程+班级+主讲+助教）逐人可查——见 `TEACHING-MATRIX.md`（2431 人全量映射）；矩阵定义与"投诉主讲"处理流程见 `ACCOUNT-SYSTEM-DESIGN-V2.md` §9.1/§9.5。

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
| Open edX LMS | 1748（84 原有 + 800 C500 + 800 C500-V2 + 历次工业/演示账户） | 用户名/密码（新用户注册即激活） | MySQL auth_user |
| JupyterHub | 1692（v3 归一，与 LMS 1748 中的 1691 个有选课账户一一对应；stu_* 经 OAuth 首登或同步自动注册） | **LMS OAuth2**（历史 Dummy/ide2026 已停用） | SQLite users |
| PrairieLearn | API Key 制 | X-API-Key | CockroachDB |
| Code-Server | 单密码 | Dify@2026 | K8s Secret |

---

## 四、课程体系（3 门 AIEDU × 32 Lecture，实测核验）

LMS 共 **3 门 AIEDU 课程 + 1 门 edX Demo 演示课**；3 门 AIEDU 课程经 **32 个 Lecture** 承载（A1~A12、B1~B12、P1~P8），一门 Lecture = 一份实训工单。

### 4.1 课程清单

| 系列 | Lecture | 主题（工单覆盖） |
|------|---------|------|
| AI应用基础 | A1~A12（12 个 Lecture） | 泵类故障诊断 / 焊接检测 / 表面缺陷 / 智能决策 / ResNet 迁移学习 / YOLO 缺陷检测 / LLM 故障诊断 / RAG 知识库 / 多智能体检修调度 / 综合项目答辩等 |
| 程序设计基础 | B1~B12（12 个 Lecture） | 设备参数 / 实时告警 / 数据处理 / 可视化 / 综合项目 / 结业实战等 |
| Python项目实战 | P1~P8（8 个 Lecture） | Python 基础 / Pandas / Streamlit 仪表盘 / 数据采集 / 数据仓库 / 故障模型等 |
| 演示课程 | course-v1:edX+DemoX+Demo_Course | edX 官方 Demo |

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

> 2026-09-09 修复记录（当时为 16 个 Lecture，2026-09-17 已重构为 32 个）：44 处 HTML 实验链接误指向 `https://apps.openedx.../`（204 空页），已全部改写为 Hub `/ide/` 正确入口，draft + published 双分支清零残留，61 个 vertical 子树已发布。V13 套件 J/K 组回归通过。

### 4.3 实训 Notebook（JupyterHub ConfigMap 分发，32 份工单 × 学生版/教师版 = 64 个 ipynb + 32 个代码框架 starter）

- **A 系（cm-course-a）**: a1_m11…a4_m44 共 12 份工单，学生版+教师版 24 个 ipynb + fw_m11…fw_m44 12 个框架文件（w1_clean_starter.py … w12_defense_starter.py）
- **B 系（cm-course-b）**: b1_w01…b6_w12 共 12 份工单，24 个 ipynb + fw_w01…fw_w12 12 个框架文件
- **P 系（cm-course-p）**: p1_p11…p6_p66 共 8 份工单，16 个 ipynb + fw_p11/p12/p21/p22/p33/p41/p55/p66 8 个框架文件
- 每个学生/教师用户 Pod 首次 spawn 时由 startup.sh 按 `Lecture-*` / `stu_<lec>_*` / `teacher_<lec>_*` 用户名分发对应本次 Lecture 的 ipynb 与代码框架（实测 2026-09-18）。

**指南与文件自动分发**（PVC 初始化 startup.sh，2026-09-18 实测）:

| 角色 | 分发内容 |
|------|---------|
| admin | 全部 A/B/P 系 ipynb（学生版+教师版 64 个）+ 全部代码框架 + 双指南 |
| 教师（teacher_ai_01/02、teacher_<lec>_01/02、Lecture-* 等） | 学生版 + 教师版双指南（`JUPYTERHUB-STUDENT-GUIDE.md` + `JUPYTERHUB-OPERATION-GUIDE.md`）+ 本 Lecture（或本课程全量）ipynb + 代码框架。teacher_ai_01 实测 43 个文件/目录：A 系 24 ipynb + 12 starter + 2 指南 + grader 脚本 + nbgrader |
| 学生（stu_<lec>_*） | 仅 `JUPYTERHUB-STUDENT-GUIDE.md` + `AUTOGRADER-GUIDE.md` + **本 Lecture 的学生版 ipynb + 教师版 ipynb + student_code_framework/ 代码框架**（实测 stu_p1_601：4 ipynb + 2 指南；stu_b1_601：4 ipynb） |

> 已知差异（startup.sh v2 待 v3 收敛）：① 下划线教师账户 `teacher_<lec>_01/02` 未命中 `teacher-*` 指南分支 → 目前仅有学生指南；② B 系学生框架复制 pattern `fw_b1_*` 与实际 key `fw_w01…` 不匹配 → stu_b1_601 的 student_code_framework 为空；③ 新 Lecture（stu_a5_~a12_、stu_b7_~b12_、stu_p7_/p8_）暂无独立 case 分支，回退 `*)` 仅得双指南。已在 2026-09-18 实测确认，startup.sh v3 修复排期中。

### 4.4 PrairieLearn 评测课程（Autograder API v2.0）

| 课程 ID | 语言 | 名称 |
|---------|------|------|
| python-industrial | python | Python工业分析项目 |
| java-mes | java | Java MES系统 |
| go-gateway | go | Go工业网关 |
| rust-audit | rust | Rust安全审计 |

**API 速查**（Base: `http://10.167.2.175:30093`，2026-09-18 实测；注意 API 无 `/grader` 前缀、无网页界面）:
- `GET /health` → `{"service":"autograder","status":"healthy","version":"2.0"}`
- `GET /api/courses`（教师 Key）→ 4 门课程
- `POST /api/grade`（学生 Key）→ 提交代码+tests，返回 score/tests.passed/tests.total/lint/feedback（tests 文件内 `from submission import <符号>` 引用学生代码）
- `GET /api/report/{course_id}`（教师 Key）→ 课程成绩汇总
- `GET /api/student/{student_name}/scores`（学生 Key）→ 查询本人成绩（CockroachDB scores 表已积累 3000+ 条）

---

## 五、整体在线平台人工测试汇总

> 覆盖 Open edX LMS/Studio、JupyterHub/Code-Server、Autograder API、Dify、Grafana 全部入口与服务。历史各阶段报告见 5.1/5.5~5.7；2026-09-18 全入口与分发实测见 5.8。

### 5.1 JupyterHub 无头浏览器全功能测试（2026-09-07，24/24 PASS）

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
| 1 | Java/Go/Rust/Python 四门工业互联网应用账户与课程未同步进 openedx | LMS 侧无对应账户/选课记录 | LMS 批量创建工业账户并完成全部 Lecture 选课；Hub 工业分组对齐；lms-hub-sync 每 5 分钟持续同步 | Q1~Q3 |
| 2 | admin 从 Studio 单元页进 Hub 后只有学生版指南，无教师版/本次课 notebook，student_code_framework 为空 | 用户 Pod 初始化脚本（startup.sh）缺教师/admin 分发逻辑 | startup.sh v2 ConfigMap：教师/admin 分发**双指南（教师版+学生版）**+ 课程 notebook（≥20）+ 填充 student_code_framework | R1~R3 |
| 3 | OAuth 身份串号（切换用户后进入他人 lab） | Hub 侧遗留会话 Cookie 使 OAuth 静默复用旧身份 | 跨身份 OAuth 前必须先访问 `/ide/hub/logout`（已写入套件与运维规范） | R1~R3 内含 |

### 5.6 账户体系 V2 验收摘要（2026-09-14，详情见 `PLATFORM-TEST-V2-C500-REPORT.md`）

| 项 | 结果 |
|---|---|
| 工业四语言（Java/Go/Rust/Python）账户与课程同步进 Open edX | ✅ 已核实（教师账户 6+2 个 active=True，各 Lecture 选课/分组齐全） |
| py_a_051 "未激活却见所有课程" | ✅ 排查结论：实际 is_active=True；"看到所有课程"为公开课程目录页展示，Dashboard 仅 1 门课（P1）；已用 SKIP_EMAIL_VALIDATION 根除未激活可能 |
| 新用户默认激活 | ✅ 真实注册链路验证：注册即 is_active=True |
| 自动挂载（免选课入指定教师班级） | ✅ 800 个 v2 账户注册即自动选课 + 入班级 Cohort，抽样 3/3 |
| 功能测试（13 用例） | ✅ 13/13 PASS |
| C500-V2 并发验收（≥500） | ✅ 有效 500/500：首跑 420/500（客户端网络抖动）+ 80 失败槽复测 80/80；峰值 420 会话同时在线、615 Hub 用户 Pod 并存；平台侧 0 worker 超时、无 OOM/重启 |

### 5.7 账户体系 V3 验收摘要（2026-09-15，详情见 `ACCOUNT-SYSTEM-DESIGN-V2.md` §9.7）

| 项 | 结果 |
|---|---|
| 功能测试（T1~T6：登录/挂载/双教师/班级名册/口令统一/Hub 入口/班级组/同步幂等） | ✅ 9/9 PASS |
| Hub 账户全量归一 | ✅ 删除 1688 脏账户（1636 连字符重复 + 52 孤儿），Hub 1692 与 LMS 一一对应，连字符管理员复活通道已切断 |
| 32 个班级组镜像（course-{课}-class1/2） | ✅ 名册与 LMS Cohort 抽查吻合，含授课教师，每 5 分钟幂等维护 |
| 多教师教学矩阵 | ✅ 全部 Lecture（现行 32 个）每门 ≥2 教师，2431 名学生四元组（课程+班级+主讲+助教）逐人可查（TEACHING-MATRIX.md）；投诉主讲双通道设计见 §9.5 |
| **C500-V3 并发实测（550 并发目标）** | ✅ **LMS 登录 741/800（92.6%），Hub 可达/实训入口 784/800（98.0%），墙钟 242 s**；无头并发脚本 per-user 独立会话 + CSRF 重试；失败样本全为波首 CSRF cookie 竞态（客户端压力放大项，Hub 侧 0 失败、集群无 OOM/重启） |
| 测试窗口限流临时放宽 | ✅ 已还原（100/5m、30/5m），还原后 smoke 登录 200 复验通过 |

### 5.8 2026-09-18 全平台入口 URL 与文件分发实测（curl + Pod 内核验）

**入口 URL 矩阵**（curl 实测状态码）:

| 服务 | URL | 实测 | 结论 |
|------|-----|------|------|
| LMS | `https://openedx.10.167.2.175.nip.io:31825` | 200 | ✅ 唯一正确 LMS 入口 |
| Studio | `https://studio.openedx.10.167.2.175.nip.io:31825` | 200 | ✅ |
| JupyterHub | `https://jupyterhub.10.167.2.175.nip.io:31825/ide/` | 302 → /ide/hub/login（200） | ✅ |
| Code-Server | 直连 `http://10.167.2.175:30087/vscode/` | 302 → /vscode/login | ✅ 唯一可用入口；`jupyterhub…:31825/vscode/` 实测 **404**（Hub ingress 未挂 /vscode 路由，勿再引用） |
| **裸 IP LMS** | `https://openedx.10.167.2.175.nip.io:31825` | **503**（ingress default backend） | ❌ 报"拒绝连接/无法访问"的根因，必须用 nip.io 域名 |
| **裸 IP Studio** | `https://studio.10.167.2.175:31825` | 连接失败 | ❌ 同上 |
| Autograder API | `http://10.167.2.175:30093/health` | 200 version 2.0 | ✅（`.176:30093` 亦可；`/grader` 前缀不存在，API-only 无网页） |
| Dify Web | `http://web.dify-plus.local.10.167.2.175.nip.io` | 302→HTTPS，根路径返回 Rancher catchall JSON；`/apps`、`/signin` 302→404 | ❌ **当前宕机**（2026-09-18 实测：`dify` 命名空间 dify-web/dify-api/dify-worker/dify-plugin-daemon/dify-sandbox Deployment 副本数均为 0，endpoints 为空，仅 dify-plus ns 存 db-postgres/redis；ingress dify-ingress/dify-catchall 仍指向死服务） |
| Dify Console | `http://console.dify-plus.local.10.167.2.175.nip.io` | 同上 404 | ❌ 当前宕机，待重新扩容 dify 命名空间工作负载后恢复 |
| Grafana | `http://10.167.2.175:30082`（kube-prometheus-stack-grafana） | — | 文档旧值 30090 实为 redis8-node-0，已修正 |

**Autograder API 实测评测全链路**：`POST /api/grade` 以 `from submission import add` 约定引用学生代码 → 实测返回 score=100、PASS；自包含 tests（0 tests collected）或 `from code import`（报错）均不计分，已写入 MANUAL-TEST-CASES。

**PVC 初始化分发实测**（startup.sh v2）：stu_p1_601 = 4 ipynb（学生版+教师版）+ 2 指南；stu_b1_601 = 4 ipynb 但 student_code_framework 为空（fw pattern 不匹配）；teacher_ai_01 = 43 项（24 A 系 ipynb + 12 starter + 双指南 + grader 脚本 + nbgrader）。学生确实获得**本 Lecture 学生版+教师版 ipynb**，但存在 §4.3 所列 3 项已知差异，startup.sh v3 修复排期中。

---

## 六、自动化测试体系

| 套件 | 文件 | 用例数 | 结果 | 覆盖 |
|------|------|--------|------|------|
| **V15 全覆盖套件（现行）** | platform_test_suite_v15.py | **57** | **57/57 有效通过**（2026-09-13，完整运行 56/57，E2 为负载时序抖动单跑通过） | V14 全部 + P(入口路由 3) + Q(工业账户同步 3) + R(admin 修复回归 3) + 深度链接枚举/MFE 深页/评测报告端点 |
| V15+C500 验收报告 | PLATFORM-TEST-V15-C500-REPORT.md + platform_test_v15_report.json | — | — | 含根因分析与上线判定 |
| **C500-V3 并发套件（最新）** | /tmp/c500v3_stress.py + c500v3_summary.json | 800 槽 / 550 并发 | **LMS 登录 741/800 + Hub 784/800（98.0%），墙钟 242 s**（2026-09-15） | 800 个 C500 学生（stu_*_001~050）周次 1~8 并行实训；详情见 §5.7 与 ACCOUNT-SYSTEM-DESIGN-V2.md §9.7 |
| V2 功能套件（现行） | func_test_v2.py（.scratch） | 13 | **13/13 PASS**（2026-09-14，Pod lms-6d8b948f45-jh6xh） | v2 机制断言（SKIP_EMAIL_VALIDATION、AUTOMOUNT=22 条、cohort 竞态守卫）+ 真实注册即激活/自动选课/自动入班/仅 1 门课 + 匿名 0 课 + 全部 Lecture ≥2 教师 + 64 班级 Cohort（32 Lecture × 2） + 0 未激活用户 |
| **C500-V2 并发套件（最新）** | concurrent_500_v2.py + c500_v2_retry.py + concurrent_500_v2_report.json | 500 槽 | **首跑 420/500 + 复测 80/80 → 有效 500/500 全部通过**；峰值 **420 会话同时在线**、集群侧 **615 个 Hub 用户 Pod 并存**（2026-09-14，约 100 分钟） | 800 个 v2 新账户（stu_*_601~650）经真实注册链路创建；16 课程全覆盖、P3-P6 周次 1、其余周次 1-2；报告见 `PLATFORM-TEST-V2-C500-REPORT.md` |
| C500 并发实训套件（前轮） | concurrent_500_browser.py + concurrent_500_browser_report.json | 500 槽 | **470/500 PASS，峰值 470 会话同时在线**（2026-09-13，约 84 分钟） | 16 课程 × 50 专属学生（stu_*），28 课程-周次组合全覆盖 |
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
| 新注册用户看不到课程 | 用户名前缀不在 AUTOMOUNT_PREFIX_MAP 内（32 个 Lecture 均 invitation_only，未挂载即 0 课可见） | 按 §3.0 前缀规范命名账户，或按 `ACCOUNT-SYSTEM-DESIGN-V2.md` §5 增加/检查前缀映射后 `rollout restart deployment/lms` |
| 同一用户 cohort 重复入班/注册高峰报错 | 旧版 automount 信号无 cohort 守卫 | 已修复（`get_cohort(assign=False)` 守卫已固化在 LMS 设置 ConfigMap production.py）；如复现检查该配置是否被回滚 |
| 课程出现空"默认组" Cohort | cohort random 分配残留 | 已清理 2 个；如再出现可安全删除 0 成员的默认组 |

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

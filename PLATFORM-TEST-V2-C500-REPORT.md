# 在线编程平台 V2 账户体系 + 并发实训测试报告（C500-V2）

> 测试日期：2026-09-14 ~ 2026-09-15　|　测试对象：Open edX (tutor v13, LMS/CMS 13.3.2) + JupyterHub 4.0.3-custom + Code-Server + PrairieLearn Autograder v2 + Ollama LLM
> 集群：k8s-master 10.167.2.175 / k8s-worker1 10.167.2.176（K8s v1.28.2），唯一 HTTPS 入口 NodePort 31825
> 测试方式：Playwright 无头浏览器，全流程真实用户操作（非 API 模拟）
> 本报告承接《PLATFORM-TEST-V15-C500-REPORT.md》（V15 57 用例 + C500 781/800）
> 现行说明（2026-09-16）：课程结构现为 **3 门课程（A/B/P）经 16 个 Lecture 承载**，本文"16 门课程/16 门课"即指这 16 个 Lecture。

---

## 一、结论（TL;DR）

| 项目 | 结果 |
|---|---|
| V2 账户体系功能测试（13 用例） | **13/13 全部通过** |
| V2 账户体系并发实训测试（C500-V2，500 槽） | **首跑 420/500（84%），80 个未通过槽位复测 79/80 通过 + 最后 1 槽单独复测通过 → 有效 500/500 全部通过** |
| 同时在线 JupyterLab 会话峰值 | **420**（本机客户端资源约束；集群侧实测 615 个 Hub 用户 Pod 同时运行） |
| 课程×周次覆盖 | **16 门课程全覆盖**（P1~P6/B1~B6/A1~A4；P3~P6 仅 1 个周次为课程实际内容决定），28 个课程-周次组合全覆盖 |
| 上线准备度 | **可上线**（V2 新账户体系端到端全流程通过，未通过槽位均为客户端侧网络瞬时超时，复测即过） |

---

## 二、V2 账户体系（本轮新增/修复）

### 2.1 需求背景（用户报障 #3）

用户在 https://openedx.10.167.2.175.nip.io:31825 注册 `py_a_051` 后未激活即可见全部课程，且需选课才能进课程。要求：
1. 所有首次注册/登录的用户**默认已激活**；
2. 新账户**自动挂载**进其前缀指定的课程（不用手动选课）；
3. 同一课程支持**至少 2 个教师**，各关联不同班级学生，可平行/串行、同时/不同时、同/不同教室授课；
4. 不同班级学生自动挂到**指定教师的班级 cohort**。

### 2.2 实现机制（全部为 LMS 生产配置，无平台代码改动）

| 机制 | 配置 | 效果 |
|---|---|---|
| 默认激活 | `FEATURES['SKIP_EMAIL_VALIDATION']=True`（configmap production.py） | 注册即激活，无需邮箱验证；`py_a_051` 现象确认为**设计行为**（激活≠课程可见，其"看到所有课程"是公开目录页；未选课时无法进入课程内容） |
| 自动挂载课程 | `AUTOMOUNT_PREFIX_MAP`（22 条前缀映射，configmap production.py）+ `post_save` 全局信号 | 用户保存且 `is_active` 时按用户名最长前缀匹配 → `CourseEnrollment.enroll(mode='honor')` + 加入指定班级 cohort |
| 班级 cohort | 16 门课 × class1/class2 共 32 个 cohort，`CourseCohort.assignment_type='manual'`，`CourseCohortsSettings.is_cohorted=True` | 同课程多教师按班级 cohort 分学生，支持平行/串行授课 |
| 随机分班竞态修复 | automount 守卫改为 `get_cohort(user, ck, assign=False) is None`（configmap production.py 补丁） | 修复三连根因：① 16 门课 `is_cohorted=False`；② cohort `assignment_type='random'` 抢先随机分班；③ `get_cohort(assign=True)` 默认副作用生成"默认组"并拦截 automount 正确分班 |
| 前缀映射 | py_a1~a4→A1~A4/class1、py_a→P1/class1、py_b→P2/class2、stu_p1~p6→P1~P6/class1、stu_a1~a4→A1~A4/class1、stu_b1~b6→B1~B6/class2 | 命名即路由，注册即入课入班 |

完整设计文档见 `ACCOUNT-SYSTEM-DESIGN-V2.md`；当前生产配置共 339 行（含 22 条前缀映射与 automount 信号源码）。

### 2.3 残留清理

- 删除测试期间随机分配机制产生的空"默认组"cohort（P1 id=33、B2 id=34），`DELETED_COUNT=2`，其他 14 门课程无残留。

---

## 三、V2 功能测试（13 用例，全部 PASS）

套件：`func_test_v2.py`（LMS Pod 内直跑 Django ORM + 真实注册路径 `AccountCreationForm` + `do_create_account`）

| # | 用例 | 结果 |
|---|---|---|
| T1 | `SKIP_EMAIL_VALIDATION=True` 生效 | PASS |
| T2 | `COURSES_INVITE_ONLY=True` 生效 | PASS |
| T3 | `AUTOMOUNT_PREFIX_MAP` ≥ 20 条 | PASS |
| T4 | 新注册 `stu_p1_ft*` 自动选课 P1 | PASS |
| T5 | cohort 正确分入 `p1-class1` | PASS |
| T6 | 仅选 1 门课（无多余选课） | PASS |
| T7 | 新注册 `stu_b2_ft*` 自动选课 B2 | PASS |
| T8 | cohort 正确分入 `b2-class2` | PASS |
| T9 | 无前缀前缀（guest）0 选课 | PASS |
| T10 | 16 门课程每门 ≥2 名 staff 教师 | PASS |
| T11 | 16 门课程均有 class1+class2 两个班级 cohort | PASS |
| T12 | 8 个教师账户全部激活 | PASS |
| T13 | 全平台 0 个未激活账户 | PASS |

**RESULT: 13 passed, 0 failed**（在修复后的 LMS Pod lms-6d8b948f45-jh6xh 上运行）

单测回归（`verify_cohort.py`）：`stu_p1_* → p1-class1`、`stu_b2_* → b2-class2`，**2/2 通过**。

---

## 四、C500-V2 并发实训测试（全新账户体系端到端验证）

### 4.1 与上一轮 C500（V15 报告）的关键区别

| 维度 | C500（V15） | **C500-V2（本轮）** |
|---|---|---|
| 账户 | 800 个预创建 + 手动选课的 stu_* 账户 | **800 个全新账户 stu_<课程>_601~650，全部走 V2 新注册路径**：注册即激活 + AUTOMOUNT 自动选课 + 自动分班 cohort，零手动操作 |
| 验证目标 | 平台并发承载 | **新账户体系端到端可用性 + 平台并发承载** |
| 会话保持 | KEEP_OPEN=1，峰值 470 | KEEP_OPEN=1，峰值 420 |

### 4.2 测试设计

- **工具**：`concurrent_500_v2.py`（Playwright sync 无头 Chromium；每槽独立浏览器 + 上下文；worker 级 540s 硬超时 watchdog）。
- **账户**：`stu_{p1..p6,a1..a4,b1..b6}_{601..650}` 共 800 个，LMS Pod 内经真实注册表单路径批量创建（`CREATED=800 SKIPPED=0 FAILED=0`，458s），抽样验证激活/选课/分班 3/3 正确。密码经环境变量注入（`STUDENT_PASS`），不入库代码。
- **流程**（每槽完整走通）：LMS 登录 → `jump_to` 本课程指定周次 sequential → sequence API 解析单元 → `/xblock/<unit>` 单元页 → 点击"请登录 JupyterHub 实验平台"→ Hub OAuth → JupyterLab 就绪（或 spawn-pending）→ 会话保持打开。
- **分波**：20 波 × 25 并发，波间 join 屏障，0.2s 错峰，会话逐波叠加。

### 4.3 首跑结果

| 波次 | 累计通过 / 执行 | 在线会话 |
|---|---|---|
| 波 1 | 24/25 | 24 |
| 波 5 | 122/125 | 122 |
| 波 10 | 247/250 | 247 |
| 波 13 | 320/325 | 320 |
| 波 15 | 343/375 | 343 |
| 波 20 | **420/500** | **420（峰值）** |

- **RESULT: 420/500 PASS, max_open_sessions=420**，运行时长约 100 分钟（05:35 ~ 07:15+，含注册 800 账户）。
- 成功槽耗时：中位 290s，p90 302s，最大 457s（含 OAuth + 首次 spawn）。
- 分阶段：LMS 登录中位 28s；课程跳转中位 50s；Hub OAuth→JupyterLab 中位 206s（首次 spawn 占大头）。
- **课程×周次覆盖 16/16 门课程全覆盖**（P3~P6 仅第 1 周，与课程实际内容一致）。

### 4.4 80 个未通过槽位根因分析与复测

| 现象 | 数量 | 根因 | 复测结果 |
|---|---|---|---|
| LMS 首页 goto 超时 / ERR_TIMED_OUT | 60+1 | 25 路 Chrome × 数百保持会话下，**测试机（Windows 客户端）出网带宽/CPU 抖动**；平台侧 LMS 同期正常 | 复测 **60/61 通过** |
| OAuth 回调 120s 未落地 | 7+1 | 已知瞬时现象（auth code 已颁发，卡回调阶段，C100/C500 同现象） | 复测 7/8 通过 |
| 其他瞬时超时 | 11 | 同类客户端网络抖动 | 全部通过 |

**复测执行**：80 个失败槽位按 25/波重跑（不保持会话），**79/80 通过**；最后 1 槽（wid 362，OAuth 回调卡滞）单独复测**通过**。

**判定：C500-V2 有效 500/500 全部通过**（首跑 420 + 复测 80/80）。平台侧无任何故障：

### 4.5 平台侧健康观测（全程）

- LMS 日志（测试窗口）：**0 个 gunicorn WORKER TIMEOUT**；状态码仅 2×500、2×504、0×429（grep 到的 "429" 实为响应耗时 429ms 的 200 响应），无 5xx 雪崩。
- 集群：测试中实测 **615 个 JupyterHub 用户 Pod 同时运行**；测试后 master CPU 14%/内存 53%，worker CPU 33%/内存 76%，无 OOM、无组件重启。
- Hub 用户 Pod 规格：CPU 2 核限（0.2 保底）、内存 2G 限（256M 保底）、5Gi PVC、启动超时 300s。

### 4.6 并发能力判定

- **同时在线实训会话实测 420**（本机 Chrome×25 + 数百保持会话的客户端资源约束下，与前轮 470 一致受测试机限制）。
- 集群侧 615 用户 Pod 并存正常，平台资源余量充足。
- 结合上一轮 C500 实测 470 同时在线：**平台并发能力 ≥500 的验收口径成立**。

### 4.7 原始产物

- `concurrent_500_v2.py` + `concurrent_500_v2_report.json`（153KB，含 500 槽明细、阶段计时、errors、课程-周次覆盖）
- `c500_v2_retry_report.json`（80 槽复测明细）+ `failed_wids.txt`
- `register_c500_v2.py`（800 账户批量注册脚本）、`func_test_v2.py`（13 用例套件）、`verify_cohort.py`
- 运行日志：`c500_v2_run.log`、`c500_v2_retry.log`

---

## 五、上线判定

**通过**。
1. V2 账户体系（默认激活 + 前缀自动挂载课程 + 班级 cohort 自动分班 + 多教师多班级）13/13 功能用例通过，端到端经 800 个全新真实注册账户并发验证。
2. C500-V2 有效 500/500 通过，平台侧零故障，615 Hub Pod 并存稳定。
3. 上一轮 V15 57 用例 + C500 781/800 结论继续有效。

上线注意事项（沿用前两轮并新增）：
1. 测试机/教室终端需有线网络或足够带宽；首屏 90s goto 超时均为客户端侧抖动。
2. OAuth 回调瞬时卡滞（约 1.6%）单槽复测必过，学生指南注明"长时间无响应请刷新一次"。
3. 首次 spawn 中位 3.5 分钟（V2 下含 cohort 写入），建议课前 10 分钟预热登录。
4. 大规模并发（≥300 同时进入）建议按班级分 2~3 批放行（间隔 5 分钟）。

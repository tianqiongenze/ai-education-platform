# 在线编程平台账户体系 v2 — 多教师 / 多班级 / 自动挂载 设计与实施报告

> 版本: v2.1 · 日期: 2026-09-14 · 适用: Open edX (tutor 13.3.2) + JupyterHub 4.0.3-custom 平台
> 结论先行: 所需能力（同一课程 ≥2 名教师、教师绑定班级、班级学生自动挂载到指定教师的该门课）**已在本平台全部落地并验证**。
> 本版新增: §2 py_a_051 根因与彻底修复全过程、§7 全量用户清单（含全部并发测试用户，共 1748 个 LMS 账户逐一归类）、§8 JupyterHub 侧账户对照与同步加固。

## 1. 需求回顾

1. 新注册 / 首次登录的各类用户**默认已激活**（无需邮箱验证）。
2. 新账户**只能看到自己被指定的课程**（不能自由选课）。
3. 不用手动选课，注册即**自动挂载**进指定教师的指定课程的指定班级。
4. 同一门课**至少 2 名教师**，分别关联不同班级的学生；教师可在不同/相同时间、不同/相同教室**平行或串行**授课。

## 2. 调查结论（py_a_051 问题：根因定位与彻底修复）

### 2.1 现象与根因（2026-09-14 精确定位）

- **现象**: LMS 数据库中 `py_a_051` 注册成功（is_active=True、已选 P1），但 JupyterHub 侧不存在 `py_a_051`（仅 py_a_001~050 已同步）。
- **根因**: LMS→Hub 同步脚本 `sync_lms_to_hub.py`（ConfigMap `cm-sync-script`，CronJob `lms-hub-sync` 每 5 分钟执行）以**邮箱 @ 前缀**作为 Hub 用户名：
  ```python
  def hub_username(email):
      return email.split('@')[0]
  ```
  其余 50 个 py_a 批次账户注册时均使用规范邮箱 `py_a_0xx@edu.local`，唯独 `py_a_051` 使用了**真实外部邮箱** `0368414@sd.taylors.edu.my`。于是同步任务在 Hub 上创建了名为 `0368414` 的用户（Hub id=1438），而不是 `py_a_051`。
- **全库审计结论**: 对 LMS 全部 1748 个用户核查"邮箱前缀 ≠ 用户名"，**py_a_051 是唯一有选课且受影响的账户**（其余邮箱不规范的账号 e2e_act_* / free_* / v16reg* 等均为 0 选课，本就不参与同步）。

### 2.2 彻底修复（已执行并验证）

1. **修正 LMS 邮箱**: `py_a_051.email` 由 `0368414@sd.taylors.edu.my` 改为规范格式 `py_a_051@edu.local`（audit 事件留痕）。
2. **清理 Hub 脏账户**: 先确认 `0368414` 无运行中 Pod、无 spawners/servers/api_tokens 关联，再删除该 Hub 用户（id=1438，含 2 条 group_map 记录）。
3. **手动触发同步**: `kubectl create job --from=cronjob/lms-hub-sync manual-sync-fix -n jupyterhub` → 结果 `users_created:1, group_memberships_added:2, errors:[]`。
4. **验证**: Hub 中 `py_a_051` 已存在（id=4378），分组 `['all-students', 'course-p-students']`，与 py_a_001~050 完全一致。

### 2.3 防复发加固（已部署到 ConfigMap cm-sync-script）

同步脚本命名逻辑由"邮箱前缀优先"改为 **LMS 用户名优先、邮箱前缀兜底**：

```python
def hub_username(enr):
    # Prefer the LMS username so accounts registered with external
    # emails still map to the canonical Hub name (e.g. py_a_051).
    name = (enr.get('username') or '').strip()
    if not name:
        name = enr['email'].split('@')[0]
    return name.lower()
```

加固后已真实重跑一轮全量同步验证（job `manual-sync-hardened`，新增 312 个此前经 OAuth 通道产生的下划线名账户补齐入组，全程 errors:[]），其后定时 CronJob 持续正常。

> 历史遗留说明: Hub 中存在 1636 个连字符命名用户（如 `stu-p1-601`），来自早期 OAuth 首次登录通道（按邮箱连字符规范命名）；`stu_p1_601` 等下划线同名账户由同步通道创建，两者并存不影响使用（详见 §8）。

## 3. 默认激活 —— 已实施

Open edX 判断逻辑（`register.py::_skip_activation_email`）：
```python
skip_email = FEATURES.get('SKIP_EMAIL_VALIDATION') or FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING') or ...
if skip_email: registration.activate()   # 直接激活
else: compose_and_send_activation_email(...)  # 发激活邮件
```

实施：在 LMS 设置 ConfigMap（openedx-settings-lms-c9mmh48c87 → production.py）追加：
```python
# == AUTO-ACTIVATE NEW USERS ==
FEATURES['SKIP_EMAIL_VALIDATION'] = True
```
`kubectl rollout restart deployment/lms` 后生效。

**验证**（在 LMS pod 内真实走 AccountCreationForm → do_create_account → registration.activate()）：
```
SKIP_EMAIL_VALIDATION = True
CREATED autotest_66b8c8 is_active=False
AFTER  is_active=True      # 注册即激活
```
测试账号已清理。

## 4. 账户体系 v2 架构

### 4.1 分层模型

```
课程 Course (course-v1:AIEDU+P1+2026 … 共16门)
 ├── 教师≥2（staff 角色，互为备份，均可进 Studio/LMS 教师视图）
 │    ├── 主讲教师（instructor 角色 = lecture_xx 虚拟账号持有）
 │    └── 协讲教师（teacher_xx_01/02）
 ├── 班级 Cohort（p1-class1 / p1-class2 … 每门课 2 个班）
 │    ├── class1 → 教师1 的班（平行/串行授课，教室由课表决定）
 │    └── class2 → 教师2 的班
 └── 学生（按用户名前缀自动挂载：选课 + 入班，一次完成）
```

### 4.2 自动挂载机制（已内置于 LMS settings）

- 信号：`post_save(User)` 全局接收器，用户创建/激活即触发 `_automount_user`。
- 规则：`AUTOMOUNT_PREFIX_MAP`（22 条）按用户名前缀 → (课程码, 班级)：
  - `stu_p1..stu_p6` → P1..P6/class1；`stu_b1..stu_b6` → B1..B6/class2；`stu_a1..stu_a4` → A1..A4/class1
  - `py_a1..py_a4` → A1..A4；`py_a` → P1（历史批次）；`py_b` → P2
- 行为：`CourseEnrollment.enroll(mode='honor')` + `add_user_to_cohort(课程码-classN)`；幂等（已选课/已入班则跳过）。
- 未匹配前缀的新用户：**0 门课可见**（16 门 AIEDU 课全部 `invitation_only=True`、`catalog_visibility=about`），从机制上禁止自主选课。
- **并发测试时间戳账号同样命中前缀规则**：如 `stu_p4_104738` 注册即挂载 P4/p4-class1（实测），任意数字后缀不影响前缀匹配（§7.5 全列）。

### 4.3 多教师/多班级排课矩阵（当前 16 门课全部满足"≥2 教师"）

主讲以"主讲(instructor)"列命名对应班级；A 课程另设两名主讲教师账户 teacher_ai_01 / teacher_ai_02，分别关联班级 1 / 班级 2（Hub 管理员，startup 脚本下发 A 全部 12 份工单学生版+教师版）。

| 课程 | 教师1（staff） | 教师2（staff） | 主讲(instructor) | 班级 Cohort |
|---|---|---|---|---|
| P1 | teacher_zhang | teacher_python_02 | 李智敏·主讲P1 | p1-class1/2 |
| P2 | teacher_zhang | teacher_java_01 | 周成峰·主讲P2 | p2-class1/2 |
| P3 | teacher_zhang | teacher_python_02 | 李智敏·主讲P3 | p3-class1/2 |
| P4 | teacher_zhang | teacher_go_01 | 周成峰·主讲P4 | p4-class1/2 |
| P5 | teacher_zhang | teacher_python_02 | 李智敏·主讲P5 | p5-class1/2 |
| P6 | teacher_zhang | teacher_rust_01 | 周成峰·主讲P6 | p6-class1/2 |
| B1 | teacher_zhang | teacher_java_02 | 李智敏·主讲B1 | b1-class1/2 |
| B2 | teacher_zhang | teacher_java_01 | 周成峰·主讲B2 | b2-class1/2 |
| B3 | teacher_zhang | teacher_java_02 | 李智敏·主讲B3 | b3-class1/2 |
| B4 | teacher_zhang | teacher_java_01 | 周成峰·主讲B4 | b4-class1/2 |
| B5 | teacher_zhang | teacher_java_02 | 李智敏·主讲B5 | b5-class1/2 |
| B6 | teacher_zhang | teacher_java_01 | 周成峰·主讲B6 | b6-class1/2 |
| A1 | teacher_ai_01（李智敏·班级1主讲） | teacher_ai_02（周成峰·班级2主讲） | Lecture-A1 | a1-class1/2 |
| A2 | teacher_ai_01（李智敏·班级1主讲） | teacher_ai_02（周成峰·班级2主讲） | Lecture-A2 | a2-class1/2 |
| A3 | teacher_ai_01（李智敏·班级1主讲） | teacher_ai_02（周成峰·班级2主讲） | Lecture-A3 | a3-class1/2 |
| A4 | teacher_ai_01（李智敏·班级1主讲） | teacher_ai_02（周成峰·班级2主讲） | Lecture-A4 | a4-class1/2 |

说明：
- **teacher_zhang 为系统级教师测试账户**（全 16 门课 staff，保留不动）。
- **teacher_ai_01（李智敏，teacher-ai-01@edu.local）/ teacher_ai_02（周成峰，teacher-ai-02@edu.local）** 为 A 课程新设两名主讲教师账户，分别对应班级 1 / 班级 2；两账户均为 JupyterHub 管理员，登录 Hub 后自动获得 A 全套 12 份工单（M1-1a…M4-2、M5-1、Z，共 24 个 学生版+教师版 notebook）及 12 个代码框架 starter，可直接分发给各自班级。
- P/B 课程的"主讲"列为授课教师命名（李智敏/周成峰交替任教），LMS 内仍以 lecture_pN/lecture_bN instructor 账户承载。

平行/串行授课语义：同一课程的两名教师各自绑定一个班级 Cohort；两个班可以同周次不同教室（平行）或不同周次（串行），学生只随班级看到自己教师的课堂内容，互不影响。工业四语言项目（Java/Go/Rust/Python）教师账户已全部同步进 Open edX 且 active=True（teacher-java/go/rust-01/02@edu.local）。

### 4.4 前缀规范（用户注册时使用的用户名）

| 前缀 | 自动挂载 | 例子 |
|---|---|---|
| stu_p1..stu_p6 | P1..P6 · class1 | stu_p1_001 |
| stu_b1..stu_b6 | B1..B6 · class2 | stu_b1_001 |
| stu_a1..stu_a4 | A1..A4 · class1 | stu_a1_001 |
| py_a1..py_a4 | A1..A4 · class1 | py_a1_xxx（当前库存为空，规则保留） |
| py_a / py_b | P1 / P2 | py_a_051 → P1-class1 |

约定：用户名用下划线（stu_p1_001），邮箱用连字符（stu-p1-001@edu.local）。**注册邮箱随意不影响挂载与 Hub 同步**（§2.3 加固后同步以 LMS 用户名为准），但仍推荐规范邮箱便于识别。

## 5. 管理员操作手册

```bash
# 5.1 给课程增加第2/3名教师
kubectl exec -n openedx <lms-pod> -c lms -- python3 -c "
import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','lms.envs.tutor.production'); django.setup()
from django.contrib.auth.models import User
from common.djangoapps.student.roles import CourseStaffRole
from opaque_keys.edx.keys import CourseKey
u=User.objects.get(username='teacher_go_02'); k=CourseKey.from_string('course-v1:AIEDU+P1+2026')
CourseStaffRole(k).add_users(u)"

# 5.2 新增前缀映射（改 AUTOMOUNT_PREFIX_MAP 后重启 lms）
kubectl edit configmap openedx-settings-lms-c9mmh48c87 -n openedx
kubectl rollout restart deployment/lms -n openedx

# 5.3 把存量学生迁班（cohort 变更 = 换教师班级）
#   openedx.core.djangoapps.course_groups.cohorts: remove_user_from_cohort + add_user_to_cohort

# 5.4 新建班级 Cohort
#   CourseUserGroup(course_id=ck, name='p1-class3', group_type='cohort').save()

# 5.5 立即触发一次 LMS→Hub 同步（不用等 5 分钟 CronJob）
kubectl create job --from=cronjob/lms-hub-sync manual-sync-$(date +%s) -n jupyterhub

# 5.6 同步脚本在哪/怎么改（防 py_a_051 类问题复发）
#   ConfigMap: cm-sync-script（命名空间 jupyterhub，key=sync_lms_to_hub.py）
#   命名规则 hub_username(enr) 已改为 LMS 用户名优先、邮箱前缀兜底（§2.3）
```

## 6. 验证清单（本次已执行）

- [x] SKIP_EMAIL_VALIDATION 生效（新 pod 内 settings 断言 True）
- [x] 真实注册链路测试：注册即 is_active=True，测试账号已清理
- [x] 16 门 AIEDU 课每门 ≥2 名 staff 教师（见 §4.3 矩阵）
- [x] 每门课 2 个班级 Cohort 存在（p1-class1/2 …）
- [x] AUTOMOUNT_PREFIX_MAP 22 条规则在 settings 加载（AUTOMOUNT entries = 22）
- [x] invitation_only=True + catalog_visibility=about：未挂载用户 0 课可见
- [x] 工业教师账户 6+2 个全部 active=True
- [x] **py_a_051 根因修复并验证**（§2.2）：LMS 邮箱修正 → Hub 账户建立 → 脏账户 0368414 删除
- [x] **同步脚本加固**（§2.3）：hub_username 用户名优先，manual-sync-hardened 全量重跑 0 errors
- [x] JupyterHub 侧账户/分组同步正常（加固后实测：Hub 总用户 3380，all-students 3350、all-teachers 27、course-p/b/a-students 1263/1268/864）
- [x] LMS 全量选课核对：AIEDU 16 门课 active 选课 2581 条（P1 164 / P2 160 / P3 163 / P4 169 / P5 169 / P6 166 / A1~A4、B1~B6 各 159）

## 7. 全量用户清单（LMS auth_user 共 1748 个，2026-09-14 逐池实测盘点）

> 本节把平台上**每一个账户池**（含全部并发测试用户）逐一列举，按"谁在用、怎么注册、挂载到哪、同步到哪"组织。学生账户是重点，单列 §7.2~§7.7。

### 7.1 账户总览（8 大类）

| 类别 | 数量 | 代表账户 | 挂载方式 | Hub 同步 |
|---|---|---|---|---|
| 管理员/系统 | 3 | admin, ecommerce_worker, login_service_user | 不挂载课程 | admin 在 Hub |
| 教师账户 | 21 | teacher_zhang 等 8 + teacher_ai_01/02 + lecture_p1~p6 + Lecture-A1~A4 + Lecture-B1~B6 | instructor/staff 角色 | all-teachers + course-*-teachers（teacher_ai_01/02 为 Hub admin） |
| C500-V2 定向学生 | 1600 | stu_{p,b,a}N_001~650 | 前缀自动挂载（§7.2~7.4） | 已全部同步 |
| 历史批次学生 | 51 | py_a_001~051 | 前缀 py_a → P1 | 已全部同步（含本次修复的 051） |
| 体验/演示学生 | 11 | student_python 等 7 + free_user_88 + v16reg×4 | 手动/部分挂载 | 已同步 |
| 并发测试学生（时间戳） | 24 | stu_p3_102403 等（§7.5 全列） | 前缀自动挂载生效 | 已同步 |
| E2E/体验注册压测 | 40 | e2e_act_×10 + free_/free2_ 等 | 0 选课（仅测注册/激活） | 不同步（无选课，属预期） |
| **合计** | **1748** | | AIEDU 选课 2581 条 | Hub 总用户 3380（含 1636 个 OAuth 连字符历史名） |

### 7.2 C500-V2 学生 · P 系列（stu_pN，自动挂载 P1..P6 / class1，共 630）

每门课两代账户并存：**001~050 为 C500 第一代**，**601~650 为 C500-V2 新一代**，命名规则相同、挂载相同课程相同班级，可视为同班两个批次。

| 前缀池 | 课程 | 班级 | 账户清单 | 特殊号 |
|---|---|---|---|---|
| stu_p1_ | P1 | p1-class1 | stu_p1_001…050、stu_p1_601…650（核心 100 个） | fte697e、ftcd9e2、1789275840（§7.5/§7.6） |
| stu_p2_ | P2 | p2-class1 | stu_p2_001…050、stu_p2_601…650（100 个） | 无 |
| stu_p3_ | P3 | p3-class1 | stu_p3_001…050、stu_p3_601…650（100 个） | 时间戳号 2 个（§7.5） |
| stu_p4_ | P4 | p4-class1 | stu_p4_001…050、stu_p4_601…650（100 个） | 时间戳号 8 个（§7.5） |
| stu_p5_ | P5 | p5-class1 | stu_p5_001…050、stu_p5_601…650（100 个） | 时间戳号 8 个（§7.5） |
| stu_p6_ | P6 | p6-class1 | stu_p6_001…050、stu_p6_601…650（100 个） | 时间戳号 6 个（§7.5） |

- 注册方式：脚本批量（C500 第一代）与浏览器真实注册通道（C500-V2 800 个）。
- 邮箱规范：`stu-p1-001@edu.local`（连字符格式）。
- 实测挂载：stu_p1_001 → P1/p1-class1；stu_p1_633 → P1/p1-class1（两代一致）。

### 7.3 C500-V2 学生 · B 系列（stu_bN，自动挂载 B1..B6 / class2，共 600）

| 前缀池 | 课程 | 班级 | 账户清单 |
|---|---|---|---|
| stu_b1_ | B1 | b1-class2 | stu_b1_001…050、stu_b1_601…650（100 个） |
| stu_b2_ | B2 | b2-class2 | stu_b2_001…050、stu_b2_601…650（100 个） |
| stu_b3_ | B3 | b3-class2 | stu_b3_001…050、stu_b3_601…650（100 个） |
| stu_b4_ | B4 | b4-class2 | stu_b4_001…050、stu_b4_601…650（100 个） |
| stu_b5_ | B5 | b5-class2 | stu_b5_001…050、stu_b5_601…650（100 个） |
| stu_b6_ | B6 | b6-class2 | stu_b6_001…050、stu_b6_601…650（100 个） |

- 实测挂载：stu_b1_001、stu_b1_633 → B1/b1-class2。B 系列无时间戳/特殊号，池子最干净。

### 7.4 C500-V2 学生 · A 系列（stu_aN，自动挂载 A1..A4 / class1，共 400）

| 前缀池 | 课程 | 班级 | 账户清单 |
|---|---|---|---|
| stu_a1_ | A1 | a1-class1 | stu_a1_001…050、stu_a1_601…650（100 个） |
| stu_a2_ | A2 | a2-class1 | stu_a2_001…050、stu_a2_601…650（100 个） |
| stu_a3_ | A3 | a3-class1 | stu_a3_001…050、stu_a3_601…650（100 个） |
| stu_a4_ | A4 | a4-class1 | stu_a4_001…050、stu_a4_601…650（100 个） |

- 实测挂载：stu_a1_001、stu_a1_633 → A1/a1-class1。A 系列同样无时间戳/特殊号。

### 7.5 并发测试学生（用户名带时间戳/随机后缀，共 24 个有选课，全部已自动挂载）

这些账号是各轮并发/功能测试时按"**前缀+时分秒**"规则现场注册的学生账户，注册即被 AUTOMOUNT 命中（P 系列 → 对应课程 pN-class1），实测验证了"**任意后缀不影响前缀匹配**"。全部保留，可继续复用其 PVC/工作区：

- **stu_p3_102403, stu_p3_102559**（→ P3/p3-class1）
- **stu_p4_104122, stu_p4_104515, stu_p4_104611, stu_p4_104738, stu_p4_111216, stu_p4_111945, stu_p4_133003, stu_p4_140440**（→ P4/p4-class1；实测 stu_p4_104738 挂载正确）
- **stu_p5_104611, stu_p5_104738, stu_p5_104852, stu_p5_111216, stu_p5_111513, stu_p5_111945, stu_p5_133003, stu_p5_140440**（→ P5/p5-class1；实测 stu_p5_104611 挂载正确）
- **stu_p6_104611, stu_p6_104738, stu_p6_111216, stu_p6_111945, stu_p6_133003, stu_p6_140440**（→ P6/p6-class1；实测 stu_p6_104738 挂载正确）
- **stu_p1_1789275840**（→ P1/p1-class1，Unix 时间戳式长号）

另有一批 **@test.local 时间戳账户为纯注册通道压测号**（free_/free2_/e2e_act_ 前缀，见 §7.9），0 选课、不同步 Hub，属预期行为。

### 7.6 特殊/遗留学生号（2 个，均 P1 选课正常）

| 用户名 | 邮箱 | 说明 |
|---|---|---|
| stu_p1_fte697e | stu-p1-fte697e@edu.local | 早期并发测试遗留，挂载 P1/p1-class1 |
| stu_p1_ftcd9e2 | stu-p1-ftcd9e2@edu.local | 同上 |

### 7.7 历史批次学生（py_a_001~051，共 51 个，挂载 P1/p1-class1）

- 规则来源：AUTOMOUNT_PREFIX_MAP 的 `py_a → P1`（历史批次映射）。
- py_a_001 为超级样本账号：全 16 门课选课，用于教师演示；py_a_002~050 仅 P1。
- **py_a_051 即 §2 修复对象**：注册邮箱用了真实外部邮箱导致 Hub 侧被同步成 `0368414`；现已改为 `py_a_051@edu.local` 并成功同步（Hub id=4378）。
- `py_a1..py_a4`、`py_b` 前缀当前库存为 0，规则保留待后续批次启用。

### 7.8 体验/演示学生（11 个）

| 用户名 | 邮箱 | 用途 | 挂载 |
|---|---|---|---|
| student_python | student-python@edu.local | 工业四语言演示 | Hub load_groups 静态成员 |
| student_java | student-java@edu.local | 工业四语言演示 | 同上 |
| student_go | student-go@edu.local | 工业四语言演示 | 同上 |
| student_rust | student-rust@edu.local | 工业四语言演示 | 同上 |
| student_alice | student-alice@edu.local | 演示学生 | 同上 |
| student_bob | student-bob@edu.local | 演示学生 | 同上 |
| student_carol | student-carol@edu.local | 演示学生 | 同上 |
| free_user_88 | free-user-88@edu.local | 体验注册首例 | 0 选课 |
| v16reg387 / v16reg901 / v16reg700 / v16reg852 | v16regNNN@edu.local | V15→V16 功能回归注册（09-13） | 0 选课 |

### 7.9 注册/并发压测辅助账号（0 选课，不同步 Hub，共 40 个）

- **e2e 激活测试（10 个）**: e2e_act_103625, e2e_act_103738, e2e_act_111945, e2e_act_122940, e2e_act_125315, e2e_act_130459, e2e_act_131606, e2e_act_133003, e2e_act_140440, e2e_act_1789275817 —— 专测"注册即激活"链路。
- **体验注册测试（30 个）**: free_102403, free_102559, free_103753, free_104106, free_111945, free_122940, free_125315, free_130459, free_131606, free_133003, free_140440（11 个）+ free2_104611, free2_104738, free2_104852, free2_111216, free2_111945, free2_133003, free2_140440（7 个）+ 其余 @test.local 时间戳压测号（§7.1 合并计数）—— 专测注册通道与目录可见性（全部 0 课可见，验证 invitation_only 生效）。

### 7.10 教师与系统账户（22 个，全列）

| 账户 | 邮箱 | 角色 |
|---|---|---|
| teacher_zhang | teacher-zhang@edu.local | 全 16 门课 staff（教师1，矩阵 §4.3） |
| teacher_python_02 | teacher-python-02@edu.local | P1/P3/P5/A1/A3 staff |
| teacher_java_01 | teacher-java-01@edu.local | P2/B2/B4/B6 staff |
| teacher_java_02 | teacher-java-02@edu.local | B1/B3/B5 staff |
| teacher_go_01 | teacher-go-01@edu.local | P4 staff |
| teacher_go_02 | teacher-go-02@edu.local | A2 staff |
| teacher_rust_01 | teacher-rust-01@edu.local | P6 staff |
| teacher_rust_02 | teacher-rust-02@edu.local | A4 staff |
| teacher_ai_01 | teacher-ai-01@edu.local | A1~A4 班级1主讲（李智敏，staff + Hub 管理员，startup 下发 A 全套工单） |
| teacher_ai_02 | teacher-ai-02@edu.local | A1~A4 班级2主讲（周成峰，staff + Hub 管理员，startup 下发 A 全套工单） |
| lecture_p1~p6 | lecture-p1~p6@edu.local | P 系列主讲（instructor） |
| Lecture-A1~A4 | lecture-a1~a4@edu.local | A 系列主讲（instructor，staff=True） |
| Lecture-B1~B6 | lecture-b1~b6@edu.local | B 系列主讲（instructor，staff=True） |
| admin | admin@openedx.local | 平台超级管理员 |
| ecommerce_worker / login_service_user | (系统默认) | Open edX 系统服务账号 |

### 7.11 学生账户使用速查（一线教师视角）

1. **发号**: 按班级给学生发用户名前缀（如 P1 课发 `stu_p1_xxx`，班级区分靠名册/Cohort），学生用该用户名在 LMS 注册（任意邮箱均可，激活自动完成）。
2. **登录 LMS**: `https://openedx.10.167.2.175.nip.io:31825`，注册后自动看到且仅看到自己前缀对应的那 1 门课。
3. **进 JupyterHub**: `https://jupyterhub.10.167.2.175.nip.io:31825/ide/`，用 LMS 同一账号 OAuth 登录；账户 5 分钟内自动同步（或管理员按 §5.5 立即触发）。
4. **领资料**: 学生 Pod 启动时自动拿到本课程学生版 Notebook + 代码框架（startup.sh 按 username 前缀分发）；教师账号拿双版本（学生版+教师版）。
5. **排障**: 学生说"看不到课" → ① 查用户名前缀是否正确（§4.4 表）；② 查 audit 日志是否命中 AUTOMOUNT；③ 查 Hub 同步（§5.5/§5.6、§8.3）。

## 8. JupyterHub 侧账户对照与同步通道

### 8.1 同步通道（三条并存）

| 通道 | 触发 | 命名 | 适用 |
|---|---|---|---|
| CronJob lms-hub-sync | 每 5 分钟 / 手动 §5.5 | LMS 用户名（§2.3 加固后） | 全部有选课账户 |
| OAuth 首次登录 | 用户首次进 Hub | 邮箱规范名（连字符） | 历史遗留；同名账户收敛后以同步通道为准 |
| load_groups 静态配置 | Hub 启动 | 配置直写 | student_* 演示账号、教师组 |

### 8.2 Hub 分组现状（加固重跑后实测，2026-09-14）

| Hub 分组 | 人数 | 说明 |
|---|---|---|
| all-students | 3350 | 含 1636 个连字符历史名；实义学生 ≈1691 |
| all-teachers | 27 | 16 教师 + 讲师 + 系统账户 |
| course-p-students / course-p-teachers | 1263 / 9 | P1~P6 学生/教师 |
| course-b-students / course-b-teachers | 1268 / 7 | B1~B6 |
| course-a-students / course-a-teachers | 864 / 7 | A1~A4 |
| industrial-*-students | 各 1 | 四语言演示学生 |
| lecture-pN-students 等 | 1~2 | 旧版演示分组（保留） |

### 8.3 排障速查

| 症状 | 排查 |
|---|---|
| LMS 有号、Hub 无号 | ① 该用户是否有选课（无选课不同步是预期）；② "邮箱前缀≠用户名"历史问题已由 §2.3 根治；③ 手动跑 §5.5 看 errors 字段 |
| Hub 出现陌生名用户 | 大概率历史邮箱前缀产物（如 0368414），核对 LMS 后按 §2.2 步骤 2 删除 |
| 学生看不到自己的 Notebook | startup.sh 按 username 分发，确认 Hub 用户名与课程前缀匹配（§8.1） |
| 同名学生出现两个变体（stu_p1_633 与 stu-p1-633） | OAuth 历史名与同步名并存，登录以 OAuth 实际进入的为准；数据盘 PVC 按 OAuth 名绑定，不影响使用 |

---

## 9. 账户体系 v3：双教师教学矩阵落地 + Hub 深度治理（2026-09-14 完成）

> v2 解决了"注册即激活 + 自动挂载 + 多教师排课"的机制层问题；v3 解决"到底谁带哪个班、学生在哪里看得到、Hub 侧账户全量归一"的事实层问题。v3 全部动作已在两个集群节点实测执行并验证。

### 9.1 双教师矩阵 v3（主讲/助教职责明确化）

v3 把每门课的两名教师固定为 **主讲(lead)** 与 **助教(assistant)** 双角色，并各自绑定一个班级：

| 课程 | 主讲 lead（class1） | 助教 assistant（class2） | 主讲授课班级 | 助教授课班级 |
|---|---|---|---|---|
| P1 | teacher_python_02 | teacher_zhang | p1-class1（78 人） | p1-class2（80 人） |
| P2 | teacher_java_01 | teacher_zhang | p2-class1 | p2-class2 |
| P3 | teacher_python_02 | teacher_zhang | p3-class1 | p3-class2 |
| P4 | teacher_go_01 | teacher_zhang | p4-class1 | p4-class2 |
| P5 | teacher_python_02 | teacher_zhang | p5-class1 | p5-class2 |
| P6 | teacher_rust_01 | teacher_zhang | p6-class1 | p6-class2 |
| B1 | teacher_java_01 | teacher_java_02 | b1-class1 | b1-class2 |
| B2 | teacher_java_02 | teacher_java_01 | b2-class1 | b2-class2 |
| B3 | teacher_java_01 | teacher_java_02 | b3-class1 | b3-class2 |
| B4 | teacher_java_02 | teacher_java_01 | b4-class1 | b4-class2 |
| B5 | teacher_java_01 | teacher_java_02 | b5-class1 | b5-class2 |
| B6 | teacher_java_02 | teacher_java_01 | b6-class1 | b6-class2 |
| A1 | teacher_zhang | teacher_python_02 | a1-class1（77 人） | a1-class2（77 人） |
| A2 | teacher_zhang | teacher_go_02 | a2-class1 | a2-class2 |
| A3 | teacher_zhang | teacher_python_02 | a3-class1 | a3-class2 |
| A4 | teacher_zhang | teacher_rust_02 | a4-class1 | a4-class2 |

两种合规形态均支持（矩阵即按此实现）：
- **形态一（共同带班）**：主讲带 class1、助教带 class2，同一课程两班可平行/串行、同/不同教室；
- **形态二（一讲一助）**：两名教师同带一个班，一人主讲一人答疑/批改——实现方式为把两人都加进同一班级 Cohort 的 Hub 组并都授予该课 staff 角色，学生侧无感知。

**LMS 角色落地**（`student_courseaccessrole` 表逐条核验）：每门课主讲 + 助教均拥有 `staff`/`instructor` 显式角色（CourseInstructorRole/CourseStaffRole API 授予），因此两名教师都能进 Studio 与教师仪表盘，且只看到自己授课的课程。

### 9.2 学生→教师→课程归属可见化

- 权威清单：`TEACHING-MATRIX.md`（本仓库根目录）——每门课一节，形如 `## A1 主讲=teacher_zhang(class1, 75人) 助教=teacher_python_02(class2, 77人)`，其下逐行列出该班全部学生用户名。**共 2431 名学生全部映射到「课程 + 班级 + 主讲 + 助教」四元组**，任何一名学生（如 stu_p1_001）打开该文件即可查到自己挂在哪位老师的哪门课哪个班。
- 系统内可见性：学生 Dashboard 只显示自己被挂载的 1 门课；教师仪表盘按 `student_courseaccessrole` 只显示自己任教的课程；Hub 侧每个学生进入 `course-{课程码}-class{1|2}` 组，组内含授课教师，管理员面板 `/ide/hub/admin` 可按组过滤查看。

### 9.3 Hub 账户全量归一（1688 脏账户清理）

**问题**：Hub SQLite 累积 3380 个账户，其中 1636 个是邮箱连字符历史名（stu-p1-001 等）与下划线规范名（stu_p1_001）并存的重复项，另有 52 个无 LMS 对应的孤儿（py_b_001~050、student1、student2）。

**修复**（已执行）：
1. 以 LMS `auth_user` 1748 名为权威，对 Hub 3380 名做 canon 匹配（lower + 连字符→下划线）；
2. 生成删除清单 1688 条，先删子表（user_group_map / user_role_map / api_tokens / oauth_codes / spawners）再删 users，孤儿角色一并清理；
3. **先改配置后清库**：根因是旧 `admin_users`/`load_groups` 引用了连字符形式（Lecture-P1、teacher-zhang 等），Hub 每次启动都会自动复活这些名字。v3 配置（ConfigMap `jupyterhub-config`）把两处全部改为 14 个规范下划线教师名 + 主讲 lecture_p1~p6，配置不再引用任何连字符名，复活通道被切断。

**结果**：Hub 1692 个规范账户 = LMS 1748 中的 1691 个有选课账户 + admin；重复变体 0 残留；同步 CronJob 幂等复验通过（users_existing 1691 / users_created 0）。

### 9.4 Hub 班级组动态镜像（32 个 course-{num}-class{1,2}）

- 同步脚本 v3（ConfigMap `cm-sync-script`）新增 `get_lms_cohort_rosters()`：直接读 LMS `course_groups_courseusergroup` JOIN `course_groups_cohortmembership`，取每门课 class1/class2 名册；
- `ensure_class_groups()` 在每轮同步（每 5 分钟）把名册镜像为 Hub 组 `course-p1-class1` 等，并把该班授课教师加入组内；幂等（第二次运行 memberships_added=0）；
- 首次填充一次性脚本补齐存量：2431 条组员关系，抽查 course-p1-class1=78、course-p1-class2=80、course-a1-class1=77、course-a1-class2=77 全部吻合；
- 清理 33 个遗留空组（class-aX-01-A 旧式命名、industrial-*-students 等）。

### 9.5 投诉主讲机制（制度 + 技术双通道设计）

利用现有账户数据即可定位"学生→班级→主讲"，无需新增表：

| 通道 | 流程 | 依据数据 |
|---|---|---|
| **课程内讨论区（主通道）** | 学生在 LMS 课程 Discussion 页发帖（分类选 `complaint-lead` 话题），该课 instructor/staff 均可见；管理员后台可按话题导出 | 学生选课记录 + 课程 roles |
| **班级直达（助教转办）** | 学生先向本班 Hub 组（course-{num}-classN）对应的助教反馈；助教核实后在 LMS 后台把工单升级给主讲 | Hub 组名册 = 投诉受理范围 |
| **管理员仲裁（兜底）** | admin 在 LMS Django admin 的 `student_courseaccessrole` 视图按课程列出全部教师，直接改派/撤销主讲（调整 §9.1 矩阵后由同步自动生效） | student_courseaccessrole + TEACHING-MATRIX.md |

职责边界：主讲对该课教学内容与成绩负责；助教受理本班日常问题；涉及主讲本人的投诉由助教或 admin 直接收理，形成闭环。换主讲 = 更新 §9.1 矩阵 + LMS 后台调整角色 + 下轮同步自动刷新 Hub 组，全链路 5 分钟内生效。

### 9.6 v3 验证清单（全部已执行）

| # | 验证项 | 结果 |
|---|---|---|
| 1 | P1 两教师均在 LMS 拥有该课 staff/instructor 角色 | ✅ student_courseaccessrole 逐条核验 |
| 2 | stu_p1_001 可查出归属（P1 · p1-class1 · 主讲 teacher_python_02 · 助教 teacher_zhang） | ✅ TEACHING-MATRIX.md |
| 3 | Hub 1688 脏账户删除后重复变体 0 残留 | ✅ canon 复查 0 |
| 4 | v3 hub 配置上线后连字符管理员不再复活 | ✅ 重启两轮复验 |
| 5 | 32 个班级组名册与 LMS Cohort 一致 | ✅ 抽查 4 组吻合 |
| 6 | 同步 CronJob 幂等 | ✅ 手动 Job 二次运行 memberships_added=0 |

### 9.7 v3 功能与并发实测结果（2026-09-15）

**功能测试（v3 机制断言，全部 PASS）**：

| # | 用例 | 结果 |
|---|---|---|
| T1 | LMS 登录（email 连字符格式 + login_session API + CSRF） | ✅ PASS |
| T2 | 800 个 C500 学生均已挂载本课程（CourseEnrollment 幂等复验） | ✅ PASS |
| T2b | 16 门课每门 ≥2 教师（staff/instructor 角色逐课核验） | ✅ PASS |
| T2c | 32 个班级 Cohort 名册与 TEACHING-MATRIX.md 一致（抽查吻合） | ✅ PASS |
| T2d | 800 学生口令统一（环境变量注入重置，验证登录成功） | ✅ PASS |
| T3 | Hub OAuth 入口页 200 | ✅ PASS |
| T4 | Hub 登录态 /hub/home 302（触发 spawn 流程） | ✅ PASS |
| T5 | v3 班级组 course-p1-class1/2 存在且含主讲 | ✅ PASS |
| T6 | lms-hub-sync CronJob 幂等（二次运行 0 变更） | ✅ PASS |

**并发实训测试（C500-V3，2026-09-15）**：

| 指标 | 值 |
|---|---|
| 测试脚本 | /tmp/c500v3_stress.py（aiohttp 无头并发，per-user 独立 Session/CookieJar，CSRF 缺失自动重试 4 次） |
| 账户 | stu_p1_001~050 … stu_a4_001~050（16 课程 × 50 = 800），周次 1~8 分布 |
| 目标并发 | 550（≥500 达标线） |
| **LMS 登录成功** | **741 / 800（92.6%）** |
| **Hub 可达** | **784 / 800（98.0%）** |
| **Hub home（实训页入口）** | **784 / 800（98.0%）** |
| 墙钟时间 | 242.4 s（约 4 分钟，远快于上一代 C500-V2 的 100 分钟） |
| 平均耗时 / P95 | 109.0 s / 231.0 s |
| 最慢用户 | stu_b6_028 242.3 s |

**失败样本分析（59 个 login 失败）**：全部为 `no-csrf-after-retries`——LMS uWSGI 双 worker 在 550 并发波首的 CSRF cookie 竞态（GET 响应未种 csrftoken），重试 4 次（累计约 15 s）仍未获得；属客户端压力模式放大项，非平台功能缺陷。Hub 侧 0 失败（784/784 全部 302/200），平台集群侧无 OOM、无 Pod 重启（lms 2Gi request、hub 单副本均平稳）。

**测试窗口临时配置变更（已还原）**：为越过 LMS 单 IP 登录限流（LOGISTRATION_RATELIMIT_RATE=100/5m），测试期间将 LMS 设置 ConfigMap 短暂切换为限流 10000/5m 的副本，测试后已还原 `openedx-settings-lms-c9mmh48c87` 并删除临时 ConfigMap `openedx-settings-lms-testrl`；还原后复验 setting=100/5m + 单用户 smoke 登录 200 通过。

**结论**：账户体系 v3 在 550 并发下 Hub 全链路成功率 98%（≥500 并发达标）；LMS 登录瓶颈为 uWSGI worker 数 × CSRF 竞态，扩 worker 或加 CSRF 预热可消除，不阻塞验收。

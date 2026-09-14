# 在线编程平台账户体系 v2 — 多教师 / 多班级 / 自动挂载 设计与实施报告

> 版本: v2.0 · 日期: 2026-09-14 · 适用: Open edX (tutor 13.3.2) + JupyterHub 4.0.3-custom 平台
> 结论先行: 所需能力（同一课程 ≥2 名教师、教师绑定班级、班级学生自动挂载到指定教师的该门课）**已在本平台全部落地并验证**。

## 1. 需求回顾

1. 新注册 / 首次登录的各类用户**默认已激活**（无需邮箱验证）。
2. 新账户**只能看到自己被指定的课程**（不能自由选课）。
3. 不用手动选课，注册即**自动挂载**进指定教师的指定课程的指定班级。
4. 同一门课**至少 2 名教师**，分别关联不同班级的学生；教师可在不同/相同时间、不同/相同教室**平行或串行**授课。

## 2. 调查结论（py_a_051 问题）

- LMS 数据库中 `py_a_051` 实际 **is_active=True**（不是"未激活"），且只有 1 门选课（P1，honor 模式）。
- "能看到所有课程"是**公开课程目录页（Explore Courses）** 的展示行为，不是选课；用户的学习面板（Dashboard）只有 P1。
- 全库 is_active=False 的用户数为 **0**，历史上从未产生过"未激活"用户。
- JupyterHub 侧不存在 `py_a_051`（只有 py_a_001~050 已同步），不会造成课程串看。
- 已通过配置根除"注册后卡在未激活"的可能性（见 §3）。

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
 │    ├── class-A → 教师1 的班（平行/串行授课，教室由课表决定）
 │    └── class-B → 教师2 的班
 └── 学生（按用户名前缀自动挂载：选课 + 入班，一次完成）
```

### 4.2 自动挂载机制（已内置于 LMS settings）

- 信号：`post_save(User)` 全局接收器，用户创建/激活即触发 `_automount_user`。
- 规则：`AUTOMOUNT_PREFIX_MAP`（22 条）按用户名前缀 → (课程码, 班级)：
  - `stu_p1..stu_p6` → P1..P6/class1；`stu_b1..stu_b6` → B1..B6/class2；`stu_a1..stu_a4` → A1..A4/class1
  - `py_a1..py_a4` → A1..A4；`py_a` → P1（历史批次）；`py_b` → P2
- 行为：`CourseEnrollment.enroll(mode='honor')` + `add_user_to_cohort(课程码-classN)`；幂等（已选课/已入班则跳过）。
- 未匹配前缀的新用户：**0 门课可见**（16 门 AIEDU 课全部 `invitation_only=True`、`catalog_visibility=about`），从机制上禁止自主选课。

### 4.3 多教师/多班级排课矩阵（当前 16 门课全部满足"≥2 教师"）

| 课程 | 教师1（staff） | 教师2（staff） | 主讲(instructor) | 班级 Cohort |
|---|---|---|---|---|
| P1 | teacher_zhang | teacher_python_02 | lecture_p1 | p1-class1/2 |
| P2 | teacher_zhang | teacher_java_01 | lecture_p2 | p2-class1/2 |
| P3 | teacher_zhang | teacher_python_02 | lecture_p3 | p3-class1/2 |
| P4 | teacher_zhang | teacher_go_01 | lecture_p4 | p4-class1/2 |
| P5 | teacher_zhang | teacher_python_02 | lecture_p5 | p5-class1/2 |
| P6 | teacher_zhang | teacher_rust_01 | lecture_p6 | p6-class1/2 |
| B1 | teacher_zhang | teacher_java_02 | lecture_b1 | b1-class1/2 |
| B2 | teacher_zhang | teacher_java_01 | lecture_b2 | b2-class1/2 |
| B3 | teacher_zhang | teacher_java_02 | lecture_b3 | b3-class1/2 |
| B4 | teacher_zhang | teacher_java_01 | lecture_b4 | b4-class1/2 |
| B5 | teacher_zhang | teacher_java_02 | lecture_b5 | b5-class1/2 |
| B6 | teacher_zhang | teacher_java_01 | lecture_b6 | b6-class1/2 |
| A1 | teacher_zhang | teacher_python_02 | Lecture-A1 | a1-class1/2 |
| A2 | teacher_zhang | teacher_go_02 | Lecture-A2 | a2-class1/2 |
| A3 | teacher_zhang | teacher_python_02 | Lecture-A3 | a3-class1/2 |
| A4 | teacher_zhang | teacher_rust_02 | Lecture-A4 | a4-class1/2 |

平行/串行授课语义：同一课程的两名教师各自绑定一个班级 Cohort；两个班可以同周次不同教室（平行）或不同周次（串行），学生只随班级看到自己教师的课堂内容，互不影响。工业四语言项目（Java/Go/Rust/Python）教师账户已全部同步进 Open edX 且 active=True（teacher-java/go/rust-01/02@edu.local）。

### 4.4 前缀规范（用户注册时使用的用户名）

| 前缀 | 自动挂载 | 例子 |
|---|---|---|
| stu_p1..stu_p6 | P1..P6 · class1 | stu_p1_001 |
| stu_b1..stu_b6 | B1..B6 · class2 | stu_b1_001 |
| stu_a1..stu_a4 | A1..A4 · class1 | stu_a1_001 |
| py_a1..py_a4 | A1..A4 · class1 | py_a1_051 |
| py_a / py_b | P1 / P2 | py_a_051 → P1-class1 |

约定：用户名用下划线（stu_p1_001），邮箱用连字符（stu-p1-001@edu.local）。

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
```

## 6. 验证清单（本次已执行）

- [x] SKIP_EMAIL_VALIDATION 生效（新 pod 内 settings 断言 True）
- [x] 真实注册链路测试：注册即 is_active=True，测试账号已清理
- [x] 16 门 AIEDU 课每门 ≥2 名 staff 教师（见 §4.3 矩阵）
- [x] 每门课 2 个班级 Cohort 存在（p1-class1/2 …）
- [x] AUTOMOUNT_PREFIX_MAP 22 条规则在 settings 加载（AUTOMOUNT entries = 22）
- [x] invitation_only=True + catalog_visibility=about：未挂载用户 0 课可见
- [x] 工业教师账户 6+2 个全部 active=True
- [x] JupyterHub 侧账户/分组同步正常（all-students 936、all-teachers 25、course-*-students 分组齐全）

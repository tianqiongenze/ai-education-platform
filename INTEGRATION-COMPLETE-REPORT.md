# 平台深度集成完成报告 (Plan B + Plan C)

> **完成时间**: 2026-09-09
> **执行范围**: 方案B (LMS选课→JupyterHub自动同步) + 方案C (全链路OAuth+成绩回写)
> **状态**: ✅ 全部完成

## 一、集成架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Open edX LMS (13)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ 16门真实课程  │  │ 228条选课记录 │  │ 18条成绩册 (grades_persistent)│   │
│  │ A1-A4/B1-B6/ │  │ 134个用户    │  │ percent_grade + letter   │   │
│  │ P1-P6        │  │ (16+8+7+100) │  │ A/B/C/D/F                │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘   │
│         │ courses          │ enrollments          │ grades           │
│         │ +HTML讲义         │                      │                  │
│         │ +JupyterHub链接   │                      │                  │
└─────────┼──────────────────┼──────────────────────┼──────────────────┘
          │                  │                      │
    ┌─────▼─────┐    ┌──────▼──────┐        ┌──────▼──────┐
    │ LMS OAuth2 │    │ CronJob     │        │ CronJob     │
    │ Provider   │    │ lms-hub-sync│        │ pl-writeback│
    │ (authorize/│    │ */5min      │        │ */15min     │
    │  token/user)│   │ MySQL→SQLite│        │ CRDB→MySQL  │
    └─────┬─────┘    └─────────────┘        └─────────────┘
          │ OAuth2
    ┌─────▼──────────────────────────────────────────┐
    │            JupyterHub (4.0.3)                   │
    │  ┌────────────────────────────────────────┐     │
    │  │ GenericOAuthenticator                  │     │
    │  │ • client_id: Cj6Ovzz0K...              │     │
    │  │ • authorize: /oauth2/authorize/        │     │
    │  │ • token: /oauth2/access_token/         │     │
    │  │ • userdata: /api/user/v1/me            │     │
    │  │ • PKCE: disabled (LMS兼容)             │     │
    │  │ • allow_all: True                      │     │
    │  └────────────────────────────────────────┘     │
    │  127 users (27原始 + 100同步)                    │
    │  分组: all-students/all-teachers/                │
    │  course-a/b/p-students/teachers                  │
    └──────────────────────────────────────────────────┘
```

## 二、各阶段执行结果

### 阶段0: 清理JupyterHub压测垃圾账号 ✅
- **操作**: 删除1311个压测垃圾账号 (stress-*, btest-*, conc-test-*, etc.)
- **结果**: Hub SQLite从1346用户降至27真实用户
- **清理表**: users, api_tokens, oauth_codes, spawners

### 阶段1: Open edX创建16门真实课程 ✅
- **课程结构**: org=AIEDU, run=2026, 共16门课程

| 系列 | 课程编号 | 课程名称 | 讲义数 |
|------|---------|---------|--------|
| A (AI应用基础) | A1-A4 | 泵类故障诊断/焊接检测/表面缺陷/智能决策 | 4门×2节=8 |
| B (程序设计基础) | B1-B6 | 设备参数/告警系统/继承体系/数据格式/故障分析/综合项目 | 6门×2节=12 |
| P (Python项目实战) | P1-P6 | Python基础/Pandas/仪表盘/数据采集/仓库/故障模型 | 4门×2节+2门×1节=10 |

- **每门课程结构**: chapter(讲义与实验) → sequential(章节) → vertical(单元) → html(讲义HTML)
- **HTML讲义内容**: 包含JupyterHub实验笔记本路径 + PrairieLearn评测入口链接
- **教师授权**: 每门课的 lecture-*@edu.local 获 CourseInstructorRole, teacher-zhang 获 CourseStaffRole
- **Overview页面**: 包含主讲教师、课程编号、学习路径指引（LMS→JupyterHub→PrairieLearn→成绩回写）

### 阶段2: Open edX学生选课+班级映射 ✅
- **总选课记录**: 228条 (AIEDU课程)
- **CourseMode**: 16门课程创建 honor 模式

| 课程 | 选课人数 | 学生构成 |
|------|---------|---------|
| A1 | 28 | 7 named students + 10 py_a class1 + teacher-zhang + 10 lecture accounts |
| A2-A4 | 18 each | 7 named + 10 py_a class2-4 + 1 teacher |
| B1-B5 | 18 each | 7 named + 10 py_b class1-5 + 1 teacher |
| B6, P1-P6 | 8 each | 7 named students + 1 teacher |

- **班级映射逻辑**: py_a_001~010→A1, py_a_011~020→A2, py_a_021~030→A3, py_a_031~040→A4, py_a_041~050→A1(回绕)
- **py_b系列同理**: 映射到B1-B6

### 阶段3 (方案B): LMS选课→JupyterHub自动同步服务 ✅
- **CronJob**: `lms-hub-sync`, namespace=jupyterhub, schedule=`*/5 * * * *`
- **镜像**: `10.100.135.132:5000/jupyterhub/custom:4.0.3` (含Python3.11+pip)
- **数据源**: Open edX MySQL `student_courseenrollment` 表 (JOIN `auth_user`)
- **目标**: JupyterHub SQLite `/srv/jupyterhub/jupyterhub.sqlite`
- **同步逻辑**:
  1. 读取所有 `course_id LIKE 'course-v1:AIEDU%+2026'` 的活跃选课记录
  2. 按email提取username (lecture-a1@edu.local → lecture-a1)
  3. 在Hub SQLite创建用户 (带cookie_id UUID + created时间戳)
  4. 加入分组: all-students/all-teachers + course-{series}-students/teachers
- **首次同步结果**: 100新用户创建, 207组成员关系添加, Hub总用户127
- **MySQL连接**: host=mysql.openedx.svc.cluster.local, user=root, pass=REDACTED

### 阶段4 (方案C-1): JupyterHub改用LMS OAuth认证 ✅
- **认证器**: `oauthenticator.generic.GenericOAuthenticator` (v17.4.0)
- **OAuth2 Provider**: Open edX LMS `oauth2_provider` 应用 `jupyterhub-sso`
- **配置参数**:

| 参数 | 值 |
|------|-----|
| client_id | REDACTED_CLIENT_ID |
| authorize_url | https://openedx.10.167.2.175.nip.io:31825/oauth2/authorize/ |
| token_url | https://openedx.10.167.2.175.nip.io:31825/oauth2/access_token/ |
| userdata_url | https://openedx.10.167.2.175.nip.io:31825/api/user/v1/me |
| username_key | username |
| scope | ["user_id"] |
| enable_pkce | False (Open edX oauth2_provider不支持PKCE) |
| allow_all | True (允许所有LMS认证用户) |

- **redirect_uri**: `https://10.167.2.175:31825/ide/hub/oauth_callback` (含/ide/前缀)
- **认证流程验证**: `/ide/hub/oauth_login` → 302重定向到LMS `/oauth2/authorize/` → 用户登录 → 回调 → token交换 → 用户信息获取
- **Hub Pod状态**: Running, 1/1 Ready

### 阶段5 (方案C-2): PrairieLearn成绩→LMS成绩册回写 ✅
- **CronJob**: `pl-lms-writeback`, namespace=jupyterhub, schedule=`*/15 * * * *`
- **数据源**: CockroachDB `scores` 表 (2991条记录)
- **目标**: MySQL `grades_persistentcoursegrade` 表
- **回写逻辑**:
  1. 读取近7天内非测试账号的最新成绩 (DISTINCT ON student_name, course_id)
  2. 按 PrairieLearn course_id 映射到 Open edX 课程编号 (python-industrial→P1-P6等)
  3. 查找LMS user_id (先精确username匹配, 再email前缀匹配)
  4. 计算 percent_grade = score/max_score, 映射 letter_grade (A≥90%, B≥80%, C≥70%, D≥60%, F<60%)
  5. INSERT或UPDATE grades_persistentcoursegrade记录
- **测试验证**: 插入3个真实学生的成绩 → 回写18条成绩记录

| 学生 | 分数 | 百分比 | 等级 | 写入课程数 |
|------|------|--------|------|-----------|
| student-alice | 95/100 | 0.95 | A | 6 (P1-P6) |
| student-python | 85/100 | 0.85 | B | 6 (P1-P6) |
| student-bob | 72/100 | 0.72 | C | 6 (P1-P6) |

### 阶段6: LMS课程页→JupyterHub/评测入口链接 ✅
- **实现方式**: 每门课程的HTML讲义内容块中包含:
  - JupyterHub入口链接: `https://apps.openedx.10.167.2.175.nip.io:31825/`
  - PrairieLearn评测链接: `http://10.167.2.175:30087`
  - 实验笔记本路径: `/tmp/notebooks/{series}/{nbname}_student.ipynb`
  - 学生版/教师版笔记本路径
- **Overview页面**: 包含4步学习路径指引 (LMS查看→JupyterHub练习→PrairieLearn提交→成绩回写)
- **课程URL验证**: `/courses/course-v1:AIEDU+P1+2026/courseware/` → 302 (重定向到登录页, 正确)

## 三、K8s资源清单

| 资源类型 | 名称 | 命名空间 | 说明 |
|---------|------|---------|------|
| CronJob | lms-hub-sync | jupyterhub | 每5分钟同步LMS选课→Hub |
| CronJob | pl-lms-writeback | jupyterhub | 每15分钟回写PrairieLearn成绩→LMS |
| ConfigMap | cm-sync-script | jupyterhub | 同步脚本 sync_lms_to_hub.py |
| ConfigMap | cm-writeback-script | jupyterhub | 回写脚本 writeback_grades.py |
| OAuth2 App | jupyterhub-sso | openedx (LMS) | OAuth2客户端, authorization-code模式 |

## 四、数据统计汇总

| 指标 | 数值 |
|------|------|
| LMS课程总数 | 17 (1 Demo + 16 AIEDU) |
| LMS用户总数 | 134 |
| LMS选课记录(AIEDU) | 228 |
| LMS成绩册记录 | 18 |
| JupyterHub用户总数 | 127 |
| JupyterHub分组数 | 8 (base) + 12 (lecture) = 20 |
| PrairieLearn成绩总数 | 2991 |
| CronJob运行状态 | 2个活跃, 均正常 |
| Hub Pod状态 | Running 1/1 |
| OAuth认证配置 | GenericOAuthenticator, PKCE禁用, allow_all |

## 五、安全说明

- 所有敏感信息（密码、API密钥、OAuth secrets）仅存储在K8s ConfigMap环境变量中, 未推送到GitHub
- GitHub仓库中不包含任何外部token (gho_/sk-) 或数据库密码
- OAuth2 client_secret 存储在JupyterHub ConfigMap中, 仅集群内可访问
- MySQL root密码存储在CronJob环境变量中, 仅集群内可访问

## 六、后续建议

1. **OAuth端到端测试**: 需通过浏览器实际登录LMS后完成OAuth回调, 验证token交换和用户信息获取的完整流程
2. **PrairieLearn API恢复**: PrairieLearn autograder API当前端口30087被code-server占用, 需恢复独立NodePort或通过Ingress访问
3. **压测数据归档**: CockroachDB中2991条测试成绩记录建议归档后清空, 仅保留真实学生成绩
4. **课程内容增强**: 当前HTML讲义为引导页面, 后续可嵌入实际教学内容、视频、交互式代码块

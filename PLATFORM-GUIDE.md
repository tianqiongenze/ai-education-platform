# 在线编程平台 用户指南与架构说明

> **更新时间**: 2026-09-09
> **平台版本**: Open edX 13 + JupyterHub 4.0.3 + PrairieLearn + Code-Server
> **访问入口**: https://10.167.2.175:31825 (局域网唯一入口)

---

## 一、LMS 与 CMS 有什么不同？

Open edX 平台由两个核心子系统组成，面向不同用户角色：

### LMS (Learning Management System) — 学习者视角

| 属性 | 说明 |
|------|------|
| **访问地址** | https://openedx.10.167.2.175.nip.io:31825 |
| **用户角色** | 学生、教师 |
| **核心功能** | 选课、学习课程内容、提交作业、查看成绩、讨论区 |
| **登录后首页** | 课程面板 (Dashboard) — 显示"我的课程" |
| **课程内容** | 讲义页面、实验指引、JupyterHub/PrairieLearn 入口链接 |

**LMS 登录后能做什么：**

1. **课程面板** (`/dashboard`) — 查看已选课程列表
2. **课程探索** (`/courses`) — 浏览全部17门可选课程
3. **课程学习** (`/courses/course-v1:AIEDU+P1+2026/courseware/`) — 查看讲义、实验内容
4. **课程进度** — 查看学习进度和成绩
5. **OAuth 登录入口** — 通过 LMS OAuth2 跳转到 JupyterHub 实验平台
6. **成绩查看** — 查看 PrairieLearn 自动回写的成绩 (grades_persistentcoursegrade)

### CMS/Studio (Course Management System) — 教师视角

| 属性 | 说明 |
|------|------|
| **访问地址** | https://studio.openedx.10.167.2.175.nip.io:31825 |
| **用户角色** | 课程创建者、教师、管理员 |
| **核心功能** | 创建/编辑课程结构、管理讲义内容、设置课程参数、管理选课 |
| **登录后首页** | Studio 主页 — 显示所有课程列表 |
| **课程编辑** | 章节结构管理、HTML 讲义编辑、课程设置 |

**Studio 登录后能做什么：**

1. **课程列表** (`/home/`) — 查看全部17门课程（1 Demo + 16 AIEDU）
2. **课程设置** (`/settings/details/course-v1:AIEDU+P1+2026`) — 课程详情、调度、评分规则
3. **课程创作** (`/course-authoring/course-v1:AIEDU+P1+2026`) — MFE 界面编辑课程内容
4. **课程大纲** — 编辑 chapter → sequential → vertical → html 层级结构
5. **查看线上版本** — 跳转到 LMS 查看学生看到的课程页面

### 对比总结

| 维度 | LMS | CMS/Studio |
|------|-----|-----------|
| 域名 | openedx.* | studio.* |
| 角色 | 学生 | 教师 |
| 首页 | 课程面板 (已选课程) | 课程列表 (全部课程) |
| 操作 | 选课、学习、提交 | 编辑、设置、管理 |
| 内容 | 只读 (消费内容) | 读写 (创建内容) |
| 对应传统系统 | 学生选课系统 | 教师后台管理系统 |

---

## 二、为什么"登录后啥也没有"？

### 问题原因

LMS 登录后看到的课程面板 (Dashboard) **只显示已选课的课程**。如果用户没有选课，面板会显示"您尚未参加任何课程"。

之前 admin 用户虽然创建了16门课程并授权了教师角色，但**没有给自己选课**，所以面板是空的。

### 已修复

已为 admin 用户选课全部16门课程。现在登录后可以看到：
- Python项目实战 P1~P6 (6门)
- 程序设计基础 B1~B6 (6门)
- AI应用基础 A1~A4 (4门)

### 操作指引

**学生登录 LMS 后的功能路径：**

```
登录 LMS → 课程面板 (看"我的课程")
    ├── 点击课程 → 课程内容页面 (courseware)
    │   ├── 查看 HTML 讲义 (含 JupyterHub 笔记本路径)
    │   ├── 点击链接 → 跳转 JupyterHub 实验平台
    │   │   └── OAuth 登录 → 打开 JupyterLab → 编写代码
    │   └── 点击链接 → 跳转 PrairieLearn 评测平台
    │       └── 提交代码 → 自动评分 → 成绩回写 LMS
    └── 点击"进度" → 查看成绩 (含 PrairieLearn 回写的分数)
```

**教师登录 Studio 后的功能路径：**

```
登录 Studio → 课程列表 (全部17门)
    ├── 点击课程 → 课程设置 (/settings/details/)
    │   └── MFE 课程创作界面 → 编辑内容
    ├── 点击"查看线上版本" → 跳转 LMS 预览
    └── 新建课程 → 创建新课程
```

---

## 三、平台全部服务与应用清单

### 3.1 核心平台服务

| 服务 | 命名空间 | 访问地址 | 端口 | 功能 |
|------|---------|---------|------|------|
| **Open edX LMS** | openedx | https://openedx.10.167.2.175.nip.io:31825 | 31825 | 学习管理系统 (学生端) |
| **Open edX CMS/Studio** | openedx | https://studio.openedx.10.167.2.175.nip.io:31825 | 31825 | 课程管理系统 (教师端) |
| **MFE 前端** | openedx | https://apps.openedx.10.167.2.175.nip.io:31825 | 31825 | 微前端 (learning/authn/account/gradebook/course-authoring) |
| **JupyterHub** | jupyterhub | https://10.167.2.175:31825/ide/ | 31825 | 编程实验平台 (JupyterLab) |
| **PrairieLearn** | prairielearn | http://10.167.2.175:30093 | 30093 | 自动评测平台 |
| **Code-Server** | ai-platform | http://10.167.2.175:30087 | 30087 | 在线 VS Code 编辑器 |
| **Ollama LLM** | ai-platform | http://10.167.2.175:30086 | 30086 | 大语言模型 (qwen2.5-coder:7b) |

### 3.2 数据库与中间件

| 服务 | 命名空间 | 用途 | 存储 |
|------|---------|------|------|
| **MySQL 5.7** | openedx | Open edX 用户/选课/成绩 | 关系型数据 |
| **MongoDB** | openedx | Open edX 课程内容 (modulestore) | 文档型存储 |
| **CockroachDB** | infra | PrairieLearn 成绩数据 | 分布式SQL |
| **JupyterHub SQLite** | jupyterhub | Hub 用户/分组/Token | SQLite 文件 |
| **Redis** | openedx | Open edX 缓存/会话 | 内存缓存 |

### 3.3 自动化服务 (CronJob)

| CronJob | 命名空间 | 调度 | 功能 |
|---------|---------|------|------|
| **lms-hub-sync** | jupyterhub | 每5分钟 | LMS选课 → JupyterHub用户/分组自动同步 |
| **pl-lms-writeback** | jupyterhub | 每15分钟 | PrairieLearn成绩 → LMS成绩册自动回写 |

### 3.4 账户体系

| 平台 | 账户数 | 认证方式 | 数据存储 |
|------|--------|---------|---------|
| Open edX LMS | 134 | 用户名/密码 | MySQL auth_user 表 |
| JupyterHub | 127 | LMS OAuth2 (GenericOAuthenticator) | SQLite users 表 |
| PrairieLearn | - | 独立注册 | CockroachDB |
| Code-Server | - | 独立密码 | - |

**账户同步流程：**
```
LMS MySQL (134用户) →[CronJob 每5分钟]→ JupyterHub SQLite (127用户)
    │
    └── 选课记录 (228条) → 自动加入 Hub 分组 (all-students/all-teachers/course-*-students/teachers)
```

### 3.5 课程体系

| 系列 | 课程数 | 课程编号 | 内容来源 |
|------|--------|---------|---------|
| AI应用基础 | 4 | A1-A4 | 泵类故障诊断/焊接检测/表面缺陷/智能决策 |
| 程序设计基础 | 6 | B1-B6 | 设备参数/告警系统/继承体系/数据格式/故障分析/综合项目 |
| Python项目实战 | 6 | P1-P6 | Python基础/Pandas/仪表盘/数据采集/仓库/故障模型 |

**每门课程结构：**
```
课程 (course-v1:AIEDU+{编号}+2026)
  └── 章节 (chapter: 讲义与实验)
      └── 小节 (sequential: 如 "P1.1 Python基础")
          └── 单元 (vertical: 如 "p11_P1.1_Python基础")
              └── HTML讲义 (html)
                  ├── 实验笔记本路径 (/tmp/notebooks/{series}/...)
                  ├── JupyterHub 入口链接
                  └── PrairieLearn 评测入口链接
```

### 3.6 集成架构

```
┌──────────────┐     OAuth2      ┌──────────────┐
│  Open edX    │◄───────────────►│  JupyterHub  │
│  LMS         │   (GenericOAuth  │  (JupyterLab)│
│  (学生端)     │   Authenticator) │              │
└──────┬───────┘                  └──────┬───────┘
       │                                 │
       │ 选课数据                  实验笔记本
       │ (MySQL)                  (ConfigMap挂载)
       │                                 │
  ┌────▼───────┐                 ┌──────▼───────┐
  │ CronJob    │                 │  PrairieLearn │
  │ lms-hub-   │                 │  (自动评测)    │
  │ sync       │                 └──────┬───────┘
  │ (每5分钟)   │                        │ 成绩
  └────────────┘                 ┌──────▼───────┐
                                 │  CronJob      │
                                 │  pl-lms-      │
                                 │  writeback    │
                                 │  (每15分钟)    │
                                 └──────────────┘
                                        │
                                        ▼
                               LMS成绩册 (grades_persistentcoursegrade)
```

---

## 四、各平台登录凭证

| 平台 | 账号 | 密码 | 角色 |
|------|------|------|------|
| LMS (管理员) | admin@openedx.local | EdxAdmin2026! | 管理员/教师/学生 |
| LMS (教师) | teacher-zhang@edu.local | EdxTeacher2026! | 教师 |
| LMS (学生) | student-python@edu.local | (同教师域) | 学生 |
| JupyterHub | (通过 LMS OAuth 登录) | - | 自动跳转LMS认证 |
| Code-Server | - | ide2026 | 独立认证 |

---

## 五、常见问题

### Q: 登录LMS后看不到课程？
**A**: LMS 面板只显示已选课的课程。需要先在 `/courses` 页面选课，选课后即可在面板看到。管理员已选全部16门课程。

### Q: Studio 和 LMS 有什么区别？
**A**: Studio (CMS) 是教师端，用于创建和编辑课程内容；LMS 是学生端，用于选课和学习。两者共用同一套课程数据，但界面和功能不同。

### Q: JupyterHub 怎么登录？
**A**: JupyterHub 使用 LMS OAuth2 认证。访问 https://10.167.2.175:31825/ide/ 后会自动跳转到 LMS 登录页，输入 LMS 账号密码后自动跳回 JupyterHub。新用户由 CronJob 每5分钟从 LMS 选课记录自动同步。

### Q: 成绩怎么看？
**A**: LMS 成绩页面会显示 PrairieLearn 自动回写的成绩。PrairieLearn 成绩通过 CronJob 每15分钟自动写入 LMS `grades_persistentcoursegrade` 表。

### Q: 课程设置页面404？
**A**: 已修复。Caddy 反向代理新增了 course-authoring MFE 路由规则，`/settings/details/` 路径现在正确转发到 MFE 服务。

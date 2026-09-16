# 在线编程平台账户密码总览

> **版本**: v1.0  
> **更新时间**: 2026-09-14  
> **平台**: Open edX + JupyterHub + Code-Server + PrairieLearn

---

## 一、平台服务账户密码

### 1.1 核心服务登录账号

| 服务 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| **Open edX LMS/Studio** | admin@openedx.local | `EdxAdmin2026!` | 管理员账号，最高权限 |
| **Open edX LMS/Studio** | teacher-zhang@edu.local | `EdxTeacher2026!` | 主教师账号，兼JupyterHub管理员 |
| **Code-Server** | 单密码 | `Dify@2026` | 所有用户共用密码 |
| **JupyterHub (历史)** | 任意用户名 | `ide2026` | **已停用**，现在通过LMS OAuth登录 |
| **Dify控制台** | myuwei@126.com | `Difyai123456` | AI应用管理 |
| **LiteLLM网关** | — | `sk-ai-platform-master` | API密钥 |
| **Redis Cluster** | — | `difyai123456` | 密码 |
| **Grafana** | admin | `uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb` | 监控面板 |
| **Rancher** | admin | `Rancher@2026` | 容器管理平台 |

### 1.2 Open edX 课程相关账户

#### 1.2.1 教师账户（已配置课程权限）

| 角色 | 账号 | 密码 | 权限说明 |
|------|------|------|---------|
| **主教师** | teacher-zhang@edu.local | `EdxTeacher2026!` | 所有课程管理，JupyterHub管理员 |
| **课程负责人** | lecture-p1@edu.local ~ lecture-p6@edu.local | `EdxTeacher2026!` | 每门课程的负责人 |
| **课程负责人** | lecture-a1@edu.local ~ lecture-a4@edu.local | `EdxTeacher2026!` | AI应用课程负责人 |
| **课程负责人** | lecture-b1@edu.local ~ lecture-b6@edu.local | `EdxTeacher2026!` | 软件工程课程负责人 |
| **助教/其他教师** | teacher_python_02, teacher_java_01 等 | `EdxTeacher2026!` | 按需分配 |
| **A 课程主讲（新设）** | teacher-ai-01@edu.local / teacher-ai-02@edu.local | 经 `TEACHER_PASS` 环境变量注入，不落文件/DB | A1~A4 班级1/班级2 主讲（李智敏/周成峰），staff + JupyterHub 管理员，登录 Hub 自动获得 A 全套 12 份工单学生版+教师版及 12 个代码框架 starter |

> 说明：teacher_zhang 保留为系统级教师测试账户。所有教师/学生密码仅通过 `TEACHER_PASS` / `STUDENT_PASS` / `ADMIN_PASS` 环境变量注入（冒烟脚本、测试套件运行时读取），不硬编码进任何文档或数据库。

#### 1.2.2 学生账户（通用样例）

| 账号类型 | LMS用户名 | 对应JupyterHub邮箱 | 说明 |
|----------|------------|-------------------|------|
| **Python实训** | student_python | student-python@edu.local | Python工业遥测分析环境 |
| **Java实训** | student_java | student-java@edu.local | Java MES生产管理系统 |
| **Go实训** | student_go | student-go@edu.local | Go工业网关开发环境 |
| **Rust实训** | student_rust | student-rust@edu.local | Rust安全审计环境 |
| **通用学生** | student_alice | student-alice@edu.local | Python通用环境 |
| **通用学生** | student_bob | student-bob@edu.local | Python通用环境 |
| **通用学生** | student_carol | student-carol@edu.local | Python通用环境 |

**注意**: 所有学生账户的密码都是通过LMS管理，没有独立的密码。学生通过LMS登录后，点击"请登录JupyterHub实验平台"自动跳转。

#### 1.2.3 C500并发测试专用学生账户

| 课程类型 | 账号范围 | 数量 | 说明 |
|----------|----------|------|------|
| **Python课程** | stu_p1_001 ~ stu_p1_050 | 50 | Python项目实战课程P1 |
| **Python课程** | stu_p2_001 ~ stu_p2_050 | 50 | Python项目实战课程P2 |
| **Python课程** | stu_p3_001 ~ stu_p3_050 | 50 | Python项目实战课程P3 |
| **Python课程** | stu_p4_001 ~ stu_p4_050 | 50 | Python项目实战课程P4 |
| **Python课程** | stu_p5_001 ~ stu_p5_050 | 50 | Python项目实战课程P5 |
| **Python课程** | stu_p6_001 ~ stu_p6_050 | 50 | Python项目实战课程P6 |
| **AI应用课程** | stu_a1_001 ~ stu_a1_050 | 50 | AI应用基础课程A1 |
| **AI应用课程** | stu_a2_001 ~ stu_a2_050 | 50 | AI应用基础课程A2 |
| **AI应用课程** | stu_a3_001 ~ stu_a3_050 | 50 | AI应用基础课程A3 |
| **AI应用课程** | stu_a4_001 ~ stu_a4_050 | 50 | AI应用基础课程A4 |
| **软件工程课程** | stu_b1_001 ~ stu_b1_050 | 50 | 软件工程基础课程B1 |
| **软件工程课程** | stu_b2_001 ~ stu_b2_050 | 50 | 软件工程基础课程B2 |
| **软件工程课程** | stu_b3_001 ~ stu_b3_050 | 50 | 软件工程基础课程B3 |
| **软件工程课程** | stu_b4_001 ~ stu_b4_050 | 50 | 软件工程基础课程B4 |
| **软件工程课程** | stu_b5_001 ~ stu_b5_050 | 50 | 软件工程基础课程B5 |
| **软件工程课程** | stu_b6_001 ~ stu_b6_050 | 50 | 软件工程基础课程B6 |

**C500学生账户登录方式**:
- **LMS邮箱**: stu-p1-001@edu.local, stu-p2-001@edu.local, ...
- **密码**: 通过环境变量注入，测试脚本自动使用
- **实际使用**: 学生通过LMS登录，点击课程链接自动跳转JupyterHub

### 1.3 Dify工作空间账户

所有Dify账户属于工作空间 `Zheng_Gong's Workspace`，统一初始密码 `Difyai123456`。

| 角色 | 人数 | 权限说明 | 账户示例 |
|------|------|---------|----------|
| **owner** (所有者) | 1 | 工作空间最高权限 | myuwei@126.com |
| **admin** (管理员) | 3 | 管理应用、知识库、成员 | javanetongzheng@icloud.com |
| **editor** (编辑者) | 1 | 创建/编辑应用和知识库 | joelgong@aliyun.com |
| **normal** (普通用户) | 10 | 使用已发布的应用 | 学生账号 |

---

## 二、账户使用流程

### 2.1 教师登录流程

1. **Open edX LMS**: `teacher-zhang@edu.local` / `EdxTeacher2026!`
2. **Studio课程管理**: 同上账号，进入studio.openedx.local
3. **JupyterHub管理**: 通过LMS OAuth登录，无需单独密码
4. **Code-Server**: `Dify@2026` (所有教师共用)
5. **Dify控制台**: `myuwei@126.com` / `Difyai123456`

### 2.2 学生登录流程

1. **Open edX LMS**: 使用个人邮箱（如 student-python@edu.local）
2. **密码**: 由教师在LMS中设置，学生忘记可联系教师重置
3. **JupyterHub**: 通过LMS点击"请登录JupyterHub实验平台"自动跳转
4. **Code-Server**: `Dify@2026` (所有学生共用)

### 2.3 特殊说明

1. **JupyterHub不再使用独立密码**: 历史的 `ide2026` 密码已停用，现在统一通过LMS OAuth
2. **C500测试账户**: 800个专用学生账户，密码通过测试脚本环境变量管理
3. **账户同步**: 每5分钟LMS会自动同步用户到JupyterHub

---

## 三、安全注意事项

### 3.1 密码安全

1. **定期更换**: 建议每学期更换教师和管理员密码
2. **避免泄露**: 不要在公开场合分享密码
3. **权限分离**: 教师和学生使用不同权限账户

### 3.2 账户管理

1. **学生账户**: 由教师统一管理，学生不能自行注册
2. **教师账户**: 由管理员创建，分配课程权限
3. **删除账户**: 如需删除，需在LMS和JupyterHub同时操作

### 3.3 访问控制

1. **网络限制**: 平台仅在内网访问，外部需要VPN
2. **IP白名单**: 可配置只允许特定IP访问
3. **会话超时**: 建议设置合理的会话超时时间

---

## 四、常见问题

### 4.1 忘记密码怎么办？

1. **教师忘记密码**: 联系系统管理员 `myuwei@126.com`
2. **学生忘记密码**: 联系课程教师重置
3. **服务密码**: 参考上表对应服务密码

### 4.2 无法登录怎么办？

1. **检查网络**: 确保在局域网内或通过VPN访问
2. **验证账号**: 确认用户名和密码正确
3. **联系支持**: 联系平台管理员

### 4.3 账户权限问题？

1. **教师权限**: 确认是否已分配课程权限
2. **学生权限**: 确认是否已选课
3. **管理员权限**: 联系统统管理员

---

## 五、联系方式

- **系统管理员**: myuwei@126.com
- **技术支持**: 通过平台内的反馈系统
- **紧急联系**: 平台故障请联系管理员

---

**文档版本**: v1.0  
**最后更新**: 2026-09-14  
**适用平台**: 在线编程平台 v3.2
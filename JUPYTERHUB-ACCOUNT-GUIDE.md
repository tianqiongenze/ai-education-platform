# JupyterHub 账户操作指南

> **适用对象**: 系统管理员、教师、学生  
> **平台**: JupyterHub 4.0.3-custom + Kubernetes  
> **更新日期**: 2026-09-14  

---

## 第一章 JupyterHub 概览

### 1.1 平台架构

```
                           局域网用户
                                 │
                    https://10.167.2.175:31825
                     (ingress-nginx NodePort)
                                 │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
    openedx.*                  studio.*                  jupyterhub.*
     LMS学生端                  Studio教师端              JupyterHub /ide/
         │                         │                         │
         └─────OAuth2 SSO──────────┘                         │
               (LMS 是唯一认证源)                             │
                                 │
                    ┌─────────────▼─────────────┐
                    │     JupyterHub Hub        │
                    │  (Kubernetes Deployment)  │
                    │     Port: 8000           │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     用户Pod               │
                    │  (Kubernetes StatefulSet) │
                    │   JupyterLab 环境        │
                    │   PVC: 5Gi 持久化存储   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     PrairieLearn         │
                    │  (自动评测系统)           │
                    │   NodePort: 30093        │
                    └───────────────────────────┘
```

### 1.2 服务地址

| 服务 | 地址 | 端口 | 说明 |
|------|------|------|------|
| **JupyterHub入口** | `https://10.167.2.175:31825/ide/` | 31825 | 通过ingress-nginx代理 |
| **Hub服务** | `http://jupyterhub.jupyterhub.svc.cluster.local:8000` | 8000 | 内部Hub服务 |
| **用户Pod** | `https://10.167.2.175:31825/ide/user/{username}/lab` | 31825 | 用户JupyterLab |
| **管理面板** | `https://10.167.2.175:31825/ide/hub/admin` | 31825 | 管理员面板 |

### 1.3 账户体系

| 账户类型 | 数量 | 认证方式 | 权限 | 存储位置 |
|----------|------|----------|------|----------|
| **教师/管理员** | 24个（16 lecture + teacher_zhang + teacher_ai_01/02 + admin 等） | OAuth2 | 管理面板访问 | SQLite |
| **学生** | 2431 个（16 门课按前缀自动挂载，详见 TEACHING-MATRIX.md） | OAuth2 | 基本使用 | SQLite |
| **通用学生** | 7个 | OAuth2 | 预配置环境 | SQLite |
| **系统用户** | 3个 | 本地 | 系统功能 | SQLite |

> 教师口令经 `TEACHER_PASS`、学生口令经 `STUDENT_PASS` 环境变量注入，不硬编码进文件或数据库。

---

## 第二章 账户类型详解

### 2.1 管理员账户

#### 2.1.1 主要管理员

| 账户 | 权限 | 说明 |
|------|------|------|
| **teacher-zhang** | 完全管理权限 | **系统级教师测试账户**（全 16 门课 staff，保留不动） |
| **teacher_ai_01** | 课程管理权限 | A 课程班级1主讲（李智敏，staff + JupyterHub 管理员，登录 Hub 自动获得 A 全套 12 份工单学生版+教师版及 12 个代码框架 starter） |
| **teacher_ai_02** | 课程管理权限 | A 课程班级2主讲（周成峰，staff + JupyterHub 管理员，同上） |
| **lecture-p1 ~ p6** | 课程管理权限 | Python项目实战课程主讲（instructor） |
| **lecture-a1 ~ a4** | 课程管理权限 | AI应用基础课程主讲（instructor） |
| **lecture-b1 ~ b6** | 课程管理权限 | 软件工程基础（程序设计基础）课程主讲（instructor） |

#### 2.1.2 管理员权限

1. **用户管理**: 创建、删除、修改用户
2. **分组管理**: 创建用户分组，设置权限
3. **服务管理**: 重启服务，查看状态
4. **资源监控**: 查看资源使用情况
5. **配置管理**: 修改JupyterHub配置

### 2.2 学生账户

#### 2.2.1 通用学生账户

| LMS用户名 | JupyterHub邮箱 | 环境配置 | 用途 |
|-----------|----------------|----------|------|
| **student_python** | student-python@edu.local | Python工业遥测分析 | Python实训 |
| **student_java** | student-java@edu.local | Java MES生产管理 | Java实训 |
| **student_go** | student-go@edu.local | Go工业网关开发 | Go实训 |
| **student_rust** | student-rust@edu.local | Rust安全审计 | Rust实训 |
| **student_alice** | student-alice@edu.local | Python通用环境 | 通用实训 |
| **student_bob** | student-bob@edu.local | Python通用环境 | 通用实训 |
| **student_carol** | student-carol@edu.local | Python通用环境 | 通用实训 |

#### 2.2.2 C500并发测试账户

| 课程类型 | 账号范围 | 数量 | 邮箱格式 |
|----------|----------|------|----------|
| **Python项目实战** | stu_p1_001 ~ stu_p1_050 | 50 | stu-p1-001@edu.local ~ stu-p1-050@edu.local |
| **Python项目实战** | stu_p2_001 ~ stu_p2_050 | 50 | stu-p2-001@edu.local ~ stu-p2-050@edu.local |
| **Python项目实战** | stu_p3_001 ~ stu_p3_050 | 50 | stu-p3-001@edu.local ~ stu-p3-050@edu.local |
| **Python项目实战** | stu_p4_001 ~ stu_p4_050 | 50 | stu-p4-001@edu.local ~ stu-p4-050@edu.local |
| **Python项目实战** | stu_p5_001 ~ stu_p5_050 | 50 | stu-p5-001@edu.local ~ stu-p5-050@edu.local |
| **Python项目实战** | stu_p6_001 ~ stu_p6_050 | 50 | stu-p6-001@edu.local ~ stu-p6-050@edu.local |
| **AI应用基础** | stu_a1_001 ~ stu_a1_050 | 50 | stu-a1-001@edu.local ~ stu-a1-050@edu.local |
| **AI应用基础** | stu_a2_001 ~ stu_a2_050 | 50 | stu-a2-001@edu.local ~ stu-a2-050@edu.local |
| **AI应用基础** | stu_a3_001 ~ stu_a3_050 | 50 | stu-a3-001@edu.local ~ stu-a3-050@edu.local |
| **AI应用基础** | stu_a4_001 ~ stu_a4_050 | 50 | stu-a4-001@edu.local ~ stu-a4-050@edu.local |
| **软件工程基础** | stu_b1_001 ~ stu_b1_050 | 50 | stu-b1-001@edu.local ~ stu-b1-050@edu.local |
| **软件工程基础** | stu_b2_001 ~ stu_b2_050 | 50 | stu-b2-001@edu.local ~ stu-b2-050@edu.local |
| **软件工程基础** | stu_b3_001 ~ stu_b3_050 | 50 | stu-b3-001@edu.local ~ stu-b3-050@edu.local |
| **软件工程基础** | stu_b4_001 ~ stu_b4_050 | 50 | stu-b4-001@edu.local ~ stu-b4-050@edu.local |
| **软件工程基础** | stu_b5_001 ~ stu_b5_050 | 50 | stu-b5-001@edu.local ~ stu-b5-050@edu.local |
| **软件工程基础** | stu_b6_001 ~ stu_b6_050 | 50 | stu-b6-001@edu.local ~ stu-b6-050@edu.local |

### 2.3 系统用户

| 用户名 | 用途 | 权限 |
|--------|------|------|
| **student1** | 历史测试用户 | 基本使用 |
| **student2** | 历史测试用户 | 基本使用 |
| **teacher_zhang** | 系统级教师测试账户（保留，全 16 门课 staff） | 管理权限 |

---

## 第三章 账户认证流程

### 3.1 OAuth2 认证流程

```
1. 学生访问 JupyterHub
   ↓
2. 重定向到 LMS 登录页
   ↓
3. 学生在 LMS 输入账号密码
   ↓
4. LMS 验证通过，生成 OAuth token
   ↓
5. 重定向回 JupyterHub，携带 token
   ↓
6. JupyterHub 验证 token，创建用户会话
   ↓
7. 启动用户 Pod，访问 JupyterLab
```

### 3.2 同步机制

#### 3.2.1 LMS 到 JupyterHub 同步

| 同步内容 | 频率 | 方式 | 说明 |
|----------|------|------|------|
| **用户创建** | 实时 | OAuth 首次登录 | 学生首次登录时自动创建 |
| **用户更新** | 每5分钟 | lms-hub-sync CronJob | 同步用户信息 |
| **用户删除** | 每5分钟 | lms-hub-sync CronJob | 同步删除用户 |
| **分组信息** | 每5分钟 | lms-hub-sync CronJob | 同步课程分组 |

#### 3.2.2 同步脚本

```bash
# 查看同步状态
kubectl get cronjob -n jupyterhub lms-hub-sync

# 查看同步日志
kubectl logs -n jupyterhub job/lms-hub-sync-xxxxx

# 手动触发同步
kubectl create job --from=cronjob/lms-hub-sync manual-sync -n jupyterhub
```

---

## 第四章 账户管理操作

### 4.1 管理员面板

#### 4.1.1 访问管理面板

1. **访问地址**: `https://10.167.2.175:31825/ide/hub/admin`
2. **登录账号**: 使用管理员账户（如 teacher-zhang）
3. **管理功能**: 用户管理、服务状态、资源监控

#### 4.1.2 用户管理

1. **查看用户**: 列出所有用户及其状态
2. **创建用户**: 手动创建新用户
3. **删除用户**: 删除用户及其数据
4. **修改权限**: 修改用户权限设置

### 4.2 命令行管理

#### 4.2.1 查看用户列表

```bash
# 查看 JupyterHub 用户
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('SELECT name, admin, created FROM users ORDER BY created')
for row in c.fetchall():
    print(f'User: {row[0]}, Admin: {row[1]}, Created: {row[2]}')
"

# 查看用户分组
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('SELECT name, users FROM groups')
for row in c.fetchall():
    print(f'Group: {row[0]}, Users: {row[1]}')
"
```

#### 4.2.2 用户操作

```bash
# 创建用户（SQLite）
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('INSERT INTO users (name, admin) VALUES (?, ?)', ('new_user', 0))
conn.commit()
print('User created: new_user')
"

# 删除用户
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('DELETE FROM users WHERE name = ?', ('old_user',))
conn.commit()
print('User deleted: old_user')
"

# 设置管理员权限
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('UPDATE users SET admin = 1 WHERE name = ?', ('admin_user',))
conn.commit()
print('Admin rights granted to: admin_user')
"
```

### 4.3 分组管理

> **现行命名**（v3 矩阵，详见 `TEACHING-MATRIX.md` / `ACCOUNT-SYSTEM-DESIGN-V2.md` §4.3）：班级分组为 `course-{课程码}-class{1|2}`（共 32 个），教师以课程 instructor（如 `lecture-p1`）及 A 课程主讲 `teacher_ai_01/02` 关联；下列 `course-p-teachers` / `class-p1-01-A` / `teacher-p1-01` 为早期示例，仅演示 SQL 用法。

#### 4.3.1 创建分组

```bash
# 创建课程分组
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()

# 创建课程教师分组
c.execute('INSERT INTO groups (name) VALUES (?)', ('course-p-teachers',))

# 创建班级分组
c.execute('INSERT INTO groups (name) VALUES (?)', ('class-p1-01-A',))

conn.commit()
print('Groups created')
"
```

#### 4.3.2 添加用户到分组

```bash
# 添加用户到分组
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()

# 获取分组ID
c.execute('SELECT id FROM groups WHERE name = ?', ('course-p-teachers',))
group_id = c.fetchone()[0]

# 添加用户到分组
c.execute('INSERT INTO group_members (group_id, user_id) VALUES (?, (SELECT id FROM users WHERE name = ?))', (group_id, 'teacher-p1-01'))

conn.commit()
print('User added to group')
"
```

---

## 第五章 资源管理

### 5.1 用户资源配置

#### 5.1.1 资源限制

| 资源类型 | 限制值 | 保底值 | 说明 |
|----------|--------|--------|------|
| **CPU** | 2核 | 0.2核 | 防止单用户占用过多资源 |
| **内存** | 2GB | 256MB | 确保基本运行需求 |
| **存储** | 5Gi | - | PVC持久化存储 |
| **启动超时** | 600秒 | - | 首次启动超时时间 |

#### 5.1.2 资源监控

```bash
# 查看Pod资源使用
kubectl top pods -n jupyterhub --sort-by=cpu

# 查看节点资源使用
kubectl top nodes

# 查看存储使用
kubectl get pvc -n jupyterhub
```

### 5.2 存储管理

#### 5.2.1 PVC 管理

```bash
# 查看所有PVC
kubectl get pvc -n jupyterhub

# 查看PVC详情
kubectl describe pvc -n jupyterhub

# 删除PVC（谨慎操作）
kubectl delete pvc -n jupyterhub claim-username
```

#### 5.2.2 数据备份

```bash
# 备份用户数据
kubectl exec -n jupyterhub jupyterhub-xxxxx -- tar czf /tmp/user_data_backup.tar.gz /srv/jupyterhub

# 备份PVC数据
kubectl exec -n jupyterhub user-pod-xxxxx -- tar czf /tmp/pvc_backup.tar.gz /home/jovyan/work
```

---

## 第六章 故障处理

### 6.1 常见问题

#### 6.1.1 用户无法登录

**问题**: 用户登录时显示认证失败

**解决方案**:
```bash
# 检查OAuth客户端状态
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('SELECT name, client_id FROM oauth_clients')
for row in c.fetchall():
    print(f'Client: {row[0]}, ID: {row[1]}')
"

# 重新创建OAuth客户端
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('DELETE FROM oauth_clients WHERE name = ?', ('jupyterhub-user-username',))
conn.commit()
"
```

#### 6.1.2 Pod 启动失败

**问题**: 用户Pod启动失败或超时

**解决方案**:
```bash
# 查看Pod事件
kubectl describe pod -n jupyterhub user-username-xxxxx

# 查看Pod日志
kubectl logs -n jupyterhub user-username-xxxxx

# 删除Pod重新创建
kubectl delete pod -n jupyterhub user-username-xxxxx
```

#### 6.1.3 存储空间不足

**问题**: PVC空间不足导致Pod启动失败

**解决方案**:
```bash
# 查看PVC使用情况
kubectl describe pvc -n jupyterhub claim-username

# 扩展PVC（如果支持）
kubectl patch pvc -n jupyterhub claim-username -p '{"spec":{"resources":{"requests":{"storage":"10Gi"}}}}'
```

### 6.2 性能优化

#### 6.2.1 节点亲和性优化

```yaml
# topologySpreadConstraints 配置
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: "kubernetes.io/hostname"
    whenUnsatisfiable: "ScheduleAnyway"
    labelSelector:
      matchLabels:
        component: "singleuser-server"
```

#### 6.2.2 资源限制调整

```yaml
# 资源限制配置
resources:
  requests:
    cpu: "0.05"
    memory: "256Mi"
  limits:
    cpu: "2"
    memory: "2Gi"
```

---

## 第七章 安全管理

### 7.1 访问控制

#### 7.1.1 网络访问控制

```bash
# 限制特定IP访问
iptables -A INPUT -p tcp --dport 31825 -s 10.167.2.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 31825 -j DROP
```

#### 7.1.2 用户权限控制

```bash
# 设置管理员权限
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "
import sqlite3
conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
c = conn.cursor()
c.execute('UPDATE users SET admin = 1 WHERE name IN (?, ?)', ('teacher-zhang', 'lecture-p1'))
conn.commit()
"
```

### 7.2 数据安全

#### 7.2.1 数据加密

```bash
# 加密PVC数据
kubectl exec -n jupyterhub user-username-xxxxx -- cryptsetup luksFormat /dev/pvc-volume
kubectl exec -n jupyterhub user-username-xxxxx -- cryptsetup luksOpen /dev/pvc-volume encrypted-volume
```

#### 7.2.2 审计日志

```bash
# 查看访问日志
kubectl logs -n jupyterhub jupyterhub-xxxxx | grep "OAuth\|login\|spawn"

# 记录用户操作
kubectl exec -n jupyterhub jupyterhub-xxxxx -- tail -f /var/log/jupyterhub/jupyterhub.log
```

---

## 第八章 监控与维护

### 8.1 系统监控

#### 8.1.1 Grafana监控面板

```bash
# 访问Grafana
open http://10.167.2.175:30090

# 默认账号
Username: admin
Password: uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb
```

#### 8.1.2 关键监控指标

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| **CPU使用率** | 节点CPU使用 | < 80% |
| **内存使用率** | 节点内存使用 | < 80% |
| **Pod数量** | 运行中的Pod数量 | 按需 |
| **响应时间** | JupyterHub响应时间 | < 5s |

### 8.2 定期维护

#### 8.2.1 数据备份

```bash
# 备份SQLite数据库
kubectl exec -n jupyterhub jupyterhub-xxxxx -- cp /srv/jupyterhub/jupyterhub.sqlite /tmp/jupyterhub_backup.db

# 备份用户数据
kubectl exec -n jupyterhub jupyterhub-xxxxx -- tar czf /tmp/user_data_backup.tar.gz /home/jovyan
```

#### 8.2.2 系统更新

```bash
# 更新JupyterHub镜像
kubectl set image deployment/jupyterhub jupyterhub=10.100.135.132:5000/jupyterhub/custom:4.0.3 -n jupyterhub

# 滚动更新
kubectl rollout status deployment/jupyterhub -n jupyterhub
```

---

## 第九章 最佳实践

### 9.1 用户管理

#### 9.1.1 账户命名规范

> **历史快照**：本表为早期命名约定。现行规范：教师用课程 instructor 账户（`lecture-p1~p6` / `Lecture-A1~A4` / `Lecture-B1~B6`）+ A 课程主讲 `teacher_ai_01/02`（李智敏/周成峰）+ 系统教师测试账户 `teacher-zhang`；学生用户名为 `stu_{p,b,a}N_xxx`（下划线前缀），分组为 `course-{课程码}-class{1|2}`。详见 `TEACHING-MATRIX.md`。

| 账户类型 | 命名规则 | 示例 |
|----------|----------|------|
| **教师** | teacher-{课程}-{序号} | teacher-p1-01 |
| **学生** | {课程}-{班级}-{学号} | p1-A-01 |
| **分组** | course-{课程}-{类型} | course-p-teachers |

#### 9.1.2 权限分配原则

1. **最小权限**: 只分配必要的权限
2. **角色分离**: 管理员和用户权限分离
3. **定期审查**: 定期审查权限设置
4. **离职处理**: 及时处理离职人员权限

### 9.2 性能优化

#### 9.2.1 资源分配

1. **按需分配**: 根据课程需求分配资源
2. **动态调整**: 根据负载动态调整资源
3. **负载均衡**: 合理分配用户到不同节点
4. **缓存优化**: 使用缓存提高响应速度

#### 9.2.2 存储管理

1. **定期清理**: 清理无用文件
2. **数据压缩**: 压缩大文件
3. **备份策略**: 制定定期备份策略
4. **监控使用**: 监控存储使用情况

---

## 第十章 联系支持

### 10.1 技术支持

- **系统管理员**: myuwei@126.com
- **紧急联系**: 平台故障请联系管理员
- **技术文档**: 查看相关技术文档

### 10.2 故障报告

1. **问题描述**: 详细描述问题现象
2. **环境信息**: 提供系统环境信息
3. **错误日志**: 提供相关错误日志
4. **复现步骤**: 提供问题复现步骤

---

## 附录：常用命令

### A.1 Kubernetes命令

```bash
# 查看Pod状态
kubectl get pods -n jupyterhub

# 查看服务状态
kubectl get svc -n jupyterhub

# 查看配置
kubectl get configmap -n jupyterhub

# 查看密钥
kubectl get secret -n jupyterhub
```

### A.2 JupyterHub命令

```bash
# 重启Hub
kubectl rollout restart deployment/jupyterhub -n jupyterhub

# 查看日志
kubectl logs -f jupyterhub-xxxxx -n jupyterhub

# 进入容器
kubectl exec -it jupyterhub-xxxxx -n jupyterhub -- bash

# 查看用户数据库
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "import sqlite3; conn=sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite'); c=conn.cursor(); c.execute('SELECT name FROM users'); print([r[0] for r in c.fetchall()])"
```

### A.3 调试命令

```bash
# 检查OAuth状态
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "import sqlite3; conn=sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite'); c=conn.cursor(); c.execute('SELECT * FROM oauth_clients'); print(c.fetchall())"

# 检查用户状态
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "import sqlite3; conn=sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite'); c=conn.cursor(); c.execute('SELECT name, admin, created FROM users'); print(c.fetchall())"

# 检查分组状态
kubectl exec -n jupyterhub jupyterhub-xxxxx -- python3 -c "import sqlite3; conn=sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite'); c=conn.cursor(); c.execute('SELECT name, users FROM groups'); print(c.fetchall())"
```

---

**文档版本**: v1.0  
**最后更新**: 2026-09-14  
**适用平台**: JupyterHub 4.0.3-custom
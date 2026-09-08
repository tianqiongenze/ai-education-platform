# JupyterHub 多租户在线编程平台 — 完整操作指南

> **平台地址**: `http://10.167.2.175:30089/ide/` (局域网IP直连,无需hosts)
> **注册密码**: `ide2026` (任意用户名+此密码即可注册)
> **版本**: JupyterHub 4.0.2 + JupyterLab 4.6.3
> **更新日期**: 2026-09-03

---

## 目录

1. [平台概览](#1-平台概览)
2. [用户注册与登录](#2-用户注册与登录)
3. [用户资源管理](#3-用户资源管理)
4. [项目管理](#4-项目管理)
5. [编程开发](#5-编程开发)
6. [测试与评分](#6-测试与评分)
7. [AI编程助手](#7-ai编程助手)
8. [GitHub集成](#8-github集成)
9. [数据分析](#9-数据分析)
10. [管理员操作](#10-管理员操作)

---

## 1. 平台概览

### 1.1 架构

```
[JupyterHub Hub] → [KubeSpawner] → 每个用户独立Pod
                                     ├─ Python 3.11 + AI框架
                                     ├─ Java 17 + Maven + Gradle + Spring Boot
                                     ├─ Go 1.21 + Gin/Echo/Fiber
                                     ├─ Rust 1.98 + Cargo
                                     ├─ Node.js v20 + Express/Next/React/Vue
                                     ├─ C/C++ GCC + CMake
                                     ├─ 数据库客户端 (psql/redis-cli/mysql/sqlite3)
                                     ├─ DevOps (docker CLI/kubectl/helm)
                                     └─ 5Gi 持久存储 (PVC)
```

### 1.2 开发环境清单

| 类别 | 工具 | 版本 |
|------|------|------|
| **Python** | Python + pip | 3.11.6 |
| **Java** | JDK + Maven + Gradle + Spring CLI | 17 + 3.9.16 + 8.10.2 + 3.3.5 |
| **Go** | Go + Gin/Echo/Fiber | 1.21.13 |
| **Rust** | rustc + cargo | 1.98.0 |
| **Node.js** | Node + npm + Express/Next/React/Vue/TS | v20.8.1 |
| **C/C++** | GCC + CMake + make + gdb | 11.4 + 3.22 |
| **数据库** | psql + redis-cli + mysql + sqlite3 | 14/6.0/8.0/3.37 |
| **DevOps** | docker CLI + kubectl + helm | 26.1.4 + 1.28.2 + 3.21 |
| **Python AI** | langchain, langgraph, openai, anthropic, transformers, torch(CPU) | latest |
| **Python Web** | flask, django, fastapi, uvicorn | latest |
| **Python 测试** | pytest, coverage, pylint, flake8, mypy, bandit, black | latest |
| **JupyterLab** | jupyter-ai, jupyterlab-lsp, python-lsp-server | 4.6.3 |

### 1.3 访问方式

- **主入口**: `http://10.167.2.175:30089/ide/`
- **Worker节点**: `http://10.167.2.176:30089/ide/`
- **无需hosts配置**, IP直连访问
- 子路径 `/ide/` 原生支持

---

## 2. 用户注册与登录

### 2.1 新用户注册

1. 浏览器打开 `http://10.167.2.175:30089/ide/`
2. 在登录页面输入:
   - **用户名**: 任意唯一用户名（如 `student-zhang`）
   - **密码**: `ide2026`（共享注册密码）
3. 点击 **Sign in** 按钮
4. 系统自动创建用户并分配独立Pod（首次约需1-2分钟）
5. Pod启动后自动进入 JupyterLab 界面

### 2.2 多账户登录

- 每个用户名对应独立的工作空间和数据
- 不同用户之间的数据完全隔离
- 支持同时多个用户登录（支持1000人并发）
- 每个用户获得 5Gi 持久存储空间

### 2.3 邀请用户

教师或管理员可以通过以下方式邀请用户:
1. 将注册密码 `ide2026` 分享给学生
2. 学生使用自己的用户名注册
3. 教师通过Mailpit (`http://10.167.2.175:30205`) 发送邀请邮件
4. 学生收到邮件后访问平台注册

### 2.4 用户名规范

推荐命名格式: `student-姓名拼音`（如 `student-zhangsan`）

---

## 3. 用户资源管理

### 3.1 存储管理

- 每用户 5Gi 持久存储 (PVC)
- 工作目录: `/home/jovyan/work/`
- 数据在Pod重启后持久化保留
- 用户可以创建子目录管理项目

### 3.2 Pod资源

- 每用户Pod: CPU 200m-2核, 内存 512Mi-4Gi
- 空闲Pod自动保持运行
- Pod状态可通过Hub管理页面查看

### 3.3 查看现有用户

管理员可从Hub数据库查看所有用户:
```bash
kubectl exec -n jupyterhub deploy/jupyterhub -- sqlite3 /srv/jupyterhub/jupyterhub.sqlite \
  "SELECT name FROM users;"
```

---

## 4. 项目管理

### 4.1 创建项目

在JupyterLab中:
1. 打开终端 (Terminal → New Terminal)
2. 创建项目目录:
   ```bash
   cd ~/work
   mkdir my-project
   cd my-project
   ```

### 4.2 项目结构规范

```
my-project/
├── src/                    # 源代码
│   ├── main/               # 主程序
│   └── test/               # 测试代码
├── docs/                   # 文档
│   └── SDD.md              # 软件设计文档
├── README.md               # 项目说明
├── .gitignore              # Git忽略文件
├── requirements.txt        # Python依赖 (或 pom.xml/build.gradle/go.mod/Cargo.toml)
└── tests/                  # 测试文件
```

### 4.3 内置项目示例

平台预置了4个完整工业互联网项目（在各学生Pod中）:

| 项目 | 语言 | 路径 | 说明 |
|------|------|------|------|
| 智能工厂MES系统 | Java/Spring Boot | ~/work/mes-system | 5个微服务模块,TOGAF架构 |
| 工业设备数据分析平台 | Python/FastAPI | ~/work/industrial-analytics | Clean Architecture,94%覆盖率 |
| 工业网关数据采集服务 | Go/Gin | ~/work/industrial-gateway | 六边形架构,97.9%覆盖率 |
| 工业安全审计系统 | Rust/Actix-Web | ~/work/security-audit | DDD领域驱动设计 |

---

## 5. 编程开发

### 5.1 Python开发

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install flask fastapi pandas numpy matplotlib

# 运行项目
python3 -m pytest --cov
python3 src/main.py
```

### 5.2 Java开发 (Spring Boot)

```bash
# 使用Maven创建项目
mvn archetype:generate -DgroupId=com.example -DartifactId=myapp -DarchetypeArtifactId=maven-archetype-webapp

# 或使用Spring CLI
spring init --dependencies=web myapp

# 构建运行
cd myapp
mvn clean test
mvn spring-boot:run
```

### 5.3 Go开发

```bash
# 初始化模块
go mod init myapp

# 安装框架
go get github.com/gin-gonic/gin

# 运行测试
go test -cover ./...
go run main.go
```

### 5.4 Rust开发

```bash
# 创建项目
cargo new myapp --bin
cd myapp

# 添加依赖
echo 'actix-web = "4"' >> Cargo.toml

# 运行测试
cargo test
cargo run
```

### 5.5 前端开发 (Node.js)

```bash
# 创建React应用
npx create-react-app my-frontend
cd my-frontend
npm start

# 或使用Next.js
npx create-next-app my-next-app
```

### 5.6 数据库连接

```bash
# PostgreSQL (集群内部)
psql -h db-postgres.dify-plus.svc.cluster.local -U postgres -W

# Redis (集群内部)
redis-cli -h redis.dify-plus.svc.cluster.local -a difyai123456

# SQLite (本地)
sqlite3 mydata.db
```

---

## 6. 测试与评分

### 6.1 自动评分系统

平台内置项目评分系统，支持自动检查和评分:

**访问方式**: 在JupyterLab中访问 `http://localhost:9999`

**评分维度** (7项, 总分130分):

| 检查项 | 工具 | 权重 | 说明 |
|--------|------|------|------|
| 代码质量 | pylint | 25分 | 语法错误、警告检查 |
| 代码风格 | flake8 | 15分 | PEP8风格规范 |
| 类型检查 | mypy | 10分 | 类型注解正确性 |
| 测试覆盖率 | pytest+coverage | 20分 | 目标≥80% |
| 代码复杂度 | AST分析 | 15分 | 圈复杂度 |
| 安全扫描 | bandit | 15分 | 安全漏洞检测 |
| 文档检查 | README/依赖/文档字符串 | 10分 | 文档完整性 |
| AI审查 | LLM代码审查 | 15分 | AI生成优化建议 |

**等级**: A(≥90%) B(≥80%) C(≥70%) D(≥60%) F(<60%)

### 6.2 使用评分系统

**Web界面**:
1. 在JupyterLab中打开浏览器或使用代理访问 `http://localhost:9999`
2. 从项目列表中选择项目
3. 点击"开始评分"
4. 查看评分报告（含等级、进度条、详细分析、优化建议）

**命令行**:
```bash
# Python项目
python3 ~/grader.py ~/work/my-project --lang python

# Java项目
python3 ~/grader.py ~/work/my-project --lang java

# Go项目
python3 ~/grader.py ~/work/my-project --lang go

# 报告保存为 grade_report.json
python3 ~/grader.py ~/work/my-project --lang python --output ~/work/report.json
```

### 6.3 运行测试

```bash
# Python
pytest --cov --cov-report=term-missing

# Java
mvn clean test

# Go
go test -cover ./...

# Rust
cargo test
```

---

## 7. AI编程助手

### 7.1 JupyterLab AI (jupyter-ai)

JupyterLab内置AI助手，可通过以下方式使用:
1. 在JupyterLab中打开AI聊天面板
2. 使用 `%%ai` 魔法命令调用AI模型

```python
# 在Jupyter Notebook中
%%ai qwen2.5-coder:7b
Write a Python function to calculate OEE
```

### 7.2 直接调用AI API

```python
import requests

# 调用LiteLLM网关
resp = requests.post(
    "http://litellm.ai-platform.svc.cluster.local:4000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-ai-platform-master",
        "Content-Type": "application/json"
    },
    json={
        "model": "qwen2.5-coder:7b",  # 编程模型
        "messages": [{"role": "user", "content": "Write a Python REST API with FastAPI"}],
        "max_tokens": 2000
    },
    timeout=120
)
print(resp.json()["choices"][0]["message"]["content"])
```

### 7.3 可用AI模型

| 模型 | 用途 | 说明 |
|------|------|------|
| qwen2.5-coder:7b | 编程辅助 | 代码生成、审查、补全 |
| qwen3:14b | 复杂推理 | 架构设计、方案分析 |
| qwen3:4b | 快速响应 | 简单问答、概念解释 |
| bge-m3 | 文本嵌入 | 语义搜索、知识库 |

---

## 8. GitHub集成

### 8.1 Git配置

```bash
# 配置Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
```

### 8.2 上传项目到GitHub

```bash
cd ~/work/my-project

# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: My Industrial IoT Project"

# 添加远程仓库
git remote add origin https://github.com/USERNAME/my-project.git

# 推送
git push -u origin main
```

### 8.3 克隆GitHub项目

```bash
cd ~/work
git clone https://github.com/USERNAME/project.git
cd project
```

### 8.4 已上传的项目

4个工业互联网项目已上传至GitHub（通过master node执行）:

| 项目 | 语言 | GitHub仓库 |
|------|------|-----------|
| 智能工厂MES系统 | Java | mes-system |
| 工业设备数据分析平台 | Python | industrial-analytics |
| 工业网关数据采集服务 | Go | industrial-gateway |
| 工业安全审计系统 | Rust | security-audit |

---

## 9. 数据分析

### 9.1 使用Pandas/NumPy

```python
import pandas as pd
import numpy as np

# 加载工业设备数据
df = pd.DataFrame({
    'device': ['CNC-001', 'CNC-002', 'Robot-001'],
    'temperature': [65.3, 72.1, 45.8],
    'vibration': [2.1, 3.5, 0.8],
    'power': [5.2, 8.7, 3.1]
})

# 统计分析
print(df.describe())
print("平均温度:", df['temperature'].mean())
print("异常设备:", df[df['temperature'] > 70]['device'].tolist())
```

### 9.2 使用Matplotlib可视化

```python
import matplotlib.pyplot as plt

# 温度趋势图
df['temperature'].plot(kind='bar')
plt.title('Device Temperature')
plt.ylabel('Temperature (°C)')
plt.show()
```

### 9.3 连接工业数据

```python
# 从工业互联网应用平台获取数据
import requests
resp = requests.get("http://10.167.2.175:30087/vscode/proxy/8888/api/v1/statistics")
stats = resp.json()
print(f"总设备数: {stats['total_devices']}")
print(f"运行中: {stats['running']}")
print(f"总功率: {stats['total_power_kw']}kW")
```

---

## 10. 管理员操作

### 10.1 查看用户Pod

```bash
# 查看所有用户Pod
kubectl get pods -n jupyterhub

# 查看用户资源使用
kubectl top pods -n jupyterhub

# 查看PVC存储使用
kubectl get pvc -n jupyterhub
```

### 10.2 管理用户

```bash
# 查看所有注册用户
kubectl exec -n jupyterhub deploy/jupyterhub -- sqlite3 /srv/jupyterhub/jupyterhub.sqlite "SELECT name FROM users;"

# 删除用户(Pod和PVC会被清理)
kubectl exec -n jupyterhub deploy/jupyterhub -- jupyterhub delete-user USERNAME

# 停止用户Pod(数据保留)
kubectl delete pod -n jupyterhub jupyter-USERNAME
```

### 10.3 配置修改

```bash
# 编辑JupyterHub配置
kubectl edit cm jupyterhub-config -n jupyterhub

# 重启Hub使配置生效
kubectl rollout restart deploy/jupyterhub -n jupyterhub

# 更新用户Pod镜像
kubectl edit cm jupyterhub-config -n jupyterhub
# 修改 c.KubeSpawner.image
# 然后重启Hub,新登录的用户将使用新镜像
```

### 10.4 扩容支持更多用户

```bash
# 增加Hub副本
kubectl scale deploy/jupyterhub -n jupyterhub --replicas=2

# 检查节点资源
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated"
```

### 10.5 故障排除

```bash
# 用户Pod卡在Pending
kubectl describe pod -n jupyterhub jupyter-USERNAME

# 检查Hub日志
kubectl logs -n jupyterhub deploy/jupyterhub --tail=50

# 清理失败的Pod
kubectl delete pods -n jupyterhub --field-selector=status.phase=Failed

# 手动清理Evicted Pod(释放资源)
kubectl delete pods -A --field-selector=status.phase=Failed
```

---

## 附录

### A. 端口对照表

| 服务 | 地址 | 说明 |
|------|------|------|
| JupyterHub | `http://10.167.2.175:30089/ide/` | 多用户在线编程平台 |
| JupyterLab (简易) | `http://10.167.2.175:30088/jupyter/` | 无需密码,快速使用 |
| Dify控制台 | `https://10.167.2.175:31825` | AI应用管理 |
| LiteLLM网关 | `http://10.167.2.176:30083` | AI模型API |
| Mailpit邮件 | `http://10.167.2.175:30205` | 邮件调试 |
| Grafana监控 | `http://10.167.2.175:30082` | 监控面板 |

### B. 常见问题

**Q: Pod启动很慢?**
A: 首次创建Pod需要拉取镜像(约8.5GB)并初始化环境,通常需要1-3分钟。后续登录会更快。

**Q: 如何安装额外的pip包?**
A: 在终端中运行 `pip3 install --break-system-packages 包名`。注意安装的包仅在当前用户Pod中有效。

**Q: 工作数据会丢失吗?**
A: 不会。每个用户有5Gi持久存储(PVC),数据在Pod重启后保留。但如果管理员删除了用户的PVC,数据会丢失。

**Q: 如何同时使用多种语言?**
A: 每个用户Pod支持所有语言(Java/Python/Go/Rust/Node.js/C++),无需切换。

**Q: 如何调用AI模型?**
A: 使用LiteLLM网关API: `http://litellm.ai-platform.svc.cluster.local:4000/v1`,密钥 `sk-ai-platform-master`。

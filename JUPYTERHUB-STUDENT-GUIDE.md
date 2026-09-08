# JupyterHub 学生使用指南

> **版本**: 2.0 | **日期**: 2026-09-05 | **适用**: 所有学生账户
> **包含**: 登录 → JupyterLab → AI 助手 → 4大项目完整操作 → 评分 → Git

---

## 目录

1. [登录与账户](#1-登录与账户)
2. [JupyterLab 界面操作](#2-jupyterlab-界面操作)
3. [AI 助手使用](#3-ai-助手使用)
4. [代码补全](#4-代码补全)
5. [项目1: Python 工业遥测分析](#5-项目1-python-工业遥测分析)
6. [项目2: Java MES 生产管理](#6-项目2-java-mes-生产管理)
7. [项目3: Go 工业网关](#7-项目3-go-工业网关)
8. [项目4: Rust 安全审计](#8-项目4-rust-安全审计)
9. [代码评分系统](#9-代码评分系统)
10. [Git 版本控制](#10-git-版本控制)
11. [8个实训 Notebook 操作](#11-8个实训-notebook-操作)
12. [常见问题](#12-常见问题)

---

## 1. 登录与账户

### 1.1 登录步骤

1. 浏览器打开 **`https://10.167.2.175:31825/ide/`**
2. 输入用户名（格式见下表）
3. 输入密码 `ide2026`
4. 等待 30-60 秒自动创建个人工作空间

### 1.2 用户名规则（重要！）

| 格式 | 自动加入分组 | 关联教师 | 示例 |
|------|-------------|----------|------|
| `p1-你的名字` | lecture-p1-students | Lecture-P1 | `p1-zhangsan` |
| `p2-你的名字` | lecture-p2-students | Lecture-P2 | `p2-lisi` |
| `p3-你的名字` | lecture-p3-students | Lecture-P3 | `p3-wangwu` |
| `p4-你的名字` | lecture-p4-students | Lecture-P4 | `p4-zhaoliu` |
| `p5-你的名字` | lecture-p5-students | Lecture-P5 | `p5-sunqi` |
| `p6-你的名字` | lecture-p6-students | Lecture-P6 | `p6-zhouba` |
| `你的名字`（无前缀） | all-students | teacher-zhang | `alice` |
| `b1-你的名字`~`b6-你的名字` | lecture-b1~b6-students | Lecture-B1~B6 | `b1-alice`~`b6-alice` |
| `a1-你的名字`~`a4-你的名字` | lecture-a1~a4-students | Lecture-A1~A4 | `a1-bob`~`a4-bob` |

> **重要**：用户名前缀决定了你自动获得哪个课程的 Notebook 和代码框架！

### 1.3 你的工作空间

| 项目 | 值 |
|------|-----|
| 目录 | `/home/jovyan/work/` |
| 存储空间 | 5Gi 持久化 PVC |
| 内核 | Python 3 (ipykernel) |
| AI 模型 | qwen2.5-coder:7b |
| 数据库 | CockroachDB (CRDB) |

---

## 2. JupyterLab 界面操作

### 2.1 界面概览

```
┌─────────────────────────────────────────────────┐
│  菜单栏: File Edit View Run Kernel Tabs Settings │
├──────────┬──────────────────────────────────────┤
│ 文件浏览器│                                      │
│          │        代码编辑器 / Notebook           │
│ /home/   │                                      │
│  jovyan/ │                                      │
│  work/   │                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│  状态栏: Python 3 (ipykernel) | 空闲             │
└─────────────────────────────────────────────────┘
```

### 2.2 快捷键

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 运行单元格 | `Shift + Enter` | 执行并跳到下一格 |
| 运行不跳格 | `Ctrl + Enter` | 执行留在当前格 |
| 代码补全 | `Tab` | 弹出补全建议 |
| AI 补全 | 自动触发 | AI 幽灵文本 |
| 保存 | `Ctrl + S` | 保存文件 |
| 新建终端 | `File → New → Terminal` | 打开终端 |
| 命令面板 | `Ctrl + Shift + C` | 快速执行命令 |

### 2.3 文件管理

- **上传**：拖放文件到浏览器，或点 Upload 按钮
- **下载**：右键文件 → Download
- **新建**：File → New → Notebook / Terminal / Folder
- **重命名**：右键文件 → Rename

### 2.4 内核管理

- **重启内核**：`Kernel → Restart Kernel`（清空所有变量）
- **切换内核**：`Kernel → Change Kernel`
- **关闭所有**：`Kernel → Shut Down All Kernels`

---

## 3. AI 助手使用

### 3.1 打开 AI 聊天

1. 点击 JupyterLab 左侧栏的 **AI 聊天图标**
2. 在聊天框中输入问题
3. AI 会在 5-15 秒内回复

### 3.2 AI 功能

| 功能 | 使用方式 | 示例 |
|------|----------|------|
| 代码生成 | 直接描述需求 | "写一个计算斐波那契的函数" |
| 代码解释 | 粘贴代码并询问 | "解释这段代码的作用" |
| 错误修复 | 粘贴代码+错误 | "这段代码报错，帮我修复" |
| 项目创建 | 详细描述架构 | "创建一个 FastAPI 项目..." |

### 3.3 AI 推理功能（在 Notebook 中使用）

```python
# 在 Notebook 单元格中运行以下代码使用 AI 功能
import json, urllib.request

PROXY = "http://ollama-master.ai-platform.svc.cluster.local:11434"
MODEL = "qwen2.5-coder:7b"

def ai_chat(prompt, max_tokens=200):
    """与 AI 对话"""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens}
    }).encode()
    req = urllib.request.Request(PROXY + "/api/chat", data=payload, 
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read()).get("message", {}).get("content", "")

def ai_embed(text):
    """文本嵌入（语义分析）"""
    payload = json.dumps({"model": "nomic-embed-text", "input": text}).encode()
    req = urllib.request.Request(PROXY + "/api/embed", data=payload,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

# 使用示例
print(ai_chat("写一个 Python 函数计算两个数的最大公约数"))
```

### 3.4 结构化输出（JSON 格式）

```python
def ai_json(prompt):
    """获取结构化 JSON 输出"""
    payload = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False, "format": "json",
        "options": {"num_predict": 100, "temperature": 0.3}
    }).encode()
    req = urllib.request.Request(PROXY + "/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(json.loads(resp.read()).get("response", "{}"))

# 使用示例：代码分析
result = ai_json('分析这段代码的质量，返回 {"score": 数字, "issues": []}...')
```

---

## 4. 代码补全

### 4.1 LSP 弹窗补全

已安装 `jupyterlab-lsp` + `python-lsp-server`，提供精确补全：

1. 输入 `pd.` → 自动弹出 DataFrame 方法
2. 输入 `np.` → 自动弹出 NumPy 函数
3. 按 `Tab` 手动触发补全
4. `Enter` 确认选择

### 4.2 AI 内联补全

输入代码后停顿，AI 会以灰色幽灵文本显示建议，按 `Tab` 接受。

---

## 5. 项目1: Python 工业遥测分析

### 5.1 项目概述

| 项目 | 值 |
|------|-----|
| 位置 | `/home/jovyan/work/industrial-analytics/` |
| 技术栈 | FastAPI + CockroachDB + Redis |
| 架构 | 六边形架构（领域层 + 用例层 + 基础设施层 + API层） |
| 数据库 | CRDB industrial_analytics |

### 5.2 目录结构

```
industrial-analytics/
├── pyproject.toml              # 项目配置
├── src/industrial/
│   ├── domain/                 # 领域层
│   │   ├── models.py           # TelemetryReading, DeviceStatus
│   │   └── thresholds.py       # 阈值分类 (NORMAL/WARNING/CRITICAL)
│   ├── use_cases/              # 用例层
│   │   ├── ingest_telemetry.py # 遥测数据入库
│   │   └── analytics_engine.py # 分析引擎
│   ├── infrastructure/         # 基础设施层
│   │   ├── database.py         # CRDB 连接
│   │   ├── sqlalchemy_repository.py  # ORM 仓储
│   │   ├── redis_cache.py      # L1+L2 双级缓存
│   │   └── mqtt_ingestor.py    # MQTT 采集
│   └── api/                    # API 层
│       ├── routes.py           # REST 路由
│       ├── schemas.py          # Pydantic 模型
│       └── app.py              # FastAPI 应用
├── tests/                      # 测试
│   ├── test_e2e_api.py         # E2E 测试 (30个)
│   └── conftest.py             # 测试配置
├── frontend/index.html         # 工业级 Dashboard
└── README.md
```

### 5.3 操作步骤

#### 步骤1: 安装依赖

```bash
cd /home/jovyan/work/industrial-analytics
pip install -e ".[dev]"
```

#### 步骤2: 启动后端

```bash
# 设置数据库连接（CockroachDB）
export DATABASE_URL="postgresql://root@cockroachdb.infra.svc.cluster.local:26257/industrial_analytics?sslmode=disable"
export DATABASE_READ_URL="postgresql://root@cockroachdb-read.infra.svc.cluster.local:26267/industrial_analytics?sslmode=disable"
export REDIS_URL="redis://:difyai123456@redis.infra.svc.cluster.local:6379/0"

# 启动
uvicorn industrial.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

#### 步骤3: 使用前端 Dashboard

1. 在 JupyterLab 文件浏览器中双击 `frontend/index.html`
2. Dashboard 会打开，显示：
   - 遥测总数、缓存类型、设备状态
   - 发送遥测数据表单
   - 异常分析查询
   - 设备状态列表
   - 缓存统计
   - API 调用日志

#### 步骤4: 运行测试

```bash
cd /home/jovyan/work/industrial-analytics

# 运行全部测试（30个 E2E 测试）
python -m pytest tests/test_e2e_api.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=industrial --cov-report=html
```

#### 步骤5: 使用 API

```python
# 在 Notebook 中调用 API
import requests

BASE = "http://localhost:8000/api/v1"

# 发送遥测数据
resp = requests.post(f"{BASE}/telemetry", json={
    "device_id": "PUMP-001",
    "metric": "temperature",
    "value": 75.5,
    "unit": "°C"
})
print(resp.json())  # {"device_id": "PUMP-001", "status": "WARNING", ...}

# 查询分析
resp = requests.get(f"{BASE}/analytics", params={
    "device_id": "PUMP-001", "metric": "temperature", "window": 10
})
print(resp.json())  # {"mean": 75.5, "std": 2.1, "anomalies_zscore": 0, ...}

# 查看设备状态
resp = requests.get(f"{BASE}/status/PUMP-001")
print(resp.json())
```

---

## 6. 项目2: Java MES 生产管理

### 6.1 项目概述

| 项目 | 值 |
|------|-----|
| 位置 | `/home/jovyan/work/mes-system/` |
| 技术栈 | Spring Boot 3 + CockroachDB + Redis |
| 微服务 | gateway(8080), production(8081), quality(8082), equipment, inventory |
| 数据库 | CRDB mes_system |

### 6.2 目录结构

```
mes-system/
├── pom.xml                        # 父 POM
├── gateway-service/               # API 网关
├── production-service/            # 生产订单管理
│   ├── src/main/java/com/mes/production/
│   │   ├── controller/ProductionController.java
│   │   ├── service/ProductionService.java
│   │   ├── entity/ProductionOrder.java
│   │   ├── dto/ProductionOrderRequest.java
│   │   ├── config/RoutingDataSource.java  # CRDB 读写分离
│   │   └── config/DataSourceConfig.java
│   └── src/test/java/com/mes/production/
├── quality-service/               # 质量检测管理
├── equipment-service/             # 设备管理
├── inventory-service/             # 库存管理
├── cache-common/                  # 双级缓存公共模块
├── frontend/index.html            # MES Dashboard
└── e2e-tests/                     # E2E 测试
```

### 6.3 操作步骤

#### 步骤1: 编译

```bash
cd /home/jovyan/work/mes-system
mvn clean package -DskipTests -q
```

#### 步骤2: 启动服务

```bash
# 启动生产服务（端口 8081）
java -jar production-service/target/production-service-*.jar &

# 启动质量服务（端口 8082）
java -jar quality-service/target/quality-service-*.jar &
```

#### 步骤3: 使用前端

双击 `frontend/index.html` 打开 MES Dashboard

#### 步骤4: 运行测试

```bash
cd /home/jovyan/work/mes-system/production-service
mvn test -q
# 结果: 19 tests pass

cd /home/jovyan/work/mes-system/quality-service
mvn test -q
# 结果: 8 tests pass
```

#### 步骤5: API 操作示例

```bash
# 创建生产订单
curl -X POST http://localhost:8081/api/v1/production/orders \
  -H "Content-Type: application/json" \
  -d '{"productName": "阀门A", "plannedQuantity": 100, "priority": "HIGH"}'

# 查询订单
curl http://localhost:8081/api/v1/production/orders

# 开始生产
curl -X POST http://localhost:8081/api/v1/production/orders/{id}/start

# 报工
curl -X POST "http://localhost:8081/api/v1/production/orders/{id}/progress?completed=50&defects=2"

# 记录质检
curl -X POST http://localhost:8082/api/v1/quality/inspections \
  -H "Content-Type: application/json" \
  -d '{"orderId": "ORD-001", "inspectionItem": "尺寸", "result": "PASS"}'
```

---

## 7. 项目3: Go 工业网关

### 7.1 项目概述

| 项目 | 值 |
|------|-----|
| 位置 | `/home/jovyan/work/industrial-gateway/` |
| 技术栈 | Gin + CockroachDB + Redis |
| 架构 | 清洁架构（domain + usecase + adapter + infra） |
| 数据库 | CRDB industrial_gateway |

### 7.2 目录结构

```
industrial-gateway/
├── cmd/gateway/main.go           # 入口
├── internal/
│   ├── domain/                   # 领域层
│   │   ├── reading.go            # Reading 实体
│   │   ├── device.go             # Device 实体
│   │   ├── classify.go           # 状态分类
│   │   └── transform.go          # 数据转换
│   ├── usecase/                  # 用例层
│   │   └── ingest.go             # IngestService
│   ├── adapter/
│   │   ├── http/                 # Gin REST API
│   │   ├── grpc/                 # gRPC 服务
│   │   └── metrics/              # Prometheus 指标
│   └── infra/
│       ├── crdbstore/            # CRDB 读写分离
│       ├── rediscache/           # Redis 缓存
│       ├── mqtt/                 # MQTT 采集
│       └── modbus/               # Modbus 采集
├── frontend/index.html           # 网关 Dashboard
└── go.mod
```

### 7.3 操作步骤

#### 步骤1: 编译

```bash
cd /home/jovyan/work/industrial-gateway
go build -o gateway cmd/gateway/main.go
```

#### 步骤2: 运行

```bash
./gateway
# 启动在 0.0.0.0:8090
```

#### 步骤3: 运行测试

```bash
go test ./... -v -count=1
# 结果: 8 个包全部通过
```

#### 步骤4: API 操作

```bash
# 采集数据
curl -X POST http://localhost:8090/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"device_id": "SENSOR-001", "metric": "temperature", "value": 45.5}'

# 查询最新读取
curl http://localhost:8090/api/v1/readings/SENSOR-001

# 设备状态
curl http://localhost:8090/api/v1/status/SENSOR-001

# 注册设备
curl -X POST http://localhost:8090/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"id": "SENSOR-006", "name": "压力传感器", "protocol": "modbus"}'
```

---

## 8. 项目4: Rust 安全审计

### 8.1 项目概述

| 项目 | 值 |
|------|-----|
| 位置 | `/home/jovyan/work/security-audit/` |
| 技术栈 | actix-web + CockroachDB + Redis |
| 架构 | 六边形架构（domain + application + infrastructure） |
| 数据库 | CRDB security_audit |

### 8.2 目录结构

```
security-audit/
├── Cargo.toml                    # Rust 项目配置
├── src/
│   ├── domain/                   # 领域层
│   │   ├── audit.rs              # AuditSession 实体
│   │   ├── compliance.rs         # 合规报告
│   │   ├── vulnerability.rs      # 漏洞扫描
│   │   └── error.rs              # 错误定义
│   ├── application/              # 应用层
│   │   └── audit_service.rs      # AuditService
│   ├── infrastructure/           # 基础设施层
│   │   ├── crdb_repository.rs    # CRDB 仓储
│   │   ├── cache.rs              # Redis 双级缓存
│   │   └── http.rs               # actix-web 路由
│   └── bin/
│       ├── server.rs             # 服务器入口
│       └── cli.rs                # CLI 工具
├── tests/                        # 32 个测试
│   ├── domain_audit_test.rs      # 10 个
│   ├── compliance_test.rs        # 7 个
│   ├── application_test.rs       # 5 个
│   ├── repository_test.rs        # 5 个
│   └── vulnerability_test.rs     # 5 个
├── frontend/index.html           # 安全审计 Dashboard
└── README.md
```

### 8.3 操作步骤

#### 步骤1: 编译

```bash
export CARGO_HOME=/home/jovyan/.cargo
cd /home/jovyan/work/security-audit
cargo build --release
```

#### 步骤2: 启动服务器

```bash
./target/release/server
# 启动在 0.0.0.0:8091
```

#### 步骤3: 运行测试

```bash
cargo test --release
# 结果: 32/32 通过
```

#### 步骤4: API 操作

```bash
# 创建审计会话
curl -X POST http://localhost:8091/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"target": "PLC-Line1", "auditor": "student"}'

# 执行漏洞扫描
curl -X POST http://localhost:8091/api/v1/audits/{id}/scan \
  -H "Content-Type: application/json" \
  -d '{"fingerprints": ["hmi-default-creds", "modbus-plaintext"]}'

# 合规报告
curl -X POST http://localhost:8091/api/v1/audits/{id}/compliance \
  -H "Content-Type: application/json" \
  -d '{"security_level": 2}'

# 完成审计
curl -X POST http://localhost:8091/api/v1/audits/{id}/finalize
```

---

## 9. 代码评分系统

### 9.1 运行评分

```bash
# 在终端中运行
python3 /home/jovyan/work/code_grader.py

# 或在 Notebook 中运行
!python3 /home/jovyan/work/code_grader.py
```

### 9.2 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| PEP8 规范 | 20% | pycodestyle 检查 |
| 测试通过率 | 40% | pytest 测试结果 |
| 原创性 | 20% | 与其他项目代码查重 |
| AI率 | 20% | 检测 AI 生成代码比例 |

### 9.3 等级标准

| 等级 | 分数 | 说明 |
|------|------|------|
| A | ≥90 | 优秀 |
| B | 80-89 | 良好 |
| C | 70-79 | 合格 |
| D | 60-69 | 勉强通过 |
| F | <60 | 不及格 |

### 9.4 查看报告

```bash
# 评分报告保存在
cat /home/jovyan/work/grading_report.json
```

---

## 10. Git 版本控制

### 10.1 配置

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 10.2 提交代码

```bash
cd /home/jovyan/work/industrial-analytics
git add -A
git commit -m "完成P1.1练习"
git push origin master
```

### 10.3 GitHub 仓库

| 项目 | 仓库 |
|------|------|
| Python | https://github.com/tianqiongenze/industrial-analytics |
| Java | https://github.com/tianqiongenze/mes-system |
| Go | https://github.com/tianqiongenze/industrial-gateway |
| Rust | https://github.com/tianqiongenze/security-audit |

---

## 11. 8个实训 Notebook 操作

根据你的用户名前缀，自动获得对应课程的 Notebook：

| 前缀 | Notebook | 主题 |
|------|----------|------|
| p1-* | P1.1 Python基础 | C→Python 迁移五题 |
| p1-* | P1.2 标准Python | 标准工程模板 |
| p2-* | P2.1 Pandas数据 | Pandas 数据清洗 |
| p2-* | P2.2 NumPy故障 | NumPy 故障特征提取 |
| p3-* | P3 KPI仪表盘 | Streamlit 仪表盘 |
| p4-* | P4.1 多源采集 | 多源数据采集系统 |
| p5-* | P5 数据仓库 | 数据仓库与 ORM |
| p6-* | P6 故障诊断 | 故障诊断模型 |

### 11.1 Notebook 操作步骤

1. 在文件浏览器中双击打开 Notebook
2. 从上到下逐个执行单元格（`Shift + Enter`）
3. 第一格输出 `工作目录: /home/jovyan/work` 表示环境正常
4. 练习单元格需要你填写 TODO 部分的代码
5. 最后一格是测试断言，完成后应显示 `全部测试通过 ✓`

### 11.2 各 Notebook 说明

#### P1.1 Python基础
- 5道练习：温度换算、一元二次方程、设备字典管理、PLC类、文件安全读取
- 完成所有 TODO 后最后一格应显示通过

#### P1.2 标准Python
- 生成标准工程模板（src/, tests/, config/）
- 执行后按提示操作：git init → pytest → pylint

#### P2.1 Pandas数据
- 数据清洗管道：加载 → 缺失值 → 异常值 → 保存
- 输出质量评分（目标 ≥85 分）

#### P2.2 NumPy故障
- 故障特征提取：时域+频域特征
- 特征矩阵 (200, 13)，目标耗时 <50ms

#### P3 KPI仪表盘
- Streamlit 仪表盘 + 自动日报
- 需要 streamlit 和 plotly 库

#### P4.1 多源采集
- 三线程采集架构：Modbus + MQTT + REST
- 需要 pymodbus 和 paho-mqtt 库

#### P5 数据仓库
- SQLite 数据仓库 + SQLAlchemy ORM
- 索引优化对比

#### P6 故障诊断
- ML 模型训练 + API 部署
- 需要安装 scikit-learn

---

## 12. 常见问题

### Notebook 无输出？
```bash
# 方法1: 重启内核
# Kernel → Restart Kernel → 重新执行

# 方法2: 检查文件是否存在
ls /home/jovyan/work/*.ipynb
```

### os.chdir 报错？
```python
# 将 os.chdir(os.path.abspath("../")) 
# 改为:
os.chdir("/home/jovyan/work")
```

### AI 无响应？
- 等待 30 秒后重试
- 高峰期响应可能较慢（Ollama CPU 推理）
- 检查代理是否正常: `curl http://ollama-master.ai-platform.svc.cluster.local:11434/health`

### 测试失败？
```bash
# 查看详细错误
python -m pytest tests/ -v --tb=long

# 检查数据库连接
export DATABASE_URL="postgresql://root@cockroachdb.infra.svc.cluster.local:26257/industrial_analytics?sslmode=disable"
```

### 缺少依赖？
```bash
pip install streamlit plotly pymodbus paho-mqtt scikit-learn
```

### 存储满了？
```bash
# 查看磁盘使用
df -h /home/jovyan/work
# 删除不需要的文件
rm -rf /home/jovyan/work/大文件
```

---

## 附录: 环境变量速查

| 变量 | 值 | 说明 |
|------|-----|------|
| `DATABASE_URL` | `postgresql://root@cockroachdb.infra.svc.cluster.local:26257/...` | 写连接 |
| `DATABASE_READ_URL` | `postgresql://root@cockroachdb-read.infra.svc.cluster.local:26267/...` | 读连接 |
| `REDIS_URL` | `redis://:difyai123456@redis.infra.svc.cluster.local:6379/0` | 缓存 |
| `CARGO_HOME` | `/home/jovyan/.cargo` | Rust |
| `GOPATH` | `/home/jovyan/go` | Go |

---

## 19. 多语言代码审查系统 (v2.1 新增)

### 支持语言与工具

| 语言 | 工具 | 检查内容 |
|------|------|----------|
| Python | pycodestyle + pyflakes | PEP8 规范、语法错误 |
| Java | Checkstyle / javac | 代码规范、编译错误 |
| Go | gofmt + go vet | 格式化、静态分析 |
| Rust | cargo clippy + rustfmt | 代码质量、格式化 |
| C/C++ | cppcheck | 内存泄漏、未初始化变量 |
| JavaScript | node --check | 语法错误 |

### 使用方式

```bash
# 单文件审查
python3 code_review.py src/main.py

# 目录审查（自动检测语言，递归所有源文件）
python3 code_review.py /home/jovyan/work/industrial-analytics/src/
python3 code_review.py /home/jovyan/work/mes-system/production-service/src/
python3 code_review.py /home/jovyan/work/industrial-gateway/
python3 code_review.py /home/jovyan/work/security-audit/
```

### 输出格式（JSON）

```json
{
  "language": "Python",
  "tool": "pycodestyle",
  "issues": ["src/main.py:10:1: E302 expected 2 blank lines"],
  "score": 85
}
```

### 评分规则

| 语言 | 每个问题扣分 | 满分 |
|------|-------------|------|
| Python | 100/总行数 | 100 |
| Java | 5分/问题 | 100 |
| Go | 10分/问题 | 100 |
| Rust | 5分/问题 | 100 |
| C/C++ | 5分/问题 | 100 |

---

## 20. 指南分发规则 (v2.1 新增)

| 用户类型 | 教师版指南 | 学生版指南 | 评分系统 | AI助手 |
|----------|-----------|-----------|----------|--------|
| teacher-zhang | ✅ | ✅ | ✅ | ✅ |
| Lecture-* (16个) | ✅ | ✅ | ✅ | ✅ |
| 学生（任何注册） | ❌ | ✅ | ✅ | ✅ |

---

## 21. CockroachDB K8s 部署确认 (v2.1 新增)

### 部署方式

CockroachDB 已从裸金属迁移到 K8s Pod 部署：

| 项目 | 旧（裸金属） | 新（K8s Pod） |
|------|-------------|--------------|
| 二进制路径 | /opt/cockroach/cockroach | /cockroach-binary/cockroach（容器内） |
| 数据路径 | /home/crdb-data/a | /cockroach/cockroach-data（hostPath） |
| systemd | cockroach-node1/2.service | StatefulSet |
| systemd 状态 | — | disabled + inactive (dead) |
| 管理方式 | systemctl | kubectl / Rancher |
| 网络模式 | 宿主机直接 | hostNetwork: true |

> **说明**：由于使用 `hostNetwork: true`，Pod 进程在宿主机 `ps aux` 中可见，
> 但实际运行在容器内（二进制路径为 `/cockroach-binary/`，非 `/opt/cockroach/`）。
> 旧 systemd 服务已 disable + stopped。

### 局域网连接（读写分离）

| 用途 | 地址 | 端口 |
|------|------|------|
| 写连接 | 10.167.2.175 | 26257 |
| 读连接 | 10.167.2.175 | 26267 |
| NodePort 写 | 10.167.2.175 | 30257 |
| NodePort 读 | 10.167.2.175 | 30267 |
| 管理界面 | http://10.167.2.175 | 30259 |
| K8s 内写 | cockroachdb.infra.svc | 26257 |
| K8s 内读 | cockroachdb-read.infra.svc | 26267 |

---

## 附注: HTTP 431 "Request Header Fields Too Large" 修复 (2026-09-07)

之前 JupyterHub 在多次登录/登出后可能出现 **HTTP 431 "Request Header Fields Too Large"** 错误，导致页面无法访问。

**根因**: Nginx 默认的头部缓冲区太小（默认 8k），无法容纳多次登录累积的 JupyterHub Cookie。

**解决方案**: 在 Nginx Ingress 中配置以下参数增大缓冲区：

| 配置项 | 值 |
|--------|-----|
| `large-client-header-buffers` | `4 32k` |
| `proxy-buffer-size` | `32k` |

**验证结果**（Playwright 浏览器测试）:

- Cookie 总大小仅 **293 字节**（3 个 Cookie）
- 3 次连续导航均返回 **HTTP 200**，无 431 错误

> **说明**: 这是平台级配置，学生无需自行处理。

---

## 22. 多教师同课程+班级关联体系 (v2.2 新增)

### 体系架构

```
teacher-zhang (总管理员)
├── 02-程序设计基础
│   ├── teacher-b1-01 → class-b1-01-A, class-b1-01-B
│   ├── teacher-b2-01 → class-b2-01-A
│   ├── teacher-b3-01 → class-b3-01-A
│   ├── teacher-b4-01 → class-b4-01-A
│   ├── teacher-b5-01 → class-b5-01-A
│   └── teacher-b6-01 → class-b6-01-A
├── 01-AI应用基础
│   ├── teacher-a1-01 → class-a1-01-A, class-a1-01-B
│   ├── teacher-a2-01 → class-a2-01-A
│   ├── teacher-a3-01 → class-a3-01-A
│   └── teacher-a4-01 → class-a4-01-A
└── 03-Python项目实战
    ├── teacher-p1-01 → class-p1-01-A, class-p1-01-B
    ├── teacher-p2-01 → class-p2-01-A
    ├── teacher-p3-01 → class-p3-01-A
    ├── teacher-p4-01 → class-p4-01-A
    ├── teacher-p5-01 → class-p5-01-A
    └── teacher-p6-01 → class-p6-01-A
```

### 同一课程多个教师

同一课程可以有多位教师同时授课，每位教师管理自己的班级：

| 课程 | 教师 | 负责班级 | 可管理学生 |
|------|------|----------|-----------|
| B1 (设备初始化) | teacher-b1-01 | class-b1-01-A, class-b1-01-B | A班+B班学生 |
| B1 (设备初始化) | teacher-b1-02 (新增) | class-b1-02-A | 新教师A班学生 |

> 教师使用 `https://10.167.2.175:31825/ide/hub/admin` 管理面板查看自己班级的学生。

### 学生登录格式

学生用户名格式: `{课程}-{班级}-{学号}`

| 格式 | 含义 | 关联教师 |
|------|------|----------|
| `b1-A-01` | 程序设计基础 B1 A班 01号 | teacher-b1-01 |
| `b1-B-05` | 程序设计基础 B1 B班 05号 | teacher-b1-01 |
| `a1-A-03` | AI应用基础 A1 A班 03号 | teacher-a1-01 |
| `p1-B-10` | Python项目实战 P1 B班 10号 | teacher-p1-01 |

### 教师管理学生流程

1. 教师登录 (`teacher-b1-01`, 密码 `ide2026`)
2. 访问管理面板: `https://10.167.2.175:31825/ide/hub/admin`
3. 查看自己班级的学生服务器状态
4. 启动/停止学生服务器
5. 使用 `code_grader.py` 评分学生代码

### 新增教师流程

1. 总管理员 `teacher-zhang` 在终端创建新教师:
   ```bash
   # 新教师登录即可自动创建 (密码 ide2026)
   # 然后在 hub pod 中将其加入对应课程组和班级组
   ```

2. 将新教师加入课程教师组和班级组（示例）:
   ```bash
   kubectl exec -n jupyterhub <hub-pod> -c jupyterhub -- python3 -c "
   import sqlite3
   conn = sqlite3.connect('/srv/jupyterhub/jupyterhub.sqlite')
   c = conn.cursor()
   # 创建教师
   c.execute('INSERT INTO users (name, admin) VALUES (?, 1)', ('teacher-b1-02',))
   # 加入课程教师组
   c.execute('SELECT id FROM groups WHERE name="course-b-teachers"')
   gid = c.fetchone()
   c.execute('SELECT id FROM users WHERE name="teacher-b1-02"')
   uid = c.fetchone()
   c.execute('INSERT INTO users_groups VALUES (?, ?)', (uid[0], gid[0]))
   # 创建新班级组
   c.execute('INSERT INTO groups (name) VALUES (?)', ('class-b1-02-A',))
   # 加入班级组
   c.execute('SELECT id FROM groups WHERE name="class-b1-02-A"')
   cg = c.fetchone()
   c.execute('INSERT INTO users_groups VALUES (?, ?)', (uid[0], cg[0]))
   conn.commit()
   "
   ```


---

## 23. OAuth 400 修复 + 测试报告 (v2.3)

### OAuth 400 修复
- 根因: Hub重启导致OAuth客户端丢失
- 修复: 清除stale oauth codes + 重新登录
- 验证: teacher-zhang登录成功

### 数据保留
- PVC Bound | 76 Notebook | 8 Code | 双指南 | 评分系统
- 结论: 零数据丢失

### LLM测试
- master: 59s | teacher pod: 28s | qwen2.5-coder:7b
- 瓶颈: CPU-only推理

### CRDB测试
- 3节点 Running | 27+数据库 | 读写分离

### 资源优化
- milvus/nebula/pulsar stopped | Worker CPU 79% -> 57%


---

## 24. nbgrader 原生作业系统 (v2.4 新增)

### 概述

JupyterHub 已安装 **nbgrader 0.9.5**，提供原生的作业分发、收集、自动评分和反馈功能，替代了之前的手动 code_grader.py。

### 教师操作流程

```bash
cd ~/work/nbgrader

# 1. 创建作业（在 source/ 目录下创建 Notebook）
#    在 JupyterLab 中使用 nbgrader 工具栏标记单元格类型:
#    - 答案区（Solution）: 学生需要填写的代码
#    - 测试区（Test）: assert 断言（自动评分用）
#    - 只读区（Read-only）: 题目描述

# 2. 生成学生版（自动去除解决方案）
python3 -m nbgrader generate_assignment ps1

# 3. 发布作业到 exchange
python3 -m nbgrader release_assignment ps1

# 4. 查看已发布的作业
python3 -m nbgrader list

# 5. 学生提交后，自动评分
python3 -m nbgrader autograde ps1

# 6. 生成反馈
python3 -m nbgrader generate_feedback ps1
python3 -m nbgrader release_feedback ps1

# 7. 导出成绩 CSV
python3 -m nbgrader export
```

### 学生操作流程

```bash
cd ~/work/nbgrader

# 1. 查看可用作业
python3 -m nbgrader list

# 2. 获取作业
python3 -m nbgrader fetch ps1

# 3. 完成作业后提交
python3 -m nbgrader submit ps1
```

### nbgrader 元数据要求

每个 nbgrader 单元格需要完整的 v3 元数据:
- `grade`: True/False（是否评分）
- `solution`: True/False（是否答案区）
- `task`: False
- `locked`: True/False（是否锁定）
- `points`: 浮点数（分值）
- `grade_id`: 唯一标识符
- `schema_version`: 3
- `cell_type`: "code"

### Exchange 目录

| 路径 | 说明 |
|------|------|
| `~/work/nbgrader/exchange/` | 共享交换目录 |
| `exchange/default/outbound/` | 教师发布的作业 |
| `exchange/default/inbound/` | 学生提交的作业 |

---

## 25. 多教师多课程账户体系 (v2.4 完整版)

### 完整对照表

```
teacher-zhang (总管理员, 密码: ide2026)
├── 02-程序设计基础
│   ├── Lecture-B1~B6 (原始管理员)
│   ├── teacher-b1-01 → class-b1-01-A, class-b1-01-B
│   ├── teacher-b2-01 → class-b2-01-A
│   ├── teacher-b3-01 → class-b3-01-A
│   ├── teacher-b4-01 → class-b4-01-A
│   ├── teacher-b5-01 → class-b5-01-A
│   └── teacher-b6-01 → class-b6-01-A
├── 01-AI应用基础
│   ├── Lecture-A1~A4
│   ├── teacher-a1-01 → class-a1-01-A, class-a1-01-B
│   ├── teacher-a2-01 → class-a2-01-A
│   ├── teacher-a3-01 → class-a3-01-A
│   └── teacher-a4-01 → class-a4-01-A
└── 03-Python项目实战
    ├── Lecture-P1~P6
    ├── teacher-p1-01 → class-p1-01-A, class-p1-01-B
    ├── teacher-p2-01 → class-p2-01-A
    ├── teacher-p3-01 → class-p3-01-A
    ├── teacher-p4-01 → class-p4-01-A
    ├── teacher-p5-01 → class-p5-01-A
    └── teacher-p6-01 → class-p6-01-A
```

### 学生登录格式

| 格式 | 含义 | 关联教师 |
|------|------|----------|
| `b1-A-01` | 程序设计基础 B1 A班 01号 | teacher-b1-01 |
| `a1-B-03` | AI应用基础 A1 B班 03号 | teacher-a1-01 |
| `p1-A-05` | Python项目实战 P1 A班 05号 | teacher-p1-01 |

### 账户总计

- 33 个教师/管理员账户
- 43 个分组
- 56 个 Notebook
- 28 个代码框架
- 3 门课程

---

## 26. 平台浏览器自动化测试验证 (v2.5 新增)

> **测试日期**: 2026-09-07 | **测试结果**: ✅ **24/24 项测试全部通过 (100%)**

### 测试概述

JupyterHub 平台已于 2026-09-07 完成 **Playwright 无头浏览器（Headless Chromium）自动化测试**，使用真实浏览器模拟用户操作，覆盖全部核心功能。

| 指标 | 数值 |
|------|------|
| 测试工具 | Playwright Headless Chromium v1.52.0 |
| 总测试用例数 | 24 |
| 通过数 | 24 |
| 失败数 | 0 |
| 通过率 | **100%** |

### 学生相关功能验证结果

以下学生日常使用的功能已全部通过自动化测试验证：

| 功能 | 状态 | 说明 |
|------|------|------|
| 学生登录 | ✅ 通过 | 输入用户名+密码后正确重定向到个人 JupyterLab |
| JupyterLab界面 | ✅ 通过 | 界面完整加载，顶部栏+启动器正常 |
| 文件访问 | ✅ 通过 | 文件浏览器可用，109个文件/目录可访问 |
| 指南分发 | ✅ 通过 | 学生账户自动获得学生指南（不含教师指南） |
| Python内核 | ✅ 通过 | python3 内核可用 |
| 终端服务 | ✅ 通过 | 终端 API 正常（status=200） |
| 并发登录 | ✅ 通过 | 10用户并发登录100%成功 |

> **总结**: 你使用的所有学生功能（登录、JupyterLab、文件访问、指南分发）均已通过真实浏览器自动化测试验证，可放心使用。完整测试报告见 `JUPYTERHUB-BROWSER-TEST-REPORT.md`。

---

## 27. 自动评测与成绩查询 (v2.6 新增)

> **测试结果**: ✅ **56/57 通过 (98%)** | PrairieLearn v2 Autograder

### 27.1 自动评测概述

JupyterHub 已集成 **PrairieLearn v2 Autograder**，你可以提交代码进行自动评分，评分结果持久化到 CockroachDB，可随时查询自己的成绩。

- 评测服务地址: `https://10.167.2.175:31825/grader/`
- 学生 API Key: `pl-student-2026`

### 27.2 提交代码评分

使用 `submit_grade.py` 脚本提交你的代码和测试代码进行评分：

```bash
# 基本用法
python3 submit_grade.py my_code.py test_code.py ps1

# 参数说明:
#   my_code.py     你的作业代码文件
#   test_code.py   测试代码文件
#   ps1            作业编号（如 ps1, ps2, p1.1 等）
```

脚本会自动:
1. 读取你的代码和测试代码
2. 调用 Autograder API 进行评分
3. 返回测试通过率、Lint 问题、最终分数
4. 将成绩写入 CockroachDB 持久化保存

### 27.3 查询自己的成绩

通过 API 查询自己的历史成绩：

```bash
curl -H "Authorization: Bearer pl-student-2026" \
     https://10.167.2.175:31825/grader/api/v2/scores
```

返回 JSON 包含: 作业编号、分数、测试通过率、Lint 问题数、提交时间。

### 27.4 评分维度

| 维度 | 说明 |
|------|------|
| 测试通过率 | pytest 测试用例通过百分比 |
| 代码风格 | PEP8 规范检查（pycodestyle） |
| 综合分数 | 0-100 分制 |

### 27.5 测试结果

| 指标 | 数值 |
|------|------|
| 全链路测试用例 | 57 |
| 通过 | 56 |
| 通过率 | **98%** |

> **提示**: 提交前先用 `python -m pytest tests/ -v` 本地验证测试通过，可提高评分通过率。详细 API 文档见 `AUTOGRADER-GUIDE.md`。

---

## 28. 完整平台使用指南 (v3.0)

> **版本**: 3.0 | **日期**: 2026-09-07 | **适用**: 全体学生
> **覆盖**: Open edX + JupyterHub + Code-Server + PrairieLearn + Ollama 全平台访问

### 28.1 全部访问地址（无需修改 hosts 文件）

| 服务 | 访问地址 | 账户 / 密码 |
|------|----------|-------------|
| Open edX LMS（在线课程） | https://openedx.10.167.2.175.nip.io:31825/ | 你的学号账户 |
| JupyterHub（实训IDE） | https://10.167.2.175:31825/ide/ | p1-你的名字 / ide2026 |
| Code-Server（VS Code） | http://10.167.2.175:30087/vscode/ | 你的JupyterHub账户 / Dify@2026 |
| PrairieLearn（自动评测） | https://10.167.2.175:31825/grader/ | API Key: pl-student-2026 |

> **说明**: Open edX 使用 `nip.io` 通配 DNS，浏览器直接打开即可，无需配置 hosts。你的账户已由教师导入 Open edX，首次登录请在 LMS 使用学号账户。

### 28.2 学生 API Key

```
pl-student-2026
```

用途：提交代码评分、查询自己的历史成绩。请求时放在 HTTP 头部：
```
Authorization: Bearer pl-student-2026
```

### 28.3 从 JupyterHub 提交代码评分

在 JupyterHub 终端中使用 `submit_grade.py`（已预装）提交作业：

```bash
# 基本用法
python3 submit_grade.py my_code.py test_code.py ps1

# 示例：提交 Python 工业遥测项目
python3 submit_grade.py src/industrial/api/routes.py tests/test_e2e_api.py python-industrial

# 参数说明:
#   my_code.py      你的作业代码文件
#   test_code.py    测试代码文件
#   python-industrial  作业编号（python-industrial / java-mes / go-gateway / rust-audit）
```

脚本会自动：1) 读取代码与测试 → 2) 调用 PrairieLearn API 评分 → 3) 返回测试通过率、Lint 问题、综合分数 → 4) 成绩写入 CockroachDB 持久化。

### 28.4 通过 PrairieLearn API 查询成绩

```bash
# 查询自己的所有历史成绩
curl -H "Authorization: Bearer pl-student-2026" \
     https://10.167.2.175:31825/grader/api/v2/scores
```

返回 JSON 包含：作业编号、分数、测试通过率、Lint 问题数、提交时间。也可在 PrairieLearn 网页端 `https://10.167.2.175:31825/grader/` 查看可视化报告。

### 28.5 测试结果

| 指标 | 数值 |
|------|------|
| 全链路测试用例 | 74 |
| 通过 | 74 |
| 通过率 | **100%** |

> **提示**: 提交前先用 `python -m pytest tests/ -v` 本地验证测试通过，可提高评分通过率。遇到问题先重启内核（Kernel → Restart Kernel），仍失败请联系授课教师。

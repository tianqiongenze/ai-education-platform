# Dify+Code-Server+JupyterLab AI 编程教学操作指南

> **适用对象**: 软件开发、AI应用、软件工程专业学生及教师  
> **平台**: Dify 1.14.2 + Code-Server 4.128.0 + JupyterLab 4.0.7 + 23个本地AI模型  
> **更新日期**: 2026-09-03  

---

## 第一章 平台概览

### 1.1 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Dify 控制台 | `https://10.167.2.175:31825` | AI应用管理(浏览器直接访问) |
| Dify API | `https://10.167.2.175:31825/v1` | 程序化调用 |
| Code-Server | `http://10.167.2.175:30087/vscode/` | 在线编程环境（IP直连，无需hosts） |
| JupyterLab | `http://10.167.2.175:30088/jupyter/` | Python科学计算（原生子路径，无需密码） |
| LiteLLM 网关 | `http://10.167.2.176:30083` | 26个AI模型代理 |
| Ollama | `http://10.167.2.176:30086` | 23个本地模型 |
| Redis 8 Cluster | `10.167.2.175:30090/30091/30092` | Redis 8.10.1 Cluster |

### 1.2 账号信息

#### 1.2.1 服务登录账号

| 服务 | 用户名 | 密码 |
|------|--------|------|
| Dify 控制台 | `myuwei@126.com` | `Difyai123456` |
| Code-Server | `http://10.167.2.175:30087/vscode/` | 密码 `Dify@2026`（Caddy代理，无需hosts） |
| JupyterHub 多租户 | `http://10.167.2.175:30089/ide/` | 密码 `ide2026`（多用户注册，每人独立工作空间5Gi，Python/Java/Go） |
| JupyterLab | `http://10.167.2.175:30088/jupyter/` | 无需密码（原生子路径，Python科学计算） |
| LiteLLM | — | `sk-ai-platform-master` |
| Redis 8 Cluster | — | `difyai123456` |
| Mailpit Web UI | 无需登录 | `http://10.167.2.175:30205` |
| Grafana | `admin` | `uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb` |
| Rancher | `admin` | `Rancher@2026` |

#### 1.2.2 Dify 账户角色体系（15 个账户，4 种角色）

所有账户属于工作空间 `Zheng_Gong's Workspace`，统一初始密码 `Difyai123456`。

| 角色 | 人数 | 权限说明 |
|------|------|---------|
| **owner** (所有者) | 1 | 工作空间最高权限：管理成员、应用、知识库、模型配置，可转移所有权 |
| **admin** (管理员) | 3 | 管理应用、知识库、成员（仅 editor/normal）、模型配置 |
| **editor** (编辑者) | 1 | 创建/编辑应用和知识库，不能管理成员和模型配置 |
| **normal** (普通用户) | 10 | 使用已发布的应用，不能创建或管理（适合学生） |

**完整账户清单**:

| 姓名 | 邮箱 | 角色 |
|------|------|------|
| Zheng_Gong | myuwei@126.com | owner |
| javanetongzheng | javanetongzheng@icloud.com | admin |
| test-0368414 | 0368414@sd.taylors.edu.my | admin |
| Test Invite User | invite-direct-test4@126.com | admin |
| joelgong | joelgong@aliyun.com | editor |
| javanetongzheng | javanetongzheng@aliyun.com | normal |
| javanetgongzheng | javanetgongzheng@icloud.com | normal |
| test_account | test_account@163.com | normal |
| myuwei | myuwei@163.com | normal |
| qiaoguiping | qiaoguiping@126.com | normal |
| sunxiaoting | sunxiaoting@126.com | normal |
| sunhaoling | sunhaoling@126.com | normal |
| weifeng | weifeng@126.com | normal |
| wangjing | wangjing@126.com | normal |
| weiwenkai | weiwenkai@126.com | normal |

> **教学建议**: 教师使用 owner/admin 账号创建应用和知识库，学生使用 normal 账号访问已发布的应用。学生通过应用对话即可触发知识库检索，无需直接管理知识库。

#### 1.2.3 知识库局域网访问方式

学生可通过三种方式使用知识库:

1. **Web 界面（推荐）**: 浏览器打开 `https://10.167.2.175:31825` → 使用学生账号登录 → 在工作室选择关联了知识库的应用 → 对话即可自动检索知识库内容
2. **API 调用**: 获取应用 API Key（需 owner/admin/editor 权限），调用 `POST https://10.167.2.175:31825/v1/chat-messages` 对话接口，AI 自动检索关联知识库
3. **知识库检索 API**: 直接调用 `POST https://10.167.2.175:31825/console/api/datasets/{id}/retrieve` 检索知识库内容（需 owner/admin/editor 权限）

**已关联知识库的应用**:

| 应用名称 | 关联知识库 | 使用方式 |
|---------|-----------|---------|
| 知识库 + 聊天机器人 | 工业互联网教学知识库 | 对话触发检索 |
| 工业互联网智能体 | 工业互联网教学知识库 | 对话触发检索 |
| PLC编程教学助手 | PLC编程教程知识库 | 对话触发检索 |
| Python编程教学助手 | Python编程教程知识库 | 对话触发检索 |
| Java编程教学助手 | Java编程教程知识库 | 对话触发检索 |
| 软件工程方法论助手 | 软件工程最佳实践知识库 | 对话触发检索 |
| 工业网络安全助手 | 工业安全标准知识库 | 对话触发检索 |

#### 1.2.4 Mailpit 邮件调试服务

Mailpit 提供 SMTP 邮件接收和 Web UI 查看，用于 Dify 平台的邮件功能测试（用户邀请、密码重置等）。

| 项目 | 地址 |
|------|------|
| Mailpit Web UI | `http://10.167.2.175:30205` |
| SMTP 内部地址 | `mailpit-smtp.dify.svc.cluster.local:1025` |

**用户邀请邮件流程**: Owner/Admin 在 Dify 控制台邀请新成员 → Dify 通过 Mailpit SMTP 发送邀请邮件 → 打开 `http://10.167.2.175:30205` 查看邮件 → 新成员点击链接设置密码注册。

### 1.3 Dify 已创建应用清单

#### 聊天助手 (10个)
| 应用名 | 用途 | 推荐模型 |
|--------|------|---------|
| 工业互联网基础助手 | 工业互联网概念问答 | glm4:9b |
| PLC编程教学助手 | PLC梯形图编程教学 | glm4:9b |
| 工业网络安全助手 | SCADA安全防护 | glm4:9b |
| MES系统顾问 | 制造执行系统咨询 | glm4:9b |
| 数字孪生设计助手 | 数字孪生架构设计 | qwen3:8b |
| 边缘计算优化助手 | 边缘部署方案 | qwen3:4b |
| 工业数据分析助手 | 工业数据分析 | qwen2.5-coder:7b |
| 传感器选型助手 | 传感器选型校准 | glm4:9b |
| Java编程教学助手 | Java编程教学 | qwen2.5-coder:7b |
| Python数据分析助手 | Python数据分析 | qwen2.5-coder:7b |

#### 工作流应用 (3个)
| 应用名 | 流程 | 推荐模型 |
|--------|------|---------|
| 工业设备故障诊断工作流 | 数据→异常检测→根因→维修建议 | qwen3:14b |
| 生产质量评估工作流 | 质检→标准对比→评级→改进 | qwen2.5-coder:7b |
| 代码质量分析工作流 | 代码→静态分析→安全扫描→评分 | qwen2.5-coder:7b |

#### Agent智能体 (3个)
| 应用名 | 能力 | 推荐模型 |
|--------|------|---------|
| 工业互联网智能体 | 知识库+代码执行+数据分析 | qwen3:8b |
| 编程作业评审智能体 | 代码质量+安全漏洞+评分报告 | qwen2.5-coder:7b |
| 软件架构评审智能体 | 架构评估+技术债+优化建议 | qwen3:14b |

#### 知识库 (7个)
| 知识库名 | 内容 | 嵌入模型 |
|---------|------|---------|
| 工业互联网教学知识库 | 工业互联网基础概念 | bge-m3 |
| PLC编程教程知识库 | 梯形图、功能块、结构化文本 | bge-m3 |
| 工业网络协议知识库 | Profinet、EtherCAT、Modbus | bge-m3 |
| 工业安全标准知识库 | IEC 62443、等保2.0 | bge-m3 |
| Python编程教程知识库 | Python基础、数据结构 | bge-m3 |
| Java编程教程知识库 | Java基础、Spring框架 | bge-m3 |
| 软件工程最佳实践知识库 | 设计模式、重构、TDD | bge-m3 |

---

## 第二章 AI 模型使用指南

### 2.1 模型分类与推荐

#### LLM 大语言模型 (19个)

| 模型 | 大小 | 速度 | 最优场景 | 使用建议 |
|------|------|------|---------|---------|
| **glm4:9b** | 5.5GB | ⚡7-13s | 中文教学/工业互联网/PLC | **教学首选**，中文理解最强 |
| **qwen2.5-coder:7b** | 4.7GB | ⚡3-31s | 编程辅导/代码生成 | **编程首选**，专为代码优化 |
| **qwen2.5-coder:14b** | 9GB | ⚡5-31s | 深度编程/算法 | 更大参数，代码质量更高 |
| llama3.1:8b | 4.9GB | ⚡10-28s | 通用教学(英文) | 平均最快(18.5s) |
| yi:6b | 3.5GB | ⏳15-44s | 中文通用 | 零一万物，中文能力强 |
| qwen3:4b | 2.5GB | ⏳10-30s | 快速问答 | thinking模式，推理质量好 |
| qwen3:8b | 5.2GB | ⏳30-90s | 深度教学 | thinking模式，通用教学 |
| qwen3:14b | 9.3GB | ⏳60-180s | 复杂分析 | thinking模式，深度推理 |
| qwen3:30b-a3b | 18GB | ⏳15-60s | 复杂工业场景 | MoE架构，高效推理 |
| qwen3:32b | 20GB | ⏳120-300s | 学术论文/科研 | 最深推理 |
| qwen2.5:7b | 4.7GB | ⚡3s | 快速问答 | 经典版 |
| qwen2.5:14b | 10GB | ⚡5s | 通用教学 | 经典版 |
| qwen2.5:72b | 47GB | ⏳60s+ | 旗舰模型 | 需要高质量输出 |
| deepseek-r1:7b | 4.7GB | ⏳10s | 深度推理 | R1系列 |
| deepseek-r1:14b | 9GB | ⏳20s | 复杂推理 | R1系列 |
| deepseek-r1:32b | 19GB | ⏳60s+ | 最深推理 | R1系列 |
| llama3.2-vision:11b | 7.8GB | ⏳15s | **图片理解(多模态)** | 支持图片输入 |
| tinyllama | 637MB | ⚡即时 | 极轻量测试 | 测试用 |

#### Embedding 嵌入模型 (4个)

| 模型 | 大小 | 维度 | 用途 |
|------|------|------|------|
| **bge-m3** | 1.2GB | 1024 | **知识库嵌入首选** |
| qwen3-embedding:0.6b | 639MB | 1024 | 轻量嵌入 |
| qwen3-embedding:4b | 2.5GB | 1024 | 高质量嵌入 |
| qwen3-embedding:8b | 4.7GB | 4096 | 最高质量嵌入 |
| nomic-embed-text | 274MB | 137 | 超轻量 |

#### 多模态能力

| 类型 | 支持情况 | 模型 | 说明 |
|------|---------|------|------|
| 图片理解 | ✅ 支持 | llama3.2-vision:11b | 支持图片输入+文字理解 |
| 音频理解 | ❌ 不支持 | — | Ollama不支持纯音频模型 |
| 视频理解 | ❌ 不支持 | — | Ollama不支持视频模型 |
| 代码补全 | ✅ 支持 | qwen2.5-coder:7b/14b | Code-Server Tab补全 |

> **多模态说明**: Ollama 目前不支持纯音频(如 Whisper)和视频模型。如需音频转文字功能，建议通过云端 API(如 OpenAI Whisper)实现。图片理解已由 `llama3.2-vision:11b` 支持。

### 2.2 模型调用方式

#### 通过 LiteLLM 网关调用 (推荐)

```bash
# 聊天
curl http://10.167.2.176:30083/v1/chat/completions \
  -H "Authorization: Bearer sk-ai-platform-master" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm4:9b","messages":[{"role":"user","content":"什么是PLC?"}],"max_tokens":100}'

# 嵌入
curl http://10.167.2.176:30083/v1/embeddings \
  -H "Authorization: Bearer sk-ai-platform-master" \
  -H "Content-Type: application/json" \
  -d '{"model":"bge-m3","input":"测试文本"}'
```

#### Python 调用示例

```python
import requests

LITELLM = "http://10.167.2.176:30083"
KEY = "sk-ai-platform-master"

# 聊天
r = requests.post(f"{LITELLM}/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={"model": "qwen2.5-coder:7b", "messages": [{"role": "user", "content": "写一个Python冒泡排序"}], "max_tokens": 200},
    timeout=120)
print(r.json()["choices"][0]["message"]["content"])

# 嵌入
r = requests.post(f"{LITELLM}/v1/embeddings",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={"model": "bge-m3", "input": "工业互联网"},
    timeout=30)
print(f"维度: {len(r.json()['data'][0]['embedding'])}")
```

#### Redis Cluster 连接

```python
from redis.cluster import RedisCluster

rc = RedisCluster(
    host='10.167.2.175', port=30090,
    password='difyai123456', decode_responses=True
)
rc.set('key', 'value')
print(rc.get('key'))
```

---

## 第三章 Code-Server AI 编程环境

### 3.1 访问方式

1. 配置 hosts: `10.167.2.175 code-server.ai-platform.local`
2. 浏览器访问: `https://code-server.ai-platform.local:31825`
3. 密码: `Dify@2026`

### 3.2 已安装插件 (52个)

#### AI 编程插件
| 插件 | 功能 |
|------|------|
| **continue.continue** | AI代码补全+对话+重构 (配置本地模型) |
| **anthropic.claude-code** | Claude AI编程助手 |
| **codeium.windsurf-cpptools** | C/C++智能补全 |
| **kilocode.kilo-code** | AI代码生成 |

#### 多语言支持
| 语言 | 插件 |
|------|------|
| Java | redhat.java + vscjava全套(debug/test/maven/gradle) |
| Go | golang.go + ms-vscode.go |
| Rust | rust-lang.rust-analyzer |
| Python | ms-python.python + debugpy + magicpython |
| C/C++ | ms-vscode.cpptools + cmake + clangd |
| Docker | ms-azuretools.vscode-containers |

### 3.3 Continue.dev 配置

Continue.dev 已配置使用本地 LiteLLM 网关的 AI 模型:

- **Tab 补全**: qwen2.5-coder:14b (编程专用)
- **对话模型**: qwen2.5:7b/14b/32b/72b, qwen2.5-coder:7b/14b
- **推理模型**: deepseek-r1:14b/32b
- **API 地址**: `http://litellm.ai-platform.svc.cluster.local:4000/v1`

### 3.4 使用方式

1. 在 Code-Server 中打开项目
2. 按 `Ctrl+Shift+P` → 输入 "Continue" 打开 AI 面板
3. 选中代码 → 右键 → "Continue: Explain" / "Refactor" / "Generate Tests"
4. Tab 键自动补全代码

---

## 第四章 Code-Server 编程作业自动评分方案

### 4.1 评分架构设计

```
学生提交代码 → Code-Server 收集 → 评分流程:
  ├─ 1. 自动化测试 (pytest/JUnit/go test)
  ├─ 2. 代码规范检查 (ESLint/Pylint/golangci-lint)
  ├─ 3. AI 代码质量评估 (Continue.dev + qwen2.5-coder:7b)
  ├─ 4. 安全漏洞扫描 (Dify工作流: 代码质量分析工作流)
  └─ 5. 评分报告生成 (Dify Agent: 编程作业评审智能体)
```

### 4.2 部署方案

#### 方案1: Dify 工作流自动评分 (已部署)

已在 Dify 中创建"代码质量分析工作流"和"编程作业评审智能体":

1. 教师在 Dify 中打开"代码质量分析工作流"
2. 输入学生代码文本
3. 工作流自动执行: 代码分析 → 安全扫描 → 质量评估 → 生成评分
4. 输出评分报告

#### 方案2: Code-Server 内置 AI 评分 (Continue.dev)

1. 教师在 Code-Server 中打开学生代码文件
2. 选中全部代码 → Ctrl+Shift+P → "Continue: Explain"
3. AI 自动分析代码质量、逻辑错误、安全漏洞
4. 教师根据 AI 反馈手动评分

#### 方案3: 自动化测试评分

1. 在 Code-Server 中安装测试框架
2. 为每个作业创建测试用例文件
3. 学生提交后运行测试: `pytest test_assignment.py`
4. 根据通过率自动计算分数

### 4.3 测试评分示例

```python
# test_student_code.py - Python作业自动测试
import pytest
import subprocess

def test_bubble_sort():
    """测试学生提交的冒泡排序"""
    from student_code import bubble_sort
    assert bubble_sort([64, 34, 25, 12, 22]) == [12, 22, 25, 34, 64]
    assert bubble_sort([]) == []
    assert bubble_sort([1]) == [1]

def test_code_style():
    """代码规范检查"""
    result = subprocess.run(['pylint', 'student_code.py'], capture_output=True)
    score = int(result.stdout.decode().split('rated at ')[1].split('/')[0]) if 'rated at' in result.stdout.decode() else 0
    assert score >= 6.0  # 至少6分(满分10)
```

---

## 第五章 Dify 平台使用指南

### 5.1 创建聊天应用

1. 登录 Dify → 工作室 → 创建空白应用 → 聊天助手
2. 填写名称、描述、图标
3. 在编排页面选择模型 (推荐 glm4:9b 或 qwen2.5-coder:7b)
4. 设置提示词模板
5. 发布应用

### 5.2 创建知识库

1. 知识库 → 创建知识库
2. 填写名称、描述
3. 选择嵌入模型 (推荐 bge-m3)
4. 上传文档 (文本/文件)
5. 等待索引完成
6. 检索测试

### 5.3 创建工作流

1. 工作室 → 创建空白应用 → 工作流
2. 拖拽节点: Start → LLM → 条件分支 → 输出
3. 配置每个节点的模型和参数
4. 发布并测试

### 5.4 创建 Agent

1. 工作室 → 创建空白应用 → 高级聊天
2. 配置工具: 知识库检索、代码执行、搜索
3. 选择模型 (推荐 qwen3:8b)
4. 设置系统提示词
5. 发布

---

## 第六章 8层 Patch 详细说明 (可移植镜像)

### 6.1 问题背景

Dify 1.14.2 存在 `model_schema: null` 问题: 当插件 daemon 对自定义模型(如 openai_api_compatible)返回 null schema 时, Dify API 抛出 ValueError 导致 400 错误, 所有聊天/工作流/Agent 功能不可用。

### 6.2 8层修复方案

已将所有修复打包进镜像 `10.100.135.132:5000/dify-api:1.14.2-patched`:

| 层级 | 文件 | 问题 | 修复 |
|------|------|------|------|
| 1 | `plugin_daemon.py` | `model_schema` 字段类型不允许 null | 改为 `AIModelEntity | None` (Optional) |
| 2 | `model.py` (impl) | `resp.model_schema` 返回 None 时无 fallback | 添加 fallback `AIModelEntity` 创建 |
| 3 | `model_runtime.py` | `schema = self.client.get_model_schema(...)` 返回 None | 添加 fallback |
| 4 | `ai_model.py` | `.venv` 中的模型运行时基类无 fallback | 添加 fallback |
| 5 | `model_manager.py` | `get_model_schema()` 返回 None 时抛 ValueError | 添加 fallback |
| 6 | `converter.py` | `if not model_schema: raise ValueError` | 创建 fallback schema |
| 7 | `model_access.py` | `if model_schema is None: raise` | 创建 fallback |
| 8 | `plugin.py` | 实体类 `model_schema` 类型不兼容 | 改为 Optional |

### 6.3 镜像使用

```bash
# 拉取已打包patch的镜像
docker pull 10.100.135.132:5000/dify-api:1.14.2-patched

# 在其他K8s集群中使用
kubectl set image deploy/dify-api -n dify \
  api=10.100.135.132:5000/dify-api:1.14.2-patched

# 同时需要更新dify-worker
kubectl set image deploy/dify-worker -n dify \
  worker=10.100.135.132:5000/dify-api:1.14.2-patched
```

---

## 第七章 软件工程各阶段 AI 辅助

### 7.1 需求分析阶段

| 工具 | 用途 | 模型 |
|------|------|------|
| Dify 聊天 | 需求拆解、用户故事生成 | glm4:9b |
| 知识库 | 行业标准检索 | bge-m3 |

### 7.2 设计阶段

| 工具 | 用途 | 模型 |
|------|------|------|
| Dify Agent | 架构模式评估、技术选型 | qwen3:14b |
| Code-Server | UML/架构图生成 | qwen2.5-coder:7b |

### 7.3 编码阶段

| 工具 | 用途 | 模型 |
|------|------|------|
| Code-Server + Continue.dev | 代码补全、重构、解释 | qwen2.5-coder:7b/14b |
| Dify 聊天 | 编程问题答疑 | glm4:9b |
| 知识库 | 编程教程检索 | bge-m3 |

### 7.4 测试阶段

| 工具 | 用途 | 模型 |
|------|------|------|
| Code-Server | 单元测试生成 | qwen2.5-coder:7b |
| Dify 工作流 | 代码质量分析 | qwen2.5-coder:7b |
| pytest/JUnit | 自动化测试 | — |

### 7.5 评审阶段

| 工具 | 用途 | 模型 |
|------|------|------|
| Dify Agent (编程作业评审) | 代码质量+安全+评分 | qwen2.5-coder:7b |
| Dify Agent (架构评审) | 架构评估+技术债 | qwen3:14b |
| Code-Server + Claude Code | 实时代码审查 | qwen2.5-coder:7b |

---

## 附录: Redis Cluster 连接方式

### Redis 8.10.1 Cluster (3主节点)

| 节点 | NodePort | 槽位范围 |
|------|---------|---------|
| Node 0 | 10.167.2.175:30090 | 0-5460 |
| Node 1 | 10.167.2.175:30091 | 5461-10922 |
| Node 2 | 10.167.2.175:30092 | 10923-16383 |

密码: `difyai123456` (无用户名)

```bash
redis-cli -h 10.167.2.175 -p 30090 -a difyai123456 -c SET key value
redis-cli -h 10.167.2.175 -p 30090 -a difyai123456 -c GET key
```

```python
from redis.cluster import RedisCluster
rc = RedisCluster(host='10.167.2.175', port=30090, password='difyai123456')
rc.set('key', 'value')
```

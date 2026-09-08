# Dify AI 教学平台 — 人工测试操作指南

> **生成时间**: 2026-09-03  
> **集群节点**: Master: 10.167.2.175, Worker: 10.167.2.176  
> **Dify 版本**: 1.14.2  
> **状态**: ✅ 全功能可用

---

## 目录

- [第一章 环境准备](#第一章-环境准备)
- [第二章 教师创建 AI 教学应用](#第二章-教师创建-ai-教学应用)
- [第三章 学生使用 AI 助手](#第三章-学生使用-ai-助手)
- [第四章 知识库管理](#第四章-知识库管理)
- [第五章 工作流应用](#第五章-工作流应用)
- [第六章 对话管理](#第六章-对话管理)
- [第七章 Agent 智能助手](#第七章-agent-智能助手)
- [第八章 监控与运维](#第八章-监控与运维)
- [第九章 故障排除](#第九章-故障排除)
- [附录 A：API 端点速查表](#附录-aapi-端点速查表)
- [附录 B：服务访问地址汇总](#附录-b服务访问地址汇总)
- [附录 C：测试账号清单](#附录-c测试账号清单)

---

## 第一章 环境准备

### 1.1 访问地址

> **注意**: 本指南所有地址均使用 IP + 端口直连方式，**无需配置 hosts 文件**。

| 服务 | 地址 | 说明 |
|------|------|------|
| Dify 控制台 | `https://10.167.2.175:31825` | 浏览器直接访问（IP直连，无需hosts，完整API链路正常） |
| Dify API | `https://10.167.2.175:31825/v1` | 程序化调用（IP直连可用） |
| LiteLLM 网关 | `http://10.167.2.176:30083` | LLM 模型代理（26个模型，支持fallback故障切换） |
| Ollama | `http://10.167.2.176:30086` | 本地模型服务（24个模型） |
| Redis 8 Cluster | `10.167.2.175:30090/30091/30092` | Redis 8.10.1 Cluster（3主节点，局域网无MOVED） |
| Code-Server | `http://10.167.2.175:30087/vscode/` | 浏览器直接访问（IP直连，Caddy反向代理strip_prefix，无需hosts） |
| JupyterHub 多租户 | `http://10.167.2.175:30089/ide/` | 多用户注册登录（任意用户名+密码ide2026，每人独立工作空间） |
| JupyterLab | `http://10.167.2.175:30088/jupyter/` | 浏览器直接访问（原生子路径，无需hosts，无需密码） |
| Grafana 监控 | `http://10.167.2.175:30082` | 监控面板（33个仪表盘） |
| Rancher 管理 | `https://10.167.2.175` | K8s 集群管理（2个集群：local + dify-cluster） |

### 1.2 访问方式说明

**浏览器直接访问（无需任何配置）**:
- **Dify 控制台**: 直接打开 `https://10.167.2.175:31825`，自动显示登录页面，登录后完整功能可用 ✅
- **Grafana**: 直接打开 `http://10.167.2.175:30082`
- **Rancher**: 直接打开 `https://10.167.2.175`
- **LiteLLM**: 直接打开 `http://10.167.2.176:30083/health/liveliness`
- **Ollama**: 直接打开 `http://10.167.2.176:30086/api/tags`

**Code-Server 访问（无需 hosts 配置，直接 IP 访问）**:
- **Code-Server**: 直接打开 `http://10.167.2.175:30087/vscode/`
- 密码: `Dify@2026`
- 已安装 53 个扩展插件，支持 Java/Go/Rust/Python/C 等多语言 AI 编程
- 通过 Caddy 反向代理 strip_prefix 实现，Caddy 自动去除 /vscode 前缀后转发到 code-server:8080
- 原生支持 WebSocket 升级，编辑器/终端/扩展均正常工作
- 也支持 worker node 访问: `http://10.167.2.176:30087/vscode/`

**JupyterLab 访问（无需 hosts 配置，无需密码）**:
- **JupyterLab**: 直接打开 `http://10.167.2.175:30088/jupyter/`
- 原生支持子路径部署（`base_url=/jupyter/`），无需反向代理
- 内置 Python 3 科学计算环境（NumPy、Pandas、Matplotlib、Scikit-learn 等）
- 支持终端、文件管理、Git 集成
- 也支持 worker node 访问: `http://10.167.2.176:30088/jupyter/`

**Dify 控制台与 Code-Server 的区别**:
- Dify 控制台是 AI 应用管理平台（创建应用、配置模型、管理知识库）— IP 直连即可
- Code-Server 是在线 VS Code 编程环境（编写代码、AI 辅助编程）— IP 直连 `http://10.167.2.175:30087/vscode/`
- IP 直连 `https://10.167.2.175:31825` 默认进入 Dify 控制台
- JupyterLab 是 Python 科学计算环境 — IP 直连 `http://10.167.2.175:30088/jupyter/`

### 1.3 登录账号

| 服务 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| Dify 控制台 | `myuwei@126.com` | `Difyai123456` | 管理员，拥有全部权限 |
| Code-Server | — | `Dify@2026` | 在线编程环境密码 |
| Grafana | `admin` | `uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb` | 监控面板 |
| Rancher | `admin` | `Rancher@2026` | K8s 集群管理（local + dify-cluster） |
| LiteLLM 网关 | — | `sk-ai-platform-master` | API Key（无需用户名） |
| Redis 8 Cluster | — | `difyai123456` | 无用户名（NodePort 30090/30091/30092） |

### 1.4 浏览器要求

- Chrome 90+ / Edge 90+ / Firefox 88+
- 需接受自签名 SSL 证书（首次访问点击"高级"→"继续前往"）
- 建议分辨率 1920×1080 或更高

### 1.5 首次登录

1. 打开浏览器，访问 `https://console.dify-plus.local:31825`
2. 浏览器提示证书不安全，点击 **高级** → **继续前往**
3. 在登录页面输入邮箱 `myuwei@126.com` 和密码 `Difyai123456`
4. 点击 **登录**，进入 Dify 控制台

**预期结果**: ✅ 成功进入 Dify 控制台首页，显示工作空间和应用列表

---

## 第二章 教师创建 AI 教学应用

### 2.1 创建"课堂问答助手"应用

1. 登录 Dify 控制台
2. 点击左侧导航栏 **工作室**
3. 点击 **创建空白应用**
4. 选择应用类型：**聊天助手**（Chatbot）
5. 填写应用信息：
   - 应用名称: `课堂问答助手`
   - 应用描述: `面向高职学生的课堂即时问答AI助手`
   - 图标: 选择 📚
6. 点击 **创建**

**预期结果**: ✅ 应用创建成功，进入应用编排页面

### 2.2 配置模型

1. 在应用编排页面，找到 **模型** 设置区域
2. 点击模型选择器，选择：
   - 提供商: **OpenAI-API-compatible**
   - 模型: **qwen2.5:7b**（快速响应）或 **qwen2.5-coder:14b**（编程教学）
3. 确认模型状态为 ✅ **可用**

**预期结果**: ✅ 模型选择成功，显示模型参数配置（Temperature、Max Tokens 等）

### 2.3 设置提示词模板

在 **编排** 页面的提示词框中输入：

```
你是一位高职学院的教师助手，擅长回答学生在课堂上的各种问题。
请用简洁、准确、易懂的语言回答学生的问题。
如果问题涉及编程，请提供代码示例。
回答时请使用中文。
```

**预期结果**: ✅ 提示词保存成功

### 2.4 获取 API Key

1. 点击应用页面顶部的 **API 访问** 标签
2. 在 API Key 管理页面，点击 **创建 API Key**
3. 复制生成的 API Key（格式: `app-xxxxxxxxxxxxxxxx`）

**预期结果**: ✅ 获得 API Key，可用于程序化调用

### 2.5 发布应用

1. 点击页面右上角的 **发布** 按钮
2. 确认发布

**预期结果**: ✅ 应用状态变为"已发布"，可通过 API 和 Web 访问

---

## 第三章 学生使用 AI 助手

### 3.1 访问应用

1. 在应用详情页，点击 **访问预览** 或获取应用访问链接
2. 学生在浏览器中打开链接

**预期结果**: ✅ 显示聊天界面，可输入问题

### 3.2 发送问题（阻塞模式）

1. 在聊天框中输入: `你好，请用一句话介绍你自己`
2. 点击 **发送** 或按 Enter
3. 等待 AI 回复

**预期结果**: ✅ AI 返回完整回复，如"你好！我是课堂问答助手..."

### 3.3 流式问答体验

1. 在应用设置中确认 `response_mode` 为 `streaming`（或使用 API 调用时指定）
2. 输入问题: `什么是二叉树？请简要说明`
3. 观察 AI 回复逐字流式输出

**预期结果**: ✅ 回复以打字机效果逐字显示

### 3.4 多轮对话（追问）

1. 第一轮提问: `Python 中列表怎么排序？`
2. 等待回复后，第二轮提问: `能举个降序的例子吗？`
3. 观察 AI 是否记住了第一轮的上下文

**预期结果**: ✅ AI 在第二轮回答中引用了列表排序的上下文，给出降序示例

### 3.5 上传文件提问

1. 在聊天界面点击 **文件上传** 按钮（📎 图标）
2. 选择一个 `.py` 代码文件或 `.txt` 文本文件上传
3. 输入问题: `请分析我上传的代码，指出其中的问题`
4. 发送

**预期结果**: ✅ AI 能读取上传文件内容并给出分析

---

## 第四章 知识库管理

### 4.1 创建知识库

1. 在控制台左侧导航，点击 **知识库**
2. 点击 **创建知识库**
3. 填写信息：
   - 名称: `Python 编程教学知识库`
   - 描述: `高职 Python 编程课程教学资料`
   - 嵌入模型: **bge-m3**
4. 点击 **创建**

**预期结果**: ✅ 知识库创建成功，进入文档管理页面

### 4.2 上传教学文档

**方式一：文本上传**

1. 点击 **添加文档** → **文本方式**
2. 输入文档名称: `Python 变量与数据类型.txt`
3. 在文本框中粘贴教学内容
4. 分段规则选择 **自动**
5. 点击 **保存并处理**

**方式二：文件上传**

1. 点击 **添加文档** → **文件方式**
2. 拖拽或选择 `.pdf`、`.docx`、`.txt`、`.md` 文件
3. 选择分段规则
4. 点击 **上传并处理**

**预期结果**: ✅ 文档开始索引处理，状态显示"处理中"

### 4.3 查看索引状态

1. 在知识库文档列表中，查看文档的 **状态** 列
2. 等待状态从"处理中"变为"已完成"
3. 查看分段数量

**预期结果**: ✅ 文档状态为"已完成"，显示分段数

### 4.4 检索测试

1. 在知识库页面，点击 **检索测试**
2. 输入测试查询: `Python 变量怎么定义`
3. 点击 **检索**
4. 查看返回的相关分段

**预期结果**: ✅ 返回与查询相关的文档分段，显示相似度分数

### 4.5 在应用中关联知识库

1. 进入聊天应用编排页面
2. 在 **上下文** 设置区域，点击 **添加**
3. 选择已创建的知识库
4. 保存设置并发布

**预期结果**: ✅ 应用关联了知识库，回答时会检索知识库内容

---

## 第五章 工作流应用

### 5.1 查看现有工作流应用

1. 在控制台 **工作室** 页面
2. 筛选应用模式为 **工作流**（Workflow）
3. 查看现有工作流应用列表

**预期结果**: ✅ 显示工作流类型应用，如"文本情感分析工作流"

### 5.2 执行文本情感分析工作流

**通过 Web 界面**:

1. 点击工作流应用进入详情
2. 点击 **运行** 按钮
3. 在输入框中输入学生评课文本: `老师讲课很认真，内容丰富，受益匪浅`
4. 点击 **开始运行**
5. 查看工作流执行结果

**预期结果**: ✅ 工作流执行完成，输出情感分析结果（如"正面情感"）

**通过 API 调用**:

```bash
curl -X POST 'https://api.dify-plus.local:31825/v1/workflows/run' \
  -H 'Authorization: Bearer app-YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {"text": "老师讲课很认真，内容丰富，受益匪浅"},
    "response_mode": "blocking",
    "user": "teacher-001"
  }'
```

### 5.3 查看工作流运行历史

1. 在工作流应用页面，点击 **运行历史**
2. 查看历史运行记录
3. 点击某条记录查看详细执行路径

**预期结果**: ✅ 显示运行历史列表，可查看每个节点的执行详情

### 5.4 教学评估自动化场景

**场景**: 教师输入学生作业文本，工作流自动分析作业质量

1. 选择一个工作流应用
2. 输入学生作业文本
3. 工作流执行：文本分析 → 评分 → 生成评语
4. 查看输出结果

**预期结果**: ✅ 工作流输出评分和评语

---

## 第六章 对话管理

### 6.1 查看对话列表

1. 在聊天应用详情页，点击 **会话** 或通过 API 获取
2. 查看所有对话列表

**预期结果**: ✅ 显示对话列表，包含对话名称、时间、消息数

### 6.2 查看对话详情

1. 在对话列表中点击某条对话
2. 查看完整的对话消息历史

**预期结果**: ✅ 显示该对话的所有消息记录

### 6.3 重命名对话

1. 在对话列表中，将鼠标悬停在对话名称上
2. 点击 **重命名** 图标
3. 输入新名称: `重点学生-张三-编程辅导`
4. 保存

**预期结果**: ✅ 对话名称更新成功

### 6.4 消息反馈（点赞/点踩）

1. 在对话详情中，每条 AI 回复下方有 👍 和 👎 按钮
2. 点击 👍 表示回答质量好
3. 点击 👎 表示回答质量差

**预期结果**: ✅ 反馈状态更新，可用于后续分析

### 6.5 导出对话记录

通过 API 导出对话:

```bash
curl -X GET 'https://api.dify-plus.local:31825/v1/messages?user=student-001&limit=100' \
  -H 'Authorization: Bearer app-YOUR_API_KEY'
```

**预期结果**: ✅ 返回 JSON 格式的消息记录

---

## 第七章 Agent 智能助手

### 7.1 访问高级聊天应用

1. 在控制台 **工作室** 页面
2. 筛选应用模式为 **高级聊天**（Advanced Chat）或 **Agent**
3. 选择一个应用，如"研发面试超级助手"或"智能法律助手"

**预期结果**: ✅ 显示高级聊天应用列表

### 7.2 复杂问题对话

1. 进入应用对话界面
2. 输入复杂问题: `请帮我分析一下劳动合同中常见的法律风险，并提供防范建议`
3. 等待 Agent 思考和回复

**预期结果**: ✅ Agent 返回结构化、详细的回答，可能包含工具调用

### 7.3 工具调用验证

1. 在应用详情页，查看 **工具** 配置
2. 确认应用配置了工具（如搜索、知识库检索等）
3. 提问一个需要工具调用的问题
4. 在控制台查看 Agent 日志

**预期结果**: ✅ Agent 日志显示工具调用过程

---

## 第八章 监控与运维

### 8.1 Grafana 监控面板访问

1. 打开浏览器访问 `http://10.167.2.175:30082`
2. 使用默认账号登录（admin / prom-operator）
3. 查看监控仪表盘

**预期结果**: ✅ Grafana 显示集群监控数据

### 8.2 查看模型调用统计

1. 在 Grafana 中选择 **Dify Platform** 仪表盘
2. 查看 LLM 模型调用次数、响应时间、Token 消耗

**预期结果**: ✅ 显示模型调用趋势图

### 8.3 查看系统资源使用

1. 在 Grafana 中选择 **Infrastructure** 仪表盘
2. 查看 CPU、内存、磁盘使用率
3. 关注 Worker 节点（128GB RAM，运行大模型）

**预期结果**: ✅ 显示两节点资源使用情况

### 8.4 LiteLLM 网关状态检查

```bash
# 检查网关健康
curl http://10.167.2.176:30083/health/liveliness
# 预期返回: "I'm alive!"

# 检查就绪状态
curl http://10.167.2.176:30083/health/readiness
# 预期返回: 200 OK

# 查看模型列表
curl http://10.167.2.176:30083/v1/models \
  -H "Authorization: Bearer sk-ai-platform-master"
```

**预期结果**: ✅ 网关健康，13 个模型可用

---

## 第九章 故障排除

### 9.1 登录失败

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 页面无法打开 | hosts 未配置 | 参见 1.2 配置 hosts |
| 证书不安全 | 自签名证书 | 点击"高级"→"继续前往" |
| 密码错误 | 密码已修改 | 联系管理员重置为 `Difyai123456` |
| 401 Unauthorized | CSRF 令牌缺失 | 清除浏览器缓存重新登录 |

### 9.2 聊天无响应

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 400 model_schema null | 模型未配置 | 参见 2.2 配置模型 |
| 400 endpoint_url | 凭据缺失 | 重新配置模型凭据 |
| 500 Internal Error | 模型推理失败 | 检查 LiteLLM 和 Ollama 状态 |
| 504 Gateway Timeout | 模型推理超时 | 使用更小的模型（qwen2.5:7b） |

### 9.3 模型超时处理

**问题**: 大模型（qwen2.5:72b）首次调用需要 60-120 秒冷启动

**解决方案**:
1. 使用更快的模型: `qwen2.5:7b`（3秒响应）
2. 预热模型: 先用 LiteLLM 直接调用一次
3. 设置 `OLLAMA_KEEP_ALIVE=24h` 保持模型常驻内存

### 9.4 知识库检索失败

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 检索返回空 | 文档未索引完成 | 等待索引状态变为"已完成" |
| 404 Not Found | API 路径变更 | 使用 Dify 1.14 正确路径 |
| 嵌入失败 | bge-m3 模型不可用 | 检查 LiteLLM 嵌入端点 |

### 9.5 常见错误码对照表

| HTTP 状态码 | 含义 | 常见场景 |
|------------|------|---------|
| 200 | 成功 | 正常请求 |
| 400 | 参数错误 | 缺少必填字段、模型未配置 |
| 401 | 未授权 | CSRF 缺失、API Key 无效 |
| 404 | 不存在 | API 路径错误 |
| 500 | 服务器内部错误 | 模型推理失败 |
| 503 | 服务不可用 | Pod 正在启动 |
| 504 | 网关超时 | 模型推理超时 |

---

## 附录 A：API 端点速查表

### 控制台 API（需 Session + CSRF）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/console/api/login` | 登录 |
| GET | `/console/api/account/profile` | 用户资料 |
| GET | `/console/api/workspaces` | 工作空间 |
| GET | `/console/api/apps` | 应用列表 |
| POST | `/console/api/apps` | 创建应用 |
| GET | `/console/api/apps/{id}` | 应用详情 |
| GET | `/console/api/apps/{id}/api-keys` | 获取 API Key |
| POST | `/console/api/apps/{id}/api-keys` | 创建 API Key |
| GET | `/console/api/apps/{id}/workflows/draft` | 工作流草稿 |
| GET | `/console/api/datasets` | 知识库列表 |
| POST | `/console/api/datasets` | 创建知识库 |
| POST | `/console/api/datasets/{id}/document/create-by-text` | 上传文本文档 |
| GET | `/console/api/datasets/{id}/documents` | 文档列表 |
| POST | `/console/api/datasets/{id}/hit-testing` | 检索测试 |
| GET | `/console/api/workspaces/current/model-providers` | 模型提供商 |
| POST | `/console/api/files/upload` | 文件上传 |

### 服务 API（需 Bearer Token）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/v1/chat-messages` | 发送聊天消息 |
| POST | `/v1/completion-messages` | 发送补全消息 |
| GET | `/v1/conversations` | 对话列表 |
| GET | `/v1/messages` | 消息历史 |
| POST | `/v1/messages/{id}/feedbacks` | 消息反馈 |
| POST | `/v1/files/upload` | 上传文件 |
| POST | `/v1/workflows/run` | 执行工作流 |
| GET | `/v1/workflows/run/{run_id}` | 工作流运行结果 |
| GET | `/v1/parameters` | 应用参数 |

---

## 附录 B：服务访问地址汇总

| 服务 | 地址 | 端口 | 用途 |
|------|------|------|------|
| Dify Console | https://10.167.2.175 | 31825 | AI 应用管理 |
| Dify API | https://10.167.2.175 | 31825 | 程序化调用 |
| LiteLLM | http://10.167.2.176 | 30083 | LLM 网关 |
| Ollama | http://10.167.2.176 | 30086 | 本地模型 |
| Code-Server | http://10.167.2.175 | 30087 | 在线编程（/vscode/路径，Caddy代理） |
| JupyterLab | http://10.167.2.175 | 30088 | Python科学计算（/jupyter/原生子路径） |
| Grafana | http://10.167.2.175 | 30082 | 监控面板 |
| Rancher | https://10.167.2.175 | 443 | K8s 管理（local+dify-cluster） |
| 本地 Registry | http://10.100.135.132 | 5000 | 镜像仓库 |
| Redis 8 Cluster | 10.167.2.175 | 30090/30091/30092 | Redis 8.10.1 Cluster (3主节点) |

---

## 附录 D：Redis 8 Cluster 详细信息

### D.1 集群概览

| 项目 | 值 |
|------|-----|
| Redis 版本 | **8.10.1** |
| 部署模式 | Cluster（3主节点，无副本） |
| 集群状态 | `cluster_state:ok` |
| 槽位分配 | 16384/16384 全覆盖 |
| 集群大小 | 3 节点 |
| 密码认证 | `difyai123456`（无用户名） |
| 最大内存 | 256MB/节点 |
| 淘汰策略 | allkeys-lru |

### D.2 节点信息

| 节点 | Pod IP | 端口 | Bus端口 | 槽位范围 | 角色 |
|------|--------|------|---------|---------|------|
| Node 0 (redis8-0) | 192.168.235.216 | 6379 | 16379 | 0-5460 | Master |
| Node 1 (redis8-1) | 192.168.235.203 | 6379 | 16379 | 5461-10922 | Master |
| Node 2 (redis8-2) | 192.168.235.198 | 6379 | 16379 | 10923-16383 | Master |

### D.3 局域网访问方式

**NodePort 访问**（局域网任意机器可用）:
```
主机: 10.167.2.175
端口: 30095
密码: difyai123456
```

**命令行连接测试**:
```bash
# 安装 redis-cli（如未安装）
# CentOS: yum install redis
# Ubuntu: apt install redis-tools

# 连接测试
redis-cli -h 10.167.2.175 -p 30095 -a difyai123456

# 在 Cluster 模式下操作（需加 -c 参数自动跳转节点）
redis-cli -h 10.167.2.175 -p 30095 -a difyai123456 -c SET mykey "hello"
redis-cli -h 10.167.2.175 -p 30095 -a difyai123456 -c GET mykey

# 查看集群状态
redis-cli -h 10.167.2.175 -p 30095 -a difyai123456 CLUSTER INFO

# 查看集群节点
redis-cli -h 10.167.2.175 -p 30095 -a difyai123456 CLUSTER NODES
```

**Python 连接示例**:
```python
from redis.cluster import RedisCluster

rc = RedisCluster(
    host='10.167.2.175',
    port=30095,
    password='difyai123456',
    decode_responses=True
)

# 写入
rc.set('test_key', 'hello_redis8')

# 读取
value = rc.get('test_key')
print(value)  # hello_redis8

# 查看集群信息
info = rc.cluster_info()
print(info)
```

**Java 连接示例**（Jedis）:
```java
import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.HostAndPort;
import java.util.HashSet;
import java.util.Set;

Set<HostAndPort> nodes = new HashSet<>();
nodes.add(new HostAndPort("10.167.2.175", 30095));

JedisCluster cluster = new JedisCluster(nodes, 5000, 5000, 5, "difyai123456", null);
cluster.set("test_key", "hello_redis8");
String value = cluster.get("test_key");
System.out.println(value);
```

### D.4 注意事项

1. **Cluster 模式操作**：所有读写命令需加 `-c` 参数（redis-cli）或使用 `RedisCluster` 客户端（编程语言），否则遇到 key 跨节点时会报 `MOVED` 错误
2. **Dify 兼容性**：Dify 平台当前使用 Redis 7 单节点模式（不兼容 Cluster），Redis 8 Cluster 供局域网其他应用独立使用
3. **数据持久化**：当前使用 `emptyDir`（Pod 重启数据丢失），生产环境建议挂载 PVC
4. **高可用**：当前 3 主节点无副本，如需高可用可添加 3 个副本节点（`--cluster-replicas 1`）

---

## 附录 C：测试账号清单

| 服务 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| Dify 控制台 | myuwei@126.com | Difyai123456 | 管理员 |
| Code-Server | — | Dify@2026 | 在线编程（Caddy代理，IP直连无需hosts） |
| JupyterHub 多租户 | — | `ide2026` | 多用户注册（任意用户名+密码登录，每人独立工作空间5Gi） |
| JupyterLab | — | — | Python科学计算（无需密码，原生子路径） |
| Grafana | admin | uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb | 查看仪表盘 |
| Rancher | admin | Rancher@2026 | 集群管理 |
| LiteLLM | — | sk-ai-platform-master | API Key |

---

## 附录 D2：Dify 账户角色与权限详解

### D2.1 账户角色体系

Dify 平台共有 **15 个账户**，分为 4 种角色。所有账户属于同一个工作空间 `Zheng_Gong's Workspace`（ID: `00040b62-119e-4aae-b046-91e7d3e21f41`）。

| 角色 | 人数 | 权限概述 |
|------|------|---------|
| **owner** (所有者) | 1 | 工作空间最高权限，可转移所有权、删除工作空间 |
| **admin** (管理员) | 3 | 可管理应用、知识库、成员、模型配置 |
| **editor** (编辑者) | 1 | 可创建/编辑应用和知识库，不能管理成员 |
| **normal** (普通用户) | 10 | 可使用已发布的应用，不能创建或管理 |

### D2.2 完整账户清单

| # | 姓名 | 邮箱 | 角色 | 状态 | 创建时间 | 最后登录 |
|---|------|------|------|------|---------|---------|
| 1 | Zheng_Gong | myuwei@126.com | **owner** | active | 2026-05-19 | 2026-09-02 |
| 2 | javanetongzheng | javanetongzheng@icloud.com | **admin** | active | 2026-05-19 | 2026-06-16 |
| 3 | test-0368414 | 0368414@sd.taylors.edu.my | **admin** | active | 2026-06-07 | 2026-06-11 |
| 4 | Test Invite User | invite-direct-test4@126.com | **admin** | active | 2026-06-09 | 2026-06-09 |
| 5 | joelgong | joelgong@aliyun.com | **editor** | active | 2026-05-20 | 2026-06-18 |
| 6 | javanetongzheng | javanetongzheng@aliyun.com | **normal** | active | 2026-05-19 | 2026-06-12 |
| 7 | javanetgongzheng | javanetgongzheng@icloud.com | **normal** | active | 2026-05-21 | 2026-06-07 |
| 8 | test_account | test_account@163.com | **normal** | active | 2026-06-09 | 2026-06-09 |
| 9 | myuwei | myuwei@163.com | **normal** | active | 2026-06-10 | 2026-06-12 |
| 10 | qiaoguiping | qiaoguiping@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |
| 11 | sunxiaoting | sunxiaoting@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |
| 12 | sunhaoling | sunhaoling@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |
| 13 | weifeng | weifeng@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |
| 14 | wangjing | wangjing@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |
| 15 | weiwenkai | weiwenkai@126.com | **normal** | active | 2026-07-13 | 2026-07-14 |

> **统一密码**: 所有 Dify 账户的初始密码均为 `Difyai123456`。首次登录后用户可自行修改密码。

### D2.3 各角色权限详解

#### Owner (所有者) — Zheng_Gong / myuwei@126.com

| 权限项 | 说明 |
|--------|------|
| 工作空间管理 | 查看/编辑工作空间设置，可转移所有权、删除工作空间 |
| 成员管理 | 邀请/移除成员，设置成员角色（owner/admin/editor/normal） |
| 应用管理 | 创建/编辑/删除/发布所有应用（聊天助手、工作流、Agent） |
| 知识库管理 | 创建/编辑/删除知识库，上传/索引文档 |
| 模型配置 | 添加/编辑/删除模型提供商和模型凭据 |
| API Key 管理 | 创建/删除所有应用的 API Key |
| 工作流编排 | 创建/编辑复杂工作流（LLM节点、知识库检索、条件分支等） |
| 数据分析 | 查看应用使用统计、对话历史、标注数据 |

#### Admin (管理员) — 3 个账户

| 权限项 | 说明 |
|--------|------|
| 工作空间管理 | 查看工作空间设置，不可删除或转移所有权 |
| 成员管理 | 邀请成员（仅可设为 editor/normal，不可设为 owner/admin） |
| 应用管理 | 创建/编辑/删除/发布应用 ✅ |
| 知识库管理 | 创建/编辑/删除知识库 ✅ |
| 模型配置 | 添加/编辑模型提供商 ✅ |
| API Key 管理 | 创建/删除 API Key ✅ |
| 工作流编排 | 创建/编辑工作流 ✅ |

> **与 Owner 的区别**: Admin 不能转移工作空间所有权、不能删除工作空间、不能设置其他成员为 admin/owner。

#### Editor (编辑者) — joelgong / joelgong@aliyun.com

| 权限项 | 说明 |
|--------|------|
| 工作空间管理 | 仅查看 |
| 成员管理 | ❌ 不可管理成员 |
| 应用管理 | 创建/编辑/发布应用 ✅（不能删除他人应用） |
| 知识库管理 | 创建/编辑知识库 ✅ |
| 模型配置 | 使用已配置的模型，不能添加新模型 |
| API Key 管理 | 创建自己应用的 API Key ✅ |
| 工作流编排 | 创建/编辑工作流 ✅ |

#### Normal (普通用户) — 10 个账户

| 权限项 | 说明 |
|--------|------|
| 工作空间管理 | ❌ 不可访问 |
| 成员管理 | ❌ 不可访问 |
| 应用管理 | 仅可使用已发布的应用（通过 Web 界面或 API Key 调用） |
| 知识库管理 | ❌ 不可管理（但可通过应用间接使用知识库检索） |
| 模型配置 | ❌ 不可配置 |
| API Key 管理 | ❌ 不可创建 API Key |
| 工作流编排 | ❌ 不可访问编排页面 |

> **普通用户适用场景**: 学生用户。他们可以打开教师发布的应用链接，进行对话问答，但不能修改应用配置或管理知识库。

### D2.4 账户管理操作

**Owner/Admin 邀请成员**:
1. 登录 Dify 控制台 → 点击右上角工作空间名称
2. 点击 **成员管理**
3. 输入被邀请人的邮箱地址
4. 选择角色（editor 或 normal）
5. 点击 **发送邀请**
6. 被邀请人收到邮件（通过 Mailpit Web UI `http://10.167.2.175:30205` 查看）
7. 被邀请人点击邮件中的链接，设置密码后加入工作空间

**角色变更**: 仅 Owner 可变更成员角色。Admin 不可将其他成员提升为 Admin 或 Owner。

---

## 附录 D3：知识库局域网访问方式

### D3.1 知识库概览

平台共有 **13 个知识库**，全部使用 `high_quality` 索引技术：

| # | 知识库名称 | 嵌入模型 | 用途 |
|---|-----------|---------|------|
| 1 | 程序员必会的40种算法 | bge-m3 | 算法教学 |
| 2 | 深入AI/大模型必修数学体系 | bge-m3 | AI 数学基础 |
| 3 | 智能体设计模式智能系统构建实战指南 | bge-m3 | 智能体设计 |
| 4 | MonkeyCode + Judge0 本地化部署完整操作指南 | bge-m3 | 编程平台 |
| 5 | 工业互联网教学知识库 | qwen3-embedding:0.6b | 工业互联网基础 |
| 6 | PLC编程教程知识库 | bge-m3 | PLC 编程 |
| 7 | 工业网络协议知识库 | bge-m3 | 工业网络 |
| 8 | 工业安全标准知识库 | bge-m3 | 工业安全 |
| 9 | Python编程教程知识库 | bge-m3 | Python 教学 |
| 10 | Java编程教程知识库 | bge-m3 | Java 教学 |
| 11 | 软件工程最佳实践知识库 | bge-m3 | 软件工程 |
| 12 | qwen3-embedding-8b测试知识库 | bge-m3 | 测试用 |
| 13 | 2026级工业互联网应用专业人才培养方案 | qwen3-embedding:4b | 专业培养方案 |

### D3.2 局域网访问知识库的三种方式

#### 方式一：通过 Dify 控制台 Web 界面（推荐）

**适用角色**: owner / admin / editor

1. 浏览器打开 `https://10.167.2.175:31825`
2. 使用 owner/admin/editor 账号登录
3. 左侧导航栏点击 **知识库**
4. 选择目标知识库，点击进入
5. 可以上传文档、查看已索引的文档段落、进行检索测试

#### 方式二：通过 Dify 应用的知识库检索（学生可用）

**适用角色**: 所有角色（包括 normal 学生用户）

知识库已关联到工作台的多个应用中。学生使用这些应用对话时，AI 会自动从知识库检索相关内容：

| 应用名称 | 关联知识库 | 使用方式 |
|---------|-----------|---------|
| 知识库 + 聊天机器人 | 工业互联网教学知识库 | 对话即可触发检索 |
| 工业互联网智能体 | 工业互联网教学知识库 | 对话即可触发检索 |
| 工业互联网基础助手 | 工业网络协议知识库 | 对话即可触发检索 |
| PLC编程教学助手 | PLC编程教程知识库 | 对话即可触发检索 |
| Python编程教学助手 | Python编程教程知识库 | 对话即可触发检索 |
| Java编程教学助手 | Java编程教程知识库 | 对话即可触发检索 |
| 软件工程方法论助手 | 软件工程最佳实践知识库 | 对话即可触发检索 |
| 工业网络安全助手 | 工业安全标准知识库 | 对话即可触发检索 |

**学生使用步骤**:
1. 浏览器打开 `https://10.167.2.175:31825`
2. 使用学生账号（如 `qiaoguiping@126.com` / `Difyai123456`）登录
3. 在工作室页面选择对应的应用
4. 在对话框输入问题，AI 会自动从关联的知识库中检索相关内容并回答

#### 方式三：通过 Dify API 编程访问（开发场景）

**适用角色**: 拥有 API Key 的 owner/admin/editor

```bash
# 1. 获取知识库列表
curl -X GET 'https://10.167.2.175:31825/console/api/datasets' \
  -H 'Authorization: Bearer {YOUR_API_KEY}'

# 2. 检索知识库内容
curl -X POST 'https://10.167.2.175:31825/console/api/datasets/{DATASET_ID}/retrieve' \
  -H 'Authorization: Bearer {YOUR_API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "什么是工业互联网",
    "retrieval_mode": "semantic_search",
    "top_k": 5
  }'

# 3. 通过应用 API 对话（自动触发知识库检索）
curl -X POST 'https://10.167.2.175:31825/v1/chat-messages' \
  -H 'Authorization: Bearer app-{APP_API_KEY}' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {},
    "query": "PLC梯形图编程的基本要素有哪些？",
    "user": "student-001"
  }'
```

> **API Key 获取**: 登录 Dify 控制台 → 选择应用 → 点击 **API 访问** → 创建 API Key。只有 owner/admin/editor 角色可以创建 API Key。

### D3.3 知识库检索测试

在 Dify 控制台中进行知识库检索测试：
1. 进入知识库页面
2. 点击右上角 **检索测试**
3. 输入查询文本（如 "PLC梯形图编程"）
4. 查看返回的相关段落及相似度分数

---

## 附录 D4：Mailpit 邮件调试服务

Mailpit 提供 SMTP 邮件接收和 Web UI 查看，用于 Dify 平台的邮件功能测试（用户邀请、密码重置等）。

| 项目 | 地址 |
|------|------|
| Mailpit Web UI | `http://10.167.2.175:30205` |
| SMTP 服务地址 | `10.167.2.175:30205`（Web UI 端口） / K8s内部 `mailpit-smtp.dify.svc.cluster.local:1025` |
| SMTP 端口 | 1025（内部，无需认证） |

**用户邀请邮件流程**:
1. Owner/Admin 在 Dify 控制台邀请新成员
2. Dify 通过 Mailpit SMTP 发送邀请邮件
3. 打开 `http://10.167.2.175:30205` 查看收到的邮件
4. 新成员点击邮件中的链接，设置密码完成注册

---

## 可用模型列表

### Qwen3 系列（最新，推荐用于教学）

| 模型名称 | 大小 | 用途 | 响应速度 | 教学场景 |
|---------|------|------|---------|---------|
| qwen3:4b | 2GB | 快速问答 | ⚡ 10-30秒 | 工业互联网基础概念、传感器原理 |
| qwen3:8b | 4GB | 通用教学 | ⏳ 30-90秒 | PLC编程、工业以太网、边缘计算 |
| qwen3:14b | 8GB | 深度教学 | ⏳ 60-180秒 | MES系统、工业物联网安全 |
| qwen3:30b-a3b | 17GB | MoE高效推理 | ⏳ 15-60秒 | 复杂工业场景（30B参数仅激活3B，速度接近8b） |
| qwen3:32b | 18GB | 旗舰推理 | ⏳ 120-300秒 | 系统设计、架构分析 |

### Qwen2.5 系列（经典）

| 模型名称 | 大小 | 用途 | 响应速度 |
|---------|------|------|---------|
| qwen2.5:7b | 4.7GB | 快速问答 | ⚡ 3秒 |
| qwen2.5:14b | 10GB | 通用教学 | ⚡ 5秒 |
| qwen2.5-coder:7b | 4.7GB | 编程辅导 | ⚡ 3秒 |
| qwen2.5-coder:14b | 9GB | 代码教学 | ⚡ 5秒 |
| deepseek-r1:7b | 4.7GB | 深度推理 | ⏳ 10秒 |
| deepseek-r1:14b | 9GB | 复杂推理 | ⏳ 20秒 |
| qwen2.5:32b | 19GB | 高质量对话 | ⏳ 15秒 |
| qwen2.5:72b | 47GB | 旗舰模型 | ⏳ 60秒+ |

### 嵌入与多模态

| 模型名称 | 大小 | 用途 | 响应速度 |
|---------|------|------|---------|
| **qwen3-embedding:0.6b** | 639MB | 轻量嵌入（1024维） | ⚡ 即时 |
| **qwen3-embedding:4b** | 2.5GB | 高质量嵌入（1024维） | ⚡ 即时 |
| bge-m3 | 1.2GB | 通用嵌入（1024维） | ⚡ 即时 |
| nomic-embed-text | 274MB | 轻量嵌入 | ⚡ 即时 |
| llama3.2-vision:11b | 7.8GB | 多模态视觉 | ⏳ 15秒 |

### 云端模型映射（通过 LiteLLM）

| 模型名称 | 实际映射 | 用途 |
|---------|---------|------|
| z-ai/glm-5.1 | → qwen2.5:14b | 工作流应用兼容 |
| deepseek-ai/deepseek-v4-pro | → deepseek-r1:14b | 工作流应用兼容 |

### 工业互联网应用专业教学场景推荐

| 教学模块 | 推荐模型 | 场景示例 |
|---------|---------|---------|
| 工业互联网基础 | qwen3:4b | "什么是工业互联网？" |
| PLC编程教学 | qwen3:8b | "PLC梯形图编程示例" |
| 工业网络通信 | qwen3:8b | "Profinet vs EtherCAT" |
| 传感器与数据采集 | qwen3:4b | "PT100温度传感器原理" |
| MES制造执行系统 | qwen3:14b | "MES在工业4.0中的角色" |
| 工业物联网安全 | qwen3:14b | "SCADA系统安全防护" |
| 数字孪生技术 | qwen3:8b | "数字孪生应用场景" |
| 边缘计算 | qwen3:8b | "边缘计算 vs 云计算" |
| 编程基础(Python) | qwen2.5-coder:7b | "Python列表排序" |
| 数据库技术 | qwen2.5:7b | "SQL GROUP BY" |

> **Qwen3 使用提示**: Qwen3 默认开启 thinking 模式（思维链推理），首次回答可能需要 10-30 秒。在提示词前加 `/no_think` 可关闭思维链获得快速回答。通过 LiteLLM 调用时 content 字段可能为空（答案在 thinking 字段），建议直接通过 Dify 应用或 Ollama API 使用。

### 3000 人并发支持配置

平台已配置 HPA 自动扩缩容，支持 3000 人同时在线：

| 服务 | Min 副本 | Max 副本 | CPU阈值 | 说明 |
|------|---------|---------|---------|------|
| dify-api | 5 | 20 | 70% | API 请求处理 |
| dify-worker | 5 | 20 | 70% | 异步任务+LLM推理 |
| litellm | 3 | 10 | 70% | LLM 网关（已提升到 4 CPU/4Gi） |
| dify-web | 2 | 10 | 70% | 前端静态服务 |
| ingress-nginx | 3 | 10 | 70% | 入口负载均衡 |
| pgbouncer | 2 | 5 | 70% | 数据库连接池 |
| dify-plugin-daemon | 1 | 5 | 75% | 插件守护进程 |
| dify-sandbox | 1 | 5 | 75% | 代码沙箱 |
| code-server | 3 | 20 | 70% | 在线编程 |

**Ollama 推理优化**：
- `OLLAMA_NUM_PARALLEL=8`（8 路并行推理，从 4 提升）
- `OLLAMA_MAX_LOADED_MODELS=4`（同时驻留 4 个模型）
- `OLLAMA_KEEP_ALIVE=-1`（模型永不过期，避免冷启动）

**LiteLLM 网关优化**：
- 3 副本预热（minReplicas=3），避免单点瓶颈
- 每副本 4 CPU/4Gi 内存限制
- 22 个模型（含 Qwen3 系列 + Embedding）

---

> **文档版本**: v2.0 | **最后更新**: 2026-09-03 | **维护**: ZCode 自动化

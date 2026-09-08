# Code-Server AI编程环境配置指南

> **版本**: v1.0
> **日期**: 2026-09-07
> **适用环境**: 2节点K8s集群 (master 10.167.2.175, worker 10.167.2.176)

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│         Code-Server Pod (ai-platform命名空间)        │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ code-server │  │  Caddy   │  │  Continue.dev │  │
│  │  (VS Code)  │  │ (代理)   │  │   (AI扩展)     │  │
│  └──────┬──────┘  └────┬─────┘  └───────┬────────┘  │
│         │              │                │            │
│  ┌──────┴──────────────┴────────────────┴────────┐  │
│  │              LSP 语言服务器                     │  │
│  │  pylsp (Python) │ gopls (Go) │ clangd (C/C++)  │  │
│  └────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────┐ │
│  │           ConfigMap (持久化配置)                 │ │
│  │  continue_config.json │ vscode_settings.json    │ │
│  │  pylsp_config.toml                               │ │
│  └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  访问地址: http://10.167.2.175:30087/vscode/        │
│  密码: Dify@2026                                     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              LiteLLM 代理 (ai-platform)              │
│  http://litellm.ai-platform.svc.cluster.local:4000  │
│  API Key: sk-ai-platform-master                      │
├─────────────────────────────────────────────────────┤
│  ┌────────────────┐    ┌──────────────────────┐     │
│  │ Ollama Worker  │    │   Ollama Master      │     │
│  │ 10.167.2.176   │    │   10.167.2.175       │     │
│  │ qwen2.5-coder  │    │ nomic-embed-text     │     │
│  │   :7b (chat)   │    │   (768维嵌入)        │     │
│  └────────────────┘    └──────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

## 已安装组件

### 一、Continue.dev AI编程助手

| 功能 | 模型 | 用途 |
|------|------|------|
| AI聊天 | qwen2.5-coder:7b | 代码问答、解释、重构建议 |
| Tab自动补全 (FIM) | qwen2.5-coder:7b | 内联代码补全（行级/函数级） |
| 嵌入向量 | nomic-embed-text | 代码库语义搜索（768维） |
| 备选聊天 | qwen3:8b / deepseek-r1:14b | 推理能力更强的备选模型 |

**配置文件**: `/home/coder/.continue/config.json`（通过ConfigMap持久化）

**LiteLLM路由**:
- 聊天请求 → LiteLLM → Ollama Worker (10.167.2.176:11434)
- 嵌入请求 → LiteLLM → Ollama Master (10.167.2.175:11435)

### 二、LSP语言服务器

| 语言 | LSP服务器 | 版本 | 功能 |
|------|-----------|------|------|
| Python | pylsp | v1.15.0 | 代码补全、定义跳转、pycodestyle/pyflakes/pylint检查、black格式化、isort排序、rope重构 |
| Go | gopls | v0.16.1 | 代码补全、定义跳转、类型检查、格式化 |
| C/C++ | clangd | v19.1.7 | 代码补全、定义跳转、clang-tidy检查、头文件插入 |
| Python(备选) | jedi-language-server | v0.47.0 | 备选Python LSP |

**pylsp配置**: `/home/coder/.config/pylsp/config.toml`（通过ConfigMap持久化）
- 最大行长度: 120字符
- 启用: pycodestyle, pyflakes, pylint, black, isort, rope
- 禁用: autopep8, yapf（避免与black冲突）

### 三、VS Code设置

**配置文件**: `/home/coder/.local/share/code-server/User/settings.json`（通过ConfigMap持久化）

关键设置:
- `python.languageServer`: pylsp
- `go.useLanguageServer`: true
- `clangd.path`: /usr/bin/clangd
- `C_Cpp.intelliSenseEngine`: disabled（使用clangd替代）
- `continue.enableTabAutocomplete`: true
- 格式化: 编辑器保存时自动格式化

### 四、已安装VS Code扩展

| 扩展 | 版本 | 用途 |
|------|------|------|
| continue.continue | 2.0.0 | AI编程助手（聊天+补全） |
| ms-python.python | 2026.4.0 | Python开发支持 |
| ms-python.debugpy | 2026.6.0 | Python调试 |
| golang.go | 0.54.0 | Go开发支持 |
| llvm-vs-code-extensions.vscode-clangd | 0.6.0 | C/C++ clangd集成 |
| ms-toolsai.jupyter | 2025.9.1 | Jupyter Notebook |
| ms-ceintl.vscode-language-pack-zh-hans | 1.123.0 | 中文界面 |
| anthropic.claude-code | 2.1.177 | Claude AI（备用） |
| kilocode.kilo-code | 7.3.45 | AI Agent（备用） |
| codeium.windsurf-cpptools | 1.0.0 | C++工具 |

## K8s部署配置

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: code-server-lsp-config
  namespace: ai-platform
data:
  continue_config.json: |
    { ... Continue.dev配置 ... }
  vscode_settings.json: |
    { ... VS Code设置 ... }
  pylsp_config.toml: |
    [plugins]
    ... pylsp配置 ...
```

### Deployment挂载

Code-Server Deployment通过以下volumeMounts挂载ConfigMap:
- `continue_config.json` → `/home/coder/.continue/config.json`
- `vscode_settings.json` → `/home/coder/.local/share/code-server/User/settings.json`
- `pylsp_config.toml` → `/home/coder/.config/pylsp/config.toml`

### 访问方式

- **URL**: `http://10.167.2.175:30087/vscode/` (无需hosts文件)
- **密码**: `Dify@2026`
- **NodePort**: 30087
- **Caddy代理**: strip_prefix `/vscode` 后转发到 code-server:8080

## 验证测试

| 测试项 | 结果 | 详情 |
|--------|------|------|
| Code-Server访问 | ✅ | HTTP 302重定向到登录页 |
| Continue.dev AI聊天 | ✅ | "Say hello" → "Hello! How can I assist you today?" |
| Continue.dev FIM补全 | ✅ | "def hello_world" → 补全正常 |
| LiteLLM嵌入 | ✅ | 768维嵌入向量 |
| pylsp | ✅ | v1.15.0, pycodestyle+pyflakes+pylint |
| gopls | ✅ | v0.16.1 |
| clangd | ✅ | v19.1.7, clang-tidy |
| VS Code设置持久化 | ✅ | ConfigMap挂载，Pod重启后配置保留 |
| Caddy代理 | ✅ | /vscode/前缀正确处理 |

## 使用指南

### 教师使用

1. 浏览器打开 `http://10.167.2.175:30087/vscode/`
2. 输入密码 `Dify@2026`
3. 打开项目文件（PVC持久化，50Gi存储）
4. 使用Continue.dev:
   - **Ctrl+L**: 打开AI聊天面板
   - **Tab**: 接受代码补全建议
   - **Ctrl+I**: 行内AI编辑
5. 多语言开发:
   - Python: 自动补全+pylint检查+black格式化
   - Go: 自动补全+gopls类型检查
   - C/C++: 自动补全+clang-tidy检查

### 学生使用

学生通过JupyterHub登录后，Code-Server作为sidecar容器自动启动。学生可在JupyterLab中切换到Code-Server视图，享受相同的AI编程体验。

## 与JupyterHub的集成

Code-Server作为JupyterHub Pod的sidecar容器运行:
- 共享PVC（与JupyterLab相同的文件系统）
- 共享Ollama AI服务
- 通过JupyterHub认证（无需额外登录）
- Caddy strip_prefix处理`/vscode`子路径

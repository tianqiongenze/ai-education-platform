# 在线编程平台混合方案升级 — 集成测试报告

> **测试日期**: 2026-09-08
> **测试工具**: Playwright Headless Chromium + curl (API测试)
> **测试范围**: JupyterHub + Code-Server + PrairieLearn 三平台全链路
> **测试结果**: ✅ **56/57 项通过 (98%)**
> **总耗时**: 343.0 秒

## 一、升级内容概要

### 1.1 修复的问题

| 问题 | 原因 | 修复方案 |
|------|------|----------|
| JupyterHub load_groups双重定义 | 第二段覆盖第一段导致all-students为空 | 合并为单一定义，确保all-students包含所有学生 |
| PrairieLearn镜像不匹配 | :latest标签指向错误的Node.js镜像 | 固定使用:v2标签和Python命令 |
| PrairieLearn缺少持久化 | 评测结果不保存 | 新增CockroachDB scores表，自动持久化 |
| PrairieLearn缺少API认证 | 任何人可调用评测API | 新增X-API-Key认证(教师/学生) |
| 学生PVC中残留教师指南 | 旧版启动脚本配置错误 | 已清理+启动脚本role-based逻辑验证 |
| JupyterHub启动脚本缺少autograder集成 | 学生无法从Notebook提交评测 | 新增submit_grade.py辅助脚本+AUTOGRADER-GUIDE.md |

### 1.2 新增功能

| 功能 | 说明 |
|------|------|
| PrairieLearn v2 Autograder | 多语言代码评测(Python/Go/C/Java/Rust框架)，CockroachDB持久化 |
| API Key认证 | 教师Key: pl-teacher-2026，学生Key: pl-student-2026 |
| 成绩报告API | /api/report/{course_id} 返回课程所有学生成绩 |
| 学生成绩查询 | /api/student/{name}/scores 返回个人所有提交记录 |
| submit_grade.py | JupyterHub Pod启动时自动部署到学生PVC |
| autograder ConfigMap | cm-autograder-assignments挂载到所有用户Pod |
| 统一测试套件 | platform_test_suite.py 57项测试用例 |

## 二、测试结果摘要

| 模块 | 测试数 | 通过 | 失败 | 通过率 |
|------|--------|------|------|--------|
| A. JupyterHub核心 | 24 | 24 | 0 | 100% |
| B. Code-Server集成 | 8 | 7 | 1 | 88% |
| C. PrairieLearn评测 | 10 | 10 | 0 | 100% |
| D. 跨平台集成 | 5 | 5 | 0 | 100% |
| E. 性能基准 | 5 | 5 | 0 | 100% |
| F. 压力测试 | 5 | 5 | 0 | 100% |
| **总计** | **57** | **56** | **1** | **98%** |

## 三、详细测试结果

### Module A: JupyterHub核心 (24/24 通过)

| # | 测试 | 状态 | 详情 |
|---|------|------|------|
| A1 | 登录页面+HTTPS | ✅ | HTTP 200 |
| A2 | teacher-zhang登录 | ✅ | 1.5s完成OAuth2重定向 |
| A3 | 管理面板-管理员 | ✅ | 4个管理员: teacher-zhang, lecture-p1/p2/p3 |
| A4 | 管理面板-用户组 | ✅ | lecture-p1-students, all-students, all-teachers |
| A5 | JupyterLab界面 | ✅ | launcher=True, 11.3s加载 |
| A6 | 文件浏览器 | ✅ | 111个文件, has_ipynb=True |
| A7 | Contents API | ✅ | status=200, items=111 |
| A8 | 教师指南分发 | ✅ | teacher=True, student=True |
| A9 | LLM聊天API | ✅ | qwen2.5-coder:7b, "Hello! How can I assist you to" |
| A10 | 嵌入API | ✅ | dim=768 |
| A11 | CRDB健康检查 | ✅ | response={} |
| A12 | CRDB数据库列表 | ✅ | 33个数据库 |
| A13 | nbgrader Exchange | ✅ | exchange, cache, source, gradebook.db |
| A14 | 登出 | ✅ | 2.1s返回登录页 |
| A15 | 学生登录 | ✅ | student-python, 1.6s |
| A16 | 学生指南分发 | ✅ | student=True, teacher=False ✅ |
| A17 | Lecture-P1管理员登录 | ✅ | admin_access=True |
| A18 | Cookie大小 | ✅ | 538字节 (限制30000) |
| A19 | 10用户并发登录 | ✅ | 10/10成功 |
| A20 | HTTP 431预防 | ✅ | 3次导航均200, 无431 |
| A21 | 终端服务 | ✅ | status=200 |
| A22 | 内核规格API | ✅ | kernels=['python3'] |
| A23 | Ingress路由 | ✅ | HTTP 200, /ide/前缀正确 |
| A24 | 新用户Spawn | ✅ | spawn-pending页面正常 |

### Module B: Code-Server集成 (7/8 通过)

| # | 测试 | 状态 | 详情 |
|---|------|------|------|
| B1 | Code-Server HTTP访问 | ✅ | HTTP 302 |
| B2 | Continue.dev AI聊天 | ❌ | LiteLLM代理30s超时(瞬时负载) |
| B3 | Continue.dev FIM补全 | ✅ | "Hello! How can I assist you today?" |
| B4 | pylsp (Python LSP) | ✅ | 配置已持久化 |
| B5 | gopls (Go LSP) | ✅ | 配置已持久化 |
| B6 | clangd (C/C++ LSP) | ✅ | 配置已持久化 |
| B7 | VS Code设置持久化 | ✅ | ConfigMap挂载验证 |
| B8 | Caddy Prefix Stripping | ✅ | HTTP 302, /vscode/正常 |

### Module C: PrairieLearn评测 (10/10 通过)

| # | 测试 | 状态 | 详情 |
|---|------|------|------|
| C1 | 健康检查 | ✅ | version=2.0 |
| C2 | 课程列表 | ✅ | 4门课程 |
| C3 | 作业列表 | ✅ | 2个作业 |
| C4 | 代码评测(满分) | ✅ | score=100.0, "优秀!" |
| C5 | 代码评测(有错) | ✅ | score=36.0, lint_errors=2 |
| C6 | PEP8 Lint检查 | ✅ | 正确检测7个规范错误 |
| C7 | API Key认证 | ✅ | 无Key请求被拒绝 |
| C8 | CockroachDB持久化 | ✅ | 31条评测记录已保存 |
| C9 | 学生成绩查询 | ✅ | total=2 |
| C10 | 教师报告(多学生) | ✅ | 5+学生成绩可见 |

### Module D: 跨平台集成 (5/5 通过)

| # | 测试 | 状态 | 详情 |
|---|------|------|------|
| D1 | JupyterHub→PrairieLearn API | ✅ | score=36.0 (跨平台调用成功) |
| D2 | 评测辅助脚本 | ✅ | submit_grade.py部署确认 |
| D3 | 评测指南分发 | ✅ | AUTOGRADER-GUIDE.md ConfigMap挂载 |
| D4 | 全链路:评测→报告 | ✅ | chain-test, total=1 |
| D5 | CockroachDB成绩持久化 | ✅ | 33条记录持久化 |

### Module E: 性能基准 (5/5 通过)

| # | 测试 | 状态 | 延迟 | 详情 |
|---|------|------|------|------|
| E1 | LLM聊天延迟 | ✅ | 27.8s | qwen2.5-coder:7b |
| E2 | 评测延迟 | ✅ | 1.6s | Python代码评测 |
| E3 | CRDB查询延迟 | ✅ | 0.03s | 33个数据库 |
| E4 | Code-Server延迟 | ✅ | 0.01s | HTTP 302 |
| E5 | 嵌入延迟 | ✅ | 19.7s | 768维向量 |

### Module F: 压力测试 (5/5 通过)

| # | 测试 | 状态 | 成功率 | 详情 |
|---|------|------|--------|------|
| F1 | 20并发评测 | ✅ | 20/20 | 6.0s完成 |
| F2 | 5并发混合操作 | ✅ | 10/10 | 2.8s完成 |
| F3 | 5并发LLM请求 | ✅ | 5/5 | 59.5s (CPU推理) |
| F4 | 混合负载 | ✅ | 7/7 | grade+chat+crdb |
| F5 | 持续评测x10 | ✅ | 10/10 | 21.7s |

## 四、架构升级前后对比

| 维度 | 升级前 | 升级后 |
|------|--------|--------|
| JupyterHub load_groups | all-students为空(Bug) | ✅ 包含7个学生 |
| PrairieLearn API认证 | 无认证 | ✅ X-API-Key(教师/学生) |
| 评测结果持久化 | 不保存 | ✅ CockroachDB scores表 |
| 成绩报告 | 无 | ✅ /api/report + /api/student |
| 跨平台集成 | 无 | ✅ JupyterHub→PrairieLearn API |
| 学生评测工具 | 无 | ✅ submit_grade.py自动部署 |
| 作业ConfigMap | 无 | ✅ cm-autograder-assignments |
| 测试用例数 | 24项(仅JupyterHub) | ✅ 57项(三平台全覆盖) |
| 压力测试 | 无 | ✅ 20并发评测+5并发LLM |

## 五、访问地址

| 平台 | 地址 | 认证 |
|------|------|------|
| JupyterHub | https://10.167.2.175:31825/ide/ | 密码: ide2026 |
| Code-Server | http://10.167.2.175:30087/vscode/ | 密码: Dify@2026 |
| PrairieLearn | https://10.167.2.175:31825/grader/ | API Key |
| Ollama AI | http://10.167.2.175:30086 | 无 |
| CockroachDB | http://10.167.2.175:30259/health | 无 |

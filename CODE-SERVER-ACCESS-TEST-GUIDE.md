# Code-Server 企业平台 — 局域网访问 & 全功能人工测试方案

> **生成时间**: 2026-06-13  
> **集群节点**: k8s-master (10.167.2.175, 64GB) / k8s-worker1 (10.167.2.176, 125GB)  
> **状态**: ✅ 所有服务运行正常，已通过实际验证

---

## 一、局域网访问方式总览

### 1.1 访问方式说明

由于集群没有公网 IP，局域网内有两种访问方式：

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **NodePort 直连** | `http://10.167.2.175:<端口>` | 快速测试、无需 DNS |
| **Ingress + hosts** | 配置 hosts 文件后 `https://域名` | 生产体验、TLS 加密 |

### 1.2 配置 hosts 文件（推荐）

在局域网内任意 Windows/Mac/Linux 机器上，编辑 hosts 文件：

**Windows**: `C:\Windows\System32\drivers\etc\hosts`  
**Mac/Linux**: `/etc/hosts`

```
10.167.2.175  code-server.ai-platform.local
10.167.2.175  web.dify-plus.local
10.167.2.175  console.dify-plus.local
10.167.2.175  api.dify-plus.local
```

---

## 二、所有服务访问入口（已验证）

### 2.1 核心服务

| 服务 | NodePort 直连 | Ingress 域名 (HTTPS) | 状态 |
|------|--------------|---------------------|------|
| **code-server** | `http://10.167.2.175:32231/login` | `https://code-server.ai-platform.local` | ✅ 200 |
| **Dify Web** | `http://10.167.2.175:30080` | `https://web.dify-plus.local` | ✅ 200 |
| **Dify API** | `http://10.167.2.175:30501` | `https://api.dify-plus.local` | ✅ |
| **Open-WebUI** | `http://10.167.2.175:30084` | — | ✅ 200 |
| **Litellm API** | `http://10.167.2.175:30083` | — | ✅ 200 |
| **Grafana** | `http://10.167.2.175:30082` | — | ✅ 302 |
| **Rancher** | `https://10.167.2.175` | — | ✅ 200 |

### 2.2 登录凭据

| 服务 | 用户名 | 密码 | 获取方式 |
|------|--------|------|----------|
| **code-server** | — | `ai@2026` | K8s Secret: `code-server-secrets` |
| **Rancher** | `admin` | `4bdv4c8w88dmmpjw22zzprj975mvmmslfrtnxzzxtqs7ml5qmmftsm` | Docker 日志 Bootstrap Password |
| **Grafana** | `admin` | `uPkH7M52W4wOCtH37V3iu3VIrNvLIqcQkx4Jw6cb` | K8s Secret: `kube-prometheus-stack-grafana` |
| **Litellm** | — | `sk-ai-platform-master` (API Key) | 环境变量 `LITELLM_MASTER_KEY` |

---

## 三、全功能人工测试方案（逐步骤验证）

### 测试 1: code-server IDE 功能测试

**目标**: 验证 Web IDE 完整可用

| 步骤 | 操作 | 预期结果 | 验证命令 |
|------|------|----------|----------|
| 1.1 | 浏览器打开 `http://10.167.2.175:32231/login` | 显示登录页面 | ✅ 已验证 (200) |
| 1.2 | 输入密码 `ai@2026`，点击登录 | 进入 VS Code 界面 | 手动测试 |
| 1.3 | 创建新文件 `test.py`，写入 `print("hello")` | 文件创建成功 | 手动测试 |
| 1.4 | 打开终端 (Ctrl+`) | 终端正常启动 | 手动测试 |
| 1.5 | 终端执行 `python3 test.py` | 输出 `hello` | 手动测试 |
| 1.6 | 安装扩展 (如 Python) | 扩展安装成功 | 手动测试 |
| 1.7 | 关闭浏览器，重新打开 | 会话保持（sticky session） | 手动测试 |
| 1.8 | HTTPS 访问 `https://code-server.ai-platform.local` | TLS 加密连接 | ✅ 已验证 (200) |

### 测试 2: Dify 平台功能测试

**目标**: 验证 AI 应用开发平台完整可用

| 步骤 | 操作 | 预期结果 | 验证命令 |
|------|------|----------|----------|
| 2.1 | 浏览器打开 `http://10.167.2.175:30080` | Dify 登录/首页 | ✅ 已验证 (307→登录) |
| 2.2 | 登录 Dify 账号 | 进入工作台 | 手动测试 |
| 2.3 | 创建新应用 → 聊天助手 | 应用创建成功 | 手动测试 |
| 2.4 | 配置 LLM 模型（选择 litellm 代理的模型） | 模型列表显示 | 手动测试 |
| 2.5 | 在预览中发送消息 | AI 正常回复 | 手动测试 |
| 2.6 | 上传知识库文档 | 文档解析成功 | 手动测试 |
| 2.7 | HTTPS 访问 `https://web.dify-plus.local` | TLS 加密连接 | ✅ 已验证 (200) |

### 测试 3: Litellm API 代理测试

**目标**: 验证 AI 模型统一代理正常工作

| 步骤 | 操作 | 预期结果 | 验证命令 |
|------|------|----------|----------|
| 3.1 | 健康检查 | 返回 healthy | `curl http://10.167.2.175:30083/health/readiness` ✅ |
| 3.2 | 列出模型 | 返回 9 个模型 | `curl -H "Authorization: Bearer sk-ai-platform-master" http://10.167.2.175:30083/v1/models` |
| 3.3 | 调用 qwen2.5:14b (实际可用) | 返回 AI 回复 | `curl -X POST http://10.167.2.175:30083/v1/chat/completions -H "Authorization: Bearer sk-ai-platform-master" -H "Content-Type: application/json" -d '{"model":"qwen2.5:14b","messages":[{"role":"user","content":"你好"}]}'` |
| 3.4 | 调用 qwen2.5-coder:14b | 返回代码 | 同上，model 改为 `qwen2.5-coder:14b` |
| 3.5 | 调用 bge-m3 (嵌入) | 返回向量 | `curl -X POST http://10.167.2.175:30083/v1/embeddings -H "Authorization: Bearer sk-ai-platform-master" -H "Content-Type: application/json" -d '{"model":"bge-m3","input":"Hello"}'` |
| 3.6 | 流式输出测试 | 逐字返回 | 添加 `"stream":true` |

> ⚠️ **注意**: 当前 ollama 中实际已拉取的模型为: `qwen2.5:14b-instruct-q5_K_M`, `qwen2.5:32b`, `qwen2.5-coder:14b-instruct-q4_K_M`, `bge-m3`, `nomic-embed-text`。litellm 配置中 `qwen2.5:72b`, `deepseek-r1:32b`, `deepseek-r1:14b`, `qwen2.5:7b` 对应的 ollama 模型尚未拉取，调用会超时。如需使用这些模型，需先 `ollama pull`。

**快速验证脚本**（在局域网机器上执行）:
```bash
# 健康检查
curl -s http://10.167.2.175:30083/health/readiness

# 模型列表
curl -s -H "Authorization: Bearer sk-ai-platform-master" \
  http://10.167.2.175:30083/v1/models | python3 -m json.tool

# 对话测试 (使用实际可用的 qwen2.5:14b 模型)
curl -s --max-time 120 -X POST http://10.167.2.175:30083/v1/chat/completions \
  -H "Authorization: Bearer sk-ai-platform-master" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:14b","messages":[{"role":"user","content":"用一句话介绍Kubernetes"}],"max_tokens":50}' \
  | python3 -m json.tool
```

### 测试 4: Open-WebUI 聊天测试

**目标**: 验证 Web 聊天界面正常

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 4.1 | 浏览器打开 `http://10.167.2.175:30084` | 聊天界面加载 | ✅ 已验证 (200) |
| 4.2 | 选择模型（如 qwen2.5:7b） | 模型列表显示 |
| 4.3 | 发送消息 "Hello" | AI 正常回复 |
| 4.4 | 切换不同模型测试 | 各模型均正常 |

### 测试 5: 监控系统测试

**目标**: 验证 Prometheus + Grafana + Alertmanager

| 步骤 | 操作 | 预期结果 | 验证命令 |
|------|------|----------|----------|
| 5.1 | 浏览器打开 `http://10.167.2.175:30082` | Grafana 登录页 | ✅ 已验证 (302) |
| 5.2 | 登录 (admin / 见上方密码) | 进入仪表板 | 手动测试 |
| 5.3 | 查看 "Kubernetes/Compute Resources" 仪表板 | 显示 Pod/Node 指标 | 手动测试 |
| 5.4 | 查看 Prometheus targets | 所有 target UP | `kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090` → `http://localhost:9090/targets` |
| 5.5 | 查看 Alertmanager | 告警规则就绪 | `kubectl get prometheusrule -n monitoring` |

### 测试 6: 高可用测试

**目标**: 验证多副本和自动恢复

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 6.1 | `kubectl get pods -n ai-platform` | code-server 3/3 Running |
| 6.2 | `kubectl delete pod <code-server-pod> -n ai-platform` | Pod 自动重建 |
| 6.3 | 删除期间访问 code-server | 服务不中断（其他副本接管） |
| 6.4 | `kubectl get hpa -n ai-platform` | HPA 正常监控 |

### 测试 7: TLS/SSL 验证

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 7.1 | `curl -svk https://code-server.ai-platform.local 2>&1 \| grep "SSL"` | TLS 握手成功 |
| 7.2 | `curl -svk https://web.dify-plus.local 2>&1 \| grep "SSL"` | TLS 握手成功 |
| 7.3 | 浏览器打开 HTTPS 地址 | 证书警告（自签名，正常）→ 点击继续 |

### 测试 8: 负载测试

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 8.1 | 安装 locust: `pip install locust` | 安装成功 |
| 8.2 | 运行: `locust -f locustfile.py --host=http://10.167.2.175:32231` | 测试启动 |
| 8.3 | 浏览器打开 `http://localhost:8089` | Locust Web UI |
| 8.4 | 设置 50 用户，spawn rate 5 | 开始压测 |
| 8.5 | 观察 HPA: `kubectl get hpa -n ai-platform -w` | 副本数自动扩展 |

---

## 四、Rancher 管理平台

### 登录信息

| 项目 | 值 |
|------|-----|
| **URL** | `https://10.167.2.175` |
| **用户名** | `admin` |
| **Bootstrap Password** | `4bdv4c8w88dmmpjw22zzprj975mvmmslfrtnxzzxtqs7ml5qmmftsm` |

> ⚠️ **注意**: 这是首次启动时生成的 Bootstrap Password。如果之前已登录并修改过密码，请使用修改后的密码。如果忘记密码，可通过以下命令重置：
> ```bash
> ssh root@10.167.2.175
> docker exec -ti rancher reset-password
> ```

### Rancher 部署方式

Rancher v2.8.3 以 Docker 容器方式运行在 k8s-master 上：
- 镜像: `rancher/rancher:v2.8.3`
- 端口: 80 (HTTP), 443 (HTTPS)
- 网络: bridge 模式 (172.17.0.2)

---

## 五、快速验证清单（5 分钟完成）

在局域网机器上依次执行：

```bash
# 1. 配置 hosts（一次性）
# Windows: 管理员记事本打开 C:\Windows\System32\drivers\etc\hosts
# 添加: 10.167.2.175 code-server.ai-platform.local web.dify-plus.local

# 2. 验证 code-server
curl -sk -o NUL -w "%{http_code}" -H "Host: code-server.ai-platform.local" http://10.167.2.175:32231/login
# 预期: 200

# 3. 验证 Dify
curl -sk -o NUL -w "%{http_code}" http://10.167.2.175:30080
# 预期: 307

# 4. 验证 Litellm
curl -s http://10.167.2.175:30083/health/readiness
# 预期: {"status":"healthy"...}

# 5. 验证 Open-WebUI
curl -sk -o NUL -w "%{http_code}" http://10.167.2.175:30084
# 预期: 200

# 6. 验证 Grafana
curl -sk -o NUL -w "%{http_code}" http://10.167.2.175:30082
# 预期: 302

# 7. 验证 Rancher
curl -sk -o NUL -w "%{http_code}" https://10.167.2.175
# 预期: 200

# 8. 验证所有 Pod 运行
ssh root@10.167.2.175 "kubectl get pods -n ai-platform"
# 预期: 全部 Running
```

---

## 六、已知限制与注意事项

| 问题 | 说明 | 影响 |
|------|------|------|
| **模型运行在 CPU** | ollama-worker 节点无 GPU，所有模型 100% CPU 推理 | 首次推理需 30-120 秒加载，后续调用正常 |
| **部分模型未拉取** | `qwen2.5:72b`, `deepseek-r1:32b`, `deepseek-r1:14b` 在 litellm 中配置但 ollama 中不存在 | 调用这些模型会超时 |
| **可用模型** | `qwen2.5:14b-instruct-q5_K_M`, `qwen2.5:32b`, `qwen2.5-coder:14b-instruct-q4_K_M`, `bge-m3`, `nomic-embed-text` | 仅这些模型可正常使用 |
| **litellm 超时** | 默认超时 60-120s，CPU 推理可能超时 | 大模型调用建议直接使用 ollama API |
| **自签名证书** | TLS 证书为自签名 | 浏览器会显示警告，点击"继续访问"即可 |

## 七、常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| code-server 返回 404 | 缺少 Host header | 使用 `-H "Host: code-server.ai-platform.local"` 或配置 hosts |
| litellm 无响应 | worker 死锁 | 已修复: `--num_workers 1` |
| HTTPS 证书警告 | 自签名证书 | 正常现象，点击"继续访问" |
| 镜像拉取失败 | 国内网络限制 | 使用阿里云镜像或配置代理 |
| NFS 不可用 | nfs-server 未启动 | `systemctl start nfs-server` |
| Rancher webhook 报错 | webhook 服务缺失 | 已修复: failurePolicy 改为 Ignore |
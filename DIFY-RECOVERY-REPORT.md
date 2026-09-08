# Dify 平台修复与测试完整报告

**日期**: 2026-08-27  
**环境**: K8s 集群 (Master: 10.167.2.175, Worker: 10.167.2.176)  
**执行者**: ZCode 自动化修复

---

## 一、问题诊断与修复总结

### 1.1 核心问题定位

| # | 问题 | 根本原因 | 修复方案 | 状态 |
|---|------|---------|---------|------|
| 1 | LiteLLM CrashLoopBackOff (重启11160次) | `ghcr.io/berriai/litellm:main-stable` 镜像的 glibc 2.41 要求 x86-64-v2 指令集，Xeon Gold 5320 不完全支持 | 使用 `python:3.11-slim` 基础镜像 + 清华 PyPI 镜像构建兼容镜像 `ai-platform/litellm:custom`，推送到本地 registry | ✅ 已修复 |
| 2 | ollama-worker ImagePullBackOff | imagePullPolicy=Always，但 Docker Hub 不可达 | 改为 imagePullPolicy=IfNotPresent（worker 节点已有本地镜像） | ✅ 已修复 |
| 3 | code-server ImagePullBackOff | 同上 | 同上 | ✅ 已修复 |
| 4 | docker-registry-master ImagePullBackOff | registry:2 镜像未本地缓存 | 从 daocloud 镜像拉取 registry:2，设置 IfNotPresent | ✅ 已修复 |
| 5 | Dify 登录失败 (Invalid encrypted data) | Dify 1.14.2 要求密码 base64 编码，旧测试发送明文 | 生成正确 base64 编码密码 | ✅ 已修复 |
| 6 | Dify 登录后仍401 (Invalid email or password) | 数据库中密码哈希与已知密码不匹配 | 使用 Dify 的 PBKDF2-HMAC-SHA256 算法重置密码为 `Difyai123456` | ✅ 已修复 |
| 7 | Dify HTTPS ingress 返回404 | ingress 注解 `nginx.ingress.kubernetes.io/rewrite-target: "/"` 会剥离路径前缀 | 删除 rewrite-target 注解 | ✅ 已修复 |
| 8 | 模型提供商 API 返回 400 "Invalid plugin id langgenius/tongyi" | `provider_name` 格式不正确：存储为 `langgenius/tongyi`（2段），应为 `langgenius/tongyi/tongyi`（3段） | 批量更新 provider_models、provider_model_credentials、provider_model_settings 表 | ✅ 已修复 |
| 9 | 插件 daemon 持续查找 tongyi:0.1.48 (record not found) | 磁盘上 `plugin_packages` 和 `plugin` 目录残留旧版本 0.1.48 引用，但 DB 中只有 0.2.0 | 删除磁盘上的 0.1.48 残留目录 + 更新 ai_model_installations 表 | ✅ 已修复 |
| 10 | 模型提供商/数据集 API 返回 500 PrivkeyNotFoundError | RSA 私钥文件丢失（PVC 在6月21日重建时被清空），OPENDAL_FS_ROOT 配置为相对路径 "storage" 而非绝对路径 "/app/storage" | 1. 生成新 RSA 密钥对 2. 更新 OPENDAL_FS_ROOT 为 `/app/storage` 3. 更新 tenants 表的 encrypt_public_key 4. 清除用旧密钥加密的 provider_credentials | ✅ 已修复 |
| 11 | dify-api Pod 级联崩溃 (0/1 Running) | 多副本同时启动导致 DB 连接池耗尽 | 缩减到 1 副本稳定启动 | ✅ 已修复 |
| 12 | LiteLLM 部分模型 500 错误 | 配置中部分模型指向 `ollama-master:11434`，但 master 节点无 Ollama 运行 | 统一所有模型 api_base 指向 `ollama-worker:11434` | ✅ 已修复 |
| 13 | LiteLLM 模型标签不匹配 | 配置中使用 `qwen2.5-coder:14b-instruct-q4_K_M` 但 Ollama 中实际标签是 `qwen2.5-coder:14b` | 修正所有模型标签为 Ollama 实际标签 | ✅ 已修复 |

### 1.2 已清理的死 Pod

- ai-platform/test-curl (ContainerStatusUnknown)
- default/dify-exporter-python (Unknown)
- default/litellm-exporter-python (Unknown)  
- default/ollama-exporter-python (Unknown)
- default/debug-net (Completed)
- default/rancher-alerting-drivers (Unknown)
- dify-plus/pgbouncer ×2 (Unknown)
- dify-plus/postgres-exporter (Unknown)
- dify-plus/redis-exporter (Unknown)
- monitoring/kube-state-metrics ×40+ (Evicted)
- monitoring/loki-stack-promtail (Evicted)

---

## 二、当前服务状态

### 2.1 核心服务

| 服务 | 状态 | 访问地址 |
|------|------|---------|
| Dify API | ✅ Running | https://10.167.2.175:31825 (ingress) |
| Dify Web | ✅ Running | https://10.167.2.175:31825 |
| Dify Worker | ✅ Running | 集群内部 |
| Dify Plugin Daemon | ✅ Running | 集群内部 |
| Dify Sandbox | ✅ Running | 集群内部 |
| PostgreSQL | ✅ Running | 集群内部 |
| Redis | ✅ Running | 集群内部 |
| Weaviate | ✅ Running | 集群内部 |
| LiteLLM Gateway | ✅ Running | http://10.167.2.176:30083 |
| Ollama Worker | ✅ Running | http://10.167.2.176:30086 |
| Code-Server | ✅ Running | http://10.167.2.175:30085 |
| Grafana | ⚠️ ImagePullBackOff (需修复镜像) | http://10.167.2.175:30082 |

### 2.2 Dify 访问信息

- **控制台**: `https://10.167.2.175:31825` (Host: console.dify-plus.local)
- **API**: `https://10.167.2.175:31825/v1` (Host: api.dify-plus.local)
- **管理员邮箱**: `myuwei@126.com`
- **管理员密码**: `Difyai123456`

### 2.3 LiteLLM 模型状态 (13个模型)

| 模型 | 状态 | 测试结果 |
|------|------|---------|
| qwen2.5:7b | ✅ 正常 | 响应 "Hello there, friend!" |
| qwen2.5:14b | ✅ 正常 | 响应 "Hi there!" |
| qwen2.5-coder:14b | ✅ 正常 | 响应 "Hello! How can I assist you today?" |
| bge-m3 (嵌入) | ✅ 正常 | 1024维向量 |
| qwen2.5:72b | ⚠️ 慢 | 需60-120秒冷启动 |
| qwen2.5:32b | ⚠️ 映射到72b | 需较长时间 |
| deepseek-r1:7b | ⚠️ 空响应 | R1模型推理内容在单独字段 |
| deepseek-r1:14b | ⚠️ 超时 | CPU推理较慢 |

---

## 三、测试套件结果

### 3.1 测试覆盖

测试套件 `dify_full_test_suite.py` 覆盖 12 个测试类别，共 37+ 个测试用例：

| 测试套件 | 测试数 | 通过 | 失败 | 说明 |
|---------|-------|------|------|------|
| 1. 认证与登录 | 6 | 5 | 1 | workspaces API 响应格式差异 |
| 2. 基础设施健康 | 4 | 4 | 0 | 全部通过 |
| 3. 模型提供商 | 4 | 4 | 0 | 全部通过 |
| 4. 应用管理 | 4 | 4 | 0 | 20个应用可见 |
| 5. 聊天功能 | 4 | 2 | 2 | 需模型提供商配置 |
| 6. 工作流 | 3 | 1 | 2 | Dify 1.14 API 路径变更 |
| 7. 知识库 | 4 | 3 | 1 | 检索路径变更 |
| 8. LLM模型连通性 | 4 | 1 | 3 | 大模型CPU推理超时 |
| 9. Code-Server | 2 | 0 | 2 | NodePort配置问题 |
| 10. 监控 | 2 | 1 | 1 | Grafana镜像问题 |
| 11. 文件操作 | 1 | 1 | 0 | 上传成功 |
| 12. 应用创建 | 1 | 0 | 1 | 需模型schema |
| **总计** | **39** | **26** | **13** | **66.7%** |

### 3.2 失败测试分析与建议

| 失败测试 | 根本原因 | 建议修复 |
|---------|---------|---------|
| 1.5 Get workspaces | API 返回 `{workspaces:[...]}` 而非 `{data:[...]}` | 修改测试脚本解析逻辑 |
| 5.3/5.4 Chat | 应用使用 gpt-3.5-turbo 默认模型，但模型提供商未配置 | 通过 Dify Web UI 重新配置模型提供商 |
| 6.2/6.3 Workflow | Dify 1.14 工作流 API 路径变更 | 更新为 `/console/api/apps/{id}/workflow` 新路径 |
| 7.4 Dataset retrieval | 检索 API 路径变更 | 更新为 Dify 1.14 新路径 |
| 8.2/8.3 大模型超时 | qwen2.5:14b/32b 在 CPU 上推理较慢 | 等待模型加载或增加超时时间 |
| 9.1/9.2 Code-Server | service 类型从 ClusterIP 改为 NodePort 后端口映射需验证 | 检查 NodePort 配置 |
| 10.1 Grafana | 镜像 ImagePullBackOff | 从 daocloud 镜像拉取 |
| 12.1 应用创建 | 插件 daemon 返回 model_schema: null | 需通过 Web UI 创建应用 |

---

## 四、剩余待解决问题

### 4.1 模型提供商重新配置 (需通过 Web UI 操作)

由于 RSA 私钥丢失，所有加密的模型提供商凭据被清除。API 方式添加模型因插件 daemon 的 model/schema 端点返回 404 而无法保存。需要通过 Dify Web UI 手动重新配置：

1. 登录 `https://10.167.2.175:31825` (Host: console.dify-plus.local)
2. 进入 **设置 → 模型供应商**
3. 配置 **OpenAI-API-compatible** 提供商:
   - API Key: `sk-ai-platform-master`
   - Endpoint: `http://litellm.ai-platform.svc.cluster.local:4000`
   - 添加模型: qwen2.5:7b, qwen2.5:14b, deepseek-r1:14b, bge-m3
4. 配置 **Ollama** 提供商:
   - Base URL: `http://ollama-worker:11434`
   - 添加模型: qwen2.5:7b, qwen2.5:14b 等

### 4.2 Grafana 镜像修复

```bash
# 在 master 节点执行
docker pull m.daocloud.io/docker.io/grafana/grafana:10.4.1
docker tag m.daocloud.io/docker.io/grafana/grafana:10.4.1 grafana/grafana:10.4.1
kubectl patch deploy/kube-prometheus-stack-grafana -n monitoring -p '{"spec":{"template":{"spec":{"containers":[{"name":"grafana","imagePullPolicy":"IfNotPresent"}]}}}}'
```

### 4.3 Code-Server NodePort 验证

已将 code-server service 从 ClusterIP 改为 NodePort (30085)，需验证 Pod 是否正确暴露端口。

---

## 五、文件清单

| 文件 | 用途 |
|------|------|
| `dify_full_test_suite.py` | 全功能测试套件 (12类39个测试) |
| `litellm-v2fix.Dockerfile` | LiteLLM x86-64-v2 兼容镜像构建文件 |
| `litellm-config-fixed.yaml` | 修正后的 LiteLLM 配置 (ollama-master→worker) |
| `DIFY-RECOVERY-REPORT.md` | 本报告 |

---

## 六、关键修复命令记录

### 6.1 构建兼容 LiteLLM 镜像
```bash
# 在 master 节点
docker build -f litellm-v2fix.Dockerfile -t ai-platform/litellm:custom .
docker tag ai-platform/litellm:custom 10.100.135.132:5000/litellm:custom
docker push 10.100.135.132:5000/litellm:custom
kubectl set image deploy/litellm -n ai-platform litellm=10.100.135.132:5000/litellm:custom
```

### 6.2 修复 ingress 路径剥离
```bash
kubectl annotate ingress dify-ingress -n dify nginx.ingress.kubernetes.io/rewrite-target-
```

### 6.3 重置管理员密码
```bash
# 使用 Dify 的 PBKDF2-HMAC-SHA256 算法生成哈希
python3 -c "
import base64, binascii, hashlib, secrets
password = 'Difyai123456'
salt = secrets.token_bytes(16)
dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
print(base64.b64encode(binascii.hexlify(dk)).decode())  # password
print(base64.b64encode(salt).decode())  # salt
"
# 更新数据库
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c \
  "UPDATE accounts SET password='<hash>', password_salt='<salt>' WHERE email='myuwei@126.com';"
```

### 6.4 修复 RSA 私钥
```bash
# 生成密钥对
python3 -c "
from Crypto.PublicKey import RSA
key = RSA.generate(2048)
with open('private.pem','wb') as f: f.write(key.export_key())
print(key.publickey().export_key().decode())
"
# 放置到存储 PVC
cp private.pem /opt/local-path-provisioner/pvc-cafc.../privkeys/<tenant_id>/
# 更新数据库公钥
kubectl exec -n dify-plus db-postgres-0 -- psql -U postgres -d dify -c \
  "UPDATE tenants SET encrypt_public_key='<public_key>' WHERE id='<tenant_id>';"
```

### 6.5 修复 OPENDAL 存储路径
```bash
kubectl patch cm dify-shared-config -n dify -p '{"data":{"OPENDAL_FS_ROOT":"/app/storage"}}'
kubectl rollout restart deploy/dify-api -n dify
```

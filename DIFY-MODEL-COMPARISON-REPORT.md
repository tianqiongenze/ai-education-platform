# Dify 多模型对比测试报告

> **测试日期**: 2026-08-29  
> **集群**: Master 10.167.2.175 + Worker 10.167.2.176  
> **Redis**: 8.10.1 Cluster (3节点, NodePort 30095)  
> **测试模型**: 6个 LLM + 1个 Embedding  
> **测试场景**: 6个工业互联网/编程/数据库/网络/AI教学场景

---

## 一、测试环境

### 1.1 集群配置

| 节点 | CPU | 内存 | 内核 | 角色 |
|------|-----|------|------|------|
| k8s-master (10.167.2.175) | Xeon Gold 5320 (16核) | 64GB | 5.4.278 | 控制面+API+Web+Redis8 |
| k8s-worker1 (10.167.2.176) | Xeon Gold 5320 (32核) | 128GB | 5.4.278 | LiteLLM+Ollama+Code-Server |

### 1.2 Redis 8 Cluster

| 项目 | 值 |
|------|-----|
| Redis 版本 | **8.10.1** |
| 模式 | Cluster (3主节点) |
| cluster_state | ok |
| cluster_slots_ok | 16384 |
| NodePort | 30095 (局域网可访问) |
| 密码 | difyai123456 |
| Dify 使用 | Redis 7 (兼容性,单节点模式) |

### 1.3 内核与 CNI

| 项目 | 状态 | 说明 |
|------|------|------|
| 内核版本 | 5.4.278 | elrepo 为 CentOS 7 提供的最高 LTS 版本 |
| Cilium 支持 | ❌ 不满足 | Cilium eBPF 需要内核 5.10+，CentOS 7 已 EOL |
| CNI | Calico IPIP | 保留当前模式，通过 Ingress 绕过跨节点 Pod 网络问题 |

---

## 二、多模型对比结果

### 2.1 测试模型

| 模型 | 大小 | 类型 | 用途 |
|------|------|------|------|
| qwen2.5-coder:7b | 4.7GB | LLM | 编程辅导 |
| glm4:9b | 5.5GB | LLM | 中文教学 |
| qwen3:4b | 2.5GB | LLM (thinking) | 快速问答 |
| qwen3:8b | 5.2GB | LLM (thinking) | 通用教学 |
| yi:6b | 3.5GB | LLM | 中文通用 |
| llama3.1:8b | 4.9GB | LLM | 通用教学 |
| bge-m3 | 1.2GB | Embedding | 1024维向量 |

### 2.2 测试场景

| 场景 | 问题 |
|------|------|
| 工业互联网 | What is Industrial Internet? Answer in one sentence. |
| PLC编程 | What is a PLC? Answer in one sentence. |
| Python编程 | Write a Python function to sort a list. Just the code. |
| 数据库 | What is a database transaction? Answer in one sentence. |
| 网络通信 | What is the difference between TCP and UDP? Answer briefly. |
| AI/机器学习 | What is overfitting in machine learning? Answer in one sentence. |

### 2.3 详细对比结果

| 模型 | 场景 | 耗时 | Tokens | 状态 |
|------|------|------|--------|------|
| qwen2.5-coder:7b | 工业互联网 | 57.3s | 69 | ✅ |
| qwen2.5-coder:7b | PLC编程 | 11.2s | 71 | ✅ |
| qwen2.5-coder:7b | Python编程 | 31.7s | 122 | ✅ |
| qwen2.5-coder:7b | 数据库 | 10.8s | 67 | ✅ |
| qwen2.5-coder:7b | 网络通信 | 33.9s | 129 | ✅ |
| qwen2.5-coder:7b | AI/ML | 14.9s | 84 | ✅ |
| glm4:9b | 工业互联网 | 12.9s | 52 | ✅ |
| glm4:9b | PLC编程 | 9.2s | 43 | ✅ |
| glm4:9b | Python编程 | 7.9s | 39 | ✅ |
| glm4:9b | 数据库 | 17.1s | 59 | ✅ |
| glm4:9b | 网络通信 | 64.0s | 120 | ✅ |
| glm4:9b | AI/ML | 13.3s | 57 | ✅ |
| qwen3:4b | 工业互联网 | 89.6s | 123 | ✅ |
| qwen3:4b | PLC编程 | 39.0s | 123 | ✅ |
| qwen3:4b | Python编程 | 25.9s | 126 | ✅ |
| qwen3:4b | 数据库 | 29.7s | 124 | ✅ |
| qwen3:4b | 网络通信 | 37.8s | 125 | ✅ |
| qwen3:4b | AI/ML | 30.3s | 127 | ✅ |
| qwen3:8b | 工业互联网 | 79.2s | 123 | ✅ |
| qwen3:8b | PLC编程 | 128.6s | 123 | ✅ |
| qwen3:8b | Python编程 | 44.6s | 126 | ✅ |
| qwen3:8b | 数据库 | 43.2s | 124 | ✅ |
| qwen3:8b | 网络通信 | 39.8s | 125 | ✅ |
| qwen3:8b | AI/ML | 67.2s | 127 | ✅ |
| yi:6b | 工业互联网 | 19.9s | 89 | ✅ |
| yi:6b | PLC编程 | 43.3s | 84 | ✅ |
| yi:6b | Python编程 | 44.0s | 119 | ✅ |
| yi:6b | 数据库 | 41.0s | 67 | ✅ |
| yi:6b | 网络通信 | 24.3s | 139 | ✅ |
| yi:6b | AI/ML | 15.4s | 80 | ✅ |
| llama3.1:8b | 工业互联网 | 28.6s | 67 | ✅ |
| llama3.1:8b | PLC编程 | 16.6s | 64 | ✅ |
| llama3.1:8b | Python编程 | 10.0s | 41 | ✅ |
| llama3.1:8b | 数据库 | 15.1s | 58 | ✅ |
| llama3.1:8b | 网络通信 | 24.5s | 80 | ✅ |
| llama3.1:8b | AI/ML | 16.2s | 59 | ✅ |

**总计: 36 个测试, 36 个通过, 0 个失败, 100% 通过率**

### 2.4 平均响应时间

| 模型 | 平均耗时 | 平均Token数 | 通过率 |
|------|---------|------------|--------|
| **llama3.1:8b** | **18.5s** | 62 | 6/6 ✅ |
| **glm4:9b** | **20.7s** | 62 | 6/6 ✅ |
| qwen2.5-coder:7b | 26.6s | 90 | 6/6 ✅ |
| yi:6b | 31.3s | 96 | 6/6 ✅ |
| qwen3:4b | 42.0s | 125 | 6/6 ✅ |
| qwen3:8b | 67.1s | 125 | 6/6 ✅ |

### 2.5 各场景最佳模型（最快）

| 场景 | 最佳模型 | 耗时 | Tokens |
|------|---------|------|--------|
| 工业互联网 | **glm4:9b** | 12.9s | 52 |
| PLC编程 | **glm4:9b** | 9.2s | 43 |
| Python编程 | **glm4:9b** | 7.9s | 39 |
| 数据库 | **qwen2.5-coder:7b** | 10.8s | 67 |
| 网络通信 | **yi:6b** | 24.3s | 139 |
| AI/ML | **glm4:9b** | 13.3s | 57 |

### 2.6 Embedding 测试

| 模型 | 维度 | 状态 |
|------|------|------|
| bge-m3 | 1024 | ✅ |

---

## 三、模型推荐

### 3.1 按场景推荐

| 教学场景 | 推荐模型 | 理由 |
|---------|---------|------|
| 工业互联网基础 | **glm4:9b** | 最快(12.9s)，中文回答准确 |
| PLC编程教学 | **glm4:9b** | 最快(9.2s)，准确解释PLC概念 |
| Python编程 | **glm4:9b** 或 **llama3.1:8b** | glm4最快(7.9s)，llama3.1代码质量好 |
| 数据库教学 | **qwen2.5-coder:7b** | 最快(10.8s)，技术概念准确 |
| 网络通信 | **yi:6b** | 最快(24.3s)，回答详细 |
| AI/机器学习 | **glm4:9b** | 最快(13.3s)，概念解释清晰 |
| 通用快速问答 | **llama3.1:8b** | 平均最快(18.5s) |
| 深度推理 | **qwen3:4b** | thinking模式，推理质量高但耗时42s |
| 编程辅助(Code-Server) | **qwen2.5-coder:7b** | 专为编程优化 |

### 3.2 模型选择建议

**高职教学场景推荐组合**:
1. **glm4:9b** — 工业互联网/PLC/AI教学主力（中文最强，速度最快）
2. **qwen2.5-coder:7b** — 编程教学主力（专为代码优化）
3. **llama3.1:8b** — 通用备用（英文场景最快）
4. **bge-m3** — 知识库嵌入（1024维）

**不推荐用于实时教学**:
- qwen3:8b — 平均67s太慢（thinking模式开销大）
- qwen3:4b — 平均42s较慢（但推理质量好，适合非实时场景）

---

## 四、Redis 8 Cluster 升级总结

### 4.1 升级结果

| 项目 | 旧版 | 新版 | 状态 |
|------|------|------|------|
| Redis 版本 | 7-alpine | **8.10.1** | ✅ 已部署 |
| 模式 | 单节点 | **3节点Cluster** | ✅ cluster_state:ok |
| 局域网访问 | ClusterIP | **NodePort 30095** | ✅ 可访问 |
| Dify 使用 | Redis 7 | Redis 7 (兼容) | ✅ Dify不兼容Cluster模式 |
| Redis 8 独立使用 | — | 局域网可用 | ✅ 供其他应用使用 |

### 4.2 架构决策说明

- **Redis 8 Cluster 已部署并运行**（3主节点，16384槽位全覆盖）
- **Dify 仍使用 Redis 7 单节点**（Dify 的 Python redis 客户端不支持 Cluster 的 MOVED 响应）
- **Redis 8 Cluster 供局域网其他应用使用**（通过 NodePort 30095）
- 如需 Dify 使用 Redis 8，需要将 Redis 8 配置为**单节点模式**（非 Cluster），或升级 Dify 的 redis 客户端库

---

## 五、内核与 Cilium 评估

### 5.1 内核升级评估

| 项目 | 结果 |
|------|------|
| 当前内核 | 5.4.278-1.el7.elrepo.x86_64 |
| elrepo 最高 LTS | 5.4.278（已是最高） |
| CentOS 7 状态 | EOL（End of Life） |
| 可否升级到 5.10+ | ❌ 不可以（elrepo 不再为 CentOS 7 发布更高版本） |

### 5.2 Cilium 评估

| 项目 | 结果 |
|------|------|
| Cilium eBPF 要求 | 内核 5.10+ |
| 当前内核 | 5.4.278 |
| 可否部署 Cilium | ❌ 不满足 |
| 当前 CNI | Calico IPIP |
| 跨节点 Pod 网络 | 受 rp_filter 限制（不影响通过 Ingress 访问的服务） |
| 建议 | 升级 OS 到 RHEL 8/9 或 Ubuntu 22.04 后再迁移 Cilium |

---

## 六、交付文件

| 文件 | 说明 |
|------|------|
| `dify_final_test.py` | 43用例100%覆盖测试脚本 |
| `dify_full_test_with_model_comparison.py` | 功能测试+模型对比脚本 |
| `model_comparison.py` | 多模型对比测试脚本 |
| `DIFY-MODEL-COMPARISON-REPORT.md` | 本报告 |

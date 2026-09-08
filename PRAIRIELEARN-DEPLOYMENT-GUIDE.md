# PrairieLearn 部署指南

> 集群环境：2 节点 K8s（master `10.167.2.175` 16C/128G，worker `10.167.2.176` 32C/128G）
> 部署日期：2026-09-07
> 部署文件：`D:\dify-install\prairielearn-k8s.yaml`、`D:\dify-install\Dockerfile.prairielearn`

---

## 一、架构总览

PrairieLearn 是一个开源的在线作业与考试平台，最初由伊利诺伊大学香槟分校（UIUC）开发，支持以 HTML/JavaScript/Python 编写任意题型，并提供代码自动评测（external grading）与学生工作区（workspace）能力。本次部署在已有 K8s 集群上构建，整体架构如下：

```
                       ┌─────────────────────────────────────────────┐
                       │            用户浏览器 / 终端                  │
                       └────────────────────┬────────────────────────┘
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 │  NodePort 30093  (任意节点 IP:30093)                  │
                 │  Ingress 31825 (Host: prairielearn.local)           │
                 │  Nginx Ingress Controller (ingress-nginx 命名空间)    │
                 └──────────────────────────┬──────────────────────────┘
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 │  Namespace: prairielearn                              │
                 │  Deployment: prairielearn (1 副本, 调度到 worker1)    │
                 │  容器端口: 3000                                       │
                 │  ConfigMap: config.json + entrypoint.sh              │
                 │  PVC: course-data 20Gi + workspace 10Gi (local-path)  │
                 │                                                       │
                 │  容器内: PostgreSQL 16 + pgvector (本地数据库)          │
                 └──────┬───────────────────────────────┬───────────────┘
                        │                               │
          ┌─────────────┴──────────────┐   ┌────────────┴──────────────┐
          │  CockroachDB v24.3.11       │   │  Redis 8 集群              │
          │  命名空间: infra (备用)       │   │  命名空间: dify-plus        │
          │  数据库: prairielearn (已建)  │   │  服务: redis.dify-plus      │
          │  注: CRDB 不支持 PL/pgSQL    │   │  端口: 6379  密码: difyai123456│
       │  DO 块, 实际使用本地 PG16      │   │  (Redis Cluster 模式)      │
          └─────────────────────────────┘   └───────────────────────────┘
```

### 1.1 组件说明

| 组件 | 位置 | 说明 |
|------|------|------|
| PrairieLearn Web | `prairielearn` 命名空间 | Node.js 24 应用，监听 3000 端口 |
| 数据库 | 容器内（本地 PG16） | PostgreSQL 16 + pgvector，由 entrypoint 启动 |
| 缓存 | `dify-plus` 命名空间 | 复用既有 Redis 8 集群（密码 `difyai123456`） |
| 镜像仓库 | `10.100.135.132:5000` | 本地 Docker Registry |
| Ingress | `ingress-nginx` 命名空间 | 复用 Nginx Ingress，31825(HTTPS)/32231(HTTP) |
| 存储 | `local-path` StorageClass | PVC 随 Pod 绑定到 worker1 本地盘 |

### 1.2 端口分配

| 端口 | 用途 |
|------|------|
| 30093 | PrairieLearn Web（NodePort） |
| 30257 | CockroachDB SQL（既有，备用） |
| 31825 | Nginx Ingress HTTPS（既有） |

> 注意：原计划使用 30090，但该端口已被 `dify-plus` 命名空间的 `redis8-node-0` 占用，故改用 **30093**。

---

## 二、数据库配置

### 2.1 数据库选择说明

PrairieLearn 原生使用 PostgreSQL，其迁移脚本大量使用 PL/pgSQL 的 `DO $$ ... $$;`
匿名代码块和 `ALTER TYPE ... ADD VALUE` 等语法。CockroachDB 虽然提供 PostgreSQL
线缆协议兼容，但**不支持 PL/pgSQL 的 `DO` 代码块**，也无法在事务块内执行
`ALTER TYPE ... ADD VALUE`。因此，PrairieLearn 的数据库迁移无法直接在 CockroachDB
上运行。

**最终方案**：在 PrairieLearn 容器内运行一个**本地 PostgreSQL 16**实例（通过
`pg_ctl` 启动），用于数据库存储。CockroachDB 上的 `prairielearn` 数据库仍保留
以备将来使用。

### 2.2 CockroachDB 数据库（已创建，备用）

```bash
kubectl exec -n infra cockroachdb-a-0 -- \
  /cockroach-binary/cockroach sql --insecure \
  --host=cockroachdb.infra.svc.cluster.local:26257 \
  -e "CREATE DATABASE IF NOT EXISTS prairielearn;"
```

### 2.3 本地 PostgreSQL 16（实际使用）

容器镜像中预装了 PostgreSQL 16（通过 CentOS Stream 8 的 `postgresql:16` 模块流）。
启动时由 entrypoint 脚本通过 `pg_ctl` 启动，运行迁移后保持运行。

配置（config.json）:
```json
{
  "postgresqlUser": "root",
  "postgresqlDatabase": "prairielearn",
  "postgresqlHost": "localhost",
  "postgresqlPoolSize": 20
}
```

### 2.4 pgvector 扩展

PrairieLearn 的 AI 题目生成功能需要 pgvector 扩展。镜像中从源码编译安装了
pgvector v0.7.4，供 `CREATE EXTENSION vector` 迁移使用。

### 2.5 数据库迁移

PrairieLearn 启动时通过 `node dist/server.js --migrate-and-exit` 执行 SQL 迁移
（`database/` 目录下的 `*.sql` 文件）。迁移脚本在 entrypoint 中自动运行。

---

## 三、Redis 配置

复用 `dify-plus` 命名空间的 Redis 8 集群（密码 `difyai123456`）。

```json
{
  "redisUrl": "redis://default:difyai123456@redis.dify-plus.svc.cluster.local:6379/0",
  "nonVolatileRedisUrl": "redis://default:difyai123456@redis.dify-plus.svc.cluster.local:6379/1"
}
```

---

## 四、镜像构建（离线环境）

集群 worker 节点无外网，Docker Hub 和 GHCR 被防火墙拦截。通过 master 节点
从可达的源构建镜像并推送到本地仓库。

### 4.1 网络可达性

| 源 | 可达性 |
|----|--------|
| Docker Hub | 不可达 |
| GHCR | 不可达 |
| quay.io | 可达 |
| mirrors.aliyun.com | 可达 |
| nodejs.org | 可达 |
| npm registry | 可达 |
| pypi | 可达 |
| codeload.github.com | 可达 |

### 4.2 构建步骤

```bash
# 在 master 节点
cd /tmp
curl -4 -sL -o prairielearn-master.tar.gz https://codeload.github.com/PrairieLearn/PrairieLearn/tar.gz/master
tar xzf prairielearn-master.tar.gz
cp -r PrairieLearn-master /tmp/pl-build-context

# 使用 Dockerfile.prairielearn 构建（基于 quay.io/centos:stream8 + Aliyun 镜像源）
cd /tmp/pl-build-context
docker build -t 10.100.135.132:5000/prairielearn:latest -f Dockerfile .
docker push 10.100.135.132:5000/prairielearn:latest
```

### 4.3 镜像中的关键适配

- 基础镜像: `quay.io/centos/centos:stream8`（CentOS Stream 9 需要 x86-64-v2，本集群 CPU 不支持）
- 系统包: Aliyun 镜像源 + PowerTools + EPEL
- Node.js 24: 从 nodejs.org 下载二进制安装
- Python 3.13: 从 python.org 源码编译（uv 从 GitHub 下载 cpython 被 block）
- gcc-toolset-12: 提供 GCC 12 以编译 C++20 代码（bind-mount 原生插件需要）
- pgvector v0.7.4: 从源码编译安装
- sharp 模块: 预编译二进制需要 x86-64-v2，构建后替换为 no-op 桩

---

## 五、部署与运维

### 5.1 应用清单

```bash
kubectl apply -f prairielearn-k8s.yaml
```

### 5.2 访问

```bash
# NodePort
curl -I http://10.167.2.176:30093/
curl http://10.167.2.176:30093/pl/webhooks/ping

# Ingress (需 hosts 解析 prairielearn.local)
curl -I -H "Host: prairielearn.local" http://10.167.2.175:32231/
```

### 5.3 常用命令

```bash
kubectl get pods -n prairielearn -o wide
kubectl logs -n prairielearn -l app.kubernetes.io/name=prairielearn -f
kubectl exec -n prairielearn -it deploy/prairielearn -- bash
kubectl rollout restart -n prairielearn deploy/prairielearn
```

---

## 六、课程创建

PrairieLearn 采用"课程即 Git 仓库"的理念。

### 6.1 创建课程

```bash
kubectl exec -n prairielearn -it deploy/prairielearn -- bash
mkdir -p /data/courses/my-course && cd /data/courses/my-course && git init
```

### 6.2 课程信息文件

`infoCourse.json`:
```json
{
  "uuid": "00000000-0000-0000-0000-000000000001",
  "name": "我的课程",
  "title": "编程基础",
  "timezone": "Asia/Shanghai"
}
```

---

## 七、题型与代码自动评测

### 7.1 题型概览

| 题型 | 说明 |
|------|------|
| MultipleChoice | 单选/多选 |
| Checkbox | 多选 |
| NumericalInput | 数值填空 |
| StringInput | 文本填空 |
| File | 文件上传 |
| Code | 代码编辑器 + 自动评测 |

### 7.2 Python 自动评测

`info.json` 配置:
```json
{
  "type": "v3",
  "gradingMethod": "External",
  "externalGradingOptions": {
    "enabled": true,
    "image": "prairielearn/grader-python",
    "entrypoint": "/python_autograder/run.sh",
    "timeout": 30
  }
}
```

### 7.3 C/Java 自动评测

评测镜像使用 `prairielearn/grader-c` 和 `prairielearn/grader-java`。
离线环境需预先推送到本地仓库。

### 7.4 使用 Ollama 辅助评测（可选）

集群 worker 上运行 Ollama（`qwen2.5-coder:7b`，NodePort 30086）。

---

## 八、与 JupyterHub 集成

集群 `jupyterhub` 命名空间已部署 JupyterHub（NodePort 30089）。

- PrairieLearn 的 Workspace 功能可让学生获得 Jupyter 环境
- 可配置 LTI 1.3 实现 SSO
- 网络: `jupyterhub.jupyterhub.svc.cluster.local:8000`

---

## 九、学生注册与选课

- 本地账号、LTI 对接、SAML/SSO
- 教师创建 Section → 生成选课链接 → 学生加入
- 支持 CSV 批量导入

---

## 十、评分工作流

```
教师创建作业 → 学生提交 → 自动评测(代码题)/即时评分(客观题) → 分数入库 → 教师复核 → 发布
```

---

## 十一、关键文件路径

| 文件 | 说明 |
|------|------|
| `D:\dify-install\prairielearn-k8s.yaml` | K8s 部署清单 |
| `D:\dify-install\Dockerfile.prairielearn` | 镜像构建文件 |
| `D:\dify-install\PRAIRIELEARN-DEPLOYMENT-GUIDE.md` | 本指南 |

---

## 附：已知限制

1. **NumPy x86-64-v2**: 容器内 Python 的 numpy 预编译包需要 x86-64-v2，Python 题目
   执行（zygote）会报错。服务器本身正常运行，但代码评测的 Python 执行需要后续
   用源码编译 numpy 解决。
2. **sharp 模块**: 已替换为 no-op 桩，图片处理功能不可用，不影响核心教学功能。
3. **imagePullPolicy**: 使用 `Always` 确保 worker 拉取正确镜像版本。

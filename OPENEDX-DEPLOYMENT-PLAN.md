# Open edX 在 Kubernetes 上的部署方案

> 文档版本：2026-09-07
> 目标集群：2 节点 K8s（master 10.167.2.175 / worker 10.167.2.176）
> 部署工具：Tutor（Open edX 官方推荐）

---

## 目录

1. [架构概览](#1-架构概览)
2. [关键可行性结论（必读）](#2-关键可行性结论必读)
3. [硬件资源评估与分配](#3-硬件资源评估与分配)
4. [前置条件与依赖](#4-前置条件与依赖)
5. [气隙环境镜像准备](#5-气隙环境镜像准备)
6. [使用 Tutor 逐步部署](#6-使用-tutor-逐步部署)
7. [CockroachDB 与 Open edX 数据库的关系](#7-cockroachdb-与-openedx-数据库的关系)
8. [与现有 Redis 的集成](#8-与现有-redis-的集成)
9. [与现有 Ollama 的 AI 集成](#9-与现有-ollama-的-ai-集成)
10. [通过 LTI 与 JupyterHub 集成](#10-通过-lti-与-jupyterhub-集成)
11. [课程创建流程](#11-课程创建流程)
12. [用户管理](#12-用户管理)
13. [备份与运维](#13-备份与运维)
14. [已知限制与替代方案](#14-已知限制与替代方案)

---

## 1. 架构概览

### 1.1 Open edX 核心组件

Open edX 是一个由 Axim Collaborative 维护的开源在线学习平台。通过 Tutor（官方推荐的 Docker 化部署工具）部署时，包含以下核心组件：

| 组件 | 说明 | 在 Tutor 中的角色 |
|------|------|-------------------|
| **LMS**（Learning Management System） | 面向学习者的前端。学生在此注册、选课、学习、考试、查看成绩 | 核心 Web 应用，uWSGI 部署 |
| **Studio / CMS**（Content Management System） | 面向教师的课程创作工具。创建课程、编排内容、管理学生 | 核心 Web 应用，uWSGI 部署 |
| **LMS Worker / CMS Worker** | Celery 异步任务处理器，处理批量作业、成绩计算、邮件发送等 | Celery worker 进程 |
| **MySQL 8.4** | 关系型数据库，存储用户、课程注册、成绩等结构化数据 | **必须使用 MySQL**，不支持 PostgreSQL |
| **MongoDB 7.0** | 文档数据库，存储课程内容结构（XBlock 树）、模块化内容 | 内置或可外接 |
| **Redis 7.4** | Celery 消息代理 + Django 缓存后端 | 内置或可外接（推荐用现有的） |
| **Meilisearch v1.36** | 课程内容搜索引擎（Tutor 用 Meilisearch 替代了 Elasticsearch） | 内置 |
| **Caddy** | 反向代理 / 负载均衡器，自动管理 TLS 证书 | K8s 中以 LoadBalancer 部署 |
| **SMTP（exim-relay）** | 内置邮件转发服务 | 内置或可外接 |
| **Permissions** | 文件权限初始化镜像 | 辅助容器 |

### 1.2 在 Kubernetes 中的拓扑

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         K8s Namespace: openedx                          │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐               │
│  │   Caddy     │───▶│   LMS Pod   │    │  CMS Pod    │               │
│  │ (LoadBalancer│    │ (uWSGI x2)  │    │ (uWSGI x2)  │               │
│  │  /Ingress)  │    └──────┬──────┘    └──────┬──────┘               │
│  └──────┬──────┘           │                  │                       │
│         │                  ▼                  ▼                       │
│         │         ┌────────────────────────────────┐                  │
│         │         │  LMS/CMS Celery Workers         │                  │
│         │         └────────────────────────────────┘                  │
│         │                                                              │
│  ┌──────┴──────────────────────────────────────────────────────────┐  │
│  │                    数据层                                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │  │
│  │  │  MySQL   │  │ MongoDB  │  │  Redis   │  │  Meilisearch │    │  │
│  │  │ (PVC)    │  │ (PVC)    │  │          │  │              │    │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  可选: MinIO (S3 兼容对象存储) / SMTP exim-relay                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                          │                        │
         ▼                          ▼                        ▼
  ┌──────────────┐         ┌──────────────┐        ┌──────────────────┐
  │ 现有 CockroachDB│       │ 现有 Redis   │        │ 现有 Ollama AI   │
  │ (MySQL 无法替代) │       │ (可复用)      │        │ (AI Extensions) │
  └──────────────┘         └──────────────┘        └──────────────────┘
```

### 1.3 数据流说明

1. **用户访问**：用户通过 Nginx Ingress -> Caddy (LoadBalancer) -> LMS/CMS
2. **结构化数据**：LMS/CMS -> MySQL（用户、注册、成绩）
3. **课程内容**：LMS/CMS -> MongoDB（课程大纲、XBlock 结构）
4. **缓存/队列**：LMS/CMS -> Redis（Django 缓存 + Celery 代理）
5. **搜索**：LMS/CMS -> Meilisearch（课程搜索索引）
6. **异步任务**：Celery workers 从 Redis 消费任务，操作 MySQL/MongoDB

---

## 2. 关键可行性结论（必读）

在深入部署步骤之前，以下是研究得出的关键结论：

### 2.1 CockroachDB 无法替代 MySQL（重大限制）

**这是最重要的发现。** Open edX 的数据库引擎在 Tutor 模板中被硬编码为 MySQL：

```yaml
# Tutor 源码: tutor/templates/apps/openedx/config/partials/auth.yml
DATABASES:
  default:
    ENGINE: "django.db.backends.mysql"   # ← 硬编码为 MySQL
    HOST: "{{ MYSQL_HOST }}"
    PORT: {{ MYSQL_PORT }}
    NAME: "{{ OPENEDX_MYSQL_DATABASE }}"
    USER: "{{ OPENEDX_MYSQL_USERNAME }}"
    PASSWORD: "{{ OPENEDX_MYSQL_PASSWORD }}"
    ATOMIC_REQUESTS: true
    OPTIONS:
      init_command: "SET sql_mode='STRICT_TRANS_TABLES'"
```

- Open edX (edx-platform) 基于 Django ORM，但其迁移脚本和 SQL 使用了 MySQL 特有语法。
- CockroachDB 虽然声称 PostgreSQL 兼容，但 Open edX **不使用 PostgreSQL**，而是直接使用 `django.db.backends.mysql` 引擎。
- Tutor 文档明确要求外部数据库必须使用 **MySQL 8.4** 版本。
- **结论：无法将 CockroachDB 作为 Open edX 的关系型数据库。必须在集群中部署独立的 MySQL 实例。**

### 2.2 资源需求分析

| 项目 | Tutor 最低要求 | Tutor 推荐配置 | 本集群实际可用 |
|------|---------------|---------------|--------------|
| RAM (每节点) | 4 GB | 8 GB | 128 GB（充足） |
| CPU (每节点) | 2 核 | 4 核 | 16-32 核（充足） |
| 磁盘 | 8 GB | 25 GB | 需评估 |
| **Open edX 总体推荐** | - | **8 GB RAM / 4 vCPU** | 需与现有服务共享 |

**资源瓶颈分析**：

集群总资源：48 vCPU / 256 GB RAM。但已有服务（JupyterHub、Code-Server、Ollama、CockroachDB、Redis、Dify、Nginx Ingress）已经占用大量资源。关键约束：

- **Ollama** 通常占用 8-16 GB RAM（模型加载）
- **Dify** 通常占用 4-8 GB RAM
- **JupyterHub** 根据并发用户数占用 4-16 GB RAM
- **CockroachDB** 占用 4-8 GB RAM

预估现有服务已占用 **20-48 GB RAM** 和 **8-16 vCPU**。Open edX 推荐至少 **8 GB RAM / 4 vCPU**，加上 MySQL + MongoDB + Meilisearch 各需 1-2 GB。

**结论：集群 RAM 充足（256 GB），但需合理分配，避免节点过载。建议将 Open edX 主要工作负载部署到 worker 节点（32 CPU）。**

### 2.3 气隙部署可行性

- Tutor 支持自定义 Docker 镜像注册表（`DOCKER_REGISTRY` 配置项）
- 所有镜像可通过 master 节点下载后推送到本地注册表 `10.100.135.132:5000`
- Tutor 的 `tutor images push` 命令可推送到自定义注册表
- **结论：气隙部署可行，但准备工作量较大（需预拉取约 10+ 个镜像）。**

### 2.4 总体可行性评估

| 维度 | 评估 | 说明 |
|------|------|------|
| 资源 | 可行 | 集群资源充足 |
| 数据库 | 需额外部署 MySQL | CockroachDB 不可用 |
| 气隙 | 可行 | 需镜像预拉取 |
| K8s 兼容 | 可行 | Tutor 原生支持 K8s |
| 复杂度 | 中高 | Open edX 是重量级平台 |

---

## 3. 硬件资源评估与分配

### 3.1 现有服务资源占用估算

| 服务 | 预估 RAM | 预估 CPU | 部署节点 |
|------|---------|---------|---------|
| Nginx Ingress | 0.5 GB | 0.5 核 | master |
| CockroachDB | 4-8 GB | 2-4 核 | master/worker |
| Redis | 1-2 GB | 0.5 核 | worker |
| Ollama AI | 8-16 GB | 2-4 核 | worker |
| Dify | 4-8 GB | 2-4 核 | worker |
| JupyterHub | 4-16 GB | 2-8 核 | worker |
| Code-Server | 1-2 GB | 0.5-1 核 | worker |
| **小计** | **22.5-52.5 GB** | **9.5-21.5 核** | - |

### 3.2 Open edX 资源分配建议

| 组件 | 建议 RAM | 建议 CPU | 建议 PVC | 部署节点 |
|------|---------|---------|---------|---------|
| LMS（2 workers x ~500MB） | 2 GB | 1-2 核 | - | worker |
| CMS/Studio（2 workers x ~500MB） | 2 GB | 1-2 核 | - | worker |
| LMS/CMS Celery Workers | 1-2 GB | 1 核 | - | worker |
| MySQL 8.4 | 2-4 GB | 1-2 核 | 20-50 GB | worker |
| MongoDB 7.0 | 1-2 GB | 0.5-1 核 | 10-20 GB | worker |
| Redis（可复用现有） | 0-1 GB | 0.25 核 | - | worker |
| Meilisearch | 1 GB | 0.5 核 | 5 GB | worker |
| Caddy | 0.5 GB | 0.25 核 | - | master/worker |
| SMTP exim-relay | 0.25 GB | 0.1 核 | - | worker |
| **Open edX 总计** | **10.75-14.75 GB** | **5.6-8.6 核** | **35-75 GB** | - |

### 3.3 资源分配总结

| 节点 | 总资源 | 已用（估算） | Open edX 新增 | 剩余 |
|------|-------|------------|-------------|------|
| **master** (10.167.2.175) | 16 CPU / 128 GB | ~5-10 GB / 2-5 核 | ~1-2 GB（Caddy 等） | 充足 |
| **worker** (10.167.2.176) | 32 CPU / 128 GB | ~18-42 GB / 8-16 核 | ~9-13 GB / 5-7 核 | 充足 |

**结论：集群资源充足，可支撑 Open edX 部署。建议将 Open edX 主要工作负载调度到 worker 节点。**

### 3.4 建议 NodePort 分配

| 服务 | NodePort | 说明 |
|------|---------|------|
| Caddy (HTTP) | 30080 | Open edX 主入口 |
| Caddy (HTTPS) | 30443 | HTTPS 入口 |
| MySQL (调试用) | 30306 | 仅调试，生产建议不暴露 |
| MinIO Console（可选） | 30090 | 对象存储控制台 |

---

## 4. 前置条件与依赖

### 4.1 Master 节点环境准备

在 master 节点（10.167.2.175）上安装 Tutor 和相关工具：

```bash
# 1. 安装 Python 3.10+ (如未安装)
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# 2. 安装 Docker (master 节点需要 Docker 来构建/拉取镜像)
# 参考: https://docs.docker.com/engine/install/
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# 3. 安装 kubectl (如未安装)
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 4. 创建 Tutor 虚拟环境
python3 -m venv /opt/tutor-env
source /opt/tutor-env/bin/activate

# 5. 安装 Tutor（完整安装，含所有官方插件）
pip install "tutor[full]"

# 验证
tutor --version
```

### 4.2 K8s 集群验证

```bash
# 确认集群状态
kubectl get nodes
kubectl get nodes -o wide

# 确认现有服务命名空间
kubectl get namespaces
kubectl get pods --all-namespaces

# 确认 Nginx Ingress 运行正常
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

# 确认本地 Docker 注册表可达
curl -s http://10.100.135.132:5000/v2/_catalog | head -50
```

### 4.3 Tutor 版本与 Open edX 版本

当前 Tutor 稳定版本为 **v22.0.2**，对应的 Open edX 版本代号为 **Verawood**（`release/verawood.1`）。

```bash
# 确认 Tutor 版本
tutor --version
# 预期输出: Tutor 22.0.2
```

### 4.4 DNS 规划

在气隙环境中，使用内部 DNS 或 hosts 文件。需要两个域名：

| 域名 | 用途 | 解析到 |
|------|------|-------|
| `openedx.local` | LMS（学习者入口） | 集群 Ingress / NodePort |
| `studio.openedx.local` | Studio/CMS（课程创作） | 集群 Ingress / NodePort |

在所有需要访问的机器上添加 hosts 记录：
```
10.167.2.176  openedx.local
10.167.2.176  studio.openedx.local
```

---

## 5. 气隙环境镜像准备

### 5.1 需要预拉取的镜像列表

Open edX 通过 Tutor 部署需要以下 Docker 镜像：

| 镜像 | 默认来源 | 说明 |
|------|---------|------|
| `overhangio/openedx:{version}` | Docker Hub | LMS/CMS 主镜像（~2 GB） |
| `overhangio/openedx-permissions:{version}` | Docker Hub | 权限初始化 |
| `mysql:8.4.11` | Docker Hub | MySQL 数据库 |
| `mongo:7.0.39` | Docker Hub | MongoDB |
| `redis:7.4.10` | Docker Hub | Redis（如不复用现有） |
| `getmeili/meilisearch:v1.36.0` | Docker Hub | 搜索引擎 |
| `caddy:2.11.4` | Docker Hub | 反向代理 |
| `devture/exim-relay:4.96-r1-0` | Docker Hub | SMTP |
| MFE 镜像（多个） | Docker Hub | 前端微服务 |

### 5.2 通过 Master 节点拉取并推送镜像

由于集群无外网，通过 master 节点（唯一有外网访问的节点）拉取镜像，再推送到本地注册表：

```bash
#!/bin/bash
# === 镜像预拉取脚本 ===
# 在 master 节点执行

LOCAL_REGISTRY="10.100.135.132:5000"
TUTOR_VERSION="22.0.2"  # 根据 tutor --version 调整

# 定义镜像列表
declare -a IMAGES=(
  "docker.io/overhangio/openedx:${TUTOR_VERSION}"
  "docker.io/overhangio/openedx-permissions:${TUTOR_VERSION}"
  "docker.io/mysql:8.4.11"
  "docker.io/mongo:7.0.39"
  "docker.io/redis:7.4.10"
  "docker.io/getmeili/meilisearch:v1.36.0"
  "docker.io/caddy:2.11.4"
  "docker.io/devture/exim-relay:4.96-r1-0"
)

# 拉取、重标记、推送到本地注册表
for image in "${IMAGES[@]}"; do
  echo "=== Processing: $image ==="
  docker pull "$image"

  # 构建本地注册表镜像名
  local_image="${LOCAL_REGISTRY}/$(echo "$image" | sed 's|docker.io/||')"

  # 重标记
  docker tag "$image" "$local_image"

  # 推送到本地注册表
  docker push "$local_image"

  echo "=== Pushed: $local_image ==="
done

echo "=== All images pushed to local registry ==="
```

### 5.3 配置 Tutor 使用本地注册表

```bash
# 设置 Tutor 使用本地注册表
tutor config save \
  --set DOCKER_REGISTRY="10.100.135.132:5000/"
```

这会将所有镜像引用从 `docker.io/xxx` 改为 `10.100.135.132:5000/xxx`。

### 5.4 构建自定义 Open edX 镜像（如果需要 XBlock）

如果需要安装额外 XBlock（如 codejail、jupyter），需要在 master 节点构建自定义镜像：

```bash
# 在 master 节点执行（需要外网访问来下载 pip 包）

# 添加额外的 pip 依赖
tutor config save \
  --append OPENEDX_EXTRA_PIP_REQUIREMENTS="edx-xblock-lti-consumer"

# 构建自定义镜像
tutor images build openedx

# 推送到本地注册表
tutor images push openedx
```

> **注意**：构建镜像需要外网访问（pip install 从 PyPI 下载包）。此步骤必须在 master 节点完成。

---

## 6. 使用 Tutor 逐步部署

### 6.1 第一步：初始化 Tutor 配置

```bash
# 在 master 节点执行
source /opt/tutor-env/bin/activate

# 设置基本配置
tutor config save \
  --set LMS_HOST="openedx.local" \
  --set CMS_HOST="studio.openedx.local" \
  --set PLATFORM_NAME="我的 Open edX" \
  --set CONTACT_EMAIL="admin@openedx.local" \
  --set LANGUAGE_CODE="zh-cn" \
  --set DOCKER_REGISTRY="10.100.135.132:5000/" \
  --set K8S_NAMESPACE="openedx"
```

### 6.2 第二步：禁用内置服务（复用现有 Redis）

```bash
# 复用现有 Redis（如果 Redis 在同一 K8s 集群中）
# 获取现有 Redis 的 Service 名称和端口
kubectl get svc -A | grep redis

# 假设现有 Redis Service 为 redis.redis.svc.cluster.local:6379
tutor config save \
  --set RUN_REDIS=false \
  --set REDIS_HOST="redis.redis.svc.cluster.local" \
  --set REDIS_PORT=6379 \
  --set REDIS_PASSWORD="<现有Redis密码>" \
  --set OPENEDX_CACHE_REDIS_DB=2 \
  --set OPENEDX_CELERY_REDIS_DB=3
```

> **注意**：如果现有 Redis 有密码保护，请设置 `REDIS_PASSWORD`。为避免与现有服务冲突，使用不同的 Redis DB 编号（Open edX 默认用 DB 0 和 1）。

### 6.3 第三步：配置 HTTPS / Ingress

由于使用 Nginx Ingress 而非 Caddy 的 LoadBalancer，需禁用内置 Web 代理：

```bash
tutor config save \
  --set ENABLE_WEB_PROXY=false \
  --set ENABLE_HTTPS=false
```

> 在气隙环境中无法通过 Let's Encrypt 获取证书，因此禁用 HTTPS 或使用自签证书。如需 HTTPS，配置 Nginx Ingress 使用自签证书。

### 6.4 第四步：配置 MySQL（必须部署在集群内）

由于 CockroachDB 无法替代 MySQL，必须在集群内部署 MySQL：

```bash
# 使用 Tutor 内置 MySQL（默认行为）
# Tutor 会在 K8s 中自动部署 MySQL 8.4
# 设置 MySQL 密码（如果不设置，Tutor 会自动生成）
tutor config save \
  --set RUN_MYSQL=true \
  --set MYSQL_ROOT_PASSWORD="<设置强密码>" \
  --set OPENEDX_MYSQL_DATABASE="openedx" \
  --set OPENEDX_MYSQL_USERNAME="openedx" \
  --set OPENEDX_MYSQL_PASSWORD="<设置强密码>"
```

> **重要**：MySQL 数据需要持久化 PVC。确保 worker 节点有足够的磁盘空间（建议至少 50 GB）。

### 6.5 第五步：禁用内置 SMTP（可选）

```bash
# 如果有现有邮件服务
tutor config save \
  --set RUN_SMTP=false \
  --set SMTP_HOST="<邮件服务器>" \
  --set SMTP_PORT=25

# 或使用内置 SMTP（默认）
tutor config save --set RUN_SMTP=true
```

### 6.6 第六步：生成 K8s 配置清单

```bash
# 生成所有 K8s manifest 文件
tutor config save

# 查看生成的配置
cat "$(tutor config printroot)/config.yml"

# 查看生成的 K8s 清单
ls "$(tutor config printroot)/env/k8s/"
```

### 6.7 第七步：自定义 K8s 资源（NodePort + 节点亲和性）

Tutor 默认使用 Caddy LoadBalancer，但在本环境中需要使用 NodePort 和 Nginx Ingress。创建自定义 Kustomize 补丁：

```bash
# 创建自定义覆盖目录
mkdir -p "$(tutor config printroot)/env-custom/"

cat > "$(tutor config printroot)/env-custom/kustomization.yml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../env/
EOF
```

**节点亲和性配置**（确保 Open edX 调度到 worker 节点）：

创建补丁文件 `$(tutor config printroot)/env-custom/node-affinity-patch.yml`：

```yaml
# 对所有 Deployment 添加节点亲和性
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lms
  namespace: openedx
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: 10.167.2.176
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cms
  namespace: openedx
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: 10.167.2.176
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lms-worker
  namespace: openedx
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: 10.167.2.176
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cms-worker
  namespace: openedx
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: 10.167.2.176
```

### 6.8 第八步：创建命名空间和 PVC

```bash
# 创建命名空间
kubectl create namespace openedx

# 标记 worker 节点（如未标记）
kubectl label nodes 10.167.2.176 openedx-role=worker --overwrite
```

### 6.9 第九步：启动 Caddy 反向代理

```bash
# 先启动 Caddy（用于获取入口 IP）
tutor k8s start caddy

# 查看 Caddy Service
kubectl --namespace openedx get services/caddy

# 如果使用 NodePort 模式，手动修改 Service 类型
kubectl --namespace openedx patch service caddy \
  --type='json' \
  -p='[{"op":"replace","path":"/spec/type","value":"NodePort"}]'

# 确认 NodePort 分配
kubectl --namespace openedx get svc caddy
```

### 6.10 第十步：配置 Nginx Ingress 路由

创建 Ingress 规则将流量路由到 Open edX：

```yaml
# openedx-ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openedx-ingress
  namespace: openedx
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 100m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_set_header X-Forwarded-Proto $scheme;
spec:
  ingressClassName: nginx
  rules:
  - host: openedx.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: caddy
            port:
              number: 80
  - host: studio.openedx.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: caddy
            port:
              number: 80
```

```bash
kubectl apply -f openedx-ingress.yml
```

### 6.11 第十一步：启动完整平台

```bash
# 先进行干运行验证
tutor k8s apply --dry-run=server --validate=true

# 启动整个平台
tutor k8s launch
```

`tutor k8s launch` 会执行以下操作：
1. 生成配置文件
2. 应用所有 K8s manifest（MySQL、MongoDB、Redis、Meilisearch、LMS、CMS、Workers）
3. 运行数据库迁移
4. 初始化平台数据

> 此过程可能需要 10-30 分钟，取决于镜像拉取速度和数据库初始化。

### 6.12 第十二步：验证部署

```bash
# 查看所有 Pod 状态
kubectl --namespace openedx get pods -w

# 查看服务
kubectl --namespace openedx get svc

# 查看节点和工作负载
tutor k8s status

# 查看 LMS 日志
tutor k8s logs -f lms

# 验证 LMS 可达
curl -I http://openedx.local

# 验证 Studio 可达
curl -I http://studio.openedx.local
```

### 6.13 第十三步：创建超级管理员

```bash
# 创建超级管理员用户
tutor k8s exec lms ./manage.py lms \
  manage_user edx@example.com staff --superuser --staff

# 设置密码
tutor k8s exec lms ./manage.py lms \
  shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(email='edx@example.com')
u.set_password('YourStrongPassword')
u.save()
"
```

---

## 7. CockroachDB 与 Open edX 数据库的关系

### 7.1 不可替代性说明

如第 2.1 节所述，Open edX 的数据库引擎在 Tutor 模板中硬编码为 `django.db.backends.mysql`。CockroachDB 虽然提供 PostgreSQL 兼容接口，但：

1. Open edX 不使用 PostgreSQL 引擎，而是直接使用 MySQL 引擎
2. Open edX 的 Django 迁移脚本包含 MySQL 特有 SQL 语法
3. Tutor 官方文档明确要求外部数据库必须为 MySQL 8.4

### 7.2 推荐方案

**方案 A（推荐）：在 K8s 集群内部署独立 MySQL**

- 使用 Tutor 内置的 MySQL 8.4 容器
- 数据持久化到 worker 节点的 PVC
- 与 CockroachDB 完全独立，互不干扰

**方案 B（备选）：在 worker 节点上裸机部署 MySQL**

- 在 worker 节点上直接安装 MySQL 8.4
- 配置 Tutor 使用 `RUN_MYSQL=false` 并指向该实例
- 优点：性能更稳定，不占用 K8s 资源
- 缺点：需要手动管理 MySQL 运维

### 7.3 CockroachDB 的角色

CockroachDB 继续服务于现有的 Dify、JupyterHub 等服务。Open edX **不会**使用 CockroachDB，两者完全独立运行。

---

## 8. 与现有 Redis 的集成

### 8.1 集成方案

Open edX 使用 Redis 两个用途：
- **缓存**：Django 缓存后端（`django_redis`）
- **消息队列**：Celery broker

如果集群中已有 Redis 服务，可以复用：

```bash
# 获取现有 Redis 的 Service 信息
kubectl get svc -A | grep redis

# 配置 Tutor 使用外部 Redis
tutor config save \
  --set RUN_REDIS=false \
  --set REDIS_HOST="<redis-service-name>.<namespace>.svc.cluster.local>" \
  --set REDIS_PORT=6379 \
  --set REDIS_PASSWORD="<redis-password-if-any>" \
  --set OPENEDX_CACHE_REDIS_DB=2 \
  --set OPENEDX_CELERY_REDIS_DB=3
```

### 8.2 Redis DB 隔离

为避免与现有服务的 Redis DB 冲突，建议使用不同的 DB 编号：

| Redis DB | 用途 |
|----------|------|
| 0 | 现有服务（默认） |
| 1 | 现有服务 |
| **2** | **Open edX 缓存**（`OPENEDX_CACHE_REDIS_DB=2`） |
| **3** | **Open edX Celery**（`OPENEDX_CELERY_REDIS_DB=3`） |

### 8.3 备选方案

如果现有 Redis 资源紧张或不确定兼容性，建议让 Tutor 部署独立的 Redis 实例（默认行为）：

```bash
# 使用 Tutor 内置 Redis（默认）
tutor config save --set RUN_REDIS=true
```

---

## 9. 与现有 Ollama 的 AI 集成

### 9.1 Open edX AI 扩展框架

Open edX 提供了一个实验性的 **AI 扩展框架**（`openedx-ai-extensions` 插件），支持以下 LLM 提供商：

| 提供商 | 模型示例 | 是否适合本环境 |
|--------|---------|--------------|
| OpenAI | `openai/gpt-4o-mini` | 否（气隙环境无外网） |
| Anthropic | `anthropic/claude-3-haiku` | 否（气隙环境无外网） |
| **Ollama（本地）** | `ollama/llama3.2:1b` | **是（集群已有 Ollama）** |
| Deepseek（HF） | `huggingface/deepseek-ai/...` | 否（需外网） |

该框架基于 **LiteLLM** 实现多提供商路由，支持通过 `API_BASE` 参数指定自定义 API 端点。

### 9.2 安装 AI 扩展插件

```bash
# 在 master 节点执行
source /opt/tutor-env/bin/activate

# 启用 AI 扩展插件（需先安装）
pip install openedx-ai-extensions

# 在 Tutor 中启用插件
tutor plugins enable openedx-ai-extensions
```

> **注意**：`openedx-ai-extensions` 是实验性插件，来源于 `github.com/openedx/openedx-ai-extensions`。在气隙环境中，需先在 master 节点通过 pip 下载安装包，再离线安装。

### 9.3 配置 Ollama 作为 LLM 提供商

获取 Ollama 的集群内访问地址：

```bash
# 查看现有 Ollama Service
kubectl get svc -A | grep ollama

# 假设 Ollama Service 为 ollama.ai-tools.svc.cluster.local:11434
```

配置 Tutor：

```bash
tutor config save \
  --set AI_EXTENSIONS_OLLAMA_API_BASE="http://ollama.ai-tools.svc.cluster.local:11434" \
  --set AI_EXTENSIONS_OLLAMA_MODEL="ollama/<你的模型名>"
```

或在 `config.yml` 中直接配置：

```yaml
AI_EXTENSIONS:
  ollama:
    API_BASE: "http://ollama.ai-tools.svc.cluster.local:11434"
    MODEL: "ollama/<你的模型名>"
    # 如 Ollama 需要认证，可设置 API_KEY
    # API_KEY: "ollama-api-key-if-set"
```

### 9.4 配置 AI 工作流

AI 扩展框架使用"工作流"（workflow）概念。默认工作流 `lms-content-summary` 在学习单元中提供"AI 摘要"按钮。

配置文件示例（通过 Tutor patch 注入）：

```json
{
  "processor_config": {
    "LLMProcessor": {
      "provider": "ollama"
    }
  }
}
```

- `provider` 值必须与 `AI_EXTENSIONS` 中定义的键名匹配
- 第一个 provider 自动成为默认

### 9.5 重建镜像并部署

```bash
# 由于添加了新插件，需要重建 Open edX 镜像
tutor images build openedx
tutor images push openedx

# 重新部署
tutor k8s launch
```

### 9.6 AI 功能说明

配置完成后，Open edX LMS 中将出现 AI 辅助功能：

- **内容摘要**：学生在学习单元中可点击"AI 摘要"按钮，获取当前单元的 AI 生成摘要
- **可扩展**：可自定义工作流实现问答、辅导等 AI 功能
- **数据隐私**：所有 AI 请求通过集群内 Ollama 处理，不出集群

> **提示**：AI 扩展框架提示词针对 OpenAI 模型优化。使用 Ollama 本地模型时，响应质量可能有所不同，可能需要调整系统提示词。

---

## 10. 通过 LTI 与 JupyterHub 集成

### 10.1 集成方案对比

有两种方式将 JupyterHub 与 Open edX 集成：

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **方案 A：LTI 集成** | Open edX 作为 LTI 消费者，JupyterHub 作为 LTI 提供者 | 标准、灵活、无需额外组件 | 需配置 LTI 凭证 |
| **方案 B：tutor-jupyter 插件** | 安装专用插件，在 Open edX 内嵌 Jupyter XBlock | 集成更深，体验更好 | 会部署新的 JupyterHub，与现有重复 |

**推荐方案 A**，因为集群已有 JupyterHub 实例。

### 10.2 方案 A：通过 LTI 1.1/1.3 集成现有 JupyterHub

#### 10.2.1 Open edX LTI 消费者 XBlock

Open edX 内置了 LTI 消费者 XBlock（`xblock-lti-consumer`），支持 LTI 1.1 和 LTI 1.3。课程作者可以在课程单元中添加 LTI 组件，嵌入外部工具。

#### 10.2.2 配置步骤

**第 1 步：确保 JupyterHub 支持 LTI**

现有 JupyterHub 需配置为 LTI 提供者。可通过安装 `jupyterhub-ltiauthenticator` 实现：

```bash
# 在 JupyterHub 环境中安装 LTI 认证器
pip install jupyterhub-ltiauthenticator
```

在 JupyterHub 配置 `jupyterhub_config.py` 中添加：

```python
c = get_config()

# LTI 1.1 配置
c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

# LTI 消费者凭证（与 Open edX 中配置一致）
c.LTIAuthenticator.consumers = {
    "openedx-lti-key": {
        "key": "openedx-lti-key",
        "secret": "openedx-lti-secret"
    }
}
```

**第 2 步：在 Open edX Studio 中配置 LTI**

1. 以课程作者身份登录 Studio（`http://studio.openedx.local`）
2. 打开目标课程
3. 进入课程内容编辑器
4. 在单元中添加"高级模块" -> "LTI 消费者"（LTI Consumer）

**第 3 步：配置 LTI 组件参数**

在 LTI 消费者 XBlock 中填写：

| 参数 | 值 |
|------|-----|
| **LTI URL**（启动 URL） | `http://<jupyterhub-url>/hub/lti/launch` |
| **LTI Launch Target** | `iframe`（嵌入到课程页面） |
| **Consumer Key** | `openedx-lti-key` |
| **Consumer Secret** | `openedx-lti-secret` |
| **LTI 1.1 / 1.3** | 根据需求选择（LTI 1.3 更安全） |

**第 4 步：测试**

学生登录 LMS -> 打开课程 -> 在包含 LTI 组件的单元中，将看到嵌入的 JupyterHub notebook 界面。

### 10.3 方案 B：使用 tutor-jupyter 插件（备选）

如果希望更紧密的集成（如直接在课程中嵌入可编辑的代码编辑器），可安装 `tutor-jupyter` 插件：

```bash
# 安装插件
pip install tutor-jupyter

# 启用插件
tutor plugins enable jupyter

# 配置（使用现有 JupyterHub 或让插件部署新的）
tutor config save \
  --set JUPYTER_HUB_HOST="http://<现有jupyterhub-url>"

# 重建镜像
tutor images build openedx
tutor images push openedx

# 重新部署
tutor k8s launch
```

> **注意**：`tutor-jupyter` 插件默认会部署一个新的 JupyterHub 单节点集群。如果复用现有 JupyterHub，需自定义配置。建议使用方案 A（LTI）以避免重复部署。

### 10.4 Codejail 代码执行（可选）

如果需要在 Open edX 中直接运行 Python 代码（不通过 JupyterHub），可安装 `tutor-contrib-codejail` 插件：

```bash
# 安装 codejail 插件（来自 contrib 索引）
pip install git+https://github.com/eduNEXT/tutor-contrib-codejail.git

# 启用插件
tutor plugins enable codejail

# 重建镜像
tutor images build openedx
tutor images push openedx

# 重新部署
tutor k8s launch
```

Codejail 用于在安全沙箱中执行不受信任的 Python 代码，支持 Python 评估输入型 XBlock（Python-evaluated input problems）。

> **气隙注意**：`tutor-contrib-codejail` 需要从 GitHub 安装。需在 master 节点先下载，再离线安装。打包为 wheel 文件传输：
> ```bash
> # 在 master 节点（有外网）
> pip download tutor-contrib-codejail
> # 将 .whl 文件复制到目标环境
> pip install tutor_contrib_codejail-*.whl
> ```

---

## 11. 课程创建流程

### 11.1 访问 Studio

1. 在浏览器中访问 `http://studio.openedx.local`
2. 使用超级管理员账号登录
3. 点击"New Course"创建新课程

### 11.2 课程创建步骤

1. **填写课程信息**：
   - 课程名称
   - 课程编号（Course Number）
   - 课程组织（Organization）
   - 课程运行（Run，如 `2026_Fall`）

2. **构建课程大纲**：
   - 创建章节（Section）
   - 在章节下创建子章节（Subsection）
   - 在子章节下创建单元（Unit）

3. **添加内容组件**：
   - **HTML 组件**：富文本内容
   - **视频组件**：嵌入视频
   - **问题组件**：选择题、填空题等
   - **LTI 组件**：嵌入 JupyterHub
   - **代码执行组件**：Python 代码练习（需 codejail）

4. **发布课程**：
   - 点击"Publish"发布课程
   - 在 LMS 中学生可注册学习

### 11.3 课程导入/导出

Open edX 支持课程包的导入导出（OLX 格式）：

```bash
# 导出课程
tutor k8s exec cms ./manage.py cms \
  export <course-id> /openedx/data/export/

# 导入课程
tutor k8s exec cms ./manage.py cms \
  import /openedx/data/import/ course-v1:Org+Course+Run
```

---

## 12. 用户管理

### 12.1 用户角色

Open edX 主要用户角色：

| 角色 | 权限 | 访问入口 |
|------|------|---------|
| **超级管理员** | 全部权限，包括 Django Admin | LMS + Studio + Django Admin |
| **课程作者** | 创建和管理课程 | Studio |
| **课程助教** | 管理特定课程学生和成绩 | LMS + Studio（限本课程） |
| **学生** | 注册课程、学习、考试 | LMS |

### 12.2 用户管理命令

```bash
# 创建超级管理员
tutor k8s exec lms ./manage.py lms \
  manage_user admin@openedx.local staff \
  --superuser --staff

# 创建普通用户
tutor k8s exec lms ./manage.py lms \
  manage_user student@example.com student

# 设置用户密码
tutor k8s exec lms ./manage.py lms \
  shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(email='admin@openedx.local')
u.set_password('NewPassword')
u.save()
"

# 授予课程作者权限
tutor k8s exec lms ./manage.py lms \
  shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(email='author@openedx.local')
u.is_staff = True
u.save()
"
```

### 12.3 批量用户注册

```bash
# 通过 CSV 批量注册
tutor k8s exec lms ./manage.py lms \
  register_students --course <course-id> /path/to/students.csv
```

CSV 格式示例：
```csv
email,username,name
student1@example.com,student1,张三
student2@example.com,student2,李四
```

### 12.4 OAuth2 / 第三方认证（可选）

Open edX 支持 OAuth2、SAML、LDAP 等第三方认证。如需与现有统一认证系统集成，参考 Tutor 文档配置 `SOCIAL_AUTH_*` 参数。

---

## 13. 备份与运维

### 13.1 数据备份策略

| 数据 | 备份方式 | 建议频率 |
|------|---------|---------|
| MySQL 数据 | `mysqldump` 导出 | 每日 |
| MongoDB 数据 | `mongodump` 导出 | 每日 |
| 用户上传文件 | PVC 快照或 MinIO 同步 | 每日 |
| Tutor 配置 | `config.yml` 备份 | 变更时 |
| K8s 清单 | `tutor config printroot` 目录备份 | 变更时 |

### 13.2 备份脚本

```bash
#!/bin/bash
# === Open edX 备份脚本 ===
# 在 master 节点执行

BACKUP_DIR="/backup/openedx/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. 备份 Tutor 配置
cp -r "$(tutor config printroot)" "$BACKUP_DIR/tutor-config/"

# 2. 备份 MySQL
kubectl --namespace openedx exec mysql-0 -- \
  mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" \
  --all-databases --single-transaction \
  > "$BACKUP_DIR/mysql-backup.sql"

# 3. 备份 MongoDB
kubectl --namespace openedx exec mongodb-0 -- \
  mongodump --archive --gzip \
  > "$BACKUP_DIR/mongodb-backup.gz"

# 4. 备份 Meilisearch 数据（如需要）
# Meilisearch 数据存储在 PVC 中，可通过快照备份

echo "Backup completed: $BACKUP_DIR"
```

### 13.3 恢复流程

```bash
# 恢复 MySQL
kubectl --namespace openedx exec -i mysql-0 -- \
  mysql -u root -p"$MYSQL_ROOT_PASSWORD" \
  < /backup/openedx/20260907/mysql-backup.sql

# 恢复 MongoDB
kubectl --namespace openedx exec -i mongodb-0 -- \
  mongorestore --archive --gzip \
  < /backup/openedx/20260907/mongodb-backup.gz
```

### 13.4 升级流程

```bash
# 升级 Tutor
pip install --upgrade "tutor[full]"

# 重新生成配置
tutor config save

# 启动升级（会自动迁移数据库）
tutor k8s launch
```

> **气隙升级注意**：升级前需在 master 节点拉取新版本镜像并推送到本地注册表。

### 13.5 日常运维命令

```bash
# 查看平台状态
tutor k8s status

# 查看特定服务日志
tutor k8s logs -f lms
tutor k8s logs -f cms
tutor k8s logs -f lms-worker

# 执行管理命令
tutor k8s exec lms ./manage.py lms migrate
tutor k8s exec cms ./manage.py cms migrate

# 重启服务
tutor k8s start lms
tutor k8s stop lms

# 重新应用配置（修改 config.yml 后）
tutor k8s launch
```

### 13.6 监控建议

```bash
# 查看资源使用
kubectl --namespace openedx top pods
kubectl --namespace openedx top nodes

# 查看 PVC 使用情况
kubectl --namespace openedx get pvc

# 查看 Events
kubectl --namespace openedx get events --sort-by='.lastTimestamp'
```

建议接入现有监控体系（如 Prometheus + Grafana）监控 Open edX 组件健康状态。

---

## 14. 已知限制与替代方案

### 14.1 已知限制

| 限制 | 影响 | 缓解措施 |
|------|------|---------|
| **必须使用 MySQL** | CockroachDB 无法替代 | 部署独立 MySQL 实例 |
| **MongoDB 不可替代** | 需额外部署 MongoDB | 使用 Tutor 内置 MongoDB |
| **气隙镜像准备复杂** | 需预拉取 10+ 镜像 | 编写自动化脚本 |
| **无 HTTPS（气隙）** | Let's Encrypt 不可用 | 使用自签证书或 Nginx Ingress 终止 TLS |
| **AI 扩展为实验性** | 可能不稳定 | 谨慎使用，关注上游更新 |
| **资源占用较高** | Open edX 是重量级平台 | 合理配置 worker 数量 |
| **LTI 配置复杂** | 需手动配置凭证 | 参考第 10 节详细步骤 |
| **MFE 构建需外网** | 前端镜像需在 master 构建 | 在 master 节点构建后推送 |

### 14.2 资源优化建议

如果资源紧张，可调整以下配置降低资源消耗：

```bash
# 减少 uWSGI worker 数量（默认各 2 个，每个约 500MB）
tutor config save \
  --set OPENEDX_LMS_UWSGI_WORKERS=1 \
  --set OPENEDX_CMS_UWSGI_WORKERS=1

# 禁用不需要的服务
tutor config save \
  --set RUN_SMTP=false  # 使用外部 SMTP

# 减少 MongoDB PVC 大小
tutor config save \
  --set MONGODB_HOST="mongodb"
# 然后通过 K8s patch 调整 PVC 大小
```

### 14.3 替代方案：Canvas LMS（更轻量）

如果 Open edX 过重，可考虑 **Canvas LMS**（Instructure 开源）作为替代：

| 对比项 | Open edX (Tutor) | Canvas LMS |
|--------|-----------------|------------|
| **数据库** | MySQL + MongoDB | **PostgreSQL**（可用 CockroachDB！） |
| **缓存/队列** | Redis | Redis |
| **语言** | Python/Django | Ruby/Rails |
| **K8s 支持** | 原生支持 | 需手动部署 |
| **LTI 支持** | 内置 | 内置（LTI 1.3） |
| **代码执行** | codejail 插件 | 需第三方工具 |
| **资源需求** | ~8-14 GB RAM | ~4-8 GB RAM |
| **PostgreSQL 兼容** | 否 | **是** |
| **CockroachDB 可用** | 否 | **可能（实验性）** |
| **成熟度** | 非常成熟 | 非常成熟 |

**Canvas LMS 的关键优势**：使用 PostgreSQL，理论上可以尝试使用 CockroachDB。但需注意 CockroachDB 与 PostgreSQL 的兼容性并非 100%，需测试验证。

### 14.4 替代方案：Moodle（最轻量）

如果只需基本 LMS 功能且资源极度受限：

| 对比项 | Open edX | Moodle |
|--------|---------|--------|
| **数据库** | MySQL + MongoDB | PostgreSQL/MySQL/MariaDB |
| **资源需求** | ~8-14 GB RAM | **~2-4 GB RAM** |
| **LTI 支持** | 内置 | 内置（LTI 1.3） |
| **K8s 部署** | Tutor | Helm Chart 或手动 |
| **代码执行** | codejail | 插件 |
| **PostgreSQL** | 否 | **是** |
| **CockroachDB** | 否 | **可能** |
| **适合场景** | 大规模 MOOC | 中小规模教学 |

### 14.5 推荐决策

| 场景 | 推荐方案 |
|------|---------|
| **需要完整 Open edX 功能、大规模在线课程** | 部署 Open edX（本方案） |
| **希望复用 CockroachDB、需要 LTI、中等规模** | 评估 Canvas LMS |
| **资源受限、仅需基本 LMS + LTI** | 评估 Moodle |
| **仅需编程教学 + Jupyter** | 直接使用现有 JupyterHub + 简单 Web 前端 |

### 14.6 混合方案（推荐）

考虑到集群已有 JupyterHub、Code-Server、Ollama 等工具，可采用混合方案：

1. **部署 Open edX** 作为课程管理和学习体验平台
2. **通过 LTI 集成现有 JupyterHub** 进行编程实践
3. **通过 Ollama + AI Extensions** 提供 AI 辅助学习
4. **通过 Code-Server** 提供高级开发环境（可选 LTI 集成）

这样既利用了 Open edX 的课程管理能力，又复用了现有基础设施，避免重复部署。

---

## 附录 A：完整配置文件参考

以下为 `config.yml` 的推荐配置汇总：

```yaml
# === 基本配置 ===
LMS_HOST: "openedx.local"
CMS_HOST: "studio.openedx.local"
PLATFORM_NAME: "我的 Open edX"
CONTACT_EMAIL: "admin@openedx.local"
LANGUAGE_CODE: "zh-cn"

# === Docker 镜像注册表（气隙） ===
DOCKER_REGISTRY: "10.100.135.132:5000/"

# === K8s 配置 ===
K8S_NAMESPACE: "openedx"

# === Web 代理（使用 Nginx Ingress） ===
ENABLE_WEB_PROXY: false
ENABLE_HTTPS: false

# === MySQL（必须使用内置） ===
RUN_MYSQL: true
MYSQL_ROOT_PASSWORD: "<强密码>"
OPENEDX_MYSQL_DATABASE: "openedx"
OPENEDX_MYSQL_USERNAME: "openedx"
OPENEDX_MYSQL_PASSWORD: "<强密码>"

# === MongoDB（内置） ===
RUN_MONGODB: true
MONGODB_DATABASE: "openedx"

# === Redis（复用现有或内置） ===
# 方案1：复用现有 Redis
# RUN_REDIS: false
# REDIS_HOST: "redis.redis.svc.cluster.local"
# REDIS_PORT: 6379
# REDIS_PASSWORD: "<现有密码>"
# OPENEDX_CACHE_REDIS_DB: 2
# OPENEDX_CELERY_REDIS_DB: 3

# 方案2：使用内置 Redis（默认）
RUN_REDIS: true

# === Meilisearch（内置） ===
RUN_MEILISEARCH: true

# === SMTP ===
RUN_SMTP: true  # 或配置外部 SMTP

# === Worker 数量优化 ===
OPENEDX_LMS_UWSGI_WORKERS: 2
OPENEDX_CMS_UWSGI_WORKERS: 2

# === AI 扩展（Ollama 集成） ===
AI_EXTENSIONS:
  ollama:
    API_BASE: "http://ollama.ai-tools.svc.cluster.local:11434"
    MODEL: "ollama/<模型名>"

# === 启用的插件 ===
PLUGINS:
  - openedx-ai-extensions
  # - jupyter      # 如需 tutor-jupyter
  # - codejail     # 如需代码沙箱执行
```

## 附录 B：部署检查清单

- [ ] Master 节点已安装 Python 3.10+、Docker、kubectl、Tutor
- [ ] Master 节点可访问外网（用于拉取镜像和 pip 包）
- [ ] 本地 Docker 注册表 `10.100.135.132:5000` 可达
- [ ] 所有 Open edX 镜像已推送到本地注册表
- [ ] DNS / hosts 记录已配置（openedx.local, studio.openedx.local）
- [ ] Worker 节点有足够磁盘空间（建议 100 GB+）
- [ ] K8s 集群健康，Nginx Ingress 运行正常
- [ ] Tutor 配置已生成并审查（`tutor config save`）
- [ ] MySQL 密码已设置
- [ ] Redis 配置已确定（复用或内置）
- [ ] AI Extensions 配置（如需 Ollama 集成）
- [ ] 自定义 K8s 补丁已创建（节点亲和性、NodePort）
- [ ] `tutor k8s apply --dry-run=server --validate=true` 通过
- [ ] `tutor k8s launch` 成功完成
- [ ] 所有 Pod 处于 Running 状态
- [ ] LMS (`http://openedx.local`) 可访问
- [ ] Studio (`http://studio.openedx.local`) 可访问
- [ ] 超级管理员已创建并可登录
- [ ] LTI 集成测试（如需 JupyterHub 集成）
- [ ] AI 摘要功能测试（如需 Ollama 集成）
- [ ] 备份脚本已配置并测试

---

## 附录 C：关键命令速查

```bash
# === 部署 ===
tutor config save                           # 保存配置
tutor k8s launch                            # 部署/升级平台
tutor k8s start <service>                   # 启动特定服务
tutor k8s stop <service>                    # 停止特定服务

# === 运维 ===
tutor k8s status                            # 查看集群状态
tutor k8s logs -f <service>                 # 查看日志
tutor k8s exec <service> <command>          # 在 Pod 中执行命令
tutor k8s apply --dry-run=server            # 干运行验证

# === 镜像 ===
tutor images build openedx                   # 构建自定义镜像
tutor images push openedx                    # 推送到注册表

# === 用户管理 ===
tutor k8s exec lms ./manage.py lms manage_user <email> staff --superuser --staff
tutor k8s exec lms ./manage.py lms shell -c "<python代码>"

# === 数据库 ===
tutor k8s exec lms ./manage.py lms migrate  # 运行迁移
tutor k8s exec cms ./manage.py cms migrate  # CMS 迁移

# === 插件 ===
tutor plugins list                           # 列出已安装插件
tutor plugins enable <name>                  # 启用插件
tutor plugins disable <name>                 # 禁用插件
```

---

*本文档基于以下来源编写：*
- *Tutor 官方文档: https://docs.tutor.edly.io/*
- *Tutor GitHub: https://github.com/overhangio/tutor*
- *Open edX 文档: https://docs.openedx.org*
- *Tutor 插件索引: https://github.com/overhangio/tpi*
- *Open edX AI 扩展文档: https://docs.openedx.org/projects/openedx-ai-extensions/*
- *Tutor 源码（auth.yml 配置模板）*

*文档日期: 2026-09-07*

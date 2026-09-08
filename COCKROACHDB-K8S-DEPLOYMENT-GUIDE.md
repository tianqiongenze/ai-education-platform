# CockroachDB K8s 部署文档（局域网访问 + 多区域 + 高可用）

> **版本**: 2.0 | **日期**: 2026-09-05 | **集群**: 3 节点 CockroachDB v24.3.11
> **命名空间**: `infra`（基础设施层，Rancher 可管理）

---

## 目录

1. [架构概览](#1-架构概览)
2. [局域网访问方式](#2-局域网访问方式)
3. [多区域数据同步](#3-多区域数据同步)
4. [冷备份与热备](#4-冷备份与热备)
5. [负载均衡](#5-负载均衡)
6. [Follower Reads（低延迟读取）](#6-follower-reads低延迟读取)
7. [节点详情](#7-节点详情)
8. [连接字符串](#8-连接字符串)
9. [管理界面](#9-管理界面)
10. [运维操作](#10-运维操作)
11. [数据备份与恢复](#11-数据备份与恢复)
12. [Changefeeds（CDC 实时复制）](#12-changefeedscdc-实时复制)
13. [迁移记录](#13-迁移记录)
14. [服务迁移到 CockroachDB](#14-服务迁移到-cockroachdb)

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    K8s Cluster (2 nodes)                        │
│                                                                 │
│  ┌──────────── infra 命名空间 (基础设施层) ──────────────┐     │
│  │                                                       │     │
│  │  ┌──────────────┐  ┌──────────────┐                  │     │
│  │  │ cockroachdb-a│  │ cockroachdb-b│                  │     │
│  │  │ (master)     │  │ (master)     │                  │     │
│  │  │ zone=sh175-a │  │ zone=sh175-b │                  │     │
│  │  │ port: 26257  │  │ port: 26267  │                  │     │
│  │  │ nodeID: 1    │  │ nodeID: 2    │                  │     │
│  │  └──────┬───────┘  └──────┬───────┘                  │     │
│  │         │                   │                          │     │
│  │  ┌──────┴───────────────────┴──────┐                  │     │
│  │  │     cockroachdb-c (worker1)     │                  │     │
│  │  │     zone=w176-c                 │                  │     │
│  │  │     port: 26257                 │                  │     │
│  │  │     nodeID: 4                   │                  │     │
│  │  └─────────────────────────────────┘                  │     │
│  │                                                       │     │
│  │  Services:                                           │     │
│  │  - cockroachdb (NodePort 30257, 负载均衡)             │     │
│  │  - cockroachdb-read (NodePort 30267, 读节点)          │     │
│  │  - cockroachdb-admin (NodePort 30259, 管理界面)      │     │
│  │                                                       │     │
│  │  ┌──────────────┐                                    │     │
│  │  │ Redis         │ (从 dify-plus 迁移)               │     │
│  │  │ port: 6379    │                                    │     │
│  │  └──────────────┘                                    │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
│  局域网: 10.167.2.175 (master) + 10.167.2.176 (worker)        │
└─────────────────────────────────────────────────────────────────┘
```

### 集群规格

| 参数 | 值 |
|------|-----|
| CockroachDB 版本 | v24.3.11 (CCL) |
| 节点数 | 3 (nodeID: 1, 2, 4) |
| 集群ID | 416456b3-b7dc-436f-b0b7-c2bf374461fa |
| 认证方式 | insecure（无 TLS） |
| 存储引擎 | Pebble |
| 缓存 | 512MiB/节点 |
| 最大 SQL 内存 | 512MiB/节点 |
| 数据库数 | 27（含 system, dify, dify_plus, industrial_analytics 等） |
| Follower Reads | 已启用（15秒延迟） |
| 复制因子 | 3（每条数据 3 副本） |
| GC TTL | 90000 秒（25 小时） |

---

## 2. 局域网访问方式

### SQL 连接（写节点 - 主节点 A）

| 属性 | 值 |
|------|-----|
| 主机 | `10.167.2.175` |
| 端口 | `26257` |
| NodePort | `30257` |
| 用户名 | `root` |
| 密码 | 无（insecure 模式） |
| SSL | disable |

### SQL 连接（读节点 B - Follower Read）

| 属性 | 值 |
|------|-----|
| 主机 | `10.167.2.175` |
| 端口 | `26267` |
| NodePort | `30267` |
| 用户名 | `root` |
| 密码 | 无 |
| SSL | disable |

### Worker 节点直连

| 属性 | 值 |
|------|-----|
| 主机 | `10.167.2.176` |
| 端口 | `26257` |
| 用户名 | `root` |

### 连接字符串

```
# 写连接（主节点 A）
postgresql://root@10.167.2.175:26257/<database>?sslmode=disable

# 读连接（节点 B，Follower Read）
postgresql://root@10.167.2.175:26267/<database>?sslmode=disable

# 负载均衡连接（所有节点轮询）
postgresql://root@10.167.2.175:30257/<database>?sslmode=disable

# 集群内服务名
postgresql://root@cockroachdb.infra.svc.cluster.local:26257/<database>?sslmode=disable
```

---

## 3. 多区域数据同步

### 当前拓扑

| 节点 | Zone | 节点 |
|------|------|------|
| A | sh175-a | k8s-master |
| B | sh175-b | k8s-master |
| C | w176-c | k8s-worker1 |

### 数据复制机制

CockroachDB 使用 **Raft 共识协议** 自动在所有节点间复制数据：
- 每个数据范围（Range）默认 **3 副本**
- 写入需要 **多数派确认**（2/3 节点同意）
- 自动负载均衡：数据在节点间自动重新分布

### 多区域配置（需要 region 层级）

```sql
-- 添加 region 到 locality（需要在节点启动参数中设置 --locality=region=cn-east,zone=sh175-a）
-- 当前仅有 zone 层级，region 层级需要重启节点添加

-- 设置数据库 primary region（需要 region 层级）
ALTER DATABASE industrial_analytics PRIMARY REGION "cn-east";

-- 设置生存目标（zone 级别故障容错）
ALTER DATABASE industrial_analytics SURVIVE ZONE FAILURE;

-- 全局表（读取优化，写入较慢）
ALTER TABLE telemetry_readings SET locality GLOBAL;

-- 区域表（指定 region 的低延迟读写）
ALTER TABLE telemetry_readings SET locality REGIONAL BY ROW;
```

---

## 4. 冷备份与热备

### 冷备份（BACKUP 命令）

```sql
-- 全量备份单个数据库
BACKUP DATABASE industrial_analytics TO 'nodelocal://1/backups/industrial_analytics';

-- 全量备份多个数据库
BACKUP DATABASE industrial_analytics, mes_system, security_audit, industrial_gateway
  TO 'nodelocal://1/backups/all_projects';

-- 增量备份（基于上一次全量备份）
BACKUP DATABASE industrial_analytics
  TO 'nodelocal://1/backups/industrial_analytics_inc'
  INCREMENTAL FROM 'nodelocal://1/backups/industrial_analytics';

-- 带版本历史的备份（可恢复到任意时间点）
BACKUP DATABASE industrial_analytics
  TO 'nodelocal://1/backups/industrial_analytics_history'
  WITH revision_history;

-- 定时备份调度
CREATE SCHEDULE FOR BACKUP DATABASE industrial_analytics
  INTO 'nodelocal://1/backups/scheduled'
  RECURRING '@daily'
  FULL BACKUP '@weekly';
```

### 热备（Changefeeds / CDC）

```sql
-- 创建实时变更流（需要 Kafka 或 webhook sink）
CREATE CHANGEFEED FOR TABLE industrial_analytics.telemetry_readings
  INTO 'kafka://broker:9092?topic_name=crdb_changes'
  WITH updated, resolved;

-- 使用 webhook sink
CREATE CHANGEFEED FOR TABLE security_audit.audit_sessions
  INTO 'webhook-https://https://backup-server/webhook?insecure_tls_skip_verify=true'
  WITH updated;
```

### 物理集群复制（热备集群）

```sql
-- 在备用集群上创建物理复制
CREATE PHYSICAL REPLICATION STREAM FROM 'source-cluster-connection-string';
```

---

## 5. 负载均衡

### 内置负载均衡 Service

| Service | 类型 | 选择器 | 端口 | 说明 |
|---------|------|--------|------|------|
| cockroachdb | NodePort | app=cockroachdb, node=a | 26257 → 30257 | 写节点 |
| cockroachdb-read | NodePort | app=cockroachdb, node=b | 26267 → 30267 | 读节点 |
| cockroachdb-admin | NodePort | app=cockroachdb, node=a | 26259 → 30259 | 管理 UI |

### 应用层负载均衡

```python
# Python 连接池配置（读写分离）
import psycopg2
from psycopg2 import pool

# 写连接池
write_pool = psycopg2.pool.ThreadedConnectionPool(
    5, 20,
    host='10.167.2.175', port=26257,
    user='root', dbname='industrial_analytics',
    options='-c statement_timeout=60000'
)

# 读连接池（Follower Read）
read_pool = psycopg2.pool.ThreadedConnectionPool(
    5, 20,
    host='10.167.2.175', port=26267,
    user='root', dbname='industrial_analytics',
    options='-c statement_timeout=30000'
)
```

### HAProxy 配置（可选外部负载均衡）

```haproxy
backend crdb_write
    balance roundrobin
    server crdb-a 10.167.2.175:26257 check
    server crdb-c 10.167.2.176:26257 check

backend crdb_read
    balance roundrobin
    server crdb-b 10.167.2.175:26267 check
```

---

## 6. Follower Reads（低延迟读取）

### 已启用配置

```sql
-- 集群级设置（已应用）
SET CLUSTER SETTING kv.closed_timestamp.follower_reads.enabled = true;
SET CLUSTER SETTING kv.closed_timestamp.target_duration = '15s';
```

### 使用方式

```sql
-- 方式 1：AS OF SYSTEM TIME（显式指定延迟）
SELECT * FROM telemetry_readings AS OF SYSTEM TIME '-15s' LIMIT 10;

-- 方式 2：bounded staleness（自动 follower read）
SELECT * FROM telemetry_readings AS OF SYSTEM TIME 'experimental_follower_read_timestamp()';

-- 方式 3：应用层设置
-- 连接到读节点 B (26267)，CRDB 自动使用 follower read
```

### 性能对比

| 读类型 | 延迟 | 一致性 | 适用场景 |
|--------|------|--------|----------|
| Leaseholder 读 | ~5ms | 强一致 | 写后立即读 |
| Follower Read | ~2ms | 15秒延迟 | 报表、分析、仪表盘 |

---

## 7. 节点详情

| 节点 | Pod | nodeID | 节点 | SQL端口 | HTTP端口 | 数据目录 | CPU/内存 |
|------|-----|--------|------|---------|----------|----------|---------|
| A | cockroachdb-a-0 | 1 | k8s-master | 26257 | 26259 | /home/crdb-data/a | 4核/3Gi |
| B | cockroachdb-b-0 | 2 | k8s-master | 26267 | 26269 | /home/crdb-data/b | 4核/3Gi |
| C | cockroachdb-c-0 | 4 | k8s-worker1 | 26257 | 8086 | /home/crdb-data/c | 4核/3Gi |

### 特殊配置

- **hostNetwork: true** — Pod 使用主机网络
- **hostPath 数据卷** — 挂载现有数据目录
- **initContainer** — 从主机 /opt/cockroach/ 复制二进制文件
- **runAsUser: 0** — root 运行
- **emptyDir /dev/shm** — 1Gi 内存型共享内存
- **ulimit -n 65536** — 提高文件描述符限制

---

## 8. 连接字符串速查

| 用途 | 连接地址 |
|------|----------|
| 写入（主节点 A） | `10.167.2.175:26257` |
| 读取（节点 B） | `10.167.2.175:26267` |
| Worker 节点直连 | `10.167.2.176:26257` |
| NodePort（局域网写） | `10.167.2.175:30257` |
| NodePort（局域网读） | `10.167.2.175:30267` |
| Admin UI | `http://10.167.2.175:30259` |
| 集群内写 | `cockroachdb.infra.svc.cluster.local:26257` |
| 集群内读 | `cockroachdb-read.infra.svc.cluster.local:26267` |
| Redis (infra) | `redis.infra.svc.cluster.local:6379` |

---

## 9. 管理界面

| 属性 | 值 |
|------|-----|
| Admin UI URL | `http://10.167.2.175:30259` |
| 节点A UI | `http://10.167.2.175:26259` |
| 节点B UI | `http://10.167.2.175:26269` |
| 节点C UI | `http://10.167.2.176:8086` |
| Rancher | infra 命名空间可直接管理 |

---

## 10. 运维操作

### 查看集群状态

```bash
# 节点列表
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach node ls --insecure --host=localhost:26257

# 数据库列表
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach sql --insecure --host=localhost:26257 \
  --execute="SHOW DATABASES"

# 复制状态
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach sql --insecure --host=localhost:26257 \
  --execute="SELECT * FROM crdb_internal.replication_stats"

# 范围分布
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach sql --insecure --host=localhost:26257 \
  --execute="SELECT range_id, replicas FROM crdb_internal.ranges LIMIT 10"
```

### 重启节点

```bash
kubectl delete pod cockroachdb-a-0 -n infra  # 重启节点 A
kubectl delete pod cockroachdb-b-0 -n infra  # 重启节点 B
kubectl delete pod cockroachdb-c-0 -n infra  # 重启节点 C
```

---

## 11. 数据备份与恢复

### 逻辑备份（SQL dump）

```bash
# 单个数据库
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach dump industrial_analytics \
  --insecure --host=localhost:26257 > backup.sql

# 恢复
kubectl exec -i -n infra cockroachdb-a-0 -c cockroachdb -- \
  /cockroach-binary/cockroach sql --insecure --host=localhost:26257 \
  --database=industrial_analytics < backup.sql
```

### 物理备份（BACKUP 命令）

```sql
-- 全量备份
BACKUP DATABASE industrial_analytics TO 'nodelocal://1/backups/industrial_analytics';

-- 增量备份
BACKUP DATABASE industrial_analytics
  TO 'nodelocal://1/backups/industrial_analytics_inc'
  INCREMENTAL FROM 'nodelocal://1/backups/industrial_analytics';

-- 恢复
RESTORE DATABASE industrial_analytics FROM 'nodelocal://1/backups/industrial_analytics';
```

---

## 12. Changefeeds（CDC 实时复制）

```sql
-- 创建 changefeed（需要 Kafka 或 webhook）
CREATE CHANGEFEED FOR TABLE industrial_analytics.telemetry_readings
  INTO 'webhook-https://https://backup.example.com/webhook'
  WITH updated, resolved;

-- 查看活跃 changefeeds
SELECT * FROM crdb_internal.changefeeds;

-- 停止 changefeed
CANCEL JOB <job_id>;
```

---

## 13. 迁移记录

### 从主机进程迁移到 K8s

| 步骤 | 操作 | 状态 |
|------|------|------|
| 1 | 创建 infra 命名空间 | ✅ |
| 2 | 停止 systemd 服务 (cockroach-node1, node2) | ✅ |
| 3 | 删除 LOCK 文件 | ✅ |
| 4 | 部署 3 个 StatefulSet (hostNetwork + hostPath) | ✅ |
| 5 | initContainer 复制二进制文件 | ✅ |
| 6 | runAsUser: 0 解决权限 | ✅ |
| 7 | /dev/shm emptyDir 解决共享内存 | ✅ |
| 8 | 验证 27 个数据库完整 | ✅ |

### 优化记录

| 优化项 | 配置 | 状态 |
|--------|------|------|
| Follower Reads | enabled, 15s | ✅ |
| GC TTL | 90000s | ✅ |
| 复制因子 | 3 | ✅ |
| 负载均衡 Service | cockroachdb (NodePort) | ✅ |
| 备份目录 | nodelocal://1/backups/ | ✅ |
| dify 数据库 | 已创建 | ✅ |
| dify_plus 数据库 | 已创建 | ✅ |

---

## 14. 服务迁移到 CockroachDB

### Dify API（已完成 ✅）

| 配置项 | 原值 | 新值 |
|--------|------|------|
| DB_HOST | pgbouncer.dify-plus.svc.cluster.local | cockroachdb.infra.svc.cluster.local |
| DB_PORT | 5432 | 26257 |
| DB_USERNAME | postgres | root |
| DB_DATABASE | dify | dify |
| DB_TYPE | postgresql | postgresql（CRDB 兼容） |

**验证**: `CRDB connection OK: CockroachDB CCL v24.3.11` ✅

### JupyterHub 项目（已配置 ✅）

| 项目 | 数据库 | 写连接 | 读连接 |
|------|--------|--------|--------|
| Python (industrial-analytics) | industrial_analytics | cockroachdb:26257 | cockroachdb-read:26267 |
| Java (mes-system) | mes_system | cockroachdb:26257 | cockroachdb-read:26267 |
| Go (industrial-gateway) | industrial_gateway | cockroachdb:26257 | cockroachdb-read:26267 |
| Rust (security-audit) | security_audit | cockroachdb:26257 | cockroachdb-read:26267 |

### Redis（已迁移 ✅）

| 配置项 | 原值 | 新值 |
|--------|------|------|
| 命名空间 | dify-plus | infra |
| 地址 | redis.dify-plus.svc.cluster.local:6379 | redis.infra.svc.cluster.local:6379 |
| 密码 | difyai123456 | difyai123456（不变） |

### dify-plus → infra 迁移状态

| 服务 | 状态 | 说明 |
|------|------|------|
| Redis | ✅ 已迁移 | 部署在 infra，dify-plus 有 ExternalName 桥接 |
| CockroachDB | ✅ 已迁移 | 3 节点 StatefulSet 在 infra |
| PostgreSQL (db-postgres) | 保留 | 作为 Dify 旧数据备份 |
| pgbouncer | 保留 | 可后续移除 |
| Weaviate | 保留 | 向量数据库，保留在 dify-plus |

---

## 附录: CockroachDB 高可用与灾备最佳实践

### 数据韧性

| 故障场景 | 影响 | 恢复 |
|----------|------|------|
| 1 节点故障 | 无影响 | 自动重新均衡 |
| 2 节点故障 | 集群不可用 | 恢复至少 2 节点 |
| master 节点故障 | 写入中断 | worker 节点接管 |
| 数据损坏 | 单范围影响 | 从其他副本恢复 |

### 灾备策略

| 策略 | 频率 | 恢复时间 | 说明 |
|------|------|----------|------|
| 逻辑备份 (dump) | 手动 | 分钟级 | SQL 文本，跨版本兼容 |
| 物理备份 (BACKUP) | 每日 | 分钟级 | 二进制，快速恢复 |
| 增量备份 | 每小时 | 秒级 | 基于全量备份 |
| Changefeeds (CDC) | 实时 | 秒级 | 实时数据复制 |
| 物理集群复制 | 实时 | 秒级 | 热备集群 |

### 3 节点集群限制

- **生存目标**: zone 级别（容忍 1 个 zone 故障）
- **Region 生存**: 需要 3+ region（当前只有 2 个 zone）
- **写入延迟**: ~5ms（本地），~50ms（跨节点）
- **读取延迟**: ~2ms（follower read），~5ms（leaseholder）

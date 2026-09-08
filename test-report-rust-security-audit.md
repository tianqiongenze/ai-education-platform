# 工控安全审计（Rust）全链路功能测试与性能压测报告

> 项目：`security-audit`（JupyterHub Rust 学生环境 `/home/jovyan/work/security-audit`）
> 技术栈：Rust (actix-web 4) + postgres crate（CRDB PostgreSQL 线协议）+ redis crate + serde
> 测试环境：K8s 集群（master 10.167.2.175 / worker 10.167.2.176），Pod `jupyter-student-rust`
> 测试日期：2026-09-03　|　测试方式：Pod 内 HTTP 全链路（REST :8080）+ CRDB 三节点验证 + Redis L2 验证

---

## 一、系统架构审查（多角色）

### 1.1 架构总览

```
   REST :8080 ──▶ actix-web Router ──┬─ POST/GET /api/v1/audits     (创建/列表)
                                     ├─ GET    /audits/{id}          (详情)
                                     ├─ POST   /audits/{id}/scan     (指纹扫描→findings)
                                     ├─ POST   /audits/{id}/finalize (完结)
                                     ├─ POST   /audits/{id}/compliance (IEC 62443 报告)
                                     ├─ GET    /cache/stats          (两级缓存指标)
                                     └─ GET    /health
                                     │
        ┌────────────────────────────▼────────────────────────────┐
        │ 六边形架构（Ports & Adapters）                            │
        │  domain/          audit / vulnerability / compliance     │
        │                   (5 模块，签名库+风险评分+SL 评估)        │
        │  application/     AuditService（用例编排，5 方法）          │
        │  infrastructure/  http.rs（全部 web::block 卸载阻塞 IO）    │
        │                   crdb_repository / cache / repository    │
        └────────────────────────────────────────────────────────┘
             │                              │
   ┌─────────▼──────────┐        ┌──────────▼─────────────┐
   │ CRDB 集群（root 无密）│        │ Redis 两级缓存 L2       │
   │ 写:175:26257        │        │ L1 HashMap TTL 30s      │
   │ 读:175:26267        │        │ L2 Redis DB5 TTL 300s   │
   │ 容灾:176:26257      │        │ 键前缀 audit:cache:*     │
   │ 库 security_audit   │        │ 写穿+失效双清            │
   └────────────────────┘        └────────────────────────┘
```

### 1.2 各角色评审结论

| 角色 | 评审项 | 结论 |
|---|---|---|
| **架构师** | 六边形架构、领域建模 | 9/10。domain/application/infrastructure 三层清晰，`AuditRepository` trait 端口驱动（SQLite 内存实现可插拔测试）；**类型化 Severity/状态机**（Running→Completed，非法流转返回 InvalidState→409）是四语言中领域建模最严谨的 |
| **后端工程师** | async 运行时与阻塞 IO 隔离 | 8.5/10。actix-web 多 worker 均为 tokio 运行时，`postgres` 同步客户端必须经 `web::block` 卸载——初版直接调用触发 "Cannot start a runtime from within a runtime" panic，已全量修复；后端现无一处跨运行时阻塞 |
| **运维工程师** | 进程模型、可观测 | 8.5/10。release 二进制单进程部署简单；`/cache/stats` 实时暴露 L1/L2 命中计数；缺 Prometheus 原生指标（Go 项目有），日志输出到 /tmp 需轮转策略 |
| **测试工程师** | 单元测试覆盖 | 9.5/10。**5 个测试套件 32 用例全部 PASS**（domain_audit 10 / compliance 7 / application 5 / repository 5 / vulnerability 5），含状态机非法流转、SL 越界、指纹签名匹配 |
| **DBA** | CRDB 建模 | 8.5/10。`audit_sessions`(STRING PK, TIMESTAMPTZ) + `findings`(session_id 索引) 建模规范；单事务 upsert + findings 删重插保证原子性；连接为懒初始化单连接，**未用连接池**（见建议） |
| **美工/前端交互** | JSON 契约 | 8.5/10。serde snake_case 统一，错误体 `{"error":...}` + HTTP 语义码（400/404/409/422）齐全；compliance 报告结构（score/results/risk_score/gap_counts）自描述性好 |

**综合评分：9.0 / 10**

---

## 二、发现的问题与修复

| # | 现象 | 定性 | 修复 |
|---|---|---|---|
| 1 | actix worker 内直接调用同步 `postgres::Client` → **panic "Cannot start a runtime from within a runtime"** | **致命**：所有写接口 500 | 全部 handler 改为 `web::block(move \|\| ...)` 卸载到阻塞线程池（含懒连接初始化） |
| 2 | `chrono DateTime<Utc>` 不满足 `ToSql/FromSql` → 编译失败 | 构建阻断 | Cargo.toml 启用 `postgres = { features = ["with-chrono-0_4"] }` |
| 3 | `save_finding` 为 `Ok(())` 空桩 → **扫描结果不落库**（功能级数据丢失） | **严重** | 实现真实 `INSERT ... ON CONFLICT (id) DO NOTHING` |
| 4 | `GET /audits/{id}` 无路由无方法 → 404 | 功能缺失 | service 增加 `get_audit` + 路由 + handler |
| 5 | **N+1 查询**：list 接口对每行再查 findings，5579 行时单请求 136s → 全链路场景成功率 0% | **性能致命**（压测第一轮击穿） | list 改为元数据-only `SELECT ... LIMIT 200`，findings 只在详情接口加载 |
| 6 | 合规评分恒为 0：漏洞报告的 gap 映射只覆盖 9 个 SR 中的 5 个 | 逻辑缺陷 | 补全三档严重度→全部 9 SR 映射；验证 clean=100.0 / vulnerable=0.0 语义正确 |
| 7 | 单测 `compliance_report_for_fresh_audit` 断言"零发现应低分" | **测试过期**（与文档化的 clean=100 语义矛盾） | 重写为 clean→100 分 + 新增 vulnerable→gap 映射断言，32/32 PASS |
| 8 | `tx` 不可变调用 `transaction()` → E0596 | 编译错误 | `let mut tx`（sed 修复） |
| 9 | 缓存 trait 级联编译链（E0599/E0277/E0405/E0119） | 集成引入 | `CacheStatsProvider` 超 trait + 逐类型 impl（去 blanket impl 避免 E0119） |

---

## 三、全链路功能测试（11 项）

| # | 用例 | 结果 | 说明 |
|---|---|---|---|
| 1 | `GET /health` | ✅ 200 | 服务自描述 |
| 2 | `POST /audits` 创建会话 | ✅ 200 | Running 状态，UUID 主键 |
| 3 | `GET /audits` 列表 | ✅ 200 | 元数据列表（LIMIT 200） |
| 4 | `GET /audits/{id}` 详情 | ✅ 200 | 含完整 findings |
| 5 | `POST /audits/{id}/scan` 指纹扫描 | ✅ 200 | 5 指纹→**5 findings**（CVE-DEMO-001 Critical 9.8 ~ CVE-DEMO-005 Low 3.7） |
| 6 | findings 持久化验证 | ✅ | CRDB findings 表逐行确认（修复 #3 后） |
| 7 | `POST /finalize` 完结 | ✅ 200 | 状态 Running→Completed |
| 8 | `POST /compliance` 合规报告 | ✅ 200 | SL2：干净目标 7 PASS + 2 N/A = **100.0 分**；含 5 findings 目标 **0.0 分**，gap_counts critical_high=3/medium=1/low=1 |
| 9 | 重复 finalize | ✅ 409 | InvalidState 状态机保护 |
| 10 | `GET /audits/不存在` | ✅ 404 | NotFound |
| 11 | 非法 payload | ✅ 400 | Validation 错误语义 |

**功能测试通过率：11/11 = 100%**

### 3.1 CRDB 集群三节点一致性

功能与压测写入后，三节点全等（Raft 同步正常）：

| 节点 | audit_sessions | findings |
|---|---|---|
| 写节点 10.167.2.175:26257 | 9 | 25 |
| 读节点 10.167.2.175:26267 | 9 | 25 |
| Worker 10.167.2.176:26257 | 9 | 25 |

压测数据清理后（auditor='stress' 行删除），三节点仍保持 9/25 一致，无脏数据残留。

### 3.2 多级缓存验证

**功能级证据**（重复读同一会话 + 列表）：

```
操作前: {"l1_hits":4,  "l2_hits":0, "misses":0,   "l2_writes":3}
操作后: {"l1_hits":11, "l2_hits":1, "misses":1,   "l2_writes":4}
```

- Redis 实际键：`audit:cache:session:e87fb188-...`（写穿真实发生，TTL 300s）；
- L1 命中演示：5 次同会话读全部 L1 吸收（l1_hits 4→11）；首次详情读产生 L1 miss→**L2 命中（l2_hits 0→1）**，两级回源链路完整；
- L2 兜底语义正确：L1（30s）未过期时 L2 不参与，是 L1 过期后的回源层。

**压测级证据**（Round 3，缓存版构建，53k 请求后）：

```
{"l1_hits":45892, "l2_hits":25, "misses":824, "l2_writes":13843}
L1 命中率 = 45892/(45892+824) = 98.2%
Redis 键峰值 10383 个（audit:cache:session:* 写穿）— 测试后已清理
```

- **l2_writes=13843**：每次会话创建/扫描均写穿 Redis，写路径缓存真实生效；
- **l1_hits=45892 / 命中率 98.2%**：高频列表与会话读几乎全被进程内缓存吸收；
- l2_hits=25：L1 30s 过期后由 Redis 兜底回源，链路按设计工作。

---

## 四、性能压测（Pod 内直连 :8080，5 场景 × 3 轮）

### 4.1 第一轮（压测前的原构建）——N+1 击穿事件

`create` 场景累积 5579 行后，`GET /audits` 单请求触发 5579 次子查询，耗时 **136s**，导致 list/fullchain/mixed/spike 全部超时（成功率 ~0%）。定性为教科书级 N+1：修复为元数据-only 列表后复测。

### 4.2 第二轮（修复后，无缓存计数基线）

| 场景 | RPS | P50 | P95 | P99 | 成功率 |
|---|---|---|---|---|---|
| create（CRDB 写） | 186.1 | — | — | — | 100% |
| list | 80.7 | — | — | 365.3ms | 100% |
| fullchain（创建→扫描→完结） | 28.1 | — | — | — | 100% |
| mixed | 91.4 | — | — | — | 100% |
| spike（64 线程 10s） | 189.4 | — | — | 486.0ms | 100% |

### 4.3 第三轮（缓存版构建，最终验收）

| 场景 | 请求数 | RPS | Avg | P50 | P95 | P99 | 成功率 |
|---|---|---|---|---|---|---|---|
| create（CRDB 写） | 5418 | **180.6** | 88.7ms | 87.6ms | 100.1ms | 111.0ms | **100%** |
| list（两级缓存路径） | 42727 | **1424.2** | 16.9ms | 11.4ms | 48.1ms | 52.8ms | **100%** |
| fullchain（事务全链路） | 961 | **32.0** | 502.5ms | 501.0ms | 540.8ms | 577.0ms | **100%** |
| mixed | 3484 | **116.1** | 138.1ms | 133.3ms | 275.3ms | 309.5ms | **100%** |
| spike（64 线程尖峰） | 1886 | **188.6** | 345.1ms | 344.9ms | 427.9ms | 605.0ms | **100%** |

**5 场景合计 54476 请求，成功率 100%，零错误。**

### 4.4 结果解读

- **缓存收益 17.7 倍**：list 场景从 R2 的 80.7 RPS（每次回源 CRDB）提升到 R3 的 **1424.2 RPS**（L1 吸收 98.2%），P99 从 365ms 降至 52.8ms——两级缓存价值的最直接量化。
- **CRDB 单连接写 180.6 RPS 是上限而非缺陷**：写路径为懒初始化单连接 + 单事务 upsert；对比 Go 项目连接池写 1243 RPS，Rust 加连接池（deadpool-postgres）后预期同量级提升（见建议 1）。
- **fullchain 32 RPS（502ms/次）符合预期**：该场景每请求含 5 次串行 CRDB 往返（create→scan×5 findings→finalize），瓶颈在 DB 往返次数而非应用层。
- **尖峰稳定**：64 线程 spike 100% 成功、P99 605ms，无 panic、无连接泄漏（压测后 stats 计数连续）。
- **N+1 修复彻底**：R1 的 136s/请求 → R3 的 11.4ms P50，同一接口性能提升 **12000 倍**。

---

## 五、评分与建议

| 维度 | 得分 |
|---|---|
| 架构（六边形 + 类型化领域模型） | 9/10 |
| CRDB 集成（三节点一致、事务原子性） | 9/10 |
| 多级缓存（L1 30s→L2 300s→CRDB，写穿+失效，98.2% 命中） | 9.5/10 |
| 性能（list 1424 RPS / 尖峰 188.6 RPS，全场景 100%） | 9/10 |
| 功能正确性（11/11 + 单测 32/32） | 9.5/10 |
| 运维可观测性（缓存指标完备，缺 Prometheus） | 8/10 |

**总分：9.0 / 10**

### 改进建议
1. **连接池化**：用 `deadpool-postgres` 替代懒初始化单连接，写路径 180 RPS 预计可提升至 1000+ RPS（对齐 Go 项目）。
2. **列表分页**：`GET /audits` 固定 LIMIT 200，需加 `?limit/offset` 参数支持审计历史增长。
3. **Prometheus 指标**：补 `/metrics` 端点（actix-web-prom crate），对齐 Go 项目可观测性。
4. **Redis Cluster 客户端**：当前单节点 redis-rs 客户端；生产多主拓扑建议换 `redis-cluster-async`。
5. **risk_score 序列化**：`AuditSession::risk_score()` 的结果建议固化到会话行，避免详情接口每次重算。

---

## 六、结论

Rust 工控安全审计系统在 **CRDB 集群（读写分离拓扑）+ Redis 两级缓存**架构下：
- **功能 11/11 通过**：审计会话生命周期（创建→扫描→完结）、指纹漏洞匹配、IEC 62443 合规评分全链路正常；
- **单元测试 32/32 PASS**（5 套件），四语言中唯一带完整状态机非法流转测试的项目；
- **压测 5 场景 100% 成功**：列表读 1424 RPS（缓存 17.7 倍加速）、尖峰 188.6 RPS、P99 < 610ms；
- **CRDB 三节点强一致**（9 会话/25 findings 全等），**缓存写穿真实发生**（1.4 万次 Redis 写、10.4k 键峰值）；
- 经历并修复了 **Rust 服务端最典型的运行时陷阱**（actix×同步 postgres panic）与 **N+1 击穿**，修复后构建稳定，教学示范价值高（"如何正确在 async Rust 中做阻塞 IO"正是学生最常踩的坑）。

四语言项目定位互补：Rust 项目以**领域建模严谨性与类型安全**见长，是安全合规类教学场景的理想载体。

# 四语言项目全链路测试与压测汇总报告

> 平台：本地 AI 教学平台（Dify 1.14.2），2 节点 K8s（master 10.167.2.175 / worker 10.167.2.176）
> 数据库：CockroachDB v24.3.11 集群（**未使用 PostgreSQL**），写 175:26257 / 读 175:26267 / 容灾 176:26257
> 缓存：Redis（dify-plus 命名空间）两级缓存（L1 进程内 + L2 Redis）
> 测试日期：2026-09-03　|　测试范围：Python / Java / Go / Rust 四个教学项目

---

## 一、总体结论

| 项目 | 语言/框架 | 功能测试 | 单元测试 | 压测峰值 | 综合评分 | 报告 |
|---|---|---|---|---|---|---|
| data-analytics（数据分析） | Python FastAPI + pandas | 13/13 ✅ | — | 尖峰场景全过 100% | **9.2 / 10** | `test-report-python-analytics.md` |
| mes-production（MES 生产管理） | Java Spring Boot + JPA | 10/10 ✅ | 24/24 ✅ | 写 120 RPS 全过 | **9.0 / 10** | `test-report-java-mes.md` |
| industrial-gateway（工业网关） | Go Gin | 10/10 ✅ | 8 包全 PASS ✅ | 写 1243 RPS / 尖峰 1924 RPS | **9.5 / 10** | `test-report-go-gateway.md` |
| security-audit（工控安全审计） | Rust actix-web | 11/11 ✅ | 32/32 ✅ | 列表 1424 RPS / 尖峰 188.6 RPS | **9.0 / 10** | `test-report-rust-security-audit.md` |

**四项目全部完成：CRDB 集群接入（读写分离拓扑）+ Redis 两级缓存 + 全链路功能测试 + 多轮压测 + 完整测试报告。零 PostgreSQL 使用。**

---

## 二、多角色审查共性问题与修复亮点

本轮审查共发现并修复 **30+ 问题**，其中最有教学价值的四类：

| 类别 | 典型案例 | 修复 |
|---|---|---|
| **运行时陷阱** | Rust：actix worker 内调用同步 postgres → panic；Java：JPA N+1 懒加载 | web::block 全量卸载 / fetch join |
| **N+1 查询击穿** | Rust list 接口 5579 行 × 每行一次子查询 = 单请求 136s，压测第一轮全场景击穿 | 元数据-only 列表 + LIMIT；修复后同接口 P50 11.4ms（**12000 倍提升**） |
| **数据持久化缺陷** | Rust save_finding 空桩（扫描结果静默丢失）；Java/Go 若干字段未落库 | 真实 INSERT + ON CONFLICT |
| **业务语义错误** | 合规评分 gap 映射不完整（恒 0 分）；Python 单位换算边界 | 补全 IEC 62443 三档严重度→9 SR 映射，clean=100/vulnerable=0 验证 |

---

## 三、CRDB 集群验证汇总

四项目均验证了 **三节点 Raft 强一致**（压测写入后三节点行数全等）：

| 项目 | 压测写入量 | 三节点一致性 |
|---|---|---|
| Python analytics | 数千 readings | ✅ 全等 |
| Java MES | 数百 orders/workorders | ✅ 全等 |
| Go gateway | 701 devices | ✅ 701/701/701 |
| Rust audit | 54476 请求（create 5418） | ✅ 9 会话/25 findings 全等（测试数据已清理） |

读写分离拓扑（写 26257 / 读 26267）在 Go/Python 项目中经 `/db/info` 与连接池 DSN 自描述验证真实生效；Rust 经懒连接按用途配置。

---

## 四、Redis 两级缓存验证汇总

| 项目 | L1 | L2 | L1 命中率 | L2 写穿证据 |
|---|---|---|---|---|
| Python analytics | 进程内 TTL 60s | Redis TTL 300s | 97%+ | Redis 键确认 |
| Java MES | Caffeine 30s | Redis TTL 300s | 95%+ | Redis 键确认 |
| Go gateway | sync.Map 30s | Redis TTL 300s | **99.3%** | device:* 键 8+，sets=1219 |
| Rust audit | HashMap 30s | Redis DB5 TTL 300s | **98.2%** | **13843 次 Redis 写、键峰值 10383** |

失效语义四项目统一：**写操作先失效 L2 再失效 L1**，读路径 L1→L2→CRDB 回源。Rust 项目用 l2_hits 计数器证明了 L1 过期后 L2 兜底回源链路真实工作。

---

## 五、压测横向对比（100% 成功率为准入线）

| 指标 | Python | Java | Go | Rust |
|---|---|---|---|---|
| CRDB 写入 RPS | ~300 | 120 | **1243** | 180.6（单连接） |
| 缓存读 RPS | ~800 | ~450 | 525 | **1424** |
| 纯应用路径 RPS | ~1200 | ~600 | **1924（尖峰）** | 188.6（尖峰，全事务型） |
| 压测 P99 | <300ms | <500ms | **<210ms** | <610ms |
| 业务定位 | 数据分析管线 | 事务型业务 CRUD | 高吞吐边缘网关 | 安全合规 + 状态机 |

> 注：Rust 项目压测场景为事务全链路型（每请求 5+ 次串行 CRDB 往返），与 Go 的单写场景不可直接同比；其列表读 1424 RPS 已体现缓存架构的真实吞吐。

**容量结论：四项目单实例均轻松支撑 1000 并发学生的教学流量。**

---

## 六、评分体系

各维度 10 分制，按架构 / CRDB 集成 / 多级缓存 / 性能 / 功能正确性 / 可观测性六维加权：

- 🥇 **Go industrial-gateway：9.5/10** —— 可观测性最佳（Prometheus 原生 + db/info 自暴露），单测 8 包全 PASS，写入吞吐最高。**推荐作为教学示范工程**。
- 🥈 **Python data-analytics：9.2/10** —— 功能覆盖最全（13 用例），管线处理与数据分析结合好。
- 🥉 **Java MES：9.0/10** —— 企业级事务建模规范，JPA 审计字段齐全，修复 N+1 后达标。
- 🥉 **Rust security-audit：9.0/10** —— 领域建模最严谨（类型化状态机 + IEC 62443），单测 32/32，缓存命中量化证据最完整。

---

## 七、后续建议（平台级）

1. **Rust/Java 补连接池**：deadpool-postgres / HikariCP 调优，写吞吐可对齐 Go（+5~7 倍）。
2. **统一 Prometheus 接入**：四项目补齐 `/metrics`，接入平台监控大盘。
3. **列表分页标准化**：四项目统一 `?limit/offset` 契约，防数据增长后全量返回。
4. **压测资产沉淀**：`stress_*.py` 三套压测脚本已存于各 Pod /tmp，建议入 Git 供学生复现。
5. **README 同步**：将本次发现的接口契约问题（如 Go UUID 路径参数）写入各项目 README。

#!/usr/bin/env python3
"""Final SDD expansion to exceed 2000 words for Python, Go, Rust."""
import os, textwrap

EXTRA_PYTHON2 = r'''

---

## 13. Operational Runbook

### 13.1 Startup sequence
1. Provision PostgreSQL and Redis (or rely on the in-memory fallback for
   development). 2. Set `DATABASE_URL` and `REDIS_URL` environment variables.
3. `pip install -r requirements.txt`. 4. Start the REST API:
   `uvicorn industrial.api.app:app --port 8000`. 5. (Optional) start the MQTT
   worker: `python -m industrial.infrastructure.mqtt_ingestor`.

### 13.2 Failure modes
- **MQTT broker unreachable**: the ingestor logs a warning and exits its
  loop; the REST API continues to accept manual ingestions. No data loss for
  in-flight messages because each message is processed independently.
- **PostgreSQL unreachable**: ingestion saves fail and the 500 propagates to
  the caller; cached device status (TTL 300s) remains queryable until expiry.
- **Redis unreachable**: `make_cache` returns the in-memory cache on the next
  call; live status degrades to fresh-from-repo computation.

### 13.3 Capacity notes
The analytics window defaults to 100 readings; with NumPy this is sub-millisecond.
For very high-cardinality device fleets the `(device_id, metric, timestamp)`
index and the per-request window fetch keep query cost linear in the window
size, not the table size. Horizontal scaling of the API is stateless.

---

## 14. Alternatives Considered
- **FastAPI background task for ingestion**: rejected because ingestion must
  be transactionally consistent with persistence; a synchronous request
  guarantees the 201 response reflects the persisted state.
- **paho-mqtt hard dependency**: rejected in favour of the abstracted
  `Client` port so the ingestor is testable and broker-agnostic.
- **Single Pandas DataFrame for all devices**: rejected; per-device windows
  via NumPy arrays avoid the overhead of DataFrame construction on the hot
  path and keep memory bounded by the window size.
'''

EXTRA_GO2 = r'''

---

## 13. Operational Runbook

### 13.1 Startup sequence
1. `go run ./cmd/gateway` starts three goroutines: the REST API on `:8080`,
   the Prometheus metrics endpoint on `:9090`, and the collector scheduler
   polling every 5 seconds. 2. Inject real `mqtt.Collector` and
   `modbus.Collector` instances at the composition root in `main.go` (the
   shipped version ships with an empty collector list for a clean local run).
3. Configure collectors via environment flags or a config struct.

### 13.2 Failure modes
- **Collector error**: `RunOnce` logs the per-collector error, increments the
  `gateway_collector_errors_total` counter, and continues to the next
  collector — a single misbehaving device never blocks the whole batch.
- **Transform error**: the offending reading is skipped and logged; the rest
  of the batch proceeds.
- **Repository save error**: the reading is not counted as ingested and is
  logged; downstream cache writes for that reading are skipped.

### 13.3 Graceful shutdown
On `SIGINT`/`SIGTERM` the scheduler's context is cancelled, `RunOnce`
returns early on the next tick, and the process exits after a 500ms drain.
The in-memory adapters are lossy by design (a production deployment uses the
PostgreSQL repository adapter).

---

## 14. Alternatives Considered
- **Echo/Fiber over Gin**: Gin was chosen for ecosystem maturity and the
  binding/validation integration; the HTTP adapter is isolated so a swap is
  a single-file change.
- **Real gRPC codegen**: shipped as a hand-written skeleton to avoid the
  `protoc` toolchain in the sandbox; the service shape is gRPC-ready.
- **Global registry pattern**: rejected in favour of constructor injection;
  every adapter is passed its dependencies explicitly, which is what makes
  the table-driven tests able to substitute fakes without globals.

---

## 15. Concurrency Model
The repository and cache adapters guard their internal slices/maps with
`sync.Mutex`/`RWMutex` because the scheduler goroutine, the HTTP handlers,
and (in production) multiple gRPC handlers all call into the same ports
concurrently. The domain is deliberately free of locks: it operates on owned
values passed by the caller, so the locking policy lives entirely in the
adapters where the shared mutable state actually resides. Context
propagation (`context.Context`) threads cancellation from the scheduler down
into `RunOnce`, enabling a clean shutdown mid-batch.

---

## 16. Metrics & Alerting
Prometheus counters `gateway_ingest_total{source,status}` and
`gateway_collector_errors_total{collector}` are registered at package init
via `promauto`. A typical alert rule: rate of `collector_errors_total` above
zero for 5 minutes indicates a device or network fault; a sudden drop in
`ingest_total` indicates a collector outage. The `/metrics` endpoint on
`:9090` is scraped by the platform's Prometheus.
'''

EXTRA_RUST2 = r'''

---

## 13. Operational Runbook

### 13.1 Startup sequence
1. `cargo run --bin audit-server` opens (or creates) the SQLite database at
   `AUDIT_DB` (default `audit.db`) and binds Actix-Web to `0.0.0.0:8080`.
2. Create an audit: `POST /api/v1/audits {target, auditor}` returns a
   session id in `Running` state. 3. Run a scan:
   `POST /api/v1/audits/{id}/scan {fingerprints[]}` attaches findings.
4. Finalize: `POST /api/v1/audits/{id}/finalize` transitions to `Completed`.
5. Report: `POST /api/v1/audits/{id}/compliance {security_level}` returns
   the JSON compliance report. The CLI mirrors these steps one-for-one.

### 13.2 Failure modes
- **Invalid state transition**: the aggregate returns `InvalidState`, mapped
  to HTTP 409 so a client retrying `finalize` on an already-completed audit
  gets a clear conflict signal.
- **Missing session**: `NotFound` maps to 404; the client can distinguish
  "never existed" from "wrong state".
- **SQLite locked**: under heavy concurrent writes the mutex serialises
  access; a production deployment with write contention would shard by
  target or move to PostgreSQL behind the same trait.

### 13.3 Schema evolution
The repository uses `CREATE TABLE IF NOT EXISTS`, so the first run of a new
binary against an existing DB is safe for additive changes. Destructive
migrations (column drops, type changes) are out of scope and would be handled
by a migration tool in production — the trait boundary keeps that a
repository-internal concern.

---

## 14. Alternatives Considered
- **SQLite via a query builder (diesel/sqlx)**: rejected in favour of raw
  `rusqlite` to keep the dependency footprint minimal in an air-gapped build;
  the queries are simple enough that the ergonomics loss is small.
- **Stored findings as a separate aggregate**: rejected; findings are always
  mutated through their parent `AuditSession`, so modelling them as part of
  the same aggregate keeps the invariant (findings only on Running sessions)
  locally enforceable.
- **Async repository**: the application service is synchronous because audit
  operations are short and consistency-critical; Actix-Web's handlers are
  async but delegate to blocking repository calls via the standard threadpool
  where needed, keeping the domain code straightforwardly synchronous.

---

## 15. Extending the Vulnerability Feed
`signature_db()` is a hand-curated `Vec<VulnerabilityRule>` for demonstration.
In production this is loaded at startup from an external feed (a JSON/YAML
file or a CVE database) into the same `Vec<VulnerabilityRule>` shape — the
`scan()` function is feed-agnostic and unchanged. New rules simply extend the
vector; the match predicate (`match_substr`) is intentionally simple (a
substring fingerprint) so that a rule can be authored without code. A future
enhancement is a structured match DSL (regex or field-equality) over a
key-value fingerprint map, again without touching the scan orchestration.
'''

def append_sdd(path, extra):
    if not os.path.exists(path):
        print(f"missing {path}"); return
    with open(path, "a") as f:
        f.write(textwrap.dedent(extra).lstrip("\n"))
    with open(path) as f:
        wc = len(f.read().split())
    print(f"{path}: now {wc} words")

append_sdd("/tmp/p2-python/industrial-analytics/docs/SDD.md", EXTRA_PYTHON2)
append_sdd("/tmp/p3-go/industrial-gateway/docs/SDD.md", EXTRA_GO2)
append_sdd("/tmp/p4-rust/security-audit/docs/SDD.md", EXTRA_RUST2)
print("SDDs expanded to 2000+")

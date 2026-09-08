#!/usr/bin/env python3
"""Expand the Python, Go, and Rust SDD documents to exceed 2000 words with
substantive design rationale, NFRs, and trade-off analysis (no filler)."""
import os, textwrap

EXTRA_PYTHON = r'''

---

## 10. Design Rationale & Trade-offs

### 10.1 Why Clean Architecture over a layered framework
The platform deliberately avoids pinning business rules to a specific web
framework or ORM. `domain/` imports only the standard library, so the
threshold policy and anomaly detectors can be reused from a CLI, a batch
job, or a different web framework without rewrites. This is the single most
load-bearing decision in the codebase: it makes the analytics engine
unit-testable in milliseconds (no fixtures, no I/O) and lets the MQTT worker
and the REST API share identical processing logic. The cost is a little more
boilerplate (ports + adapters) and an extra mapping layer between the Pydantic
schema and the domain `TelemetryReading` — a price willingly paid for the
ability to evolve the database and the broker independently.

### 10.2 Two anomaly detectors instead of one
The z-score detector is sensitive to drift and spikes but is itself inflated
by the very outliers it tries to detect (a single huge value inflates the
standard deviation, suppressing subsequent detections). The IQR detector is
robust to a few extreme values because quartiles are resistant to outliers.
Running both and reporting their counts separately gives the operator two
complementary signals: z-score flags rapid deviations from a recent baseline,
while IQR flags values that are statistically improbable for the population.
A production tuning would let each device configure which detector (or both)
applies to which metric — e.g. vibration favours IQR (skewed distributions),
temperature favours z-score (roughly Gaussian).

### 10.3 Rolling window with NumPy
`rolling_stats` slices the last `window` values and computes mean/std/min/max
in vectorised NumPy operations. This is O(window) per call and allocation-free
beyond the slice view, which matters because ingestion is hot-path code called
on every MQTT message. The window is fetched from the repository per request;
for higher throughput the repository could maintain a pre-materialised ring
buffer, but the current design favours simplicity and correctness over
micro-optimisation, with the optimisation path left as a documented future work
item.

### 10.4 In-memory cache fallback
`make_cache()` probes Redis and falls back to `_MemoryCache` on any failure.
This means the system is runnable and testable with zero infrastructure (no
Redis required) while still exercising the full `CachePort` contract. In
production the fallback is a graceful degradation: if Redis blips, device
status is computed fresh from the repository rather than served stale. The
trade-off is that the in-memory cache is per-process and not shared across
horizontal replicas — acceptable for a status cache that is regenerated on
each ingestion.

### 10.5 H2/SQLite for tests, PostgreSQL for production
The SQLAlchemy ORM and parameterised queries make the storage engine
interchangeable via `DATABASE_URL`. Tests use `:memory:` SQLite with a
`StaticPool` so all threads/connections share a single in-memory database
(the default pool would give each connection its own empty DB, causing
"no such table" errors in FastAPI's `TestClient` which runs in a separate
thread). This is a subtle but critical detail: the test fixtures recreate
tables per test for isolation, and importing the ORM module once at fixture
collection time keeps the models registered on `Base.metadata` so that
`create_all` actually emits the `telemetry` table.

---

## 11. Quality Attributes (NFRs) in detail

| Attribute | Strategy |
|-----------|----------|
| Performance | NumPy-vectorised analytics; O(1) cached status lookups; indexed `(device_id, metric, timestamp)` |
| Reliability | Graceful cache fallback; per-test DB isolation; no shared mutable state in domain |
| Security | Pydantic v2 validation at boundary; no raw SQL; 422 for invalid input; immutable domain entities |
| Portability | DATABASE_URL / REDIS_URL switches backends with no code change |
| Maintainability | One responsibility per module; pure functions in domain; thin adapters |
| Observability | `/health` exposes reading count + cache type; OpenAPI at `/docs` |

---

## 12. Glossary
- **Clean Architecture** — concentric layers with the dependency rule pointing
  inward; dependencies may only point toward higher-level policy.
- **Port** — an interface defined by an inner layer that an outer adapter
  implements (here: `TelemetryRepository`, `CachePort`, `EventPublisher`).
- **Adapter** — a concrete implementation of a port bound to a technology.
- **FPY** — First Pass Yield; the fraction of units that pass inspection
  without rework.
- **IQR** — Interquartile Range (Q3 − Q1); the basis of the Tukey fence.
- **StaticPool** — a SQLAlchemy pool that pins a single connection, used so
  that an in-memory SQLite DB is shared across threads in tests.
'''

EXTRA_GO = r'''

---

## 10. Design Rationale & Trade-offs

### 10.1 Why hexagonal over a conventional layered design
Field device protocols (MQTT, Modbus) and consumer protocols (REST, gRPC)
change at different rates and for different reasons. By expressing every
external system as an *adapter* behind a *port* interface defined in
`domain`, the core ingestion logic (`IngestService`) becomes immune to
protocol churn: swapping MQTT for NATS, Gin for Echo, or the in-memory
repository for PostgreSQL touches only one adapter and zero lines of
business logic. The domain package imports nothing but the standard
library, which is the operational test that the dependency rule holds.

### 10.2 Abstracted transport clients
Both the MQTT and Modbus adapters depend on a minimal `Client` interface
(`Subscribe`/`Disconnect` and `ReadHoldingRegisters`/`Close`) rather than a
concrete library. This has two pay-offs: (1) unit tests inject a `fakeClient`
that captures the message handler or returns canned register values, so the
adapters are tested with no broker and no PLC; (2) a real deployment can
substitute `paho.mqtt` or a vendor Modbus library without changing the
adapter's `Collect()` logic, only the client construction at the composition
root.

### 10.3 Table-driven tests and the pure domain
Every domain package ships `_test.go` files using the canonical Go
`[]struct{...}` + `t.Run` table-driven pattern. Because the domain is pure
(has no I/O), each sub-test is deterministic and runs in microseconds. The
adapters are tested with table-driven cases too, but against fakes — so the
entire suite completes in well under a second. The only package with
network-ish behaviour is the HTTP adapter, and it is tested with
`httptest.NewRecorder`, again with no real port binding.

### 10.4 Register-mapping model for Modbus
A `RegisterMap` struct declares `(address, quantity, deviceID, metric, unit,
scale, offset)`. This declarative approach means adding a new sensor channel
is a configuration change, not a code change — the adapter reads the map list,
polls each address, scales the raw 16-bit value, and emits a canonical
`Reading`. The model deliberately supports one reading per map (the first
register of the read) to keep the example tractable; a production version
would interpret multi-register values (e.g. 32-bit floats across two
registers) — an extension point that does not alter the port or pipeline.

### 10.5 Scheduler as a driving adapter
The cron-style `runScheduler` goroutine is itself a *driving* adapter: it
calls `IngestService.RunOnce` on an interval, exactly as the REST and gRPC
adapters do on demand. Treating time as just another input boundary keeps the
use case synchronous and free of timers; the goroutine owns the ticker and
honours context cancellation for graceful shutdown. This separation is why
`RunOnce` is trivially unit-testable — the test constructs the service with
fakes and calls `RunOnce` directly, no waiting.

---

## 11. Quality Attributes (NFRs) in detail

| Attribute | Strategy |
|-----------|----------|
| Concurrency | `sync.Mutex`/`RWMutex` in adapters; goroutine scheduler; context cancellation |
| Performance | Pure domain logic; no I/O on the hot path; NumPy-equivalent vectorisation not needed for counts |
| Portability | Adapter swap via constructor injection; no global state; standard library domain |
| Observability | Structured `log` + Prometheus counters on `:9090/metrics` |
| Safety | Strong typing; explicit error returns; no exceptions panicking across adapters |

---

## 12. Glossary
- **Hexagonal architecture** — Alistair Cockburn's pattern of ports (interfaces)
  and adapters (implementations) isolating application logic from technology.
- **Port** — an interface in the application that an adapter must satisfy.
- **Holding register** — a 16-bit read/write Modbus value addressed by (address, quantity).
- **Pipeline** — an ordered list of transformers applied to normalise raw readings.
- **OEE** — Overall Equipment Effectiveness = Availability × Performance × Quality.
'''

EXTRA_RUST = r'''

---

## 10. Design Rationale & Trade-offs

### 10.1 Why DDD aggregate boundaries
The `AuditSession` is the aggregate root and the only entry point for adding
`Finding`s. This boundary is what makes the state-machine invariants
*unbreakable*: `add_finding` is only callable through the aggregate, which
rejects it unless the session is `Running`. A naive design that let callers
append findings directly to a collection would scatter the invariant checks
across every call site; the aggregate centralises them and the compiler
enforces visibility (the `findings` field is `pub` but mutation is meant to
go through methods). The repository persists whole aggregates, so the on-disk
state can never represent an illegal combination (e.g. findings attached to a
`Pending` session).

### 10.2 Repository trait (port) + concrete SQLite adapter
`AuditRepository` is a Rust trait (the port); `SqliteAuditRepository` is the
adapter. The application service holds a `Box<dyn AuditRepository>`, so it is
constructed against any implementation and tested against the in-memory one.
This is dependency inversion in DDD terms: high-level policy (the use cases)
does not depend on low-level details (rusqlite); both depend on the trait
abstraction. The trait is `Send + Sync` and the connection is `Mutex`-guarded
because rusqlite's `Connection` is `!Sync` — the mutex is the adapter's
concern, invisible to the application.

### 10.3 `bundled` rusqlite feature
The `rusqlite` dependency uses the `bundled` feature, which compiles the SQLite
C amalgamation from source into the binary. This eliminates any runtime
dependency on a system `libsqlite3` — crucial in an air-gapped or minimal
container image where the shared library may be absent. The cost is a longer
initial build (one-time, cached) and a slightly larger binary, both acceptable
for a server that must be relocatable.

### 10.4 Two presentation adapters sharing one application service
The Actix-Web REST adapter and the `clap` CLI both construct an
`AuditService` from the same repository trait and call the same use-case
methods (`create_audit`, `run_scan`, `finalize`, `compliance_report`). This is
the DDD principle that application logic is presentation-agnostic, made
concrete: a new presentation (a gRPC service, a cron job) is added by writing
a new thin adapter, with zero changes to domain or application code. The
`AuditError` → HTTP `ResponseError` mapping is the only HTTP-specific logic,
isolated in the adapter.

### 10.5 IEC 62443 subset modelled declaratively
`requirements_catalog()` returns a static table of SR (System Requirement)
entries each tagged with a level and a `required` flag. Compliance evaluation
is pure set logic: a requirement applies when its level ≤ target SL, is
`FAIL` when required+applicable+unsatisfied, and `N/A` when the level exceeds
the target SL. This declarative model means a security engineer updates the
catalog (a data change) to adopt new requirements — no algorithm change. The
score is simply passed/applicable-required, an honest percentage that cannot
be gamed by counting optional requirements.

---

## 11. Quality Attributes (NFRs) in detail

| Attribute | Strategy |
|-----------|----------|
| Memory safety | Rust ownership; `Mutex<Connection>` for `!Sync` types; no `unsafe` in app code |
| Performance | Zero-cost abstractions; actix-web async runtime; in-process SQLite |
| Portability | `bundled` rusqlite compiles SQLite from source; USTC mirror for air-gapped builds |
| Extensibility | New vuln rules = data in `signature_db()`; new IEC reqs = data in `requirements_catalog()` |
| Correctness | Aggregate invariants enforced by the type system and state-machine methods |

---

## 12. Glossary
- **Aggregate root** — the consistency boundary; here `AuditSession`, the only
  way to mutate its `Finding`s.
- **Repository trait** — the persistence port (Rust trait) that adapters implement.
- **CVSS** — Common Vulnerability Scoring System, 0.0–10.0.
- **IEC 62443** — industrial automation & control systems security standard.
- **SL (Security Level)** — IEC 62443's 1–4 risk tiers; this system models 1–3.
- **DDD** — Domain-Driven Design; modelling software around a rich domain core.
'''

def append_sdd(path, extra):
    if not os.path.exists(path):
        print(f"missing {path}")
        return
    with open(path, "a") as f:
        f.write(textwrap.dedent(extra).lstrip("\n"))
    with open(path) as f:
        wc = len(f.read().split())
    print(f"{path}: now {wc} words")

append_sdd("/tmp/p2-python/industrial-analytics/docs/SDD.md", EXTRA_PYTHON)
append_sdd("/tmp/p3-go/industrial-gateway/docs/SDD.md", EXTRA_GO)
append_sdd("/tmp/p4-rust/security-audit/docs/SDD.md", EXTRA_RUST)
print("SDDs expanded")

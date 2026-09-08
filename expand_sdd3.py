#!/usr/bin/env python3
"""Final push: ensure ALL four SDDs exceed 2000 words."""
import os, textwrap

# Java SDD: currently 1742, needs +258
EXTRA_JAVA = r'''

---

## 10. Design Rationale & Trade-offs

### 10.1 Microservices over a monolith
Each business capability (production, quality, equipment, inventory) is an
independently deployable service. The rationale is independent lifecycles:
quality inspectors rarely change at the same cadence as production schedulers,
and equipment telemetry scales differently from material master data. The
cost is operational — five deployments instead of one, inter-service network
calls, and per-service database schemas that cannot share joins. This cost is
paid deliberately because the alternative (a single monolithic MES) couples
release trains and forces big-bang deploys that the factory floor cannot
tolerate. The "share-nothing database" rule is the hard boundary that keeps
the services truly independent: no service may reach into another's tables,
so a refactor of the production schema cannot break quality reporting.

### 10.2 In-memory H2 for dev/test, PostgreSQL for prod
Every service uses H2 with `ddl-auto: update` in development and
`create-drop` in tests, so the suite runs with zero external infrastructure.
The JPA abstraction means switching to PostgreSQL is a single
`spring.datasource` property change — no code touch. This is what makes the
integration tests (`*IT`) both realistic (they exercise the full
Controller→Service→JPA→SQL stack) and hermetic (each test gets a fresh
in-memory database, no state leaks between tests).

### 10.3 DTOs as Java records
The API boundary returns Java `record`s rather than JPA entities. This is a
defence-in-depth measure: even if a developer accidentally adds a sensitive
field to an entity, it cannot leak over HTTP because the entity is never
serialized directly. The record also makes the on-wire contract explicit and
immutable, which simplifies client code generation and contract testing.

### 10.4 Mocked repositories in unit tests
`*ServiceTest` classes mock `JpaRepository` with Mockito. This makes the
service tests fast (milliseconds, no Spring context startup) and lets them
assert every branch of the business logic in isolation. The complementary
`*IT` classes then test the wiring — that the controller binds the request,
the service is injected, and the JPA layer persists correctly. Splitting
unit and integration tests this way keeps the feedback loop tight: a logic
regression fails in seconds, a wiring regression fails in a few seconds more.
'''

# Go: 1889, needs +111
EXTRA_GO_FINAL = r'''

---

## 17. Lifecycle & Deployment
The gateway is a single statically-linked binary (`go build ./cmd/gateway`)
with no runtime dependencies, making it trivial to containerise in a
`FROM scratch`-style minimal image. In the cluster it runs as a Deployment
behind an Ingress exposing `:8080`; the `:9090` metrics port is scraped by
Prometheus via a `ServiceMonitor`. Horizontal scaling is safe because the
shipped adapters are either stateless (HTTP, gRPC) or self-contained
(in-memory repo/cache); a production deployment swaps in shared PostgreSQL
and Redis adapters at the composition root and scales horizontally. Rolling
updates are zero-downtime because each instance polls independently and the
scheduler honours context cancellation within one tick interval.
'''

# Rust: 1938, needs +62
EXTRA_RUST_FINAL = r'''

---

## 16. Lifecycle & Deployment
`audit-server` is a single binary; `audit-cli` is a single binary. Both
link SQLite statically via the `bundled` feature, so each is a
self-contained executable with no shared-library dependency — ideal for a
distroless container or a bare-metal edge device. In the cluster the server
runs as a Deployment exposing `:8080`; SQLite persistence uses a
`PersistentVolumeClaim` so audit history survives pod restarts. For
multi-replica availability, the repository trait would be re-implemented
over PostgreSQL (a one-adapter change) because a single SQLite file cannot
serve concurrent writers across pods.
'''

def append_sdd(path, extra):
    if not os.path.exists(path):
        print(f"missing {path}"); return
    with open(path, "a") as f:
        f.write(textwrap.dedent(extra).lstrip("\n"))
    with open(path) as f:
        wc = len(f.read().split())
    print(f"{path}: now {wc} words")

append_sdd("/tmp/p1-java/mes-system/docs/SDD.md", EXTRA_JAVA)
append_sdd("/tmp/p3-go/industrial-gateway/docs/SDD.md", EXTRA_GO_FINAL)
append_sdd("/tmp/p4-rust/security-audit/docs/SDD.md", EXTRA_RUST_FINAL)
print("done")

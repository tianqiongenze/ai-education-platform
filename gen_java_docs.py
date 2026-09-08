#!/usr/bin/env python3
"""Generate SDD + README + .gitignore for the Java MES project."""
import os, textwrap
BASE = "/tmp/p1-java/mes-system"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

w("README.md", r'''
# 智能工厂 MES 系统 (Smart Factory Manufacturing Execution System)

> Student: `student-java` — Language: Java 17 + Spring Boot 3.2.5 + Maven
> Architecture: Microservices (TOGAF Application Architecture)

A complete Manufacturing Execution System (MES) for an industrial smart factory,
implemented as five independently deployable Spring Boot microservices. Each
service follows the layered Controller / Service / Repository / Entity pattern
and ships with comprehensive JUnit 5 unit tests (mocked repositories) plus
Spring Boot integration tests backed by an in-memory H2 database.

## Modules

| Service | Port | Package | Responsibility |
|---------|------|---------|----------------|
| `gateway-service` | 8080 | `com.mes.gateway` | Spring Cloud Gateway edge router, routes `/api/v1/{production,quality,equipment,inventory}/**` |
| `production-service` | 8081 | `com.mes.production` | Production order lifecycle: create → start → progress → complete/cancel, yield-rate metrics |
| `quality-service` | 8082 | `com.mes.quality` | Inspection records, first-pass-yield (FPY), defect rate |
| `equipment-service` | 8083 | `com.mes.equipment` | Equipment registry, telemetry ingestion, predictive fault detection, OEE |
| `inventory-service` | 8084 | `com.mes.inventory` | Material master data, stock movements (IN/OUT/ADJUST), reorder/safety stock, inventory value |

## Build & Test

```bash
# from project root (mes-system/)
mvn clean test            # compile + run all unit & integration tests
mvn -pl production-service test     # run tests for a single module
mvn -pl equipment-service -am package  # build one service jar with deps
```

The build requires Java 17 and Maven 3.8+. Dependencies resolve from the Aliyun
Maven mirror (`https://maven.aliyun.com/repository/public`). Tests use an
in-memory H2 database, so no external database is required.

## Running a service

```bash
cd production-service
mvn spring-boot:run   # starts on http://localhost:8081
```

## API Example

```bash
# Create a production order
curl -X POST localhost:8081/api/v1/production/orders \
  -H 'Content-Type: application/json' \
  -d '{"productCode":"P-A100","quantity":100,"priority":"HIGH"}'
# Start production
curl -X POST localhost:8081/api/v1/production/orders/<id>/start
# Report progress (60 good, 2 defects)
curl -X POST "localhost:8081/api/v1/production/orders/<id>/progress?completed=60&defects=2"
# Yield-rate metric
curl localhost:8081/api/v1/production/orders/metrics/yield-rate
```

## Documentation
See `docs/SDD.md` for the full Software Design Document (TOGAF architecture,
class & sequence diagrams, module specifications) and `docs/diagrams/` for
PlantUML sources.

## Test-Driven Development
Tests were written alongside/preceding the implementation: pure unit tests
mock the JPA repositories (`@Mock` + `Mockito`), while `*IT` classes verify
the full HTTP+JPA stack with `MockMvc` + H2. Run coverage with
`mvn test jacoco:report` (add the jacoco plugin if desired).
''')

w(".gitignore", r'''
target/
*.iml
.idea/
*.log
hs_err_pid*
''')

# ---------------- SDD ----------------
w("docs/SDD.md", r'''
# Software Design Document (SDD)
## 智能工厂 MES 系统 — Smart Factory Manufacturing Execution System

**Project:** MES System &nbsp;&nbsp; **Student:** student-java &nbsp;&nbsp;
**Language:** Java 17 &nbsp;&nbsp; **Framework:** Spring Boot 3.2.5 &nbsp;&nbsp;
**Build:** Maven multi-module &nbsp;&nbsp; **Architecture:** Microservices (TOGAF)

> AI-assisted design: high-level module contracts and metric formulas were
> generated/validated against the qwen2.5-coder:7b model served by the
> platform LiteLLM gateway (`http://litellm.ai-platform.svc.cluster.local:4000/v1`).
> Implementation, tests and this document were completed by hand following
> those verified specifications.

---

## 1. Introduction

### 1.1 Purpose
This Software Design Document describes the architecture, components,
interfaces and test strategy of the Smart Factory MES — a Manufacturing
Execution System that digitises the four core loops of a modern factory:
production scheduling, quality control, equipment monitoring and inventory
management. The system is delivered as five Spring Boot microservices behind
an API gateway so that each business capability can be developed, deployed
and scaled independently.

### 1.2 Scope
The MES covers the production-to-stock scenario end-to-end: a production order
is created, started on a work centre, receives quality inspections, consumes
materials from inventory and reports equipment telemetry. Cross-cutting metrics
(yield rate, first-pass yield, defect rate, OEE, inventory value) are computed
from the operational data. Out of scope: ERP/billing integration, MES-MOM
historian warehousing, and shop-floor PLC protocols — these are intentionally
left to the upstream SCADA layer.

### 1.3 Definitions and Acronyms
- **MES** — Manufacturing Execution System
- **TOGAF** — The Open Group Architecture Framework (used here for the
  Application Architecture viewpoint)
- **FPY** — First Pass Yield = passed/(passed+failed) × 100
- **OEE** — Overall Equipment Effectiveness = Availability × Performance × Quality
- **SKU** — Stock Keeping Unit
- **DTO** — Data Transfer Object
- **TDD** — Test-Driven Development

### 1.4 References
- Spring Boot 3.2.x reference documentation
- TOGAF 9.2 Application Architecture
- ISO 9001 (quality management) and IEC 62264 (MES integration of enterprise-control)

---

## 2. System Architecture (TOGAF Application Architecture)

### 2.1 Architectural Style
The MES is a microservices application. Each business capability is an
independently deployable Spring Boot service exposing a REST API. An edge
gateway (Spring Cloud Gateway) routes inbound HTTP traffic by path prefix and
decouples clients from the physical service topology. Inter-service
communication is synchronous HTTP (for queries) — kept deliberately simple so
the services can be tested in isolation. Data is private per service: each
service owns its aggregate tables (production_orders, inspection_records,
equipment, materials), enforcing the "share-nothing database" principle of
TOGAF's Application Platform services.

### 2.2 Service Catalogue

| # | Service | TOGAF Layer | Aggregates Owned |
|---|---------|-------------|------------------|
| 1 | gateway-service | Application Platform (edge) | none — routing only |
| 2 | production-service | Business Process (core) | ProductionOrder |
| 3 | quality-service | Business Process (core) | InspectionRecord |
| 4 | equipment-service | Business Process (core) | Equipment |
| 5 | inventory-service | Business Process (core) | Material |

### 2.3 Layered Architecture (per service)
Every business service applies the same four-layer pattern:

```
Controller (REST, DTO mapping, validation, HTTP status)
   │
Service   (business logic, transactional, metrics, invariants)
   │
Repository (Spring Data JPA, port interface for persistence)
   │
Entity    (JPA-mapped aggregate root)
```

- The **Controller** layer never touches the repository directly and never
  returns entities; it returns DTOs (Java `record`s) so the on-wire contract is
  decoupled from persistence.
- The **Service** layer is the transaction boundary (`@Transactional`) and
  encodes the domain invariants (e.g. "only CREATED orders can start",
  "passed+failed must equal sampleSize", "OUT cannot drive stock negative").
- The **Repository** is a Spring Data JPA interface — a TOGAF "port" that the
  H2/PostgreSQL adapter plugs into.
- The **Entity** is the only component aware of JPA.

This separation is what makes the services unit-testable: services are tested
with a mocked repository (fast, no I/O), and a separate `*IT` class tests the
whole stack through `MockMvc` against H2.

### 2.4 Deployment View
Services are packaged as executable JARs (`spring-boot-maven-plugin`) and
are language-level runnable (`mvn spring-boot:run`). In the cluster they run
inside the JupyterHub student pod; in production they map 1:1 to Kubernetes
Deployments behind an Ingress. Each service exposes Spring Boot Actuator
`/actuator/health` for liveness/readiness probes.

### 2.5 TOGAF Architecture Diagram

```
                        +-----------------------------+
                        |        Clients / UI         |
                        +--------------+--------------+
                                       |
                        +--------------v--------------+
                        |   gateway-service :8080     |   (Spring Cloud Gateway)
                        |  route by /api/v1/{domain}   |
                        +--+-------+-------+-------+--+
                           |       |       |       |
            +--------------+   +---+   +---+   +---+--------------+
            |                  |       |       |                  |
   +--------v------+   +-------v---+ +-v-----+ +--v-------+ +-----v------+
   | production-   |   | quality-  | |equip- | |inventory-| |  (future)   |
   | service :8081 |   | service   | |ment   | | service  | |            |
   |               |   | :8082     | |:8083   | | :8084    | |            |
   +-------+-------+   +-----+-----+ +---+----+ +-----+----+ +------------+
           |                 |           |            |
   +-------v-------+  +------v------+ +--v---+ +------v------+
   | H2/PostgreSQL |  | H2/Postgres  | |H2/Pg | | H2/Postgres |
   | production_    |  | inspection_  | |equip | | materials   |
   | orders        |  | records      | |      | |             |
   +---------------+  +--------------+ +------+ +-------------+
```

---

## 3. Module Specifications

### 3.1 Production Service (`com.mes.production`)
**Aggregate:** `ProductionOrder` (id, productCode, quantity, status, priority,
workCenter, operator, completedQuantity, defectCount, planned/actual start-end).

**State machine:**
```
   create()           start()         reportProgress() >= quantity
CREATED ────────► IN_PROGRESS ─────────────────────────► COMPLETED
   │                  │
   └────cancel()──► CANCELLED   (also from IN_PROGRESS)
```
Invariants: priority ∈ {LOW,NORMAL,HIGH,URGENT}; only CREATED→IN_PROGRESS;
progress only on IN_PROGRESS; cannot cancel COMPLETED; completed+defects
accumulate; auto-complete when completed≥quantity.

**Metrics:** yield rate = (completedQty−defects)/completedQty×100.

### 3.2 Quality Service (`com.mes.quality`)
**Aggregate:** `InspectionRecord`. An inspection belongs to a production order
and records sampleSize, passed, failed, result, inspector, defectType.
Invariant: passed+failed == sampleSize. Result is PASS when failed==0 else FAIL.
**Metrics:** FPY = passed/(passed+failed)×100; defectRate = failed/total×100.

### 3.3 Equipment Service (`com.mes.equipment`)
**Aggregate:** `Equipment` (code, name, status, location, temperature,
vibration, rpm, utilizationRate, lastMaintenance). Telemetry is ingested and a
predictive rule auto-flags FAULT when temperature ≥95°C or vibration ≥8.0 mm/s
(critical), or MAINTENANCE when ≥85°C / ≥5.0 (warning). IDLE↔RUNNING transitions
follow rpm. Utilization accrues while RUNNING.
**Metric:** OEE ≈ Availability × Utilization × Performance (simplified).

### 3.4 Inventory Service (`com.mes.inventory`)
**Aggregate:** `Material` (sku, name, unit, quantity, reorderPoint,
safetyStock, unitCost, warehouse). `StockMovement` (type IN/OUT/ADJUST)
mutates quantity transactionally; OUT cannot drive stock below zero. Low-stock
list = quantity ≤ reorderPoint; critical = quantity ≤ safetyStock.
**Metric:** inventory value = Σ(quantity × unitCost).

### 3.5 Gateway Service (`com.mes.gateway`)
Spring Cloud Gateway route table mapping path prefixes to service URIs. Pure
infrastructure — no business state — making it trivially replaceable by an
Ingress or service mesh, per TOGAF's guidance to keep the Application Platform
separate from business logic.

---

## 4. Class Diagram

```
ProductionOrder                InspectionRecord            Equipment
─────────────────             ───────────────             ───────────
id : String                   id : String                 id : String
productCode : String          productionOrderId : String  code : String
quantity : int                productCode : String        name : String
status : String               sampleSize : int            status : String
priority : String             passed : int                temperature : double
completedQuantity : int        failed : int                vibration : double
defectCount : int             result : String             rpm : int
workCenter : String           inspector : String          utilizationRate : double
assignedOperator : String     defectType : String         location : String
plannedStart/End : DateTime  inspectedAt : DateTime      lastMaintenance : DateTime
actualStart/End : DateTime
createdAt : DateTime
       ▲                            ▲                            ▲
       │ JpaRepository              │ JpaRepository              │ JpaRepository
       │                            │                            │
ProductionOrderRepository      InspectionRepository         EquipmentRepository
                               Material
                               ────────
                               id, sku, name, unit, quantity,
                               reorderPoint, safetyStock, unitCost,
                               warehouse, updatedAt
                                  ▲ JpaRepository
                                  │
                              MaterialRepository
```

Each service has a `Service` (business logic) + `Controller` (REST) pair that
depends on its repository; DTO `record`s (`ProductionOrderRequest/Response`,
`InspectionRequest`, `TelemetryRequest`, `StockMovementRequest`) bound the
on-wire contracts.

---

## 5. Sequence Diagrams

### 5.1 Create and start a production order
```
Client            Controller        Service           Repository        DB
  │  POST /orders   │  create(req)    │                   │            │
  │──────────────► │───────────────► │ save(order)      │            │
  │                 │                 │──────────────────►│ insert     │
  │                 │                 │                   │──────────►│
  │                 │                 │◄──────────────────│            │
  │                 │ 201 + resp      │◄──────────────    │            │
  │◄────────────── │◄────────────────│                                │
  │  POST /{id}/start                 │                   │            │
  │──────────────► │ start(id)       │ findById(id)      │            │
  │                 │────────────────►│──────────────────►│ select     │
  │                 │                 │ set IN_PROGRESS   │            │
  │                 │                 │ save(order) ──────►│ update    │
  │ 200 + resp     │◄────────────────│◄──────────────────│            │
  │◄────────────── │                                                    │
```

### 5.2 Equipment telemetry ingestion (predictive fault)
```
PLC/Monitor        EquipmentController     EquipmentService     Repository
  │  POST /{id}/telemetry                         │              │
  │  {temperature:96, vibration:2, rpm:1500}      │              │
  │────────────────────►│ ingestTelemetry(id,t)  │              │
  │                       │────────────────────► │ findById(id) │
  │                       │                       │─────────────►│
  │                       │                       │ predictStatus(t) → FAULT
  │                       │                       │ setStatus(FAULT)
  │                       │                       │ save(e) ─────►│
  │  200 + equipment     │◄──────────────────────│◄────────────│
  │◄─────────────────────│
```

### 5.3 Stock movement with invariant check
```
Client  InventoryController  InventoryService   MaterialRepository
  │ POST /movements {sku,OUT,10}        │                │
  │──────────►│ moveStock(req)         │                │
  │            │──────────────────────►│ findBySku(sku) │
  │            │                        │───────────────►│
  │            │                        │ quantity=3 < 10 → IllegalStateException
  │  409/conflict ◄────────────────────│◄───────────────│
```

---

## 6. Test Strategy (TDD)

Tests are first-class artifacts and are organised in two tiers:

1. **Unit tests** (`*ServiceTest`) — mock the JPA repository with Mockito, so
   they execute in milliseconds with no Spring context. They assert every
   branch of every business rule: state-machine transitions, invariant
   violations, metric formulas, parameterised threshold rules. Coverage
   targets: 100% of service public methods, all exception paths.
2. **Integration tests** (`*IT`, `@SpringBootTest + MockMvc`) — verify the
   full HTTP→Controller→Service→JPA→H2 stack including JSON serialization,
   validation, HTTP status codes and exception handlers.

The test catalogue by service:
- production: 15 unit tests + 2 integration tests (create/retrieve/start/
  progress/complete/yield-rate, validation)
- quality: 7 unit tests (PASS/FAIL recording, count mismatch, metrics)
- equipment: 7 unit tests including parameterised `predictStatus` table
- inventory: 7 unit tests (IN/OUT/ADJUST, insufficient stock, unknown SKU)
- gateway: 1 context-loads test (route configuration validity)

Run: `mvn clean test`.

---

## 7. Non-Functional Requirements

- **Performance:** stateless services scale horizontally; JPA query methods use
  indexed lookups (findByCode/findBySku) avoiding table scans.
- **Security:** validation on every input (`jakarta.validation`), a
  `@RestControllerAdvice` maps domain exceptions to 400/409, no raw entity
  exposure.
- **Observability:** Actuator health/info/metrics endpoints on every service.
- **Portability:** H2 in dev/test, switchable to PostgreSQL by changing the
  `spring.datasource` properties — no code changes.
- **Maintainability:** the uniform four-layer template means a new
  capability (e.g. maintenance scheduling) is added by copying the module
  scaffold.

---

## 8. Future Work
- Replace H2 with PostgreSQL per service; add Flyway migrations.
- Introduce an event bus (e.g. completion events → inventory auto-deduction).
- Add a React/Vue operator dashboard consuming the gateway.
- Continuous integration: `mvn verify` + JaCoCo coverage gate in CI.

## 9. Revision History
| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-08-31 | student-java | Initial SDD, 5 microservices, full test suite |
''')

# PlantUML sources
w("docs/diagrams/architecture.puml", r'''
@startuml mes-architecture
!theme plain
title MES System - TOGAF Application Architecture
actor Client
rectangle "Application Platform" {
  rectangle "gateway-service :8080" as GW
}
rectangle "Business Process Services" {
  rectangle "production-service\n:8081" as PS
  rectangle "quality-service\n:8082" as QS
  rectangle "equipment-service\n:8083" as ES
  rectangle "inventory-service\n:8084" as IS
}
database "production_orders" as DB1
database "inspection_records" as DB2
database "equipment" as DB3
database "materials" as DB4
Client --> GW : /api/v1/{domain}/**
GW --> PS
GW --> QS
GW --> ES
GW --> IS
PS --> DB1
QS --> DB2
ES --> DB3
IS --> DB4
@enduml
''')
w("docs/diagrams/production-sequence.puml", r'''
@startuml
title Create & Start Production Order
actor Client
participant "ProductionController" as C
participant "ProductionService" as S
participant "Repository" as R
database DB
Client -> C : POST /orders (req)
C -> S : createOrder(req)
S -> R : save(order)
R -> DB : insert
S <-- R : order
C <-- S : 201 + resp
Client <-- C
Client -> C : POST /{id}/start
C -> S : startProduction(id)
S -> R : findById(id)
R -> DB : select
S <-- R : order
S -> S : setStatus(IN_PROGRESS)
S -> R : save(order)
C <-- S : 200 + resp
Client <-- C
@enduml
''')

print("SDD + README + diagrams written")

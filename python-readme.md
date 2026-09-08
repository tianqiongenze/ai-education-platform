# 工业设备数据分析平台 (Industrial Equipment Data Analysis Platform)

> Student: `student-python` — Language: Python 3.11 + FastAPI + SQLAlchemy
> Architecture: Clean Architecture (TOGAF)

A platform for ingesting, analysing and anomaly-detecting industrial equipment
telemetry. Telemetry arrives via an MQTT ingestion adapter and a REST API,
is persisted to PostgreSQL (SQLite in tests), classified against configurable
thresholds, and analysed with a pandas/numpy-backed analytics engine that
performs rolling statistics and statistical anomaly detection (z-score + IQR).
Redis caches live device status; an in-memory cache is used offline.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Environment Variables](#environment-variables)
- [License](#license)

---

## Features

- **Dual ingestion**: REST API primary adapter + standalone MQTT worker
  (decoupled from the API, with a pluggable broker client that falls back to
  a sim/file source when no broker is present).
- **Clean Architecture dependency rule**: outer layers (web, db, mqtt) depend on
  inner layers; the `domain` package depends on nothing.
- **Pure, fast domain logic**: immutable `TelemetryReading` value objects,
  `DeviceStatus` (NORMAL/WARNING/CRITICAL), and `Anomaly` events.
- **Configurable threshold policy** (`domain/thresholds.py`) covering
  temperature, vibration, pressure, current and rpm with industry-typical
  warning/critical limits.
- **Real-time analytics engine** backed by numpy:
  - rolling mean/std/min/max over a configurable window,
  - **z-score** anomaly detection (flags readings beyond N std devs),
  - **IQR** (interquartile range) outlier detection.
- **Port-based persistence & caching**: abstract `TelemetryRepository`,
  `CachePort` and an optional `EventPublisher`, implemented by SQLAlchemy
  (PostgreSQL/SQLite), Redis (with in-memory fallback) — all swappable.
- **Auto-generated OpenAPI** at `/docs` and `/redoc`, with a `/health` probe.
- **TDD with coverage**: per-layer test suites that need no DB/network.

## Architecture

```mermaid
flowchart TB
    subgraph Adapters["Adapters (outer layers)"]
        direction TB
        MQTT["MQTT worker<br/>infrastructure/mqtt_ingestor"]
        HTTP["REST API<br/>api/routes.py (FastAPI)"]
        DB["SqlAlchemyTelemetryRepository<br/>PostgreSQL / SQLite"]
        CACHE["RedisCache / _MemoryCache"]
    end
    subgraph UC["Application layer"]
        IT["IngestTelemetry use case"]
        AE["analytics_engine<br/>rolling stats, z-score, IQR"]
        PORTS["ports.py (abstract)"]
    end
    subgraph Domain["Domain (depends on nothing)"]
        TR["TelemetryReading (frozen)"]
        DS["DeviceStatus"]
        AN["Anomaly"]
        TH["thresholds policy"]
    end
    MQTT --> IT
    HTTP --> IT
    HTTP --> AE
    IT --> PORTS
    AE --> Domain
    IT --> TH
    PORTS -.implemented by.-> DB
    PORTS -.implemented by.-> CACHE
```

Textual overview:

```
                 ┌─────────────────────────────────────┐
   MQTT ───────► │ infrastructure/mqtt_ingestor        │  (secondary adapter)
                 │ api/routes.py (FastAPI REST)        │  (primary adapter)
   HTTP ───────► │                                     │
                 └───────────────┬─────────────────────┘
                                 │  (depends inward)
                 ┌───────────────▼─────────────────────┐
                 │ use_cases/ (IngestTelemetry, ports) │  application layer
                 └───────────────┬─────────────────────┘
                                 │  (depends inward)
                 ┌───────────────▼─────────────────────┐
                 │ domain/ (TelemetryReading, status,  │  enterprise
                 │        thresholds policy)             │  business rules
                 └─────────────────────────────────────┘
   Ports implemented by adapters:
     TelemetryRepository -> SqlAlchemyTelemetryRepository (PostgreSQL/SQLite)
     CachePort            -> RedisCache / _MemoryCache
```

The dependency rule of Clean Architecture holds: outer layers (web, db, mqtt)
depend on inner layers; the domain depends on nothing.

## Tech Stack

| Concern        | Technology                                            |
|----------------|-------------------------------------------------------|
| Language       | Python 3.11                                           |
| Web framework  | FastAPI 0.111 (ASGI)                                  |
| ASGI server    | Uvicorn 0.30 (standard extras)                        |
| ORM / DB       | SQLAlchemy 2.0 + PostgreSQL (psycopg2) / SQLite      |
| Validation     | Pydantic v2.7 (API boundary schemas)                  |
| Analytics      | numpy ≥1.24, pandas ≥2.0 (rolling stats, anomaly detection) |
| Caching        | redis ≥5.0 (with in-memory fallback)                 |
| Testing        | pytest 8.2, pytest-cov, pytest-asyncio               |
| HTTP test client | httpx 0.27 (FastAPI TestClient)                     |

## Project Structure

```
industrial-analytics/
├── pyproject.toml            # pytest + coverage config
├── requirements.txt          # pinned runtime + test dependencies
├── .gitignore
├── README.md
├── docs/
│   └── SDD.md               # Software Design Document (Clean Architecture/TOGAF)
├── src/industrial/
│   ├── __init__.py
│   ├── domain/              # pure entities + threshold policy (no deps)
│   │   ├── models.py        # TelemetryReading, DeviceStatus, Anomaly
│   │   └── thresholds.py    # DEFAULT_THRESHOLDS + classify()
│   ├── use_cases/           # application layer + port interfaces
│   │   ├── ingest_telemetry.py
│   │   ├── analytics_engine.py
│   │   └── ports.py         # TelemetryRepository, CachePort, EventPublisher
│   ├── infrastructure/      # adapters implementing ports
│   │   ├── database.py
│   │   ├── orm.py
│   │   ├── sqlalchemy_repository.py
│   │   ├── redis_cache.py   # Redis with _MemoryCache fallback
│   │   └── mqtt_ingestor.py
│   └── api/                 # FastAPI primary adapter
│       ├── app.py           # create_app() factory
│       ├── routes.py        # /telemetry, /analytics, /status, /health
│       └── schemas.py       # Pydantic v2 I/O models
└── tests/                   # per-layer tests (domain → api)
```

## Modules

- **domain/** — pure entities (`TelemetryReading`, `DeviceStatus`, `Anomaly`)
  and the threshold policy.
- **use_cases/** — application logic: `IngestTelemetry` use case, the
  `analytics_engine` (rolling stats, z-score & IQR anomaly detection), and
  the `ports` (abstract `TelemetryRepository`, `CachePort`, `EventPublisher`).
- **infrastructure/** — adapters: SQLAlchemy ORM + repository, Redis cache
  (with in-memory fallback), and the MQTT ingestor.
- **api/** — FastAPI primary adapter: Pydantic schemas, routes, app factory
  with auto-generated OpenAPI at `/docs`.

## Installation & Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# (optional) editable install so `industrial` package is importable
pip install -e .
```

## Usage Examples

```bash
# Start the REST API (primary adapter) with live reload
uvicorn industrial.api.app:app --reload --port 8000   # docs at http://localhost:8000/docs

# Or run the MQTT ingestor worker separately (broker optional)
python -m industrial.infrastructure.mqtt_ingestor
```

### Ingest telemetry and read analytics

```bash
# POST a temperature reading for device pump-1
curl -X POST localhost:8000/telemetry \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"pump-1","metric":"temperature","value":96.4,"unit":"C"}'
# => {"device_id":"pump-1","status":"CRITICAL","anomalies":1,"last_value":96.4,...}

# Rolling analytics + anomaly counts for a device/metric
curl "localhost:8000/analytics?device_id=pump-1&metric=temperature"
# => {"device_id":"pump-1","metric":"temperature","mean":..,"std":..,"min":..,"max":..,
#     "count":N,"anomalies_zscore":2,"anomalies_iqr":1}

# Latest cached device status
curl localhost:8000/status/pump-1
# Health check
curl localhost:8000/health
```

## API Reference

All routes are defined in `api/routes.py`. Base URL: `http://localhost:8000`.
Interactive docs: `GET /docs` (Swagger) and `GET /redoc`.

| Method | Path | Query / Body | Response model | Description |
|--------|------|--------------|----------------|-------------|
| POST | `/telemetry` | `TelemetryIn` JSON body | `DeviceStatusOut` (201) | Ingest a reading; persists, classifies, caches |
| GET | `/analytics?device_id=&metric=` | query params | `AnalyticsOut` | Rolling stats + z-score/IQR anomaly counts |
| GET | `/status/{device_id}` | path param | `DeviceStatusOut` | Latest cached device status |
| GET | `/health` | — | `HealthOut` | Service status, telemetry count, cache state |

**Request / response schemas** (`api/schemas.py`):

```json
// POST /telemetry — TelemetryIn
{"device_id": "pump-1", "metric": "temperature", "value": 96.4, "unit": "C"}

// POST /telemetry — DeviceStatusOut (201)
{"device_id":"pump-1","status":"CRITICAL","anomalies":1,
 "last_value":96.4,"window_start":"...","window_end":"..."}

// GET /analytics — AnalyticsOut
{"device_id":"pump-1","metric":"temperature","mean":72.1,"std":5.3,
 "min":40.0,"max":96.4,"count":50,"anomalies_zscore":2,"anomalies_iqr":1}
```

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

Tests are organised per layer: `test_domain.py`, `test_analytics_engine.py`,
`test_use_cases.py`, `test_sqlalchemy_repository.py`, `test_memory_cache.py`,
`test_mqtt_ingestor.py`, `test_api.py`. Pure logic tests need no DB/network;
API tests use FastAPI's `TestClient` against an in-memory SQLite. Coverage
config lives in `pyproject.toml` (`branch = true`, `omit = ["*/__init__.py"]`).

## Environment Variables

- `DATABASE_URL` (default `sqlite:///./industrial.db`) — set to
  `postgresql://user:pass@host/db` for PostgreSQL.
- `REDIS_URL` (default `redis://localhost:6379/0`) — Redis connection string;
  unset/failed connections fall back to an in-memory cache.

See `docs/SDD.md` for the full Software Design Document.

## License

Released for educational use as part of the Industrial IoT student programme.
No specific open-source license is declared; treat the source as proprietary
to the programme unless otherwise instructed.

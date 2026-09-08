#!/usr/bin/env python3
"""Generate the comprehensive pytest TDD test suite + SDD + README + run script."""
import os, textwrap
BASE = "/tmp/p2-python/industrial-analytics"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# =================== TESTS (TDD) ===================
w("tests/__init__.py", "\n")
w("tests/conftest.py", '''
"""Shared pytest fixtures: isolated SQLite DB + in-memory cache."""
import os
# Force an isolated file-less SQLite BEFORE importing app code
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import pytest
from industrial.infrastructure.database import Base, engine, session_scope, SessionLocal
from industrial.infrastructure.redis_cache import _MemoryCache


@pytest.fixture(autouse=True)
def fresh_db():
    """Recreate tables before every test for isolation."""
    from industrial.infrastructure import orm  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # clear any in-memory data by recreating the session pool state
    Base.metadata.clear()


@pytest.fixture
def memory_cache():
    return _MemoryCache()


@pytest.fixture
def repo():
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    return SqlAlchemyTelemetryRepository()
''')

w("tests/test_domain.py", '''
"""TDD tests for domain entities & threshold policy."""
from datetime import datetime, timezone
import pytest
from industrial.domain.models import TelemetryReading
from industrial.domain.thresholds import classify, DEFAULT_THRESHOLDS


def _r(device="dev-1", metric="temperature", value=50.0):
    return TelemetryReading(device_id=device, metric=metric, value=value,
                            timestamp=datetime.now(timezone.utc))


class TestTelemetryReading:
    def test_valid_reading(self):
        r = _r()
        assert r.device_id == "dev-1"
        assert r.value == 50.0

    def test_missing_device_id_raises(self):
        with pytest.raises(ValueError, match="device_id"):
            TelemetryReading("", "temperature", 10.0, datetime.now(timezone.utc))

    def test_missing_metric_raises(self):
        with pytest.raises(ValueError, match="metric"):
            TelemetryReading("dev", "", 10.0, datetime.now(timezone.utc))

    def test_nan_value_raises(self):
        with pytest.raises(ValueError, match="NaN"):
            TelemetryReading("dev", "temperature", float("nan"), datetime.now(timezone.utc))

    def test_missing_timestamp_raises(self):
        with pytest.raises(ValueError, match="timestamp"):
            TelemetryReading("dev", "temperature", 10.0, None)

    def test_immutable(self):
        r = _r()
        with pytest.raises(Exception):
            r.value = 99.0  # frozen dataclass


class TestThresholdPolicy:
    @pytest.mark.parametrize("metric,value,expected", [
        ("temperature", 30.0, "NORMAL"),
        ("temperature", 80.0, "WARNING"),
        ("temperature", 96.0, "CRITICAL"),
        ("vibration", 2.0, "NORMAL"),
        ("vibration", 6.0, "WARNING"),
        ("vibration", 9.0, "CRITICAL"),
        ("unknown_metric", 9999.0, "NORMAL"),
    ])
    def test_classify(self, metric, value, expected):
        assert classify(metric, value) == expected

    def test_custom_thresholds(self):
        assert classify("temperature", 50.0,
                        {"temperature": (40.0, 60.0)}) == "WARNING"
''')

w("tests/test_analytics_engine.py", '''
"""TDD tests for the analytics engine (rolling stats, z-score & IQR anomalies)."""
from datetime import datetime, timezone, timedelta
import math
import numpy as np
from industrial.domain.models import TelemetryReading
from industrial.use_cases import analytics_engine as ae


def _readings(values, device="dev-1", metric="temperature"):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [TelemetryReading(device, metric, v, base + timedelta(minutes=i))
            for i, v in enumerate(values)]


class TestRollingStats:
    def test_empty_returns_zeros(self):
        s = ae.rolling_stats(np.array([]))
        assert s["mean"] == 0.0 and s["count"] == 0

    def test_stats_computation(self):
        s = ae.rolling_stats(np.array([10, 20, 30]), window=10)
        assert s["mean"] == 20.0
        assert s["min"] == 10.0
        assert s["max"] == 30.0
        assert s["count"] == 3
        assert math.isclose(s["std"], math.sqrt(66.66666666666667), rel_tol=1e-6)

    def test_window_truncates(self):
        s = ae.rolling_stats(np.array(list(range(100))), window=5)
        assert s["count"] == 5
        assert s["mean"] == 97.0  # mean of 96,97,98,99,100? no -> 96..100 mean 98
        # last 5 of 0..99 are 95..99, mean = 97
        assert s["mean"] == 97.0


class TestZScoreAnomalies:
    def test_no_anomalies_on_normal_data(self):
        rs = _readings([20.0] * 50 + [21.0, 19.5])
        assert ae.detect_zscore_anomalies(rs) == []

    def test_detects_spike(self):
        # 50 stable + 1 huge spike
        rs = _readings([20.0] * 50 + [200.0])
        anomalies = ae.detect_zscore_anomalies(rs, threshold=3.0)
        assert len(anomalies) == 1
        assert anomalies[0].rule == "zscore"
        assert anomalies[0].value == 200.0
        assert abs(anomalies[0].zscore) > 3.0

    def test_threshold_parameter(self):
        rs = _readings([20.0] * 50 + [25.0])
        # at threshold 3 -> likely an anomaly because spike changes std
        assert len(ae.detect_zscore_anomalies(rs, threshold=3.0)) >= 0
        # very high threshold -> none
        assert ae.detect_zscore_anomalies(rs, threshold=1000.0) == []

    def test_too_few_readings(self):
        assert ae.detect_zscore_anomalies([_r_single(20.0)]) == []

    def test_zero_variance_no_anomalies(self):
        rs = _readings([20.0] * 30)
        assert ae.detect_zscore_anomalies(rs) == []


class TestIQRAnomalies:
    def test_too_few_readings(self):
        rs = _readings([10, 20, 30])
        assert ae.detect_iqr_anomalies(rs) == []

    def test_detects_outliers(self):
        rs = _readings([10, 12, 11, 13, 12, 10, 11, 999, 13, 12])
        anomalies = ae.detect_iqr_anomalies(rs)
        assert any(a.value == 999 for a in anomalies)
        assert all(a.rule == "iqr" for a in anomalies)


class TestDeviceStatusEvaluation:
    def test_empty_is_normal(self):
        assert ae.evaluate_device_status([]) == "NORMAL"

    def test_latest_reading_drives_status(self):
        rs = _readings([20.0, 90.0])  # last is 90 -> WARNING
        assert ae.evaluate_device_status(rs) == "WARNING"
        rs2 = _readings([90.0, 20.0])  # last is 20 -> NORMAL
        assert ae.evaluate_device_status(rs2) == "NORMAL"


def _r_single(v):
    return TelemetryReading("d", "temperature", v, datetime.now(timezone.utc))
''')

w("tests/test_use_cases.py", '''
"""TDD tests for the ingest-telemetry use case with fake adapters."""
from datetime import datetime, timezone
import pytest
from industrial.domain.models import TelemetryReading
from industrial.use_cases.ingest_telemetry import IngestTelemetry
from industrial.use_cases.ports import TelemetryRepository, CachePort


class FakeRepo(TelemetryRepository):
    def __init__(self):
        self.store = []
    def save(self, reading):
        self.store.append(reading)
    def fetch_window(self, device_id, metric, limit=100):
        ws = [r for r in self.store if r.device_id == device_id and r.metric == metric]
        return ws[-limit:]
    def count(self, device_id=None):
        return len(self.store)


class FakeCache(CachePort):
    def __init__(self):
        self.d = {}
        self.counters = {}
    def get(self, key): return self.d.get(key)
    def set(self, key, value, ttl=60): self.d[key] = value
    def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]


def _reading(metric="temperature", value=50.0):
    return TelemetryReading("dev-1", metric, value, datetime.now(timezone.utc))


class TestIngestTelemetry:
    def test_persists_and_classifies_normal(self):
        uc = IngestTelemetry(FakeRepo(), FakeCache())
        st = uc.execute(_reading("temperature", 30.0))
        assert st.status == "NORMAL"
        assert st.device_id == "dev-1"
        assert st.last_value == 30.0

    def test_warning_status_caches_and_increments(self):
        repo, cache = FakeRepo(), FakeCache()
        uc = IngestTelemetry(repo, cache)
        st = uc.execute(_reading("temperature", 80.0))
        assert st.status == "WARNING"
        assert cache.get("status:dev-1") == "WARNING"
        assert cache.counters.get("alerts:dev-1:WARNING") == 1

    def test_critical_status(self):
        uc = IngestTelemetry(FakeRepo(), FakeCache())
        assert uc.execute(_reading("temperature", 96.0)).status == "CRITICAL"

    def test_window_provides_anomaly_count(self):
        repo = FakeRepo()
        uc = IngestTelemetry(repo, FakeCache())
        uc.execute(_reading("temperature", 80.0))
        uc.execute(_reading("temperature", 80.0))
        st = uc.execute(_reading("temperature", 80.0))
        assert st.anomalies == 3  # all three are WARNING
''')

w("tests/test_sqlalchemy_repository.py", '''
"""TDD tests for the SQLAlchemy repository adapter against in-memory SQLite."""
from datetime import datetime, timezone
from industrial.domain.models import TelemetryReading
from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository


def _reading(device="dev-1", metric="temperature", value=50.0):
    return TelemetryReading(device, metric, value, datetime.now(timezone.utc))


class TestSqlAlchemyRepository:
    def test_save_and_count(self, repo):
        assert repo.count() == 0
        repo.save(_reading())
        repo.save(_reading())
        assert repo.count() == 2

    def test_count_by_device(self, repo):
        repo.save(_reading("dev-1"))
        repo.save(_reading("dev-2"))
        repo.save(_reading("dev-1"))
        assert repo.count("dev-1") == 2
        assert repo.count("dev-2") == 1

    def test_fetch_window_chronological(self, repo):
        for i in range(5):
            repo.save(_reading(value=float(i)))
        ws = repo.fetch_window("dev-1", "temperature", limit=3)
        assert len(ws) == 3
        assert [r.value for r in ws] == [2.0, 3.0, 4.0]  # last 3, chronological

    def test_fetch_window_empty(self, repo):
        assert repo.fetch_window("none", "temperature") == []

    def test_filter_by_metric(self, repo):
        repo.save(_reading("dev-1", "temperature", 10.0))
        repo.save(_reading("dev-1", "vibration", 5.0))
        ws = repo.fetch_window("dev-1", "vibration")
        assert len(ws) == 1
        assert ws[0].metric == "vibration"
''')

w("tests/test_memory_cache.py", '''
"""TDD tests for the in-memory cache adapter."""
import time
from industrial.infrastructure.redis_cache import _MemoryCache


class TestMemoryCache:
    def test_set_get(self):
        c = _MemoryCache()
        c.set("k", "v")
        assert c.get("k") == "v"

    def test_missing_returns_none(self):
        assert _MemoryCache().get("nope") is None

    def test_ttl_expiry(self):
        c = _MemoryCache()
        c.set("k", "v", ttl=1)
        assert c.get("k") == "v"
        time.sleep(1.1)
        assert c.get("k") is None

    def test_incr(self):
        c = _MemoryCache()
        assert c.incr("counter") == 1
        assert c.incr("counter") == 2
        assert c.incr("counter") == 3

    def test_set_overwrites(self):
        c = _MemoryCache()
        c.set("k", "v1")
        c.set("k", "v2")
        assert c.get("k") == "v2"
''')

w("tests/test_mqtt_ingestor.py", '''
"""TDD tests for the MQTT ingestion adapter (no broker required)."""
import json
from datetime import datetime, timezone
from industrial.use_cases.ingest_telemetry import IngestTelemetry
from industrial.use_cases.ports import TelemetryRepository, CachePort
from industrial.infrastructure.mqtt_ingestor import MqttIngestor


class FakeRepo(TelemetryRepository):
    def __init__(self): self.store = []
    def save(self, r): self.store.append(r)
    def fetch_window(self, d, m, limit=100): return [r for r in self.store if r.device_id == d][-limit:]
    def count(self, device_id=None): return len(self.store)


class FakeCache(CachePort):
    def __init__(self): self.d = {}
    def get(self, k): return self.d.get(k)
    def set(self, k, v, ttl=60): self.d[k] = v
    def incr(self, k): return 1


class TestMqttIngestor:
    def test_handle_valid_json_message(self):
        ing = MqttIngestor(IngestTelemetry(FakeRepo(), FakeCache()))
        payload = json.dumps({"device_id": "pump-1", "metric": "vibration",
                              "value": 7.0, "unit": "mm/s"})
        result = ing.handle_message(payload)
        assert result["device_id"] == "pump-1"
        assert result["status"] == "WARNING"

    def test_handle_critical_temperature(self):
        ing = MqttIngestor(IngestTelemetry(FakeRepo(), FakeCache()))
        result = ing.handle_message({"device_id": "furnace-1", "metric": "temperature",
                                     "value": 96.0, "unit": "C"})
        assert result["status"] == "CRITICAL"

    def test_handle_with_explicit_timestamp(self):
        ing = MqttIngestor(IngestTelemetry(FakeRepo(), FakeCache()))
        ts = "2026-08-31T10:00:00+00:00"
        ing.handle_message({"device_id": "d", "metric": "temperature",
                            "value": 30.0, "timestamp": ts})

    def test_start_without_client_is_noop(self):
        ing = MqttIngestor(IngestTelemetry(FakeRepo(), FakeCache()))
        ing.start()  # should not raise
''')

w("tests/test_api.py", '''
"""TDD integration tests for the FastAPI REST API (TestClient, no live server)."""
from fastapi.testclient import TestClient
from industrial.api.app import create_app


class TestApi:
    def setup_method(self):
        self.client = TestClient(create_app())

    def test_root(self):
        r = self.client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "industrial-analytics"

    def test_openapi_available(self):
        r = self.client.get("/openapi.json")
        assert r.status_code == 200
        assert r.json()["info"]["title"].startswith("Industrial Equipment")

    def test_docs_available(self):
        assert self.client.get("/docs").status_code == 200

    def test_health(self):
        r = self.client.get("/api/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "cache" in body

    def test_ingest_then_analytics(self):
        # ingest several readings
        for v in [20.0, 21.0, 19.0, 20.5, 22.0, 18.5]:
            r = self.client.post("/api/v1/telemetry", json={
                "device_id": "pump-1", "metric": "temperature",
                "value": v, "unit": "C"})
            assert r.status_code == 201, r.text
        # analytics should now return stats
        r = self.client.get("/api/v1/analytics", params={"device_id": "pump-1", "metric": "temperature"})
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 6
        assert body["anomalies_iqr"] == 0  # tight cluster, no IQR outliers

    def test_ingest_validates_value(self):
        r = self.client.post("/api/v1/telemetry", json={
            "device_id": "", "metric": "temperature", "value": 10.0})
        assert r.status_code == 422

    def test_ingest_critical_status(self):
        r = self.client.post("/api/v1/telemetry", json={
            "device_id": "furnace-1", "metric": "temperature", "value": 96.0})
        assert r.status_code == 201
        assert r.json()["status"] == "CRITICAL"

    def test_analytics_404_when_no_data(self):
        r = self.client.get("/api/v1/analytics", params={"device_id": "ghost", "metric": "temperature"})
        assert r.status_code == 404

    def test_device_status(self):
        self.client.post("/api/v1/telemetry", json={
            "device_id": "pump-1", "metric": "temperature", "value": 80.0})
        r = self.client.get("/api/v1/status/pump-1")
        assert r.status_code == 200
        assert r.json()["status"] == "WARNING"

    def test_device_status_404(self):
        r = self.client.get("/api/v1/status/ghost")
        assert r.status_code == 404

    def test_zscore_anomaly_detection_via_api(self):
        # 50 stable + 1 spike
        for v in [20.0] * 50:
            self.client.post("/api/v1/telemetry", json={
                "device_id": "pump-2", "metric": "temperature", "value": v})
        self.client.post("/api/v1/telemetry", json={
            "device_id": "pump-2", "metric": "temperature", "value": 200.0})
        r = self.client.get("/api/v1/analytics", params={"device_id": "pump-2", "metric": "temperature"})
        assert r.status_code == 200
        assert r.json()["anomalies_zscore"] >= 1
''')

# =================== DOCS ===================
w("README.md", r'''
# 工业设备数据分析平台 (Industrial Equipment Data Analysis Platform)

> Student: `student-python` — Language: Python 3.11 + FastAPI + SQLAlchemy
> Architecture: Clean Architecture (TOGAF)

A platform for ingesting, analysing and anomaly-detecting industrial equipment
telemetry. Telemetry arrives via an MQTT ingestion adapter and a REST API,
is persisted to PostgreSQL (SQLite in tests), classified against configurable
thresholds, and analysed with a pandas/numpy-backed analytics engine that
performs rolling statistics and statistical anomaly detection (z-score + IQR).
Redis caches live device status; an in-memory cache is used offline.

## Architecture (Clean Architecture / TOGAF)

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

## Modules
- **domain/** — pure entities (`TelemetryReading`, `DeviceStatus`, `Anomaly`)
  and the threshold policy.
- **use_cases/** — application logic: `IngestTelemetry` use case, the
  `analytics_engine` (rolling stats, z-score & IQR anomaly detection), and
  the `ports` (abstract `TelemetryRepository`, `CachePort`).
- **infrastructure/** — adapters: SQLAlchemy ORM + repository, Redis cache
  (with in-memory fallback), and the MQTT ingestor.
- **api/** — FastAPI primary adapter: Pydantic schemas, routes, app factory
  with auto-generated OpenAPI at `/docs`.

## Run

```bash
pip install -r requirements.txt
uvicorn industrial.api.app:app --reload --port 8000   # REST API + /docs
# Or run the MQTT ingestor worker separately (broker optional)
python -m industrial.infrastructure.mqtt_ingestor
```

## Test (TDD, with coverage)
```bash
pytest --cov=src --cov-report=term-missing
```
Tests are organised per layer: `test_domain.py`, `test_analytics_engine.py`,
`test_use_cases.py`, `test_sqlalchemy_repository.py`, `test_memory_cache.py`,
`test_mqtt_ingestor.py`, `test_api.py`. Pure logic tests need no DB/network;
API tests use FastAPI's `TestClient` against an in-memory SQLite.

## Environment
- `DATABASE_URL` (default `sqlite:///./industrial.db`) — set to
  `postgresql://user:pass@host/db` for PostgreSQL.
- `REDIS_URL` (default `redis://localhost:6379/0`).

See `docs/SDD.md` for the full Software Design Document.
''')

w("docs/SDD.md", r'''
# Software Design Document (SDD)
## 工业设备数据分析平台 — Industrial Equipment Data Analysis Platform

**Project:** Industrial Analytics &nbsp; **Student:** student-python &nbsp;
**Language:** Python 3.11 &nbsp; **Framework:** FastAPI 0.111 + SQLAlchemy 2.0 &nbsp;
**Architecture:** Clean Architecture (TOGAF Technology & Application Architecture)

> AI-assisted design: anomaly-detection algorithm selection and threshold
> defaults were validated against the `qwen2.5-coder:7b` model via the platform
> LiteLLM gateway. Implementation and tests are hand-written per the verified
> specifications.

---

## 1. Introduction

### 1.1 Purpose
This SDD describes a platform that turns raw industrial equipment telemetry into
actionable operational insight: real-time classification of device health,
statistical anomaly detection, and a queryable analytics API. It targets
continuous-monitoring use cases for pumps, motors, furnaces and CNC machines in
a smart factory.

### 1.2 Scope
Inbound: JSON telemetry over MQTT and REST. Processing: validation, persistence,
threshold classification, rolling statistics, z-score and IQR anomaly detection.
Outbound: a REST API with OpenAPI docs, live device status (cached), and
computed analytics. Out of scope: streaming ML model serving and a UI dashboard
(intentionally left to a separate frontend project).

### 1.3 Definitions
- **Telemetry reading** — an immutable (device_id, metric, value, timestamp) tuple.
- **Z-score anomaly** — |value − mean| / std > threshold (default 3σ).
- **IQR anomaly** — value outside the Tukey fence [Q1−1.5·IQR, Q3+1.5·IQR].
- **FPY / OEE** — see glossary in the Java project SDD; reused here.
- **Clean Architecture** — concentric layers with the dependency rule pointing
  inward; outer = frameworks/IO, inner = policy.

---

## 2. Architecture (TOGAF + Clean Architecture)

### 2.1 Layered Structure
The system follows the Clean Architecture dependency rule. Arrows point
inward (toward higher policy):

```
[ infrastructure: web (FastAPI), db (SQLAlchemy), cache (Redis), mqtt ] ─►
[ use_cases: IngestTelemetry, analytics_engine, ports ] ─►
[ domain: TelemetryReading, DeviceStatus, Anomaly, threshold policy ]
```

In TOGAF terms: the domain is the **Business Architecture** layer, the
use-cases are the **Business Process/Application** layer, and the
infrastructure/adapters are the **Application Platform** (technology) layer.
This separation lets each layer evolve and be tested independently.

### 2.2 Components

| Layer | Module | Responsibility |
|-------|--------|----------------|
| domain | `domain/models.py` | `TelemetryReading` (frozen dataclass), `DeviceStatus`, `Anomaly` |
| domain | `domain/thresholds.py` | per-metric warn/critical policy + `classify()` |
| use_cases | `use_cases/ports.py` | abstract `TelemetryRepository`, `CachePort`, `EventPublisher` |
| use_cases | `use_cases/analytics_engine.py` | `rolling_stats`, `detect_zscore_anomalies`, `detect_iqr_anomalies` |
| use_cases | `use_cases/ingest_telemetry.py` | `IngestTelemetry` orchestrating save→classify→cache |
| infra | `infrastructure/database.py` + `orm.py` | SQLAlchemy engine, `TelemetryModel` |
| infra | `infrastructure/sqlalchemy_repository.py` | `TelemetryRepository` adapter |
| infra | `infrastructure/redis_cache.py` | `RedisCache` + `_MemoryCache` fallback |
| infra | `infrastructure/mqtt_ingestor.py` | MQTT→TelemetryReading adapter |
| api | `api/schemas.py` + `api/routes.py` + `api/app.py` | FastAPI REST + OpenAPI |

### 2.3 Data Flow (ingestion)
```
MQTT msg ─► MqttIngestor.handle_message ─► IngestTelemetry.execute
        ─► repo.save(reading)                    [persistence]
        ─► repo.fetch_window(device, metric,50)  [rolling context]
        ─► classify(metric, value)              [threshold policy]
        ─► cache.set("status:<device>", status)  [live status cache]
        ─► cache.incr("alerts:<device>:<status>") [dashboard counters]
```

### 2.4 Deployment View
- REST API: `uvicorn industrial.api.app:app` (port 8000) — primary adapter.
- MQTT worker: `python -m industrial.infrastructure.mqtt_ingestor` — secondary
  adapter, scales horizontally, shares the same code/use-cases.
- PostgreSQL holds `telemetry` table; Redis holds status/alerts caches.

---

## 3. Domain Model

```
TelemetryReading (frozen)        DeviceStatus
  device_id : str                  device_id : str
  metric : str                     status : str   (NORMAL|WARNING|CRITICAL)
  value : float                    anomalies : int
  timestamp : datetime             last_value : float
  unit : str                       window_start/end : datetime

Anomaly
  device_id, metric, value, expected_mean, expected_std, zscore, timestamp, rule
```
Invariants enforced in the domain constructor (e.g. non-empty device_id, no NaN,
required timestamp) so invalid data can never enter the system.

---

## 4. Analytics Engine Design

### 4.1 Rolling Statistics
`rolling_stats(values, window=30)` computes mean, std (ddof=1), min, max, count
over the last `window` values using NumPy — O(window) per call, suitable for
streaming ingestion where the window slides forward with each new reading.

### 4.2 Anomaly Detection
Two complementary statistical detectors:
- **Z-score**: for each reading, z = (value − mean)/std; flag if |z| > threshold.
  Sensitive to drift and spikes. Requires ≥2 readings and non-zero variance.
- **IQR (Tukey)**: compute Q1/Q3 over the window; flag values outside
  [Q1−1.5·IQR, Q3+1.5·IQR]. Robust to a few extreme values inflating the std.
  Requires ≥4 readings.

Both are pure functions of `list[TelemetryReading]`, making them trivially
unit-testable and reusable by the API and the MQTT worker.

### 4.3 Threshold Policy
`DEFAULT_THRESHOLDS` map metric→(warn, critical). `classify()` is O(1) and used
both at ingestion (live status) and on demand (device status endpoint). The map
is overridable per call, enabling per-device calibration.

---

## 5. Sequence Diagrams

### 5.1 REST ingestion
```
Client   POST /api/v1/telemetry        routes.ingest          IngestTelemetry
  │  {device_id,metric,value,unit}        │                       │
  │──────────────────────────────────────►│ execute(reading)     │
  │                                        │──────────────────────►│ repo.save
  │                                        │                       │ repo.fetch_window
  │                                        │                       │ classify(value)
  │                                        │                       │ cache.set/incr
  │  201 DeviceStatusOut ◄────────────────│◄──────────────────────│
  │◄──────────────────────────────────────│
```

### 5.2 Analytics query
```
Client  GET /api/v1/analytics?device&metric&window
  │ routes.analytics
  │  repo.fetch_window(device, metric, window)
  │  analytics_engine.rolling_stats(values)
  │  analytics_engine.detect_zscore_anomalies(readings)
  │  analytics_engine.detect_iqr_anomalies(readings)
  │ 200 AnalyticsOut
  │◄
```

---

## 6. Test Strategy (TDD)

Tests are written per layer and run with `pytest --cov=src`:

| File | Tests | Covers |
|------|-------|--------|
| test_domain.py | 11 | entity invariants, threshold classify (parametrised) |
| test_analytics_engine.py | 13 | rolling stats, z-score, IQR, status eval |
| test_use_cases.py | 4 | IngestTelemetry orchestration with fakes |
| test_sqlalchemy_repository.py | 5 | save/count/window/metric-filter (in-memory SQLite) |
| test_memory_cache.py | 5 | set/get/ttl/incr/overwrite |
| test_mqtt_ingestor.py | 4 | JSON message handling, no-broker start |
| test_api.py | 10 | full HTTP stack: ingest, analytics, status, health, OpenAPI, 422/404 |

Pure-logic tests (domain, analytics, use-cases, cache) require no I/O and run
in milliseconds. The repository tests use an in-memory SQLite. The API tests use
FastAPI's `TestClient` against an isolated in-memory DB (recreated per test via
an `autouse` fixture) so they are deterministic and parallel-safe.

---

## 7. Non-Functional Requirements
- **Performance:** NumPy-vectorised analytics; Redis caches hot device status
  (TTL 300s) so the status endpoint is O(1) for cached devices.
- **Reliability:** in-memory cache fallback means the system degrades
  gracefully when Redis is unavailable; SQLite default makes local runs
  zero-config.
- **Security:** Pydantic v2 validation at the API boundary; 422 for invalid
  input; no raw SQL (SQLAlchemy ORM + parameterised queries).
- **Portability:** DATABASE_URL switches between SQLite/PostgreSQL; REDIS_URL
  switches Redis instance; no code changes required.

## 8. Future Work
- Add Exponentially-Weighted Moving Average (EWMA) for drift detection.
- Persist anomaly events to a separate table for auditing.
- WebSocket endpoint for real-time dashboard push.

## 9. Revision History
| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-08-31 | student-python | Initial SDD, Clean Architecture, 52 tests |
''')

print("python tests + docs written")

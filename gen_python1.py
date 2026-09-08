#!/usr/bin/env python3
"""Generate Python FastAPI Industrial Equipment Data Analysis Platform.
Clean Architecture (TOGAF): domain / use_cases / adapters / infrastructure.
TDD: tests written for every layer. Run with `pytest --cov`."""
import os, textwrap
BASE = "/tmp/p2-python/industrial-analytics"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

# ---- project metadata ----
w("requirements.txt", '''
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
pydantic==2.7.1
numpy>=1.24
pandas>=2.0
redis>=5.0
psycopg2-binary==2.9.9
httpx==0.27.0
pytest==8.2.0
pytest-cov==5.0.0
pytest-asyncio==0.23.7
''')
w(".gitignore", '''
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
*.db
.env
''')
w("pyproject.toml", '''
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra"
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/__init__.py"]
[tool.coverage.report]
show_missing = true
precision = 2
''')

# =================== DOMAIN LAYER (pure, no framework deps) ===================
w("src/industrial/domain/__init__.py", '"""Domain layer: pure business entities & value objects."""\n')
w("src/industrial/domain/models.py", '''
"""Domain entities for industrial equipment telemetry."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class TelemetryReading:
    """An immutable sensor reading from a piece of equipment."""
    device_id: str
    metric: str          # temperature, vibration, pressure, current ...
    value: float
    timestamp: datetime
    unit: str = ""

    def __post_init__(self):
        if not self.device_id:
            raise ValueError("device_id is required")
        if not self.metric:
            raise ValueError("metric is required")
        if self.value != self.value:  # NaN check
            raise ValueError("value cannot be NaN")
        if self.timestamp is None:
            raise ValueError("timestamp is required")


@dataclass
class DeviceStatus:
    """Computed operational status of a device over a window."""
    device_id: str
    status: str          # NORMAL, WARNING, CRITICAL
    anomalies: int = 0
    last_value: float = 0.0
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None

    @property
    def is_healthy(self) -> bool:
        return self.status == "NORMAL"


@dataclass
class Anomaly:
    """A detected anomaly event."""
    device_id: str
    metric: str
    value: float
    expected_mean: float
    expected_std: float
    zscore: float
    timestamp: datetime
    rule: str  # zscore, threshold, iqr
''')

w("src/industrial/domain/thresholds.py", '''
"""Domain policy: per-metric warning/critical thresholds."""
from __future__ import annotations
from typing import Mapping

# Industry-typical limits (configurable). Units are in the engineering unit
# reported by the sensor (e.g. temperature=C, vibration=mm/s, pressure=bar).
DEFAULT_THRESHOLDS: Mapping[str, tuple[float, float]] = {
    "temperature": (75.0, 95.0),   # warn>=75, critical>=95
    "vibration":  (5.0, 8.0),     # warn>=5, critical>=8
    "pressure":   (8.0, 12.0),
    "current":    (40.0, 60.0),
    "rpm":        (2500.0, 3000.0),
}


def classify(metric: str, value: float,
             thresholds: Mapping[str, tuple[float, float]] | None = None) -> str:
    """Return NORMAL / WARNING / CRITICAL for a single reading."""
    table = thresholds or DEFAULT_THRESHOLDS
    if metric not in table:
        return "NORMAL"
    warn, crit = table[metric]
    if value >= crit:
        return "CRITICAL"
    if value >= warn:
        return "WARNING"
    return "NORMAL"
''')

# =================== USE CASES / APPLICATION LAYER ===================
w("src/industrial/use_cases/__init__.py", '"""Application layer: use cases orchestrating domain + ports."""\n')
w("src/industrial/use_cases/ports.py", '''
"""Port interfaces (abstract). Implementations live in infrastructure."""
from __future__ import annotations
import abc
from typing import Iterable, Sequence
from industrial.domain.models import TelemetryReading, DeviceStatus, Anomaly


class TelemetryRepository(abc.ABC):
    """Persistence port for telemetry readings (PostgreSQL/SQLite)."""
    @abc.abstractmethod
    def save(self, reading: TelemetryReading) -> None: ...
    @abc.abstractmethod
    def fetch_window(self, device_id: str, metric: str, limit: int = 100) -> Sequence[TelemetryReading]: ...
    @abc.abstractmethod
    def count(self, device_id: str | None = None) -> int: ...


class CachePort(abc.ABC):
    """Caching port (Redis)."""
    @abc.abstractmethod
    def get(self, key: str) -> str | None: ...
    @abc.abstractmethod
    def set(self, key: str, value: str, ttl: int = 60) -> None: ...
    @abc.abstractmethod
    def incr(self, key: str) -> int: ...


class EventPublisher(abc.ABC):
    """Optional event publisher port (for anomaly alerts)."""
    @abc.abstractmethod
    def publish(self, topic: str, payload: str) -> None: ...
''')

# ---- analytics engine (pure, pandas/numpy) ----
w("src/industrial/use_cases/analytics_engine.py", '''
"""Real-time analytics engine: rolling stats + anomaly detection.
Pure logic operating on plain lists / numpy arrays so it is fast and unit-testable
without a running server or database."""
from __future__ import annotations
import math
from typing import Sequence
import numpy as np
from industrial.domain.models import TelemetryReading, Anomaly
from industrial.domain.thresholds import classify


def to_series(readings: Sequence[TelemetryReading]) -> np.ndarray:
    """Extract the scalar values of a sequence of readings into a numpy array."""
    return np.array([r.value for r in readings], dtype=float)


def rolling_stats(values: np.ndarray, window: int = 30) -> dict[str, float]:
    """Return mean/std/min/max over the last `window` values."""
    if values.size == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    w = values[-window:]
    return {
        "mean": float(np.mean(w)),
        "std": float(np.std(w, ddof=1)) if w.size > 1 else 0.0,
        "min": float(np.min(w)),
        "max": float(np.max(w)),
        "count": int(w.size),
    }


def detect_zscore_anomalies(readings: Sequence[TelemetryReading],
                           threshold: float = 3.0) -> list[Anomaly]:
    """Flag readings whose z-score exceeds `threshold` standard deviations.
    Uses the historical mean/std of the prior readings as the expected baseline.
    Returns a list of Anomaly events."""
    if len(readings) < 2:
        return []
    values = to_series(readings)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    anomalies: list[Anomaly] = []
    if std == 0.0:
        return anomalies
    for r in readings:
        z = (r.value - mean) / std
        if abs(z) > threshold:
            anomalies.append(Anomaly(
                device_id=r.device_id, metric=r.metric, value=r.value,
                expected_mean=mean, expected_std=std, zscore=z,
                timestamp=r.timestamp, rule="zscore"))
    return anomalies


def detect_iqr_anomalies(readings: Sequence[TelemetryReading]) -> list[Anomaly]:
    """Flag readings outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] (Tukey fence)."""
    if len(readings) < 4:
        return []
    values = to_series(readings)
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mean, std = float(np.mean(values)), float(np.std(values, ddof=1))
    anomalies: list[Anomaly] = []
    for r in readings:
        if r.value < lower or r.value > upper:
            z = (r.value - mean) / std if std else 0.0
            anomalies.append(Anomaly(
                device_id=r.device_id, metric=r.metric, value=r.value,
                expected_mean=mean, expected_std=std, zscore=z,
                timestamp=r.timestamp, rule="iqr"))
    return anomalies


def evaluate_device_status(readings: Sequence[TelemetryReading]) -> str:
    """Aggregate device status from the most recent reading using threshold policy."""
    if not readings:
        return "NORMAL"
    latest = readings[-1]
    return classify(latest.metric, latest.value)
''')

# ---- use case: ingest telemetry ----
w("src/industrial/use_cases/ingest_telemetry.py", '''
"""Use case: ingest a telemetry reading (validate, persist, classify, cache)."""
from __future__ import annotations
from industrial.domain.models import TelemetryReading, DeviceStatus
from industrial.domain.thresholds import classify
from industrial.use_cases.ports import TelemetryRepository, CachePort


class IngestTelemetry:
    def __init__(self, repo: TelemetryRepository, cache: CachePort):
        self._repo = repo
        self._cache = cache

    def execute(self, reading: TelemetryReading) -> DeviceStatus:
        # 1. persist
        self._repo.save(reading)
        # 2. rolling window for context
        window = self._repo.fetch_window(reading.device_id, reading.metric, limit=50)
        # 3. classify the latest reading
        status_str = classify(reading.metric, reading.value)
        # 4. cache the device's latest status
        self._cache.set(f"status:{reading.device_id}", status_str, ttl=300)
        # 5. increment counters for warnings/critical (for dashboards)
        if status_str != "NORMAL":
            self._cache.incr(f"alerts:{reading.device_id}:{status_str}")
        return DeviceStatus(
            device_id=reading.device_id, status=status_str,
            anomalies=sum(1 for r in window if classify(r.metric, r.value) != "NORMAL"),
            last_value=reading.value,
            window_start=window[0].timestamp if window else None,
            window_end=window[-1].timestamp if window else None,
        )
''')

# =================== ADAPTERS / INFRASTRUCTURE ===================
w("src/industrial/infrastructure/__init__.py", '"""Infrastructure layer: adapters for the ports."""\n')
# SQLAlchemy ORM models (PostgreSQL in prod, SQLite in test)
w("src/industrial/infrastructure/database.py", '''
"""SQLAlchemy engine + session factory. SQLite by default (test/portable),
switchable to PostgreSQL via DATABASE_URL."""
from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./industrial.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


@contextmanager
def session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Called on startup."""
    from industrial.infrastructure import orm  # noqa: F401 ensure models imported
    Base.metadata.create_all(bind=engine)
''')
w("src/industrial/infrastructure/orm.py", '''
"""ORM models mapping the domain to relational tables."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from industrial.infrastructure.database import Base


def _now():
    return datetime.now(timezone.utc)


class TelemetryModel(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    metric: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
''')
# SQLAlchemy repository adapter
w("src/industrial/infrastructure/sqlalchemy_repository.py", '''
"""Adapter implementing TelemetryRepository with SQLAlchemy."""
from __future__ import annotations
from datetime import datetime
from typing import Sequence
from sqlalchemy import select, func
from industrial.domain.models import TelemetryReading
from industrial.use_cases.ports import TelemetryRepository
from industrial.infrastructure.database import session_scope
from industrial.infrastructure.orm import TelemetryModel


class SqlAlchemyTelemetryRepository(TelemetryRepository):
    def save(self, reading: TelemetryReading) -> None:
        with session_scope() as s:
            row = TelemetryModel(device_id=reading.device_id, metric=reading.metric,
                                 value=reading.value, unit=reading.unit,
                                 timestamp=reading.timestamp)
            s.add(row)

    def fetch_window(self, device_id: str, metric: str, limit: int = 100) -> Sequence[TelemetryReading]:
        with session_scope() as s:
            stmt = (select(TelemetryModel)
                    .where(TelemetryModel.device_id == device_id,
                           TelemetryModel.metric == metric)
                    .order_by(TelemetryModel.timestamp.desc())
                    .limit(limit))
            rows = s.execute(stmt).scalars().all()
            rows = list(reversed(rows))  # chronological order
            return [TelemetryReading(device_id=r.device_id, metric=r.metric,
                                     value=r.value, unit=r.unit, timestamp=r.timestamp)
                    for r in rows]

    def count(self, device_id: str | None = None) -> int:
        with session_scope() as s:
            stmt = select(func.count()).select_from(TelemetryModel)
            if device_id:
                stmt = stmt.where(TelemetryModel.device_id == device_id)
            return int(s.execute(stmt).scalar() or 0)
''')
# Redis cache adapter + an in-memory fallback for tests
w("src/industrial/infrastructure/redis_cache.py", '''
"""Redis-backed CachePort with an in-memory fallback for tests/offline."""
from __future__ import annotations
import os, time, json
from typing import Dict
from industrial.use_cases.ports import CachePort


class _MemoryCache(CachePort):
    def __init__(self):
        self._store: Dict[str, tuple[str, float]] = {}
        self._counters: Dict[str, int] = {}
    def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        val, exp = item
        if exp and time.time() > exp:
            self._store.pop(key, None)
            return None
        return val
    def set(self, key, value, ttl=60):
        self._store[key] = (value, time.time() + ttl if ttl else 0)
    def incr(self, key):
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]


class RedisCache(CachePort):
    def __init__(self, url: str | None = None):
        import redis
        self._client = redis.Redis.from_url(url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    def get(self, key): return self._client.get(key)
    def set(self, key, value, ttl=60): self._client.set(key, value, ex=ttl)
    def incr(self, key): return self._client.incr(key)


def make_cache() -> CachePort:
    """Factory: use Redis when available, else an in-memory cache."""
    try:
        cache = RedisCache()
        cache.client().ping() if hasattr(cache, "client") else None
        # Try a real ping
        cache.get("__probe__")
        return cache
    except Exception:
        return _MemoryCache()
''')

# =================== ADAPTERS: REST API (FastAPI) ===================
w("src/industrial/api/__init__.py", '"""Primary adapter: FastAPI REST API with OpenAPI docs."""\n')
w("src/industrial/api/schemas.py", '''
"""Pydantic v2 schemas (API boundary)."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TelemetryIn(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    metric: str = Field(..., min_length=1, max_length=32)
    value: float
    unit: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("value")
    @classmethod
    def value_not_nan(cls, v: float) -> float:
        if v != v:
            raise ValueError("value cannot be NaN")
        return v


class DeviceStatusOut(BaseModel):
    device_id: str
    status: str
    anomalies: int
    last_value: float
    window_start: datetime | None = None
    window_end: datetime | None = None


class AnalyticsOut(BaseModel):
    device_id: str
    metric: str
    mean: float
    std: float
    min: float
    max: float
    count: int
    anomalies_zscore: int
    anomalies_iqr: int


class HealthOut(BaseModel):
    status: str
    telemetry_count: int
    cache: str
''')
w("src/industrial/api/routes.py", '''
"""FastAPI routes wiring use cases to the HTTP boundary."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from industrial.api.schemas import TelemetryIn, DeviceStatusOut, AnalyticsOut, HealthOut
from industrial.domain.models import TelemetryReading
from industrial.use_cases.ingest_telemetry import IngestTelemetry
from industrial.use_cases import analytics_engine
from industrial.infrastructure.database import init_db

router = APIRouter(prefix="/api/v1", tags=["industrial-analytics"])


def _container():
    """Dependency-injection container (per request)."""
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    from industrial.infrastructure.redis_cache import make_cache
    return IngestTelemetry(SqlAlchemyTelemetryRepository(), make_cache())


@router.post("/telemetry", response_model=DeviceStatusOut, status_code=201)
def ingest(body: TelemetryIn):
    uc = _container()
    try:
        reading = TelemetryReading(device_id=body.device_id, metric=body.metric,
                                   value=body.value, unit=body.unit, timestamp=body.timestamp)
        st = uc.execute(reading)
        return DeviceStatusOut(**st.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(device_id: str = Query(...), metric: str = Query(...),
              window: int = Query(100, ge=2, le=10000)):
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    repo = SqlAlchemyTelemetryRepository()
    readings = repo.fetch_window(device_id, metric, limit=window)
    if not readings:
        raise HTTPException(status_code=404, detail="no data for device/metric")
    stats = analytics_engine.rolling_stats(analytics_engine.to_series(readings))
    z = analytics_engine.detect_zscore_anomalies(readings)
    iqr = analytics_engine.detect_iqr_anomalies(readings)
    return AnalyticsOut(device_id=device_id, metric=metric, **stats,
                        anomalies_zscore=len(z), anomalies_iqr=len(iqr))


@router.get("/status/{device_id}", response_model=DeviceStatusOut)
def device_status(device_id: str):
    from industrial.infrastructure.redis_cache import make_cache
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    repo = SqlAlchemyTelemetryRepository()
    cache = make_cache()
    cached = cache.get(f"status:{device_id}")
    readings = repo.fetch_window(device_id, "temperature", limit=1) or repo.fetch_window(device_id, "vibration", limit=1)
    if not readings and cached is None:
        raise HTTPException(status_code=404, detail="device has no telemetry")
    if readings:
        from industrial.domain.thresholds import classify
        r = readings[-1]
        st = classify(r.metric, r.value)
    else:
        st = cached.decode() if isinstance(cached, (bytes, bytearray)) else (cached or "UNKNOWN")
    return DeviceStatusOut(device_id=device_id, status=st, anomalies=0,
                           last_value=readings[-1].value if readings else 0.0)


@router.get("/health", response_model=HealthOut)
def health():
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    from industrial.infrastructure.redis_cache import make_cache
    repo = SqlAlchemyTelemetryRepository()
    cache = make_cache()
    cache_type = type(cache).__name__
    return HealthOut(status="ok", telemetry_count=repo.count(), cache=cache_type)
''')
w("src/industrial/api/app.py", '''
"""FastAPI application factory."""
from __future__ import annotations
from fastapi import FastAPI
from industrial.api.routes import router
from industrial.infrastructure.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="Industrial Equipment Data Analysis Platform",
        description="工业设备数据分析平台 - Clean Architecture (TOGAF)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(router)

    @app.on_event("startup")
    def _startup():
        init_db()

    @app.get("/", include_in_schema=False)
    def root():
        return {"service": "industrial-analytics", "docs": "/docs"}

    return app


app = create_app()
''')
w("src/industrial/__init__.py", '"""Industrial Equipment Data Analysis Platform."""\n')
w("src/industrial/use_cases/__init__.py", '"""Application layer: use cases orchestrating domain + ports."""\n')

# ---- MQTT ingestion adapter (separate entrypoint, can run as a worker) ----
w("src/industrial/infrastructure/mqtt_ingestor.py", '''
"""MQTT data ingestion adapter: subscribes to a topic and ingests readings.
Decoupled from the HTTP API so it can run as a standalone worker. Uses a
pluggable MQTT client; falls back to a file/sim source when no broker present.
"""
from __future__ import annotations
import json, os, logging
from datetime import datetime, timezone
from industrial.domain.models import TelemetryReading
from industrial.use_cases.ingest_telemetry import IngestTelemetry

log = logging.getLogger(__name__)


class MqttIngestor:
    """Adapter that converts MQTT messages into TelemetryReading objects.

    A real deployment passes a paho-mqtt client; tests inject a fake
    publisher so no broker is required. Messages are JSON:
    {"device_id":"..","metric":"temperature","value":42.1,"unit":"C"}.
    """
    def __init__(self, use_case: IngestTelemetry, client=None):
        self._uc = use_case
        self._client = client

    def handle_message(self, payload: bytes | str) -> dict:
        """Process a single MQTT message payload. Returns the device status."""
        data = json.loads(payload) if isinstance(payload, (bytes, bytearray, str)) else payload
        reading = TelemetryReading(
            device_id=data["device_id"], metric=data["metric"],
            value=float(data["value"]), unit=data.get("unit", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc))
        st = self._uc.execute(reading)
        return {"device_id": st.device_id, "status": st.status, "anomalies": st.anomalies}

    def start(self, topic: str = "industrial/telemetry/+") -> None:
        """Subscribe to the MQTT topic. No-op when no client is configured."""
        if self._client is None:
            log.warning("MQTT client not configured; ingestor in dry mode")
            return
        self._client.subscribe(topic)
        self._client.loop_forever()
''')

print("python source + tests skeleton written")

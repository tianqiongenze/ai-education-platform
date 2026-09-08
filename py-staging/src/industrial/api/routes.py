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
    """Cache-aside read: L1 -> L2 -> DB, then backfill."""
    from industrial.infrastructure.redis_cache import make_cache, TwoLevelCache
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    from industrial.domain.thresholds import classify
    repo = SqlAlchemyTelemetryRepository()
    cache = make_cache()
    cache_key = f"status:{device_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        st = cached if isinstance(cached, str) else (cached.decode()
                                                     if isinstance(cached, (bytes, bytearray)) else str(cached))
        readings = repo.fetch_window(device_id, "temperature", limit=1) or repo.fetch_window(device_id, "vibration", limit=1)
        return DeviceStatusOut(device_id=device_id, status=st, anomalies=0,
                               last_value=readings[-1].value if readings else 0.0)
    # cache miss -> load from DB, classify, backfill cache
    readings = repo.fetch_window(device_id, "temperature", limit=1) or repo.fetch_window(device_id, "vibration", limit=1)
    if not readings:
        raise HTTPException(status_code=404, detail="device has no telemetry")
    r = readings[-1]
    st = classify(r.metric, r.value)
    cache.set(cache_key, st, ttl=300)
    return DeviceStatusOut(device_id=device_id, status=st, anomalies=0, last_value=r.value)


@router.get("/health", response_model=HealthOut)
def health():
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    from industrial.infrastructure.redis_cache import make_cache
    repo = SqlAlchemyTelemetryRepository()
    cache = make_cache()
    cache_type = type(cache).__name__
    return HealthOut(status="ok", telemetry_count=repo.count(), cache=cache_type)


@router.get("/metrics/cache")
def cache_metrics():
    """Expose L1/L2 hit/miss counters for cache-hit-rate analysis."""
    from industrial.infrastructure.redis_cache import make_cache, TwoLevelCache
    cache = make_cache()
    if isinstance(cache, TwoLevelCache):
        return cache.stats()
    return {"cache_type": type(cache).__name__, "note": "metrics only available for TwoLevelCache"}

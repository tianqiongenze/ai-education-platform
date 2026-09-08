"""Adapter implementing TelemetryRepository with SQLAlchemy.

Read/write separation: writes go to the master engine (session_scope),
reads go to the read engine/replica (read_session_scope) to offload the
writer and scale read throughput.
"""
from __future__ import annotations
from typing import Sequence
from sqlalchemy import select, func
from industrial.domain.models import TelemetryReading
from industrial.use_cases.ports import TelemetryRepository
from industrial.infrastructure.database import session_scope, read_session_scope
from industrial.infrastructure.orm import TelemetryModel


class SqlAlchemyTelemetryRepository(TelemetryRepository):
    def save(self, reading: TelemetryReading) -> None:
        # WRITE -> master
        with session_scope() as s:
            row = TelemetryModel(device_id=reading.device_id, metric=reading.metric,
                                 value=reading.value, unit=reading.unit,
                                 timestamp=reading.timestamp)
            s.add(row)

    def fetch_window(self, device_id: str, metric: str, limit: int = 100) -> Sequence[TelemetryReading]:
        # READ -> replica (or master if no replica configured)
        with read_session_scope() as s:
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
        with read_session_scope() as s:
            stmt = select(func.count()).select_from(TelemetryModel)
            if device_id:
                stmt = stmt.where(TelemetryModel.device_id == device_id)
            return int(s.execute(stmt).scalar() or 0)

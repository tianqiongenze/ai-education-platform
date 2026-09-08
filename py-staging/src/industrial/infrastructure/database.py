"""SQLAlchemy engines + session factories with read/write separation.

Write master:  PRIMARY_DATABASE_URL (default = DATABASE_URL)
Read replica:   READ_DATABASE_URL (falls back to the write master when unset)

Connection pooling is tuned for PostgreSQL:
  - pool_size + max_overflow controls total connections
  - pool_pre_ping avoids stale connections after DB failovers
  - pool_recycle prevents the server from closing idle conns first
"""
from __future__ import annotations
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./industrial.db")
# Read replica (optional). Defaults to the write master so reads still work
# in single-instance deployments. Set READ_DATABASE_URL to a PG replica.
READ_DATABASE_URL = os.getenv("READ_DATABASE_URL", DATABASE_URL)

_PRIMARY_URL = os.getenv("PRIMARY_DATABASE_URL", DATABASE_URL)


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _build_engine(url: str, *, for_write: bool):
    if _is_sqlite(url):
        connect_args = {"check_same_thread": False}
        pool_kwargs = {"poolclass": StaticPool} if ":memory:" in url else {}
        return create_engine(url, connect_args=connect_args, future=True, **pool_kwargs)
    # PostgreSQL (or other network DBs): use a real connection pool.
    pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,        # drop stale connections transparently
        pool_recycle=pool_recycle,  # avoid server idle timeouts
        pool_timeout=30,
        future=True,
    )


# Write master engine (all INSERT/UPDATE/DELETE go here).
engine = _build_engine(_PRIMARY_URL, for_write=True)
# Read engine (SELECT queries route here for read/write splitting).
read_engine = _build_engine(READ_DATABASE_URL, for_write=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
ReadSessionLocal = sessionmaker(bind=read_engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


@contextmanager
def session_scope() -> Session:
    """Write session (master). Use for writes; commits on success, rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def read_session_scope() -> Session:
    """Read session (replica/master). Use for read-only queries to offload the writer."""
    session = ReadSessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables on the write master. Called on startup."""
    from industrial.infrastructure import orm  # noqa: F401 ensure models imported
    Base.metadata.create_all(bind=engine)

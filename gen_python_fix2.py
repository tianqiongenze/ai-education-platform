#!/usr/bin/env python3
"""Fix conftest: don't clear metadata; import orm once; recreate tables per test."""
import os, textwrap
BASE = "/tmp/p2-python/industrial-analytics"
def w(rel, content):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))

w("tests/conftest.py", '''
"""Shared pytest fixtures: isolated in-memory SQLite DB + in-memory cache.

The in-memory SQLite DB uses SQLAlchemy's StaticPool so every connection
shares the single in-memory database (a normal pool would give each
connection its own empty DB). Tables are recreated before each test for
isolation, and the ORM module is imported once so models stay registered.
"""
import os
# Force an isolated in-memory SQLite BEFORE importing app code.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import pytest

# Import the ORM models ONCE so they register on Base.metadata. This must
# happen before the fixtures recreate tables.
from industrial.infrastructure import orm  # noqa: F401
from industrial.infrastructure.database import Base, engine
from industrial.infrastructure.redis_cache import _MemoryCache


@pytest.fixture(autouse=True)
def fresh_db():
    """Recreate all tables before every test for full isolation."""
    Base.metadata.create_all(bind=engine)
    yield
    # Drop everything (including data) so the next test starts clean.
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def memory_cache():
    return _MemoryCache()


@pytest.fixture
def repo():
    from industrial.infrastructure.sqlalchemy_repository import SqlAlchemyTelemetryRepository
    return SqlAlchemyTelemetryRepository()
''')

print("conftest fixed (no clear(), import orm once, drop_all per test)")

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.clock import current_time
from app.core.db import Base, get_db
from app.main import app


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture()
def clock():
    return FakeClock()


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    engine.dispose()


@pytest.fixture()
def client(clock, session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_time] = lambda: clock.now
    yield TestClient(app)
    app.dependency_overrides.clear()

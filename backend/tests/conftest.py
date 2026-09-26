from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.security as security
from app.core.clock import current_time
from app.core.db import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.models import Employee

PASSWORD = "test-password"


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    monkeypatch.setattr(security, "PBKDF2_ITERATIONS", 1_000)


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
def app_setup(clock, session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[current_time] = lambda: clock.now
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def make_account(session_factory):
    def _make(login: str, role: str = "conductor", brigade: str = "Бригада 1", depot: str = "Депо Восток", **extra):
        with session_factory() as db:
            employee = Employee(
                login=login,
                password_hash=hash_password(PASSWORD),
                full_name=extra.pop("full_name", f"Сотрудник {login}"),
                role=role,
                brigade=brigade,
                depot=depot,
                **extra,
            )
            db.add(employee)
            db.commit()
            return employee.id

    return _make


@pytest.fixture()
def login_as(app_setup, make_account):
    """A fresh client (own cookie jar) signed in as a newly created account."""

    def _login(login: str, role: str = "conductor", **account) -> TestClient:
        make_account(login, role, **account)
        c = TestClient(app)
        r = c.post("/auth/login", json={"login": login, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return c

    return _login


@pytest.fixture()
def metod(login_as):
    return login_as("metodist", role="methodologist")


@pytest.fixture()
def client(login_as):
    """Signed-in methodologist: may create scenarios and also play them like any user."""
    return login_as("tester", role="methodologist")


@pytest.fixture()
def anon(app_setup):
    return TestClient(app)

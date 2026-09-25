"""Real parallel requests against Postgres: the row lock + unique step must apply a step exactly once.

Runs only when TEST_DATABASE_URL points to a disposable database whose name ends with "_test"
(its public schema is dropped and recreated), e.g.:
    TEST_DATABASE_URL=postgresql://vsm@localhost:5433/vsm_test pytest tests/test_concurrency_pg.py
"""

import os
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.db_upgrade import upgrade
from app.main import app
from app.models.models import ChoiceLog
from app.scenarios.library import load_scenario

PG_URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not PG_URL.startswith("postgresql") or not (make_url(PG_URL).database or "").endswith("_test"),
    reason="needs TEST_DATABASE_URL to a disposable Postgres database named *_test",
)


@pytest.fixture()
def pg():
    engine = create_engine(PG_URL, pool_size=20)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    upgrade(PG_URL)
    Session = sessionmaker(bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), Session
    app.dependency_overrides.clear()
    engine.dispose()


def test_parallel_submits_for_one_step_apply_exactly_once(pg):
    client, Session = pg
    employee_id = client.post("/employees", json={"full_name": "Синтетический Проводник"}).json()["id"]
    scenario_id = client.post("/scenarios", json=load_scenario("window_seat")).json()["id"]
    attempt_id = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id}).json()["attempt_id"]

    workers = 8
    barrier = threading.Barrier(workers)
    statuses: list[int] = []

    def submit(choice_id: str) -> None:
        barrier.wait()
        r = client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": choice_id, "expected_step": 0})
        statuses.append(r.status_code)

    threads = [threading.Thread(target=submit, args=("calm" if i % 2 else "order",)) for i in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(statuses) == [200] + [409] * (workers - 1)
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(ChoiceLog).where(ChoiceLog.attempt_id == attempt_id)) == 1
    state = client.get(f"/attempts/{attempt_id}").json()
    assert state["step"] == 1
    assert state["loyalty"] in (65, 50)  # exactly one of calm (+5) / order (-10) was applied

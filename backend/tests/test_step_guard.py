"""Protection against applying the same step twice (double click, retries, concurrent requests)."""

import pytest
from sqlalchemy import func, select

from app.models.models import Attempt, ChoiceLog, Employee, Scenario
from app.scenarios.library import load_scenario
from app.scenarios.errors import ScenarioError
from app.services import attempts as service

DEMO_SCENARIO = load_scenario("seat_recline")


def _seed(db):
    employee = Employee(full_name="Синтетический Проводник")
    scenario = Scenario(title="demo", description="", graph=DEMO_SCENARIO["graph"])
    db.add_all([employee, scenario])
    db.commit()
    return employee.id, scenario.id


def _log_count(db, attempt_id):
    return db.scalar(select(func.count()).select_from(ChoiceLog).where(ChoiceLog.attempt_id == attempt_id))


def test_repeated_submit_with_same_expected_step_applies_once(client, session_factory):
    employee_id = client.post("/employees", json={"full_name": "Синтетический Проводник"}).json()["id"]
    scenario_id = client.post("/scenarios", json={"title": "demo", "graph": DEMO_SCENARIO["graph"]}).json()["id"]
    attempt_id = client.post("/attempts", json={"scenario_id": scenario_id}).json()["attempt_id"]

    first = client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c2", "expected_step": 0})
    second = client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c2", "expected_step": 0})

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["code"] in ("attempt_finished", "step_mismatch")
    with session_factory() as db:
        assert _log_count(db, attempt_id) == 1


def test_missing_expected_step_is_a_validation_error(client):
    r = client.post("/attempts/whatever/choice", json={"choice_id": "c1"})
    assert r.status_code == 422


def test_concurrent_winner_log_makes_loser_roll_back_entirely(session_factory, clock):
    """Simulates the race the row lock prevents: another transaction already wrote step 1.

    The unique (attempt_id, step) constraint must reject our write, and the rollback must
    undo our change to the attempt as well, so the state is changed exactly once.
    """
    with session_factory() as db:
        employee_id, scenario_id = _seed(db)
        attempt_id = service.start_attempt(db, employee_id, scenario_id, clock.now).attempt.id
        db.add(ChoiceLog(attempt_id=attempt_id, step=1, node_id="n1", choice_id="c1", timed_out=False))
        db.commit()

    with session_factory() as db:
        with pytest.raises(ScenarioError) as exc:
            service.submit_choice(db, attempt_id, employee_id, "c3", 0, clock.now)
        assert exc.value.code == "step_mismatch"

    with session_factory() as db:
        attempt = db.get(Attempt, attempt_id)
        assert (attempt.step, attempt.current_node, attempt.loyalty, attempt.safety) == (0, "n1", 50, 50)
        assert _log_count(db, attempt_id) == 1

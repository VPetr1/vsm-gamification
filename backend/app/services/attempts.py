"""Attempt use-cases: load under a row lock, run the engine, persist state and the step log."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Attempt, ChoiceLog, Employee, Scenario
from app.scenarios.engine import ScenarioEngine, StepResult
from app.scenarios.errors import ScenarioError


@dataclass
class AttemptView:
    attempt: Attempt
    engine: ScenarioEngine
    last_step: ChoiceLog | None


def _lock_attempt(db: Session, attempt_id: str) -> Attempt:
    # FOR UPDATE serialises concurrent requests on one attempt (Postgres; SQLite ignores it).
    attempt = db.execute(select(Attempt).where(Attempt.id == attempt_id).with_for_update()).scalar_one_or_none()
    if attempt is None:
        raise ScenarioError("attempt_not_found", "attempt not found")
    return attempt


def _last_log(db: Session, attempt_id: str) -> ChoiceLog | None:
    return db.execute(
        select(ChoiceLog).where(ChoiceLog.attempt_id == attempt_id).order_by(ChoiceLog.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def _record(db: Session, attempt: Attempt, result: StepResult) -> ChoiceLog:
    log = ChoiceLog(
        attempt_id=attempt.id,
        node_id=result.prev_node_id,
        choice_id=result.choice_id,
        timed_out=result.timed_out,
        loyalty_delta=result.loyalty_delta,
        safety_delta=result.safety_delta,
    )
    db.add(log)
    return log


def start_attempt(db: Session, employee_id: str, scenario_id: str, now: datetime) -> AttemptView:
    if db.get(Employee, employee_id) is None:
        raise ScenarioError("employee_not_found", "employee not found")
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise ScenarioError("scenario_not_found", "scenario not found")

    engine = ScenarioEngine(scenario.graph)
    attempt = Attempt(employee_id=employee_id, scenario_id=scenario.id, current_node="")
    engine.start(attempt, now)
    db.add(attempt)
    db.commit()
    return AttemptView(attempt, engine, last_step=None)


def get_attempt(db: Session, attempt_id: str, now: datetime) -> AttemptView:
    """Returns current state; if the timer ran out while the client was away, applies the timeout first."""
    attempt = _lock_attempt(db, attempt_id)
    engine = ScenarioEngine(attempt.scenario.graph)
    result = engine.expire_if_due(attempt, now)
    if result is None:
        db.rollback()  # release the row lock; nothing changed
        return AttemptView(attempt, engine, _last_log(db, attempt_id))
    log = _record(db, attempt, result)
    db.commit()
    return AttemptView(attempt, engine, log)


def submit_choice(db: Session, attempt_id: str, choice_id: str | None, now: datetime) -> AttemptView:
    attempt = _lock_attempt(db, attempt_id)
    engine = ScenarioEngine(attempt.scenario.graph)
    try:
        result = engine.apply_choice(attempt, choice_id, now)
    except ScenarioError:
        db.rollback()
        raise
    log = _record(db, attempt, result)
    db.commit()
    return AttemptView(attempt, engine, log)

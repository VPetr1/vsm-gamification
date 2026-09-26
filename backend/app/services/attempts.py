"""Attempt use-cases: load under a row lock, run the engine, persist state and the step log."""

import copy
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Attempt, AttemptStatus, ChoiceLog, Employee, Scenario
from app.scenarios.engine import ScenarioEngine, StepResult
from app.scenarios.errors import ScenarioError
from app.services.rewards import apply_rewards


@dataclass
class AttemptView:
    attempt: Attempt
    engine: ScenarioEngine
    last_step: ChoiceLog | None


def _owned(attempt_id: str, employee_id: str):
    # Someone else's attempt is reported as missing, so attempt ids cannot be probed.
    return select(Attempt).where(Attempt.id == attempt_id, Attempt.employee_id == employee_id)


def _lock_attempt(db: Session, attempt_id: str, employee_id: str) -> Attempt:
    # FOR UPDATE serialises concurrent requests on one attempt (Postgres; SQLite ignores it).
    attempt = db.execute(_owned(attempt_id, employee_id).with_for_update()).scalar_one_or_none()
    if attempt is None:
        raise ScenarioError("attempt_not_found", "attempt not found")
    return attempt


def _last_log(db: Session, attempt_id: str) -> ChoiceLog | None:
    return db.execute(
        select(ChoiceLog).where(ChoiceLog.attempt_id == attempt_id).order_by(ChoiceLog.step.desc()).limit(1)
    ).scalar_one_or_none()


def _record(db: Session, attempt: Attempt, result: StepResult, now: datetime) -> ChoiceLog:
    if attempt.status == AttemptStatus.finished:
        apply_rewards(db, attempt, now)
    log = ChoiceLog(
        attempt_id=attempt.id,
        step=result.step,
        node_id=result.prev_node_id,
        choice_id=result.choice_id,
        timed_out=result.timed_out,
        next_node=result.next_node,
        loyalty_delta=result.loyalty_delta,
        safety_delta=result.safety_delta,
        loyalty_after=result.loyalty_after,
        safety_after=result.safety_after,
        assessment=result.assessment,
    )
    db.add(log)
    return log


def _commit_step(db: Session) -> None:
    """Commit state + log atomically; a duplicate (attempt_id, step) means another request won the race."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ScenarioError("step_mismatch", "this step was already applied by another request") from exc


def start_attempt(db: Session, employee_id: str, scenario_id: str, now: datetime) -> AttemptView:
    if db.get(Employee, employee_id) is None:
        raise ScenarioError("employee_not_found", "employee not found")
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise ScenarioError("scenario_not_found", "scenario not found")

    snapshot = copy.deepcopy(scenario.graph)
    engine = ScenarioEngine(snapshot)
    attempt = Attempt(
        employee_id=employee_id,
        scenario_id=scenario.id,
        scenario_version=scenario.version,
        graph_snapshot=snapshot,
        current_node="",
    )
    engine.start(attempt, now)
    db.add(attempt)
    db.commit()
    return AttemptView(attempt, engine, last_step=None)


def get_attempt(db: Session, attempt_id: str, employee_id: str, now: datetime) -> AttemptView:
    """Returns current state; if the timer ran out while the client was away, applies the timeout first."""
    attempt = _lock_attempt(db, attempt_id, employee_id)
    engine = ScenarioEngine(attempt.graph_snapshot)
    result = engine.expire_if_due(attempt, now)
    if result is None:
        db.rollback()  # release the row lock; nothing changed
        return AttemptView(attempt, engine, _last_log(db, attempt_id))
    log = _record(db, attempt, result, now)
    try:
        _commit_step(db)
    except ScenarioError:
        # A concurrent request resolved the same timeout first; show what it produced.
        attempt = db.get(Attempt, attempt_id)
        return AttemptView(attempt, engine, _last_log(db, attempt_id))
    return AttemptView(attempt, engine, log)


def submit_choice(
    db: Session, attempt_id: str, employee_id: str, choice_id: str | None, expected_step: int, now: datetime
) -> AttemptView:
    attempt = _lock_attempt(db, attempt_id, employee_id)
    engine = ScenarioEngine(attempt.graph_snapshot)
    try:
        result = engine.apply_choice(attempt, choice_id, expected_step, now)
    except ScenarioError:
        db.rollback()
        raise
    log = _record(db, attempt, result, now)
    _commit_step(db)
    return AttemptView(attempt, engine, log)


def finished_attempt_with_logs(db: Session, attempt_id: str, employee_id: str) -> tuple[Attempt, list[ChoiceLog]]:
    """The debrief is only available after the end, so it never reveals effects of pending choices."""
    attempt = db.execute(_owned(attempt_id, employee_id)).scalar_one_or_none()
    if attempt is None:
        raise ScenarioError("attempt_not_found", "attempt not found")
    if attempt.status != AttemptStatus.finished:
        raise ScenarioError("attempt_not_finished", "the result is available after the attempt is finished")
    logs = db.execute(select(ChoiceLog).where(ChoiceLog.attempt_id == attempt_id).order_by(ChoiceLog.step)).scalars()
    return attempt, list(logs)

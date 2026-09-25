from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Attempt, ChoiceLog, Employee, Scenario
from app.schemas.schemas import (
    AttemptStateOut,
    ChoiceOut,
    NodeOut,
    StartAttemptIn,
    SubmitChoiceIn,
)
from app.scenarios.engine import ScenarioEngine, visible_choices

router = APIRouter(prefix="/attempts", tags=["attempts"])


def _node_out(node_id: str, node: dict, loyalty: int, safety: int) -> NodeOut:
    if node.get("is_ending"):
        return NodeOut(node_id=node_id, text=node["text"], is_ending=True, ending_summary=node["ending_summary"])
    choices = [ChoiceOut(id=c["id"], text=c["text"]) for c in visible_choices(node, loyalty, safety)]
    return NodeOut(node_id=node_id, text=node["text"], timer_seconds=node["timer_seconds"], choices=choices)


def _state_out(attempt: Attempt, node: dict) -> AttemptStateOut:
    return AttemptStateOut(
        attempt_id=attempt.id,
        loyalty=attempt.loyalty,
        safety=attempt.safety,
        status=attempt.status.value,
        node=_node_out(attempt.current_node, node, attempt.loyalty, attempt.safety),
        node_shown_at=attempt.node_shown_at,
    )


@router.post("", response_model=AttemptStateOut, status_code=201)
def start_attempt(payload: StartAttemptIn, db: Session = Depends(get_db)) -> AttemptStateOut:
    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(404, "employee not found")
    scenario = db.get(Scenario, payload.scenario_id)
    if scenario is None:
        raise HTTPException(404, "scenario not found")

    engine = ScenarioEngine(scenario.graph)
    attempt = Attempt(employee_id=employee.id, scenario_id=scenario.id, current_node="")
    engine.start(attempt)

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return _state_out(attempt, engine.current_node(attempt))


@router.get("/{attempt_id}", response_model=AttemptStateOut)
def get_attempt(attempt_id: str, db: Session = Depends(get_db)) -> AttemptStateOut:
    attempt = db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(404, "attempt not found")
    engine = ScenarioEngine(attempt.scenario.graph)
    return _state_out(attempt, engine.current_node(attempt))


@router.post("/{attempt_id}/choice", response_model=AttemptStateOut)
def submit_choice(attempt_id: str, payload: SubmitChoiceIn, db: Session = Depends(get_db)) -> AttemptStateOut:
    attempt = db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(404, "attempt not found")

    engine = ScenarioEngine(attempt.scenario.graph)
    try:
        result = engine.apply_choice(attempt, payload.choice_id, datetime.now(timezone.utc))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    db.add(
        ChoiceLog(
            attempt_id=attempt.id,
            node_id=result.prev_node_id,
            choice_id=None if result.timed_out else payload.choice_id,
            timed_out=result.timed_out,
            loyalty_delta=result.loyalty_delta,
            safety_delta=result.safety_delta,
        )
    )
    db.commit()
    db.refresh(attempt)

    return _state_out(attempt, engine.current_node(attempt))

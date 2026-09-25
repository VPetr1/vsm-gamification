from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import as_aware, current_time
from app.core.db import get_db
from app.schemas.schemas import (
    AttemptStateOut,
    ChoiceOut,
    LastStepOut,
    NodeOut,
    StartAttemptIn,
    SubmitChoiceIn,
)
from app.scenarios.engine import visible_choices
from app.services import attempts as service

router = APIRouter(prefix="/attempts", tags=["attempts"])


def _node_out(node_id: str, node: dict, loyalty: int, safety: int) -> NodeOut:
    # Only ids and texts are exposed: effects, conditions and next nodes stay on the server.
    if node.get("is_ending"):
        return NodeOut(node_id=node_id, text=node["text"], is_ending=True, ending_summary=node["ending_summary"])
    choices = [ChoiceOut(id=c["id"], text=c["text"]) for c in visible_choices(node, loyalty, safety)]
    return NodeOut(node_id=node_id, text=node["text"], timer_seconds=node.get("timer_seconds"), choices=choices)


def _state_out(view: service.AttemptView, now: datetime) -> AttemptStateOut:
    attempt, engine, log = view.attempt, view.engine, view.last_step
    return AttemptStateOut(
        attempt_id=attempt.id,
        loyalty=attempt.loyalty,
        safety=attempt.safety,
        status=attempt.status.value,
        step=attempt.step,
        node=_node_out(attempt.current_node, engine.current_node(attempt), attempt.loyalty, attempt.safety),
        node_shown_at=as_aware(attempt.node_shown_at),
        deadline=engine.deadline(attempt),
        server_time=now,
        last_step=None if log is None else LastStepOut(step=log.step, node_id=log.node_id, choice_id=log.choice_id, timed_out=log.timed_out),
    )


@router.post("", response_model=AttemptStateOut, status_code=201)
def start_attempt(
    payload: StartAttemptIn, db: Session = Depends(get_db), now: datetime = Depends(current_time)
) -> AttemptStateOut:
    return _state_out(service.start_attempt(db, payload.employee_id, payload.scenario_id, now), now)


@router.get("/{attempt_id}", response_model=AttemptStateOut)
def get_attempt(attempt_id: str, db: Session = Depends(get_db), now: datetime = Depends(current_time)) -> AttemptStateOut:
    return _state_out(service.get_attempt(db, attempt_id, now), now)


@router.post("/{attempt_id}/choice", response_model=AttemptStateOut)
def submit_choice(
    attempt_id: str,
    payload: SubmitChoiceIn,
    db: Session = Depends(get_db),
    now: datetime = Depends(current_time),
) -> AttemptStateOut:
    return _state_out(service.submit_choice(db, attempt_id, payload.choice_id, payload.expected_step, now), now)

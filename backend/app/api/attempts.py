from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import as_utc, current_time
from app.core.db import get_db
from app.models.models import Attempt, ChoiceLog
from app.schemas.schemas import (
    AttemptResultOut,
    AttemptStateOut,
    ChoiceOut,
    EndingOut,
    LastStepOut,
    NodeOut,
    ResultStepOut,
    ScalesOut,
    StartAttemptIn,
    SubmitChoiceIn,
)
from app.scenarios.engine import DEFAULT_INITIAL, visible_choices
from app.services import attempts as service

router = APIRouter(prefix="/attempts", tags=["attempts"])


def _node_out(node_id: str, node: dict, attempt) -> NodeOut:
    # Only ids and texts are exposed: effects, conditions and next nodes stay on the server.
    if node.get("is_ending"):
        return NodeOut(node_id=node_id, text=node["text"], is_ending=True, ending_summary=node["ending_summary"])
    choices = [ChoiceOut(id=c["id"], text=c["text"]) for c in visible_choices(node, attempt)]
    return NodeOut(node_id=node_id, text=node["text"], timer_seconds=node.get("timer_seconds"), choices=choices)


def _state_out(view: service.AttemptView, now: datetime) -> AttemptStateOut:
    attempt, engine, log = view.attempt, view.engine, view.last_step
    return AttemptStateOut(
        attempt_id=attempt.id,
        scenario_id=attempt.scenario_id,
        scenario_version=attempt.scenario_version,
        loyalty=attempt.loyalty,
        safety=attempt.safety,
        status=attempt.status.value,
        step=attempt.step,
        node=_node_out(attempt.current_node, engine.current_node(attempt), attempt),
        node_shown_at=as_utc(attempt.node_shown_at),
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


def _result_step(nodes: dict, log: ChoiceLog) -> ResultStepOut:
    node = nodes[log.node_id]
    if log.timed_out:
        outcome, choice_text = node.get("timeout", {}), None
    else:
        outcome = next(c for c in node["choices"] if c["id"] == log.choice_id)
        choice_text = outcome["text"]
    return ResultStepOut(
        step=log.step,
        node_id=log.node_id,
        situation=node["text"],
        choice_id=log.choice_id,
        choice_text=choice_text,
        timed_out=log.timed_out,
        loyalty_delta=log.loyalty_delta,
        safety_delta=log.safety_delta,
        loyalty_after=log.loyalty_after,
        safety_after=log.safety_after,
        explanation=outcome.get("explanation"),
        lesson=node.get("debrief"),
    )


def _result_out(attempt: Attempt, logs: list[ChoiceLog]) -> AttemptResultOut:
    graph = attempt.graph_snapshot
    ending = graph["nodes"][attempt.current_node]
    return AttemptResultOut(
        attempt_id=attempt.id,
        scenario_id=attempt.scenario_id,
        scenario_title=attempt.scenario.title,
        scenario_version=attempt.scenario_version,
        status=attempt.status.value,
        started_at=as_utc(attempt.started_at),
        finished_at=as_utc(attempt.finished_at),
        initial=ScalesOut(**{**DEFAULT_INITIAL, **graph.get("initial", {})}),
        final=ScalesOut(loyalty=attempt.loyalty, safety=attempt.safety),
        ending=EndingOut(
            node_id=attempt.current_node,
            text=ending["text"],
            summary=ending["ending_summary"],
            outcome=ending.get("outcome"),
        ),
        steps=[_result_step(graph["nodes"], log) for log in logs],
    )


@router.get("/{attempt_id}/result", response_model=AttemptResultOut)
def get_result(attempt_id: str, db: Session = Depends(get_db)) -> AttemptResultOut:
    return _result_out(*service.finished_attempt_with_logs(db, attempt_id))

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime

from app.api.deps import current_user, methodologist
from app.core.clock import current_time
from app.core.db import get_db
from app.models.models import Attempt, AttemptStatus, Employee, Scenario, ScenarioBest
from app.scenarios.validator import ScenarioValidationError, validate_graph

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    graph: dict


class ScenarioOut(BaseModel):
    id: str
    title: str
    description: str
    tags: list[str]
    version: int

    model_config = {"from_attributes": True}


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(
    payload: ScenarioIn,
    db: Session = Depends(get_db),
    _: Employee = Depends(methodologist),
    now: datetime = Depends(current_time),
) -> Scenario:
    try:
        validate_graph(payload.graph)
    except ScenarioValidationError as exc:
        raise HTTPException(
            422,
            detail={
                "code": "invalid_scenario",
                "message": f"scenario graph has {len(exc.errors)} problem(s)",
                "errors": exc.errors,
            },
        ) from exc

    tags = [t.strip() for t in payload.tags if t.strip()][:12]
    scenario = Scenario(
        title=payload.title,
        description=payload.description,
        tags=tags,
        graph=payload.graph,
        origin="api",
        published_at=now,
        updated_at=now,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


class CatalogItemOut(ScenarioOut):
    my_best_score: int | None
    in_progress_attempt_id: str | None


@router.get("", response_model=list[CatalogItemOut])
def list_scenarios(db: Session = Depends(get_db), user: Employee = Depends(current_user)) -> list[CatalogItemOut]:
    """Published scenarios with the caller's own progress (never anyone else's)."""
    bests = dict(
        db.execute(select(ScenarioBest.scenario_id, ScenarioBest.best_score).where(ScenarioBest.employee_id == user.id)).all()
    )
    in_progress: dict[str, str] = {}
    for scenario_id, attempt_id in db.execute(
        select(Attempt.scenario_id, Attempt.id)
        .where(Attempt.employee_id == user.id, Attempt.status == AttemptStatus.in_progress)
        .order_by(Attempt.started_at)
    ):
        in_progress[scenario_id] = attempt_id
    scenarios = db.scalars(select(Scenario).where(Scenario.version > 0).order_by(Scenario.created_at, Scenario.title))
    return [
        CatalogItemOut(
            id=s.id,
            title=s.title,
            description=s.description,
            tags=s.tags or [],
            version=s.version,
            my_best_score=bests.get(s.id),
            in_progress_attempt_id=in_progress.get(s.id),
        )
        for s in scenarios
    ]

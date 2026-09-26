from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import current_user, methodologist
from app.core.db import get_db
from app.models.models import Employee, Scenario
from app.scenarios.validator import ScenarioValidationError, validate_graph

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    graph: dict


class ScenarioOut(BaseModel):
    id: str
    title: str
    description: str
    version: int

    model_config = {"from_attributes": True}


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(
    payload: ScenarioIn, db: Session = Depends(get_db), _: Employee = Depends(methodologist)
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

    scenario = Scenario(title=payload.title, description=payload.description, graph=payload.graph)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db), _: Employee = Depends(current_user)) -> list[Scenario]:
    return db.query(Scenario).all()

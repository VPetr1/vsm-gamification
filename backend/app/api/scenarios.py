from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Scenario
from app.scenarios.validator import ScenarioValidationError, validate_graph

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioIn(BaseModel):
    title: str
    description: str = ""
    graph: dict


class ScenarioOut(BaseModel):
    id: str
    title: str
    description: str

    model_config = {"from_attributes": True}


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(payload: ScenarioIn, db: Session = Depends(get_db)) -> Scenario:
    try:
        validate_graph(payload.graph)
    except ScenarioValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    scenario = Scenario(title=payload.title, description=payload.description, graph=payload.graph)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)) -> list[Scenario]:
    return db.query(Scenario).all()

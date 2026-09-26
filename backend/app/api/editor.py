from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import methodologist
from app.core.clock import current_time
from app.core.db import get_db
from app.services import editor as service

router = APIRouter(prefix="/editor", tags=["editor"], dependencies=[Depends(methodologist)])


class DraftIn(BaseModel):
    title: str = Field(max_length=300)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    graph: dict

    def normalized(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": [t.strip() for t in self.tags if t.strip()],
            "graph": self.graph,
        }


class NewScenarioIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    graph: dict | None = None


@router.get("/scenarios")
def list_scenarios(db: Session = Depends(get_db)) -> list[dict]:
    return service.list_items(db)


@router.post("/scenarios", status_code=201)
def create_scenario(payload: NewScenarioIn, db: Session = Depends(get_db), now: datetime = Depends(current_time)) -> dict:
    return service.view(service.create(db, payload.title, payload.description, payload.tags, payload.graph, now))


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str, db: Session = Depends(get_db)) -> dict:
    return service.view(service.get(db, scenario_id))


@router.put("/scenarios/{scenario_id}/draft")
def save_draft(
    scenario_id: str, payload: DraftIn, db: Session = Depends(get_db), now: datetime = Depends(current_time)
) -> dict:
    """Saves even an invalid draft; the response lists the problems with node/field paths."""
    return service.view(service.save_draft(db, service.get(db, scenario_id), payload.normalized(), now))


@router.delete("/scenarios/{scenario_id}/draft")
def discard_draft(scenario_id: str, db: Session = Depends(get_db), now: datetime = Depends(current_time)) -> dict:
    return service.view(service.discard_draft(db, service.get(db, scenario_id), now))


@router.post("/scenarios/{scenario_id}/publish")
def publish(scenario_id: str, db: Session = Depends(get_db), now: datetime = Depends(current_time)) -> dict:
    return service.view(service.publish(db, service.get(db, scenario_id), now))

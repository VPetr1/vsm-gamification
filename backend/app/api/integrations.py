"""Read-only API for HR and LMS systems, authorised by a static key (X-API-Key), not by user sessions."""

import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.gamification.rules import level_for
from app.models.models import Attempt, AttemptStatus, Employee, EmployeeAchievement, Role
from app.scenarios.errors import ScenarioError
from app.services.competency import competency_profile, competency_view
from app.services.rewards import total_xp


def integration_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.integration_api_key:
        raise ScenarioError("integration_disabled", "интеграционный API выключен: задайте INTEGRATION_API_KEY")
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.integration_api_key):
        raise ScenarioError("bad_api_key", "неверный или отсутствующий X-API-Key")


router = APIRouter(prefix="/integrations", tags=["integrations"], dependencies=[Depends(integration_key)])


def _competencies(items: list[dict]) -> list[dict]:
    return [{"id": c["id"], "earned": c["earned"], "max": c["max"], "percent": c["percent"]} for c in items]


@router.get("/progress")
def progress(db: Session = Depends(get_db)) -> list[dict]:
    """Current training status of every conductor: XP, level, competencies, achievements."""
    result = []
    for employee in db.scalars(select(Employee).where(Employee.role == Role.conductor.value).order_by(Employee.full_name)):
        xp = total_xp(db, employee.id)
        last = db.scalar(
            select(Attempt.finished_at)
            .where(Attempt.employee_id == employee.id, Attempt.status == AttemptStatus.finished)
            .order_by(Attempt.finished_at.desc())
            .limit(1)
        )
        comp = competency_profile(db, employee)
        result.append(
            {
                "employee_id": employee.id,
                "full_name": employee.full_name,
                "brigade": employee.brigade,
                "depot": employee.depot,
                "synthetic": employee.is_synthetic,
                "xp": xp,
                "level": level_for(xp).number,
                "competencies": _competencies(comp["competencies"]),
                "weakest_competency": comp["weakest"]["id"] if comp["weakest"] else None,
                "achievements": sorted(
                    db.scalars(select(EmployeeAchievement.achievement_id).where(EmployeeAchievement.employee_id == employee.id))
                ),
                "last_finished_at": last,
            }
        )
    return result


@router.get("/attempts")
def finished_attempts(
    finished_after: datetime | None = Query(default=None, description="ISO 8601; only attempts finished later"),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Finished attempts in chronological order, for incremental export (pass the last finished_at back)."""
    query = select(Attempt).where(Attempt.status == AttemptStatus.finished).order_by(Attempt.finished_at).limit(limit)
    if finished_after is not None:
        query = query.where(Attempt.finished_at > finished_after)
    items = []
    for a in db.scalars(query):
        ending = a.graph_snapshot["nodes"].get(a.current_node, {})
        items.append(
            {
                "attempt_id": a.id,
                "employee_id": a.employee_id,
                "scenario_id": a.scenario_id,
                "scenario_title": a.scenario_title,
                "scenario_version": a.scenario_version,
                "started_at": a.started_at,
                "finished_at": a.finished_at,
                "outcome": ending.get("outcome"),
                "score": a.score,
                "xp_gained": a.xp_gained,
                "synthetic": a.is_synthetic,
                "competencies": [c for c in _competencies(competency_view(a.assessment or {})) if c["percent"] is not None],
            }
        )
    return items

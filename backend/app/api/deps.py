from datetime import datetime

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.clock import current_time
from app.core.db import get_db
from app.models.models import Employee, Role
from app.scenarios.errors import ScenarioError
from app.services.auth import employee_for_token

SESSION_COOKIE = "vsm_session"


def current_user(request: Request, db: Session = Depends(get_db), now: datetime = Depends(current_time)) -> Employee:
    """Identity comes only from the server-side session, never from ids or roles sent by the client."""
    employee = employee_for_token(db, request.cookies.get(SESSION_COOKIE), now)
    if employee is None:
        raise ScenarioError("unauthorized", "нужно войти в систему")
    return employee


def methodologist(user: Employee = Depends(current_user)) -> Employee:
    if user.role != Role.methodologist.value:
        raise ScenarioError("forbidden", "доступно только методисту")
    return user

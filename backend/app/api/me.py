from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.clock import current_time
from app.core.db import get_db
from app.models.models import Employee
from app.services import profile as service

router = APIRouter(tags=["profile"])


@router.get("/me/profile")
def my_profile(db: Session = Depends(get_db), user: Employee = Depends(current_user)) -> dict:
    return service.profile(db, user)


@router.get("/me/attempts")
def my_attempts(db: Session = Depends(get_db), user: Employee = Depends(current_user)) -> list[dict]:
    return service.history(db, user)


@router.get("/me/notifications")
def my_notifications(db: Session = Depends(get_db), user: Employee = Depends(current_user)) -> dict:
    return service.notifications(db, user)


@router.post("/me/notifications/read-all", status_code=204)
def read_all(
    db: Session = Depends(get_db), user: Employee = Depends(current_user), now: datetime = Depends(current_time)
) -> None:
    service.mark_read(db, user, now)


@router.post("/me/notifications/{notification_id}/read", status_code=204)
def read_one(
    notification_id: str,
    db: Session = Depends(get_db),
    user: Employee = Depends(current_user),
    now: datetime = Depends(current_time),
) -> None:
    service.mark_read(db, user, now, notification_id)


@router.get("/leaderboard")
def leaderboard(
    scope: str = Query("brigade", description="brigade | depot | company"),
    db: Session = Depends(get_db),
    user: Employee = Depends(current_user),
) -> dict:
    return service.leaderboard(db, user, scope)

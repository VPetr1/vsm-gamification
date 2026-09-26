from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE, current_user
from app.core.clock import current_time
from app.core.config import settings
from app.core.db import get_db
from app.models.models import Employee
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class MeOut(BaseModel):
    id: str
    login: str | None
    full_name: str
    role: str
    brigade: str
    depot: str

    model_config = {"from_attributes": True}


class DemoAccountOut(BaseModel):
    login: str
    full_name: str
    role: str
    brigade: str
    depot: str

    model_config = {"from_attributes": True}


@router.get("/demo-accounts", response_model=list[DemoAccountOut])
def demo_accounts(db: Session = Depends(get_db)) -> list[Employee]:
    """Public list for the profile picker: display fields only, no ids, hashes or history."""
    return list(db.execute(select(Employee).where(Employee.login.is_not(None)).order_by(Employee.role, Employee.full_name)).scalars())


@router.post("/login", response_model=MeOut)
def login(
    payload: LoginIn, response: Response, db: Session = Depends(get_db), now: datetime = Depends(current_time)
) -> Employee:
    token, employee = service.sign_in(db, payload.login, payload.password, now)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return employee


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    service.sign_out(db, request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=MeOut)
def me(user: Employee = Depends(current_user)) -> Employee:
    return user

"""Demo sign-in: password check, opaque session token in an HttpOnly cookie, session rows in the DB."""

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.clock import as_utc
from app.core.config import settings
from app.core.security import new_session_token, token_digest, verify_password
from app.models.models import AuthSession, Employee
from app.scenarios.errors import ScenarioError


def sign_in(db: Session, login: str, password: str, now: datetime) -> tuple[str, Employee]:
    employee = db.execute(select(Employee).where(Employee.login == login).with_for_update()).scalar_one_or_none()
    if employee is not None and employee.locked_until is not None and as_utc(employee.locked_until) > now:
        retry_after = int((as_utc(employee.locked_until) - now).total_seconds()) + 1
        db.rollback()
        raise ScenarioError("too_many_attempts", "слишком много неудачных попыток входа", retry_after=retry_after)
    # Same error for an unknown login and a wrong password, so logins cannot be probed.
    if employee is None or not verify_password(password, employee.password_hash):
        if employee is not None:
            employee.failed_logins += 1
            if employee.failed_logins >= settings.login_max_failures:
                employee.failed_logins = 0
                employee.locked_until = now + timedelta(seconds=settings.login_lock_seconds)
            db.commit()
        raise ScenarioError("invalid_credentials", "неверный логин или пароль")
    employee.failed_logins = 0
    employee.locked_until = None
    token = new_session_token()
    db.execute(delete(AuthSession).where(AuthSession.expires_at < now))
    db.add(
        AuthSession(
            token_hash=token_digest(token),
            employee_id=employee.id,
            created_at=now,
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
        )
    )
    db.commit()
    return token, employee


def employee_for_token(db: Session, token: str | None, now: datetime) -> Employee | None:
    if not token:
        return None
    session = db.execute(select(AuthSession).where(AuthSession.token_hash == token_digest(token))).scalar_one_or_none()
    if session is None or as_utc(session.expires_at) <= now:
        return None
    return session.employee


def sign_out(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == token_digest(token)))
        db.commit()

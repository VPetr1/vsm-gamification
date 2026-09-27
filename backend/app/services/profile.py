"""Read models for the player: profile, history, leaderboard, notifications."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.gamification.rules import ACHIEVEMENTS, custom_achievement_id, level_for
from app.models.models import (
    Attempt,
    AttemptStatus,
    Employee,
    EmployeeAchievement,
    Notification,
    Role,
    Scenario,
    ScenarioBest,
)
from app.scenarios.errors import ScenarioError
from app.services.competency import competency_profile, competency_view as _competency_view
from app.services.rewards import total_xp

SCOPES = ("brigade", "depot", "company")


def level_view(xp: int) -> dict:
    level = level_for(xp)
    return {"number": level.number, "title": level.title, "min_xp": level.min_xp, "next_min_xp": level.next_min_xp}


def achievements_view(db: Session, employee_id: str) -> list[dict]:
    """Built-in achievements, then those defined in published scenarios, then earned ones whose
    scenario no longer defines them (their title and icon were copied when awarded)."""
    owned = {
        row.achievement_id: row
        for row in db.scalars(select(EmployeeAchievement).where(EmployeeAchievement.employee_id == employee_id))
    }

    def item(aid: str, title: str, description: str, icon: str, scenario_title: str | None) -> dict:
        row = owned.get(aid)
        return {
            "id": aid,
            "title": title,
            "description": description,
            "icon": icon,
            "scenario_title": scenario_title,
            "earned": row is not None,
            "awarded_at": row.awarded_at if row else None,
            "attempt_id": row.attempt_id if row else None,
        }

    items = [item(a.id, a.title, a.description, a.icon, None) for a in ACHIEVEMENTS.values()]
    for scenario in published_scenarios(db):
        for a in (scenario.graph or {}).get("achievements", []):
            aid = custom_achievement_id(scenario.id, a["id"])
            items.append(item(aid, a["title"], a.get("description", ""), a.get("icon", "medal"), scenario.title))
    listed = {i["id"] for i in items}
    for aid, row in owned.items():
        if aid not in listed:
            items.append(item(aid, row.title or aid, row.description or "", row.icon or "medal", None))
    return items


def published_scenarios(db: Session) -> list[Scenario]:
    return list(db.scalars(select(Scenario).where(Scenario.version > 0).order_by(Scenario.created_at, Scenario.title)))


def profile(db: Session, user: Employee) -> dict:
    xp = total_xp(db, user.id)
    finished = db.scalar(
        select(func.count()).select_from(Attempt).where(
            Attempt.employee_id == user.id, Attempt.status == AttemptStatus.finished
        )
    )
    completed = db.scalar(select(func.count()).select_from(ScenarioBest).where(ScenarioBest.employee_id == user.id))
    return {
        "full_name": user.full_name,
        "role": user.role,
        "brigade": user.brigade,
        "depot": user.depot,
        "xp": xp,
        "level": level_view(xp),
        "achievements": achievements_view(db, user.id),
        "stats": {
            "finished_attempts": finished,
            "scenarios_completed": completed,
            "scenarios_published": len(published_scenarios(db)),
        },
        **competency_profile(db, user),
    }


def history(db: Session, user: Employee) -> list[dict]:
    rows = db.execute(
        select(Attempt, Scenario.title)
        .join(Scenario, Scenario.id == Attempt.scenario_id)
        .where(Attempt.employee_id == user.id)
        .order_by(Attempt.started_at.desc())
    ).all()
    items = []
    for attempt, title in rows:
        ending = attempt.graph_snapshot["nodes"].get(attempt.current_node, {})
        finished = attempt.status == AttemptStatus.finished
        items.append(
            {
                "attempt_id": attempt.id,
                "scenario_id": attempt.scenario_id,
                "scenario_title": attempt.scenario_title or title,
                "scenario_version": attempt.scenario_version,
                "status": attempt.status.value,
                "started_at": attempt.started_at,
                "finished_at": attempt.finished_at,
                "score": attempt.score,
                "xp_gained": attempt.xp_gained,
                "outcome": ending.get("outcome") if finished else None,
                "outcome_label": ending.get("outcome_label") if finished else None,
                "outcome_tone": ending.get("outcome_tone") if finished else None,
                "synthetic": attempt.is_synthetic,
                "competencies": [
                    {"id": c["id"], "title": c["title"], "earned": c["earned"], "max": c["max"], "percent": c["percent"]}
                    for c in _competency_view(attempt.assessment or {})
                    if c["percent"] is not None
                ]
                if finished
                else [],
            }
        )
    return items


def leaderboard(db: Session, user: Employee, scope: str) -> dict:
    if scope not in SCOPES:
        raise ScenarioError("bad_scope", f"scope must be one of {list(SCOPES)}")
    xp = func.coalesce(func.sum(ScenarioBest.best_score), 0).label("xp")
    completed = func.count(ScenarioBest.id).label("completed")
    query = (
        select(Employee, xp, completed)
        .outerjoin(ScenarioBest, ScenarioBest.employee_id == Employee.id)
        .where(Employee.role == Role.conductor.value)
        .group_by(Employee.id)
        .order_by(xp.desc(), Employee.full_name)
    )
    if scope == "brigade":
        query = query.where(Employee.brigade == user.brigade, Employee.depot == user.depot)
        label = f"{user.brigade}, {user.depot}" if user.brigade else "бригада не указана"
    elif scope == "depot":
        query = query.where(Employee.depot == user.depot)
        label = user.depot or "депо не указано"
    else:
        label = "вся компания"
    if scope != "company" and not (user.brigade if scope == "brigade" else user.depot):
        return {"scope": scope, "scope_label": label, "entries": []}

    entries, rank, previous_xp = [], 0, None
    for position, (employee, points, done) in enumerate(db.execute(query).all(), start=1):
        if points != previous_xp:
            rank, previous_xp = position, points
        level = level_for(points)
        # Only what the table shows: no ids, logins or roles of other people.
        entries.append(
            {
                "rank": rank,
                "name": employee.full_name,
                "brigade": employee.brigade,
                "depot": employee.depot,
                "level": level.number,
                "level_title": level.title,
                "xp": points,
                "completed": done,
                "is_me": employee.id == user.id,
                "synthetic": employee.is_synthetic,
            }
        )
    return {"scope": scope, "scope_label": label, "entries": entries}


def notifications(db: Session, user: Employee) -> dict:
    items = list(
        db.scalars(
            select(Notification)
            .where(Notification.employee_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
    )
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.employee_id == user.id, Notification.read_at.is_(None)
        )
    )
    return {
        "unread": unread,
        "items": [
            {
                "id": n.id,
                "kind": n.kind,
                "title": n.title,
                "body": n.body,
                "link": n.link,
                "created_at": n.created_at,
                "read": n.read_at is not None,
            }
            for n in items
        ],
    }


def mark_read(db: Session, user: Employee, now: datetime, notification_id: str | None = None) -> None:
    stmt = update(Notification).where(Notification.employee_id == user.id, Notification.read_at.is_(None))
    if notification_id is not None:
        stmt = stmt.where(Notification.id == notification_id)
    db.execute(stmt.values(read_at=now))
    db.commit()

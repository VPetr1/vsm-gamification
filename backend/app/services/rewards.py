"""Rewards for a finished attempt: score, XP (improvement only), level, achievements, notifications.

Runs inside the transaction of the step that finished the attempt. That step can be committed
only once (row lock + UNIQUE(attempt_id, step)), so rewards are granted exactly once — whether
the attempt ended by a choice, by a timeout, or by a timeout resolved on restore.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gamification.rules import ACHIEVEMENTS, attempt_score, level_for
from app.models.models import Attempt, Employee, EmployeeAchievement, Notification, ScenarioBest
from app.scenarios.conditions import evaluate


def total_xp(db: Session, employee_id: str) -> int:
    return db.scalar(
        select(func.coalesce(func.sum(ScenarioBest.best_score), 0)).where(ScenarioBest.employee_id == employee_id)
    )


def _notify(db: Session, employee_id: str, kind: str, title: str, body: str, link: str | None, now: datetime) -> None:
    db.add(Notification(employee_id=employee_id, kind=kind, title=title, body=body, link=link, created_at=now))


def apply_rewards(db: Session, attempt: Attempt, now: datetime) -> None:
    # Serialise reward updates per employee, so two attempts finishing at once cannot both
    # claim the same improvement or the same achievement.
    db.execute(select(Employee.id).where(Employee.id == attempt.employee_id).with_for_update())

    score = attempt_score(attempt.loyalty, attempt.safety)
    xp_before = total_xp(db, attempt.employee_id)
    best = db.execute(
        select(ScenarioBest)
        .where(ScenarioBest.employee_id == attempt.employee_id, ScenarioBest.scenario_id == attempt.scenario_id)
        .with_for_update()
    ).scalar_one_or_none()
    previous = best.best_score if best else 0
    gained = max(0, score - previous)
    if best is None:
        db.add(
            ScenarioBest(
                employee_id=attempt.employee_id,
                scenario_id=attempt.scenario_id,
                best_score=score,
                attempt_id=attempt.id,
                updated_at=now,
            )
        )
    elif score > previous:
        best.best_score, best.attempt_id, best.updated_at = score, attempt.id, now
    attempt.score = score
    attempt.xp_gained = gained

    level_before, level_after = level_for(xp_before), level_for(xp_before + gained)
    if level_after.number > level_before.number:
        _notify(db, attempt.employee_id, "level_up", f"Новый уровень: {level_after.title}",
                f"Опыт: {xp_before + gained}.", "/profile", now)

    owned = set(
        db.scalars(select(EmployeeAchievement.achievement_id).where(EmployeeAchievement.employee_id == attempt.employee_id))
    )
    candidates = ["first_trip"]
    for award in attempt.graph_snapshot.get("awards", []):
        if evaluate(award["when"], attempt):
            candidates.append(award["achievement"])
    new = [a for a in dict.fromkeys(candidates) if a not in owned and a in ACHIEVEMENTS]
    for achievement_id in new:
        db.add(EmployeeAchievement(employee_id=attempt.employee_id, achievement_id=achievement_id,
                                   attempt_id=attempt.id, awarded_at=now))
        achievement = ACHIEVEMENTS[achievement_id]
        _notify(db, attempt.employee_id, "achievement", f"Достижение «{achievement.title}»",
                achievement.description, f"/attempts/{attempt.id}/result", now)

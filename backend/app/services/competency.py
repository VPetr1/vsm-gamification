"""Competency profile and the recommended next training.

Aggregation: for every scenario take the employee's latest finished attempt and sum its
per-competency earned and max points; score = earned / max. Replaying a scenario replaces its
contribution instead of adding to it, so repetition alone cannot raise a competency.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.gamification.competencies import COMPETENCIES, add_assessments, percent
from app.models.models import Attempt, AttemptStatus, Employee, Scenario, ScenarioBest


def latest_finished_per_scenario(db: Session, employee_id: str) -> dict[str, Attempt]:
    latest: dict[str, Attempt] = {}
    for attempt in db.scalars(
        select(Attempt)
        .where(Attempt.employee_id == employee_id, Attempt.status == AttemptStatus.finished)
        .order_by(Attempt.finished_at)
    ):
        latest[attempt.scenario_id] = attempt
    return latest


def competency_view(totals: dict) -> list[dict]:
    items = []
    for c in COMPETENCIES.values():
        bucket = totals.get(c.id, {"earned": 0, "max": 0})
        items.append(
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "earned": bucket["earned"],
                "max": bucket["max"],
                "percent": percent(bucket["earned"], bucket["max"]),  # None = "нет данных"
            }
        )
    return items


def weakest(items: list[dict]) -> dict | None:
    """Lowest evaluated competency below 100%; nothing is "weak" when every assessed decision was right."""
    candidates = [i for i in items if i["percent"] is not None and i["percent"] < 100]
    return min(candidates, key=lambda i: i["percent"]) if candidates else None


def _recommend(db: Session, employee: Employee, latest: dict[str, Attempt], weak: dict | None) -> dict | None:
    published = list(db.scalars(select(Scenario).where(Scenario.version > 0).order_by(Scenario.created_at)))
    if not published:
        return None
    unfinished = [s for s in published if s.id not in latest]

    def card(scenario: Scenario, kind: str, reason: str, goal: str | None = None) -> dict:
        return {"scenario_id": scenario.id, "title": scenario.title, "kind": kind, "reason": reason, "goal": goal}

    if not latest:
        return card(published[0], "start", "Первый рейс: начните с этого сценария, чтобы получить оценки компетенций.")
    if weak:
        tagged = [s for s in unfinished if weak["id"] in (s.tags or [])]
        if tagged:
            return card(
                tagged[0], "weak_new",
                f"Слабая оценённая компетенция — «{weak['title']}» ({weak['percent']}%). Этот сценарий её тренирует.",
            )
    if unfinished:
        return card(unfinished[0], "new", "Вы ещё не проходили этот сценарий.")

    # Everything is done: replay with a concrete, measurable goal.
    if weak and weak["percent"] < 100:
        def ratio(attempt: Attempt) -> float:
            bucket = (attempt.assessment or {}).get(weak["id"])
            return bucket["earned"] / bucket["max"] if bucket and bucket["max"] else 2.0

        scenario_id, attempt = min(latest.items(), key=lambda item: ratio(item[1]))
        bucket = (attempt.assessment or {}).get(weak["id"])
        if bucket and bucket["max"]:
            scenario = next(s for s in published if s.id == scenario_id)
            return card(
                scenario, "replay",
                f"В последнем прохождении «{scenario.title}» по компетенции «{weak['title']}» "
                f"набрано {bucket['earned']} из {bucket['max']}.",
                f"Цель: больше {bucket['earned']} из {bucket['max']} баллов по компетенции «{weak['title']}».",
            )
    bests = dict(db.execute(select(ScenarioBest.scenario_id, ScenarioBest.best_score).where(ScenarioBest.employee_id == employee.id)).all())
    scenario = min(published, key=lambda s: bests.get(s.id, 0))
    best = bests.get(scenario.id, 0)
    return card(scenario, "replay", "Все оценённые решения приняты верно.",
                f"Цель: результат рейса выше лучшего ({best} из 100).")


def competency_profile(db: Session, employee: Employee) -> dict:
    latest = latest_finished_per_scenario(db, employee.id)
    totals: dict = {}
    for attempt in latest.values():
        totals = add_assessments(totals, attempt.assessment or {})
    items = competency_view(totals)
    weak = weakest(items)
    return {
        "competencies": items,
        "weakest": None if weak is None else {"id": weak["id"], "title": weak["title"], "percent": weak["percent"]},
        "recommendation": _recommend(db, employee, latest, weak),
        "aggregation": "последнее завершённое прохождение каждого сценария; сумма набранных и максимальных баллов",
    }

"""Competencies are separate from XP and from the two game scales.

A scenario marks how well each option serves a competency ("assessment" on choices and timeouts).
At every decision the engine records, per competency, the points earned by the applied outcome and
the maximum available among the options the player could actually see at that moment. Steps where
nothing was available for a competency (max 0) are not evaluated for it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Competency:
    id: str
    title: str
    description: str


COMPETENCIES: dict[str, Competency] = {
    c.id: c
    for c in [
        Competency("communication", "Коммуникация", "Тон, деэскалация, работа с обеими сторонами конфликта."),
        Competency("safety", "Безопасность", "Своевременное устранение угроз в салоне и проходе."),
        Competency("first_aid", "Первая помощь", "Действия при ухудшении самочувствия пассажира."),
        Competency(
            "stress_resistance",
            "Стрессоустойчивость",
            "Учебный показатель: качество действий в шагах с таймером. Не психологическая оценка.",
        ),
    ]
}

MAX_POINTS = 10


def add_assessments(total: dict | None, step: dict) -> dict:
    """Running per-competency sums {id: {"earned": e, "max": m}}; returns a new dict."""
    merged = {k: dict(v) for k, v in (total or {}).items()}
    for competency, points in step.items():
        bucket = merged.setdefault(competency, {"earned": 0, "max": 0})
        bucket["earned"] += points["earned"]
        bucket["max"] += points["max"]
    return merged


def percent(earned: int, maximum: int) -> int | None:
    return None if maximum == 0 else round(100 * earned / maximum)

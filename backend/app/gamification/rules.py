"""Reward rules. Formulas are documented in docs/scoring.md; keep the two in sync.

- Attempt score = the raw score (mean of the final scales) placed between the scenario's worst (0)
  and best (100) reachable ending; see app/scenarios/scoring.py.
- XP = sum over scenarios of the employee's best score in that scenario. A finished attempt
  therefore adds max(0, score - previous best): replaying a scenario can only add an improvement.
- Level = the highest threshold reached in LEVELS.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Achievement:
    id: str
    title: str
    description: str
    icon: str = "medal"


# Stable ids: scenarios reference them in "awards"; titles may change freely.
ACHIEVEMENTS: dict[str, Achievement] = {
    a.id: a
    for a in [
        Achievement("first_trip", "Первый рейс", "Завершите первый сценарий."),
        Achievement("diplomat", "Дипломат", "Выполните условия деэскалации, заданные в сценарии.", "handshake"),
        Achievement("safe_passage", "Безопасный проход", "Освободите проход до истечения таймера.", "shield"),
    ]
}

# Icons a scenario's own achievements may use; the frontend maps each to a glyph.
ACHIEVEMENT_ICONS = ("medal", "star", "shield", "heart", "handshake", "clock")


def custom_achievement_id(scenario_id: str, local_id: str) -> str:
    return f"s:{scenario_id}:{local_id}"


LEVELS: list[tuple[int, str]] = [
    (0, "Стажёр"),
    (50, "Проводник"),
    (120, "Опытный проводник"),
    (200, "Старший проводник"),
    (300, "Наставник"),
]


@dataclass(frozen=True)
class Level:
    number: int
    title: str
    min_xp: int
    next_min_xp: int | None


def level_for(xp: int) -> Level:
    number = max(i for i, (threshold, _) in enumerate(LEVELS) if xp >= threshold)
    threshold, title = LEVELS[number]
    next_min = LEVELS[number + 1][0] if number + 1 < len(LEVELS) else None
    return Level(number=number + 1, title=title, min_xp=threshold, next_min_xp=next_min)

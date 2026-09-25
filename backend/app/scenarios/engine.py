from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.models import Attempt, AttemptStatus


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _as_aware(dt: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip; Postgres keeps it. Normalize to UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _condition_met(condition: dict | None, loyalty: int, safety: int) -> bool:
    if not condition:
        return True
    if "min_safety" in condition and safety < condition["min_safety"]:
        return False
    if "min_loyalty" in condition and loyalty < condition["min_loyalty"]:
        return False
    return True


def visible_choices(node: dict, loyalty: int, safety: int) -> list[dict]:
    return [c for c in node["choices"] if _condition_met(c.get("condition"), loyalty, safety)]


@dataclass
class StepResult:
    attempt: Attempt
    prev_node_id: str
    node: dict
    timed_out: bool
    loyalty_delta: int
    safety_delta: int


class ScenarioEngine:
    """Applies a single decision (or timeout) to an in-progress attempt.

    The engine is the sole place attempt state is mutated, so scoring rules
    stay in one auditable spot instead of being duplicated per endpoint.
    """

    def __init__(self, graph: dict):
        self.graph = graph
        self.nodes = graph["nodes"]

    def current_node(self, attempt: Attempt) -> dict:
        return self.nodes[attempt.current_node]

    def start(self, attempt: Attempt) -> Attempt:
        attempt.current_node = self.graph["start_node"]
        attempt.node_shown_at = datetime.now(timezone.utc)
        attempt.loyalty = 50
        attempt.safety = 50
        attempt.status = AttemptStatus.in_progress
        return attempt

    def apply_choice(self, attempt: Attempt, choice_id: str | None, now: datetime) -> StepResult:
        if attempt.status != AttemptStatus.in_progress:
            raise ValueError("attempt is already finished")

        prev_node_id = attempt.current_node
        node = self.current_node(attempt)
        elapsed = (_as_aware(now) - _as_aware(attempt.node_shown_at)).total_seconds()
        timed_out = choice_id is None or elapsed > node["timer_seconds"]

        if timed_out:
            effects = node["timeout"]["effects"]
            next_node_id = node["timeout"]["next_node"]
        else:
            choice = self._find_choice(node, choice_id)
            effects = choice["effects"]
            next_node_id = choice["next_node"]

        loyalty_delta = effects.get("loyalty", 0)
        safety_delta = effects.get("safety", 0)
        attempt.loyalty = _clamp(attempt.loyalty + loyalty_delta)
        attempt.safety = _clamp(attempt.safety + safety_delta)
        attempt.current_node = next_node_id
        attempt.node_shown_at = now

        next_node = self.nodes[next_node_id]
        if next_node.get("is_ending"):
            attempt.status = AttemptStatus.finished
            attempt.ending_summary = next_node["ending_summary"]
            attempt.finished_at = now

        return StepResult(
            attempt=attempt,
            prev_node_id=prev_node_id,
            node=next_node,
            timed_out=timed_out,
            loyalty_delta=loyalty_delta,
            safety_delta=safety_delta,
        )

    def _find_choice(self, node: dict, choice_id: str) -> dict:
        for choice in node["choices"]:
            if choice["id"] == choice_id:
                return choice
        raise ValueError(f"choice '{choice_id}' not found in node")

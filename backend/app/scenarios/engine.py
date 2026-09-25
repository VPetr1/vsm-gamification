from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.clock import as_aware
from app.models.models import Attempt, AttemptStatus
from app.scenarios.errors import ScenarioError


def _clamp(value: int) -> int:
    return max(0, min(100, value))


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
    step: int
    prev_node_id: str
    choice_id: str | None
    timed_out: bool
    next_node: str
    loyalty_delta: int
    safety_delta: int
    loyalty_after: int
    safety_after: int


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

    def start(self, attempt: Attempt, now: datetime) -> Attempt:
        attempt.current_node = self.graph["start_node"]
        attempt.step = 0
        attempt.node_shown_at = now
        attempt.loyalty = 50
        attempt.safety = 50
        attempt.status = AttemptStatus.in_progress
        return attempt

    def deadline(self, attempt: Attempt) -> datetime | None:
        if attempt.status != AttemptStatus.in_progress:
            return None
        timer = self.current_node(attempt).get("timer_seconds")
        if timer is None:
            return None
        return as_aware(attempt.node_shown_at) + timedelta(seconds=timer)

    def is_expired(self, attempt: Attempt, now: datetime) -> bool:
        deadline = self.deadline(attempt)
        return deadline is not None and as_aware(now) >= deadline

    def apply_choice(self, attempt: Attempt, choice_id: str | None, expected_step: int, now: datetime) -> StepResult:
        """A choice made at or after the deadline is ignored and the timeout branch applies."""
        self._ensure_in_progress(attempt)
        if expected_step != attempt.step:
            raise ScenarioError(
                "step_mismatch",
                f"expected step {expected_step}, but the attempt is at step {attempt.step}",
                current_step=attempt.step,
            )
        node = self.current_node(attempt)

        if self.is_expired(attempt, now):
            return self._apply_outcome(attempt, node["timeout"], now, choice_id=None, timed_out=True)

        if choice_id is None:
            if node.get("timer_seconds") is None:
                raise ScenarioError("choice_required", "this step has no timer; a choice_id is required")
            raise ScenarioError(
                "timer_not_expired",
                "timeout requested before the deadline",
                deadline=self.deadline(attempt).isoformat(),
            )

        choice = self._find_visible_choice(node, choice_id, attempt)
        return self._apply_outcome(attempt, choice, now, choice_id=choice["id"], timed_out=False)

    def expire_if_due(self, attempt: Attempt, now: datetime) -> StepResult | None:
        """Apply the timeout branch for an attempt whose deadline passed while nobody was answering."""
        if not self.is_expired(attempt, now):
            return None
        return self._apply_outcome(attempt, self.current_node(attempt)["timeout"], now, choice_id=None, timed_out=True)

    def _ensure_in_progress(self, attempt: Attempt) -> None:
        if attempt.status != AttemptStatus.in_progress:
            raise ScenarioError("attempt_finished", "attempt is already finished")

    def _find_visible_choice(self, node: dict, choice_id: str, attempt: Attempt) -> dict:
        # Hidden and unknown choices share one error so the response does not leak hidden branches.
        for choice in visible_choices(node, attempt.loyalty, attempt.safety):
            if choice["id"] == choice_id:
                return choice
        raise ScenarioError("choice_not_available", f"choice '{choice_id}' is not available")

    def _apply_outcome(
        self, attempt: Attempt, outcome: dict, now: datetime, choice_id: str | None, timed_out: bool
    ) -> StepResult:
        prev_node_id = attempt.current_node
        effects = outcome.get("effects", {})
        old_loyalty, old_safety = attempt.loyalty, attempt.safety

        attempt.loyalty = _clamp(old_loyalty + effects.get("loyalty", 0))
        attempt.safety = _clamp(old_safety + effects.get("safety", 0))
        attempt.current_node = outcome["next_node"]
        attempt.step += 1
        attempt.node_shown_at = now

        next_node = self.nodes[attempt.current_node]
        if next_node.get("is_ending"):
            attempt.status = AttemptStatus.finished
            attempt.ending_summary = next_node["ending_summary"]
            attempt.finished_at = now

        return StepResult(
            step=attempt.step,
            prev_node_id=prev_node_id,
            choice_id=choice_id,
            timed_out=timed_out,
            next_node=attempt.current_node,
            loyalty_delta=attempt.loyalty - old_loyalty,
            safety_delta=attempt.safety - old_safety,
            loyalty_after=attempt.loyalty,
            safety_after=attempt.safety,
        )

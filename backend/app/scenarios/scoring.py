"""Attempt score relative to what the scenario allows: the best reachable ending scores 100, the worst 0.

The raw score is the mean of the two scales at the ending. score_range explores every reachable
state (node, scales, flags) - choices visible in that state plus the timeout branch - so hidden
choices never inflate the best, and loops terminate because each state is visited once.
Formulas are documented in docs/scoring.md; keep the two in sync.
"""

from collections import deque
from dataclasses import dataclass

from app.scenarios.conditions import evaluate

MAX_STATES = 200_000
DEFAULT_INITIAL = {"loyalty": 50, "safety": 50}


class ScenarioTooLarge(ValueError):
    pass


@dataclass(frozen=True)
class ScoreRange:
    worst: int
    best: int


@dataclass(frozen=True)
class _State:
    node: str
    loyalty: int
    safety: int
    flag_items: tuple

    @property
    def flags(self) -> dict:
        return dict(self.flag_items)


def raw_score(loyalty: int, safety: int) -> int:
    return (loyalty + safety + 1) // 2  # halves round up; Python's round() would round 57.5 and 42.5 differently


def normalized_score(raw: int, rng: ScoreRange) -> int:
    span = rng.best - rng.worst
    if span <= 0:
        return 100
    clamped = max(rng.worst, min(rng.best, raw))
    return (200 * (clamped - rng.worst) + span) // (2 * span)  # halves round up


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _step(state: _State, outcome: dict) -> _State:
    effects = outcome.get("effects", {})
    flags = {**state.flags, **outcome.get("set_flags", {})}
    after = _State("", _clamp(state.loyalty + effects.get("loyalty", 0)),
                   _clamp(state.safety + effects.get("safety", 0)), tuple(sorted(flags.items())))
    if "next_node" in outcome:
        target = outcome["next_node"]
    else:
        target = next(t["next_node"] for t in outcome["transitions"] if evaluate(t.get("condition"), after))
    return _State(target, after.loyalty, after.safety, after.flag_items)


def score_range(graph: dict) -> ScoreRange:
    """Raises ScenarioTooLarge when more than MAX_STATES states are reachable."""
    initial = {**DEFAULT_INITIAL, **graph.get("initial", {})}
    nodes = graph["nodes"]
    start = _State(graph["start_node"], initial["loyalty"], initial["safety"],
                   tuple(sorted(graph.get("flags", {}).items())))
    seen, queue, raws = {start}, deque([start]), []
    while queue:
        state = queue.popleft()
        node = nodes[state.node]
        if node.get("is_ending"):
            raws.append(raw_score(state.loyalty, state.safety))
            continue
        outcomes = [c for c in node["choices"] if evaluate(c.get("condition"), state)]
        if "timeout" in node:
            outcomes.append(node["timeout"])
        for outcome in outcomes:
            nxt = _step(state, outcome)
            if nxt not in seen:
                if len(seen) >= MAX_STATES:
                    raise ScenarioTooLarge(f"more than {MAX_STATES} reachable states")
                seen.add(nxt)
                queue.append(nxt)
    return ScoreRange(worst=min(raws), best=max(raws))


def attempt_score(graph: dict, loyalty: int, safety: int) -> int:
    return normalized_score(raw_score(loyalty, safety), score_range(graph))

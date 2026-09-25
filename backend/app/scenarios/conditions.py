"""Declarative conditions over attempt state. Plain JSON data, interpreted here; never eval'd.

Forms (exactly one key per object):
  {"flag": "promised_upgrade"}                         flag is true
  {"scale": "loyalty", "op": ">=", "value": 70}        scale comparison
  {"all": [cond, ...]}   {"any": [cond, ...]}   {"not": cond}
  {"min_loyalty": 40}    {"min_safety": 40}             legacy shorthand for "scale >= value"
"""

import operator
from typing import Protocol

SCALES = ("loyalty", "safety")
OPERATORS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}
LEGACY_MIN = {"min_loyalty": "loyalty", "min_safety": "safety"}


class State(Protocol):
    loyalty: int
    safety: int
    flags: dict


def _scale(state: State, name: str) -> int:
    return state.loyalty if name == "loyalty" else state.safety


def evaluate(condition: dict | None, state: State) -> bool:
    if condition is None:
        return True
    if "all" in condition:
        return all(evaluate(c, state) for c in condition["all"])
    if "any" in condition:
        return any(evaluate(c, state) for c in condition["any"])
    if "not" in condition:
        return not evaluate(condition["not"], state)
    if "flag" in condition:
        return bool((state.flags or {}).get(condition["flag"], False))
    if "scale" in condition:
        return OPERATORS[condition["op"]](_scale(state, condition["scale"]), condition["value"])
    for key, scale in LEGACY_MIN.items():
        if key in condition:
            return _scale(state, scale) >= condition[key]
    raise ValueError(f"unknown condition form: {sorted(condition)}")

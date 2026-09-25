from types import SimpleNamespace

import pytest

from app.scenarios.conditions import evaluate


def state(loyalty=50, safety=50, **flags):
    return SimpleNamespace(loyalty=loyalty, safety=safety, flags=flags)


def test_missing_condition_is_true():
    assert evaluate(None, state()) is True


def test_flag_condition_defaults_to_false_for_unset_flags():
    assert evaluate({"flag": "was_rude"}, state(was_rude=True)) is True
    assert evaluate({"flag": "was_rude"}, state()) is False


@pytest.mark.parametrize(
    "op, value, expected",
    [(">=", 70, True), (">", 70, False), ("<=", 70, True), ("<", 70, False), ("==", 70, True), ("!=", 70, False)],
)
def test_scale_comparisons(op, value, expected):
    assert evaluate({"scale": "loyalty", "op": op, "value": value}, state(loyalty=70)) is expected


def test_combinators():
    s = state(loyalty=65, safety=90, was_rude=False, promised_upgrade=True)
    assert evaluate({"all": [{"flag": "promised_upgrade"}, {"scale": "safety", "op": ">=", "value": 80}]}, s)
    assert evaluate({"any": [{"flag": "was_rude"}, {"scale": "loyalty", "op": "<", "value": 70}]}, s)
    assert not evaluate({"not": {"flag": "promised_upgrade"}}, s)


def test_legacy_min_shorthand():
    assert evaluate({"min_safety": 40}, state(safety=40)) is True
    assert evaluate({"min_loyalty": 41}, state(loyalty=40)) is False

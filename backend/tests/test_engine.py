from datetime import datetime, timedelta, timezone

import pytest

from app.models.models import Attempt, AttemptStatus
from app.scenarios.demo_scenario import DEMO_SCENARIO
from app.scenarios.engine import ScenarioEngine
from app.scenarios.validator import ScenarioValidationError, validate_graph


def make_attempt(graph: dict) -> Attempt:
    attempt = Attempt(employee_id="e1", scenario_id="s1", current_node="")
    ScenarioEngine(graph).start(attempt)
    return attempt


def test_demo_scenario_is_valid():
    validate_graph(DEMO_SCENARIO["graph"])


def test_start_sets_start_node_and_default_scales():
    attempt = make_attempt(DEMO_SCENARIO["graph"])
    assert attempt.current_node == "n1"
    assert attempt.loyalty == 50
    assert attempt.safety == 50


def test_good_choice_increases_both_scales_and_ends_scenario():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    result = engine.apply_choice(attempt, "c1", attempt.node_shown_at + timedelta(seconds=5))

    assert attempt.status == AttemptStatus.finished
    assert attempt.loyalty == 60
    assert attempt.safety == 55
    assert result.node["is_ending"] is True
    assert attempt.ending_summary


def test_timeout_applies_timeout_effects_not_any_choice():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    result = engine.apply_choice(attempt, None, attempt.node_shown_at + timedelta(seconds=999))

    assert result.timed_out is True
    assert attempt.current_node == "n2_escalation"
    assert attempt.loyalty == 40
    assert attempt.safety == 45


def test_choosing_after_timer_expired_counts_as_timeout_even_with_choice_id():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    result = engine.apply_choice(attempt, "c1", attempt.node_shown_at + timedelta(seconds=25))

    assert result.timed_out is True
    assert attempt.current_node == "n2_escalation"


def test_scales_are_clamped_to_0_100():
    graph = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "text": "x",
                "timer_seconds": 10,
                "timeout": {"effects": {}, "next_node": "n1"},
                "choices": [
                    {"id": "c1", "text": "x", "effects": {"loyalty": 1000, "safety": -1000}, "next_node": "end"}
                ],
            },
            "end": {"text": "x", "is_ending": True, "ending_summary": "x"},
        },
    }
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)
    engine.apply_choice(attempt, "c1", attempt.node_shown_at + timedelta(seconds=1))

    assert attempt.loyalty == 100
    assert attempt.safety == 0


def test_apply_choice_on_finished_attempt_raises():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)
    engine.apply_choice(attempt, "c1", attempt.node_shown_at + timedelta(seconds=1))

    with pytest.raises(ValueError):
        engine.apply_choice(attempt, "c1", datetime.now(timezone.utc))


def test_unknown_choice_id_raises():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    with pytest.raises(ValueError):
        engine.apply_choice(attempt, "does-not-exist", attempt.node_shown_at + timedelta(seconds=1))


def test_choice_hidden_by_condition_cannot_be_submitted_by_id():
    graph = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "text": "x",
                "timer_seconds": 10,
                "timeout": {"effects": {}, "next_node": "end"},
                "choices": [
                    {"id": "open", "text": "x", "effects": {}, "next_node": "end"},
                    {
                        "id": "gated",
                        "text": "x",
                        "condition": {"min_safety": 90},
                        "effects": {"loyalty": 50},
                        "next_node": "end",
                    },
                ],
            },
            "end": {"text": "x", "is_ending": True, "ending_summary": "x"},
        },
    }
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    with pytest.raises(ValueError):
        engine.apply_choice(attempt, "gated", attempt.node_shown_at + timedelta(seconds=1))
    assert attempt.loyalty == 50
    assert attempt.current_node == "n1"


def test_validator_rejects_missing_start_node():
    with pytest.raises(ScenarioValidationError):
        validate_graph({"start_node": "missing", "nodes": {}})


def test_validator_rejects_dangling_next_node():
    graph = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "text": "x",
                "timer_seconds": 10,
                "timeout": {"effects": {}, "next_node": "n1"},
                "choices": [{"id": "c1", "text": "x", "effects": {}, "next_node": "ghost"}],
            }
        },
    }
    with pytest.raises(ScenarioValidationError):
        validate_graph(graph)


def test_validator_rejects_ending_node_without_summary():
    graph = {"start_node": "n1", "nodes": {"n1": {"text": "x", "is_ending": True}}}
    with pytest.raises(ScenarioValidationError):
        validate_graph(graph)

from datetime import datetime, timedelta, timezone

import pytest

from app.models.models import Attempt, AttemptStatus
from app.scenarios.demo_scenario import DEMO_SCENARIO
from app.scenarios.engine import ScenarioEngine, visible_choices
from app.scenarios.errors import ScenarioError
from app.scenarios.validator import ScenarioValidationError, validate_graph


T0 = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)


def make_attempt(graph: dict) -> Attempt:
    attempt = Attempt(employee_id="e1", scenario_id="s1", current_node="")
    ScenarioEngine(graph).start(attempt, T0)
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

    result = engine.apply_choice(attempt, "c1", attempt.step, attempt.node_shown_at + timedelta(seconds=5))

    assert attempt.status == AttemptStatus.finished
    assert attempt.loyalty == 60
    assert attempt.safety == 55
    assert result.timed_out is False
    assert attempt.current_node == "n2_resolved"
    assert attempt.ending_summary


def test_timeout_applies_timeout_effects_not_any_choice():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    result = engine.apply_choice(attempt, None, attempt.step, attempt.node_shown_at + timedelta(seconds=999))

    assert result.timed_out is True
    assert attempt.current_node == "n2_escalation"
    assert attempt.loyalty == 40
    assert attempt.safety == 45


def test_choosing_after_timer_expired_counts_as_timeout_even_with_choice_id():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    result = engine.apply_choice(attempt, "c1", attempt.step, attempt.node_shown_at + timedelta(seconds=25))

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
    engine.apply_choice(attempt, "c1", attempt.step, attempt.node_shown_at + timedelta(seconds=1))

    assert attempt.loyalty == 100
    assert attempt.safety == 0


def test_apply_choice_on_finished_attempt_raises():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)
    engine.apply_choice(attempt, "c1", attempt.step, attempt.node_shown_at + timedelta(seconds=1))

    with pytest.raises(ScenarioError):
        engine.apply_choice(attempt, "c1", attempt.step, datetime.now(timezone.utc))


def test_unknown_choice_id_raises():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    with pytest.raises(ScenarioError):
        engine.apply_choice(attempt, "does-not-exist", attempt.step, attempt.node_shown_at + timedelta(seconds=1))


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

    with pytest.raises(ScenarioError):
        engine.apply_choice(attempt, "gated", attempt.step, attempt.node_shown_at + timedelta(seconds=1))
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


def test_null_choice_before_deadline_is_rejected_and_state_unchanged():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    engine = ScenarioEngine(graph)

    with pytest.raises(ScenarioError) as exc:
        engine.apply_choice(attempt, None, attempt.step, T0 + timedelta(seconds=19, microseconds=999_999))

    assert exc.value.code == "timer_not_expired"
    assert (attempt.current_node, attempt.loyalty, attempt.safety) == ("n1", 50, 50)


def test_deadline_boundary_is_inclusive():
    graph = DEMO_SCENARIO["graph"]
    engine = ScenarioEngine(graph)

    just_before = make_attempt(graph)
    result = engine.apply_choice(just_before, "c1", just_before.step, T0 + timedelta(seconds=20) - timedelta(microseconds=1))
    assert result.timed_out is False

    exactly_at = make_attempt(graph)
    result = engine.apply_choice(exactly_at, "c1", exactly_at.step, T0 + timedelta(seconds=20))
    assert result.timed_out is True
    assert result.choice_id is None
    assert exactly_at.current_node == "n2_escalation"


def test_deadline_is_node_shown_at_plus_timer():
    graph = DEMO_SCENARIO["graph"]
    attempt = make_attempt(graph)
    assert ScenarioEngine(graph).deadline(attempt) == T0 + timedelta(seconds=20)


def test_expire_if_due_applies_timeout_only_after_deadline():
    graph = DEMO_SCENARIO["graph"]
    engine = ScenarioEngine(graph)
    attempt = make_attempt(graph)

    assert engine.expire_if_due(attempt, T0 + timedelta(seconds=5)) is None
    assert attempt.current_node == "n1"

    result = engine.expire_if_due(attempt, T0 + timedelta(minutes=10))
    assert result.timed_out is True
    assert attempt.current_node == "n2_escalation"
    assert engine.expire_if_due(attempt, T0 + timedelta(minutes=20)) is None


def test_logged_deltas_are_actual_changes_after_clamping():
    graph = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "text": "x",
                "timer_seconds": 10,
                "timeout": {"effects": {}, "next_node": "end"},
                "choices": [{"id": "c1", "text": "x", "effects": {"loyalty": 80, "safety": -80}, "next_node": "end"}],
            },
            "end": {"text": "x", "is_ending": True, "ending_summary": "x"},
        },
    }
    attempt = make_attempt(graph)
    result = ScenarioEngine(graph).apply_choice(attempt, "c1", attempt.step, T0 + timedelta(seconds=1))
    assert (result.loyalty_delta, result.safety_delta) == (50, -50)


def test_steps_increment_and_stale_expected_step_is_rejected():
    graph = DEMO_SCENARIO["graph"]
    engine = ScenarioEngine(graph)
    attempt = make_attempt(graph)
    assert attempt.step == 0

    with pytest.raises(ScenarioError) as exc:
        engine.apply_choice(attempt, "c1", 3, T0 + timedelta(seconds=1))
    assert exc.value.code == "step_mismatch"
    assert exc.value.extra == {"current_step": 0}
    assert (attempt.step, attempt.current_node) == (0, "n1")

    result = engine.apply_choice(attempt, "c1", 0, T0 + timedelta(seconds=1))
    assert result.step == attempt.step == 1
    assert (result.prev_node_id, result.next_node) == ("n1", "n2_resolved")
    assert (result.loyalty_after, result.safety_after) == (60, 55)


V2_GRAPH = {
    "initial": {"loyalty": 60, "safety": 80},
    "flags": {"was_rude": False},
    "start_node": "talk",
    "nodes": {
        "talk": {
            "text": "no timer here",
            "choices": [
                {"id": "polite", "text": "x", "effects": {"loyalty": 5}, "next_node": "decide"},
                {"id": "rude", "text": "x", "effects": {"loyalty": -5}, "set_flags": {"was_rude": True}, "next_node": "decide"},
            ],
        },
        "decide": {
            "text": "x",
            "choices": [
                {
                    "id": "go",
                    "text": "x",
                    "effects": {"loyalty": 5},
                    "transitions": [
                        {"condition": {"flag": "was_rude"}, "next_node": "bad"},
                        {"condition": {"scale": "loyalty", "op": ">=", "value": 70}, "next_node": "good"},
                        {"next_node": "meh"},
                    ],
                },
                {
                    "id": "secret",
                    "text": "x",
                    "condition": {"not": {"flag": "was_rude"}},
                    "effects": {"loyalty": 20},
                    "next_node": "good",
                },
            ],
        },
        "good": {"text": "x", "is_ending": True, "ending_summary": "good"},
        "meh": {"text": "x", "is_ending": True, "ending_summary": "meh"},
        "bad": {"text": "x", "is_ending": True, "ending_summary": "bad"},
    },
}


def _play(graph, *choice_ids):
    engine = ScenarioEngine(graph)
    attempt = make_attempt(graph)
    for choice_id in choice_ids:
        engine.apply_choice(attempt, choice_id, attempt.step, T0 + timedelta(seconds=1))
    return attempt


def test_initial_scales_and_flags_come_from_the_scenario():
    attempt = make_attempt(V2_GRAPH)
    assert (attempt.loyalty, attempt.safety, attempt.flags) == (60, 80, {"was_rude": False})


def test_old_graph_without_initial_starts_at_50_50_with_no_flags():
    attempt = make_attempt(DEMO_SCENARIO["graph"])
    assert (attempt.loyalty, attempt.safety, attempt.flags) == (50, 50, {})


def test_action_sets_flag_and_flag_routes_transition():
    attempt = _play(V2_GRAPH, "rude", "go")
    assert attempt.flags == {"was_rude": True}
    assert attempt.current_node == "bad"


def test_transition_threshold_is_checked_after_the_choice_effects():
    # polite: 60+5=65; go: 65+5=70 -> the ">= 70" branch only matches after go's own effect.
    assert _play(V2_GRAPH, "polite", "go").current_node == "good"


def test_default_transition_when_no_condition_matches():
    graph = {**V2_GRAPH, "initial": {"loyalty": 50, "safety": 80}}
    assert _play(graph, "polite", "go").current_node == "meh"


def test_previous_action_hides_a_later_choice():
    engine = ScenarioEngine(V2_GRAPH)
    attempt = _play(V2_GRAPH, "rude")
    assert [c["id"] for c in visible_choices(V2_GRAPH["nodes"]["decide"], attempt)] == ["go"]
    with pytest.raises(ScenarioError) as exc:
        engine.apply_choice(attempt, "secret", attempt.step, T0 + timedelta(seconds=2))
    assert exc.value.code == "choice_not_available"


def test_node_without_timer_has_no_deadline_and_requires_a_choice():
    engine = ScenarioEngine(V2_GRAPH)
    attempt = make_attempt(V2_GRAPH)
    assert engine.deadline(attempt) is None
    assert engine.expire_if_due(attempt, T0 + timedelta(days=1)) is None
    with pytest.raises(ScenarioError) as exc:
        engine.apply_choice(attempt, None, 0, T0 + timedelta(days=1))
    assert exc.value.code == "choice_required"

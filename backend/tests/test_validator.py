import copy

import pytest

from app.scenarios.demo_scenario import DEMO_SCENARIO
from app.scenarios.validator import ScenarioValidationError, collect_errors, validate_graph
from tests.test_engine import V2_GRAPH


def graph(**patch):
    """A small valid v2 graph; keyword args replace top-level keys."""
    g = copy.deepcopy(V2_GRAPH)
    g.update(patch)
    return g


def errors_for(g) -> str:
    return "\n".join(collect_errors(g))


def test_bundled_graphs_are_valid():
    validate_graph(DEMO_SCENARIO["graph"])
    validate_graph(V2_GRAPH)


@pytest.mark.parametrize("bad", [None, [], "x", 42])
def test_non_object_graph(bad):
    assert collect_errors(bad) == ["graph: must be an object"]


@pytest.mark.parametrize("nodes", [[], {}, "n1", None])
def test_nodes_must_be_a_non_empty_object_without_crashing(nodes):
    assert "graph.nodes: must be a non-empty object" in errors_for(graph(nodes=nodes))


def test_missing_start_node():
    assert "graph.start_node: must name an existing node" in errors_for(graph(start_node="ghost"))


def test_node_must_be_an_object():
    g = graph()
    g["nodes"]["talk"] = ["not", "a", "node"]
    assert "nodes.talk: must be an object" in errors_for(g)


def test_required_fields_and_types_are_reported_together():
    g = graph()
    choice = g["nodes"]["talk"]["choices"][0]
    del choice["id"]
    choice["text"] = ""
    choice["effects"] = {"loyalty": "5", "safety": True}
    err = collect_errors(g)
    assert "nodes.talk.choices[0].id: must be a non-empty string" in err
    assert "nodes.talk.choices[0].text: must be a non-empty string" in err
    assert "nodes.talk.choices[0].effects.loyalty: must be an integer -100..100" in err
    assert "nodes.talk.choices[0].effects.safety: must be an integer -100..100" in err


def test_effect_out_of_range_and_unknown_scale():
    g = graph()
    g["nodes"]["talk"]["choices"][0]["effects"] = {"loyalty": 500, "mood": 1}
    err = errors_for(g)
    assert "effects.loyalty: must be an integer -100..100" in err
    assert "effects.mood: unknown field" in err


def test_duplicate_choice_ids_in_one_node():
    g = graph()
    g["nodes"]["talk"]["choices"][1]["id"] = "polite"
    assert "choices[1].id: duplicate choice id 'polite'" in errors_for(g)


@pytest.mark.parametrize("timer", [0, 4, 601, "20", 20.5, True])
def test_bad_timer_values(timer):
    g = graph()
    g["nodes"]["talk"]["timer_seconds"] = timer
    g["nodes"]["talk"]["timeout"] = {"next_node": "decide"}
    assert "nodes.talk.timer_seconds: must be an integer 5..600 or null" in errors_for(g)


def test_timer_requires_timeout_and_timeout_requires_timer():
    g = graph()
    g["nodes"]["talk"]["timer_seconds"] = 20
    g["nodes"]["decide"]["timeout"] = {"next_node": "good"}
    err = errors_for(g)
    assert "nodes.talk.timeout: required when the node has a timer" in err
    assert "nodes.decide.timeout: allowed only together with timer_seconds" in err


def test_timeout_without_effects_is_valid():
    g = graph()
    g["nodes"]["talk"]["timer_seconds"] = 20
    g["nodes"]["talk"]["timeout"] = {"next_node": "decide"}
    assert collect_errors(g) == []


def test_unknown_field_catches_typos():
    g = graph()
    g["nodes"]["talk"]["choices"][0]["next_nod"] = "decide"
    assert "nodes.talk.choices[0].next_nod: unknown field" in errors_for(g)


def test_unknown_flags_in_set_flags_and_conditions():
    g = graph()
    g["nodes"]["talk"]["choices"][0]["set_flags"] = {"wasrude": True}
    g["nodes"]["decide"]["choices"][1]["condition"] = {"flag": "promised"}
    err = errors_for(g)
    assert "set_flags.wasrude: unknown flag" in err
    assert "condition.flag: unknown flag 'promised'" in err


@pytest.mark.parametrize(
    "condition, message",
    [
        ({"scale": "mood", "op": ">=", "value": 5}, "condition.scale: must be one of"),
        ({"scale": "loyalty", "op": "=>", "value": 5}, "condition.op: must be one of"),
        ({"scale": "loyalty", "op": ">=", "value": 150}, "condition.value: must be an integer 0..100"),
        ({"all": []}, "condition.all: must be a non-empty list"),
        ({"flag": "was_rude", "not": {}}, "unknown condition form"),
        ({"python": "__import__('os')"}, "unknown condition form"),
        ({}, "condition: must be a non-empty object"),
    ],
)
def test_bad_conditions(condition, message):
    g = graph()
    g["nodes"]["decide"]["choices"][1]["condition"] = condition
    assert message in errors_for(g)


def test_deeply_nested_condition_is_rejected_not_crashing():
    cond = {"flag": "was_rude"}
    for _ in range(2000):
        cond = {"not": cond}
    g = graph()
    g["nodes"]["decide"]["choices"][1]["condition"] = cond
    assert "nested deeper than 8 levels" in errors_for(g)


def test_transitions_need_a_single_unconditional_default_at_the_end():
    g = graph()
    transitions = g["nodes"]["decide"]["choices"][0]["transitions"]
    transitions[-1]["condition"] = {"flag": "was_rude"}
    transitions.insert(0, {"next_node": "meh"})
    err = errors_for(g)
    assert "transitions[0]: only the last transition may omit condition" in err
    assert "transitions[3].condition: the last transition is the default" in err


def test_next_node_and_transitions_are_mutually_exclusive():
    g = graph()
    g["nodes"]["decide"]["choices"][0]["next_node"] = "good"
    assert "nodes.decide.choices[0]: needs exactly one of next_node or transitions" in errors_for(g)


def test_dangling_target():
    g = graph()
    g["nodes"]["talk"]["choices"][0]["next_node"] = "ghost"
    assert "nodes.talk.choices[0].next_node: points to unknown node 'ghost'" in errors_for(g)


def test_all_conditional_choices_would_strand_the_player():
    g = graph()
    for choice in g["nodes"]["talk"]["choices"]:
        choice["condition"] = {"flag": "was_rude"}
    assert "nodes.talk.choices: at least one choice must have no condition" in errors_for(g)


def test_unreachable_node():
    g = graph()
    g["nodes"]["orphan"] = {"text": "x", "is_ending": True, "ending_summary": "x"}
    assert "nodes.orphan: unreachable from start_node" in errors_for(g)


def test_loop_without_way_out_cannot_reach_an_ending():
    g = graph()
    g["nodes"]["talk"]["choices"] = [{"id": "again", "text": "x", "next_node": "loop"}]
    g["nodes"]["loop"] = {"text": "x", "choices": [{"id": "back", "text": "x", "next_node": "talk"}]}
    err = errors_for(g)
    assert "nodes.talk: no path from this node to any ending" in err
    assert "nodes.loop: no path from this node to any ending" in err


def test_graph_without_endings():
    g = graph(start_node="a", nodes={"a": {"text": "x", "choices": [{"id": "c", "text": "x", "next_node": "a"}]}})
    assert "at least one ending node" in errors_for(g)


def test_initial_and_flag_declarations_are_typed():
    err = errors_for(graph(initial={"loyalty": 120, "safety": "80"}, flags={"was_rude": "no"}))
    assert "graph.initial.loyalty: must be an integer 0..100" in err
    assert "graph.initial.safety: must be an integer 0..100" in err
    assert "graph.flags.was_rude: default must be true or false" in err


def test_validate_graph_raises_with_all_errors():
    g = graph(start_node="ghost")
    g["nodes"]["talk"]["choices"][0]["effects"] = {"loyalty": "x"}
    with pytest.raises(ScenarioValidationError) as exc:
        validate_graph(g)
    assert len(exc.value.errors) == 2


def test_api_returns_readable_422(client):
    g = graph()
    g["nodes"]["talk"]["choices"][0]["next_node"] = "ghost"
    r = client.post("/scenarios", json={"title": "broken", "graph": g})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["code"] == "invalid_scenario"
    assert detail["errors"] == ["nodes.talk.choices[0].next_node: points to unknown node 'ghost'"]

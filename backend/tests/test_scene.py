"""Scene metadata: roles, poses, positions, who is on stage, props, background."""

from types import SimpleNamespace

import pytest

from app.scenarios.validator import collect_errors
from app.scenarios.visual import resolve


def state(loyalty=60, safety=60, **flags):
    return SimpleNamespace(loyalty=loyalty, safety=safety, flags=flags)


GRAPH = {
    "flags": {"called": False},
    "visual": {
        "background": "business",
        "characters": {
            "sick": {"name": "Пассажирка", "figure": "elderly", "gender": "f", "color": "purple", "pose": "sitting", "position": "left"},
            "chief": {"name": "Начальник поезда", "figure": "chief", "gender": "m", "pose": "standing", "position": "far_right"},
            "kid": {"name": "Ребёнок", "figure": "child"},
        },
    },
}


def test_without_cast_every_character_is_present_with_defaults():
    visual = resolve(GRAPH, {"text": "x"}, state())
    assert visual["background"] == "business"
    by_id = {c["id"]: c for c in visual["characters"]}
    assert set(by_id) == {"sick", "chief", "kid"}
    assert (by_id["sick"]["figure"], by_id["sick"]["gender"], by_id["sick"]["color"]) == ("elderly", "f", "purple")
    assert (by_id["kid"]["pose"], by_id["kid"]["position"], by_id["kid"]["gender"], by_id["kid"]["color"]) == ("standing", "center", "n", None)


def test_cast_limits_who_is_on_stage_and_overrides_pose_and_position():
    node = {"text": "x", "visual": {"background": "vestibule", "cast": [
        {"character": "sick", "pose": "unwell"},
        {"character": "chief", "position": "right", "when": {"flag": "called"}},
    ]}}
    alone = resolve(GRAPH, node, state())
    assert [(c["id"], c["pose"], c["position"]) for c in alone["characters"]] == [("sick", "unwell", "left")]
    assert alone["background"] == "vestibule"
    helped = resolve(GRAPH, node, state(called=True))
    assert [(c["id"], c["position"]) for c in helped["characters"]] == [("sick", "left"), ("chief", "right")]


def test_first_matching_cast_rule_wins():
    node = {"text": "x", "visual": {"cast": [
        {"character": "sick", "pose": "unwell", "when": {"flag": "called"}},
        {"character": "sick", "pose": "sitting"},
    ]}}
    assert resolve(GRAPH, node, state())["characters"][0]["pose"] == "sitting"
    assert resolve(GRAPH, node, state(called=True))["characters"][0]["pose"] == "unwell"


def test_new_props_resolve():
    node = {"text": "x", "visual": {"props": [{"id": "first_aid_kit"}, {"id": "water", "when": {"flag": "called"}}, {"id": "stroller"}]}}
    assert resolve(GRAPH, node, state())["props"] == ["first_aid_kit", "stroller"]


def _graph_with(visual_graph=None, node_visual=None):
    graph = {
        "start_node": "a",
        "flags": {"called": False},
        "visual": visual_graph if visual_graph is not None else GRAPH["visual"],
        "nodes": {
            "a": {"text": "x", "choices": [{"id": "c", "text": "x", "next_node": "e"}]},
            "e": {"text": "x", "is_ending": True, "ending_summary": "x"},
        },
    }
    if node_visual is not None:
        graph["nodes"]["a"]["visual"] = node_visual
    return graph


def test_valid_scene_passes():
    node_visual = {"background": "standard", "cast": [{"character": "sick", "pose": "pointing", "position": "far_left", "when": {"flag": "called"}}],
                   "props": [{"id": "phone"}, {"id": "bag"}]}
    assert collect_errors(_graph_with(node_visual=node_visual)) == []


@pytest.mark.parametrize(
    ("graph", "error"),
    [
        (_graph_with({"characters": {"x": {"figure": "robot"}}}), "graph.visual.characters.x.figure"),
        (_graph_with({"characters": {"x": {"gender": "x"}}}), "graph.visual.characters.x.gender"),
        (_graph_with({"characters": {"x": {"color": "gold"}}}), "graph.visual.characters.x.color"),
        (_graph_with({"characters": {"x": {"pose": "flying"}}}), "graph.visual.characters.x.pose"),
        (_graph_with({"background": "space", "characters": {}}), "graph.visual.background"),
        (_graph_with(node_visual={"background": "space"}), "nodes.a.visual.background"),
        (_graph_with(node_visual={"cast": [{"character": "ghost"}]}), "nodes.a.visual.cast[0].character"),
        (_graph_with(node_visual={"cast": [{"character": "sick", "pose": "flying"}]}), "nodes.a.visual.cast[0].pose"),
        (_graph_with(node_visual={"cast": [{"character": "sick", "position": "roof"}]}), "nodes.a.visual.cast[0].position"),
        (_graph_with(node_visual={"cast": [{"character": "sick", "when": {"flag": "nope"}}]}), "nodes.a.visual.cast[0].when.flag"),
        (_graph_with(node_visual={"cast": "sick"}), "nodes.a.visual.cast"),
    ],
)
def test_invalid_scene_is_rejected(graph, error):
    errors = collect_errors(graph)
    assert any(e.startswith(error) for e in errors), errors

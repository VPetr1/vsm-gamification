"""An ending type the methodologist names: outcome "custom" with its own label and tone."""

import copy

import pytest

from app.scenarios.library import load_scenario
from app.scenarios.validator import collect_errors
from tests.test_gamification import play, publish  # noqa: F401  (publish is a fixture)

DEMO = load_scenario("seat_recline")


def _custom_demo(**ending) -> dict:
    data = copy.deepcopy(DEMO)
    data["graph"]["nodes"]["n2_resolved"].update(
        {"outcome": "custom", "outcome_label": "Пассажир благодарит", "outcome_tone": "good", **ending}
    )
    return data


def test_result_and_history_carry_the_custom_label_and_tone(login_as, publish, clock):  # noqa: F811
    anna = login_as("anna")
    sid = publish(_custom_demo())
    state = play(anna, clock, sid, "c1")
    ending = anna.get(f"/attempts/{state['attempt_id']}/result").json()["ending"]
    assert (ending["outcome"], ending["outcome_label"], ending["outcome_tone"]) == ("custom", "Пассажир благодарит", "good")
    history = anna.get("/me/attempts").json()[0]
    assert (history["outcome_label"], history["outcome_tone"]) == ("Пассажир благодарит", "good")


def test_preset_outcomes_have_no_label():
    assert collect_errors(DEMO["graph"]) == []


@pytest.mark.parametrize(
    ("ending", "error"),
    [
        ({"outcome_label": " "}, "nodes.n2_resolved.outcome_label"),
        ({"outcome_tone": "purple"}, "nodes.n2_resolved.outcome_tone"),
        ({"outcome_label": None}, "nodes.n2_resolved.outcome_label"),
    ],
)
def test_validator_checks_custom_endings(ending, error):
    data = _custom_demo()
    node = data["graph"]["nodes"]["n2_resolved"]
    for key, value in ending.items():
        if value is None:
            node.pop(key)
        else:
            node[key] = value
    assert any(e.startswith(error) for e in collect_errors(data["graph"])), collect_errors(data["graph"])

"""Competency scores: explicit data rules, only visible options count, latest attempt per scenario."""

from datetime import timedelta

import pytest

from app.scenarios.engine import ScenarioEngine
from app.scenarios.library import load_scenario
from tests.test_engine import T0, make_attempt
from tests.test_gamification import play

DEMO = load_scenario("seat_recline")
WINDOW = load_scenario("window_seat")


def by_id(items):
    return {i["id"]: i for i in items}


GATED = {
    "flags": {"trained": False},
    "start_node": "n1",
    "nodes": {
        "n1": {
            "text": "x",
            "timer_seconds": 10,
            "timeout": {"next_node": "end"},
            "choices": [
                {"id": "ok", "text": "x", "assessment": {"communication": 1}, "next_node": "end"},
                {"id": "expert", "text": "x", "condition": {"flag": "trained"}, "assessment": {"communication": 5}, "next_node": "end"},
            ],
        },
        "end": {"text": "x", "is_ending": True, "ending_summary": "x"},
    },
}


def test_maximum_counts_only_options_the_player_could_see():
    attempt = make_attempt(GATED)
    result = ScenarioEngine(GATED).apply_choice(attempt, "ok", 0, T0 + timedelta(seconds=1))
    assert result.assessment == {"communication": {"earned": 1, "max": 1}}


def test_visible_expert_option_raises_the_maximum():
    attempt = make_attempt(GATED)
    attempt.flags = {"trained": True}
    result = ScenarioEngine(GATED).apply_choice(attempt, "ok", 0, T0 + timedelta(seconds=1))
    assert result.assessment == {"communication": {"earned": 1, "max": 5}}


def test_timeout_earns_nothing_against_the_best_visible_option():
    attempt = make_attempt(GATED)
    result = ScenarioEngine(GATED).apply_choice(attempt, None, 0, T0 + timedelta(seconds=10))
    assert result.assessment == {"communication": {"earned": 0, "max": 1}}


@pytest.fixture()
def setup(login_as, metod):
    ids = {name: metod.post("/scenarios", json=data).json()["id"] for name, data in [("demo", DEMO), ("window", WINDOW)]}
    return login_as("anna"), ids


def test_result_totals_and_no_data_for_unassessed_competency(setup, clock):
    anna, ids = setup
    state = play(anna, clock, ids["window"], "calm", "stow_together", "check", "tactful", "escort")
    result = anna.get(f"/attempts/{state['attempt_id']}/result").json()
    totals = by_id(result["competencies"])
    assert (totals["communication"]["earned"], totals["communication"]["max"]) == (8, 8)
    assert (totals["safety"]["earned"], totals["safety"]["max"]) == (3, 3)
    assert (totals["stress_resistance"]["earned"], totals["stress_resistance"]["max"]) == (2, 2)
    assert totals["first_aid"]["percent"] is None
    suitcase = next(s for s in result["steps"] if s["node_id"] == "suitcase")
    assert {a["id"]: (a["earned"], a["max"]) for a in suitcase["assessment"]} == {
        "communication": (1, 1), "safety": (2, 2), "stress_resistance": (2, 2)}


def test_timeout_lowers_stress_resistance(setup, clock):
    anna, ids = setup
    play(anna, clock, ids["window"], "calm", None, "call_colleague", "check", "tactful", "escort")
    comp = by_id(anna.get("/me/profile").json()["competencies"])
    assert (comp["stress_resistance"]["earned"], comp["stress_resistance"]["max"], comp["stress_resistance"]["percent"]) == (0, 2, 0)


def test_profile_uses_the_latest_attempt_per_scenario_so_replays_do_not_inflate(setup, clock):
    anna, ids = setup
    play(anna, clock, ids["demo"], "c1")
    once = by_id(anna.get("/me/profile").json()["competencies"])
    play(anna, clock, ids["demo"], "c1")
    play(anna, clock, ids["demo"], "c1")
    thrice = by_id(anna.get("/me/profile").json()["competencies"])
    assert once == thrice
    assert (thrice["communication"]["earned"], thrice["communication"]["max"]) == (2, 2)

    play(anna, clock, ids["demo"], "c3")  # latest attempt now counts, even though it is worse
    latest = by_id(anna.get("/me/profile").json()["competencies"])
    assert (latest["communication"]["earned"], latest["communication"]["max"]) == (0, 2)


def test_first_aid_has_no_data_and_is_never_the_weakest(setup, clock):
    anna, ids = setup
    play(anna, clock, ids["demo"], "c2")
    profile = anna.get("/me/profile").json()
    assert by_id(profile["competencies"])["first_aid"]["percent"] is None
    assert profile["weakest"] == {"id": "communication", "title": "Коммуникация", "percent": 50}


def test_recommendations_follow_rules(setup, clock):
    anna, ids = setup
    first = anna.get("/me/profile").json()["recommendation"]
    assert (first["kind"], first["scenario_id"]) == ("start", ids["demo"])

    play(anna, clock, ids["demo"], "c2")  # communication 1/2 is the weakest
    weak = anna.get("/me/profile").json()["recommendation"]
    assert (weak["kind"], weak["scenario_id"]) == ("weak_new", ids["window"])
    assert "Коммуникация" in weak["reason"] and "50%" in weak["reason"]

    play(anna, clock, ids["window"], "calm", "stow_together", "check", "tactful", "escort")
    replay = anna.get("/me/profile").json()["recommendation"]
    assert (replay["kind"], replay["scenario_id"]) == ("replay", ids["demo"])
    # communication is now 9/10 (90%), stress resistance 3/4 (75%) -> the weakest, lowest in the demo
    assert replay["goal"] == "Цель: больше 1 из 2 баллов по компетенции «Стрессоустойчивость»."


def test_no_recommendation_card_without_published_scenarios(login_as):
    assert login_as("anna").get("/me/profile").json()["recommendation"] is None


def test_history_lists_competency_results_per_attempt(setup, clock):
    anna, ids = setup
    play(anna, clock, ids["demo"], "c1")
    item = anna.get("/me/attempts").json()[0]
    assert {c["id"] for c in item["competencies"]} == {"communication", "safety", "stress_resistance"}


def test_nothing_is_weak_when_every_assessed_decision_was_right(setup, clock):
    anna, ids = setup
    play(anna, clock, ids["demo"], "c1")
    profile = anna.get("/me/profile").json()
    assert profile["weakest"] is None
    assert (profile["recommendation"]["kind"], profile["recommendation"]["scenario_id"]) == ("new", ids["window"])

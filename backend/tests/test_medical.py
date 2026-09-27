"""«Пассажиру стало плохо»: all endings, the medicine rule, and first aid finally has data."""

import pytest

from app.scenarios.library import load_scenario
from app.scenarios.validator import validate_graph
from tests.test_gamification import play

SCENARIO = load_scenario("medical_help")


@pytest.fixture()
def run(login_as, metod, clock):
    sid = metod.post("/scenarios", json=SCENARIO).json()["id"]
    player = login_as("anna")
    return player, (lambda *path: play(player, clock, sid, *path))


def test_scenario_is_valid():
    validate_graph(SCENARIO["graph"])


def test_correct_actions_lead_to_the_good_ending_and_full_first_aid(run):
    player, go = run
    state = go("approach", "call_senior", "stay_calm", "assist", "prepare_exit")
    assert state["node"]["node_id"] == "end_good"
    first_aid = {c["id"]: c for c in player.get("/me/profile").json()["competencies"]}["first_aid"]
    assert (first_aid["earned"], first_aid["max"], first_aid["percent"]) == (9, 9, 100)


def test_personal_medicine_always_ends_in_a_complication(run):
    _, go = run
    state = go("approach", "own_meds", "stay_calm", "prepare_exit")
    assert state["node"]["node_id"] == "end_complication"


def test_delay_or_panic_spoils_the_ending(run):
    _, go = run
    assert go("later", "call_now", "stay_calm", "assist", "prepare_exit")["node"]["node_id"] == "end_tense"
    assert go("shout", "call_senior", "stay_calm", "assist", "prepare_exit")["node"]["node_id"] == "end_tense"


def test_timeout_on_the_critical_step_makes_things_worse(run):
    _, go = run
    state = go("approach", None)
    assert state["last_step"]["timed_out"] is True
    assert state["node"]["node_id"] == "worse"


def test_medic_appears_only_after_the_announcement(run):
    _, go = run
    assert go("approach", "call_senior", "stay_calm")["node"]["node_id"] == "medic"
    assert go("approach", "own_meds", "stay_calm")["node"]["node_id"] == "station"


def _cast(state):
    return {c["id"]: c["pose"] for c in state["node"]["visual"]["characters"]}


def test_scene_shows_who_arrives_and_how_the_passenger_feels(run):
    _, go = run
    assert _cast(go()) == {"patient": "unwell", "neighbor": "pointing"}
    care = go("approach", "call_senior")
    assert set(_cast(care)) == {"patient", "neighbor", "chief"}
    assert "first_aid_kit" in care["node"]["visual"]["props"]
    assert "chief" not in _cast(go("approach", "own_meds"))
    medic = go("approach", "call_senior", "stay_calm")
    assert medic["node"]["node_id"] == "medic"
    assert {"medic", "chief"} <= set(_cast(medic))
    assert _cast(go("approach", "call_senior", "stay_calm", "assist", "prepare_exit"))["patient"] == "sitting"


def test_calm_carriage_achievement_and_complication_badge(run):
    player, go = run
    good = go("approach", "call_senior", "stay_calm", "assist", "prepare_exit")
    titles = {a["title"] for a in player.get(f"/attempts/{good['attempt_id']}/result").json()["reward"]["achievements"]}
    assert "Спокойный вагон" in titles
    bad = go("approach", "own_meds", "stay_calm", "prepare_exit")
    ending = player.get(f"/attempts/{bad['attempt_id']}/result").json()["ending"]
    assert (ending["outcome_label"], ending["outcome_tone"]) == ("Осложнение", "bad")

"""Achievements a methodologist defines inside a scenario (graph.achievements)."""

import copy

import pytest

from app.scenarios.library import load_scenario
from app.scenarios.validator import collect_errors
from tests.test_gamification import play, publish, reward  # noqa: F401  (publish is a fixture)

DEMO = load_scenario("seat_recline")


def _with_achievements(data: dict, achievements: list[dict]) -> dict:
    data = copy.deepcopy(data)
    data["graph"]["achievements"] = achievements
    return data


CALM_MASTER = {
    "id": "calm_master",
    "title": "Мастер спокойствия",
    "description": "Сохраните лояльность не ниже 60.",
    "icon": "heart",
    "when": {"scale": "loyalty", "op": ">=", "value": 60},
}


def test_custom_achievement_is_awarded_with_its_title_and_icon(login_as, publish, clock):  # noqa: F811
    anna = login_as("anna")
    sid = publish(_with_achievements(DEMO, [CALM_MASTER]))
    earned = reward(anna, play(anna, clock, sid, "c1"))["achievements"]
    assert {"id": f"s:{sid}:calm_master", "title": "Мастер спокойствия", "icon": "heart"} in earned
    assert reward(anna, play(anna, clock, sid, "c1"))["achievements"] == []


def test_custom_achievement_not_awarded_when_condition_fails(login_as, publish, clock):  # noqa: F811
    anna = login_as("anna")
    sid = publish(_with_achievements(DEMO, [CALM_MASTER]))
    earned = reward(anna, play(anna, clock, sid, "c3"))["achievements"]  # loyalty 35
    assert all(a["id"] != f"s:{sid}:calm_master" for a in earned)


def test_profile_lists_custom_achievements_locked_and_earned(login_as, publish, clock):  # noqa: F811
    anna = login_as("anna")
    sid = publish(_with_achievements(DEMO, [CALM_MASTER]))
    locked = {a["id"]: a for a in anna.get("/me/profile").json()["achievements"]}
    custom_id = f"s:{sid}:calm_master"
    assert locked[custom_id]["earned"] is False
    assert locked[custom_id]["title"] == "Мастер спокойствия"
    assert locked[custom_id]["icon"] == "heart"
    assert locked[custom_id]["scenario_title"] == DEMO["title"]
    play(anna, clock, sid, "c1")
    earned = {a["id"]: a for a in anna.get("/me/profile").json()["achievements"]}
    assert earned[custom_id]["earned"] is True
    assert earned["first_trip"]["icon"] == "medal"


def test_earned_custom_achievement_survives_removal_from_the_scenario(login_as, publish, metod, clock):  # noqa: F811
    anna = login_as("anna")
    sid = publish(_with_achievements(DEMO, [CALM_MASTER]))
    play(anna, clock, sid, "c1")
    metod.put(f"/editor/scenarios/{sid}/draft", json=_with_achievements(DEMO, []))
    assert metod.post(f"/editor/scenarios/{sid}/publish").status_code == 200
    earned = {a["id"]: a for a in anna.get("/me/profile").json()["achievements"]}
    assert earned[f"s:{sid}:calm_master"]["title"] == "Мастер спокойствия"


@pytest.mark.parametrize(
    ("patch", "error"),
    [
        ({"id": "9bad"}, "graph.achievements[0].id"),
        ({"title": " "}, "graph.achievements[0].title"),
        ({"icon": "rocket"}, "graph.achievements[0].icon"),
        ({"when": {"flag": "nope"}}, "graph.achievements[0].when.flag"),
        ({"extra": 1}, "graph.achievements[0].extra"),
    ],
)
def test_validator_checks_custom_achievements(patch, error):
    graph = _with_achievements(DEMO, [{**CALM_MASTER, **patch}])["graph"]
    assert any(e.startswith(error) for e in collect_errors(graph)), collect_errors(graph)


def test_validator_rejects_duplicate_and_missing_condition():
    graph = _with_achievements(DEMO, [CALM_MASTER, CALM_MASTER, {k: v for k, v in CALM_MASTER.items() if k != "when"} | {"id": "x"}])["graph"]
    errors = collect_errors(graph)
    assert any(e.startswith("graph.achievements[1].id") and "duplicate" in e for e in errors)
    assert any(e.startswith("graph.achievements[2].when") for e in errors)

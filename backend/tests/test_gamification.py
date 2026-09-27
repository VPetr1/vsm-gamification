"""Server-side rewards: exactly once, improvement-only XP, declarative achievements, leaderboard."""

import pytest
from sqlalchemy import func, select

from app.models.models import EmployeeAchievement, Notification, ScenarioBest
from app.scenarios.library import load_scenario

DEMO = load_scenario("seat_recline")
WINDOW = load_scenario("window_seat")


@pytest.fixture()
def publish(metod):
    def _publish(data) -> str:
        r = metod.post("/scenarios", json=data)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    return _publish


def play(client, clock, scenario_id, *path):
    state = client.post("/attempts", json={"scenario_id": scenario_id}).json()
    for choice in path:
        clock.advance(state["node"]["timer_seconds"] if choice is None else 1)
        state = client.post(
            f"/attempts/{state['attempt_id']}/choice", json={"choice_id": choice, "expected_step": state["step"]}
        ).json()
    return state


def reward(client, state):
    return client.get(f"/attempts/{state['attempt_id']}/result").json()["reward"]


def test_xp_counts_only_improvements_over_the_best_result(login_as, publish, clock):
    anna = login_as("anna")
    demo = publish(DEMO)

    first = reward(anna, play(anna, clock, demo, "c2"))  # 40/55 -> raw 48 of 38..58 -> 50
    worse = reward(anna, play(anna, clock, demo, "c3"))  # 35/40 -> raw 38, the worst ending -> 0
    better = reward(anna, play(anna, clock, demo, "c1"))  # 60/55 -> raw 58, the best ending -> 100

    assert (first["score"], first["xp_gained"]) == (50, 50)
    assert (worse["score"], worse["xp_gained"], worse["best_score"]) == (0, 0, 50)
    assert (better["score"], better["xp_gained"], better["best_score"]) == (100, 50, 100)
    profile = anna.get("/me/profile").json()
    assert profile["xp"] == 100  # sum of best results, not of all attempts


def test_replaying_the_same_result_never_adds_xp(login_as, publish, clock):
    anna = login_as("anna")
    demo = publish(DEMO)
    for _ in range(5):
        play(anna, clock, demo, "c1")
    assert anna.get("/me/profile").json()["xp"] == 100


def test_achievements_are_awarded_once(login_as, publish, clock, session_factory):
    anna = login_as("anna")
    demo = publish(DEMO)
    assert [a["id"] for a in reward(anna, play(anna, clock, demo, "c1"))["achievements"]] == ["first_trip", "diplomat"]
    assert reward(anna, play(anna, clock, demo, "c1"))["achievements"] == []
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(EmployeeAchievement)) == 2


def test_timeout_finish_resolved_on_restore_rewards_exactly_once(login_as, publish, clock, session_factory):
    anna = login_as("anna")
    demo = publish(DEMO)
    started = anna.post("/attempts", json={"scenario_id": demo}).json()
    clock.advance(600)

    first = anna.get(f"/attempts/{started['attempt_id']}").json()
    anna.get(f"/attempts/{started['attempt_id']}")
    anna.post(f"/attempts/{started['attempt_id']}/choice", json={"choice_id": None, "expected_step": 0})

    assert first["status"] == "finished"
    assert reward(anna, first) == {"score": 25, "xp_gained": 25, "best_score": 25,
                                   "achievements": [{"id": "first_trip", "title": "Первый рейс", "icon": "medal"}]}
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(ScenarioBest)) == 1
        assert db.scalar(select(func.count()).select_from(Notification).where(Notification.kind == "achievement")) == 1


@pytest.mark.parametrize(
    "path, expected",
    [
        (["calm", "stow_together", "check", "tactful", "escort"], {"first_trip", "diplomat", "safe_passage"}),
        (["order", "stow_together", "check", "tactful", "escort"], {"first_trip", "safe_passage"}),
        (["calm", None, "call_colleague", "check", "tactful", "escort"], {"first_trip", "diplomat"}),
    ],
)
def test_window_seat_achievements_follow_declared_rules(login_as, publish, clock, path, expected):
    anna = login_as("anna")
    window = publish(WINDOW)
    earned = {a["id"] for a in reward(anna, play(anna, clock, window, *path))["achievements"]}
    assert earned == expected


def test_level_up_creates_a_notification(login_as, publish, clock):
    anna = login_as("anna")
    demo = publish(DEMO)
    play(anna, clock, demo, "c1")  # 100 XP -> level 2
    profile = anna.get("/me/profile").json()
    assert profile["level"] == {"number": 2, "title": "Проводник", "min_xp": 50, "next_min_xp": 120}
    notes = anna.get("/me/notifications").json()
    assert notes["unread"] == 3
    assert {n["kind"] for n in notes["items"]} == {"level_up", "achievement"}


def test_notifications_can_be_marked_read(login_as, publish, clock):
    anna = login_as("anna")
    play(anna, clock, publish(DEMO), "c1")
    first = anna.get("/me/notifications").json()["items"][0]
    assert anna.post(f"/me/notifications/{first['id']}/read").status_code == 204
    assert anna.get("/me/notifications").json()["unread"] == 2
    anna.post("/me/notifications/read-all")
    assert anna.get("/me/notifications").json()["unread"] == 0


def test_notifications_of_others_are_not_touched(login_as, publish, clock):
    anna, boris = login_as("anna"), login_as("boris")
    play(anna, clock, publish(DEMO), "c1")
    note = anna.get("/me/notifications").json()["items"][0]
    boris.post(f"/me/notifications/{note['id']}/read")
    assert anna.get("/me/notifications").json()["unread"] == 3


def test_leaderboard_scopes_and_fields(login_as, publish, clock):
    demo = publish(DEMO)
    anna = login_as("anna", full_name="Анна", brigade="Бригада 1", depot="Депо Восток")
    boris = login_as("boris", full_name="Борис", brigade="Бригада 1", depot="Депо Восток")
    vera = login_as("vera", full_name="Вера", brigade="Бригада 2", depot="Депо Восток")
    gleb = login_as("gleb", full_name="Глеб", brigade="Бригада 3", depot="Депо Запад")
    play(anna, clock, demo, "c2")  # 50
    play(boris, clock, demo, "c1")  # 100
    play(vera, clock, demo, "c3")  # 0
    play(gleb, clock, demo, "c1")  # 100

    brigade = anna.get("/leaderboard?scope=brigade").json()
    assert [(e["rank"], e["name"], e["xp"], e["is_me"]) for e in brigade["entries"]] == [(1, "Борис", 100, False), (2, "Анна", 50, True)]
    assert set(brigade["entries"][0]) == {"rank", "name", "brigade", "depot", "level", "level_title", "xp", "completed", "is_me", "synthetic"}

    depot = anna.get("/leaderboard?scope=depot").json()
    assert [e["name"] for e in depot["entries"]] == ["Борис", "Анна", "Вера"]

    company = anna.get("/leaderboard?scope=company").json()["entries"]
    assert [(e["rank"], e["name"]) for e in company] == [(1, "Борис"), (1, "Глеб"), (3, "Анна"), (4, "Вера")]
    assert "metodist" not in {e["name"] for e in company}
    assert anna.get("/leaderboard?scope=planet").status_code == 422


def test_history_and_catalog_show_own_progress(login_as, publish, clock):
    anna = login_as("anna")
    demo = publish(DEMO)
    play(anna, clock, demo, "c1")
    running = anna.post("/attempts", json={"scenario_id": demo}).json()

    history = anna.get("/me/attempts").json()
    assert [h["status"] for h in history] == ["in_progress", "finished"]
    assert history[1]["score"] == 100 and history[1]["outcome"] == "calm_resolution" and history[1]["xp_gained"] == 100

    catalog = anna.get("/scenarios").json()
    assert catalog[0]["my_best_score"] == 100
    assert catalog[0]["in_progress_attempt_id"] == running["attempt_id"]
    assert login_as("boris").get("/scenarios").json()[0]["my_best_score"] is None

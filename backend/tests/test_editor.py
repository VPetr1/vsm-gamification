"""Editor: drafts, validation with paths, publishing versions, snapshots of running attempts."""

import copy

from app.models.models import Scenario
from app.scenarios.library import load_scenario
from app.seed import seed_scenarios
from tests.test_gamification import play

WINDOW = load_scenario("window_seat")


def test_editor_is_methodologist_only(login_as):
    conductor = login_as("anna")
    assert conductor.get("/editor/scenarios").status_code == 403
    assert conductor.post("/editor/scenarios", json={"title": "x"}).status_code == 403


def test_new_draft_is_hidden_from_the_catalog_and_cannot_be_played(metod, login_as):
    created = metod.post("/editor/scenarios", json={"title": "Черновик"}).json()
    assert created["version"] == 0 and created["published"] is None and created["errors"] == []
    anna = login_as("anna")
    assert anna.get("/scenarios").json() == []
    assert anna.post("/attempts", json={"scenario_id": created["id"]}).status_code == 404


def test_invalid_draft_is_saved_but_cannot_be_published(metod):
    sid = metod.post("/editor/scenarios", json={"title": "Черновик"}).json()["id"]
    draft = metod.get(f"/editor/scenarios/{sid}").json()["draft"]
    draft["graph"]["nodes"]["start"]["choices"][0]["next_node"] = "ghost"
    draft["title"] = " "

    saved = metod.put(f"/editor/scenarios/{sid}/draft", json=draft)
    assert saved.status_code == 200
    assert saved.json()["errors"] == [
        "title: название обязательно",
        "nodes.start.choices[0].next_node: points to unknown node 'ghost'",
    ]
    r = metod.post(f"/editor/scenarios/{sid}/publish")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "invalid_scenario"
    assert "nodes.start.choices[0].next_node: points to unknown node 'ghost'" in r.json()["detail"]["errors"]


def test_publishing_creates_versions_and_notifies_conductors(metod, login_as):
    anna = login_as("anna")
    sid = metod.post("/editor/scenarios", json={"title": "Новый рейс", "tags": ["safety"]}).json()["id"]
    first = metod.post(f"/editor/scenarios/{sid}/publish").json()
    assert (first["version"], first["has_unpublished_changes"]) == (1, False)
    catalog = anna.get("/scenarios").json()
    assert [(s["title"], s["version"], s["tags"]) for s in catalog] == [("Новый рейс", 1, ["safety"])]
    assert anna.get("/me/notifications").json()["items"][0]["title"] == "Новый сценарий: «Новый рейс»"

    draft = metod.get(f"/editor/scenarios/{sid}").json()["draft"]
    draft["title"] = "Новый рейс, редакция 2"
    metod.put(f"/editor/scenarios/{sid}/draft", json=draft)
    assert anna.get("/scenarios").json()[0]["title"] == "Новый рейс"  # draft stays invisible
    assert metod.post(f"/editor/scenarios/{sid}/publish").json()["version"] == 2
    assert anna.get("/scenarios").json()[0]["title"] == "Новый рейс, редакция 2"


def test_adding_a_fork_in_the_editor_keeps_running_attempts_on_their_version(metod, login_as, clock):
    sid = metod.post("/scenarios", json=WINDOW).json()["id"]
    anna = login_as("anna")
    running = anna.post("/attempts", json={"scenario_id": sid}).json()

    draft = metod.get(f"/editor/scenarios/{sid}").json()["draft"]
    graph = draft["graph"]
    graph["nodes"]["start"]["choices"].append(
        {"id": "ask_colleague", "text": "Позвать коллегу, чтобы помочь разобраться", "effects": {"loyalty": 2},
         "next_node": "colleague"}
    )
    graph["nodes"]["colleague"] = {
        "text": "Коллега подходит и помогает выяснить, чей это билет.",
        "choices": [{"id": "go_on", "text": "Вместе разобраться с чемоданом", "next_node": "suitcase"}],
    }
    assert metod.put(f"/editor/scenarios/{sid}/draft", json=draft).json()["errors"] == []
    assert metod.post(f"/editor/scenarios/{sid}/publish").json()["version"] == 2

    old = anna.get(f"/attempts/{running['attempt_id']}").json()
    assert old["scenario_version"] == 1
    assert "ask_colleague" not in [c["id"] for c in old["node"]["choices"]]

    fresh = play(anna, clock, sid, "ask_colleague")
    assert fresh["scenario_version"] == 2
    assert fresh["node"]["node_id"] == "colleague"


def test_discarding_returns_to_the_published_version(metod):
    sid = metod.post("/scenarios", json=WINDOW).json()["id"]
    draft = metod.get(f"/editor/scenarios/{sid}").json()["draft"]
    draft["title"] = "Правка"
    metod.put(f"/editor/scenarios/{sid}/draft", json=draft)
    back = metod.delete(f"/editor/scenarios/{sid}/draft").json()
    assert back["has_unpublished_changes"] is False and back["draft"]["title"] == WINDOW["title"]

    never = metod.post("/editor/scenarios", json={"title": "Черновик"}).json()["id"]
    assert metod.delete(f"/editor/scenarios/{never}/draft").status_code == 409


def test_seed_never_overwrites_a_scenario_published_from_the_editor(session_factory, clock):
    with session_factory() as db:
        seed_scenarios(db, clock.now)
        db.commit()
        window = db.query(Scenario).filter_by(key="window_seat").one()
        edited = copy.deepcopy(window.graph)
        edited["nodes"]["start"]["text"] = "Текст методиста"
        window.graph, window.version, window.origin = edited, 2, "editor"
        db.commit()

        seed_scenarios(db, clock.now)
        db.commit()
        db.refresh(window)
        assert (window.version, window.graph["nodes"]["start"]["text"]) == (2, "Текст методиста")

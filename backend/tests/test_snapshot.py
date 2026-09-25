"""Editing a scenario must not change attempts that already started."""

import copy

from app.models.models import Scenario
from app.scenarios.library import load_scenario

DEMO_SCENARIO = load_scenario("seat_recline")


def test_started_attempt_keeps_its_snapshot_after_the_scenario_is_edited(client, session_factory):
    employee_id = client.post("/employees", json={"full_name": "Синтетический Проводник"}).json()["id"]
    scenario = client.post("/scenarios", json={"title": "demo", "graph": DEMO_SCENARIO["graph"]}).json()
    assert scenario["version"] == 1
    started = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario["id"]}).json()

    edited = copy.deepcopy(DEMO_SCENARIO["graph"])
    edited["nodes"]["n1"]["text"] = "Отредактированный текст"
    edited["nodes"]["n1"]["choices"][0]["effects"] = {"loyalty": -40, "safety": -40}
    with session_factory() as db:
        row = db.get(Scenario, scenario["id"])
        row.graph = edited
        row.version = 2
        db.commit()

    state = client.get(f"/attempts/{started['attempt_id']}").json()
    assert state["node"]["text"] == DEMO_SCENARIO["graph"]["nodes"]["n1"]["text"]
    assert state["scenario_version"] == 1

    after = client.post(f"/attempts/{started['attempt_id']}/choice", json={"choice_id": "c1", "expected_step": 0}).json()
    assert (after["loyalty"], after["safety"]) == (60, 55)

    fresh = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario["id"]}).json()
    assert fresh["scenario_version"] == 2
    assert fresh["node"]["text"] == "Отредактированный текст"

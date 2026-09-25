from app.scenarios.demo_scenario import DEMO_SCENARIO


def _create_employee(client):
    r = client.post("/employees", json={"full_name": "Иван Иванов", "depot": "Восток", "brigade": "1"})
    assert r.status_code == 201
    return r.json()["id"]


def _create_scenario(client):
    r = client.post(
        "/scenarios",
        json={
            "title": DEMO_SCENARIO["title"],
            "description": DEMO_SCENARIO["description"],
            "graph": DEMO_SCENARIO["graph"],
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_full_scenario_playthrough_to_saved_result(client):
    employee_id = _create_employee(client)
    scenario_id = _create_scenario(client)

    r = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id})
    assert r.status_code == 201
    state = r.json()
    attempt_id = state["attempt_id"]
    assert state["node"]["node_id"] == "n1"
    assert state["status"] == "in_progress"
    assert {c["id"] for c in state["node"]["choices"]} == {"c1", "c2", "c3"}

    r = client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c1"})
    assert r.status_code == 200
    final_state = r.json()
    assert final_state["status"] == "finished"
    assert final_state["node"]["is_ending"] is True
    assert final_state["loyalty"] == 60
    assert final_state["safety"] == 55

    r = client.get(f"/attempts/{attempt_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "finished"


def test_scenario_creation_rejects_invalid_graph(client):
    r = client.post("/scenarios", json={"title": "broken", "graph": {"start_node": "missing", "nodes": {}}})
    assert r.status_code == 422


def test_start_attempt_with_unknown_employee_returns_404(client):
    scenario_id = _create_scenario(client)
    r = client.post("/attempts", json={"employee_id": "does-not-exist", "scenario_id": scenario_id})
    assert r.status_code == 404


def test_choice_on_unknown_attempt_returns_404(client):
    r = client.post("/attempts/does-not-exist/choice", json={"choice_id": "c1"})
    assert r.status_code == 404

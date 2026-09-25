from app.scenarios.library import load_scenario

DEMO_SCENARIO = load_scenario("seat_recline")


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

    r = client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c1", "expected_step": 0})
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
    r = client.post("/attempts/does-not-exist/choice", json={"choice_id": "c1", "expected_step": 0})
    assert r.status_code == 404


def _start(client):
    employee_id = _create_employee(client)
    scenario_id = _create_scenario(client)
    r = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id})
    assert r.status_code == 201
    return r.json()


def test_state_exposes_server_time_and_deadline(client, clock):
    state = _start(client)
    assert state["server_time"] == "2026-09-25T12:00:00Z"
    assert state["deadline"] == "2026-09-25T12:00:20Z"
    assert "effects" not in str(state) and "next_node" not in str(state)


def test_timeout_request_before_deadline_returns_409_and_keeps_state(client, clock):
    state = _start(client)
    clock.advance(10)

    r = client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": None, "expected_step": 0})

    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "timer_not_expired"
    after = client.get(f"/attempts/{state['attempt_id']}").json()
    assert after["node"]["node_id"] == "n1"
    assert after["last_step"] is None


def test_timeout_request_at_deadline_applies_timeout(client, clock):
    state = _start(client)
    clock.advance(20)

    r = client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": None, "expected_step": 0})

    assert r.status_code == 200
    body = r.json()
    assert body["last_step"] == {"step": 1, "node_id": "n1", "choice_id": None, "timed_out": True}
    assert body["step"] == 1
    assert body["node"]["node_id"] == "n2_escalation"
    assert (body["loyalty"], body["safety"]) == (40, 45)


def test_late_choice_is_converted_to_timeout(client, clock):
    state = _start(client)
    clock.advance(21)

    body = client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": "c1", "expected_step": 0}).json()

    assert body["last_step"]["timed_out"] is True
    assert body["node"]["node_id"] == "n2_escalation"


def test_restoring_an_expired_attempt_applies_timeout_once(client, clock):
    state = _start(client)
    clock.advance(600)

    first = client.get(f"/attempts/{state['attempt_id']}").json()
    second = client.get(f"/attempts/{state['attempt_id']}").json()

    assert first["status"] == "finished"
    assert first["last_step"]["timed_out"] is True
    assert (first["loyalty"], first["safety"]) == (40, 45)
    assert (second["loyalty"], second["safety"]) == (40, 45)


def test_restoring_before_deadline_changes_nothing(client, clock):
    state = _start(client)
    clock.advance(5)

    body = client.get(f"/attempts/{state['attempt_id']}").json()

    assert body["node"]["node_id"] == "n1"
    assert body["deadline"] == "2026-09-25T12:00:20Z"
    assert body["server_time"] == "2026-09-25T12:00:05Z"


def test_choice_on_finished_attempt_returns_409(client, clock):
    state = _start(client)
    client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": "c1", "expected_step": 0})

    r = client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": "c1", "expected_step": 0})

    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "attempt_finished"


def test_timerless_node_has_null_deadline_and_rejects_null_choice(client, clock):
    from tests.test_engine import V2_GRAPH

    employee_id = _create_employee(client)
    scenario_id = client.post("/scenarios", json={"title": "v2", "graph": V2_GRAPH}).json()["id"]
    state = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id}).json()

    assert state["deadline"] is None
    assert state["node"]["timer_seconds"] is None
    assert (state["loyalty"], state["safety"]) == (60, 80)
    assert "flags" not in state

    clock.advance(3600)
    r = client.post(f"/attempts/{state['attempt_id']}/choice", json={"choice_id": None, "expected_step": 0})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "choice_required"


def test_employee_field_lengths_are_validated(client):
    assert client.post("/employees", json={"full_name": "x" * 201}).status_code == 422
    assert client.post("/employees", json={"full_name": ""}).status_code == 422
    assert client.post("/employees", json={"full_name": "x" * 200}).status_code == 201

from tests.test_api import _create_employee

GRAPH = {
    "initial": {"loyalty": 95, "safety": 50},
    "flags": {},
    "start_node": "greet",
    "nodes": {
        "greet": {
            "text": "Пассажир просит помощи.",
            "debrief": "Лучше всего сразу помочь.",
            "choices": [
                {"id": "help", "text": "Помочь", "effects": {"loyalty": 20}, "explanation": "Помощь ценят.", "next_node": "rush"},
                {"id": "skip", "text": "Пройти мимо", "effects": {"loyalty": -20}, "next_node": "rush"},
            ],
        },
        "rush": {
            "text": "В проходе препятствие.",
            "timer_seconds": 10,
            "timeout": {"effects": {"safety": -30}, "explanation": "Промедление опасно.", "next_node": "end"},
            "choices": [{"id": "clear", "text": "Убрать", "effects": {"safety": 10}, "next_node": "end"}],
        },
        "end": {"text": "Поездка продолжается.", "is_ending": True, "ending_summary": "Итог.", "outcome": "calm"},
    },
}


def _finished_attempt(client, clock):
    employee_id = _create_employee(client)
    scenario_id = client.post("/scenarios", json={"title": "Тест", "graph": GRAPH}).json()["id"]
    attempt_id = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id}).json()["attempt_id"]
    clock.advance(3)
    client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "help", "expected_step": 0})
    clock.advance(10)
    client.post(f"/attempts/{attempt_id}/choice", json={"choice_id": None, "expected_step": 1})
    return attempt_id


def test_result_lists_decisions_with_actual_deltas_and_explanations(client, clock):
    attempt_id = _finished_attempt(client, clock)

    r = client.get(f"/attempts/{attempt_id}/result")

    assert r.status_code == 200
    body = r.json()
    assert body["initial"] == {"loyalty": 95, "safety": 50}
    assert body["final"] == {"loyalty": 100, "safety": 20}
    assert body["ending"] == {"node_id": "end", "text": "Поездка продолжается.", "summary": "Итог.", "outcome": "calm"}
    assert body["started_at"] == "2026-09-25T12:00:00Z"
    assert body["finished_at"] == "2026-09-25T12:00:13Z"

    first, second = body["steps"]
    assert first == {
        "step": 1,
        "node_id": "greet",
        "situation": "Пассажир просит помощи.",
        "choice_id": "help",
        "choice_text": "Помочь",
        "timed_out": False,
        "loyalty_delta": 5,  # +20 requested, capped at 100
        "safety_delta": 0,
        "loyalty_after": 100,
        "safety_after": 50,
        "explanation": "Помощь ценят.",
        "lesson": "Лучше всего сразу помочь.",
    }
    assert second["timed_out"] is True
    assert second["choice_id"] is None and second["choice_text"] is None
    assert (second["safety_delta"], second["safety_after"]) == (-30, 20)
    assert second["explanation"] == "Промедление опасно."
    assert second["lesson"] is None


def test_result_is_not_available_before_the_end(client, clock):
    employee_id = _create_employee(client)
    scenario_id = client.post("/scenarios", json={"title": "Тест", "graph": GRAPH}).json()["id"]
    attempt_id = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id}).json()["attempt_id"]

    r = client.get(f"/attempts/{attempt_id}/result")

    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "attempt_not_finished"


def test_result_for_unknown_attempt_is_404(client):
    assert client.get("/attempts/nope/result").status_code == 404

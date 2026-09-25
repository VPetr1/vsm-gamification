"""«Место у окна»: every ending, flag- and threshold-driven branches, the critical timer."""

import pytest

from app.scenarios.library import load_scenario
from app.scenarios.validator import validate_graph

TIMEOUT = None  # in a path: wait for the timer to run out, then send choice_id=null
SCENARIO = load_scenario("window_seat")


@pytest.fixture()
def play(client, clock):
    employee_id = client.post("/employees", json={"full_name": "Синтетический Проводник"}).json()["id"]
    scenario_id = client.post("/scenarios", json=SCENARIO).json()["id"]

    def _play(*path):
        state = client.post("/attempts", json={"employee_id": employee_id, "scenario_id": scenario_id}).json()
        for choice_id in path:
            if choice_id is TIMEOUT:
                clock.advance(state["node"]["timer_seconds"])
            else:
                clock.advance(2)
            r = client.post(
                f"/attempts/{state['attempt_id']}/choice",
                json={"choice_id": choice_id, "expected_step": state["step"]},
            )
            assert r.status_code == 200, r.json()
            state = r.json()
        return state

    return _play


def result(client, state):
    return client.get(f"/attempts/{state['attempt_id']}/result").json()


def test_scenario_data_is_valid_and_sized():
    validate_graph(SCENARIO["graph"])
    assert 10 <= len(SCENARIO["graph"]["nodes"]) <= 14


def test_starts_with_scenario_initial_scales(client, play):
    state = play()
    assert (state["loyalty"], state["safety"]) == (60, 80)
    assert state["node"]["node_id"] == "start"
    assert state["deadline"] is None  # the opening step has no timer


def test_calm_ending(client, play):
    state = play("calm", "stow_together", "check", "tactful", "escort")
    assert state["status"] == "finished"
    assert state["node"]["node_id"] == "end_calm"
    assert (state["loyalty"], state["safety"]) == (90, 95)
    assert result(client, state)["ending"]["outcome"] == "calm_resolution"


def test_rudeness_earlier_turns_the_same_resolution_into_dissatisfaction(play):
    # Same later choices as the calm path; loyalty ends at 75 (>= 70), only the was_rude flag differs.
    state = play("order", "stow_together", "check", "tactful", "escort")
    assert state["loyalty"] == 75
    assert state["node"]["node_id"] == "end_dissatisfied"


def test_loyalty_threshold_alone_decides_the_ending(play):
    # No negative flags on either path; the final loyalty is 65 vs 70 around the ">= 70" threshold.
    below = play("calm", "stow_together", "check", "public", "send_alone")
    at = play("calm", "stow_together", "check", "public", "escort")
    assert (below["loyalty"], below["node"]["node_id"]) == (65, "end_dissatisfied")
    assert (at["loyalty"], at["node"]["node_id"]) == (70, "end_calm")


def test_escalation_ending_and_asking_for_help_costs_nothing(client, play):
    state = play("ignore", "call_senior")
    assert state["node"]["node_id"] == "end_senior"
    steps = result(client, state)["steps"]
    assert (steps[0]["loyalty_delta"], steps[0]["safety_delta"]) == (-15, -5)
    assert (steps[1]["choice_id"], steps[1]["loyalty_delta"], steps[1]["safety_delta"]) == ("call_senior", 0, 0)
    assert result(client, state)["ending"]["outcome"] == "escalated_to_senior"


def test_unverified_promise_spoils_an_otherwise_calm_resolution(play):
    state = play("calm", "stow_together", "promise_upgrade", "clear_and_apologize", "tactful", "escort")
    assert (state["loyalty"], state["safety"]) == (90, 100)  # both scales well above 70
    assert state["node"]["node_id"] == "end_dissatisfied"


def test_promise_brings_the_suitcase_back_and_offers_a_last_chance_to_clear_the_aisle(play):
    state = play("calm", "stow_together", "promise_upgrade", "apologize_and_check", "tactful", "escort")
    assert state["node"]["node_id"] == "aisle"
    assert [c["id"] for c in state["node"]["choices"]] == ["clear_now", "leave"]


def test_calling_senior_after_a_broken_promise_is_not_penalised(client, play):
    state = play("calm", "stow_together", "promise_upgrade", "call_senior")
    last = result(client, state)["steps"][-1]
    assert (last["loyalty_delta"], last["safety_delta"]) == (0, 0)
    assert state["node"]["node_id"] == "end_senior"


def test_suitcase_timeout_leads_to_the_trip_incident(client, play):
    state = play("calm", TIMEOUT)
    assert state["last_step"]["timed_out"] is True
    assert state["node"]["node_id"] == "trip"
    assert (state["loyalty"], state["safety"]) == (60, 60)


def test_safety_threshold_after_a_timeout(play):
    recovered = play("calm", TIMEOUT, "help_alone", "check", "tactful", "escort")
    neglected = play("calm", TIMEOUT, "back_to_dispute", "check", "tactful", "escort", "clear_now")
    assert (recovered["safety"], recovered["node"]["node_id"]) == (70, "end_calm")
    assert (neglected["safety"], neglected["node"]["node_id"]) == (65, "end_dissatisfied")


def test_leaving_the_suitcase_is_revisited_before_the_ending(play):
    state = play("calm", "leave_it", "check", "tactful", "escort")
    assert state["node"]["node_id"] == "aisle"
    assert play("calm", "leave_it", "check", "tactful", "escort", "leave")["node"]["node_id"] == "end_dissatisfied"


def test_reseating_without_checking_can_be_corrected(play):
    state = play("calm", "stow_together", "reseat_girl", "check_now", "tactful", "escort")
    assert state["loyalty"] == 75
    assert state["node"]["node_id"] == "end_calm"


def test_restoring_an_expired_suitcase_step(client, clock, play):
    state = play("calm")
    assert state["deadline"] is not None
    clock.advance(45)

    restored = client.get(f"/attempts/{state['attempt_id']}").json()

    assert restored["node"]["node_id"] == "trip"
    assert restored["step"] == 2
    assert restored["last_step"] == {"step": 2, "node_id": "suitcase", "choice_id": None, "timed_out": True}


def test_double_submit_in_the_middle_of_the_scenario(client, play, session_factory):
    state = play()
    url = f"/attempts/{state['attempt_id']}/choice"

    first = client.post(url, json={"choice_id": "calm", "expected_step": 0})
    second = client.post(url, json={"choice_id": "order", "expected_step": 0})

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == {
        "code": "step_mismatch",
        "message": "expected step 0, but the attempt is at step 1",
        "current_step": 1,
    }
    after = client.get(f"/attempts/{state['attempt_id']}").json()
    assert (after["step"], after["loyalty"]) == (1, 65)


def test_state_never_reveals_effects_or_routing(play):
    state = play("calm")
    raw = str(state)
    for secret in ("effects", "set_flags", "transitions", "condition", "explanation", "debrief", "flags"):
        assert secret not in raw


def test_result_explains_each_decision(client, play):
    state = play("calm", "stow_together", "check", "tactful", "escort")
    steps = result(client, state)["steps"]
    assert [s["choice_id"] for s in steps] == ["calm", "stow_together", "check", "tactful", "escort"]
    assert all(s["explanation"] and s["lesson"] for s in steps)
    assert steps[1]["situation"].startswith("Поезд набирает скорость")

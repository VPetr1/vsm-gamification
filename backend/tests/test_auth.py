"""Demo sign-in and access boundaries: identity and role come only from the server session."""

from app.scenarios.library import load_scenario
from tests.conftest import PASSWORD

DEMO = load_scenario("seat_recline")


def _publish(metod) -> str:
    r = metod.post("/scenarios", json=DEMO)
    assert r.status_code == 201
    return r.json()["id"]


def test_login_sets_httponly_cookie_and_me_returns_the_account(login_as):
    c = login_as("anna", full_name="Анна Тестова")
    cookie = c.cookies.jar._cookies  # noqa: SLF001 - inspect flags set by the server
    flags = next(iter(next(iter(cookie.values())).values()))["vsm_session"]
    assert flags.has_nonstandard_attr("HttpOnly")
    me = c.get("/auth/me").json()
    assert (me["login"], me["full_name"], me["role"]) == ("anna", "Анна Тестова", "conductor")


def test_wrong_password_and_unknown_login_look_the_same(anon, make_account):
    make_account("anna")
    wrong = anon.post("/auth/login", json={"login": "anna", "password": "nope"})
    unknown = anon.post("/auth/login", json={"login": "ghost", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert "vsm_session" not in anon.cookies


def test_protected_endpoints_require_a_session(anon):
    for method, path in [("get", "/auth/me"), ("get", "/scenarios"), ("post", "/attempts"), ("get", "/attempts/x")]:
        r = getattr(anon, method)(path, **({"json": {"scenario_id": "x"}} if method == "post" else {}))
        assert r.status_code == 401, path
        assert r.json()["detail"]["code"] == "unauthorized"


def test_conductor_cannot_use_methodologist_endpoints(login_as):
    conductor = login_as("anna")
    assert conductor.get("/employees").status_code == 403
    assert conductor.post("/employees", json={"full_name": "X"}).status_code == 403
    r = conductor.post("/scenarios", json=DEMO)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "forbidden"


def test_conductor_sees_only_own_attempts(login_as, metod):
    scenario_id = _publish(metod)
    anna, boris = login_as("anna"), login_as("boris")
    attempt_id = anna.post("/attempts", json={"scenario_id": scenario_id}).json()["attempt_id"]

    assert boris.get(f"/attempts/{attempt_id}").status_code == 404
    assert boris.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c1", "expected_step": 0}).status_code == 404
    assert anna.post(f"/attempts/{attempt_id}/choice", json={"choice_id": "c1", "expected_step": 0}).status_code == 200
    assert boris.get(f"/attempts/{attempt_id}/result").status_code == 404
    assert anna.get(f"/attempts/{attempt_id}/result").status_code == 200


def test_employee_id_in_the_body_does_not_choose_the_player(login_as, metod):
    scenario_id = _publish(metod)
    anna = login_as("anna")
    boris_id = login_as("boris").get("/auth/me").json()["id"]
    attempt_id = anna.post("/attempts", json={"scenario_id": scenario_id, "employee_id": boris_id}).json()["attempt_id"]
    assert anna.get(f"/attempts/{attempt_id}").status_code == 200


def test_logout_and_expiry_end_the_session(login_as, clock):
    c = login_as("anna")
    assert c.post("/auth/logout").status_code == 204
    assert c.get("/auth/me").status_code == 401

    c2 = login_as("boris")
    clock.advance(13 * 3600)
    assert c2.get("/auth/me").status_code == 401


def test_demo_accounts_list_exposes_display_fields_only(anon, make_account):
    make_account("anna", full_name="Анна Тестова")
    accounts = anon.get("/auth/demo-accounts").json()
    assert accounts == [{"login": "anna", "full_name": "Анна Тестова", "role": "conductor", "brigade": "Бригада 1", "depot": "Депо Восток"}]


def test_repeated_wrong_passwords_lock_the_login_for_a_while(anon, make_account, clock):
    make_account("anna")
    for _ in range(5):
        assert anon.post("/auth/login", json={"login": "anna", "password": "nope"}).status_code == 401
    locked = anon.post("/auth/login", json={"login": "anna", "password": PASSWORD})
    assert locked.status_code == 429
    assert locked.json()["detail"]["code"] == "too_many_attempts"
    assert locked.json()["detail"]["retry_after"] == 61

    clock.advance(61)
    assert anon.post("/auth/login", json={"login": "anna", "password": PASSWORD}).status_code == 200


def test_successful_login_resets_the_failure_counter(anon, make_account):
    make_account("anna")
    for _ in range(4):
        anon.post("/auth/login", json={"login": "anna", "password": "nope"})
    assert anon.post("/auth/login", json={"login": "anna", "password": PASSWORD}).status_code == 200
    for _ in range(4):
        assert anon.post("/auth/login", json={"login": "anna", "password": "nope"}).status_code == 401

import pytest

from app.core.config import settings
from app.scenarios.library import load_scenario
from tests.test_gamification import play


@pytest.fixture()
def key(monkeypatch):
    monkeypatch.setattr(settings, "integration_api_key", "secret-key")
    return {"X-API-Key": "secret-key"}


def test_integration_api_is_off_without_a_configured_key(anon):
    r = anon.get("/integrations/progress", headers={"X-API-Key": "anything"})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "integration_disabled"


def test_wrong_or_missing_key_is_rejected_and_sessions_do_not_count(anon, key, login_as):
    assert anon.get("/integrations/progress").status_code == 401
    assert anon.get("/integrations/progress", headers={"X-API-Key": "nope"}).status_code == 401
    assert login_as("anna", role="methodologist").get("/integrations/progress").status_code == 401


def test_progress_and_incremental_attempt_export(anon, key, login_as, metod, clock):
    sid = metod.post("/scenarios", json=load_scenario("seat_recline")).json()["id"]
    anna = login_as("anna", full_name="Анна")
    first = play(anna, clock, sid, "c1")
    clock.advance(60)
    play(anna, clock, sid, "c2")

    progress = anon.get("/integrations/progress", headers=key).json()
    row = next(p for p in progress if p["full_name"] == "Анна")
    assert (row["xp"], row["level"], row["achievements"]) == (58, 2, ["diplomat", "first_trip"])
    assert {c["id"]: c["percent"] for c in row["competencies"]}["first_aid"] is None
    assert all(p["full_name"] != "Сотрудник metodist" for p in progress)

    all_attempts = anon.get("/integrations/attempts", headers=key).json()
    assert [a["score"] for a in all_attempts] == [58, 48]
    later = anon.get("/integrations/attempts", headers=key, params={"finished_after": all_attempts[0]["finished_at"]}).json()
    assert [a["attempt_id"] for a in later] == [all_attempts[1]["attempt_id"]]
    assert first["attempt_id"] == all_attempts[0]["attempt_id"]

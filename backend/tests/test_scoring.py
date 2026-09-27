import json
from pathlib import Path

import pytest

from app.scenarios.scoring import MAX_STATES, ScoreRange, normalized_score, raw_score, score_range
from app.scenarios.validator import collect_errors

DATA = Path(__file__).resolve().parents[1] / "app" / "scenarios" / "data"


def _graph(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["graph"]


def _ending(summary: str = "итог") -> dict:
    return {"text": "Конец", "is_ending": True, "ending_summary": summary}


def test_range_covers_every_ending_including_timeouts():
    graph = {
        "start_node": "a",
        "initial": {"loyalty": 50, "safety": 50},
        "nodes": {
            "a": {
                "text": "Шаг",
                "timer_seconds": 10,
                "timeout": {"effects": {"safety": -50}, "next_node": "end"},
                "choices": [
                    {"id": "good", "text": "Хорошо", "effects": {"loyalty": 30, "safety": 30}, "next_node": "end"},
                    {"id": "meh", "text": "Так себе", "next_node": "end"},
                ],
            },
            "end": _ending(),
        },
    }
    assert score_range(graph) == ScoreRange(worst=raw_score(50, 0), best=raw_score(80, 80))


def test_hidden_choices_do_not_count_towards_the_best():
    graph = {
        "start_node": "a",
        "flags": {"vip": False},
        "nodes": {
            "a": {
                "text": "Шаг",
                "choices": [
                    {"id": "secret", "text": "Секрет", "condition": {"flag": "vip"},
                     "effects": {"loyalty": 50, "safety": 50}, "next_node": "end"},
                    {"id": "plain", "text": "Обычно", "next_node": "end"},
                ],
            },
            "end": _ending(),
        },
    }
    assert score_range(graph) == ScoreRange(worst=50, best=50)


def test_cycles_terminate():
    graph = {
        "start_node": "a",
        "nodes": {
            "a": {
                "text": "Шаг",
                "choices": [
                    {"id": "again", "text": "Ещё раз", "effects": {"loyalty": 10}, "next_node": "a"},
                    {"id": "stop", "text": "Стоп", "next_node": "end"},
                ],
            },
            "end": _ending(),
        },
    }
    assert score_range(graph) == ScoreRange(worst=50, best=75)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(30, 0), (95, 100), (60, 46), (62, 49), (63, 51)],
)
def test_normalized_score_maps_worst_to_0_and_best_to_100(raw, expected):
    assert normalized_score(raw, ScoreRange(worst=30, best=95)) == expected


def test_single_outcome_scenario_scores_100():
    assert normalized_score(40, ScoreRange(worst=40, best=40)) == 100


@pytest.mark.parametrize("name", ["seat_recline", "window_seat", "medical_help"])
def test_builtin_scenarios_have_a_perfect_path(name):
    rng = score_range(_graph(name))
    assert normalized_score(rng.best, rng) == 100
    assert normalized_score(rng.worst, rng) == 0


def test_known_ranges_of_builtin_scenarios():
    assert score_range(_graph("window_seat")) == ScoreRange(worst=30, best=95)
    assert score_range(_graph("medical_help")) == ScoreRange(worst=38, best=90)


def test_validator_rejects_graphs_too_large_to_score(monkeypatch):
    import app.scenarios.scoring as scoring

    monkeypatch.setattr(scoring, "MAX_STATES", 3)
    errors = collect_errors(_graph("window_seat"))
    assert any("слишком разветвлён" in e for e in errors)
    assert MAX_STATES == 200_000

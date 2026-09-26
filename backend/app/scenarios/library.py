"""Built-in scenarios shipped as JSON files: texts, effects and explanations live in data, not code."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_scenario(name: str) -> dict:
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        data = json.load(f)
    return {**data, "key": name}


# Catalog order for new users: a short warm-up first; files not listed follow alphabetically.
BUILTIN_ORDER = ["seat_recline", "window_seat", "medical_help"]


def builtin_scenarios() -> list[dict]:
    names = sorted(path.stem for path in DATA_DIR.glob("*.json"))
    ordered = [n for n in BUILTIN_ORDER if n in names] + [n for n in names if n not in BUILTIN_ORDER]
    return [load_scenario(name) for name in ordered]

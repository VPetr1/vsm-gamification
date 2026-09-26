"""Built-in scenarios shipped as JSON files: texts, effects and explanations live in data, not code."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_scenario(name: str) -> dict:
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        data = json.load(f)
    return {**data, "key": name}


def builtin_scenarios() -> list[dict]:
    return [load_scenario(path.stem) for path in sorted(DATA_DIR.glob("*.json"))]

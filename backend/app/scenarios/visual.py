"""Optional scene metadata. The API sends only resolved values (who is present, their mood,
visible props) — never the conditions — so the client cannot learn about hidden branches.

Graph:  "visual": {"characters": {"man": {"name", "figure", "pose", "position"}}}
Node:   "visual": {"speaker": "man",
                   "moods": [{"character": "man", "mood": "angry", "when": <condition>?}],
                   "props": [{"id": "suitcase", "when": <condition>?}]}
Without a mood rule a character's mood follows the loyalty scale.
"""

from app.scenarios.conditions import evaluate

FIGURES = {"man", "woman", "passenger"}
POSES = {"sitting", "standing"}
POSITIONS = {"left", "center", "right"}
MOODS = {"happy", "calm", "worried", "scared", "upset", "angry"}
PROPS = {"suitcase", "spill"}


def mood_from_loyalty(loyalty: int) -> str:
    if loyalty >= 75:
        return "happy"
    if loyalty >= 55:
        return "calm"
    if loyalty >= 40:
        return "worried"
    if loyalty >= 25:
        return "upset"
    return "angry"


def resolve(graph: dict, node: dict, state) -> dict | None:
    characters = (graph.get("visual") or {}).get("characters") or {}
    visual = node.get("visual") or {}
    if not characters and not visual:
        return None
    moods: dict[str, str] = {}
    for rule in visual.get("moods", []):
        if rule["character"] not in moods and evaluate(rule.get("when"), state):
            moods[rule["character"]] = rule["mood"]
    default_mood = mood_from_loyalty(state.loyalty)
    return {
        "speaker": visual.get("speaker"),
        "characters": [
            {
                "id": cid,
                "name": c.get("name", ""),
                "figure": c.get("figure", "passenger"),
                "pose": c.get("pose", "standing"),
                "position": c.get("position", "center"),
                "mood": moods.get(cid, default_mood),
            }
            for cid, c in characters.items()
        ],
        "props": [p["id"] for p in visual.get("props", []) if evaluate(p.get("when"), state)],
    }

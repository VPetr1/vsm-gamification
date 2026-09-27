"""Optional scene metadata. The API sends only resolved values (who is present, their mood,
visible props) - never the conditions - so the client cannot learn about hidden branches.

Graph:  "visual": {"background": "standard",
                   "characters": {"man": {"name", "figure", "gender", "color", "pose", "position"}}}
Node:   "visual": {"speaker": "man", "background": "vestibule",
                   "cast": [{"character": "man", "pose"?, "position"?, "when"?}],
                   "moods": [{"character": "man", "mood": "angry", "when": <condition>?}],
                   "props": [{"id": "suitcase", "when": <condition>?}]}
Without "cast" every character is on stage in its default pose and position; with it, only the
characters with a matching rule (the first match per character wins). Without a mood rule a
character's mood follows the loyalty scale.
"""

from app.scenarios.conditions import evaluate

FIGURES = {"man", "woman", "passenger", "elderly", "child", "chief", "medic", "conductor", "business"}
POSES = {"sitting", "standing", "unwell", "pointing", "hands_on_hips"}
POSITIONS = {"far_left", "left", "center", "right", "far_right"}
MOODS = {"happy", "calm", "worried", "scared", "upset", "angry"}
PROPS = {"suitcase", "spill", "first_aid_kit", "water", "phone", "stroller", "bag"}
BACKGROUNDS = {"standard", "business", "vestibule"}
GENDERS = {"m", "f", "n"}
COLORS = {"blue", "red", "green", "grey", "purple", "orange", "teal", "brown"}
DEFAULT_GENDER = {"man": "m", "woman": "f"}


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


def _on_stage(characters: dict, visual: dict, state) -> dict[str, dict]:
    """Character id -> pose/position overrides, in declaration order."""
    if "cast" not in visual:
        return {cid: {} for cid in characters}
    matched: dict[str, dict] = {}
    for rule in visual["cast"]:
        if rule["character"] not in matched and evaluate(rule.get("when"), state):
            matched[rule["character"]] = rule
    return {cid: matched[cid] for cid in characters if cid in matched}


def resolve(graph: dict, node: dict, state) -> dict | None:
    graph_visual = graph.get("visual") or {}
    characters = graph_visual.get("characters") or {}
    visual = node.get("visual") or {}
    if not characters and not visual and "background" not in graph_visual:
        return None
    moods: dict[str, str] = {}
    for rule in visual.get("moods", []):
        if rule["character"] not in moods and evaluate(rule.get("when"), state):
            moods[rule["character"]] = rule["mood"]
    default_mood = mood_from_loyalty(state.loyalty)
    present = _on_stage(characters, visual, state)
    return {
        "speaker": visual.get("speaker"),
        "background": visual.get("background") or graph_visual.get("background") or "standard",
        "characters": [
            {
                "id": cid,
                "name": c.get("name", ""),
                "figure": c.get("figure", "passenger"),
                "gender": c.get("gender", DEFAULT_GENDER.get(c.get("figure"), "n")),
                "color": c.get("color"),
                "pose": override.get("pose", c.get("pose", "standing")),
                "position": override.get("position", c.get("position", "center")),
                "mood": moods.get(cid, default_mood),
            }
            for cid, override in present.items()
            for c in [characters[cid]]
        ],
        "props": [p["id"] for p in visual.get("props", []) if evaluate(p.get("when"), state)],
    }

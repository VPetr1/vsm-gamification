"""Validates a scenario graph before it is stored, so the engine can trust its shape at runtime.

Every problem is collected (not only the first) and reported with a JSON-like path,
e.g. "nodes.n1.choices[0].effects.loyalty: must be an integer -100..100".
"""

from collections import deque

from app.gamification.competencies import COMPETENCIES, MAX_POINTS
from app.gamification.rules import ACHIEVEMENTS
from app.scenarios import visual as vis
from app.scenarios.conditions import LEGACY_MIN, OPERATORS, SCALES

TIMER_MIN, TIMER_MAX = 5, 600
EFFECT_LIMIT = 100
MAX_CONDITION_DEPTH = 8

GRAPH_KEYS = {"start_node", "nodes", "initial", "flags", "awards", "visual"}
CHARACTER_KEYS = {"name", "figure", "pose", "position"}
NODE_VISUAL_KEYS = {"speaker", "moods", "props"}
AWARD_KEYS = {"achievement", "when"}
STEP_NODE_KEYS = {"text", "is_ending", "timer_seconds", "timeout", "choices", "debrief", "visual"}
ENDING_NODE_KEYS = {"text", "is_ending", "ending_summary", "outcome", "visual"}
OUTCOME_KEYS = {"effects", "set_flags", "next_node", "transitions", "explanation", "assessment"}
CHOICE_KEYS = OUTCOME_KEYS | {"id", "text", "condition"}
TRANSITION_KEYS = {"condition", "next_node"}


class ScenarioValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_graph(graph) -> None:
    errors = collect_errors(graph)
    if errors:
        raise ScenarioValidationError(errors)


def collect_errors(graph) -> list[str]:
    return _Checker().run(graph)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _outcome_targets(outcome: dict) -> list[str]:
    if "next_node" in outcome:
        return [outcome["next_node"]]
    return [t["next_node"] for t in outcome["transitions"]]


class _Checker:
    def __init__(self):
        self.errors: list[str] = []
        self.flags: set[str] = set()
        self.node_ids: set[str] = set()

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def unknown_keys(self, obj: dict, allowed: set[str], path: str) -> None:
        for key in sorted(set(obj) - allowed):
            self.error(f"{path}.{key}", "unknown field")

    def run(self, graph) -> list[str]:
        if not isinstance(graph, dict):
            return ["graph: must be an object"]
        self.unknown_keys(graph, GRAPH_KEYS, "graph")
        self.check_initial(graph.get("initial"))
        self.check_flags(graph.get("flags"))
        self.check_awards(graph.get("awards"))
        self.characters: set[str] = set()
        self.check_characters(graph.get("visual"))

        nodes = graph.get("nodes")
        if not isinstance(nodes, dict) or not nodes:
            self.error("graph.nodes", "must be a non-empty object of nodes")
            return self.errors
        self.node_ids = set(nodes)

        start = graph.get("start_node")
        if not isinstance(start, str) or start not in nodes:
            self.error("graph.start_node", f"must name an existing node, got {start!r}")

        for node_id, node in nodes.items():
            self.check_node(node, f"nodes.{node_id}")

        # Graph-level checks rely on a well-formed structure, so they run only if everything above passed.
        if not self.errors:
            self.check_paths(nodes, start)
        return self.errors

    def check_initial(self, initial) -> None:
        if initial is None:
            return
        if not isinstance(initial, dict):
            self.error("graph.initial", "must be an object")
            return
        self.unknown_keys(initial, set(SCALES), "graph.initial")
        for scale in SCALES:
            if scale in initial and not (_is_int(initial[scale]) and 0 <= initial[scale] <= 100):
                self.error(f"graph.initial.{scale}", "must be an integer 0..100")

    def check_flags(self, flags) -> None:
        if flags is None:
            return
        if not isinstance(flags, dict):
            self.error("graph.flags", "must be an object of flag name -> default true/false")
            return
        for name, default in flags.items():
            if not _is_text(name):
                self.error("graph.flags", "flag names must be non-empty strings")
            if not isinstance(default, bool):
                self.error(f"graph.flags.{name}", "default must be true or false")
        self.flags = set(flags)

    def check_awards(self, awards) -> None:
        """Achievements granted at the end when their condition holds for the final state."""
        if awards is None:
            return
        if not isinstance(awards, list):
            self.error("graph.awards", "must be a list")
            return
        for i, award in enumerate(awards):
            path = f"graph.awards[{i}]"
            if not isinstance(award, dict):
                self.error(path, "must be an object")
                continue
            self.unknown_keys(award, AWARD_KEYS, path)
            if award.get("achievement") not in ACHIEVEMENTS:
                self.error(f"{path}.achievement", f"must be one of {sorted(ACHIEVEMENTS)}")
            if "when" not in award:
                self.error(f"{path}.when", "a condition is required")
            else:
                self.check_condition(award["when"], f"{path}.when", depth=0)

    def check_characters(self, visual) -> None:
        if visual is None:
            return
        if not isinstance(visual, dict):
            self.error("graph.visual", "must be an object")
            return
        self.unknown_keys(visual, {"characters"}, "graph.visual")
        characters = visual.get("characters", {})
        if not isinstance(characters, dict):
            self.error("graph.visual.characters", "must be an object of id -> character")
            return
        allowed = {"figure": vis.FIGURES, "pose": vis.POSES, "position": vis.POSITIONS}
        for cid, c in characters.items():
            path = f"graph.visual.characters.{cid}"
            if not isinstance(c, dict):
                self.error(path, "must be an object")
                continue
            self.unknown_keys(c, CHARACTER_KEYS, path)
            if "name" in c and not isinstance(c["name"], str):
                self.error(f"{path}.name", "must be a string")
            for key, values in allowed.items():
                if key in c and c[key] not in values:
                    self.error(f"{path}.{key}", f"must be one of {sorted(values)}")
        self.characters = set(characters)

    def check_node_visual(self, visual, path: str) -> None:
        if not isinstance(visual, dict):
            self.error(path, "must be an object")
            return
        self.unknown_keys(visual, NODE_VISUAL_KEYS, path)
        if "speaker" in visual and visual["speaker"] not in self.characters:
            self.error(f"{path}.speaker", "must be a character declared in graph.visual.characters")
        for key, id_key, allowed in (("moods", "character", None), ("props", "id", vis.PROPS)):
            rules = visual.get(key, [])
            if not isinstance(rules, list):
                self.error(f"{path}.{key}", "must be a list")
                continue
            for i, rule in enumerate(rules):
                rpath = f"{path}.{key}[{i}]"
                if not isinstance(rule, dict):
                    self.error(rpath, "must be an object")
                    continue
                self.unknown_keys(rule, {id_key, "when"} | ({"mood"} if key == "moods" else set()), rpath)
                if key == "moods":
                    if rule.get("character") not in self.characters:
                        self.error(f"{rpath}.character", "must be a declared character")
                    if rule.get("mood") not in vis.MOODS:
                        self.error(f"{rpath}.mood", f"must be one of {sorted(vis.MOODS)}")
                elif rule.get("id") not in allowed:
                    self.error(f"{rpath}.id", f"must be one of {sorted(allowed)}")
                if "when" in rule:
                    self.check_condition(rule["when"], f"{rpath}.when", depth=0)

    def check_node(self, node, path: str) -> None:
        if not isinstance(node, dict):
            self.error(path, "must be an object")
            return
        if not _is_text(node.get("text")):
            self.error(f"{path}.text", "must be a non-empty string")

        if "visual" in node:
            self.check_node_visual(node["visual"], f"{path}.visual")

        is_ending = node.get("is_ending", False)
        if not isinstance(is_ending, bool):
            self.error(f"{path}.is_ending", "must be true or false")
            return
        if is_ending:
            self.unknown_keys(node, ENDING_NODE_KEYS, path)
            if not _is_text(node.get("ending_summary")):
                self.error(f"{path}.ending_summary", "must be a non-empty string")
            if "outcome" in node and not _is_text(node["outcome"]):
                self.error(f"{path}.outcome", "must be a non-empty string")
            return

        self.unknown_keys(node, STEP_NODE_KEYS, path)
        if "debrief" in node and not _is_text(node["debrief"]):
            self.error(f"{path}.debrief", "must be a non-empty string")

        timer = node.get("timer_seconds")
        if timer is not None:
            if not (_is_int(timer) and TIMER_MIN <= timer <= TIMER_MAX):
                self.error(f"{path}.timer_seconds", f"must be an integer {TIMER_MIN}..{TIMER_MAX} or null")
            if "timeout" not in node:
                self.error(f"{path}.timeout", "required when the node has a timer")
            else:
                self.check_outcome(node["timeout"], f"{path}.timeout", OUTCOME_KEYS)
        elif "timeout" in node:
            self.error(f"{path}.timeout", "allowed only together with timer_seconds")

        choices = node.get("choices")
        if not isinstance(choices, list) or not choices:
            self.error(f"{path}.choices", "must be a non-empty list")
            return
        seen: set[str] = set()
        has_unconditional = False
        for i, choice in enumerate(choices):
            cpath = f"{path}.choices[{i}]"
            if not isinstance(choice, dict):
                self.error(cpath, "must be an object")
                continue
            choice_id = choice.get("id")
            if not _is_text(choice_id):
                self.error(f"{cpath}.id", "must be a non-empty string")
            elif choice_id in seen:
                self.error(f"{cpath}.id", f"duplicate choice id {choice_id!r} in this node")
            else:
                seen.add(choice_id)
            if not _is_text(choice.get("text")):
                self.error(f"{cpath}.text", "must be a non-empty string")
            if "condition" in choice:
                self.check_condition(choice["condition"], f"{cpath}.condition", depth=0)
            else:
                has_unconditional = True
            self.check_outcome(choice, cpath, CHOICE_KEYS)
        if not has_unconditional:
            self.error(f"{path}.choices", "at least one choice must have no condition, so a player always has an option")

    def check_outcome(self, outcome, path: str, allowed: set[str]) -> None:
        if not isinstance(outcome, dict):
            self.error(path, "must be an object")
            return
        self.unknown_keys(outcome, allowed, path)

        effects = outcome.get("effects", {})
        if not isinstance(effects, dict):
            self.error(f"{path}.effects", "must be an object")
        else:
            self.unknown_keys(effects, set(SCALES), f"{path}.effects")
            for scale, delta in effects.items():
                if scale in SCALES and not (_is_int(delta) and -EFFECT_LIMIT <= delta <= EFFECT_LIMIT):
                    self.error(f"{path}.effects.{scale}", f"must be an integer -{EFFECT_LIMIT}..{EFFECT_LIMIT}")

        set_flags = outcome.get("set_flags", {})
        if not isinstance(set_flags, dict):
            self.error(f"{path}.set_flags", "must be an object of flag name -> true/false")
        else:
            for name, value in set_flags.items():
                if name not in self.flags:
                    self.error(f"{path}.set_flags.{name}", "unknown flag (declare it in graph.flags)")
                if not isinstance(value, bool):
                    self.error(f"{path}.set_flags.{name}", "must be true or false")

        assessment = outcome.get("assessment", {})
        if not isinstance(assessment, dict):
            self.error(f"{path}.assessment", "must be an object of competency -> points")
        else:
            for competency, points in assessment.items():
                if competency not in COMPETENCIES:
                    self.error(f"{path}.assessment.{competency}", f"unknown competency; use one of {sorted(COMPETENCIES)}")
                elif not (_is_int(points) and 0 <= points <= MAX_POINTS):
                    self.error(f"{path}.assessment.{competency}", f"must be an integer 0..{MAX_POINTS}")

        if "explanation" in outcome and not _is_text(outcome["explanation"]):
            self.error(f"{path}.explanation", "must be a non-empty string")

        has_next, has_transitions = "next_node" in outcome, "transitions" in outcome
        if has_next == has_transitions:
            self.error(path, "needs exactly one of next_node or transitions")
        elif has_next:
            self.check_target(outcome["next_node"], f"{path}.next_node")
        else:
            self.check_transitions(outcome["transitions"], f"{path}.transitions")

    def check_transitions(self, transitions, path: str) -> None:
        if not isinstance(transitions, list) or not transitions:
            self.error(path, "must be a non-empty list")
            return
        last = len(transitions) - 1
        for i, transition in enumerate(transitions):
            tpath = f"{path}[{i}]"
            if not isinstance(transition, dict):
                self.error(tpath, "must be an object")
                continue
            self.unknown_keys(transition, TRANSITION_KEYS, tpath)
            if "condition" in transition:
                if i == last:
                    self.error(f"{tpath}.condition", "the last transition is the default and must have no condition")
                self.check_condition(transition["condition"], f"{tpath}.condition", depth=0)
            elif i != last:
                self.error(tpath, "only the last transition may omit condition; later ones would be unreachable")
            self.check_target(transition.get("next_node"), f"{tpath}.next_node")

    def check_target(self, target, path: str) -> None:
        if not isinstance(target, str) or target not in self.node_ids:
            self.error(path, f"points to unknown node {target!r}")

    def check_condition(self, condition, path: str, depth: int) -> None:
        if depth > MAX_CONDITION_DEPTH:
            self.error(path, f"nested deeper than {MAX_CONDITION_DEPTH} levels")
            return
        if not isinstance(condition, dict) or not condition:
            self.error(path, "must be a non-empty object")
            return
        keys = set(condition)
        if keys in ({"all"}, {"any"}):
            (key,) = keys
            items = condition[key]
            if not isinstance(items, list) or not items:
                self.error(f"{path}.{key}", "must be a non-empty list of conditions")
                return
            for i, item in enumerate(items):
                self.check_condition(item, f"{path}.{key}[{i}]", depth + 1)
        elif keys == {"not"}:
            self.check_condition(condition["not"], f"{path}.not", depth + 1)
        elif keys == {"flag"}:
            if condition["flag"] not in self.flags:
                self.error(f"{path}.flag", f"unknown flag {condition['flag']!r} (declare it in graph.flags)")
        elif keys == {"scale", "op", "value"}:
            if condition["scale"] not in SCALES:
                self.error(f"{path}.scale", f"must be one of {list(SCALES)}")
            if condition["op"] not in OPERATORS:
                self.error(f"{path}.op", f"must be one of {list(OPERATORS)}")
            if not (_is_int(condition["value"]) and 0 <= condition["value"] <= 100):
                self.error(f"{path}.value", "must be an integer 0..100")
        elif len(keys) == 1 and next(iter(keys)) in LEGACY_MIN:
            (key,) = keys
            if not (_is_int(condition[key]) and 0 <= condition[key] <= 100):
                self.error(f"{path}.{key}", "must be an integer 0..100")
        else:
            self.error(path, f"unknown condition form {sorted(keys)}; see docs/scenario-format.md")

    def check_paths(self, nodes: dict, start: str) -> None:
        """Every node is reachable from start and can reach an ending.

        Conditions are ignored here (every edge counts), which is safe because each
        node has an unconditional choice and each transition list ends in a default.
        """
        edges: dict[str, set[str]] = {}
        for node_id, node in nodes.items():
            targets: set[str] = set()
            if not node.get("is_ending", False):
                for choice in node["choices"]:
                    targets.update(_outcome_targets(choice))
                if "timeout" in node:
                    targets.update(_outcome_targets(node["timeout"]))
            edges[node_id] = targets

        reachable = _bfs({start}, edges)
        for node_id in nodes:
            if node_id not in reachable:
                self.error(f"nodes.{node_id}", "unreachable from start_node")

        endings = {node_id for node_id, node in nodes.items() if node.get("is_ending", False)}
        if not endings:
            self.error("graph.nodes", "at least one ending node (is_ending: true) is required")
            return
        reverse: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        for source, targets in edges.items():
            for target in targets:
                reverse[target].add(source)
        can_finish = _bfs(endings, reverse)
        for node_id in nodes:
            if node_id in reachable and node_id not in can_finish:
                self.error(f"nodes.{node_id}", "no path from this node to any ending")


def _bfs(roots: set[str], edges: dict[str, set[str]]) -> set[str]:
    seen, queue = set(roots), deque(roots)
    while queue:
        for nxt in edges[queue.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen

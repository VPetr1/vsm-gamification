class ScenarioValidationError(ValueError):
    pass


def validate_graph(graph: dict) -> None:
    """Raises ScenarioValidationError if the scenario graph is malformed.

    Checked eagerly at scenario creation time so the engine can trust the
    graph shape at runtime and never has to guard against missing nodes.
    """
    if "start_node" not in graph or "nodes" not in graph:
        raise ScenarioValidationError("graph must have 'start_node' and 'nodes'")

    nodes = graph["nodes"]
    if graph["start_node"] not in nodes:
        raise ScenarioValidationError(f"start_node '{graph['start_node']}' not found in nodes")

    for node_id, node in nodes.items():
        if node.get("is_ending"):
            if "ending_summary" not in node:
                raise ScenarioValidationError(f"ending node '{node_id}' missing ending_summary")
            continue

        if not node.get("choices"):
            raise ScenarioValidationError(f"non-ending node '{node_id}' has no choices")

        outcomes = list(node["choices"])
        if node.get("timer_seconds") is not None:
            timeout = node.get("timeout")
            if not timeout:
                raise ScenarioValidationError(f"node '{node_id}' has a timer but no timeout")
            outcomes.append(timeout)

        for outcome in outcomes:
            targets = [outcome["next_node"]] if "next_node" in outcome else [
                t["next_node"] for t in outcome.get("transitions", [])
            ]
            if not targets:
                raise ScenarioValidationError(f"outcome in node '{node_id}' has no next_node/transitions")
            for target in targets:
                if target not in nodes:
                    raise ScenarioValidationError(f"node '{node_id}' points to missing node '{target}'")

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

        if "timer_seconds" not in node:
            raise ScenarioValidationError(f"node '{node_id}' missing timer_seconds")

        if not node.get("choices"):
            raise ScenarioValidationError(f"non-ending node '{node_id}' has no choices")

        timeout = node.get("timeout")
        if not timeout or "next_node" not in timeout:
            raise ScenarioValidationError(f"node '{node_id}' missing timeout.next_node")
        if timeout["next_node"] not in nodes:
            raise ScenarioValidationError(
                f"node '{node_id}' timeout.next_node '{timeout['next_node']}' not found"
            )

        for choice in node["choices"]:
            if "next_node" not in choice:
                raise ScenarioValidationError(f"choice in node '{node_id}' missing next_node")
            if choice["next_node"] not in nodes:
                raise ScenarioValidationError(
                    f"node '{node_id}' choice next_node '{choice['next_node']}' not found"
                )

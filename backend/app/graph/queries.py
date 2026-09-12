def neighbors(graph: dict, node_id: str) -> list[dict]:
    ids = set()
    for edge in graph["edges"]:
        if edge["source"] == node_id:
            ids.add(edge["target"])
        if edge["target"] == node_id:
            ids.add(edge["source"])
    return [node for node in graph["nodes"] if node["id"] in ids]


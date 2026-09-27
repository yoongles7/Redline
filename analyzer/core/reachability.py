"""
reachability.py — BFS reachability analysis over the capability graph.

Exposes one public function:

    compute_reachability(graph: dict) -> dict
        Performs BFS from the "agent" node and returns all reachable asset
        nodes with their shortest-path depth and route.
"""

from collections import deque


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_reachability(graph: dict) -> dict:
    """
    Perform BFS from the "agent" node and return all reachable asset nodes.

    Parameters
    ----------
    graph : dict
        Output of graph.build_graph().  Expected keys:
            nodes – list of {id, label, kind}
            edges – list of {from, to, operation, sensitivity}

    Returns
    -------
    dict with keys:
        reachable_assets  – list of asset dicts (see below), ordered by depth
        max_depth         – deepest reachable asset depth (int)
        total_reachable   – count of reachable assets (int)

    Each asset dict contains:
        id            – asset node id, e.g. "asset:customers"
        label         – asset name
        type          – database / filesystem / etc.
        sensitivity   – int
        depth         – shortest path length from agent (edges)
        path          – ordered node ids from agent to asset
        path_labels   – same as path but with human-readable labels
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Build fast lookup maps from node id
    node_by_id = {n["id"]: n for n in nodes}

    # Build adjacency map: from_id -> [(to_id, operation, sensitivity), ...]
    adjacency: dict[str, list[tuple[str, object, object]]] = {}
    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        op = edge.get("operation")
        sens = edge.get("sensitivity")
        adjacency.setdefault(src, []).append((dst, op, sens))

    # Build asset metadata lookup: asset_id -> {type, sensitivity}
    # We derive type/sensitivity from the edge sensitivity and node kind.
    # The asset type is not stored on the node directly — we infer it from
    # the asset id label combined with the model's sensitivity_map embedded
    # in the edges. Since graph.py stores sensitivity on edges (tool→asset),
    # we pick the max sensitivity per asset as the canonical value.
    asset_meta: dict[str, dict] = {}
    for edge in edges:
        dst = edge["to"]
        if not dst.startswith("asset:"):
            continue
        sens = edge.get("sensitivity")
        if sens is not None:
            prev = asset_meta.get(dst, {}).get("sensitivity", 0)
            asset_meta[dst] = {"sensitivity": max(prev, sens)}

    # BFS
    # State: (node_id, depth, path_ids)
    visited: set[str] = set()
    queue: deque[tuple[str, int, list[str]]] = deque()

    start = "agent"
    queue.append((start, 0, [start]))
    visited.add(start)

    reachable_assets: list[dict] = []

    while queue:
        current_id, depth, path = queue.popleft()

        for neighbour_id, _op, _sens in adjacency.get(current_id, []):
            if neighbour_id in visited:
                continue
            visited.add(neighbour_id)

            new_path = path + [neighbour_id]
            new_depth = depth + 1

            node = node_by_id.get(neighbour_id, {})

            if node.get("kind") == "asset":
                label = node.get("label", neighbour_id)
                sensitivity = asset_meta.get(neighbour_id, {}).get("sensitivity", 0)
                path_labels = [
                    node_by_id[nid]["label"] if nid in node_by_id else nid
                    for nid in new_path
                ]
                # Derive type from the asset label: we look for the asset in
                # the model via the model's assets list, but graph.py does not
                # carry asset type on the node.  The asset id is "asset:<name>",
                # and the sensitivity_map in graph.py comes from model assets.
                # Since the type is not embedded in the graph dict, we record
                # it as empty string here; callers that need the type should
                # use the model directly. The field is included for API
                # completeness and will be populated if the graph node carries
                # a "type" key (future-proofing).
                asset_type = node.get("type", "")

                reachable_assets.append({
                    "id": neighbour_id,
                    "label": label,
                    "type": asset_type,
                    "sensitivity": sensitivity,
                    "depth": new_depth,
                    "path": new_path,
                    "path_labels": path_labels,
                })
            else:
                # Tool or other non-asset node — keep traversing
                queue.append((neighbour_id, new_depth, new_path))

    reachable_assets.sort(key=lambda a: a["depth"])

    max_depth = max((a["depth"] for a in reachable_assets), default=0)
    total_reachable = len(reachable_assets)

    return {
        "reachable_assets": reachable_assets,
        "max_depth": max_depth,
        "total_reachable": total_reachable,
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import os

    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(_here))
    sys.path.insert(0, _root)

    from analyzer.core import scanner, inference
    from analyzer.core.model import build_model
    from analyzer.core.graph import build_graph

    sample_path = os.path.join(_root, "samples", "overprivileged_agent")

    scan = scanner.scan_repository(sample_path)
    enriched = inference.infer_capabilities(scan)
    model = build_model(enriched, sample_path)
    graph = build_graph(model)
    result = compute_reachability(graph)

    print(f"total_reachable : {result['total_reachable']}")
    print(f"max_depth       : {result['max_depth']}")
    print()

    for asset in result["reachable_assets"]:
        path_str = " → ".join(asset["path_labels"])
        print(
            f"  [{asset['depth']}] {asset['label']}"
            f"  (sensitivity={asset['sensitivity']})"
            f"  path: {path_str}"
        )

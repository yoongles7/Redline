"""
graph.py — builds a directed capability graph from the Agent Security Model.

Exposes two public functions:

    build_graph(model: dict) -> dict
        Returns a simple adjacency representation with nodes and edges.

    graph_to_dot(graph: dict) -> str
        Returns a Graphviz DOT string for visualization.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_graph(model: dict) -> dict:
    """
    Build a directed capability graph from the Agent Security Model.

    Parameters
    ----------
    model : dict
        Output of model.build_model().  Expected keys:
            agent   – {name, purpose}
            tools   – [{name, operation, resources: [asset_name, ...], ...}]
            assets  – [{name, type, sensitivity, reached_by, ...}]

    Returns
    -------
    dict with keys:
        nodes – list of {id, label, kind}   kind ∈ {"agent", "tool", "asset"}
        edges – list of {from, to, operation, sensitivity}
    """
    tools = model.get("tools", [])
    assets = model.get("assets", [])

    # Build a fast sensitivity lookup: asset_name → sensitivity
    sensitivity_map = {a["name"]: a["sensitivity"] for a in assets}

    nodes = []
    edges = []

    # ----- Agent node --------------------------------------------------------
    agent_name = model.get("agent", {}).get("name", "agent")
    nodes.append({"id": "agent", "label": agent_name, "kind": "agent"})

    # Track which tool/asset nodes have already been added
    seen_tools = set()
    seen_assets = set()

    for tool in tools:
        tool_name = tool["name"]
        tool_id = f"tool:{tool_name}"
        operation = tool.get("operation")

        # ----- Tool node (deduplicated) --------------------------------------
        if tool_id not in seen_tools:
            nodes.append({"id": tool_id, "label": tool_name, "kind": "tool"})
            seen_tools.add(tool_id)

        # ----- Agent → Tool edge ---------------------------------------------
        edges.append({
            "from": "agent",
            "to": tool_id,
            "operation": None,
            "sensitivity": None,
        })

        # ----- Tool → Asset edges --------------------------------------------
        for asset_name in tool.get("resources", []):
            asset_id = f"asset:{asset_name}"

            # Asset node (deduplicated)
            if asset_id not in seen_assets:
                nodes.append({
                    "id": asset_id,
                    "label": asset_name,
                    "kind": "asset",
                })
                seen_assets.add(asset_id)

            sensitivity = sensitivity_map.get(asset_name)

            edges.append({
                "from": tool_id,
                "to": asset_id,
                "operation": operation,
                "sensitivity": sensitivity,
            })

    return {"nodes": nodes, "edges": edges}


def graph_to_dot(graph: dict) -> str:
    """
    Return a Graphviz DOT string for the given capability graph.

    Node colours:
        agent → blue  (filled)
        tool  → orange
        asset → red if sensitivity >= 4, else grey

    Parameters
    ----------
    graph : dict
        Output of build_graph().

    Returns
    -------
    str — a valid DOT digraph string.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Build a fast sensitivity lookup from the edge data
    # (asset_id → max sensitivity seen across all incoming edges)
    asset_sensitivity = {}
    for edge in edges:
        to_id = edge["to"]
        s = edge.get("sensitivity")
        if s is not None and to_id.startswith("asset:"):
            prev = asset_sensitivity.get(to_id, 0)
            asset_sensitivity[to_id] = max(prev, s)

    lines = [
        "digraph capability_graph {",
        '    rankdir=LR;',
        '    graph [fontsize=10, bgcolor="transparent", pad="0.5", nodesep="0.4", ranksep="0.6"];',
        '    node [fontsize=10, fontcolor="#e4e4e7"];',
        '    edge [fontsize=9, fontcolor="#a1a1aa"];',
        "",
    ]

    # ---- Nodes --------------------------------------------------------------
    for node in nodes:
        nid = node["id"]
        label = node["label"]
        kind = node["kind"]

        quoted_id = '"' + _dot_id(nid) + '"'
        escaped_label = label.replace('"', '\\"')

        if kind == "agent":
            attrs = (
                'shape=doubleoctagon, style=filled, '
                'fillcolor="#0a0a0a", color="#f97316", fontcolor="#e4e4e7"'
            )
        elif kind == "tool":
            attrs = (
                'shape=box, style=filled, '
                'fillcolor="#0a0a0a", color="#f97316", fontcolor="#e4e4e7"'
            )
        else:
            # asset — red border if sensitivity >= 4, otherwise orange
            s = asset_sensitivity.get(nid, 0)
            border = "#ef4444" if s >= 4 else "#f97316"
            attrs = (
                f'shape=cylinder, style=filled, '
                f'fillcolor="#0a0a0a", color="{border}", fontcolor="#e4e4e7"'
            )

        lines.append(f'    {quoted_id} [label="{escaped_label}", {attrs}];')

    lines.append("")

    # ---- Edges --------------------------------------------------------------
    for edge in edges:
        src = '"' + _dot_id(edge["from"]) + '"'
        dst = '"' + _dot_id(edge["to"]) + '"'
        op = edge.get("operation")

        if op is not None:
            edge_label = op.upper()
            lines.append(
                f'    {src} -> {dst} [label="{edge_label}", '
                f'color="#f97316", fontcolor="#a1a1aa"];'
            )
        else:
            lines.append(f'    {src} -> {dst} [color="#f97316"];')

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dot_id(node_id: str) -> str:
    """Convert a node id like 'tool:read_customer' to a valid DOT identifier."""
    # Replace characters that are invalid in unquoted DOT identifiers
    safe = node_id.replace(":", "_").replace("-", "_").replace(" ", "_")
    return safe


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

    sample_path = os.path.join(_root, "samples", "overprivileged_agent")

    scan = scanner.scan_repository(sample_path)
    enriched = inference.infer_capabilities(scan)
    model = build_model(enriched, sample_path)
    graph = build_graph(model)

    node_count = len(graph["nodes"])
    edge_count = len(graph["edges"])

    print(f"Nodes : {node_count}")
    print(f"Edges : {edge_count}")
    print()

    dot = graph_to_dot(graph)
    print(dot)

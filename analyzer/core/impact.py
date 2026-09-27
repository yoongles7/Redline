"""
impact.py — impact path detection over the reachability result.

Exposes one public function:

    detect_impact_paths(model: dict, graph: dict, reachability: dict) -> list[dict]
        Examines every reachable asset and flags paths that meet the SPEC's
        flagging criteria.  Returns a sorted list of flagged path dicts.
"""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

_INTERNAL_TYPES = {"database", "filesystem", "credentials"}
_EXTERNAL_TYPES = {"external_api", "email", "cloud"}

_SENSITIVITY_TO_SEVERITY = {
    5: "CRITICAL",
    4: "HIGH",
    3: "MEDIUM",
    2: "LOW",
    1: "LOW",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _severity(sensitivity: int) -> str:
    return _SENSITIVITY_TO_SEVERITY.get(sensitivity, "LOW")


def _category(operation: str, asset_type: str) -> str:
    if asset_type == "credentials":
        return "Credential access"
    if asset_type == "cloud":
        return "Privileged infrastructure access"
    if operation == "execute":
        return "Arbitrary command execution"
    if operation == "send":
        return "External communication"
    if operation in ("write", "delete") and asset_type in ("database", "filesystem"):
        if operation == "delete":
            return "Data deletion"
        return "Data modification"
    if asset_type == "database" and operation == "read":
        return "Sensitive data access"
    return "Sensitive data access"


def _explanation(tool_name: str, operation: str, asset_name: str, asset_type: str) -> str:
    op_upper = operation.upper() if operation else "ACCESS"
    if operation == "execute":
        return (
            f"{tool_name} has EXECUTE access to the {asset_name} {asset_type}. "
            f"The agent can run arbitrary commands against {asset_name}."
        )
    if operation == "send":
        return (
            f"{tool_name} has SEND access to {asset_name}. "
            f"The agent can transmit data to an external {asset_type} channel."
        )
    if operation in ("write", "delete"):
        verb = "modify" if operation == "write" else "delete"
        return (
            f"{tool_name} has {op_upper} access to the {asset_name} {asset_type}. "
            f"The agent can {verb} data in {asset_name}."
        )
    if asset_type == "credentials":
        return (
            f"{tool_name} has {op_upper} access to {asset_name}. "
            f"The agent can read secret credentials, potentially unlocking access to other systems."
        )
    if asset_type == "cloud":
        return (
            f"{tool_name} has {op_upper} access to {asset_name}. "
            f"The agent can affect live cloud infrastructure through {asset_name}."
        )
    # default read / sensitive data
    return (
        f"{tool_name} has {op_upper} access to the {asset_name} {asset_type}. "
        f"The agent can read data from {asset_name}."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_HIGH_IMPACT_OPS = {"write", "delete", "execute", "financial", "admin"}


def detect_impact_paths(model: dict, graph: dict, reachability: dict) -> list[dict]:
    """
    Iterate over every tool→asset edge in the graph and return flagged paths.

    Each edge produces one candidate path:
        chain  = [agent_label, tool_label, asset_label]
        length = 2

    reachability is used only to determine which asset types are reachable
    (for the cross-boundary rule); it is NOT used for path enumeration.

    Parameters
    ----------
    model : dict
        Output of model.build_model().
    graph : dict
        Output of graph.build_graph().
    reachability : dict
        Output of reachability.compute_reachability().

    Returns
    -------
    list of dicts, each containing:
        chain           – ordered node labels from agent to asset
        length          – number of edges (always 2 for MVP)
        severity        – CRITICAL / HIGH / MEDIUM / LOW
        category        – category string
        explanation     – one or two sentence string
        terminal_asset  – asset name
        operation       – operation on the tool→asset edge
    """
    # --- Build fast lookups ---------------------------------------------------

    # node_id → label
    node_label: dict[str, str] = {
        n["id"]: n.get("label", n["id"])
        for n in graph.get("nodes", [])
    }

    # asset_name → asset dict (type, sensitivity)
    asset_info: dict[str, dict] = {a["name"]: a for a in model.get("assets", [])}

    # Cross-boundary: does the agent reach any internal asset type?
    # Use the full asset list from the model (all assets the graph can reach),
    # not just the BFS-shortest-path set, so the flag is symmetric across edges.
    all_asset_types: set[str] = {a["type"] for a in model.get("assets", []) if a.get("type")}
    has_internal = bool(all_asset_types & _INTERNAL_TYPES)

    agent_label = node_label.get("agent", "agent")

    # --- Iterate over every tool→asset edge ----------------------------------

    flagged: list[dict] = []

    for edge in graph.get("edges", []):
        src = edge["from"]
        dst = edge["to"]

        if not (src.startswith("tool:") and dst.startswith("asset:")):
            continue

        operation = edge.get("operation") or ""
        tool_label = node_label.get(src, src)
        asset_label = node_label.get(dst, dst)

        info = asset_info.get(asset_label, {})
        asset_type = info.get("type", "")
        sensitivity = info.get("sensitivity", 0)

        # --- Flagging rules ---------------------------------------------------
        flag_high_sensitivity = sensitivity >= 4
        flag_high_impact_op = operation in _HIGH_IMPACT_OPS
        flag_cross_boundary = (asset_type in _EXTERNAL_TYPES) and has_internal

        if not (flag_high_sensitivity or flag_high_impact_op or flag_cross_boundary):
            continue

        chain = [agent_label, tool_label, asset_label]

        sev = _severity(sensitivity)
        cat = _category(operation, asset_type)
        expl = _explanation(tool_label, operation, asset_label, asset_type)

        flagged.append({
            "chain": chain,
            "length": 2,
            "severity": sev,
            "category": cat,
            "explanation": expl,
            "terminal_asset": asset_label,
            "operation": operation,
        })

    # --- Sort: severity desc, length desc ------------------------------------
    flagged.sort(key=lambda p: (_SEVERITY_ORDER[p["severity"]], -p["length"]))

    return flagged


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
    from analyzer.core.reachability import compute_reachability

    sample_path = os.path.join(_root, "samples", "overprivileged_agent")

    scan = scanner.scan_repository(sample_path)
    enriched = inference.infer_capabilities(scan)
    model = build_model(enriched, sample_path)
    graph = build_graph(model)
    reach = compute_reachability(graph)
    paths = detect_impact_paths(model, graph, reach)

    print(f"Flagged impact paths: {len(paths)}")
    print()
    for i, p in enumerate(paths, 1):
        chain_str = " → ".join(p["chain"])
        print(f"[{i}] {chain_str}")
        print(f"     severity      : {p['severity']}")
        print(f"     category      : {p['category']}")
        print(f"     operation     : {p['operation']}")
        print(f"     terminal_asset: {p['terminal_asset']}")
        print(f"     length        : {p['length']}")
        print(f"     explanation   : {p['explanation']}")
        print()

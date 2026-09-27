"""
metrics.py — blast-radius metrics and score computation.

Exposes one public function:

    compute_metrics(model: dict, reachability: dict, impact_paths: list) -> dict
        Computes the blast-radius metrics and 0-100 score defined in SPEC.md.
"""

# Operations considered write-capable for the write_capable_assets metric
_WRITE_OPS = {"write", "delete", "execute", "financial", "admin"}

# Operations counted as high-impact tools
_HIGH_IMPACT_OPS = {"execute", "delete", "financial", "admin"}

# Score band thresholds (inclusive upper bound)
_BANDS = [(25, "LOW"), (50, "MEDIUM"), (75, "HIGH"), (100, "CRITICAL")]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_metrics(model: dict, reachability: dict, impact_paths: list) -> dict:
    """
    Compute blast-radius metrics and score from the pipeline outputs.

    Parameters
    ----------
    model : dict
        Output of model.build_model().
    reachability : dict
        Output of reachability.compute_reachability().
    impact_paths : list
        Output of impact.detect_impact_paths().

    Returns
    -------
    dict with keys:
        reachable_assets    – int
        sensitive_assets    – int
        write_capable_assets – int
        max_depth           – int
        high_impact_tools   – int
        approval_coverage   – float
        recovery_coverage   – float
        score               – int  (0-100)
        band                – str  (LOW / MEDIUM / HIGH / CRITICAL)
    """
    tools = model.get("tools", [])
    assets = model.get("assets", [])
    controls = model.get("controls", {})
    reach_list = reachability.get("reachable_assets", [])

    # --- reachable_assets -----------------------------------------------------
    reachable_assets = len(reach_list)

    # --- sensitive_assets -----------------------------------------------------
    sensitive_assets = sum(
        1 for a in reach_list if a.get("sensitivity", 0) >= 4
    )

    # --- write_capable_assets -------------------------------------------------
    # Build: asset_name -> set of operations applied to it across all tools
    asset_ops: dict[str, set] = {}
    for tool in tools:
        op = tool.get("operation", "")
        for resource_name in tool.get("resources", []):
            asset_ops.setdefault(resource_name, set()).add(op)

    # Set of reachable asset labels (from BFS output)
    reachable_labels = {a["label"] for a in reach_list}

    write_capable_assets = sum(
        1
        for asset_name in reachable_labels
        if asset_ops.get(asset_name, set()) & _WRITE_OPS
    )

    # --- max_depth ------------------------------------------------------------
    max_depth = reachability.get("max_depth", 0)

    # --- high_impact_tools ----------------------------------------------------
    high_impact_tools = sum(
        1 for t in tools if t.get("operation") in _HIGH_IMPACT_OPS
    )

    # --- approval_coverage / recovery_coverage --------------------------------
    approval_coverage = float(controls.get("human_approval", 0.0))
    recovery_coverage = float(controls.get("rollback", 0.0))

    # --- score ----------------------------------------------------------------
    norm_sensitive = min(sensitive_assets / 5, 1.0)
    norm_write = min(write_capable_assets / 5, 1.0)
    norm_high_impact = min(high_impact_tools / 5, 1.0)

    raw_score = (
        0.35 * norm_sensitive
        + 0.25 * norm_write
        + 0.15 * (1.0 - approval_coverage)
        + 0.10 * (1.0 - recovery_coverage)
        + 0.15 * norm_high_impact
    ) * 100

    score = round(raw_score)

    # --- band -----------------------------------------------------------------
    band = "CRITICAL"
    for threshold, label in _BANDS:
        if score <= threshold:
            band = label
            break

    return {
        "reachable_assets": reachable_assets,
        "sensitive_assets": sensitive_assets,
        "write_capable_assets": write_capable_assets,
        "max_depth": max_depth,
        "high_impact_tools": high_impact_tools,
        "approval_coverage": approval_coverage,
        "recovery_coverage": recovery_coverage,
        "score": score,
        "band": band,
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
    from analyzer.core.reachability import compute_reachability
    from analyzer.core.impact import detect_impact_paths

    sample_path = os.path.join(_root, "samples", "overprivileged_agent")

    scan = scanner.scan_repository(sample_path)
    enriched = inference.infer_capabilities(scan)
    model = build_model(enriched, sample_path)
    graph = build_graph(model)
    reach = compute_reachability(graph)
    paths = detect_impact_paths(model, graph, reach)
    result = compute_metrics(model, reach, paths)

    print(f"reachable_assets     : {result['reachable_assets']}")
    print(f"sensitive_assets     : {result['sensitive_assets']}")
    print(f"write_capable_assets : {result['write_capable_assets']}")
    print(f"max_depth            : {result['max_depth']}")
    print(f"high_impact_tools    : {result['high_impact_tools']}")
    print(f"approval_coverage    : {result['approval_coverage']:.2f}")
    print(f"recovery_coverage    : {result['recovery_coverage']:.2f}")
    print()
    print(f"score                : {result['score']}")
    print(f"band                 : {result['band']}")

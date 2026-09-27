"""
mitigate.py — mitigation candidate generation.

Exposes one public function:

    generate_mitigations(model: dict, impact_paths: list, repo_path: str) -> list[dict]
        Identifies the primary tool from the highest-severity flagged impact
        path and generates three mitigation candidates (remove, restrict_scope,
        human_approval).  Each candidate includes before/after metrics computed
        by re-running the full pipeline on a deep copy of the model.
"""

import copy

from analyzer.core.graph import build_graph
from analyzer.core.reachability import compute_reachability
from analyzer.core.impact import detect_impact_paths
from analyzer.core.metrics import compute_metrics


# ---------------------------------------------------------------------------
# Severity ordering (lower number = higher severity, matches impact.py)
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Operations counted as high-impact (mirrors model.py / metrics.py)
_HIGH_IMPACT_OPS = {"execute", "delete", "financial", "admin"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pick_primary_tool(impact_paths: list) -> str | None:
    """
    Return the tool name from the highest-severity flagged impact path.

    Tie-breaking:
        1. highest severity (CRITICAL > HIGH > MEDIUM > LOW)
        2. longest chain (most edges)
        3. alphabetically first chain string
    """
    if not impact_paths:
        return None

    def _sort_key(p):
        sev_rank = _SEVERITY_ORDER.get(p.get("severity", "LOW"), 3)
        # Negate length so that longer chains sort first (ascending sort)
        neg_len = -p.get("length", 0)
        # Alphabetical on the full chain joined string (ascending = first)
        chain_str = " → ".join(p.get("chain", []))
        return (sev_rank, neg_len, chain_str)

    best = min(impact_paths, key=_sort_key)
    chain = best.get("chain", [])
    # chain = [agent_label, tool_label, asset_label, ...]
    if len(chain) < 2:
        return None
    return chain[1]


def _run_pipeline(model_copy: dict, repo_path: str) -> dict:
    """
    Re-run graph → reachability → impact → metrics on *model_copy*.
    Returns the metrics dict (with score / band).
    """
    graph = build_graph(model_copy)
    reach = compute_reachability(graph)
    paths = detect_impact_paths(model_copy, graph, reach)
    return compute_metrics(model_copy, reach, paths)


def _apply_remove(model: dict, tool_name: str) -> dict:
    """
    Return a deep copy of *model* with *tool_name* entirely removed.

    Steps:
    - Remove the tool entry from model["tools"].
    - Remove the tool from every asset's reached_by list.
    - Drop assets that are no longer reached by any tool.
    """
    m = copy.deepcopy(model)

    # Remove the tool
    m["tools"] = [t for t in m["tools"] if t["name"] != tool_name]

    # Update assets
    surviving_assets = []
    for asset in m["assets"]:
        asset["reached_by"] = [r for r in asset.get("reached_by", []) if r != tool_name]
        if asset["reached_by"]:
            surviving_assets.append(asset)
    m["assets"] = surviving_assets

    return m


def _apply_restrict_scope(model: dict, tool_name: str) -> tuple[dict, str]:
    """
    Return (modified_model, reason) for the restrict_scope candidate.

    - More than one resource: remove the highest-sensitivity asset from the
      tool's resource list and return a reason naming the removed asset.
    - Exactly one resource: downgrade the tool's operation to "read" (keeping
      the resource) and return a reason noting the operation downgrade.
    - No resources: return the model unchanged with a generic reason.

    The asset remains in model["assets"] if still reached by other tools.
    """
    m = copy.deepcopy(model)

    # Find the target tool
    target_tool = next((t for t in m["tools"] if t["name"] == tool_name), None)
    if not target_tool or not target_tool.get("resources"):
        return m, (
            f"Limit {tool_name} to a narrower resource scope by removing "
            f"its highest-sensitivity asset."
        )

    resources = target_tool["resources"]

    if len(resources) > 1:
        # Multi-resource: remove the highest-sensitivity asset
        asset_sens = {a["name"]: a.get("sensitivity", 0) for a in m["assets"]}
        worst = max(resources, key=lambda r: asset_sens.get(r, 0))
        target_tool["resources"] = [r for r in resources if r != worst]

        # Update reached_by for the dropped asset
        for asset in m["assets"]:
            if asset["name"] == worst:
                asset["reached_by"] = [
                    r for r in asset.get("reached_by", []) if r != tool_name
                ]

        # Drop assets no longer reached by any tool
        m["assets"] = [a for a in m["assets"] if a.get("reached_by")]

        reason = (
            f"Removed highest-sensitivity asset '{worst}' from {tool_name}."
        )
    else:
        # Single resource: downgrade operation to read
        original_op = target_tool.get("operation", "read")
        target_tool["operation"] = "read"
        reason = (
            f"Downgraded operation from {original_op} to read to reduce blast radius."
        )

    return m, reason


def _apply_human_approval(model: dict, tool_name: str) -> dict:
    """
    Return a deep copy of *model* that simulates adding human approval gating
    to *tool_name*.

    Simulation:
        new_coverage = (currently_gated_count + 1) / high_impact_tool_count

    where currently_gated_count = round(current_coverage * high_impact_count).

    If the tool is not a high-impact tool, this mitigation has no effect on
    coverage but is still returned for completeness.
    """
    m = copy.deepcopy(model)

    high_impact_tools = [t for t in m["tools"] if t.get("operation") in _HIGH_IMPACT_OPS]
    n = len(high_impact_tools)

    if n == 0:
        return m

    current_coverage = float(m.get("controls", {}).get("human_approval", 0.0))
    currently_gated = round(current_coverage * n)

    # Add one more gated tool (cap at n)
    new_gated = min(currently_gated + 1, n)
    new_coverage = new_gated / n

    m.setdefault("controls", {})["human_approval"] = new_coverage
    return m


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_mitigations(model: dict, impact_paths: list, repo_path: str) -> list[dict]:
    """
    Generate mitigation candidates for the primary tool in the highest-severity
    flagged impact path.

    Parameters
    ----------
    model : dict
        Output of model.build_model().
    impact_paths : list
        Output of impact.detect_impact_paths() — must already be sorted by
        severity descending (as detect_impact_paths guarantees).
    repo_path : str
        Filesystem path to the scanned repository (passed through to
        _run_pipeline for any future pipeline stages that need it).

    Returns
    -------
    list of candidate dicts, each with keys:
        action          – "remove" | "restrict_scope" | "human_approval"
        tool            – tool name targeted
        reason          – one sentence
        expected_impact – one sentence
        before          – metrics dict (same structure as metrics.py output)
        after           – metrics dict after applying the candidate
    """
    if not impact_paths:
        return []

    primary_tool = _pick_primary_tool(impact_paths)
    if primary_tool is None:
        return []

    # Verify the tool exists in the model
    tool_names = {t["name"] for t in model.get("tools", [])}
    if primary_tool not in tool_names:
        return []

    # Compute baseline metrics once
    before = _run_pipeline(model, repo_path)

    # --- remove ---------------------------------------------------------------
    candidates = []

    modified_model = _apply_remove(model, primary_tool)
    candidates.append({
        "action": "remove",
        "tool": primary_tool,
        "reason": (
            f"Remove {primary_tool} entirely to eliminate its contribution "
            f"to the agent's blast radius."
        ),
        "expected_impact": "Removes the tool and its reachable assets from the capability graph.",
        "before": before,
        "after": _run_pipeline(modified_model, repo_path),
    })

    # --- restrict_scope / scope_limit ----------------------------------------
    # Find the primary tool's current operation.
    primary_tool_entry = next(
        (t for t in model.get("tools", []) if t["name"] == primary_tool), {}
    )
    primary_op = primary_tool_entry.get("operation", "read")

    if primary_op == "read":
        # Downgrading read→read is a no-op; emit a scope_limit candidate instead.
        candidates.append({
            "action": "scope_limit",
            "tool": primary_tool,
            "reason": (
                f"Restrict {primary_tool} to a fixed allowlist of keys or resources."
            ),
            "expected_impact": (
                "Narrows the tool's inputs but does not change its operation."
            ),
            "before": before,
            "after": before,
        })
    else:
        modified_model, restrict_reason = _apply_restrict_scope(model, primary_tool)
        candidates.append({
            "action": "restrict_scope",
            "tool": primary_tool,
            "reason": restrict_reason,
            "expected_impact": "Reduces the tool's reachable assets but preserves the tool.",
            "before": before,
            "after": _run_pipeline(modified_model, repo_path),
        })

    # --- human_approval -------------------------------------------------------
    modified_model = _apply_human_approval(model, primary_tool)
    candidates.append({
        "action": "human_approval",
        "tool": primary_tool,
        "reason": (
            f"Gate {primary_tool} behind an explicit human-approval step "
            f"before execution."
        ),
        "expected_impact": "Requires explicit approval for the tool's high-impact operations.",
        "before": before,
        "after": _run_pipeline(modified_model, repo_path),
    })

    return candidates


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

    print(f"Impact paths found: {len(paths)}")
    print()

    candidates = generate_mitigations(model, paths, sample_path)

    if not candidates:
        print("No mitigation candidates generated.")
        sys.exit(0)

    print(f"Primary tool : {candidates[0]['tool']}")
    print(f"Baseline     : score={candidates[0]['before']['score']}  "
          f"band={candidates[0]['before']['band']}")
    print()

    # Find the primary tool's resource count for display
    primary_tool_entry = next(
        (t for t in model["tools"] if t["name"] == candidates[0]["tool"]), {}
    )
    resource_count = len(primary_tool_entry.get("resources", []))

    for c in candidates:
        b = c["before"]
        a = c["after"]
        print(f"Action  : {c['action']}", end="")
        if c["action"] == "restrict_scope":
            if resource_count > 1:
                print("  [multi-resource → asset removed]", end="")
            else:
                print("  [single-resource → operation downgraded]", end="")
        print()
        print(f"Tool    : {c['tool']}")
        print(f"Reason  : {c['reason']}")
        print(f"Impact  : {c['expected_impact']}")
        print(f"Before  : score={b['score']}  band={b['band']}  "
              f"sensitive={b['sensitive_assets']}  "
              f"write_capable={b['write_capable_assets']}  "
              f"high_impact_tools={b['high_impact_tools']}  "
              f"approval={b['approval_coverage']:.2f}")
        print(f"After   : score={a['score']}  band={a['band']}  "
              f"sensitive={a['sensitive_assets']}  "
              f"write_capable={a['write_capable_assets']}  "
              f"high_impact_tools={a['high_impact_tools']}  "
              f"approval={a['approval_coverage']:.2f}")
        print()

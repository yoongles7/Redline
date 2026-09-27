"""
report.py — assembles the final Redline report by running the full pipeline.

Exposes one public function:

    build_report(repo_path: str) -> dict
        Runs scanner → inference → model → graph → reachability → impact →
        metrics → mitigate and returns the structured report dict defined in
        SPEC.md's Output section.
"""

import json

from analyzer.core import scanner, inference
from analyzer.core.model import build_model
from analyzer.core.graph import build_graph, graph_to_dot
from analyzer.core.reachability import compute_reachability
from analyzer.core.impact import detect_impact_paths
from analyzer.core.metrics import compute_metrics
from analyzer.core.mitigate import generate_mitigations


# Severities that generate findings (SPEC: only CRITICAL and HIGH)
_FINDING_SEVERITIES = {"CRITICAL", "HIGH"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_finding(path: dict) -> dict:
    """
    Build a single finding dict from a flagged impact path.

    title       — short human-readable summary
    severity    — path severity
    description — tool name, operation, and terminal asset
    """
    chain = path.get("chain", [])
    tool_name = chain[1] if len(chain) >= 2 else "unknown_tool"
    asset_name = path.get("terminal_asset", chain[-1] if chain else "unknown_asset")
    operation = path.get("operation", "access")
    category = path.get("category", "")

    title = f"{tool_name} can {operation} {asset_name}"

    description = (
        f"Tool '{tool_name}' performs a '{operation}' operation on asset "
        f"'{asset_name}' ({category}). {path.get('explanation', '')}"
    )

    return {
        "title": title,
        "severity": path["severity"],
        "description": description,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_report(repo_path: str) -> dict:
    """
    Run the full analysis pipeline on *repo_path* and return the report dict.

    Parameters
    ----------
    repo_path : str
        Filesystem path to a LangChain Python repository.

    Returns
    -------
    dict matching the SPEC.md Output section schema.
    """
    # 1. Scan
    scan = scanner.scan_repository(repo_path)

    # 2. Inference
    enriched = inference.infer_capabilities(scan)

    # 3. Security model
    model = build_model(enriched, repo_path)

    # 4. Capability graph
    graph = build_graph(model)

    # 5. Reachability
    reach = compute_reachability(graph)

    # 6. Impact paths
    impact_paths = detect_impact_paths(model, graph, reach)

    # 7. Metrics + score
    metrics = compute_metrics(model, reach, impact_paths)

    # 8. Mitigations
    candidates = generate_mitigations(model, impact_paths, repo_path)

    # 9. DOT graph
    dot = graph_to_dot(graph)

    # --- Assemble findings (CRITICAL and HIGH only) --------------------------
    findings = [
        _make_finding(p)
        for p in impact_paths
        if p.get("severity") in _FINDING_SEVERITIES
    ]

    # --- Build report ---------------------------------------------------------
    return {
        "agent_name": model["agent"]["name"],
        "intended_purpose": model["agent"]["purpose"],
        "blast_radius": {
            "score": metrics["score"],
            "band": metrics["band"],
            "metrics": {
                "reachable_assets": metrics["reachable_assets"],
                "sensitive_assets": metrics["sensitive_assets"],
                "write_capable_assets": metrics["write_capable_assets"],
                "max_depth": metrics["max_depth"],
                "high_impact_tools": metrics["high_impact_tools"],
                "approval_coverage": metrics["approval_coverage"],
                "recovery_coverage": metrics["recovery_coverage"],
            },
        },
        "impact_paths": [
            {
                "chain": p["chain"],
                "length": p["length"],
                "severity": p["severity"],
                "category": p["category"],
                "explanation": p["explanation"],
            }
            for p in impact_paths
        ],
        "findings": findings,
        "mitigation": {
            "candidates": candidates,
        },
        "graph": {
            "dot": dot,
        },
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import sys

    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(_here))

    _sample = os.path.join(_root, "samples", "overprivileged_agent")
    _report = build_report(_sample)
    print(json.dumps(_report, indent=2, default=str))

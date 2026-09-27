# 10-report: Final Report Assembly

**Task:** Build `analyzer/core/report.py` — assemble the complete report dict.

**Bobcoins used:** 1.14

**Prompt:** 

Read @SPEC.md and all modules in analyzer/core/ (scanner, inference, model, graph, reachability, impact, metrics, mitigate).

Build analyzer/core/report.py.

Function: build_report(repo_path: str) -> dict

Runs the full pipeline and returns the final report dict as defined in SPEC.md's Output section:{
    "agent_name": str,
    "intended_purpose": str,
    "blast_radius": {
        "score": int,
        "band": str,
        "metrics": {
            "reachable_assets": int,
            "sensitive_assets": int,
            "write_capable_assets": int,
            "max_depth": int,
            "high_impact_tools": int,
            "approval_coverage": float,
            "recovery_coverage": float,
        },
    },
    "impact_paths": [
        {
            "chain": [str, ...],
            "length": int,
            "severity": str,
            "category": str,
            "explanation": str,
        },
        ...
    ],
    "findings": [
        {
            "title": str,        # e.g. "execute_sql can run arbitrary SQL against customers"
            "severity": str,
            "description": str,
        },
        ...
    ],
    "mitigation": {
        "candidates": [ ... ],   # from mitigate.py
    },
    "graph": {                    # optional but useful for UI
        "dot": str,               # Graphviz DOT string
    },
}Findings: Only generate findings for CRITICAL and HIGH impact paths. The title should be a short human-readable summary, description should include the tool name, operation, and terminal asset.

Include a test under if __name__ == "__main__": that runs build_report on samples/overprivileged_agent and prints the full report as formatted JSON (use json.dumps(report, indent=2, default=str)).

Do not modify any other files. Only create report.py.

**Output:** `analyzer/core/report.py`

**Test result:** overprivileged_agent produces complete report with score 40, 4 impact paths, 3 findings, 3 mitigation candidates.
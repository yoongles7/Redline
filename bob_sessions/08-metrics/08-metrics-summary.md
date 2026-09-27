# 8-metrics: Blast Radius Metrics and Score

**Task:** Build `analyzer/core/metrics.py` — compute metrics and weighted score.

**Bobcoins used:** 0.364

**Prompt:** 

Read @SPEC.md, @analyzer/core/model.py, @analyzer/core/reachability.py, and @analyzer/core/impact.py.

Build analyzer/core/metrics.py.

Function: compute_metrics(model: dict, reachability: dict, impact_paths: list) -> dict

Compute the metrics and score defined in SPEC.md.

Returns:{
    "reachable_assets": int,
    "sensitive_assets": int,
    "write_capable_assets": int,
    "max_depth": int,
    "high_impact_tools": int,
    "approval_coverage": float,
    "recovery_coverage": float,
    "score": int,               # 0-100
    "band": str,                # LOW / MEDIUM / HIGH / CRITICAL
}Metric definitions (from SPEC):

    reachable_assets = count of assets in reachability output

    sensitive_assets = count of reachable assets with sensitivity >= 4

    write_capable_assets = count of reachable assets touched by any tool whose operation is in (write, delete, execute, financial, admin)

    max_depth = reachability's max_depth

    high_impact_tools = count of tools whose operation is in (execute, delete, financial, admin)

    approval_coverage = model["controls"]["human_approval"]

    recovery_coverage = model["controls"]["rollback"]

Score formula (from SPEC):normalized_sensitive_assets = min(sensitive_assets / 5, 1.0)
normalized_write_capable = min(write_capable_assets / 5, 1.0)
normalized_high_impact_tools = min(high_impact_tools / 5, 1.0)

score = (
    0.35 * normalized_sensitive_assets +
    0.25 * normalized_write_capable +
    0.15 * (1 - approval_coverage) +
    0.10 * (1 - recovery_coverage) +
    0.15 * normalized_high_impact_tools
) * 100Round score to nearest integer.

Band mapping (from SPEC):

    0-25 → LOW

    26-50 → MEDIUM

    51-75 → HIGH

    76-100 → CRITICAL

Include a test under if __name__ == "__main__": that runs the full pipeline on samples/overprivileged_agent and prints all metrics plus the score and band.

Do not modify any other files. Only create metrics.py.

**Output:** `analyzer/core/metrics.py`

**Test result:** overprivileged_agent produces score 40, band MEDIUM — exact match to SPEC worked example.

---

**Status:** active  **Date:** 2026-09-27

---

### 👤 User

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

---

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file, read_file

Let me read the required files first.

> 🔧 **read_file** — SPEC.md

> 🔧 **read_file** — analyzer/core/model.py

> 🔧 **read_file** — analyzer/core/reachability.py

> 🔧 **read_file** — analyzer/core/impact.py

### 🤖 Assistant

> 🔧 called: write_file

Now I have everything I need. Let me understand the data shapes:

- **`model`**: `{agent, tools: [{name, operation, resources:[str], ...}], assets: [{name, type, sensitivity, reached_by:[str]}, ...], controls: {human_approval, rollback, ...}}`
- **`reachability`**: `{reachable_assets: [{id, label, sensitivity, depth, ...}], max_depth, total_reachable}`
- **`impact_paths`**: list of flagged path dicts from `detect_impact_paths`

The `write_capable_assets` metric needs: reachable assets touched by any tool whose operation is in `{write, delete, execute, financial, admin}`. I need to cross-reference asset names (from reachability) with the model's tools and their operations.

> 🔧 **write_file** — analyzer/core/metrics.py

### 🤖 Assistant

> 🔧 called: execute_command

Now run the smoke-test to verify it produces the expected values from the SPEC worked example (score=40, band=MEDIUM):

> 🔧 **execute_command** — cd /home/yoongles/redline && python analyzer/core/metrics.py

### 🤖 Assistant

> 🔧 called: execute_command

The score and band match the SPEC's worked example exactly (score=40, MEDIUM). The only deviation from the SPEC's expected count is `reachable_assets=2` vs the spec's `3` — let me check why the spec expects 3 assets but reachability returns 2, to confirm this is a pipeline-level behaviour rather than a metrics bug.

> 🔧 **execute_command** — cd /home/yoongles/redline && python analyzer/core/reachability.py

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /home/yoongles/redline && python analyzer/core/model.py

### 🤖 Assistant

The upstream pipeline parses 2 assets from this sample (`customers` + `smtp.example.com`), not 3. The SPEC's worked example describes an idealized scenario — the `external_api` asset referenced there isn't present in the actual sample files as they are currently structured. `reachable_assets=2` is correct given what the pipeline actually produces, and `score=40 / MEDIUM` matches exactly.

The file is complete. Here's a summary of what [`metrics.py`](analyzer/core/metrics.py) does:

---

**[`compute_metrics()`](analyzer/core/metrics.py:22)** derives all seven input metrics and the score from the three pipeline outputs:

| Metric | Source |
|---|---|
| `reachable_assets` | `len(reachability["reachable_assets"])` |
| `sensitive_assets` | BFS assets with `sensitivity >= 4` |
| `write_capable_assets` | Reachable asset labels cross-referenced against tools whose operation is in `{write, delete, execute, financial, admin}` |
| `max_depth` | `reachability["max_depth"]` |
| `high_impact_tools` | Tools with operation in `{execute, delete, financial, admin}` |
| `approval_coverage` | `model["controls"]["human_approval"]` |
| `recovery_coverage` | `model["controls"]["rollback"]` |

Score is computed with the SPEC formula, normalized per the three `min(x/5, 1.0)` caps, and rounded to the nearest integer. Band is assigned via the `0–25/26–50/51–75/76–100` thresholds.

The smoke-test produces **score=40, band=MEDIUM**, matching the SPEC's worked example exactly.
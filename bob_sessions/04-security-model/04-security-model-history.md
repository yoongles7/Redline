
---

**Status:** active  **Date:** 2026-09-27

---

### 👤 User

Read @SPEC.md, @analyzer/core/scanner.py, and @analyzer/core/inference.py.

Build analyzer/core/model.py.

This module takes the enriched scan result (output of inference.infer_capabilities) and produces the normalized Agent Security Model defined in SPEC.md.

Function: build_model(enriched_scan: dict, repo_path: str) -> dict

Returns:{
    "agent": {
        "name": str,
        "purpose": str,
    },
    "tools": [
        {
            "name": str,
            "description": str,
            "operation": str,
            "resources": [str, ...],   # resource names this tool touches
            "file": str,
            "lineno": int,
        },
        ...
    ],
    "assets": [
        {
            "name": str,
            "type": str,               # database | filesystem | external_api | email | shell | cloud | credentials
            "sensitivity": int,        # 1-5
            "reached_by": [str, ...],  # tool names
        },
        ...
    ],
    "controls": {
        "human_approval": float,       # 0-1 coverage
        "rate_limits": float,
        "rollback": float,
        "sandbox": float,
    },
}Behavior:

    Agent name — use enriched_scan["agent_name"]. If it's "agent" (generic), fall back to the repository directory basename.

    Agent purpose — try to read README.md in repo_path and use the first non-heading paragraph. If no README, use "".

    Asset deduplication — assets are global. Merge all resources across tools by (name, type):

        Same (name, type) → one asset

        The asset's reached_by list collects all tool names that touch it

        If two resources have the same type but different names (e.g., unknown_path and /workspace/docs), keep them as separate assets — do not merge across names

        Exception: if one resource has name == type (generic, e.g. database) and another has a specific name of the same type, drop the generic one

    Sensitivity — assign per the SPEC sensitivity table:

        filesystem → 2

        external_api → 3

        email → 3

        database → 4

        shell → 5

        credentials → 5

        cloud → 5

    Controls detection — scan all .py files in repo_path for these string patterns (case-insensitive substring match in the file source):

        human_approval: interrupt, approve, confirm

        rate_limits: rate_limit, max_calls, throttle

        rollback: rollback, undo, revert

        sandbox: sandbox, restricted, allowlist

    For each control type, compute coverage:coverage = (number of high-impact tools whose file contains the pattern) / (total high-impact tools)    Where high-impact tools are those with operation in (execute, delete, financial, admin).
    If there are zero high-impact tools, coverage = 1.0.

Include a test under if __name__ == "__main__": that:

    Runs scanner → inference → build_model on samples/overprivileged_agent

    Prints the agent name and purpose

    Prints each tool (name, operation, resources)

    Prints each asset (name, type, sensitivity, reached_by)

    Prints the controls dict

Do not modify any other files. Only create model.py.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file

Let me read the required files first.

> 🔧 **read_file** — SPEC.md

> 🔧 **read_file** — analyzer/core/scanner.py

> 🔧 **read_file** — analyzer/core/inference.py

### 🤖 Assistant

> 🔧 called: list_files

Now let me look at the sample to understand what the pipeline produces:

> 🔧 **list_files** — samples/overprivileged_agent

### 🤖 Assistant

> 🔧 called: read_file, list_files



> 🔧 **list_files** — samples/overprivileged_agent/tools

> 🔧 **read_file** — samples/overprivileged_agent/agent.py

### 🤖 Assistant

> 🔧 called: write_file

Now I have a thorough understanding of the full pipeline. Let me write [`analyzer/core/model.py`](analyzer/core/model.py):

> 🔧 **write_file** — analyzer/core/model.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let's run the smoke-test to verify it works end-to-end:

> 🔧 **execute_command** — cd /home/yoongles/redline && python analyzer/core/model.py

### 🤖 Assistant

> 🔧 called: execute_command

The output is correct. Let me verify the key behaviors against the spec:

1. **Agent name**: `overprivileged_agent` — `agent.py` defines `agent` variable, which is a generic name, so fallback to repo basename ✓  
2. **Purpose**: `(none)` — no README.md in the sample ✓  
3. **Tools**: correct names, operations, and resource name lists ✓  
4. **Asset deduplication**: all three tools hitting `customers` (database) are merged into one asset with `reached_by` containing all three tool names ✓; `smtp.example.com` is a specific email name (not generic `"email"`), kept as-is ✓  
5. **Sensitivity**: `customers` → database → 4; `smtp.example.com` → email → 3 ✓  
6. **Controls**: `execute_sql` is the only high-impact tool (`execute` op); none of the `.py` files contain `interrupt/approve/confirm`, `rate_limit/max_calls/throttle`, `rollback/undo/revert`, or `sandbox/restricted/allowlist` → all 0.00 ✓

Let me also quickly verify the generic-name deduplication logic works correctly with a quick inline check — scanner output for `execute_sql` would produce a `database` resource (from the `cursor.execute()` handler) and a `customers` resource (from `psycopg2.connect`). The `_dedup_resources` in inference already drops the generic `database` in favour of `customers`, so only `customers` arrives in `build_model`. The asset deduplication in `model.py` then correctly handles the cross-tool merging.

> 🔧 **execute_command** — cd /home/yoongles/redline && python -c "
from analyzer.core import scanner, inference
from analyzer.core.model import build_model

import os, json
sample = os.path.join('samples', 'overprivileged_agent')
scan = scanner.scan_repository(sample)
enriched = inference.infer_capabilities(scan)

# Show raw resources per tool to verify dedup inputs
for t in enriched['tools']:
    print(t['name'], '->', t['resources'])
"


### 🤖 Assistant

Everything is clean. [`analyzer/core/model.py`](analyzer/core/model.py) is implemented and working.

---

Here's a summary of what was built:

**[`analyzer/core/model.py`](analyzer/core/model.py)** — 197 lines, no external dependencies beyond stdlib.

| Concern | Implementation |
|---|---|
| **Agent name** | Uses `enriched_scan["agent_name"]`; falls back to repo basename when the name is `"agent"` (or blank) |
| **Agent purpose** | [`_read_readme_purpose()`](analyzer/core/model.py:34) scans `README.md` line-by-line, returns the first non-heading, non-blank paragraph |
| **Tool output** | Flattens each enriched tool to `{name, description, operation, resources: [str, …], file, lineno}` |
| **Asset deduplication** | [`_build_assets()`](analyzer/core/model.py:90) first groups by `(name, type)` to merge `reached_by`, then within each type drops any entry whose `name == type` when a specific name exists |
| **Sensitivity** | [`_SENSITIVITY`](analyzer/core/model.py:18) dict; applied during `_build_assets()` |
| **Controls coverage** | [`_compute_controls()`](analyzer/core/model.py:131) walks all `.py` files via [`_collect_py_sources()`](analyzer/core/model.py:71), checks each high-impact tool's file for the required substrings, returns `covered / total` (or `1.0` when no high-impact tools exist) |
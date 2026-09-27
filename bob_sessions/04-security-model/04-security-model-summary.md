#04-model: Agent Security Model

**Task:** Build `analyzer/core/model.py` — normalized internal representation.

**Bobcoins used:** 0.436

**Prompt:** 

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

**Output:** `analyzer/core/model.py`

**Test result:** overprivileged_agent produces 2 assets:
- customers (database, sensitivity 4, reached by 3 tools)
- smtp.example.com (email, sensitivity 3, reached by send_email)
Controls all 0.0 (no safeguards detected).
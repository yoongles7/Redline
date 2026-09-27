# 9-mitigate: Mitigation Candidate Generation

**Task:** Build `analyzer/core/mitigate.py` — generate mitigation candidates with before/after metrics.

**Bobcoins used:** 1.19

**Prompt:** 

Read @SPEC.md, @analyzer/core/model.py, @analyzer/core/metrics.py, and @analyzer/core/impact.py.

Build analyzer/core/mitigate.py.

Function: generate_mitigations(model: dict, impact_paths: list, repo_path: str) -> list[dict]

Generate mitigation candidates. Each candidate is a dict:{
    "action": str,            # "remove", "restrict_scope", "read_only", "human_approval", "sandbox", "rate_limit"
    "tool": str,              # the tool the mitigation targets
    "reason": str,            # one sentence
    "expected_impact": str,   # one sentence
    "before": dict,           # metrics before mitigation
    "after": dict,            # metrics after mitigation
}Algorithm:

    Identify the primary tool: the tool in the highest-severity flagged impact path. If ties, pick the longest chain; if still tied, alphabetically first.

    For the primary tool, generate 3 candidate mitigations:

        "remove" — remove the tool entirely

        "restrict_scope" — keep the tool but limit it to a narrower resource scope (simulated: remove the highest-sensitivity asset from the tool's resource list)

        "human_approval" — keep the tool but mark it as requiring approval (simulated: set controls.human_approval to the fraction of high-impact tools that are gated — i.e., add this tool as gated)

    For each candidate, apply the change to a deep copy of the model, then re-run:

        model (modified) → graph → reachability → impact → metrics

    Produce before and after metric dicts (the same structure as metrics.py output).

    If the primary tool is not found, or no impact paths exist, return [].

Expected impact strings:

    remove: "Removes the tool and its reachable assets from the capability graph."

    restrict_scope: "Reduces the tool's reachable assets but preserves the tool."

    human_approval: "Requires explicit approval for the tool's high-impact operations."

Include a test under if __name__ == "__main__": that runs the full pipeline plus mitigations on samples/overprivileged_agent and prints each candidate with before/after scores.

Do not modify any other files. Only create mitigate.py.

**Fix applied:** restrict_scope falls back to read-only downgrade when the tool has only one resource.

**Output:** `analyzer/core/mitigate.py`

**Test result:** overprivileged_agent — primary tool execute_sql. Three candidates:
- remove → 37
- restrict_scope (downgrade to read) → 37
- human_approval → 25 (best)

Key insight: gating preserves functionality while removing blast radius.
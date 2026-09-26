"""
classifier.py — Classify each tool in a parsed config by permission severity.

Accepts the dict produced by parser.parse() and returns a new dict with the
same structure, except each tool gains a "severity" field (str).

Severity per permission (SPEC.md):
    read    -> LOW
    write   -> MEDIUM
    network -> HIGH
    execute -> CRITICAL

When a tool carries multiple permissions the highest severity wins.
"""

import copy

# Severity rank: higher index = higher severity.
_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Per-permission baseline severity.
_PERMISSION_SEVERITY: dict[str, str] = {
    "read":    "LOW",
    "write":   "MEDIUM",
    "network": "HIGH",
    "execute": "CRITICAL",
}


def _highest_severity(permissions: list[str]) -> str:
    """Return the highest severity label for a list of permissions.

    Falls back to "LOW" when *permissions* is empty (no permissions declared).
    """
    if not permissions:
        return "LOW"
    return max(
        (_PERMISSION_SEVERITY[p] for p in permissions),
        key=lambda s: _SEVERITY_ORDER.index(s),
    )


def classify(config: dict) -> dict:
    """Return a deep copy of *config* with a ``severity`` field added to every tool.

    Args:
        config: A validated agent config dict as returned by ``parser.parse()``.

    Returns:
        A new dict (the original is never mutated) where each tool dict has an
        additional ``"severity"`` key whose value is one of:
        ``"LOW"``, ``"MEDIUM"``, ``"HIGH"``, or ``"CRITICAL"``.
    """
    result = copy.deepcopy(config)
    for tool in result["tools"]:
        tool["severity"] = _highest_severity(tool["permissions"])
    return result


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pathlib
    import sys

    # Resolve the samples directory relative to this file's location.
    _repo_root = pathlib.Path(__file__).parent.parent.parent
    sys.path.insert(0, str(_repo_root))

    from analyzer.core import parser  # noqa: E402

    sample_path = _repo_root / "samples" / "high_risk_medicare.json"
    config = parser.parse(str(sample_path))
    classified = classify(config)

    print(f"Agent : {classified['agent_name']}")
    print(f"Purpose: {classified['intended_purpose']}\n")
    for tool in classified["tools"]:
        perms = ", ".join(tool["permissions"]) or "(none)"
        print(f"  {tool['name']:<30} permissions={perms:<20} severity={tool['severity']}")

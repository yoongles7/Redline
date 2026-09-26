"""
report.py — Assemble a structured blast-radius report.

Accepts the parsed config, classified tools, and detected attack paths and
returns a single report dict ready for serialisation.

Report shape:
    {
        "agent_name":        str,
        "intended_purpose":  str,
        "blast_radius":      str,   # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
        "attack_paths":      list,  # unchanged from paths.detect()
        "mitigations": [
            {
                "action":      "remove" | "restrict",
                "tool":        str,
                "reason":      str,
                "alternative": str,  # present only when action == "restrict"
            },
            ...
        ],
    }
"""

from __future__ import annotations

_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Suggested control per permission, used when action == "restrict".
# When a tool has multiple relevant permissions the highest-severity one wins.
_PERMISSION_ALTERNATIVE: dict[str, str] = {
    "execute": "JIT",
    "network": "segmentation",
    "write":   "approval threshold",
    "read":    "scoping",
}

# Severity rank for each permission (used to pick the best alternative).
_PERMISSION_SEVERITY_RANK: dict[str, int] = {
    "read":    0,
    "write":   1,
    "network": 2,
    "execute": 3,
}


def _overall_blast_radius(attack_paths: list[dict]) -> str:
    """Return the highest severity among all detected paths, or 'LOW' if none."""
    if not attack_paths:
        return "LOW"
    return max(
        (p["severity"] for p in attack_paths),
        key=lambda s: _SEVERITY_ORDER.index(s),
    )


def _purpose_implies_permission(intended_purpose: str, permissions: list[str]) -> bool:
    """Return True if any permission word appears in *intended_purpose* (case-insensitive)."""
    purpose_lower = intended_purpose.lower()
    return any(perm.lower() in purpose_lower for perm in permissions)


def _best_alternative(permissions: list[str]) -> str:
    """Pick the alternative control that matches the highest-severity permission."""
    if not permissions:
        return "scoping"
    best = max(permissions, key=lambda p: _PERMISSION_SEVERITY_RANK.get(p, 0))
    return _PERMISSION_ALTERNATIVE.get(best, "scoping")


def _build_mitigations(
    intended_purpose: str,
    classified_tools: list[dict],
    attack_paths: list[dict],
) -> list[dict]:
    """Build a deduplicated mitigation entry for every tool involved in any path."""
    # Collect tool names that appear in at least one attack path chain, in
    # first-occurrence order.
    seen: set[str] = set()
    involved_names: list[str] = []
    for path in attack_paths:
        for name in path["chain"]:
            if name not in seen:
                seen.add(name)
                involved_names.append(name)

    # Index classified tools by name for O(1) lookup.
    tool_index: dict[str, dict] = {t["name"]: t for t in classified_tools}

    mitigations: list[dict] = []
    for name in involved_names:
        tool = tool_index[name]
        permissions = tool["permissions"]

        if _purpose_implies_permission(intended_purpose, permissions):
            action = "restrict"
            mitigation: dict = {
                "action":      action,
                "tool":        name,
                "reason":      (
                    f"'{name}' has {permissions} permissions that overlap with the "
                    f"intended purpose but still expand the blast radius beyond "
                    f"what is strictly necessary."
                ),
                "alternative": _best_alternative(permissions),
            }
        else:
            mitigation = {
                "action": "remove",
                "tool":   name,
                "reason": (
                    f"'{name}' has {permissions} permissions that are not implied "
                    f"by the intended purpose and should be eliminated entirely."
                ),
            }

        mitigations.append(mitigation)

    return mitigations


def generate(config: dict, classified: dict, attack_paths: list[dict]) -> dict:
    """Assemble and return the final blast-radius report.

    Args:
        config:       Validated agent config dict from ``parser.parse()``.
        classified:   Config dict with per-tool severity from ``classifier.classify()``.
        attack_paths: List of attack path dicts from ``paths.detect()``.

    Returns:
        A report dict as described in the module docstring.
    """
    return {
        "agent_name":      config["agent_name"],
        "intended_purpose": config["intended_purpose"],
        "blast_radius":    _overall_blast_radius(attack_paths),
        "attack_paths":    attack_paths,
        "mitigations":     _build_mitigations(
            config["intended_purpose"],
            classified["tools"],
            attack_paths,
        ),
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import pathlib
    import sys

    _repo_root = pathlib.Path(__file__).parent.parent.parent
    sys.path.insert(0, str(_repo_root))

    from analyzer.core import parser, classifier, paths  # noqa: E402

    sample_path = _repo_root / "samples" / "high_risk_medicare.json"
    _config     = parser.parse(str(sample_path))
    _classified = classifier.classify(_config)
    _paths      = paths.detect(_classified)
    _report     = generate(_config, _classified, _paths)

    print(json.dumps(_report, indent=2))

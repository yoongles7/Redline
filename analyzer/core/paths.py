"""
paths.py — Detect attack paths in a classified agent config.

Accepts the dict produced by classifier.classify() and applies the detection
rules from SPEC.md to return a list of attack path dicts, one per matched rule.

Detection rules (SPEC.md):
    read + network          -> Data exfiltration,       HIGH
    execute alone           -> Arbitrary code execution, CRITICAL
    execute + write         -> Persistence,              HIGH
    execute + network       -> Command & control,        CRITICAL
    read + write + network  -> Full compromise,          CRITICAL
    write alone             -> Data tampering,           MEDIUM
    read + write            -> Data modification,        MEDIUM

Each returned path dict has:
    chain       -- list of tool names whose permissions satisfy the rule
    category    -- risk category string (e.g. "Data exfiltration")
    severity    -- "MEDIUM", "HIGH", or "CRITICAL"
    explanation -- one or two plain-English sentences describing the risk
"""

from __future__ import annotations

from typing import TypedDict


class AttackPath(TypedDict):
    chain: list[str]
    category: str
    severity: str
    explanation: str


# ── Detection rule table ─────────────────────────────────────────────────────
# Each entry:
#   required  -- frozenset of permissions that must ALL be present
#   excluded  -- frozenset of permissions that must NOT be present (for "alone" rules)
#   category  -- risk label
#   severity  -- severity level
#   explanation -- plain-English description

_RULES: list[dict] = [
    {
        "required": frozenset({"read", "write", "network"}),
        "excluded": frozenset(),
        "category": "Full compromise",
        "severity": "CRITICAL",
        "explanation": (
            "An attacker can read sensitive data, modify it in place, and "
            "exfiltrate everything to an external server. This combination "
            "enables complete end-to-end data compromise."
        ),
    },
    {
        "required": frozenset({"execute", "network"}),
        "excluded": frozenset(),
        "category": "Command & control",
        "severity": "CRITICAL",
        "explanation": (
            "Arbitrary code can be executed and its output (or further "
            "instructions) relayed over the network, allowing an attacker "
            "to establish a persistent command-and-control channel."
        ),
    },
    {
        "required": frozenset({"execute"}),
        "excluded": frozenset({"network", "write"}),
        "category": "Arbitrary code execution",
        "severity": "CRITICAL",
        "explanation": (
            "The agent can run arbitrary commands on the host system with "
            "no network or write constraint to limit the blast radius."
        ),
    },
    {
        "required": frozenset({"execute", "write"}),
        "excluded": frozenset(),
        "category": "Persistence",
        "severity": "HIGH",
        "explanation": (
            "Code execution combined with write access lets an attacker "
            "drop and persist malicious payloads on the filesystem."
        ),
    },
    {
        "required": frozenset({"read", "network"}),
        "excluded": frozenset(),
        "category": "Data exfiltration",
        "severity": "HIGH",
        "explanation": (
            "The agent can read local data and transmit it to an external "
            "endpoint, enabling silent exfiltration of sensitive information."
        ),
    },
    {
        "required": frozenset({"read", "write"}),
        "excluded": frozenset(),
        "category": "Data modification",
        "severity": "MEDIUM",
        "explanation": (
            "Read and write access together allow an attacker to inspect "
            "existing data and overwrite it with tampered content."
        ),
    },
    {
        "required": frozenset({"write"}),
        "excluded": frozenset({"read", "execute", "network"}),
        "category": "Data tampering",
        "severity": "MEDIUM",
        "explanation": (
            "Write-only access allows an attacker to overwrite or corrupt "
            "stored data without being able to read it first."
        ),
    },
]


def detect(classified_config: dict) -> list[AttackPath]:
    """Detect attack paths in a classified agent config.

    Args:
        classified_config: The dict returned by ``classifier.classify()``.

    Returns:
        A list of :class:`AttackPath` dicts, one per matched detection rule.
        All matching rules are returned; no deduplication is applied.
    """
    tools: list[dict] = classified_config["tools"]

    # Build a mapping from permission -> list of tool names that carry it.
    perm_to_tools: dict[str, list[str]] = {}
    for tool in tools:
        for perm in tool["permissions"]:
            perm_to_tools.setdefault(perm, []).append(tool["name"])

    all_perms: frozenset[str] = frozenset(perm_to_tools)

    paths: list[AttackPath] = []
    for rule in _RULES:
        required: frozenset[str] = rule["required"]
        excluded: frozenset[str] = rule["excluded"]

        if not required.issubset(all_perms):
            continue
        if excluded and excluded.intersection(all_perms):
            continue

        # Collect the tools that contribute the required permissions (in rule order).
        chain: list[str] = []
        seen: set[str] = set()
        for perm in sorted(required):  # sorted for deterministic order
            for name in perm_to_tools[perm]:
                if name not in seen:
                    chain.append(name)
                    seen.add(name)

        paths.append(
            AttackPath(
                chain=chain,
                category=rule["category"],
                severity=rule["severity"],
                explanation=rule["explanation"],
            )
        )

    return paths


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pathlib
    import sys

    _repo_root = pathlib.Path(__file__).parent.parent.parent
    sys.path.insert(0, str(_repo_root))

    from analyzer.core import parser, classifier  # noqa: E402

    sample_path = _repo_root / "samples" / "high_risk_medicare.json"
    config = parser.parse(str(sample_path))
    classified = classifier.classify(config)
    detected = detect(classified)

    print(f"Agent : {classified['agent_name']}")
    print(f"Purpose: {classified['intended_purpose']}")
    print(f"\nDetected {len(detected)} attack path(s):\n")
    for i, path in enumerate(detected, 1):
        print(f"  [{i}] chain      : {path['chain']}")
        print(f"      category   : {path['category']}")
        print(f"      severity   : {path['severity']}")
        print(f"      explanation: {path['explanation']}")
        print()

"""
model.py — builds the normalized Agent Security Model from enriched scan output.

Takes the dict returned by inference.infer_capabilities() and produces the
structured security model defined in SPEC.md.
"""

import os
import re


# ---------------------------------------------------------------------------
# Sensitivity table
# ---------------------------------------------------------------------------

_SENSITIVITY = {
    "filesystem": 2,
    "external_api": 3,
    "email": 3,
    "database": 4,
    "shell": 5,
    "credentials": 5,
    "cloud": 5,
}

# Operations considered high-impact for controls coverage
_HIGH_IMPACT_OPS = {"execute", "delete", "financial", "admin"}

# Control patterns: name → list of lowercase substrings to match
_CONTROL_PATTERNS = {
    "human_approval": ["interrupt", "approve", "confirm"],
    "rate_limits": ["rate_limit", "max_calls", "throttle"],
    "rollback": ["rollback", "undo", "revert"],
    "sandbox": ["sandbox", "restricted", "allowlist"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_readme_purpose(repo_path: str) -> str:
    """
    Return the first non-heading paragraph from README.md in repo_path.
    Returns "" if no README is found or no paragraph can be extracted.
    """
    for name in ("README.md", "README.MD", "readme.md"):
        readme = os.path.join(repo_path, name)
        if os.path.isfile(readme):
            try:
                with open(readme, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                return ""
            for line in text.splitlines():
                stripped = line.strip()
                # Skip blank lines and headings
                if stripped and not stripped.startswith("#"):
                    return stripped
            return ""
    return ""


def _load_py_source(path: str) -> str:
    """Return the lowercased source of a .py file, or "" on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().lower()
    except OSError:
        return ""


def _collect_py_sources(repo_path: str) -> dict:
    """
    Walk repo_path and return {rel_path: lowercased_source} for every .py file.
    Skips common non-project directories.
    """
    _SKIP = {"venv", ".venv", "__pycache__", ".git", "node_modules",
              ".tox", "build", "dist"}
    sources = {}
    for dirpath, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, repo_path)
            sources[rel_path] = _load_py_source(abs_path)
    return sources


def _file_contains_any(source: str, patterns: list) -> bool:
    """Return True if source (lowercased) contains any of the given substrings."""
    return any(p in source for p in patterns)


# ---------------------------------------------------------------------------
# Asset deduplication
# ---------------------------------------------------------------------------

def _build_assets(tools: list) -> list:
    """
    Merge tool resources into a global deduplicated asset list.

    Rules (from SPEC):
    - Same (name, type) → one asset; reached_by collects all touching tool names.
    - Different names within same type → separate assets.
    - If one resource has name == type (generic) AND another has a specific name
      of the same type → drop the generic one.
    """
    # First pass: collect all (name, type) → set of tool names
    asset_map = {}   # (name, type) -> {"name", "type", "reached_by": []}

    for tool in tools:
        for resource in tool.get("resources", []):
            key = (resource["name"], resource["type"])
            if key not in asset_map:
                asset_map[key] = {
                    "name": resource["name"],
                    "type": resource["type"],
                    "reached_by": [],
                }
            if tool["name"] not in asset_map[key]["reached_by"]:
                asset_map[key]["reached_by"].append(tool["name"])

    # Second pass: drop generic names when a specific name exists for that type
    # Group by type
    by_type = {}
    for (name, rtype), entry in asset_map.items():
        by_type.setdefault(rtype, []).append(entry)

    result = []
    for rtype, entries in by_type.items():
        specific = [e for e in entries if e["name"] != rtype]
        if specific:
            result.extend(specific)
        else:
            result.extend(entries)

    # Assign sensitivity
    for asset in result:
        asset["sensitivity"] = _SENSITIVITY.get(asset["type"], 1)

    return result


# ---------------------------------------------------------------------------
# Controls detection
# ---------------------------------------------------------------------------

def _compute_controls(tools: list, py_sources: dict) -> dict:
    """
    For each control type, compute:
        coverage = high-impact tools whose file contains the pattern
                   / total high-impact tools
    If no high-impact tools exist, coverage = 1.0.
    """
    high_impact = [t for t in tools if t.get("operation") in _HIGH_IMPACT_OPS]

    if not high_impact:
        return {name: 1.0 for name in _CONTROL_PATTERNS}

    controls = {}
    for ctrl_name, patterns in _CONTROL_PATTERNS.items():
        covered = 0
        for tool in high_impact:
            source = py_sources.get(tool.get("file", ""), "")
            if _file_contains_any(source, patterns):
                covered += 1
        controls[ctrl_name] = covered / len(high_impact)

    return controls


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_model(enriched_scan: dict, repo_path: str) -> dict:
    """
    Build the normalized Agent Security Model from enriched scan output.

    Parameters
    ----------
    enriched_scan : dict
        Output of inference.infer_capabilities().
    repo_path : str
        Filesystem path to the scanned repository (used for README and
        controls detection).

    Returns
    -------
    dict with keys: agent, tools, assets, controls.
    """
    raw_tools = enriched_scan.get("tools", [])

    # --- Agent ---------------------------------------------------------------
    agent_name = enriched_scan.get("agent_name", "")
    if not agent_name or agent_name == "agent":
        agent_name = os.path.basename(os.path.normpath(repo_path))

    purpose = _read_readme_purpose(repo_path)

    # --- Tools ---------------------------------------------------------------
    tools = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "operation": t.get("operation", "read"),
            "resources": [r["name"] for r in t.get("resources", [])],
            "file": t.get("file", ""),
            "lineno": t.get("lineno", 0),
        }
        for t in raw_tools
    ]

    # --- Assets --------------------------------------------------------------
    assets = _build_assets(raw_tools)

    # --- Controls ------------------------------------------------------------
    py_sources = _collect_py_sources(repo_path)
    controls = _compute_controls(raw_tools, py_sources)

    return {
        "agent": {
            "name": agent_name,
            "purpose": purpose,
        },
        "tools": tools,
        "assets": assets,
        "controls": controls,
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import os as _os

    _here = _os.path.dirname(_os.path.abspath(__file__))
    _root = _os.path.dirname(_os.path.dirname(_here))
    sys.path.insert(0, _root)

    from analyzer.core import scanner, inference

    sample_path = _os.path.join(_root, "samples", "overprivileged_agent")

    scan = scanner.scan_repository(sample_path)
    enriched = inference.infer_capabilities(scan)
    model = build_model(enriched, sample_path)

    print(f"Agent name : {model['agent']['name']}")
    print(f"Purpose    : {model['agent']['purpose'] or '(none)'}")
    print()

    print("Tools:")
    for t in model["tools"]:
        print(f"  {t['name']:25s}  op={t['operation']:10s}  resources={t['resources']}")
    print()

    print("Assets:")
    for a in model["assets"]:
        print(
            f"  {a['name']:25s}  type={a['type']:12s}  "
            f"sensitivity={a['sensitivity']}  "
            f"reached_by={a['reached_by']}"
        )
    print()

    print("Controls:")
    for ctrl, cov in model["controls"].items():
        print(f"  {ctrl:18s}  {cov:.2f}")

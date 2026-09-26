"""
parser.py — Parse and validate an agent config JSON.

Accepts either a raw JSON string or a file path (str ending with .json or an
existing file path).  Returns a validated dict with the shape expected by the
rest of the Redline pipeline.
"""

import json
import os
from typing import Union

VALID_PERMISSIONS = {"read", "write", "execute", "network"}

# ── Top-level keys ──────────────────────────────────────────────────────────
_REQUIRED_TOP = ("agent_name", "intended_purpose", "tools")

# ── Per-tool keys ───────────────────────────────────────────────────────────
_REQUIRED_TOOL = ("name", "description", "parameters", "permissions")


def parse(source: Union[str, os.PathLike]) -> dict:
    """Parse an agent config from a JSON string or a file path.

    Args:
        source: A raw JSON string **or** a path to a .json file.

    Returns:
        A validated dict::

            {
                "agent_name":        str,
                "intended_purpose":  str,
                "tools": [
                    {
                        "name":        str,
                        "description": str,
                        "parameters":  list[str],
                        "permissions": list[str],  # subset of VALID_PERMISSIONS
                    },
                    ...
                ],
            }

    Raises:
        FileNotFoundError: If *source* looks like a path but the file is absent.
        json.JSONDecodeError: If the input is not valid JSON.
        ValueError: If required fields are missing or permissions are invalid.
    """
    raw = _load_raw(source)
    data = _parse_json(raw)
    return _validate(data)


# ── Internal helpers ────────────────────────────────────────────────────────

def _load_raw(source: Union[str, os.PathLike]) -> str:
    """Return the raw JSON text from either a string literal or a file path."""
    source = str(source).strip()

    # Treat the input as a file path when it does NOT start with '{' or '[',
    # or when it is an existing path on disk (handles edge cases like
    # whitespace-padded JSON objects).
    looks_like_json = source.startswith(("{", "["))
    is_file = os.path.exists(source)

    if is_file or not looks_like_json:
        # May raise FileNotFoundError if the path simply does not exist.
        if not os.path.exists(source):
            raise FileNotFoundError(f"Agent config file not found: {source!r}")
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read()

    return source


def _parse_json(raw: str) -> dict:
    """Decode *raw* as JSON and assert the top level is an object."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(
            f"Invalid JSON in agent config: {exc.msg}", exc.doc, exc.pos
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Agent config must be a JSON object at the top level, "
            f"got {type(data).__name__}."
        )
    return data


def _validate(data: dict) -> dict:
    """Validate required fields and permission values; return normalised dict."""
    # ── top-level fields ────────────────────────────────────────────────────
    for key in _REQUIRED_TOP:
        if key not in data:
            raise ValueError(f"Missing required top-level field: '{key}'.")

    agent_name = data["agent_name"]
    intended_purpose = data["intended_purpose"]
    tools_raw = data["tools"]

    if not isinstance(agent_name, str) or not agent_name.strip():
        raise ValueError("'agent_name' must be a non-empty string.")

    if not isinstance(intended_purpose, str) or not intended_purpose.strip():
        raise ValueError("'intended_purpose' must be a non-empty string.")

    if not isinstance(tools_raw, list):
        raise ValueError(f"'tools' must be a list, got {type(tools_raw).__name__}.")

    # ── per-tool validation ─────────────────────────────────────────────────
    tools = []
    for idx, tool in enumerate(tools_raw):
        if not isinstance(tool, dict):
            raise ValueError(
                f"tools[{idx}] must be a JSON object, got {type(tool).__name__}."
            )

        for key in _REQUIRED_TOOL:
            if key not in tool:
                raise ValueError(
                    f"tools[{idx}] ('{tool.get('name', '<unnamed>')}') "
                    f"is missing required field: '{key}'."
                )

        name = tool["name"]
        description = tool["description"]
        parameters = tool["parameters"]
        permissions = tool["permissions"]

        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"tools[{idx}].name must be a non-empty string.")

        if not isinstance(description, str):
            raise ValueError(f"tools[{idx}] ('{name}').description must be a string.")

        if not isinstance(parameters, list) or not all(
            isinstance(p, str) for p in parameters
        ):
            raise ValueError(
                f"tools[{idx}] ('{name}').parameters must be a list of strings."
            )

        if not isinstance(permissions, list):
            raise ValueError(
                f"tools[{idx}] ('{name}').permissions must be a list."
            )

        invalid = [p for p in permissions if p not in VALID_PERMISSIONS]
        if invalid:
            raise ValueError(
                f"tools[{idx}] ('{name}') has invalid permission(s): "
                f"{invalid!r}. Allowed values: {sorted(VALID_PERMISSIONS)}."
            )

        tools.append(
            {
                "name": name,
                "description": description,
                "parameters": list(parameters),
                "permissions": list(permissions),
            }
        )

    return {
        "agent_name": agent_name,
        "intended_purpose": intended_purpose,
        "tools": tools,
    }


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pathlib
    import pprint

    sample_path = pathlib.Path(__file__).parent.parent.parent / "samples" / "high_risk_medicare.json"
    result = parse(str(sample_path))
    pprint.pprint(result)

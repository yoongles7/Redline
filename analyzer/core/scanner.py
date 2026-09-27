"""
scanner.py — discovers @tool-decorated functions in a LangChain repository.
"""

import ast
import os

_SKIP_DIRS = {
    "venv", ".venv", "__pycache__", ".git",
    "node_modules", ".tox", "build", "dist",
}


def _is_tool_decorator(node):
    """Return True if an AST decorator node represents @tool."""
    if isinstance(node, ast.Name):
        return node.id == "tool"
    if isinstance(node, ast.Attribute):
        return node.attr == "tool"
    # @tool(...) called as a function
    if isinstance(node, ast.Call):
        return _is_tool_decorator(node.func)
    return False


def _infer_agent_name(repo_path):
    """
    Return the agent name.

    Priority:
    1. If agent.py exists at the repo root and contains a module-level
       assignment to 'agent' or 'agent_executor', return that variable name.
    2. Otherwise, return the basename of repo_path.
    """
    basename = os.path.basename(os.path.normpath(repo_path))
    agent_py = os.path.join(repo_path, "agent.py")

    if not os.path.isfile(agent_py):
        return basename

    try:
        with open(agent_py, "r", encoding="utf-8", errors="replace") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=agent_py)
    except SyntaxError:
        return basename

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in (
                    "agent", "agent_executor"
                ):
                    return target.id

    return basename


def scan_repository(repo_path: str) -> dict:
    """
    Walk *repo_path* and return every @tool-decorated function found.

    Returns
    -------
    {
        "repo_path": str,
        "agent_name": str,
        "tools": [
            {
                "name": str,
                "description": str,
                "file": str,
                "lineno": int,
                "body_source": str,
            },
            ...
        ]
    }
    """
    tools = []

    for dirpath, dirnames, filenames in os.walk(repo_path):
        # Prune skipped directories in-place so os.walk won't descend into them.
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]

        for filename in filenames:
            if not filename.endswith(".py"):
                continue

            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, repo_path)

            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=abs_path)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not any(_is_tool_decorator(d) for d in node.decorator_list):
                    continue

                tools.append({
                    "name": node.name,
                    "description": ast.get_docstring(node) or "",
                    "file": rel_path,
                    "lineno": node.lineno,
                    "body_source": ast.get_source_segment(source, node) or "",
                })

    return {
        "repo_path": repo_path,
        "agent_name": _infer_agent_name(repo_path),
        "tools": tools,
    }


if __name__ == "__main__":
    import sys

    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "samples", "overprivileged_agent",
    )

    result = scan_repository(sample_path)

    print(f"Agent name : {result['agent_name']}")
    print(f"Repo path  : {result['repo_path']}")
    print(f"Tools found: {len(result['tools'])}\n")

    for tool_info in result["tools"]:
        print(f"  [{tool_info['file']}:{tool_info['lineno']}]  {tool_info['name']}")
        if tool_info["description"]:
            print(f"    {tool_info['description']}")
        print()

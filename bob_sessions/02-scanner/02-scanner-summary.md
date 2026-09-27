# 02-scanner: AST-based Tool Discovery

**Task:** Build `analyzer/core/scanner.py` — scans LangChain repos for `@tool` functions.

**Bobcoins used:** 0.322

**Prompt:** 

Read @SPEC.md.

Build analyzer/core/scanner.py.

This module scans a LangChain Python repository on disk and discovers @tool-decorated functions.

Requirements:

Function: scan_repository(repo_path: str) -> dictReturns:{
    "repo_path": str,
    "agent_name": str,
    "tools": [
        {
            "name": str,               # function name
            "description": str,        # docstring, empty string if None
            "file": str,               # relative path from repo_path
            "lineno": int,             # line number of the function def
            "body_source": str,        # the raw source of the function body
        },
        ...
    ]
}Behavior:

    Walk repo_path recursively, skipping:

        directories: venv, .venv, __pycache__, .git, node_modules, .tox, build, dist

        files not ending in .py

    For each .py file, parse it with ast.parse. If parsing fails (syntax error), skip the file and continue — do not crash.

    Walk the AST looking for FunctionDef nodes that have a decorator whose name is tool (either @tool, @langchain.tools.tool, or @tools.tool — check the last attribute in ast.Attribute chains, or the id in ast.Name).

    For each such function, extract:

        name = node.name

        description = ast.get_docstring(node) or ""

        file = path relative to repo_path

        lineno = node.lineno

        body_source = ast.get_source_segment(source, node) (the full function source, so later stages can analyze the body)

    Infer agent_name:

        Use the basename of repo_path (e.g., /path/to/customer-support-agent → customer-support-agent)

        If agent.py exists at repo root and contains a module-level assignment to a variable named agent or agent_executor, use the variable name as the agent name instead

    Return the dict above.

Include a test under if __name__ == "__main__": that:

    Scans samples/overprivileged_agent

    Prints the agent name

    Prints each discovered tool with its name, description, and file

Do not modify any other files. Only create scanner.py.

**Output:** `analyzer/core/scanner.py`

**Test result:** Discovered 4 tools in overprivileged_agent:
- read_customer (tools/customer_db.py)
- update_customer (tools/customer_db.py)
- execute_sql (tools/sql.py)
- send_email (tools/email.py)
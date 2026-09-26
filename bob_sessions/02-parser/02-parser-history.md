
---

**Status:** active  **Date:** 2026-09-26

---

### 👤 User

Read @SPEC.md and @samples/high_risk_medicare.json.

Build analyzer/core/parser.py.

It should:
- Accept a JSON string OR a file path
- Return a validated dict with fields: agent_name (str), intended_purpose (str), tools (list of dicts)
- Each tool dict has: name (str), description (str), parameters (list of str), permissions (list of str)
- Validate that every permission is one of: read, write, execute, network- Raise clear, specific errors for missing fields or invalid permissions
- Include a test under if __name__=="__main__": that loads samples/high_risk_medicare.json and prints the parsed output

Do not modify any other files. Only create parser.py.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me read the spec and sample file first.

> 🔧 **read_file** — SPEC.md

> 🔧 **read_file** — samples/high_risk_medicare.json

### 🤖 Assistant

> 🔧 called: read_file

Now let me check the existing stub:

> 🔧 **read_file** — analyzer/core/parser.py

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — analyzer/core/parser.py

### 🤖 Assistant

> 🔧 called: execute_command

Now run the self-test to verify it works end-to-end:

> 🔧 **execute_command** — source venv/bin/activate && python analyzer/core/parser.py

### 🤖 Assistant

> 🔧 called: execute_command

Also run the existing test suite to confirm nothing is broken:

> 🔧 **execute_command** — source venv/bin/activate && python manage.py test

### 🤖 Assistant

All clean. Here's what was built in [`analyzer/core/parser.py`](analyzer/core/parser.py):

---

### Public surface

| Symbol | Purpose |
|---|---|
| [`VALID_PERMISSIONS`](analyzer/core/parser.py:14) | `{"read", "write", "execute", "network"}` — the canonical set from SPEC.md |
| [`parse(source)`](analyzer/core/parser.py:22) | Single entry point — accepts a JSON string **or** a file path |

### Internal pipeline

1. **[`_load_raw`](analyzer/core/parser.py:55)** — decides whether `source` is a literal JSON string (`{`/`[` prefix) or a file path; reads the file if so, raises `FileNotFoundError` if the path doesn't exist.
2. **[`_parse_json`](analyzer/core/parser.py:72)** — `json.loads` the raw text; raises a clear `json.JSONDecodeError` if malformed, `ValueError` if the top level isn't an object.
3. **[`_validate`](analyzer/core/parser.py:86)** — checks every required field at both levels, types, non-empty strings, and permission membership. Error messages always include the tool index and name so failures are easy to locate.

### Error examples

```
ValueError: Missing required top-level field: 'intended_purpose'.
ValueError: tools[1] ('write_file') is missing required field: 'permissions'.
ValueError: tools[2] ('http_request') has invalid permission(s): ['admin']. Allowed values: ['execute', 'network', 'read', 'write'].
```
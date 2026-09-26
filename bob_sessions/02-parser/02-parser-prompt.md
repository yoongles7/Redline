# 02-parser: Agent Config Parser

**Task:** Build `analyzer/core/parser.py` — reads and validates agent JSON config.

**Bobcoins used:** 0.225

**Prompt:**

Read @SPEC.md and @samples/high_risk_medicare.json.

Build analyzer/core/parser.py.

It should:
- Accept a JSON string OR a file path
- Return a validated dict with fields: agent_name (str), intended_purpose (str), tools (list of dicts)
- Each tool dict has: name (str), description (str), parameters (list of str), permissions (list of str)
- Validate that every permission is one of: read, write, execute, network
- Raise clear, specific errors for missing fields or invalid permissions
- Include a test under if __name__=="__main__": that loads samples/high_risk_medicare.json and prints the parsed output

Do not modify any other files. Only create parser.py.

**Output:**
- `analyzer/core/parser.py`

**Test:** `python analyzer/core/parser.py` loads `samples/high_risk_medicare.json` and prints parsed output.
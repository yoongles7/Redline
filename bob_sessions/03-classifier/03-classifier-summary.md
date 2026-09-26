# 03-classifier: Tool Severity Classification

**Task:** Build `analyzer/core/classifier.py` — assigns severity per tool.

**Bobcoins used:** 0.361

**Prompt:** 

Read @SPEC.md and @analyzer/core/parser.py.

Build analyzer/core/classifier.py.

It should:
- Accept the parsed config dict (from parser.py)
- Return a new dict with the same structure, but each tool gets an added field severity (string)
- Compute severity for each tool:  
  - read -> "LOW"  
  - write -> "MEDIUM"  
  - execute -> "CRITICAL"  
  - network -> "HIGH"  
  - if a tool has multiple permissions, use the highest severity present
- include a test under if __name__=="__main__": that imports the parser, loads samples/high_risk_medicare.json, classifies it, and prints each tool name with its permissions and severity

Do not modify andy other files. Only create classifier.py.

**Output:** `analyzer/core/classifier.py`

**Test result:**
- read_file → LOW
- write_file → MEDIUM
- http_request → HIGH
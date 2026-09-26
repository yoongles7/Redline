# 04-paths: Attack Path Detection

**Task:** Build `analyzer/core/paths.py` — detects dangerous tool combinations.

**Bobcoins used:** 0.263

**Prompt:** 

Read @SPEC.md, @analyzer/core/parser.py, and @analyzer/core/classifier.py.

Build analyzer/core/paths.py.

It should:
- Accept the classified config dict (from classififer.py)
- Detect attack paths using the detection rules table in SPEC.md
- For each detected path, return a dict with:
  - chain -- list of tool names involved (e.g., ["read_file", "http_request"])  
  - category -- the risk category from SPEC.md (e.g., "Data exfiltration")  
  - severity -- th severity from SPEC.md ("HIGH", "CRITICAL", "MEDIUM")  
  - explanation -- one or two sentences in plain English describing what the path allows
- Detection rules from SPEC.md:
  - read + network -> Data exfiltration, HIGH  
  - execute alone -> Arbitrary code execution, CRITICAL  
  - execute + write -> Persistance, HIGH  
  - execute + network -> Command & control, CRITICAL  
  - read + write + network -> Full compromise, CRITICAL  
  - write alone -> Data tampering, MEDIUM  
  - read + write -> Data modification, MEDIUM
- If multiple rules match, return all matched paths (don't deduplicate)
- Include a test under if __name__=="__main__": that loads samples/high_risk_medicare.json through parser -> classifier -> paths, and prints each detected path with its chain, category, severity, and explanation

Do not modify any other files. Only create paths.py.

**Output:** `analyzer/core/paths.py`

**Test result:** 3 paths detected:
1. Full compromise (CRITICAL) — http_request + read_file + write_file
2. Data exfiltration (HIGH) — http_request + read_file
3. Data modification (MEDIUM) — read_file + write_file
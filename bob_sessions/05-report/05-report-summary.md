# 05-report: Final Report Generation

**Task:** Build `analyzer/core/report.py` — produces the structured report.

**Bobcoins used:** (check screenshot)

**Prompt:** 

Read @SPEC.md, @analyzer/core/parser.py, @analyzer/core/classifier.py, and @analyzer/core/paths.py.

Build analyzer/core/report.py.

It should:
- Accccept the parsed config, classified tools, and detected paths
- Return a structured report dict with:
  - agent_name (str)  
  - intended_purpose (str)  
  - blast_radius (str) -- overall score = highest severity among detected paths. If no paths detected, "LOW"  
  - attack_paths (list) -- the paths form paths.py, unchanged  
  - mitigations (list) -- for each tool involved in any path:
    - action -- "remove" if the tool's permissions are not implied by the intended_purpose, othewise "restrict"    
    - tool -- the tool name    
    - reason -- one sentence explaining why    
    - alternative - if action if "restrict", suggest one of: "JIT", "scoping", "approval threshold", "segmentataion"
- For the "remove vs restrict" decision: check if any word in the tool's permissions appears in the intended_purpose string (case-insensitive). If not, recommend "remove". If yes, recommend "restrict".
- Include a test under if __name__=="__main__": that loads samples/high_risk_medicare.json through all four modules and prints the final report as formatted JSON

Do not modify any other files. Only create report.py.

**Output:** `analyzer/core/report.py`

**Test result:** End-to-end run through all four modules on samples/high_risk_medicare.json produces JSON with blast_radius=CRITICAL and 3 attack paths.

# 06-models: Django models to store reports

**Task:** Build `analyzer/models.py` — write Report model to store reports.

**Bobcoins used:** 0.144

**Prompt:** 

Read @SPEC.md and @analyze/core/report.py.

Build the Django model for storing reports in analyzer/models.py.

Create a Report model with these fields:
- agent_name -- CharField, max_length=200
- intended_purpose -- TextField
- config_text -- TextField (the raw JSON the user submitted)
- blast_radius -- CharField, max_length=20 (stores LOW/MEDIUM/HIGH/CRITICAL)
- attack_paths -- JSONField, default=list
- mitigations -- JSONField, default=list
- created_at -- DateTimeField, auto_now_add=True

Add a __str__ method that returns the agent name and blast radius.

Do not modify any other files. Only edit analyzer/models.py.

**Output:** `analyzer/models.py'
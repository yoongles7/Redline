# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Documentation Context

- `SPEC.md` is the canonical product spec — it defines the input schema, detection rules (permission combos → severity), scoring logic, and output report structure. Always consult it before answering questions about intended behavior.
- `analyzer/core/` modules are empty stubs; they define the intended architecture but contain no implementation yet.
- There is no `requirements.txt` — installed packages are only discoverable via `pip freeze` inside the venv.
- Django app name is `analyzer`; project package is `redline_bob` — these are distinct and easy to confuse.

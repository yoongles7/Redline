# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Architectural Constraints

- The analysis pipeline is strictly sequential: parse → classify → detect paths → score → report. `SPEC.md` defines this flow; any planned architecture must preserve it.
- Severity is ordinal (LOW < MEDIUM < HIGH < CRITICAL); overall blast radius = highest severity among all detected paths. Do not average or aggregate differently.
- The project has no frontend yet — `analyzer/templates/analyzer/` is empty. Plan UI work knowing there are no existing templates to extend.
- Settings are environment-split (`base` / `development` / `production`) — new configuration belongs in `base.py` unless it is environment-specific.
- No test infrastructure beyond Django's built-in test runner. Plan any test tooling additions (pytest, coverage) as explicit dependencies since there is no `requirements.txt`.

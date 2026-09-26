# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Coding Rules

- All four `analyzer/core/` modules (`parser.py`, `classifier.py`, `paths.py`, `report.py`) are empty stubs — implement them according to `SPEC.md`, which is the authoritative spec.
- Detection rule table (permission combos → severity) is in `SPEC.md` — do not hardcode severity values without cross-checking it.
- No `requirements.txt` exists. After installing new packages with pip, run `pip freeze > requirements.txt` or manually document the dependency.
- `DJANGO_SETTINGS_MODULE` defaults to `redline_bob.settings.development` — do not override in code unless writing production-specific logic.
- When adding URL patterns, edit `redline_bob/urls.py` (project-level) and wire app-level routes via `include()`.
- Tests go in `analyzer/tests.py` (single file). Run a specific test: `python manage.py test analyzer.tests.ClassName.method_name`.

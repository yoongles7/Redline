# Project Coding Rules (Non-Obvious Only)

- `analyzer/core/` modules (`parser`, `classifier`, `paths`, `report`) are **not yet implemented** — the directory exists but only has an empty `__init__.py`. These are the primary implementation targets.
- `analyzer/views.py` imports them as: `from .core import parser, classifier, paths, report as report_module` — match these exact module names.
- `analyzer/core/__init__.py` must stay empty; do not add re-exports there.
- `Report` model stores `attack_paths` and `mitigations` as `JSONField(default=list)` — pass Python lists, not JSON strings.
- `manage.py` hardcodes `DJANGO_SETTINGS_MODULE=redline_bob.settings.development`; do not change it — override via env var when needed.
- No linter/formatter config exists; follow PEP 8 manually. Imports order: stdlib → third-party → local (relative `.` imports within app).
- Samples in `samples/` are synthetic LangChain repos used as analyzer inputs, not as Django test fixtures.

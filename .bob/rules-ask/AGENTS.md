# Project Documentation Context (Non-Obvious Only)

- `SPEC.md` in the project root is the canonical reference for all domain logic — blast-radius scoring formula, operation priority order, sensitivity values, impact path flagging rules, and mitigation logic are all defined there.
- `analyzer/core/` appears to contain the analysis engine but is currently **empty** (only an `__init__.py`). The imports in `views.py` reference modules that do not yet exist.
- `samples/` contains three synthetic LangChain repositories used as test inputs to the analyzer (`overprivileged_agent`, `credential_agent`, `secure_agent`), not as Python test files.
- `redline_bob/` is the Django project package (settings, urls, wsgi/asgi) — it is not a separate app; the only Django app is `analyzer/`.
- `bob_sessions/` at the root is an IDE artifact (Bob AI session history) — unrelated to the Django app.
- `TIME_ZONE` is set to `'Asia/Kathmandu'` in base settings — not UTC.

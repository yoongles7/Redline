# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

Django 6.1 + Django REST Framework blast-radius analyzer for AI agent tool definitions. Python 3.14 venv at `venv/`.

## Commands

```bash
# Activate venv first (required)
source venv/bin/activate

# Run dev server
python manage.py runserver

# Run all tests
python manage.py test

# Run a single test
python manage.py test analyzer.tests.MyTestCase.test_method

# Apply migrations
python manage.py migrate
```

## Settings

- `manage.py` defaults to `redline_bob.settings.development` — no env var needed locally.
- Dev settings load from `.env` (not committed). Requires `SECRET_KEY` at minimum.
- Settings split: `redline_bob/settings/base.py` → `development.py` / `production.py`.
- `TIME_ZONE` is `Asia/Kathmandu` (non-standard).

## Architecture

Core analysis pipeline lives in `analyzer/core/` with four stub modules (not yet implemented):
- `parser.py` — parse incoming JSON agent config
- `classifier.py` — classify tools by permission dimension (read/write/execute/network)
- `paths.py` — detect attack chains and score against intended purpose
- `report.py` — produce structured blast radius report

Detection rules and severity logic are defined in `SPEC.md` — treat it as the authoritative spec.

## Key Conventions

- Templates follow Django app convention: `analyzer/templates/analyzer/<name>.html`
- No `requirements.txt` — dependencies tracked only in `venv/`. If adding packages, document them here or add a requirements file.
- Tests live in `analyzer/tests.py` (single file, not a `tests/` directory).
- No linter or formatter config present yet; follow PEP 8.

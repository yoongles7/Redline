# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

**Redline** — a Django web app that performs static blast-radius analysis on LangChain agent repositories. It takes a local filesystem path to a LangChain repo, scans `@tool`-decorated functions via AST, and produces a security report with a 0–100 blast-radius score.

## Stack

- Python + Django 6.1 + Django REST Framework
- SQLite (dev), settings split: `redline_bob/settings/{base,development,production}.py`
- No frontend build step — plain Django templates in `analyzer/templates/`

## Commands

```bash
# Run dev server (default settings module: redline_bob.settings.development)
python manage.py runserver

# Migrations
python manage.py makemigrations && python manage.py migrate

# Tests
python manage.py test                         # all tests
python manage.py test analyzer.tests.MyTest   # single test
```

- Requires a `.env` file with `SECRET_KEY` and optionally `DEBUG=True` (read via `python-dotenv` in dev settings)
- `DJANGO_SETTINGS_MODULE` defaults to `redline_bob.settings.development` (set in `manage.py`)

## Architecture

```
views.py (POST /analyze/)
  → analyzer/core/parser.py      — parses the LangChain repo path input
  → analyzer/core/classifier.py  — classifies tools (operation + resource type)
  → analyzer/core/paths.py       — detects flagged impact paths via BFS
  → analyzer/core/report.py      — generates the structured report dict + score
  → Report model (DB)            — stores result; redirects to /report/<id>/
```

The four core modules (`parser`, `classifier`, `paths`, `report`) are imported in `analyzer/views.py` — they live in `analyzer/core/` but **are not yet implemented** (the `__init__.py` is empty; they must be created).

## Key Domain Rules (from SPEC.md)

- **Operation priority** (highest wins): `admin > financial > execute > delete > write > send > read`
- **Sensitivity**: `shell=5, credentials=5, cloud=5, database=4, external_api=3, email=3, filesystem=2`
- **Blast radius score formula** (0–100):
  `0.35·norm_sensitive + 0.25·norm_write_capable + 0.15·(1−approval_coverage) + 0.10·(1−recovery_coverage) + 0.15·norm_high_impact_tools`
- Score bands: `0–25 LOW, 26–50 MEDIUM, 51–75 HIGH, 76–100 CRITICAL`
- Findings generated only for `CRITICAL` and `HIGH` impact paths
- Assets are global to the agent — same resource name across tools = one asset node

## Samples

Three synthetic LangChain repos in `samples/` (`overprivileged_agent`, `credential_agent`, `secure_agent`) — use these as test inputs; the `overprivileged_agent` has a worked example in SPEC.md.

## Code Style

- Imports: stdlib → third-party → local (relative `.` imports within `analyzer/`)
- No linter config present; follow PEP 8
- `analyzer/core/__init__.py` is empty — do not import module-level symbols there
- Settings use `from .base import *` wildcard — keep per-environment overrides minimal

# Project Architecture Rules (Non-Obvious Only)

- The entire analysis pipeline is synchronous and request-scoped: parse → classify → paths → report all happen in a single POST handler in `views.py`, then the result is persisted to DB and the user is redirected. No async, no background tasks.
- `analyzer/core/` is the **only** place for domain logic — views must stay thin (parse input, call core modules, persist result, redirect).
- Assets are global to the agent (deduplicated by resource name across all tools) — the data model reflects this: `attack_paths` on the `Report` stores paths, not per-tool data.
- The blast-radius score formula has fixed weights (see SPEC.md §5) — do not change weights without updating SPEC.md.
- `max_depth` is deliberately excluded from the score formula (propagation metric only, not severity) — do not add it to the score.
- Mitigation candidates must never modify the source repository — they are advisory output only.
- Settings are split base/development/production; `development.py` and `production.py` both use `from .base import *`. Adding new base settings should go in `base.py` only; environment-specific overrides go in the respective file.

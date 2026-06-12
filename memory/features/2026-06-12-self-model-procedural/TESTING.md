# Testing

TDD: tests written first; ImportError observed before implementation.

- `python -m pytest tests/test_self_model.py` — 7 passed.
- `python -m pytest` — 178 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: identity create/read/in-place update without conflicts, deterministic listing/description, retrieval integration, parameter versioning with supersession chain + provenance notes, unset defaults, per-skill latest-value mapping, superseded-version queryability.

Not verified: skill controllers actually consuming parameters (Stage 5); bounded procedural learning (Stage 7).

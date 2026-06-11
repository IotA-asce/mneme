# Configurable Salience Scoring

Type: Feature
Date: 2026-06-11
Status: Complete

## Summary

Made salience scoring configurable and more explainable while keeping deterministic scoring:

- added config loading from `config/memory.yaml`,
- added configurable promotion thresholds,
- preserved explicit remember override behavior,
- added detailed `SalienceResult.explanation`,
- added threshold boundary, config, override, and clamping tests,
- documented scoring in `docs/memory/SALIENCE.md`.

No machine learning, storage changes, retrieval changes, or new dependencies were added.

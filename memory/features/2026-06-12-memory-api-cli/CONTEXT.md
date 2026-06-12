# Context

The memory prototype already had separate modules for models, salience scoring, SQLite storage, retrieval, conflict handling, provenance/meta-memory, and deterministic consolidation.

Using those modules required manual orchestration. That was acceptable for focused unit tests, but brittle for Codex replay/debug flows and future scripts that need a clean memory entry point.

This feature adds a facade without changing the ownership of lower-level behavior. Validation remains in dataclasses, persistence remains in `MemoryStore`, scoring remains in `salience.py`, retrieval remains in `retrieval.py`, and consolidation remains in `consolidation.py`.

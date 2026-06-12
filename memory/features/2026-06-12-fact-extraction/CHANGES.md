# Changes

- `src/android_brain_memory/extraction.py` (new): `FactExtractor`, `FactExtractionReport`, `statement_fact_id`.
- `src/android_brain_memory/__init__.py`: exports.
- `tests/test_fact_extraction.py` (new): 7 tests — deterministic IDs, provenance, capping, idempotency, malformed skipping, conflict precedence, bus-driven end-to-end, non-semantic promotions ignored.
- `docs/memory/EXTRACTION.md` (new); `docs/architecture/MASTER_ROADMAP.md` M1.2 complete; `docs/architecture/REPO_STATUS.md` updated.
- `implement/fact-extraction/` planning files.

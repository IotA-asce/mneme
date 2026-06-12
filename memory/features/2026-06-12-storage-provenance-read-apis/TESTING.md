# Testing

Tests were written first and observed failing (ImportError on the new read models) before implementation.

Commands run:

- `python -m pytest tests/test_storage_provenance_reads.py` — 10 passed.
- `python -m pytest` — 87 passed (full suite, no regressions).

Covered behavior:

- Raw trace round-trip preserves payload JSON, source type enum, confidence, salience, and source ID; missing IDs return `None`.
- Recent trace listing is newest-first with deterministic tie-breaks, respects `limit`, and filters by source type.
- Fact support links are readable directly with weights, ordered by episode ID; reverse lookup returns facts ordered by fact ID.
- Episode window query uses overlap semantics and rejects inverted ranges and non-positive limits.
- Provenance chain reaches raw trace from fact through episode; edges carry `supported_by` / `derived_from` relations; summary text includes all IDs.
- Unresolvable supporting IDs are reported in `missing` without failing.
- Unknown roots raise `KeyError`; unsupported kinds raise `ValueError`.

Not verified (out of scope): retrieval-bundle integration of provenance summaries (Phase 4 follow-up), behavior under concurrent writers.

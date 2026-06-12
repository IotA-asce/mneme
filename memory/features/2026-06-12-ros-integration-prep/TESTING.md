# Testing

The contract test was written first and observed failing against the stale drafts (missing fields in `Fact.msg`, `MemoryQuery.msg`, `MemoryBundle.msg`, absent `SalienceFeatures.msg`/`MemorySummary.msg`/`RuntimeEvent.msg`, no `conflict_report_json` in `UpsertFact.srv`) before the drafts were updated.

Commands run:

- `python -m pytest tests/test_interface_alignment.py` — 3 passed.
- `python -m pytest` — 99 passed (full suite).
- `python scripts/dev_check.py` — completed successfully (run before merge).

Covered behavior:

- Every interface draft field maps to a model `to_dict()` key under the documented mapping; every model key (minus explicit derived exclusions) appears in the draft; no double mappings.
- `UpsertFact.srv` response carries conflict report JSON.
- All transportable models survive `json.dumps` → `json.loads` → `from_dict` round-trips with identical `to_dict()` output.

Note: the JSON round-trip test passed immediately because it pins existing serialization behavior as a regression guard; the alignment tests were the red→green TDD target.

Not verified (deliberately out of scope): actual ROS message generation/compilation (no ROS toolchain in this repo), transport behavior, QoS.

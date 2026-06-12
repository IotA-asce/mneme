# Testing

TDD: tests written first; ImportError (no ExecutiveGoal) observed before implementation. Mid-implementation, two tests exposed that storage matches query_text as a single substring so full dialogue sentences never hit — fixed in the executive with deterministic cue-token fallback (not by weakening tests). One test initially used fact id "fact_tea" whose ID contains the content word; renamed to "fact_beverage" so the content-leak assertion tests what it means.

- `python -m pytest tests/test_executive_v1.py tests/test_executive.py` — 14 passed (v0 unchanged).
- `python -m pytest` — 162 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: goal context attach/detach, suspend/resume across safety freeze with one-shot resumption reporting, timing gate both sides, memory payload IDs + bundle retention + content-leak guard, conflict-driven clarification flag, idle rotation, v0 default preservation.

Not verified: response timing against real speech endpointing (Stage 4); memory-informed behavior under large fact stores (bench-scale only).

# Testing

TDD: tests written first; ImportError observed before implementation.

- `python -m pytest tests/test_world_model.py` — 7 passed.
- `python -m pytest` — 142 passed.
- `python scripts/dev_check.py` — run before merge.

Covered: presence + TTL expiry, speaker TTL, sound/touch/internal/safety updates, published state keys/topics, snapshot determinism + JSON round-trip, replay-fixture end state.

Not verified: multi-sensor fusion conflicts (single simulated source per modality in V1); object tracking (deferred to Stage 4).

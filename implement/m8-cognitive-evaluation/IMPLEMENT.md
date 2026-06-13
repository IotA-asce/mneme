# M8 Cognitive Evaluation Implementation

## Phases

1. Add deterministic turn classification for greetings, remembering, recall, review, correction, forget, self, capability, and device/model status turns.
2. Add memory review helpers that explain the memory refs used by the previous response and create non-mutating correction proposals.
3. Add cognitive benchmark fixtures and `mneme eval cognition`.
4. Add conservative capability ladder reporting through `mneme eval capability`.
5. Show turn/capability evidence in the local UI snapshot.
6. Update docs, backlog, and project memory.

## Validation

Run:

```bash
.venv/bin/python -m pytest tests/test_cognitive_benchmarks.py tests/test_turn_understanding.py tests/test_memory_review.py tests/test_capability_ladder.py
.venv/bin/python scripts/dev_check.py
```

## Rollback

The feature is isolated in new cognition/review modules plus CLI/UI/runtime hooks. Revert the feature branch to remove it; no storage migration is involved.

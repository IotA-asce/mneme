# Implementation Plan

## Phases

1. Add persistent `memory_review` records and storage methods.
2. Add review apply/reject helpers for correction, forget, confirm, and contradiction review.
3. Wire runtime, dialogue, CLI, and UI to the same review backend.
4. Expand cognitive benchmark fixtures and suite scoring.
5. Update docs, backlog, and project memory.

## Validation

- Unit tests for storage, proposal creation, apply/reject behavior, and conflict reports.
- Runtime tests for correction, forget, confirm, reject, and confirmed-vs-confirmed conflict.
- CLI JSON tests for `mneme review`.
- Benchmark suite tests for default `mneme eval cognition --json`.
- Full `scripts/dev_check.py`.

## Rollback

The feature is isolated behind a new migration and new review commands. Runtime still works without applying proposals. Rollback would remove `memory_review` usage from runtime/UI and leave existing memory rows untouched.

## Done

- Review records are durable and auditable.
- User-approved correction/forget/confirm actions use explicit commands.
- Benchmarks prove the behavior deterministically.
- Documentation and memory entries are updated.

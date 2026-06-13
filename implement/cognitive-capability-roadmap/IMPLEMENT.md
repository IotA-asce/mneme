# Implementation Notes

## Documentation Deliverables

1. Add `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md`.
2. Link the new document from `docs/architecture/MASTER_ROADMAP.md`.
3. Update `docs/architecture/REPO_STATUS.md` so current capability remains truthful.
4. Update `tasks/backlog.md` with milestone-level tasks.
5. Record project memory and index it.

## Future Implementation Order

1. Local model runtime adapter protocol and fake backend.
2. Ollama/local HTTP adapter.
3. `mneme cognition check`.
4. Cognitive context builder.
5. Model dialogue realizer with deterministic fallback.
6. Cognitive benchmark harness.
7. UI status for model connection, memory refs, and capability evidence.

## Validation

This change is documentation-only. Validation should include:

- Markdown/file inspection.
- `git diff --check`.
- Existing developer check if practical.

## Rollback

Remove the new roadmap document and revert the master roadmap/status/backlog/memory references.

# Initial Backlog

## Foundation

- [x] Verify project structure
- [x] Run `python scripts/init_db.py`
- [x] Run `python scripts/smoke_test_memory.py`
- [x] Add pytest baseline

## Memory models

- [x] Implement/extend `MemoryCandidate`
- [x] Implement/extend `Episode`
- [x] Implement/extend `Fact`
- [x] Implement/extend `MemoryQuery`
- [x] Implement/extend `MemoryBundle`

## Salience

- [x] Add weighted scoring
- [x] Add explicit remember override
- [x] Add promotion thresholds
- [x] Add score explanation output

## Storage

- [x] Add migration runner
- [x] Add raw trace writes
- [x] Add episode writes
- [x] Add fact upserts
- [ ] Add meta-memory writes

## Retrieval

- [ ] Retrieve facts by subject/predicate/topic
- [x] Retrieve episodes by text query
- [ ] Add reranking
- [x] Return provenance summary

## Consolidation

- [ ] Add simple summary creation
- [ ] Add repeated-event clustering placeholder
- [ ] Add conflict detection
- [ ] Add decay/downranking fields

## Documentation

- [ ] Keep `docs/DESIGN_DOCUMENT.md` current
- [ ] Add ADRs for major architecture changes

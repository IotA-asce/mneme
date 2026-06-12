# Automatic Memory Promotion

Status: V1 deterministic promotion pipeline (Stage 1 / M1.1)

`MemoryPromoter` connects the runtime bus to durable storage: it subscribes to `memory_candidate` events, scores each candidate with the existing salience machinery, and maps the decision to storage actions through `MnemeMemory`. This automates the `observe → buffer → score → promote` segment of the memory lifecycle.

## Boundary

The promoter owns:

- consuming `memory_candidate` events,
- mapping salience decisions to storage actions,
- publishing `memory_lifecycle` events (`lifecycle_stage="promotion"`),
- promotion statistics (`handled`, `skipped`, per-decision counts).

It does not own:

- salience scoring policy (it never adjusts scores or thresholds),
- working-memory context (the `WorkingMemory` component consumes the same events independently),
- fact extraction (it only flags semantic candidates; see M1.2),
- intent, skill, or safety behavior.

## Decision Mapping

| Salience decision | Durable storage |
|---|---|
| `echo_only` | none — the in-memory sensory echo buffer already holds the fragment until its TTL expires |
| `working_memory_candidate` | raw trace only, so the turn's context stays traceable |
| `episode` | raw trace + episode (with provenance linking episode to trace) |
| `episode_and_semantic_candidate` | raw trace + episode, and the outcome/lifecycle event is flagged `semantic_candidate: true` for the fact extractor |

Storage goes through `MnemeMemory.remember_candidate()` so provenance and meta-memory behavior stays identical to manual storage.

## Usage

```python
engine = MnemeMemory(db_path, migrations_dir=MIGRATIONS)
engine.init_db()
bus = EventBus()
promoter = MemoryPromoter(engine, bus=bus)
promoter.attach_to_bus(bus)
# from here, every memory_candidate event on the bus is promoted automatically
ScenarioReplayRunner(bus).replay_file("scenario.yaml")
```

`promote(candidate)` can also be called directly without a bus; the lifecycle event is then skipped unless `bus` was provided at construction.

## Observability

Every promotion publishes a `memory_lifecycle` event with: `candidate_id`, `decision`, `score`, `trace_id`, `episode_id`, `semantic_candidate`. Malformed candidate events (missing or invalid `candidate` payload) are counted in `stats["skipped"]` and never raise out of the bus callback.

## Failure Behavior

- Malformed payloads: skipped and counted, dispatch continues.
- Storage failures propagate (SQLite errors are not swallowed) — promotion must not silently lose memories.

## Testing

`tests/test_promotion.py` covers all four decision mappings, bus-driven promotion, malformed-event tolerance, lifecycle event contents, and the Stage 1 exit criterion: a full scenario replay produces a durable episode with a provenance chain reaching the raw trace, with no manual storage calls.

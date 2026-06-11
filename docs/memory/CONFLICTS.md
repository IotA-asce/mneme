# Semantic Fact Conflicts

Status: V1 deterministic SQLite prototype

Mneme must not silently overwrite semantic facts when a new assertion conflicts with an existing active assertion.

## Boundary

The V1 conflict layer owns:

- detecting incompatible active facts during `MemoryStore.upsert_fact()`,
- preserving old and new fact rows,
- marking superseded or conflicted statuses,
- storing `supersedes_fact_id` where one fact cleanly supersedes another,
- returning a `FactConflictReport` from an upsert when conflict handling occurred,
- querying current conflict/supersession groups with `get_fact_conflict_reports()`.

It does not own:

- user review UI,
- automatic dialogue clarification,
- purge/deletion behavior,
- background consolidation passes,
- LLM-based contradiction judgment.

## V1 Detection Rule

Conflict detection is intentionally conservative.

A new fact is compared with existing active facts when:

- subject matches case-insensitively,
- predicate matches case-insensitively,
- fact IDs differ,
- both facts are truth-assertion sources: `user_confirmed` or `model_inferred`,
- object values are not identical,
- the context envelope matches.

For object values that contain a `value` key, `value` is treated as the assertion and all other keys are treated as context. Different context means both facts are preserved as active because the facts may describe different situations.

Examples:

```json
{"value": "tea"}
{"value": "coffee"}
```

These conflict for the same subject/predicate.

```json
{"value": "tea", "context": "morning"}
{"value": "coffee", "context": "evening"}
```

These do not conflict because context differs.

## Resolution Rules

When incompatible facts are found:

- New `user_confirmed` over old `model_inferred`: old fact becomes `superseded`; new fact remains `active`; new fact stores `supersedes_fact_id`.
- New `user_confirmed` against old `user_confirmed`: both facts become `conflicted`.
- New `model_inferred` against old `user_confirmed`: new fact becomes `conflicted`; old fact remains `active`.
- New `model_inferred` against old `model_inferred`: both facts become `conflicted`.

No old fact is deleted by conflict handling.

## Retrieval Behavior

Ordinary retrieval already defaults to `active` facts. That means:

- superseded inferred facts drop out of ordinary retrieval,
- conflicted fact pairs drop out of ordinary retrieval until explicitly requested for review,
- explicit `fact_status=conflicted` or `fact_status=superseded` queries remain available.

## Conflict Reports

`MemoryStore.get_fact_conflict_reports()` returns grouped report records with:

- subject,
- predicate,
- all fact IDs in the group,
- active fact IDs,
- conflicted fact IDs,
- superseded fact IDs,
- supersession edges,
- reason.

Reports are for review/debug flows. They are not a final user-facing clarification mechanism.

## Testing

Current tests cover:

- user-confirmed facts superseding inferred facts,
- user-confirmed facts conflicting with other user-confirmed facts,
- duplicate semantic facts not being marked as conflicts,
- context-specific facts remaining active as non-conflicts.

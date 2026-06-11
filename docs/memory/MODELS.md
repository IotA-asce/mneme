# Memory Domain Models

Status: V1 local prototype

The Python models in `src/android_brain_memory/models.py` define the in-process memory domain boundary. They are standard-library dataclasses with validation and JSON-friendly serialization helpers. They do not depend on Pydantic or any external validation framework.

## Boundary

The model layer owns:

- Python representations of memory candidates, episodes, facts, queries, bundles, salience features, and salience results.
- Validation for confidence, salience, timestamps, source types, status values, required identifiers, and required summaries.
- Conversion between enum instances and their string wire values.
- `to_dict()` and `from_dict()` helpers for JSON-friendly data exchange.

The model layer does not own:

- SQLite persistence details.
- ROS 2 message generation or transport.
- Retrieval ranking behavior.
- Consolidation, conflict resolution, or decay policy.
- Hardware, perception, executive, skill, actuator, or safety behavior.

## Validation Rules

Confidence and salience values must be finite numbers from `0.0` through `1.0`. Invalid values are rejected with `ValueError`; they are not clamped or silently corrected.

Timestamps must be non-negative integers. `Episode.end_ts` must be greater than or equal to `Episode.start_ts`.

Source types must match `SourceType`:

- `sensor_observed`
- `model_inferred`
- `executive_generated`
- `user_confirmed`
- `imported`
- `system_generated`

Memory statuses must match `MemoryStatus`:

- `active`
- `superseded`
- `conflicted`
- `suppressed`
- `purged`

Speakability values must match `Speakability`:

- `normal`
- `restricted`
- `never_say`
- `internal_only`

Required identifiers and summaries must be non-empty strings. Whitespace-only summaries are invalid.

Optional list fields use dataclass default factories. Missing optional fields in `from_dict()` use their documented defaults, but invalid supplied values are rejected.

Facts may carry optional `tags`. Queries may carry optional structured fact filters:

- `fact_subject`
- `fact_predicate`
- `fact_object_text`
- `fact_source_type`
- `fact_status`

These fields are additive. Existing `query_text`-based retrieval remains valid.

`MemoryBundle` may include `ranking_explanations`, a JSON-friendly debug list returned by the retrieval layer. It is optional and defaults to an empty list so existing bundle construction remains compatible.

`MemoryQuery.trusted_internal` and `MemoryQuery.include_internal` default to `False`. Both must be true before retrieval may include `never_say` or `internal_only` items.

## Serialization

The following models expose `to_dict()` and `from_dict()`:

- `MemoryCandidate`
- `Episode`
- `Fact`
- `MemoryQuery`
- `MemoryBundle`

`SalienceFeatures` and `SalienceResult` also expose the same helpers because they are nested in the public models and scoring path.

Serialization output uses only JSON-friendly primitives:

- enum values are strings,
- nested models become dictionaries,
- nested model lists become lists of dictionaries,
- mapping fields remain plain dictionaries,
- sequence fields become lists.

Example:

```python
candidate = MemoryCandidate(
    candidate_id="cand_001",
    candidate_type="dialogue",
    summary="User asked Mneme to remember a preference.",
    source_type="user_confirmed",
    confidence=0.95,
    features=SalienceFeatures(explicit_remember_flag=1.0),
)

payload = candidate.to_dict()
round_tripped = MemoryCandidate.from_dict(payload)
assert round_tripped == candidate
```

## Compatibility Notes

Existing scripts and tests can continue constructing dataclasses directly with valid values.

Storage code can continue using `SourceType(...)` and `MemoryStatus(...)` values from SQLite rows. Direct string input is also accepted for source type and status fields, then normalized to enum instances.

`SalienceFeatures.normalized()` remains available for the scoring path, but invalid feature values are rejected when the model is constructed. This avoids hiding bad salience data by clamping it after the fact.

## Future Work

The current models are intentionally lightweight. Future work should preserve the in-process dataclass boundary unless a concrete need appears for richer validation or schema generation.

Before changing public model fields, update:

- `docs/memory/MODELS.md`
- interface drafts under `interfaces/` if the wire shape changes,
- storage migrations if persisted fields change,
- model serialization tests,
- project memory for the completed change.

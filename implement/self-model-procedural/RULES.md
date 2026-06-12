# Rules

- Both layers ride on the existing fact machinery — no parallel store, no schema changes.
- Procedural parameter changes are explicit API calls with provenance; no autonomous learning, no parameter writes from perception or model inference.
- Version history must be preserved: superseded parameter versions stay queryable, never deleted.
- Identity updates are deliberate replacements (fixed ID), never silent inference; inferred self-beliefs would go through the normal extraction path as `model_inferred`, not through `SelfModel`.
- Deterministic IDs and ordering. Tests first (red).

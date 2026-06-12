# Fact Extraction (Semanticization)

Status: V1 deterministic structured-context extraction (Stage 1 / M1.2)

`FactExtractor` implements the `semanticize` step of the memory lifecycle: it turns structured statements inside episode context into semantic facts through the existing conflict-aware fact path.

## Boundary

The extractor owns:

- parsing `episode.context["statements"]` entries,
- building `model_inferred` facts with deterministic content-derived IDs,
- upserting through `MnemeMemory.add_fact` (conflict-aware),
- reacting to `memory_lifecycle` promotion events flagged `semantic_candidate`,
- publishing `memory_lifecycle` extraction events.

It does not own:

- free-text or LLM-based extraction (deferred; Stage 7 may add LLM *proposals* behind the same interface),
- conflict resolution (conflicts are flagged for review, never resolved here),
- consolidation summaries (extraction from summaries is future work).

## Statement Shape

```yaml
context:
  statements:
    - subject: user
      predicate: prefers_prompt_style
      value: short          # any JSON value
      confidence: 0.9       # optional; clamped into [0,1], defaults to episode confidence
```

Statements typically arrive through `MemoryCandidate.payload` (which `encode_episode` merges into episode context), authored by scenario fixtures today and perception/dialogue workers later.

## Guarantees

- **Inference never masquerades as confirmation**: extracted facts are always `model_inferred`, confidence capped at 0.75 by default (`min(episode confidence, statement confidence, cap)`).
- **Deterministic and idempotent**: fact IDs are derived from normalized subject/predicate plus canonical value JSON, so re-extracting the same episode updates the same fact instead of duplicating it.
- **Conflict-safe**: an extracted fact contradicting a user-confirmed fact is stored as `conflicted` while the confirmed fact stays active (existing storage precedence rules).
- **Provenance-complete**: facts carry `supporting_episode_ids`, derivation path `episode → extraction → fact`, and the source episode as `source_id`; `get_provenance_chain` reaches the raw trace.
- Malformed statements are skipped with recorded reasons; malformed events never raise out of bus callbacks.

## Usage

```python
extractor = FactExtractor(engine, bus=bus)
extractor.attach_to_bus(bus)   # extracts automatically after semantic-candidate promotions
report = extractor.extract_from_episode("ep_id")   # or manually
reports = extractor.extract_recent(limit=50)        # or as a batch
```

## Testing

`tests/test_fact_extraction.py` covers deterministic IDs, provenance, confidence capping, idempotent re-extraction, malformed-statement skipping, user-confirmed conflict precedence, the event-driven promotion→extraction path, and that non-semantic promotions are ignored.

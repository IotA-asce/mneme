# Consolidation Daemon Skeleton

Type: Feature
Date: 2026-06-12
Status: Complete

## Summary

Added a deterministic one-shot consolidation skeleton:

- `consolidate_once(store, options)` now groups repeated active episodes,
- groups can be formed from shared context tags, participants plus topic text, topic tokens, or close time windows,
- repeated groups create deterministic `memory_summary` records,
- source episodes are preserved and remain active,
- non-representative episodes receive decay/downranking hints in meta-memory provenance,
- `scripts/consolidate_once.py` runs one manual consolidation pass,
- tests verify repeated events produce one summary.

No LLM summarization, scheduler, purge behavior, or new dependency was added.

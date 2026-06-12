# Memory API and CLI

Type: Feature
Date: 2026-06-12
Status: Complete

## Summary

Added a high-level memory facade and JSON command-line interface:

- `MnemeMemory` / `MemoryEngine` wraps the current local memory lifecycle,
- candidate scoring can store a raw trace and optionally encode/store an episode,
- episodes and facts can be stored through typed facade methods,
- retrieval and one-shot consolidation are available through the same API,
- database inspection returns JSON-friendly table counts and summary metadata,
- `scripts/mneme_memory.py` exposes the facade through argparse commands,
- integration tests cover candidate -> score -> episode/fact -> retrieve -> consolidate.

No new runtime dependency, daemon, schema migration, LLM behavior, vector search, or hardware-facing behavior was added.

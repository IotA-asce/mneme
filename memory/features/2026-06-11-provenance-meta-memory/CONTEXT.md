# Context

Mneme's memory rules require durable memory items to preserve source, confidence, provenance, derivation path, and status without silently treating inferences as confirmed facts.

Before this change, the SQLite schema already had a `meta_memory` table with provenance, retrieval history, contradiction score, and speakability fields, but storage and retrieval did not consistently integrate that table. Raw traces, episodes, facts, and summaries needed a shared way to write provenance metadata, and retrieval needed to update history while respecting speakability.

This feature keeps the existing SQLite design and public retrieval entrypoint. It adds deterministic metadata behavior without adding encryption or authorization enforcement.

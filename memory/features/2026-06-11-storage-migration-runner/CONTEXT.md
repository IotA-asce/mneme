# Context

The initial storage layer had an idempotent SQL file but no migration audit history. `scripts/init_db.py` directly executed one SQL file. The schema already included `meta_memory` and `working_context_snapshot`, but the code had no typed methods for those tables.

This feature implements the existing design intent: local SQLite storage with provenance-aware records and auditable migrations. It does not add an ORM, external service, vector database, retrieval ranking, conflict handling, consolidation behavior, ROS runtime, or hardware behavior.

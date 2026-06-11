# Rules

## Architecture Boundaries

- Storage owns SQLite persistence and migration application.
- Storage does not own scoring, retrieval ranking, consolidation, executive behavior, or safety behavior.

## Migration Rules

- Every SQL migration must have a stable file name.
- Applied migrations must record ID, filename, checksum, and timestamp.
- A migration with a changed checksum must not be silently reapplied.
- Local database files must not be committed.

## Testing Rules

- Storage tests must use temporary databases.
- Tests must not depend on `.local/android_brain_memory.sqlite3`.
- Tests should verify source type, status, confidence, support links, and provenance JSON where relevant.

## Anti-Patterns

- Do not add an ORM or migration framework for V1.
- Do not manually mutate persistent databases.
- Do not mix storage changes with retrieval ranking or consolidation behavior.

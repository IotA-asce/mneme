# Risks

## Existing Database State

Existing local databases may already have the base schema but no migration row. The runner bootstraps `schema_migration` before applying migrations. Because `001_init.sql` remains idempotent, running it on an existing local database records the migration without dropping data.

## Checksum Changes

Once a migration is recorded, changing that SQL file causes a checksum mismatch. Future schema changes should be added as new migration files rather than editing applied migrations.

## Provenance Gap

The current episode table still does not persist `Episode.provenance_refs` as a first-class field. Provenance is preserved through raw traces, fact support links, meta-memory provenance JSON, and context data until a future migration adds dedicated episode provenance storage.

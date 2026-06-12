# Memory API and CLI Rules

Date: 2026-06-12
Status: Implemented in this feature branch

## Architectural Boundaries

- The facade orchestrates existing modules; it does not own storage schema, scoring policy, retrieval ranking, or consolidation logic.
- Lower-level modules must remain directly testable.
- CLI JSON payloads should match `to_dict()` / `from_dict()` model shapes.

## Safety Constraints

- Bench-only memory tooling.
- No hardware control.
- No secrets in command examples, provenance, or tests.
- No network or cloud dependency.

## Testing Expectations

- Use temporary SQLite databases in tests.
- Test the facade and CLI flow end to end.
- Keep existing storage, retrieval, salience, and consolidation tests intact.

## Persistence Rules

- Run migrations through `MemoryStore.run_migrations()`.
- Do not bypass migration tracking.
- Do not add schema changes for this facade unless a required operation cannot be expressed with existing tables.

## Anti-Patterns

- Do not add Click/Typer for V1.
- Do not make the CLI parse free-form natural language into facts.
- Do not silently coerce invalid model data.
- Do not duplicate retrieval ranking or conflict handling in the facade.

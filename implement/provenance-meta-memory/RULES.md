# Rules

## Architectural Boundaries

- Meta-memory records annotate stored memory; they do not confirm facts or command behavior.
- Retrieval may update retrieval history but must not change memory truth/status.
- Speakability filtering is retrieval policy only; it is not authorization or encryption.

## Provenance Rules

- Preserve source type, source ID, derivation path, supporting memory IDs, and optional notes.
- Reject secret-like provenance keys.
- Do not store credentials, tokens, private keys, or secrets.
- Keep provenance JSON-compatible.

## Speakability Rules

- Valid values are `normal`, `restricted`, `never_say`, and `internal_only`.
- Ordinary retrieval may return `normal` and `restricted`.
- Ordinary retrieval must hide `never_say` and `internal_only`.
- Returning hidden values requires both `trusted_internal=True` and `include_internal=True`.

## Testing Expectations

- Test provenance for raw traces, episodes, facts, and summaries.
- Test retrieval count and last-retrieved timestamp updates.
- Test speakability filtering and trusted internal override.

## Anti-Patterns

- Do not add encryption in this phase.
- Do not add vector search or LLM policy decisions.
- Do not leak hidden records through ordinary retrieval warnings.

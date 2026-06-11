# Core Idea

## Problem

Semantic facts with the same subject and predicate could be inserted without any truth handling. New facts did not mark older incompatible facts as superseded or conflicted, which violated the documented memory rule against silent overwrite.

## Desired Outcome

Add conservative deterministic conflict handling to fact storage while preserving all fact rows.

## Value

Mneme can keep user-confirmed knowledge ahead of inferred beliefs and preserve incompatible user-confirmed assertions for review.

## Affected Systems

- Memory domain models.
- SQLite fact storage.
- Retrieval status behavior.
- Memory documentation.
- Project backlog and memory.

## Assumptions

- `supersedes_fact_id` already exists in the initial schema.
- V1 conflict detection should avoid broad false positives.
- Human review workflows are future work.

## Constraints

- Do not delete old facts.
- Do not add dependencies.
- Do not add vector search, embeddings, or LLM contradiction checks.
- Preserve ordinary retrieval defaults for active facts.

## Non-Goals

- Purge workflows.
- Conflict-resolution UI.
- Automatic user clarification dialogue.
- Background consolidation mutation.

## Risks

- V1 compatibility checks are deterministic heuristics and can miss nuanced contradictions.
- `supersedes_fact_id` stores one direct predecessor even if a new fact supersedes multiple lower-trust facts.

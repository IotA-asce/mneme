# Core Idea

## Problem

Meta-memory existed as a manual storage helper, but raw traces, episodes, facts, summaries, retrieval history, and speakability policy were not integrated end to end.

## Desired Outcome

Store normalized provenance and meta-memory records alongside stored memories, update retrieval history when memories are returned, and enforce a first deterministic speakability filter in retrieval.

## User/Project Value

Mneme needs memory records that are explainable, auditable, and policy-aware before higher-level executive behavior relies on them.

## Affected Systems

- Memory domain models.
- SQLite storage helpers.
- Retrieval manager.
- Meta-memory records.
- Retrieval and storage tests.
- Memory documentation and backlog.

## Assumptions

- `meta_memory` already has the required columns.
- V1 does not add encryption yet.
- Summary retrieval is still future work, but summary writes can be meta-memory-aware now.
- Trusted internal retrieval is represented by explicit query flags, not a complete authorization system.

## Constraints

- Do not store secrets or credentials.
- Do not add encryption or new dependencies.
- Keep existing storage and retrieval call sites compatible.

## Non-Goals

- Full authorization framework.
- Provenance graph traversal.
- Conflict resolution.
- Summary retrieval.

## Risks

- Speakability filtering is a policy hook, not complete privacy enforcement.
- Provenance is only as accurate as caller-provided source and derivation data.

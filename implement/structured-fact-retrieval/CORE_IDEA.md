# Core Idea

## Problem

Fact retrieval only supported broad free-text matching over subject, predicate, and object JSON. It did not expose structured filters for subject, predicate, object text, source type, status, or tags, and it did not distinguish ordinary active retrieval from review/debug access to non-active facts.

## Desired Outcome

Add deterministic structured fact retrieval while preserving `query_text` compatibility.

## User/Project Value

Mneme can retrieve semantic facts by explicit cues without vector search or machine learning, which strengthens the memory prototype before consolidation and future executive integration.

## Affected Systems

- Memory domain models.
- SQLite storage and migrations.
- Retrieval manager.
- Retrieval tests.
- Memory documentation and backlog.

## Assumptions

- V1 remains local SQLite only.
- Fact object matching can use JSON text search for now.
- Tags are optional metadata on facts.
- Non-active facts can be returned only when explicitly requested.

## Constraints

- Do not add embeddings, vector search, or external services.
- Do not modify the existing `001_init.sql` checksum.
- Preserve backwards-compatible `query_text` retrieval behavior for non-empty queries.

## Non-Goals

- Retrieval reranking formula implementation.
- Entity-aware episode retrieval.
- Conflict detection or supersession decisions.
- Provenance graph traversal.

## Risks

- JSON text matching for object values is coarse.
- Source priority is a deterministic ordering rule, not a full trust model.

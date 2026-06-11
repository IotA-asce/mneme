# Core Idea

## Problem

Retrieval returned facts and episodes in storage-defined order and did not expose why one result ranked ahead of another. The design document already described ranking factors, but the Python retrieval layer had no candidate or explanation layer.

## Desired Outcome

Add deterministic reranking for facts and episodes, with a candidate shape that can later include summaries, and return JSON-friendly explanations for ranked results.

## User/Project Value

Mneme needs explainable memory retrieval before executive behavior can depend on recalled facts or episodes. Ranking explanations make retrieval debuggable without adding opaque machine learning or vector infrastructure.

## Affected Systems

- Retrieval manager.
- Memory bundle model.
- Retrieval tests.
- Memory retrieval documentation.
- Backlog, roadmap/status docs, and durable project memory.

## Assumptions

- V1 stays local and deterministic.
- Facts do not yet expose first-class salience or timestamp fields.
- Episodes expose timestamp, salience, confidence, and entity fields.
- Meta-memory records may exist for retrieval history, but retrieval does not update counters yet.

## Constraints

- Do not add vector databases, embeddings, LLM reranking, or new dependencies.
- Preserve `retrieve_memory(store, query)` and existing bundle fields.
- Keep ranking explanations JSON-friendly.

## Non-Goals

- Summary retrieval.
- Meta-memory counter mutation during retrieval.
- Provenance graph traversal.
- Learned ranking.

## Risks

- Text matching is token overlap, not semantic matching.
- Fact recency and salience remain unavailable until the fact domain model or storage projection grows those fields.

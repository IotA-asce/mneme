# Core Idea

## Problem

Mneme had a consolidation placeholder that counted active episodes and performed no mutations. The design calls for repeated episodes to become summaries and for low-value or summarized details to receive decay/downranking metadata.

## Desired Outcome

Implement a safe, deterministic one-shot consolidation skeleton that can be run manually and tested locally.

## Value

Repeated events can produce durable summary artifacts without deleting source episodes or pretending to have a full background daemon.

## Affected Systems

- Consolidation module.
- SQLite storage helpers.
- Meta-memory provenance metadata.
- Manual scripts.
- Memory docs, backlog, and project memory.

## Assumptions

- Episode context may carry tags in `context["tag"]` or `context["tags"]`.
- Repeated-event summaries should be deterministic and idempotent by group key.
- Decay/downranking metadata can live in meta-memory provenance for this phase.

## Constraints

- Do not use an LLM.
- Do not delete, purge, suppress, or mutate source episode rows.
- Do not add dependencies.
- Keep the pass manually invocable rather than a long-running daemon.

## Non-Goals

- Fact extraction from summaries.
- Conflict detection inside consolidation.
- Retrieval use of decay metadata.
- Scheduler/daemon runtime.

## Risks

- Deterministic grouping is intentionally simple and may group too broadly or miss nuanced repeated events.
- Summary retrieval is still not wired into `retrieve_memory()`.

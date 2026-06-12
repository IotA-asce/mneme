# Memory API and CLI Core Idea

Date: 2026-06-12
Status: Implemented in this feature branch

## Problem

Mneme has testable memory primitives for scoring, storage, retrieval, conflict handling, provenance, and consolidation, but callers must manually stitch those pieces together. That makes replay, smoke testing, and future Codex-driven debugging more fragile than necessary.

## Desired Outcome

Add a small high-level memory facade and command-line interface that expose the existing memory lifecycle without replacing the lower-level modules.

## Project Value

- Gives Codex, scripts, and future replay tools one stable entry point for common memory operations.
- Keeps storage, salience, retrieval, and consolidation independently testable.
- Makes local inspection and JSON-based debugging easier.

## Affected Systems

- Python memory package API.
- Developer scripts.
- Documentation and runbooks.
- Integration tests.

## Constraints

- Keep SQLite as the only persistence dependency.
- Use standard-library `argparse` for V1 CLI.
- Preserve existing model, storage, retrieval, and consolidation behavior.
- Do not introduce ROS, hardware, vector search, or LLM behavior.

## Non-Goals

- No daemon process.
- No new storage schema.
- No summary retrieval implementation.
- No autonomous fact extraction from arbitrary text.

## Risks

- A facade can hide invalid inputs if it over-normalizes. The implementation should delegate validation to existing dataclasses.
- CLI commands can become a second API. The JSON input shapes should match the existing model serialization contracts.

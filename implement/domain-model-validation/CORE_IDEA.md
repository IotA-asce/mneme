# Core Idea

## Problem

The V1 memory models accepted arbitrary values and had no JSON-friendly round-trip boundary. Invalid confidence, salience, timestamps, enum strings, or empty summaries could enter the in-process domain objects and fail later in storage, retrieval, or future interface wrappers.

## Desired Outcome

Keep the existing dataclass architecture, but add explicit validation and serialization helpers to the model layer. Invalid data should fail fast with clear `ValueError`s. Valid models should round-trip through JSON-friendly dictionaries without changing existing scripts or tests.

## Value

This gives future storage, retrieval, and ROS wrapper work a stable domain boundary without adding heavy dependencies or changing the memory architecture.

## Affected Systems

- Python memory models.
- Tests for model validation and serialization.
- Memory model documentation.
- Backlog and durable project memory.

## Constraints

- No Pydantic or heavyweight validation dependency.
- No SQLite schema changes.
- No runtime behavior changes outside model validation and serialization.
- Preserve existing scripts and tests.

## Non-Goals

- No retrieval ranking changes.
- No storage read APIs.
- No conflict resolution or consolidation behavior.
- No ROS 2 runtime implementation.

## Risks

Stricter constructors may reject invalid caller data that previously slipped through. That is intentional for domain safety, but future callers should use the documented validation rules.

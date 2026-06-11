# Core Idea

## Problem

Salience scoring used hardcoded weights and thresholds. `config/memory.yaml` already contained matching values, but callers had no supported path to load them or inspect a detailed scoring explanation.

## Desired Outcome

Keep deterministic scoring and existing default behavior, while allowing callers to opt into config-loaded weights and thresholds. Every score should explain the feature values, weighted components, threshold band, and explicit remember override reason.

## Value

This makes promotion decisions easier to audit and tune without changing the memory architecture, storage schema, retrieval behavior, or adding machine learning.

## Affected Systems

- Salience scoring.
- Salience result model.
- Tests.
- Salience documentation.
- Backlog and project memory.

## Constraints

- No machine learning.
- No new dependencies.
- Preserve explicit remember override behavior.
- Preserve existing default behavior when no config is supplied.

## Non-Goals

- No automatic config loading at import time.
- No retrieval ranking.
- No persistence changes.
- No consolidation behavior.

## Risks

Custom threshold configurations can change promotion decisions. Tests cover boundaries and the default path to keep behavior understandable.

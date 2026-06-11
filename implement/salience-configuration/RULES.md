# Rules

## Architecture Boundaries

- Scoring is deterministic arithmetic only.
- Scoring does not store memories or command behavior.
- Explicit remember can override promotion, but does not bypass storage or future executive layers.

## Configuration Rules

- Default behavior must not require a config file.
- Loading from `config/memory.yaml` must be explicit.
- Unknown weight names are invalid.
- Thresholds must be ordered.
- In V1, `episode_max` and `semantic_candidate_min` must match.

## Explanation Rules

- Include feature values used for scoring.
- Include weighted components.
- Include threshold band.
- Include override reason when present.
- Report defensive clamping instead of hiding it.

## Anti-Patterns

- Do not add machine learning.
- Do not add new dependencies.
- Do not change storage, retrieval, or consolidation behavior in this task.

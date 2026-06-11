# Salience Scoring

Status: V1 deterministic scoring

Salience scoring decides what kind of memory treatment a candidate deserves. It is deterministic arithmetic over configured feature weights. It does not use machine learning, embeddings, LLM calls, or external services.

## Boundary

The salience layer owns:

- scoring `MemoryCandidate.features`,
- applying feature weights,
- applying promotion thresholds,
- preserving the explicit remember override,
- returning an explainable `SalienceResult`.

The salience layer does not own:

- writing raw traces, episodes, or facts,
- retrieval ranking,
- consolidation,
- conflict resolution,
- actuator behavior,
- safety decisions.

## Default Weights

The built-in default weights match `config/memory.yaml` and the design document:

```text
0.22 novelty
0.18 task_relevance
0.18 social_relevance
0.14 surprise
0.12 risk
0.08 contradiction
0.05 repetition_signal
0.03 explicit_remember_flag
```

Calling `score_candidate(candidate)` uses these built-in defaults. This preserves the original behavior.

## Config Loading

Use `load_salience_config()` or pass `config_path` to `score_candidate()` when a caller wants to load salience defaults from `config/memory.yaml`:

```python
from android_brain_memory import load_salience_config, score_candidate

config = load_salience_config("config/memory.yaml")
result = score_candidate(candidate, config=config)

same_result = score_candidate(candidate, config_path="config/memory.yaml")
```

Configurable fields:

- `salience.weights`
- `salience.thresholds`
- `salience.explicit_remember_override`

Unknown weight names are rejected. Missing weight names default to `0.0` in custom weight mappings.

## Promotion Thresholds

Default thresholds:

| Score | Decision |
|---:|---|
| `< 0.25` | `echo_only` |
| `>= 0.25` and `< 0.55` | `working_memory_candidate` |
| `>= 0.55` and `< 0.80` | `episode` |
| `>= 0.80` | `episode_and_semantic_candidate` |

In V1, `episode_max` and `semantic_candidate_min` must match to avoid a gap or overlap between episode-only and semantic-candidate decisions.

## Explicit Remember Override

If `explicit_remember_flag >= 0.9` and `explicit_remember_override` is enabled, the decision becomes:

```text
episode_and_semantic_candidate
```

The numeric score is still reported. The override reason appears in both `SalienceResult.reasons` and `SalienceResult.explanation["override_reason"]`.

## Explanation Payload

`score_candidate()` returns a `SalienceResult` with:

- `score`: final clamped score from `0.0` to `1.0`,
- `decision`: promotion decision,
- `reasons`: short human-readable reason list,
- `components`: weighted score components by feature,
- `explanation`: detailed JSON-friendly scoring details.

The explanation contains:

- `feature_values`: values used for scoring,
- `raw_feature_values`: values found on the feature object before defensive scoring clamp,
- `weights`: weights used,
- `weighted_components`: per-feature weighted contributions,
- `raw_score`: sum before final score clamp,
- `score`: final score,
- `thresholds`: thresholds used,
- `threshold_crossed`: threshold band for the final score,
- `decision`: final decision,
- `override_reason`: explicit remember override reason or `None`,
- `clamped_features`: any defensively clamped feature values.

## Feature Validation and Clamping

Normal `SalienceFeatures` construction rejects invalid feature values through the model layer. Scoring still defensively clamps any mutated or legacy feature values into `0.0..1.0` and records the raw/clamped pair in `clamped_features`.

This keeps the scoring path robust without silently hiding bad input.

## Examples

```python
from android_brain_memory import MemoryCandidate, SalienceFeatures, SourceType, score_candidate

candidate = MemoryCandidate(
    candidate_id="cand_001",
    candidate_type="dialogue",
    summary="User asked Mneme to remember this preference.",
    source_type=SourceType.USER_CONFIRMED,
    confidence=0.95,
    features=SalienceFeatures(novelty=0.8, task_relevance=0.9, explicit_remember_flag=1.0),
)

result = score_candidate(candidate)
assert result.decision == "episode_and_semantic_candidate"
print(result.explanation["weighted_components"])
```

## Testing

Current tests cover:

- threshold boundaries below `0.25`, at `0.25`, at `0.55`, and at `0.80`,
- explicit remember override,
- loading `config/memory.yaml`,
- custom thresholds,
- explanation payload shape,
- defensive clamping for mutated feature values.

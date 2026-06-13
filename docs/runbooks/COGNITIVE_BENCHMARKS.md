# Cognitive Benchmarks

Status: M8 foundation
Date: 2026-06-13

Mneme now has a local benchmark harness for measuring brain-loop behavior without giving a model control over cognition. Benchmarks replay scripted user turns through `MnemeRuntime`, score the response and memory refs, and produce conservative capability ladder evidence.

## Run A Benchmark

```bash
mneme eval cognition --fixture tests/fixtures/cognition/basic_preference_recall.yaml --json
```

Benchmark runs use an isolated temporary SQLite database by default. To inspect a benchmark database after the run, pass an explicit path:

```bash
mneme eval cognition \
  --fixture tests/fixtures/cognition/basic_preference_recall.yaml \
  --benchmark-db .local/evaluation/basic_preference_recall.sqlite3 \
  --json
```

## Capability Evidence

```bash
mneme eval capability --json
```

When the bundled benchmark fixture is available, this command runs it and maps the result to the conservative L0-L8 ladder in `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md`.

This is not an animal-equivalence or sentience claim. It is only behavioral evidence for the benchmark categories that passed.

## Fixture Shape

Fixtures are YAML or JSON:

```yaml
name: basic_preference_recall
category: preference_recall
steps:
  - input: "remember that I like green tea"
    expect:
      turn_type: explicit_remember_instruction
      act_type: acknowledge
      response_contains:
        - remember
  - input: "what do I like?"
    expect:
      turn_type: recall_question
      act_type: answer
      memory_ref_required: true
      response_contains:
        - green tea
```

Supported expectation fields include:

- `turn_type`
- `act_type`
- `response_contains`
- `response_not_contains`
- `memory_ref_required`
- `correction_proposal`
- `model_realized`
- `max_latency_ms`
- `contradiction_clarification`
- `category_tags`

## Current Scored Areas

The first scorer reports:

- preference recall,
- delayed recall,
- hallucinated memory guard,
- provenance correctness,
- contradiction handling,
- correction acceptance,
- interruption recovery placeholder,
- stuck-state detection,
- response latency,
- model fallback rate.

Some categories are intentionally shallow until richer fixtures exist. Future benchmarks should add live-speech interruption runs, person continuity, contradiction review, correction approval, and long-running soak replay.

## Review And Explanation Commands

The runtime now classifies user turns before dialogue planning. Useful typed checks:

```bash
mneme run --json --input "remember that I like green tea" --input "what do I like?" --input "why did you say that?"
mneme run --json --input "what do you remember about me?"
mneme run --json --input "what can you do?"
mneme run --json --input "what model are you using?"
```

Correction and forget turns create review proposals in the runtime snapshot, but they do not mutate durable facts or purge memory yet.

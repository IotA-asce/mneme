# Cognitive Capability Roadmap

Date: 2026-06-13
Status: Planning reference for local model integration and long-term cognitive evaluation

This document refines the post-Stage 6 roadmap for Mneme's brain-first path. It answers two questions:

1. How should local AI models be connected without turning the model into the whole brain?
2. How should Mneme's cognitive capability be measured over time against biological reference points, while avoiding false claims of sentience or human equivalence?

The short answer:

- Mneme should add local models as bounded cognitive tools behind existing runtime boundaries.
- Mneme should be evaluated through behavioral capability tests, not neuron-count comparisons.
- Physical embodiment stays deferred until the local brain loop is stable, inspectable, and useful over repeated sessions.

## Current Baseline

Mneme currently implements a deterministic local virtual-head brain loop:

- memory lifecycle,
- retrieval and provenance,
- salience scoring,
- working memory,
- world model,
- attention,
- executive intent,
- deterministic dialogue planning,
- virtual speech/avatar state,
- local UI,
- optional local speech/vision/TTS seams,
- local model registry hygiene.

Mneme does **not** currently use a local LLM or cloud LLM for conversation. The current dialogue planner is deterministic and template-based, though it can ground responses in memory and current-turn context.

Behaviorally, the current system sits around **L1 to early L2** on the capability ladder below: more structured than a reflex loop, but not yet a flexible animal-like agent.

## Non-Negotiable Architecture Rule

The model must not become the robot brain by itself.

Mneme's architecture remains:

```text
perception workers
  -> world model / working memory
  -> retrieval and memory services
  -> attention
  -> executive intent
  -> dialogue planner / model realizer
  -> safety filter
  -> virtual or physical skills
```

Local models may help with:

- language realization,
- intent interpretation,
- summarization,
- retrieval query expansion,
- memory-candidate proposal,
- contradiction explanation,
- lightweight planning proposals,
- perception model outputs through existing worker contracts.

Local models may not:

- directly command actuators,
- bypass executive intent,
- silently write confirmed facts,
- overwrite user-confirmed memory,
- change safety policy,
- perform unrestricted self-modification,
- treat inference as truth.

Every learned or model-generated claim remains `model_inferred` unless explicitly confirmed by the user.

## Cognitive Target Definition

The long-term goal is **human-brain-equivalent functional capability** for a bounded android-head context, not a claim of biological consciousness.

For Mneme, "human-brain-equivalent" should mean:

- stable autobiographical continuity,
- grounded multimodal perception,
- long-horizon memory and planning,
- conversational reasoning,
- self-monitoring,
- uncertainty awareness,
- correction acceptance,
- social timing,
- safe action arbitration,
- bounded adaptive learning,
- transparent explanations of what it remembers and why.

It does **not** mean:

- claiming consciousness,
- unrestricted autonomy,
- direct human-level general agency,
- biological neuron simulation,
- uncontrolled self-improvement,
- permanent storage of everything.

## Biological Reference Points

Neuron counts are useful context but not the main metric. Behavioral capability matters more.

Known reference anchors:

- `C. elegans`: 302 neurons; useful reference for simple stimulus-response and whole-connectome simulation.
- Adult fruit fly: complete brain connectome around 139,255 neurons; useful reference for compact perception/action behaviors.
- Human brain: commonly cited around 86 billion neurons; useful only as a rough biological scale reference.

Mneme should compare itself to animals through tasks:

- Can it orient to relevant stimuli?
- Can it remember a repeated person?
- Can it learn preferences?
- Can it resolve contradictions?
- Can it recover from interruption?
- Can it pursue a goal across multiple turns?
- Can it explain uncertainty?

Do not publish claims like "Mneme is equivalent to a mouse" unless the claim is explicitly scoped to the benchmark set.

## Capability Ladder

This ladder is an operational yardstick. It is not a literal biological equivalence claim.

| Level | Analogy | Mneme Capability Definition | Current Status |
|---|---|---|---|
| L0 | Reflex circuit | Reacts to events with fixed outputs, no durable context | Passed |
| L1 | Simple nervous system | Maintains short state, deterministic stimulus-response, basic safety reflexes | Passed |
| L2 | Insect-like | Attention, salience, simple memory promotion, repeated-pattern awareness | Partial |
| L3 | Fish/reptile-like | Persistent environment state, novelty/threat handling, basic routines | Planned |
| L4 | Mouse-like | Episodic recall, object/person continuity, preference learning, correction | Planned |
| L5 | Dog/corvid-like | Social memory, flexible problem solving, expectation, interruption recovery | Planned |
| L6 | Primate-like | Multi-step planning, social inference, tool-like reasoning, self-monitoring | Planned |
| L7 | Human-assistant-like | Rich language, reliable autobiographical memory, abstraction, explainability | Planned |
| L8 | Human-brain-equivalent target | Robust lifelong continuity, cross-modal grounding, adaptive learning, safe autonomy | Long-term target |

Progression requires benchmark evidence, not subjective impressions.

## Milestone Overview

The post-Stage 6 brain-first roadmap is:

```text
M7   Local Cognitive Model Layer
M8   Cognitive Benchmark Harness and Capability Ladder
M9   Live Multimodal Daily Driver
M10  Memory Self-Review and Correction Loop
M11  Bounded Adaptation and Procedural Learning
M12  Higher Cognitive Functions
M13  Physical Embodiment Readiness Gate
```

These milestones refine the existing Stage 7+ roadmap. Physical embodiment remains deferred until M13 gate criteria are met.

## M7 — Local Cognitive Model Layer

Goal: connect local models to Mneme without compromising memory provenance, safety, or architecture boundaries.

Implementation status as of 2026-06-13: M7.1-M7.4 are implemented for local Ollama readiness, bounded context construction, model-backed wording with deterministic fallback, and runtime/UI cognition status. The model remains a wording layer; benchmark-driven capability scoring starts in M8.

### M7.1 Model Runtime Adapter

Add:

- `src/android_brain_memory/model_runtime.py`
- `tests/test_model_runtime.py`
- `docs/runbooks/LOCAL_COGNITIVE_MODELS.md`
- `config/models.yaml` entries for chat/reasoning models

Implement:

- `ModelRuntimeAdapter` protocol.
- `ModelRequest` and `ModelResponse` dataclasses.
- `FakeModelRuntime` for deterministic tests.
- `OllamaRuntimeAdapter` using local HTTP API.
- `OpenAICompatibleLocalAdapter` for llama.cpp or similar local servers.
- Timeout, max tokens, temperature, seed, and stop sequence controls.
- Explicit unavailable/error result states instead of exceptions leaking into cognition.

Do not add a hard dependency on Ollama, llama.cpp, MLX, or Transformers in the base install.

Expected tests:

- fake model returns deterministic response,
- unavailable model produces structured failure,
- adapter redacts or rejects nonlocal URLs unless explicitly configured,
- timeout produces failed model response,
- model output is JSON-serializable.

Exit criteria:

- `mneme cognition check` can report whether a configured local model backend is reachable.
- Existing deterministic dialogue still works when no model is available.

### M7.2 Cognitive Context Builder

Add:

- `src/android_brain_memory/cognitive_context.py`
- `tests/test_cognitive_context.py`
- documentation section in `docs/runbooks/LOCAL_COGNITIVE_MODELS.md`

Build a compact context packet from:

- user utterance,
- working memory,
- attention state,
- safety state,
- top retrieved facts,
- top retrieved episodes,
- provenance summaries,
- speakability constraints,
- current avatar/speech state.

Rules:

- Context includes memory IDs and source types.
- Context excludes `never_say` and `internal_only` content.
- Restricted content can be summarized only as "restricted memory exists" unless trusted internal mode is enabled.
- Token/character budgets are enforced deterministically.
- Facts and episodes are ranked before context construction.

Exit criteria:

- Context is bounded, stable under tests, and explains which memory refs were included or omitted.

### M7.3 Model Dialogue Realizer

Add:

- `src/android_brain_memory/model_dialogue.py`
- `tests/test_model_dialogue.py`
- updates to `src/android_brain_memory/dialogue.py`

Modify:

- `DialoguePlanner` keeps deterministic act selection.
- A new `ModelDialogueRealizer` turns a safe act plan and cognitive context into final wording.
- If model realization fails, fallback to deterministic text.

Expected model output schema:

```json
{
  "response_text": "string",
  "memory_refs_used": [{"memory_kind": "fact", "memory_id": "fact_..."}],
  "uncertainty": "low|medium|high",
  "proposed_memory_candidates": [],
  "safety_notes": []
}
```

Rules:

- The model may not invent memory refs.
- The model may not claim user-confirmed status for inferred memory.
- The model may propose memory candidates, but not commit them.
- The deterministic safety filter reviews final text before speech.

Exit criteria:

- A typed UI conversation can use the local model for wording while still showing memory refs and falling back cleanly.

### M7.4 CLI and UI Integration

Add or modify:

- `src/android_brain_memory/virtual_head.py`
- `src/android_brain_memory/local_ui.py`
- `README.md`
- `docs/runbooks/LOCAL_COGNITIVE_MODELS.md`

Commands:

```bash
mneme cognition check
mneme run --profile local-cognition
mneme ui --cognition-profile local
```

UI should show:

- model connected/disconnected,
- configured backend,
- last model latency,
- model failure reason,
- memory refs used,
- deterministic fallback indicator.

Exit criteria:

- The UI makes it obvious whether responses are model-realized or deterministic fallback.

## M8 — Cognitive Benchmark Harness and Capability Ladder

Goal: make cognitive progress measurable and comparable over time.

### M8.1 Benchmark Fixture Format

Add:

- `docs/runbooks/COGNITIVE_BENCHMARKS.md`
- `tests/fixtures/cognition/`
- `src/android_brain_memory/cognitive_benchmarks.py`
- `tests/test_cognitive_benchmarks.py`

Fixture format should support:

- scripted events,
- user utterances,
- expected memory state,
- expected response constraints,
- expected attention shifts,
- expected safety state,
- scoring rubric.

Example benchmark categories:

- preference recall,
- delayed recall,
- contradiction handling,
- interruption recovery,
- object/person continuity,
- self-model question,
- uncertainty phrasing,
- safety/degraded response,
- repeated visitor continuity,
- multi-turn goal tracking.

Exit criteria:

- `mneme eval cognition --fixture tests/fixtures/cognition/basic_recall.yaml --json` produces a score report.

### M8.2 Capability Ladder Scoring

Add:

- `src/android_brain_memory/capability_ladder.py`
- `tests/test_capability_ladder.py`
- update `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md`

Metrics:

- recall success rate,
- hallucinated memory rate,
- contradiction rate,
- correction acceptance,
- response latency,
- interruption recovery,
- repeated-person continuity,
- stuck-state count,
- safety intervention count,
- provenance correctness,
- uncertainty correctness.

Map metrics to ladder levels conservatively:

- L2 requires stable attention + salience + simple memory recall.
- L3 requires persistent world state and reliable novelty/threat handling.
- L4 requires episodic recall, preference learning, and corrections.
- L5 requires social continuity and flexible interruption recovery.
- L6+ requires multi-step planning and self-monitoring benchmarks.

Exit criteria:

- Mneme can report current ladder evidence without overclaiming.

### M8.3 Evaluation Dashboard

Modify:

- `src/android_brain_memory/local_ui.py`
- `src/android_brain_memory/evaluation.py`

Add:

- latest benchmark score,
- cognitive level estimate,
- failure categories,
- recent regressions,
- "why this level" explanation.

Exit criteria:

- UI shows capability evidence, not just runtime state.

## M9 — Live Multimodal Daily Driver

Goal: run Mneme locally in a useful everyday loop with microphone, speaker, camera, local model, and memory.

### M9.1 Speech Loop Hardening

Modify:

- `src/android_brain_memory/live_perception.py`
- `src/android_brain_memory/local_audio.py`
- `src/android_brain_memory/presence.py`
- `docs/runbooks/LOCAL_LIVING_LAB.md`

Add:

- ASR latency metrics,
- no-speech handling,
- barge-in metrics,
- TTS failure recovery,
- duplicate-response prevention checks,
- speaker device routing documentation.

Exit criteria:

- 30-minute local speech session with no duplicate responses and bounded latency.

### M9.2 Vision and Person Continuity

Modify or add:

- `src/android_brain_memory/local_vision.py`
- `src/android_brain_memory/world_model.py`
- `src/android_brain_memory/person_continuity.py`
- `tests/test_person_continuity.py`
- `docs/perception/PERSON_CONTINUITY.md`

Start with:

- anonymous session person IDs,
- user-confirmed names,
- camera/speaker temporal fusion,
- no unrestricted face recognition.

Optional later:

- face embeddings only after a specific permissive-license model is approved.

Exit criteria:

- Mneme can distinguish "same session visitor likely continues" without claiming permanent identity.

### M9.3 Daily Logs and Redaction

Add:

- `src/android_brain_memory/redaction.py`
- `tests/test_redaction.py`
- `docs/runbooks/PRIVATE_LOGS.md`

Add support for:

- raw local private logs,
- redacted replay logs,
- user-approved export,
- deletion and purge commands.

Exit criteria:

- Real logs can become replay fixtures without exposing private raw content.

## M10 — Memory Self-Review and Correction Loop

Goal: Mneme can inspect, explain, and repair its memory with user supervision.

### M10.1 Memory Inspector UI

Modify:

- `src/android_brain_memory/local_ui.py`

Add:

- memory refs shown beside responses,
- "why did you say that?",
- "what do you remember about me?",
- "forget this",
- "that is wrong",
- "confirm this".

Backend additions:

- review commands on `MnemeMemory`,
- safe write paths for corrections,
- explicit provenance updates.

Exit criteria:

- User corrections produce auditable memory changes.

### M10.2 Contradiction Review Workflow

Modify:

- `src/android_brain_memory/storage.py`
- `src/android_brain_memory/retrieval.py`
- `src/android_brain_memory/dialogue.py`

Add:

- review queue for conflicted facts,
- user confirmation prompts,
- conflict resolution history,
- no silent deletion.

Exit criteria:

- Conflicts can be reviewed in UI/CLI and resolved without data loss.

### M10.3 Self-Model Review

Modify:

- `src/android_brain_memory/self_model.py`
- `docs/memory/SELF_MODEL.md`

Add:

- "what are you?",
- "what can you do?",
- "what do you not know?",
- "what devices are connected?",
- "what model are you using?"

Exit criteria:

- Mneme can accurately describe its current implementation and limitations.

## M11 — Bounded Adaptation and Procedural Learning

Goal: Mneme adjusts behavior within safe documented ranges based on evaluation evidence.

### M11.1 Adaptation Controller

Add:

- `src/android_brain_memory/adaptation.py`
- `tests/test_adaptation.py`
- `docs/cognition/ADAPTATION_POLICY.md`

Allow bounded updates to:

- salience thresholds,
- retrieval weights,
- response delay,
- gaze dwell,
- curiosity interval,
- TTS pace/voice preference,
- interruption timeout.

Rules:

- every update uses procedural memory,
- every update has provenance,
- every update is reversible,
- no safety policy updates through adaptation,
- no model self-modification.

Exit criteria:

- A benchmark-driven adaptation can improve one metric without regressing safety tests.

### M11.2 Soak Replay and Regression Guard

Add:

- `tests/fixtures/soak/`
- `scripts/run_soak_replay.py`
- `docs/runbooks/SOAK_REPLAY.md`

Measure:

- memory growth,
- contradiction growth,
- latency drift,
- stuck states,
- duplicate speech,
- correction rate.

Exit criteria:

- Repeated daily-driver logs can be replayed and compared across commits.

## M12 — Higher Cognitive Functions

Goal: move from reactive conversation to flexible local reasoning and planning.

### M12.1 Goal Decomposition

Add:

- `src/android_brain_memory/planning.py`
- `tests/test_planning.py`
- `docs/executive/GOAL_PLANNING.md`

Capabilities:

- break user request into steps,
- ask clarification before acting,
- track plan progress,
- update working memory,
- avoid direct actuator calls.

Exit criteria:

- Mneme can maintain and explain a multi-turn goal.

### M12.2 Mental Simulation

Add:

- `src/android_brain_memory/simulation_reasoning.py`
- `tests/test_simulation_reasoning.py`

Use local model proposals for:

- possible outcomes,
- risk notes,
- memory checks,
- response options.

Rules:

- simulation output is advisory,
- executive chooses intent,
- safety can reject proposals.

Exit criteria:

- Mneme can evaluate multiple response/action options and explain why one was selected.

### M12.3 Curiosity and Exploration

Modify:

- `src/android_brain_memory/attention.py`
- `src/android_brain_memory/executive.py`
- `src/android_brain_memory/adaptation.py`

Add:

- bounded curiosity goals,
- novelty-driven questions,
- safe "I wonder..." prompts,
- no intrusive behavior loops.

Exit criteria:

- Curiosity improves knowledge without annoying repetition or unsafe action.

## M13 — Physical Embodiment Readiness Gate

Goal: decide whether Mneme is ready to connect to physical hardware.

Do not start physical embodiment until the following are true:

- M7 local model layer works with deterministic fallback.
- M8 benchmark harness exists.
- M9 live multimodal daily driver runs reliably.
- M10 correction/review workflow exists.
- M11 adaptation is bounded and reversible.
- Safety tests remain green.
- The UI can explain memory refs, model status, and confidence.
- No duplicate speech or stuck listening/speaking loops in soak tests.
- Hardware safety planning is updated before any actuation code.

Physical embodiment then resumes under the existing hardware safety rules:

- fake actuator backend first,
- actuator bridge chokepoint,
- limits and rate limiting,
- emergency stop,
- one actuator at a time,
- never direct model-to-actuator control.

## Evaluation Matrix

Each milestone should update this matrix.

| Capability | Metric | Baseline | Target Before Hardware |
|---|---|---:|---:|
| Preference recall | correct answer after 1 day | not measured | >90% on confirmed facts |
| Hallucinated memory | unsupported memory claim rate | not measured | <2% in benchmark suite |
| Contradiction handling | asks for clarification | partial | >95% on conflict fixtures |
| Interruption recovery | resumes or cancels appropriately | partial | >95% in speech soak |
| Latency | user speech to response start | not measured | p95 under local threshold |
| Person continuity | session visitor continuity | not implemented | >85% session-local |
| Correction acceptance | user correction changes memory safely | not implemented | >95% audited |
| Stuck states | stuck listening/speaking loops | not measured | 0 in soak suite |
| Provenance correctness | response memory refs valid | partial | 100% in benchmarks |
| Safety override | degraded/emergency behavior | virtual only | 100% in dry-run tests |

## Model Backend Preference

Start with adapters, not a hard runtime choice.

Recommended order:

1. **Ollama adapter** for easiest local setup and model management.
2. **OpenAI-compatible local adapter** for llama.cpp and similar servers.
3. **MLX-LM adapter** for Apple Silicon optimized local inference.
4. **Transformers adapter** for task-specific pipelines where needed.

Base install remains lightweight. Model backends belong behind optional extras or external local services.

## Data and Memory Policy

Local models must preserve Mneme's memory semantics:

- User-confirmed facts outrank inferred facts.
- Model outputs are `model_inferred`.
- Proposed memories go through salience scoring.
- Confirmations require explicit user action.
- Speakability filtering applies before model context construction.
- Restricted/internal memories are not exposed to ordinary dialogue generation.
- Raw logs remain local and require redaction before becoming replay fixtures.

## UI Requirements

The Local Living Lab UI should eventually show:

- model backend and model name,
- connected/disconnected state,
- model latency,
- deterministic fallback state,
- active attention target,
- current memory refs,
- latest retrieval query,
- confidence/uncertainty,
- safety state,
- current capability ladder evidence,
- recent benchmark regressions.

The UI must not own cognition. It visualizes and sends user input/control events only.

## Documentation Updates Required Per Milestone

Each milestone must update:

- this file,
- `docs/architecture/MASTER_ROADMAP.md`,
- `docs/architecture/REPO_STATUS.md`,
- relevant runbook under `docs/runbooks/`,
- `tasks/backlog.md`,
- project memory under `memory/`,
- implementation plan under `implement/`.

## References

- `llama.cpp` local server: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Ollama API: https://docs.ollama.com/api/introduction
- MLX-LM: https://github.com/ml-explore/mlx-lm
- Hugging Face Transformers pipelines: https://huggingface.co/docs/transformers/en/main_classes/pipelines
- Human brain neuron count reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC2776484/
- OpenWorm: https://openworm.org/
- Adult fruit fly connectome report: https://www.cam.ac.uk/research/news/first-map-of-every-neuron-in-an-adult-fly-brain-complete

## Next Concrete Task

The safest first implementation task is **M7.1 Model Runtime Adapter**:

1. Add dataclasses and adapter protocol.
2. Add fake adapter tests.
3. Add Ollama adapter behind standard-library HTTP calls.
4. Add `mneme cognition check`.
5. Show model availability in `mneme ui`.
6. Keep deterministic dialogue fallback active.

This gives Mneme a local model connection without changing safety, memory, or executive ownership.

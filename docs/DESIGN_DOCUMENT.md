# Android Brain — Comprehensive Design Document

Status: **Starter design**  
Primary subsystem: **Memory architecture**  
Target implementation phase: **V1 local prototype**

---

## 1. Vision

The long-term goal is to build the software brain for a small-scale android robot, beginning with a robot head and later expanding into a body. The desired behavior is not just chatbot-like speech. The robot should feel like it has presence: it should perceive, attend, remember, reason, speak, and act with continuity.

The system should eventually support:

- vision, hearing, touch, body state, and internal health sensing
- parallel perception workers
- shared world model
- attention management
- human-inspired memory
- executive reasoning
- dialogue planning
- motor skills
- safety override and observability

The first build target is the **memory system**, because memory determines continuity, identity, learning, personalization, and context-aware behavior.

---

## 2. Core architecture philosophy

The robot brain must not be a single giant loop.

A serial workflow like this is too slow and brittle:

```text
sense → think → act
```

The desired architecture is organized parallelism:

```text
many workers observe → shared state is built → one executive arbitrates → many skills execute
```

The key authority rule is:

```text
workers publish observations
state builders publish state
executive publishes intent
skills publish actuator goals
actuator bridge sends final commands
safety can override all stages
```

Memory follows the same principle. It does not directly control behavior. It provides structured context, facts, episodes, and confidence-weighted retrieval results to the executive and dialogue planner.

---

## 3. V1 scope

V1 is a **local memory prototype** that can run on a laptop or Mac mini without robot hardware.

### V1 must include

- SQLite database schema
- Python data models
- sensory echo representation
- working memory representation
- salience scoring
- episode encoding
- fact storage
- provenance tracking
- retrieval manager
- basic consolidation daemon
- CLI smoke test
- unit tests

### V1 should expose

- a programmatic Python API
- a CLI/demo path
- JSON-friendly outputs suitable for future ROS messages

### V1 must not include

- physical actuator control
- real-time safety-critical code
- direct camera/microphone processing
- full ROS 2 integration
- long-running LLM agents
- procedural self-modification

---

## 4. Brain-level modules

The eventual full robot brain has these major modules:

### 4.1 Sensory inputs

Examples:

- vision cameras
- microphones / ears
- touch sensors
- IMU / balance
- proprioception / joint state
- internal health sensors

### 4.2 Parallel perception workers

Specialist processes that convert raw sensory data into observations:

- face tracking
- speaker localization
- speech-to-text
- object detection
- prosody / emotion cue estimation
- touch interpretation
- saliency detection

These workers are not allowed to command motors directly.

### 4.3 Shared world model

A structured representation of the current situation:

- active people
- active speaker
- salient objects
- current scene
- safety state
- body state

### 4.4 Attention manager

The selector of relevance. It answers:

- What should the robot focus on now?
- What should be remembered?
- What should be ignored?
- What should receive sensor/motor resources?

### 4.5 Memory system

The system described in this document.

### 4.6 Executive / thought engine

The decision layer:

- behavior tree executive
- dialogue planner
- policy layer
- retrieval manager
- task reasoning

### 4.7 Skill controllers

The action layer:

- gaze control
- eyelids / brows / ears
- head pose
- voice / speech
- gesture / future body actions

### 4.8 Safety and observability

Cross-cutting supervision:

- safety override
- diagnostics
- logging
- replay
- degraded mode handling

---

## 5. Memory design goals

The memory system must satisfy these goals:

1. **Fast during live interaction**  
   Working memory and recent context must be quickly accessible.

2. **Selective, not exhaustive**  
   The system should not store everything forever.

3. **Human-inspired compression**  
   Repetitive experiences should become summaries, facts, or procedures.

4. **Provenance-aware**  
   The system must track where a memory came from.

5. **Confidence-aware**  
   The system must distinguish certainty from weak inference.

6. **Contextual retrieval**  
   Retrieval should be based on current speaker, topic, goal, recency, place, object, and relevance.

7. **Auditable and reversible**  
   Changes should preserve history when possible.

---

## 6. Memory layers

The system uses seven memory layers.

### 6.1 Sensory Echo Buffer

Purpose: hold very recent raw or semi-raw traces.

Typical duration:

- milliseconds to seconds for raw streams
- seconds to minutes for summarized fragments

Stores:

- recent ASR fragments
- recent face/person observations
- recent touch events
- recent body-state events
- recent attention changes
- recent internal/system events

Most sensory echo items are not promoted.

### 6.2 Working Memory

Purpose: active context for current reasoning.

Stores:

- current speaker
- current topic
- current attention target
- recent dialogue turns
- active goal
- active safety state
- unresolved references
- pending response intent

Working memory should be small and frequently updated.

### 6.3 Episodic Memory

Purpose: time-stamped autobiographical events.

Stores:

- important conversations
- first encounters
- surprising events
- errors and recoveries
- explicit user instructions
- task outcomes
- high-salience social interactions

Episodes should include time, participants, context, summary, salience, confidence, and provenance.

### 6.4 Semantic Memory

Purpose: generalized knowledge.

Stores:

- facts
- preferences
- identities
- relationships
- object/room knowledge
- recurring patterns

Semantic memory should be cleaner than episodic memory.

### 6.5 Procedural Memory

Purpose: how-to behavior and skill parameters.

Examples:

- gaze timing preferences
- blink behavior profiles
- greeting routines
- safe motion profiles
- interaction habits

V1 only stores procedural candidates. It does not autonomously modify live behavior.

### 6.6 Self Model

Purpose: the robot's memory of its own body, capabilities, and limits.

Examples:

- left eyelid tendon is loose
- camera exposure is weak in low light
- speech system has high latency
- current build version
- known limitations

### 6.7 Meta-Memory

Purpose: memory about memory.

Stores:

- confidence
- source type
- last retrieval time
- retrieval count
- contradiction status
- whether something is user-confirmed
- whether something is safe to speak aloud

---

## 7. Memory lifecycle

Every memory candidate follows this lifecycle:

```text
observe → buffer → score → promote → consolidate → semanticize → retrieve → decay/suppress/forget
```

### 7.1 Observe

An observation is created by a perception worker, state builder, dialogue system, or executive event.

Examples:

- “User said: remember this.”
- “Face detected.”
- “Touch detected on right ear shell.”
- “Task succeeded.”
- “Dialogue response failed.”

### 7.2 Buffer

The observation enters the sensory echo buffer.

### 7.3 Score

The salience scoring engine calculates importance.

### 7.4 Promote

Important candidates become working-memory items, episodes, fact candidates, or procedural candidates.

### 7.5 Consolidate

Background processing clusters, summarizes, extracts facts, detects conflicts, and prunes low-value traces.

### 7.6 Semanticize

Repeated or important episodes become semantic facts, preferences, relationships, or summaries.

### 7.7 Retrieve

The executive or dialogue planner asks for relevant memory based on current context.

### 7.8 Decay / suppress / forget

Low-value, obsolete, unsafe, or user-deleted memories are down-ranked, compressed, hidden, or purged depending on policy.

---

## 8. Salience scoring

Salience determines what deserves memory resources.

Detailed V1 implementation notes live in `docs/memory/SALIENCE.md`.

### 8.1 Scoring factors

Each candidate is scored using:

- novelty
- task relevance
- social relevance
- surprise
- risk
- contradiction
- repetition
- explicit remember flag

### 8.2 Default scoring formula

```text
salience =
  0.22 * novelty +
  0.18 * task_relevance +
  0.18 * social_relevance +
  0.14 * surprise +
  0.12 * risk +
  0.08 * contradiction +
  0.05 * repetition_signal +
  0.03 * explicit_remember_flag
```

For V1, explicit remember requests may override normal thresholds.

The default weights and thresholds are mirrored in `config/memory.yaml`.

### 8.3 Promotion thresholds

Suggested defaults:

| Score | Action |
|---:|---|
| `< 0.25` | Echo only, then decay |
| `>= 0.25` and `< 0.55` | Working memory / short candidate retention |
| `>= 0.55` and `< 0.80` | Store episode |
| `>= 0.80` | Store episode and queue semantic extraction |

---

## 9. Truth and provenance model

The system must never collapse these categories:

```text
raw observation ≠ inference ≠ confirmed fact
```

### 9.1 Source types

- `sensor_observed`
- `model_inferred`
- `executive_generated`
- `user_confirmed`
- `imported`
- `system_generated`

### 9.2 Confidence

Every memory item has confidence from `0.0` to `1.0`.

### 9.3 Provenance

Every memory item should preserve:

- source node or source type
- timestamp
- supporting observations
- supporting episodes
- derivation chain
- version history

### 9.4 Speaking rules

The dialogue layer should phrase memories according to certainty:

- “You told me…” for user-confirmed facts
- “I observed…” for sensor observations
- “I think…” for inferred facts
- “I may be wrong…” for low-confidence facts

---

## 10. Storage architecture

V1 uses SQLite.

Main tables:

- `raw_trace`
- `episode`
- `episode_entity`
- `fact`
- `fact_support`
- `fact_tag`
- `memory_summary`
- `meta_memory`
- `working_context_snapshot`

The database must support:

- chronological queries
- entity-based queries
- fact lookup
- provenance traversal
- full-text search later

---

## 11. Retrieval architecture

Retrieval is cue-based, not global.

Detailed V1 implementation notes live in `docs/memory/RETRIEVAL.md`.

### 11.1 Query cues

A retrieval query may include:

- person
- topic
- object
- place
- current goal
- recent dialogue
- active task
- memory type
- tags
- structured fact filters for subject, predicate, object text, source type, and status

### 11.2 Retrieval order

The retrieval manager should search:

1. working memory
2. semantic memory
3. recent episodes
4. older episodes
5. summaries
6. self model

### 11.3 Reranking factors

Suggested score:

```text
score =
  0.30 * context_match +
  0.20 * entity_match +
  0.15 * recency +
  0.15 * salience +
  0.10 * confidence +
  0.05 * source_reliability +
  0.05 * retrieval_history_bonus
```

### 11.4 Retrieval result

A retrieval response should include:

- summary
- facts
- episodes
- warnings
- confidence
- provenance summary
- ranking explanations for debug/traceability

---

## 12. Consolidation daemon

The consolidation daemon runs during idle time.

Jobs:

1. replay recent important episodes
2. cluster similar episodes
3. create summaries
4. extract facts
5. detect contradictions
6. prune or down-rank low-value items
7. stage procedural candidates

V1 can implement this as a simple CLI/background function rather than a real daemon.

---

## 13. Forgetting policy

Forgetting is not only deletion. The system supports:

### 13.1 Accessibility decay

The item remains stored but becomes less likely to retrieve.

### 13.2 Detail decay

The rich episode is compressed into a gist.

### 13.3 Compression

Multiple similar episodes become a summary.

### 13.4 Suppression

Unsafe, irrelevant, or user-restricted items are hidden from normal retrieval.

### 13.5 Purge

The item is irreversibly deleted. This should be rare and usually user-requested.

---

## 14. Conflict policy

When new information conflicts with old information:

1. Do not silently overwrite.
2. Preserve both items if context differs.
3. Prefer user-confirmed facts over inferred facts.
4. Mark obsolete facts as `superseded`.
5. Ask for confirmation if the conflict matters for behavior.

---

## 15. API design

V1 exposes a Python API.

Primary functions:

- `score_candidate(candidate) -> SalienceResult`
- `store_raw_trace(trace) -> trace_id`
- `encode_episode(candidate) -> episode_id`
- `upsert_fact(fact) -> fact_id`
- `retrieve(query) -> MemoryBundle`
- `consolidate_once() -> ConsolidationReport`

Future ROS-style APIs are drafted in `interfaces/`.

---

## 16. Observability

The system should log:

- every promotion decision
- score components
- storage writes
- retrieval queries
- retrieval rankings
- consolidation changes
- conflicts detected
- pruning decisions

V1 uses structured JSON logs where possible.

---

## 17. Testing strategy

### Unit tests

- salience scoring
- promotion thresholds
- fact upsert
- episode write/read
- retrieval ranking
- conflict handling

### Integration tests

- simulate a conversation
- store important event
- retrieve by topic/person
- consolidate repeated events

### Failure tests

- empty database
- malformed candidate
- duplicate fact
- low-confidence inference
- contradictory fact

---

## 18. Future ROS 2 integration

Future memory nodes:

- `sensory_echo_node`
- `working_memory_node`
- `episodic_encoder_node`
- `semantic_extractor_node`
- `retrieval_manager_node`
- `consolidation_daemon_node`
- `conflict_resolver_node`
- `meta_memory_node`

Future ROS-style communication:

- topics for continuous memory candidates and debug events
- services for quick fact/context lookups
- actions for retrieval and consolidation

The current repo includes interface drafts but does not require a ROS 2 installation.

---

## 19. Design constraints for Codex

Codex should follow these constraints:

- Do not expand scope without explicit permission.
- Keep V1 lightweight and local.
- Avoid adding vector databases in the first implementation.
- Avoid adding LLM dependencies in the first implementation.
- Keep every data model source-aware.
- Write tests before expanding features.
- Preserve design docs as source of truth.

---

## 20. Milestone definition of done

V1 is done when:

- database initializes cleanly
- a memory candidate can be scored
- high-salience events become episodes
- explicit user facts can be stored
- relevant facts/episodes can be retrieved by query
- consolidation can produce at least one summary artifact
- all major paths have smoke tests
- design docs match implementation

---

## 21. Open questions

These should be decided later:

- exact ROS 2 package structure
- whether to use embeddings/vector search
- whether memory should support multimodal raw trace storage
- exact privacy/speakability policy
- how user identity will be confirmed
- whether procedural memory can tune behavior automatically
- whether long-term memory should sync across devices

---

## 22. Summary

The memory system should operate by this law:

> Experience broadly, store narrowly, summarize aggressively, preserve the rare, and retrieve by context.

That is the foundation of the android brain.

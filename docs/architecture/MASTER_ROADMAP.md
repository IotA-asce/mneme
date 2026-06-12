# Mneme Master Roadmap

Date: 2026-06-12
Status: Long-term implementation roadmap from the V1 memory core to the complete android head brain

This roadmap covers every implementation milestone between the current bench-only memory prototype and the end goal: a safe, debuggable, expressive, memory-centered robot head with lifelike attention, timing, memory continuity, and transparent reasoning.

Ordering rules:

- Milestones are ordered by dependency and safety, not by excitement.
- Every stage must keep the scenario-replay regression harness green.
- Determinism first: every capability ships deterministic and testable before any learned or model-driven variant is allowed.
- Safety gates are hard boundaries — later stages do not start until the gate criteria hold.
- The V1 architecture rule holds at every stage: workers publish observations, state builders publish state, the executive publishes intent, skills publish actuator goals, the actuator bridge sends final commands, safety may override any stage.

```text
Stage 0  V1 memory core                      [complete]
Stage 1  Autonomous memory lifecycle         [next]
Stage 2  Cognitive integration on the bench
Stage 3  ROS 2 runtime bridge
Stage 4  Real perception
Stage 5  Expressive skills and dry-run actuation
Stage 6  Hardware bring-up (gated)
Stage 7  Lifelike presence and long-term continuity
```

---

## Stage 0 — V1 Memory Core (complete, 2026-06-12)

Everything below is implemented, tested (99 tests), and documented:

- SQLite storage with tracked, checksummed migrations.
- Salience scoring with configurable weights, promotion thresholds, explicit-remember override.
- Raw traces, episodes, facts, summaries, meta-memory, working context snapshots — writes and reads, including time-window and provenance-chain traversal (fact → episode → raw trace).
- Conservative fact conflict/supersession handling; user-confirmed outranks inferred; conflicts marked, never silently overwritten.
- Deterministic retrieval with weighted reranking, ranking explanations, speakability filtering, retrieval-history updates, warnings, and provenance summaries derived from stored links.
- One-shot deterministic consolidation (repeated-episode summaries, decay metadata).
- Local runtime event bus with kind/topic boundary validation; bounded sensory echo and working memory; attention manager v0; executive v0 (deterministic intent arbitration with safety priority).
- Simulated perception workers and YAML/JSON scenario replay.
- `MnemeMemory` facade and JSON CLI; interface drafts aligned with models under a tested contract; serialization contract and ROS integration plan documented.

See `docs/architecture/ROADMAP.md` for the detailed V1 phase record.

---

## Stage 1 — Autonomous Memory Lifecycle

Goal: the memory lifecycle (`observe → buffer → score → promote → consolidate → semanticize → retrieve → decay`) runs end-to-end without caller intervention. This is the largest functional gap today: all pieces exist, nothing connects them autonomously.

### M1.1 Automatic promotion pipeline — complete (2026-06-12)

- [x] `MemoryPromoter` subscribes to `memory_candidate` events and drives `remember_candidate` automatically: echo-only, working-memory (trace only), episode, or episode-plus-semantic-candidate per the salience decision.
- [x] Scenario replay produces durable traces/episodes with no manual storage calls.
- [x] Promotion decisions are published as `memory_lifecycle` runtime events for observability.
- [x] Exit: a replayed scenario yields the documented storage outcomes deterministically; promotion is covered by replay tests (`tests/test_promotion.py`). See `docs/memory/PROMOTION.md`.

### M1.2 Fact extraction (semanticization) — complete (2026-06-12)

- [x] Deterministic extraction of semantic facts from structured episode context (`statements` entries; no LLM), triggered automatically by semantic-candidate promotions.
- [x] Extracted facts enter through the existing conflict-aware path as `model_inferred` with capped confidence, never as confirmed.
- [x] Exit: extracted facts carry full provenance chains; conflict precedence against user-confirmed facts proven under tests (`tests/test_fact_extraction.py`). See `docs/memory/EXTRACTION.md`. Extraction from consolidation summaries remains a future increment.

### M1.3 Consolidation daemon — complete (2026-06-12)

- [x] Schedulable, replay-testable consolidation wrapper over the one-shot pass: minimum-interval scheduling policy, batch limits, cumulative stats, and `memory_lifecycle` progress events.
- [x] Exit: repeated invocations are idempotent; daemon behavior fully testable without threads (`tests/test_consolidation_daemon.py`). Idle-detection triggers deferred to Stage 2 (needs executive/world-model integration). See `docs/memory/CONSOLIDATION.md`.

### M1.4 Forgetting and decay policy — complete (2026-06-12)

- [x] Retrieval-time downranking from decay metadata (`score × (1 − penalty)`, visible in ranking explanations).
- [x] Staged forgetting: accessibility decay → suppression (`run_decay_once`, reversible, conservative criteria) → explicit purge with provenance-preserving tombstones (`purge_memory`).
- [x] User-confirmed facts never auto-suppressed; purging one requires `force=True` with a reason.
- [x] Exit: decay outcomes deterministic and explainable; purge requires explicit invocation (`tests/test_decay.py`). Detail decay (in-place summarization) and raw-trace retention remain documented future work. See `docs/memory/DECAY.md`.

### M1.5 Memory observability — complete (2026-06-12)

- [x] `memory_lifecycle` events for promotion decisions (M1.1), extraction results (M1.2), consolidation passes (M1.3), decay actions (M1.4), retrievals, and fact conflicts (engine-level, opt-in `event_bus`). Retrieval events carry IDs/counts/warnings only — never memory content.
- [x] CLI inspection commands: `inspect-provenance` (chain JSON) and `inspect-decay` (decay-bearing meta-memory).
- [x] Exit: every memory state change is traceable from the event stream alone (`tests/test_observability.py`).

**Stage 1 status: complete (2026-06-12).** The memory lifecycle (`observe → buffer → score → promote → consolidate → semanticize → retrieve → decay/suppress/purge`) runs end-to-end, deterministically, with full observability.

**Safety gate to Stage 2:** the full lifecycle runs under replay with deterministic results across three runs; no memory layer regression.

---

## Stage 2 — Cognitive Integration on the Bench

Goal: the cognition layers behave as one mind on simulated input — still no ROS, no hardware.

### M2.1 Shared world model — complete (2026-06-12)

- [x] `WorldModel` state builder fusing perception events into typed state: persons present (TTL), active speaker (TTL), last speech, ambient sound (TTL), last touch, internal/body state, safety level — published as `world_state_update` events.
- [x] Exit: world state queryable and snapshot-testable under replay (`tests/test_world_model.py`). See `docs/architecture/WORLD_MODEL.md`. Object tracking deferred to Stage 4 (real perception).

### M2.2 Working memory lifecycle v1 — complete (2026-06-12)

- [x] Context windows open/close around interactions (`ContextWindowManager`): speech/person/touch events open and extend windows, idle timeout or explicit close bounds them.
- [x] Snapshots persist at the close boundary automatically; transitions published as `world_state_update` events.
- [x] Exit: conversation-shaped replay produces correct context windows and persisted snapshots (`tests/test_context_windows.py`). Window→episode bridging noted as future work in `docs/memory/WORKING_MEMORY.md`.

### M2.3 Attention manager v1 — complete (2026-06-12)

- [x] Habituation (geometric novelty decay per exposure), inhibition-of-return (windowed priority penalty with explicit factor, safety-immune), opt-in curiosity scan targets during idle, and bounded attention state history.
- [x] Exit: attention traces over scripted scenarios match documented expectations (`tests/test_attention_v1.py`); v0 behavior preserved (existing tests unchanged). See `docs/attention/ATTENTION_MANAGER.md`.

### M2.4 Executive v1 — complete (2026-06-12)

- [x] Goal stack with safety-driven suspension and post-recovery resumption; intents carry goal context.
- [x] Response timing gate (`min_response_delay_ms`, opt-in) — LISTEN/`awaiting_turn_completion` until the turn settles.
- [x] Memory-informed RESPOND_TO_USER: retrieval with cue-token fallback, ID-only memory payloads, `needs_clarification` from conflicting-fact warnings, full bundle on `last_memory_bundle`.
- [x] Deterministic idle behavior rotation.
- [x] Exit: preemption, resumption, timing, and memory-informed behavior covered by deterministic tests (`tests/test_executive_v1.py`); v0 defaults preserved.

### M2.5 Dialogue planner v0 (intent-level) — complete (2026-06-12)

- [x] Deterministic act planner (`answer`/`clarify`/`acknowledge`/`greet` or silence) over executive intent + memory bundle, with content slots, template text, and speakability-filtered memory references; silent in safety modes.
- [x] Exit: utterance plans never reference `never_say`/`internal_only` memory (retrieval excludes them; the planner additionally drops `restricted` from spoken refs); covered by tests (`tests/test_dialogue.py`). See `docs/executive/DIALOGUE_PLANNER.md`.

### M2.6 Self model v0 and procedural memory v0 — complete (2026-06-12)

- [x] Self model: identity facts under the reserved `self` subject with deliberate in-place updates (fixed fact ID per predicate), retrieval integration, and a deterministic `describe()`.
- [x] Procedural memory: versioned skill parameters (`procedure:<skill>:<parameter>`) with explicit supersession chains, provenance notes, full queryable history, and no autonomous learning.
- [x] Exit: self-queries answerable from memory; procedural parameters versioned with provenance (`tests/test_self_model.py`). See `docs/memory/SELF_MODEL.md`.

**Stage 2 status: complete (2026-06-12).** The full bench cognition chain — perception sim → world model → context windows → attention v1 → memory → executive v1 → dialogue plan — runs deterministically under tests, with self model and procedural memory layers in place.

**Safety gate to Stage 3:** full bench stack (perception sim → world model → attention → memory → executive → dialogue plan) runs scripted scenarios deterministically in CI.

---

## Stage 3 — ROS 2 Runtime Bridge

Goal: the same behavior, over ROS 2 transport, with zero domain model changes. Follows `docs/architecture/ROS_INTEGRATION_PLAN.md`.

### M3.1 Interface package generation

- Generate the `android_brain_interfaces` ROS package from the aligned drafts; CI checks generated package against `tests/test_interface_alignment.py` contracts.

### M3.2 Single-process memory bridge

- One `mneme_memory_node` wrapping `MnemeMemory`: `RetrieveMemory.action`, `UpsertFact.srv`, `GetWorkingContext.srv`, `ConsolidateMemory.action`. Local bus stays internal; ROS adapters only at the edge.
- Exit: replay scenarios pass through ROS services with results identical to the local-bus harness.

### M3.3 Split cognition nodes

- `working_memory_node`, `attention_manager_node`, `executive_node` as separate processes; QoS and namespace conventions encode the topic/kind boundaries.
- Exit: replay parity maintained; node restart mid-scenario degrades gracefully (no crash, documented behavior).

### M3.4 Launch, diagnostics, and replay-over-ROS

- Launch files for bench topologies; diagnostics topics for every node; rosbag-based record/replay interop with the YAML scenario format.
- Exit: one-command bench bring-up; CI runs at least one ROS-transport replay scenario.

**Safety gate to Stage 4:** replay parity between local bus and ROS transport; diagnostics prove event flow; no perception-to-actuator path exists (there are still no actuators).

---

## Stage 4 — Real Perception

Goal: replace simulated workers with real sensors behind the same topics and event shapes. Simulated workers remain forever for CI.

### M4.1 Vision worker

- Camera capture, face detection, face re-identification with confidence; person entity events compatible with the simulated face worker.
- Privacy policy: embeddings/identifiers storage rules documented; raw frames never persisted into memory.

### M4.2 Speech worker

- VAD + ASR transcript events with confidence; speaker attribution when resolvable; explicit-remember phrase detection feeding the salience flag.

### M4.3 Sound direction worker

- Microphone-array (or stereo) direction-of-arrival events for attention.

### M4.4 Touch and body-state workers

- Touch sensor events; servo temperature/load/voltage and compute health as `internal_health` events.

### M4.5 Perception fusion and calibration

- World model fusion across real modalities (vision + sound direction + speech attribution); per-sensor confidence calibration; latency budgets documented and measured.

- Exit criteria for the stage: a person walking up, greeting, and leaving produces correct world state, attention shifts, episodes, and facts — live, repeatedly, and the same pipeline still passes simulated CI. Memory provenance distinguishes `sensor_observed` correctly end-to-end.

**Safety gate to Stage 5:** sustained live perception soak runs without memory corruption or unbounded growth; privacy rules enforced in tests.

---

## Stage 5 — Expressive Skills and Dry-Run Actuation

Goal: the full behavior loop with a fake actuator backend — every motion decision testable before any real motor exists.

### M5.1 Skill controller framework

- Async skill controllers consuming executive intent and publishing `skill_goal` events: accept/reject, progress, completion, cancellation, timeout, preemption semantics.

### M5.2 Core expressive skills

- Gaze (attention-driven), blink (idle patterns + reactive), head pose (orientation toward targets), ear expression, speech output (TTS adapter behind the dialogue plan).
- Procedural memory parameters (Stage 2) drive timing/style values.

### M5.3 Actuator bridge with fake backend

- Single chokepoint for final commands: limit enforcement, rate limiting, command validation, timeout behavior, neutral-pose fallback; fake backend records command streams for assertion.

### M5.4 Safety supervisor v1

- Dedicated node: e-stop event handling, watchdog heartbeats from every stage, degraded-mode policy (which skills shut down under which failures), safe neutral pose command, override authority over all skill goals.

### M5.5 Behavior integration and social timing

- Idle presence behavior; attention-gaze coupling with natural dynamics; turn-taking timing between listening and speaking; interruption handling down through skills.

- Exit criteria: scripted live-perception scenarios produce correct, complete command streams against the fake backend; cancellation/timeout/preemption/safety-override tests pass at every layer; no module bypasses the executive or the bridge.

**Safety gate to Stage 6 (hard):** e-stop verified end-to-end in dry-run; actuator limits enforced in the bridge with tests; degraded modes proven; hardware bring-up plan with per-actuator command range, failure mode, safe default, expected feedback, timeout behavior documented per `AGENTS.md` §11.

---

## Stage 6 — Hardware Bring-Up (gated)

Goal: the bench head moves, safely. Every step here is explicitly human-supervised; nothing actuates by default.

### M6.1 Bench platform definition

- Mechanical/electrical documentation under `docs/hardware/`: actuators (neck, eyes/gaze mechanism, eyelids, ears), sensor mounts, power, wiring, physical e-stop.

### M6.2 Real actuator backend

- Servo driver backend behind the existing bridge interface; per-actuator calibration, soft limits inside hardware limits, current/temperature monitoring feeding `internal_health`.

### M6.3 Staged actuation

- One actuator at a time: dry-run stream diff against fake backend → limited-range live test → full-range live test; neutral pose and e-stop verified at each step before the next actuator.

### M6.4 Integrated live behavior

- Full loop on hardware: live perception → cognition → expressive skills → motion; long-duration supervised soak tests; thermal and duty-cycle limits enforced.

- Exit criteria: the head tracks people with gaze and head pose, blinks naturally, reacts to sound, speaks, and remembers interactions — with e-stop, neutral-pose fallback, and degraded modes demonstrated live, repeatedly.

---

## Stage 7 — Lifelike Presence and Long-Term Continuity

Goal: from a working robot head to a convincing, continuous presence. Capabilities here may use learned/model-driven components, but always behind the deterministic safety and provenance machinery.

### M7.1 Long-term identity and personalization

- Person-scoped memory: stable person entities across sessions; preference facts accumulated with provenance; greeting/recall behavior driven by retrieval ("you mentioned tea yesterday").
- Memory hygiene at scale: consolidation, decay, and contradiction review proven over weeks of accumulated memory.

### M7.2 LLM-assisted services (optional, guarded)

- LLM adapters for summarization, fact extraction proposals, and dialogue realization — each behind the same interfaces as the deterministic versions, marked `model_inferred`, never writing confirmed facts, never commanding actuators, degradable to deterministic fallbacks when offline.

### M7.3 Procedural learning (bounded)

- Slow, bounded adaptation of procedural parameters (timing, gaze dynamics) from interaction statistics, with version history, rollback, and hard parameter ranges enforced by the bridge.

### M7.4 Contradiction and review workflows

- Interactive review of conflicted facts ("did you say X or Y?"); supersession through conversation; meta-memory contradiction scores driving review priority.

### M7.5 Evaluation and presence quality

- A repeatable evaluation suite for the qualities that define the project: attention naturalness, response timing, memory continuity across sessions, expression coherence, safety behavior under injected failures.
- Long-running unattended-cognition soak (perception + memory live, actuation supervised) measured for stability.

- Exit criteria: a returning visitor is recognized, remembered, and engaged with appropriate continuity and timing; the robot can explain what it remembers and why it trusts it; every safety property still holds.

---

## Cross-Cutting Tracks (every stage)

- **Safety:** the gate criteria above are blocking. New hardware-facing behavior always documents actuators, ranges, failure modes, safe defaults, feedback, timeouts, and hardware-free test methods before code.
- **Testing:** replay fixtures grow with every capability; CI runs the full deterministic suite plus at least one end-to-end scenario per stage reached. Nothing merges red.
- **Documentation and project memory:** each milestone updates `docs/`, `implement/`, `memory/` + `MEMORY_INDEX.md` per `AGENTS.md` §16. Status documents (`REPO_STATUS.md`) stay truthful to implemented behavior.
- **Performance:** latency budgets (perception → attention < 100 ms target, executive tick rate, retrieval under conversational deadlines) get measured once real sensors exist and tracked thereafter.
- **Privacy:** person data, embeddings, and transcripts follow documented retention and speakability policy; no secrets in provenance (enforced); nothing leaves the device without explicit design.

## Explicit Non-Goals (unchanged from AGENTS.md)

Full humanoid body control, biped walking, dexterous hands, unrestricted self-modification, uncontrolled procedural learning, permanent storage of everything, emotion detection treated as truth, direct LLM-to-actuator control, cloud as a hard dependency, and hardware actuation without simulation/dry-run support.

# Mneme Master Roadmap

Date: 2026-06-12 (revision 2)
Status: Long-term implementation roadmap from the V1 memory core to the complete android head brain

This roadmap covers every implementation milestone between the current bench-only memory prototype and the end goal: a safe, debuggable, expressive, memory-centered robot head with lifelike attention, timing, memory continuity, and transparent reasoning.

**Revision 2 (2026-06-12), by owner decision:** motor/actuator work is deferred. The near-term embodiment is a *virtual head* — a cross-platform app that perceives through the host machine's camera/microphone and talks back on screen/speakers. Mneme targets **Windows, macOS, and Linux** equally (primary dev machine is an Apple Silicon Mac), so the ROS 2 bridge moved into the deferred physical-embodiment track and a cross-platform runtime replaced it. Perception must **discover attached peripherals at startup/runtime** rather than assuming configured devices. Recorded privacy decisions live in `docs/safety/MEMORY_PRIVACY.md`.

Ordering rules:

- Milestones are ordered by dependency and safety, not by excitement.
- Every stage must keep the scenario-replay regression harness green.
- Determinism first: every capability ships deterministic and testable before any learned or model-driven variant is allowed.
- Safety gates are hard boundaries — later stages do not start until the gate criteria hold.
- The V1 architecture rule holds at every stage: workers publish observations, state builders publish state, the executive publishes intent, skills publish actuator goals, the actuator bridge sends final commands, safety may override any stage.

```text
Stage 0  V1 memory core                            [complete]
Stage 1  Autonomous memory lifecycle               [complete]
Stage 2  Cognitive integration on the bench        [complete]
Stage 3  Cross-platform runtime and virtual head   [complete]
Stage 4  Real perception (camera + microphone)     [next]
Stage 5  Conversational presence
Stage 6  Physical embodiment                       [deferred: ROS, skills, actuators, hardware]
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

## Stage 3 — Cross-Platform Runtime and Virtual Head (complete, 2026-06-12)

Goal: Mneme becomes a runnable, interactive program on Windows, macOS, and Linux — one process that wires the whole Stage 0–2 stack together, discovers what the host machine offers, and presents a virtual head that can hold a (typed, then spoken) conversation. Zero domain model changes; the local event bus is the runtime transport.

### M3.1 Runtime loop

- [x] A single cross-platform runtime process (`mneme run`) constructs and wires bus + engine + world model + working memory/context windows + attention + executive + dialogue planner + promoter/extractor/consolidation daemon, drives `tick()` components on a deterministic scheduler, and shuts down cleanly by closing context windows and persisting snapshots.
- [x] Console-script entry point in `pyproject.toml`.
- [x] Exit: replay fixtures run through the runtime loop; runtime starts and stops cleanly under deterministic tests.

### M3.2 Peripheral discovery service

- [x] Startup and runtime scanning contract for cameras, microphones, and speakers publishes availability as world-state events.
- [x] Deterministic fake discovery backend for tests and CI; platform backends can implement the same interface later.
- [x] Exit: tests cover appearance, removal, and absence of devices.

### M3.3 Virtual head v0

- [x] Minimal terminal front end: typed user input becomes `speech_transcript` perception events; Mneme's utterance plans render as text.
- [x] JSON scripted mode supports deterministic replay/debug.
- [x] Exit: a typed conversation can be remembered and answered from memory in the runtime loop.

### M3.4 Cross-platform CI and packaging

- [x] CI matrix runs the full suite on `ubuntu-latest`, `macos-latest`, `windows-latest`.
- [x] Package console scripts expose `mneme run` and `mneme-memory`.
- [x] Exit: documented one-command install (`pip install -e .` + `mneme run`) for Stage 3.

**Stage 3 status: complete (2026-06-12).** Mneme now has a deterministic local runtime loop and terminal virtual head. The runtime is still typed-input only; real camera/microphone perception starts in Stage 4.

**Safety gate to Stage 4:** the virtual-head loop runs deterministically under replay on all three OSes; peripheral discovery never blocks or crashes the runtime when devices are missing.

---

## Stage 4 — Real Perception (Camera + Microphone)

Goal: replace simulated workers with the host machine's real camera and microphone, behind the same event shapes, using devices found by the Stage 3 discovery service. Simulated workers remain forever for CI. Touch and body-state sensors are deferred to the physical-embodiment track (Stage 6) — a virtual head has neither.

Privacy (owner-decided, recorded in `docs/safety/MEMORY_PRIVACY.md`): raw frames **are** stored, transcripts persist, and everyone seen or heard is remembered — no enrollment gate. Storage growth therefore needs hygiene (M4.4).

### M4.1 Vision worker

- Capture from the discovered camera (cross-platform: AVFoundation/MediaFoundation/V4L2 behind one library), face detection, face re-identification with confidence; person entity events compatible with the simulated face worker.
- Raw frame archive: captured frames associated with episodes (bounded rate, e.g. keyframes at salience boundaries, not full video), with provenance.

### M4.2 Speech worker

- Local VAD + ASR (Apple Silicon friendly) producing transcript events with confidence; speaker attribution when resolvable; explicit-remember phrase detection feeding the salience flag.
- Transcripts persist into episodes per the recorded privacy decisions.

### M4.3 Perception fusion and calibration

- World model fusion across vision + speech attribution; per-sensor confidence calibration; latency budgets documented and measured. Sound direction is best-effort from available hardware (stereo) and optional — a proper mic array arrives with the physical head.

### M4.4 Storage hygiene at perception scale

- Raw-frame and transcript retention knobs (size/age caps on the frame archive, decay integration), database growth monitoring via lifecycle events, and documented bounds — because "store everything" must still fit on a disk.

- Exit criteria: a person walking up to the machine, greeting, and leaving produces correct world state, attention shifts, episodes (with frames), transcripts, and facts — live, repeatedly, on all three OSes where the hardware exists, and the same pipeline still passes simulated CI. Memory provenance distinguishes `sensor_observed` correctly end-to-end.

**Safety gate to Stage 5:** sustained live perception soak runs without memory corruption or unbounded growth; retention bounds enforced in tests.

---

## Stage 5 — Conversational Presence

Goal: the virtual head becomes a convincing conversational partner — full spoken loop, expressive on-screen behavior, and social timing, on whatever machine it runs on.

### M5.1 Speech output

- Cross-platform local TTS adapter behind the dialogue planner (utterance plans → audio out through discovered speakers); voice selection persisted as a self-model fact.

### M5.2 Live spoken loop

- Microphone ASR (Stage 4) → cognition → spoken reply, with the executive's response timing gate tuned against real speech endpointing; barge-in handling (user speaks while Mneme talks → interruption through the executive).

### M5.3 Expressive virtual avatar

- The on-screen head visualizes attention (gaze direction toward the active target), blink/idle behaviors from the executive's idle rotation, listening/speaking/thinking states, and safety states. Procedural memory parameters drive timing/style values.

### M5.4 Virtual skill controllers

- The skill-controller framework (accept/reject, progress, cancellation, timeout, preemption semantics) implemented against *virtual* skills (speak, express, gaze-on-screen) publishing `skill_goal`/`skill_status` events — the same contracts physical skills will use later, proven without motors.

### M5.5 Social timing integration

- Turn-taking between listening and speaking; interruption handling down through virtual skills; idle presence that feels attentive rather than frozen.

- Exit criteria: a walk-up spoken conversation works end-to-end — Mneme listens, looks (on screen), remembers, answers from memory, and can be interrupted — repeatedly, with the full suite still green.

**Gate to Stage 7:** sustained daily-driver use of the virtual head without memory corruption, unbounded growth, or stuck states.

---

## Stage 6 — Physical Embodiment (deferred)

Deferred by owner decision (2026-06-12) until the virtual head proves itself. This track collects everything motion-related from roadmap revision 1; nothing here starts without an explicit go-ahead, and all original safety gates apply unchanged.

### M6.1 ROS 2 bridge (optional transport step)

- The former Stage 3: interface package generation from the aligned drafts, `mneme_memory_node`, split cognition nodes, launch/diagnostics, replay-over-ROS parity (`docs/architecture/ROS_INTEGRATION_PLAN.md`). Linux-hosted; revisit whether ROS is still the right transport when this track resumes.

### M6.2 Actuator bridge and dry-run actuation

- The former Stage 5 hardware parts: actuator bridge chokepoint with fake backend (limits, rate limiting, validation, neutral-pose fallback), safety supervisor v1 (e-stop, watchdogs, degraded-mode policy, override authority), physical skill controllers reusing the Stage 5 virtual-skill contracts.

### M6.3 Hardware bring-up (gated, human-supervised)

- The former Stage 6 unchanged: bench platform definition under `docs/hardware/`, real servo backend with feedback, one-actuator-at-a-time staged actuation with e-stop verified at every step, integrated live behavior with thermal/duty-cycle limits.
- Adds the deferred perception hardware: microphone-array sound direction, touch sensors, servo body-state telemetry.

**Hard gate (unchanged):** e-stop end-to-end in dry-run, limits enforced in the bridge with tests, degraded modes proven, and per-actuator safety documentation per `AGENTS.md` §11 — before any live motion.

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

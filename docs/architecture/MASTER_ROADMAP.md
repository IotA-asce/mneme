# Mneme Master Roadmap

Date: 2026-06-13 (revision 5)
Status: Long-term implementation roadmap from the V1 memory core to the complete android head brain

This roadmap covers every implementation milestone between the current bench-only memory prototype and the end goal: a safe, debuggable, expressive, memory-centered robot head with lifelike attention, timing, memory continuity, and transparent reasoning.

**Revision 2 (2026-06-12), by owner decision:** motor/actuator work is deferred. The near-term embodiment is a *virtual head* — a cross-platform app that perceives through the host machine's camera/microphone and talks back on screen/speakers. Mneme targets **Windows, macOS, and Linux** equally (primary dev machine is an Apple Silicon Mac), so the ROS 2 bridge moved into the deferred physical-embodiment track and a cross-platform runtime replaced it. Perception must **discover attached peripherals at startup/runtime** rather than assuming configured devices. Recorded privacy decisions live in `docs/safety/MEMORY_PRIVACY.md`.

**Revision 4 (2026-06-13), by owner decision:** the next active stage is **Stage 6 — Local Living Lab**, not physical embodiment. Mneme should become useful as a daily local brain loop on the current computer first: microphone, speaker, camera, local models, memory, attention, virtual presence, and evaluation. Physical motors, GPIO, serial, PWM, ROS control, and actuator hardware remain deferred until the brain loop is stable.

**Revision 5 (2026-06-13), by owner decision:** the post-Stage 6 trajectory is now documented as a cognitive capability roadmap: local model integration first, then benchmarked capability growth against an explicit animal-reference ladder, with physical embodiment deferred until the brain loop passes a readiness gate. See `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md`.

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
Stage 4  Real perception (camera + microphone)     [complete]
Stage 5  Conversational presence                   [complete]
Stage 6  Local Living Lab                          [foundation implemented; opt-in live validation next]
Stage 7  Local cognitive model + evaluation        [planned]
Stage 8  Physical embodiment                       [deferred: ROS, skills, actuators, hardware]
Stage 9  Lifelike embodied continuity              [planned]
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

Goal: replace simulated workers with the host machine's real camera and microphone, behind the same event shapes, using devices found by the Stage 3 discovery service. Simulated workers remain forever for CI. Touch and body-state sensors are deferred to the physical-embodiment track (Stage 8) — a virtual head has neither.

Privacy (owner-decided, recorded in `docs/safety/MEMORY_PRIVACY.md`): raw frames **are** stored, transcripts persist, and everyone seen or heard is remembered — no enrollment gate. Storage growth therefore needs hygiene (M4.4).

### M4.0 Real peripheral inventory — complete (2026-06-12)

- [x] `RealPeripheralBackend` inventories host cameras, microphones, and speakers through best-effort OS commands without opening sensors.
- [x] `mneme run --device-backend real` exposes real inventory while fake discovery remains the deterministic default.
- [x] Missing tools, unsupported platforms, malformed output, and command failures produce partial or empty inventories rather than runtime failure.
- [x] Exit: injected platform-output tests cover macOS, Linux, and Windows parsing (`tests/test_real_peripherals.py`). Live capture remains unimplemented.

### M4.1 Vision worker

- [x] `LiveVisionWorker` selects discovered cameras and captures bounded keyframes through a configured local command adapter or deterministic scripted backend.
- [x] Face/person detections supplied by command JSON or sidecar metadata are published as `person_seen` events compatible with the simulated face worker.
- [x] Raw frame archive stores keyframes with provenance, confidence, hash, path, and source device metadata; no continuous video is stored.

### M4.2 Speech worker

- [x] `LiveSpeechWorker` selects discovered microphones and accepts local speech transcripts through a configured command adapter or deterministic scripted backend.
- [x] Transcript events carry confidence, speaker attribution when provided, and explicit-remember phrase detection feeding the salience flag.
- [x] Transcripts persist as raw traces and produce memory candidates; structured remember phrases enter semantic extraction.

### M4.3 Perception fusion and calibration

- [x] `PerceptionFusionCalibrator` publishes speaker/person match diagnostics with latency and confidence when recent vision and speech observations align.
- [x] Existing world model consumes the same `person_seen` and `speech_transcript` event shapes used by simulated workers.
- [x] Sound direction remains best-effort/optional; a proper mic array arrives with the physical head.

### M4.4 Storage hygiene at perception scale

- [x] `PerceptionRetentionPolicy` enforces size, count, and age caps on the frame archive.
- [x] Frame/transcript storage emits `memory_lifecycle` events for traceability.
- [x] Retention knobs are documented and recorded in `config/memory.yaml`; transcript purge remains explicit rather than automatic.

**Stage 4 status: complete (2026-06-12).** Mneme now supports live perception through repo-owned worker contracts and local command adapters, while keeping scripted backends for CI. The base package intentionally does not bundle OpenCV, face models, VAD, or ASR engines; those can be plugged in behind the command/backend contracts without changing cognition layers.

Exit criteria met for the local architecture: vision/speech observations update world state, attention, memory promotion, fact extraction, and provenance under deterministic tests. Hardware-specific quality still depends on the configured local tools and host permissions.

**Safety gate to Stage 5:** sustained live perception soak runs without memory corruption or unbounded growth; retention bounds enforced in tests.

---

## Stage 5 — Conversational Presence (complete, 2026-06-13)

Goal: the virtual head becomes a convincing conversational partner — full spoken loop, expressive on-screen behavior, and social timing, on whatever machine it runs on.

### M5.1 Speech output

- [x] Dialogue plans become virtual `speech` skill goals.
- [x] Simulated speech backend records output deterministically for JSON/replay use.
- [x] Optional local TTS command adapter supports `{text}`, `{voice}`, and `{device_id}` placeholders without bundling a speech engine.
- [x] Voice selection is persisted as procedural memory under the `speech` skill and reused by later runs.

### M5.2 Live spoken loop

- [x] Stage 4 speech-transcript events and typed input enter the same cognition path.
- [x] Runtime responses flow through executive intent, dialogue planning, virtual speech goals, and skill status events.
- [x] Barge-in handling preempts active virtual speech when user speech arrives while Mneme is speaking.
- [x] Real endpointing quality remains dependent on the configured local ASR adapter.

### M5.3 Expressive virtual avatar

- [x] `VirtualAvatarController` tracks attention target, listening/thinking/speaking/idle/safety mode, blink pattern, expression, mouth state, and last skill status.
- [x] Avatar state is JSON-friendly and exposed in the runtime snapshot for terminal demos and future GUI rendering.
- [x] Graphical rendering is intentionally not implemented yet; Stage 5 owns the state contract.

### M5.4 Virtual skill controllers

- [x] `VirtualSkillRunner` accepts virtual speech, gaze, and idle-presence goals.
- [x] Virtual skills publish accepted, running, completed, failed, preempted, and canceled statuses.
- [x] Cancellation/preemption works through event contracts and is used for barge-in and safety events.
- [x] No hardware command path exists in this stage.

### M5.5 Social timing integration

- [x] Turn-taking flows from perception/working memory through executive/dialogue to virtual speech.
- [x] Duplicate response intents do not duplicate spoken output.
- [x] Completion returns avatar state to listening; safety events cancel active virtual skills.
- [x] Idle and gaze goals remain virtual status events, ready for future GUI/physical skill consumers.

Exit criteria met for the repository-owned architecture: a local interaction can be typed or supplied by a Stage 4 transcript adapter, remembered, answered from memory, routed through virtual speech and avatar state, and interrupted through deterministic virtual skill preemption. At Stage 5 completion, native ASR/TTS engines and graphical avatar rendering were intentionally deferred to Stage 6.

**Stage 5 status: complete (2026-06-13).** Conversational presence is implemented as virtual state and local command adapters. Physical embodiment remains deferred behind the Local Living Lab.

**Gate to Stage 6:** local optional backends remain dependency-isolated, fake/model tests stay deterministic, and the base install remains lightweight.

---

## Stage 6 — Local Living Lab

Goal: make Mneme usable every day on the current computer before physical embodiment. This stage keeps the architecture brain-first and local-first: optional microphone/speaker/camera/model backends feed the same runtime events, memory, attention, executive, dialogue, and virtual skill contracts that already exist.

The base install remains lightweight. Local media and model packages are optional extras, and tests use fakes rather than real devices/models.

### M6A Native local speech loop — foundation implemented (2026-06-13)

- [x] Optional extras are declared for local audio, VAD, ASR, TTS, local-speech bundles, vision, and local-lab bundles.
- [x] `SoundDeviceMicrophoneRecorder` records bounded local WAV segments through optional `sounddevice`/`numpy`.
- [x] `WebRtcVadEndpointDetector` wraps optional WebRTC VAD with deterministic fake-device tests.
- [x] `FasterWhisperSpeechRecognitionBackend` implements microphone → local ASR → `speech_transcript` observation behind the existing speech worker contract.
- [x] `KokoroSpeechOutputBackend` implements local TTS behind the existing speech-output backend contract, with the existing simulated and command backends preserved.
- [x] `mneme run --profile local-speech` wires native ASR/TTS defaults while keeping command adapters and JSON mode working.
- [x] Missing optional dependencies, capture errors, no transcript, ASR failures, and TTS failures surface as explicit worker/skill failures rather than hidden success.
- [x] Barge-in behavior still preempts active virtual speech through the Stage 5 virtual skill coordinator.

Manual real-device validation and latency tuning remain local runbook work; CI does not install or run real ASR/TTS models.

### M6B Local model management — foundation implemented (2026-06-13)

- [x] Model files live under `.local/models/` and are not tracked by git.
- [x] `config/models.yaml` records model IDs, backend, path, license notes, source URL, checksum if known, and enabled profiles.
- [x] `mneme models list`, `mneme models verify`, and guarded `mneme models download` commands are available.
- [x] Downloads are disabled unless a registry entry explicitly documents a URL; tests use fake model records.

### M6C Native camera and person presence — foundation implemented (2026-06-13)

- [x] Optional `vision-local` dependencies are declared for OpenCV capture and MediaPipe face detection.
- [x] `OpenCVCameraCaptureBackend` captures bounded local camera frames behind the existing live-vision worker contract.
- [x] `MediaPipeFaceDetectionBackend` emits anonymous session person observations with bounding boxes, keypoints, confidence, and an attention-facing signal.
- [x] Identity recognition is intentionally absent: no unrestricted face recognition, no embeddings, and no emotion-as-truth behavior.
- [x] `mneme run --profile local-vision` and `mneme run --camera-backend opencv --face-backend mediapipe` can opt into native vision.

Manual camera permission checks and real MediaPipe model validation remain local runbook work.

### M6D Graphical virtual head UI — foundation implemented (2026-06-13)

- [x] `mneme ui` starts a stdlib-served local browser UI.
- [x] The UI reads runtime snapshot state: avatar mode, gaze target, mouth/speaking state, blink pattern, recent response, and raw debug JSON.
- [x] The UI can submit typed user input back into the runtime.
- [x] Cognition remains owned by the runtime; the UI only visualizes state and sends user-input events.
- [x] Terminal and JSON runtime modes remain supported.

This is a lightweight local dashboard, not a polished avatar renderer.

### M6E Evolving brain evaluation — foundation implemented (2026-06-13)

- [x] `EvaluationLogger` appends local JSONL daily-driver metrics.
- [x] Metrics include response generation, memory recall signal, skill-status count, safety-event count, and barge-in count.
- [x] `mneme eval summarize` summarizes local evaluation logs.
- [x] Runtime `--evaluation-log` records scripted or interactive turns without changing cognition.

Future work: redaction workflows, replayable soak scenarios from real logs, response-latency histograms, contradiction/correction metrics, repeated-visitor continuity scoring, and bounded procedural adaptation.

**Stage 6 status: foundation implemented (2026-06-13).** The native local speech/vision/model/UI/evaluation seams exist behind optional dependencies and are tested with fakes. The next work is real local validation on the current computer: permissions, model placement, latency, quality, and daily-driver logs.

**Gate to Stage 7:** a sustained local-speech/local-vision daily-driver run should show no memory corruption, no duplicate spoken responses per user turn, bounded latency, explicit failures, and useful evaluation logs.

---

## Stage 7 — Local Cognitive Model and Evolving Brain Evaluation

Goal: connect local AI models as bounded cognitive tools, then evaluate whether Mneme's local brain loop improves in continuity, memory, social timing, and reasoning before any physical embodiment. Capabilities here may use learned/model-driven components, but always behind deterministic safety, provenance, replay, and rollback.

The comprehensive implementation reference for this stage is `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md`. It defines:

- the local model runtime adapter path,
- cognitive context construction,
- model-backed dialogue realization with deterministic fallback,
- benchmark fixtures and capability scoring,
- an animal-reference capability ladder,
- the long-term human-brain-equivalent functional target,
- the physical embodiment readiness gate.

### M7.0 Local cognitive model layer

- Model runtime adapters for local backends such as Ollama and OpenAI-compatible local servers.
- Compact cognitive context builder from working memory, attention, safety, and retrieved memory.
- Model dialogue realizer behind the existing deterministic planner.
- UI/CLI status surfaces showing whether the model is connected, which memory refs were used, and whether deterministic fallback was used.

### M7.1 Daily-driver metrics

- Response latency, interruption handling, memory recall success, contradiction rate, repeated visitor continuity, user correction rate, and stuck-state count.
- Private-content redaction before logs become replay fixtures.

### M7.2 Soak replay

- Replayable scenarios generated from real logs after redaction.
- Regression checks for duplicate responses, forgotten confirmations, stale attention, stuck listening/speaking states, and memory overgrowth.

### M7.3 Bounded procedural adaptation

- Adapt timing, gaze dwell, response delay, salience thresholds, and retrieval preferences only within documented ranges.
- Learned/model-generated memory remains `model_inferred` unless confirmed by the user.
- Every parameter update carries provenance, version history, and rollback.

### M7.4 Local model improvements

- Improve ASR/VAD/TTS/vision model choices only after license/source checks.
- Keep cloud models optional, never hard requirements.

### M7.5 Continuity and review workflows

- Person-scoped continuity through anonymous session IDs, user-confirmed labels, and speaker/person fusion before face embeddings.
- Interactive review of conflicted facts and user corrections.

Exit criteria: Mneme can be used locally over repeated sessions, explain what it remembers and why it trusts it, recover from interruptions, avoid stuck states, and produce useful evaluation traces.

---

## Stage 8 — Physical Embodiment (deferred)

Deferred by owner decision until the Local Living Lab proves itself. This track collects everything motion-related from earlier roadmap revisions; nothing here starts without an explicit go-ahead, and all original safety gates apply unchanged.

### M8.1 ROS 2 bridge (optional transport step)

- Interface package generation from the aligned drafts, `mneme_memory_node`, split cognition nodes, launch/diagnostics, replay-over-ROS parity (`docs/architecture/ROS_INTEGRATION_PLAN.md`). Linux-hosted; revisit whether ROS is still the right transport when this track resumes.

### M8.2 Actuator bridge and dry-run actuation

- Actuator bridge chokepoint with fake backend (limits, rate limiting, validation, neutral-pose fallback), safety supervisor v1 (e-stop, watchdogs, degraded-mode policy, override authority), physical skill controllers reusing the virtual-skill contracts.

### M8.3 Hardware bring-up (gated, human-supervised)

- Bench platform definition under `docs/hardware/`, real servo backend with feedback, one-actuator-at-a-time staged actuation with e-stop verified at every step, integrated live behavior with thermal/duty-cycle limits.
- Adds deferred physical sensors: microphone-array sound direction, touch sensors, and servo body-state telemetry.

**Hard gate:** e-stop end-to-end in dry-run, limits enforced in the bridge with tests, degraded modes proven, and per-actuator safety documentation per `AGENTS.md` §11 before any live motion.

---

## Stage 9 — Lifelike Embodied Continuity

Goal: from a working local brain and safe robot head to a convincing, continuous embodied presence. Stage 9 depends on Stage 7 evaluation and Stage 8 hardware safety.

---

## Cross-Cutting Tracks (every stage)

- **Safety:** the gate criteria above are blocking. New hardware-facing behavior always documents actuators, ranges, failure modes, safe defaults, feedback, timeouts, and hardware-free test methods before code.
- **Testing:** replay fixtures grow with every capability; CI runs the full deterministic suite plus at least one end-to-end scenario per stage reached. Nothing merges red.
- **Documentation and project memory:** each milestone updates `docs/`, `implement/`, `memory/` + `MEMORY_INDEX.md` per `AGENTS.md` §16. Status documents (`REPO_STATUS.md`) stay truthful to implemented behavior.
- **Performance:** latency budgets (perception → attention < 100 ms target, executive tick rate, retrieval under conversational deadlines) get measured once real sensors exist and tracked thereafter.
- **Privacy:** person data, embeddings, and transcripts follow documented retention and speakability policy; no secrets in provenance (enforced); nothing leaves the device without explicit design.

## Explicit Non-Goals (unchanged from AGENTS.md)

Full humanoid body control, biped walking, dexterous hands, unrestricted self-modification, uncontrolled procedural learning, permanent storage of everything, emotion detection treated as truth, direct LLM-to-actuator control, cloud as a hard dependency, and hardware actuation without simulation/dry-run support.

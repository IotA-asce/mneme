# Mneme Documentation

The map of all documentation in this repository. Keep it current: whenever a
doc is **added, moved, or retired**, update the matching line here (see
`AGENTS.md` §6). Naming and directory conventions live in `AGENTS.md` §5–8.

**Start here:** [`../README.md`](../README.md) (project overview) →
[`vision/BRAIN_FINAL_STATE.md`](vision/BRAIN_FINAL_STATE.md) (the north-star end state) →
[`DESIGN_DOCUMENT.md`](DESIGN_DOCUMENT.md) (the current design & architecture) →
[`architecture/MASTER_ROADMAP.md`](architecture/MASTER_ROADMAP.md) (where the work is going) →
[`status/REPO_STATUS.md`](status/REPO_STATUS.md) (what actually works today).

---

## Top level

| Doc | Purpose |
|-----|---------|
| [`DESIGN_DOCUMENT.md`](DESIGN_DOCUMENT.md) | Comprehensive design reference: vision, architecture philosophy, memory layers, lifecycle, retrieval, provenance, testing. The canonical design source. |

## `vision/` — north-star end state (aspirational, forward-looking)

| Doc | Purpose |
|-----|---------|
| [`BRAIN_FINAL_STATE.md`](vision/BRAIN_FINAL_STATE.md) | Detailed specification of the finished brain: sensory + cognitive + motor capabilities and the requirements they satisfy, with architecture diagrams. |
| [`ANDROID_VISION_STORY.md`](vision/ANDROID_VISION_STORY.md) | Narrative "day in the life" of a future android running Mneme, mapping each story beat to a real capability, with diagrams. |

## `architecture/` — system architecture, roadmaps, contracts

| Doc | Purpose |
|-----|---------|
| [`PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md) | Factual map of the repository layout and where new work belongs. |
| [`MASTER_ROADMAP.md`](architecture/MASTER_ROADMAP.md) | **Canonical** long-term roadmap, Stages 0–9. |
| [`ROADMAP.md`](architecture/ROADMAP.md) | Completed V1 memory-prototype phase record (subset of the master). |
| [`COGNITIVE_CAPABILITY_ROADMAP.md`](architecture/COGNITIVE_CAPABILITY_ROADMAP.md) | Stage 7+ local-model integration and the animal-reference capability ladder. |
| [`IMPLEMENTATION_PLAN.md`](architecture/IMPLEMENTATION_PLAN.md) | *Historical.* Original V1 Phase 0–6 build plan; superseded by the roadmaps. |
| [`NODE_ARCHITECTURE.md`](architecture/NODE_ARCHITECTURE.md) | Future ROS node graph (overview; detail in the ROS plan). |
| [`ROS_INTEGRATION_PLAN.md`](architecture/ROS_INTEGRATION_PLAN.md) | Module→node boundary mapping and phased launch plan (deferred track). |
| [`RUNTIME.md`](architecture/RUNTIME.md) | Local in-process runtime event layer / event model. |
| [`SERIALIZATION.md`](architecture/SERIALIZATION.md) | JSON wire/serialization contract. |
| [`WORLD_MODEL.md`](architecture/WORLD_MODEL.md) | Shared world-state builder (deterministic, Stage 2). |

## `memory/` — memory subsystem reference

| Doc | Purpose |
|-----|---------|
| [`MODELS.md`](memory/MODELS.md) | Memory domain models (candidates, episodes, facts, bundles, meta-memory). |
| [`STORAGE.md`](memory/STORAGE.md) | SQLite storage schema and access. |
| [`SALIENCE.md`](memory/SALIENCE.md) | Salience scoring factors, weights, thresholds. |
| [`PROMOTION.md`](memory/PROMOTION.md) | Automatic promotion from candidate to trace/episode/fact. |
| [`EXTRACTION.md`](memory/EXTRACTION.md) | Deterministic fact extraction (semanticization). |
| [`RETRIEVAL.md`](memory/RETRIEVAL.md) | Cue-based retrieval, reranking, ranking explanations. |
| [`CONSOLIDATION.md`](memory/CONSOLIDATION.md) | Deterministic consolidation / summaries. |
| [`DECAY.md`](memory/DECAY.md) | Forgetting: accessibility decay, suppression, purge. |
| [`CONFLICTS.md`](memory/CONFLICTS.md) | Semantic-fact conflict and supersession handling. |
| [`PROVENANCE.md`](memory/PROVENANCE.md) | Provenance chains and meta-memory fields. |
| [`WORKING_MEMORY.md`](memory/WORKING_MEMORY.md) | Sensory echo and working-memory/context-window lifecycle. |
| [`SELF_MODEL.md`](memory/SELF_MODEL.md) | Self model and procedural (skill-parameter) memory. |
| [`MEMORY_REVIEW.md`](memory/MEMORY_REVIEW.md) | Supervised memory-review loop (apply/reject conflicted facts). |

## `attention/` · `executive/` · `safety/`

| Doc | Purpose |
|-----|---------|
| [`attention/ATTENTION_MANAGER.md`](attention/ATTENTION_MANAGER.md) | Attention manager (novelty/habituation, inhibition-of-return, curiosity). |
| [`executive/EXECUTIVE_V0.md`](executive/EXECUTIVE_V0.md) | Executive intent arbitration (v0/v1). |
| [`executive/DIALOGUE_PLANNER.md`](executive/DIALOGUE_PLANNER.md) | Deterministic dialogue act planning with speakability filtering. |
| [`safety/MEMORY_PRIVACY.md`](safety/MEMORY_PRIVACY.md) | Recorded privacy decisions (retention, speakability, no-secrets). |

## `runbooks/` — operational & debugging procedures

| Doc | Purpose |
|-----|---------|
| [`DEVELOPMENT.md`](runbooks/DEVELOPMENT.md) | Dev setup, running tests, common workflows. |
| [`MEMORY_CLI.md`](runbooks/MEMORY_CLI.md) | Using the memory CLI and inspection commands. |
| [`SCENARIO_REPLAY.md`](runbooks/SCENARIO_REPLAY.md) | Running deterministic scenario replay fixtures. |
| [`VIRTUAL_HEAD.md`](runbooks/VIRTUAL_HEAD.md) | Stage 3 terminal virtual-head runtime. |
| [`LOCAL_LIVING_LAB.md`](runbooks/LOCAL_LIVING_LAB.md) | Running Mneme as a daily local brain loop. |
| [`LIVE_PERCEPTION.md`](runbooks/LIVE_PERCEPTION.md) | Live camera/microphone perception workers. |
| [`REAL_DEVICE_DISCOVERY.md`](runbooks/REAL_DEVICE_DISCOVERY.md) | Discovering host cameras/mics/speakers. |
| [`LOCAL_MODELS.md`](runbooks/LOCAL_MODELS.md) | Managing local model **files/assets** and the registry. |
| [`LOCAL_COGNITIVE_MODELS.md`](runbooks/LOCAL_COGNITIVE_MODELS.md) | **Using** a local Ollama model as a bounded wording layer. |
| [`CONVERSATIONAL_PRESENCE.md`](runbooks/CONVERSATIONAL_PRESENCE.md) | Spoken loop, avatar state, turn-taking. |
| [`COGNITIVE_BENCHMARKS.md`](runbooks/COGNITIVE_BENCHMARKS.md) | Fixture-based cognitive benchmark suite. |
| [`STAGE_PREREQUISITES.md`](runbooks/STAGE_PREREQUISITES.md) | Prerequisites gating Stages 3→8. |

## `status/` — dated snapshots (point-in-time, not living reference)

| Doc | Purpose |
|-----|---------|
| [`REPO_STATUS.md`](status/REPO_STATUS.md) | Capability audit: what the repo actually implements today. |
| [`LIVE_LAB_STATUS_REPORT.md`](status/LIVE_LAB_STATUS_REPORT.md) | Report from the first live camera/mic/speaker run and behavior gaps. |

## `adr/` — architecture decision records

| Doc | Purpose |
|-----|---------|
| [`0001-memory-first-v1.md`](adr/0001-memory-first-v1.md) | Decision to build the memory subsystem first, hardware/ROS-free. |

## `assets/` — diagrams & images

| Asset | Purpose |
|-------|---------|
| [`architecture_overview.mmd`](assets/architecture_overview.mmd) | Mermaid source for the end-to-end architecture flow. |
| `memory_system_architecture.png` | Rendered memory-system architecture diagram. |
| `executive_skills_safety_architecture.png` | Rendered executive/skills/safety architecture diagram. |

---

## Related, outside `docs/`

- [`../AGENTS.md`](../AGENTS.md) — authoritative contributor/agent ruleset and doc conventions.
- [`../PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md) — concise project orientation brief.
- [`../memory/MEMORY_INDEX.md`](../memory/MEMORY_INDEX.md) — index of durable project-memory entries (completed work, decisions, investigations).
- `../implement/` — active implementation planning workspace (`<topic>/CORE_IDEA|IMPLEMENT|RULES.md`).

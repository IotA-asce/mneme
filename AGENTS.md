# AGENTS.md

Guidance for Codex and any coding assistant working in this repository.

Project: **Mneme**
Tagline: **A memory-centered cognition engine for lifelike androids.**

Mneme is an experimental android cognition architecture for building a lifelike robot head. The system is designed around parallel perception, attention, human-like memory, executive reasoning, coordinated sensory-motor behavior, and strict safety boundaries.

This repository is not just an application. It is the long-term design and implementation record for an embodied cognition system.

---

# 1. Core project mission

Mneme aims to become the software brain for a small-scale android robot head.

The first target is a bench-mounted expressive robot head that can:

1. perceive people, speech, sound direction, touch, and body state,
2. maintain a structured world model,
3. manage attention,
4. remember context and important experiences,
5. retrieve relevant memory,
6. plan responses and actions,
7. drive expressive skills such as gaze, blinking, head pose, ears, and speech,
8. remain safe under failures, uncertainty, and partial system availability.

The long-term inspiration is a Vivy-like android presence: lifelike attention, continuity, memory, expression, and social timing.

Do not optimize for flashy demos at the cost of architecture, safety, or maintainability.

---

# 2. Current development stage

This repository is currently in early architecture and prototype phase.

Assume that many systems are incomplete, simulated, or stubbed.

Prefer clear scaffolding, testable boundaries, and durable design notes over premature complexity.

When adding new code, keep it compatible with future ROS 2 integration, but do not introduce unnecessary ROS complexity before the local prototype needs it.

---

# 3. Prime directive

The robot must remain understandable, debuggable, and safe.

The system must preserve separation between:

* perception,
* world state,
* attention,
* memory,
* executive intent,
* skill goals,
* final actuator commands,
* safety override.

Do not blur these layers for convenience.

The most important architectural rule is:

> Workers publish observations.
> State builders publish state.
> The executive publishes intent.
> Skills publish actuator goals.
> The actuator bridge sends final commands.
> Safety may override any stage.

---

# 4. Repository ownership and modification boundaries

This repository owns the Mneme cognition stack.

You may modify files in this repository when the task requires it.

Do not modify files outside this repository unless explicitly instructed by the user.

If external repos, generated assets, hardware firmware, or local machine configuration are referenced, treat them as read-only context unless the user clearly asks for changes there.

Do not assume connected hardware is safe to actuate.

Do not issue real motor, servo, GPIO, serial, firmware flashing, or destructive hardware commands unless the user explicitly requests it and the safety implications are clear.

---

# 5. Project structure

The repository should maintain this broad structure:

```text
docs/                  Human-readable design and architecture documentation
docs/architecture/     System architecture, node graphs, decision records
docs/memory/           Memory model, schemas, retrieval, consolidation
docs/hardware/         Hardware assumptions, actuator safety, wiring notes
docs/safety/           Safety model, failure modes, degraded behavior
docs/runbooks/         Debugging and operation procedures

implement/             Active implementation planning workspace
memory/                Durable project memory for completed work and decisions
interfaces/            Message, service, action, and API contracts
src/                   Source code
tests/                 Unit, integration, replay, and contract tests
configs/               Runtime and development configuration
scripts/               Developer scripts and utilities
tools/                 Debugging, replay, profiling, and inspection tools
assets/                Diagrams, generated architecture images, visual references
```

If these directories do not exist and the task is substantial, create them only as needed. Do not create empty architecture theater.

---

# 6. Documentation system

Documentation is part of the deliverable.

Use `docs/` for human-readable explanations of systems, decisions, and operational behavior.

Recommended documentation areas:

```text
docs/architecture/
docs/memory/
docs/perception/
docs/attention/
docs/executive/
docs/skills/
docs/safety/
docs/hardware/
docs/runbooks/
docs/decisions/
```

Good documentation should answer:

1. What does this system do?
2. Why does it exist?
3. What owns it?
4. What inputs does it consume?
5. What outputs does it publish?
6. What assumptions does it make?
7. How does it fail?
8. How can it be tested?
9. What should future contributors avoid changing casually?

Do not write vague documentation that merely repeats filenames.

---

# 7. Implementation planning system

Use `implement/` for non-trivial work.

A non-trivial task is any task that:

* changes architecture,
* introduces a new subsystem,
* changes memory behavior,
* changes safety behavior,
* changes public interfaces,
* touches multiple modules,
* modifies persistence or migrations,
* introduces hardware-facing behavior,
* changes action/skill execution,
* changes decision-making or retrieval logic.

Each non-trivial topic should get:

```text
implement/<topic-slug>/
  CORE_IDEA.md
  IMPLEMENT.md
  RULES.md
```

## CORE_IDEA.md

Should include:

* problem statement
* desired outcome
* user/project value
* affected systems
* assumptions
* constraints
* non-goals
* risks

## IMPLEMENT.md

Should include:

* phased implementation plan
* files/modules likely to change
* validation steps
* dependency order
* rollback notes
* definition of done

## RULES.md

Should include:

* architectural boundaries
* safety constraints
* testing expectations
* performance constraints
* persistence/migration rules
* anti-patterns
* what must not change

For small tasks, do not create unnecessary planning files. Instead, keep the change focused and explain verification in the final response.

---

# 8. Durable project memory

The `memory/` directory records completed work, major decisions, investigations, and architectural changes.

This is project memory, not assistant memory.

Use project memory for information future maintainers need to understand why something exists.

Recommended organization:

```text
memory/
  MEMORY_INDEX.md
  features/
  fixes/
  refactors/
  decisions/
  investigations/
  safety/
  hardware/
  experiments/
```

Each meaningful memory entry should live in its own folder:

```text
memory/<type>/<YYYY-MM-DD-slug>/
  SUMMARY.md
  CONTEXT.md
  CHANGES.md
  LINKS.md
```

Optional files:

```text
RISKS.md
FOLLOW_UP.md
ROLLBACK.md
TESTING.md
```

## Required memory index

`memory/MEMORY_INDEX.md` must list:

* title
* type
* date
* status
* path
* related docs
* related implementation plan
* short summary

No orphan memory entries.

## When memory is required

Create or update project memory for:

* architecture decisions
* completed features
* meaningful fixes
* investigations with useful conclusions
* safety-related changes
* memory schema changes
* retrieval/scoring/consolidation behavior changes
* hardware assumptions
* actuator/control decisions
* failed experiments worth remembering

Do not create memory entries for trivial typo fixes unless they reveal a larger issue.

---

# 9. Memory architecture rules

Mneme’s internal robot memory model is central to the project.

Do not reduce memory to a flat vector store or chat-history log.

The intended memory layers are:

1. sensory echo buffer
2. working memory
3. episodic memory
4. semantic memory
5. procedural memory
6. self model
7. meta-memory

The memory lifecycle is:

```text
observe -> buffer -> score -> promote -> consolidate -> semanticize -> retrieve -> decay/suppress/forget
```

Every durable memory item should preserve:

* source
* timestamp
* confidence
* provenance
* derivation path
* version history where relevant

Never silently treat an inference as a confirmed fact.

Keep these distinct:

* raw observation
* inferred belief
* user-confirmed fact
* summarized pattern
* procedural parameter
* deprecated/superseded memory

User-confirmed facts outrank inferred facts.

Contradictions should create review or supersession state, not silent overwrite.

---

# 10. Thought engine architecture rules

The thought engine is not a single giant AI process.

It should be implemented as organized parallelism:

* parallel perception workers,
* structured state builders,
* attention manager,
* memory services,
* executive arbiter,
* asynchronous skill controllers,
* actuator bridge,
* safety supervisor.

Do not let every intelligent module directly command behavior.

Do not allow worker nodes or model wrappers to bypass the executive.

Do not let the dialogue planner own the whole robot.

The executive should coordinate intent, not perform all computation itself.

---

# 11. Safety rules

Safety is not optional.

The system must support:

* emergency stop,
* safe neutral pose,
* actuator limit enforcement,
* degraded mode,
* diagnostic visibility,
* replay/debug traceability.

Hardware-facing code must be treated as high risk.

Before adding or changing hardware control logic, document:

* affected actuators,
* command range,
* failure mode,
* safe default,
* expected feedback,
* timeout behavior,
* test method without live hardware.

Never run uncontrolled motion by default.

Never assume simulated success means hardware safety.

If actuator commands are added, they must pass through a validation or actuator-bridge layer.

Do not implement direct perception-to-actuator shortcuts except for explicitly documented safety reflexes.

---

# 12. Simulation and replay rules

Prefer simulation, fake backends, replay, and dry-run modes before live hardware.

For perception, memory, executive, and skills:

* create testable input fixtures,
* record representative traces where possible,
* design replayable scenarios,
* keep debugging hooks.

For hardware-adjacent logic:

* provide a fake actuator backend,
* test command validation,
* test timeout and cancellation,
* test degraded behavior.

Any feature that cannot be tested yet must clearly state what remains unverified.

---

# 13. Coding rules

Preserve architecture unless the task explicitly requires architecture change.

Keep diffs focused.

Avoid unrelated cleanup.

Follow existing patterns before creating new abstractions.

Prefer explicit dataflow over hidden magic.

Prefer typed contracts over loose dictionaries once an interface stabilizes.

Early prototypes may use JSON payloads, but stable interfaces should move toward typed messages or schemas.

Public interfaces should be stable unless the change is intentional and documented.

Breaking changes require documentation and memory updates.

Do not introduce large dependencies casually.

For new dependencies, explain:

* why it is needed,
* what alternatives were considered,
* impact on install complexity,
* impact on runtime performance,
* whether it is required or optional.

---

# 14. Data and storage rules

For the early memory prototype, prefer simple local storage such as SQLite unless the user explicitly chooses another store.

Schema changes must be handled through migrations.

Do not manually mutate persistent files without documenting the change.

Persistent memory data should distinguish:

* episodes,
* facts,
* summaries,
* provenance,
* meta-memory,
* skill/procedural parameters.

Do not store secrets, tokens, private keys, or credentials in the repo.

Do not commit large generated artifacts unless they are intentionally part of the design record.

---

# 15. Testing and verification

Run targeted tests for the changed area first.

Add or update tests when behavior changes.

Do not claim success without stating what was verified.

If something could not be verified, say so explicitly.

For meaningful changes, verification should include one or more of:

* unit tests,
* integration tests,
* schema/migration tests,
* replay tests,
* dry-run hardware tests,
* manual inspection notes,
* lint/type checks where configured.

For memory system changes, test:

* salience scoring,
* promotion thresholds,
* retrieval ranking,
* fact insertion,
* contradiction behavior,
* provenance preservation.

For executive/skill changes, test:

* cancellation,
* timeout,
* preemption,
* safety override,
* degraded behavior.

---

# 16. Completion criteria

A trivial task is complete when:

* the change is made,
* relevant targeted verification is done or explicitly marked unverified.

A non-trivial task is complete only when:

1. implementation is done,
2. relevant verification is done,
3. documentation is updated,
4. project memory is created or updated,
5. `memory/MEMORY_INDEX.md` is updated,
6. implementation planning artifacts exist under `implement/<topic-slug>/`,
7. remaining risks or follow-ups are stated.

Do not mark non-trivial work complete until documentation and memory are handled.

---

# 17. Assistant behavior rules

Before editing:

1. inspect relevant files,
2. understand existing architecture,
3. check docs and memory,
4. state the intended plan for non-trivial work.

While editing:

* make small coherent changes,
* avoid speculative rewrites,
* preserve existing public contracts unless intentionally changing them,
* keep safety constraints visible.

After editing:

* summarize changed files,
* summarize verification,
* mention docs/memory updates,
* list unresolved risks or follow-ups.

Never say tests passed unless they were actually run.

Never imply hardware behavior is safe unless hardware-relevant checks were performed.

Never invent project facts. If unsure, inspect files or say uncertainty clearly.

---

# 18. Destructive and external operations

Do not run destructive commands unless explicitly requested.

Be careful with:

* deleting files,
* rewriting history,
* force-pushing,
* changing permissions,
* installing global packages,
* flashing firmware,
* moving large folders,
* modifying generated assets,
* clearing databases,
* running live actuator commands.

When a destructive operation is necessary, explain what will happen first.

---

# 19. Recommended first read order for assistants

When starting a fresh session, read:

1. `README.md`
2. `AGENTS.md`
3. `CLAUDE.md` if present
4. `CODEX_CONTEXT.md` if present
5. `docs/DESIGN_DOCUMENT.md`
6. `docs/architecture/`
7. `docs/memory/`
8. `memory/MEMORY_INDEX.md`
9. relevant implementation plan under `implement/`

Then summarize:

* project mission,
* current status,
* relevant constraints,
* safe next steps.

`AGENTS.md` is the canonical instruction file for this repository. If `CLAUDE.md` exists, treat it as a compatibility copy or pointer to `AGENTS.md`.

---

# 20. Project-specific non-goals for v1

Do not build these in v1 unless explicitly requested:

* full humanoid body control,
* biped walking,
* dexterous hands,
* unrestricted autonomous self-modification,
* uncontrolled procedural learning,
* permanent storage of everything,
* emotion detection treated as truth,
* direct LLM-to-actuator control,
* cloud dependency as a hard requirement,
* hardware actuation without simulation or dry-run support.

The v1 goal is a safe, debuggable, expressive, memory-centered robot head architecture.

---

# 21. Final principle

Mneme should feel alive because it has:

* attention,
* timing,
* memory continuity,
* safe expression,
* coherent action,
* and transparent reasoning.

Do not trade those away for short-term demo behavior.

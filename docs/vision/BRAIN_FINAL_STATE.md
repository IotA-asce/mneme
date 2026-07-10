# The Mneme Brain — Final-State Specification

Status: **Vision / north-star specification** (aspirational end state, not current implementation)
Related: [`../architecture/MASTER_ROADMAP.md`](../architecture/MASTER_ROADMAP.md) (how we get there) ·
[`../DESIGN_DOCUMENT.md`](../DESIGN_DOCUMENT.md) (current design) ·
[`ANDROID_VISION_STORY.md`](ANDROID_VISION_STORY.md) (what it feels like in use)

> This document describes Mneme **as it is intended to exist when complete**: a
> full software brain — sensory, cognitive, and motor — that can be dropped into
> a compatible android body and make it feel *almost alive*. It defines the
> capabilities the brain will have and the requirements it must satisfy. It is a
> target to design toward, not a claim about what runs today. For what actually
> works now, see [`../status/REPO_STATUS.md`](../status/REPO_STATUS.md).

---

## 1. What "the final state" means

The end goal is a **complete, embodiment-agnostic cognitive system** — a brain,
not a chatbot — that:

- **perceives** the world through many parallel senses,
- **attends** to what matters based on goals, salience, and safety,
- **remembers** its life the way a person does: selectively, with compression,
  provenance, and forgetting,
- **thinks** — reasons, plans, imagines, and models other minds,
- **speaks and acts** through coordinated motor skills, and
- **continues** as a stable identity across days, months, and body upgrades,

all while remaining **safe, private, observable, and explainable**, and able to
be **integrated into future androids** through a stable body-abstraction contract.

The organizing law of the whole system is unchanged from the current design:

> **Experience broadly, store narrowly, summarize aggressively, preserve the
> rare, and retrieve by context** — and let *nothing* reach a motor without
> passing through intent arbitration and safety.

---

## 2. Design axioms (invariant at every scale)

These hold in the final state exactly as they hold in V1:

1. **Organized parallelism, not a serial loop.** Many workers observe → shared
   state is built → one executive arbitrates → many skills execute.
2. **Authority chain.** Workers publish observations · state builders publish
   state · executive publishes intent · skills publish actuator goals · the
   actuator bridge sends final commands · **safety can override any stage.**
3. **Memory never directly controls motors.** It provides context; the executive
   decides.
4. **Three truths are never collapsed:** raw observation ≠ inference ≠ confirmed
   fact. Everything carries source type, confidence, and provenance.
5. **Determinism first.** Every capability ships deterministic and testable
   before any learned or model-driven variant is allowed behind it.
6. **Safety and privacy are hard boundaries,** not features to be traded off.
7. **Local-first.** The brain runs on-device; the cloud is never a hard
   dependency for core cognition.

---

## 3. The human parallel

Mneme is explicitly modeled on human cognitive architecture. Each faculty maps
to a subsystem and a rough neural analog:

| Human faculty | Mneme subsystem | Rough biological analog |
|---|---|---|
| Senses (sight, hearing, touch, balance, interoception) | Perception workers | Sensory cortices, thalamus |
| "What's out there right now" | Shared World Model | Association cortex / situational model |
| Focus & filtering | Attention Manager | Fronto-parietal attention networks, superior colliculus |
| Split-second memory | Sensory echo + Working memory | Iconic/echoic memory, prefrontal working memory |
| Life events | Episodic memory | Hippocampus → neocortical consolidation |
| Facts & knowledge | Semantic memory | Distributed neocortex |
| Skills & habits | Procedural memory | Basal ganglia, cerebellum |
| Sense of self | Self-model | Default mode network, insula |
| Knowing what you know | Meta-memory | Metacognitive prefrontal circuits |
| Deciding & planning | Executive / thought engine | Prefrontal cortex |
| Feeling states | Affect / internal state | Limbic system, amygdala, insula |
| Speaking & understanding | Language & dialogue | Broca's / Wernicke's areas |
| Moving & expressing | Skill controllers | Motor cortex, cerebellum |
| Not dying | Safety supervisor | Brainstem reflexes, protective reflex arcs |

---

## 4. Whole-brain architecture

```mermaid
flowchart TB
  subgraph BODY["Android Body — any compatible chassis"]
    direction LR
    SENS["Sensors<br/>cameras · microphones · tactile skin · IMU/balance<br/>joint encoders · thermal · power/health"]
    ACT["Actuators<br/>eyes · eyelids · brows · neck · voice<br/>arms · hands · locomotion"]
  end

  subgraph BRAIN["Mneme Brain — embodiment-agnostic"]
    direction TB
    PERC["Perception workers<br/>vision · speech · sound-source · touch<br/>prosody · proprioception · interoception"]
    WM["Shared World Model<br/>people · objects · scene · space<br/>self body-state · social frame · safety level"]
    ATT["Attention Manager<br/>salience · novelty · goals · social relevance<br/>habituation · inhibition-of-return · curiosity"]

    subgraph MEM["Memory System"]
      direction LR
      SE["Sensory<br/>echo"] --> WK["Working"]
      WK --> EP["Episodic"]
      EP --> SM["Semantic"]
      PRO["Procedural"]
      SELF["Self-model"]
      MTA["Meta-memory"]
    end

    AFF["Affect / Internal State<br/>modeled, never treated as truth"]
    EXEC["Executive / Thought Engine<br/>goal stack · planning · reasoning<br/>imagination/simulation · theory-of-mind"]
    LANG["Language & Dialogue<br/>understanding · grounding · realization"]
    SKILL["Skill Controllers<br/>gaze · expression · speech<br/>gesture · manipulation · locomotion"]
  end

  SAFE["🛑 Safety Supervisor<br/>override authority · e-stop<br/>watchdogs · degraded modes"]

  SENS --> PERC --> WM
  WM --> ATT --> EXEC
  WM --> AFF --> EXEC
  WM --> MEM
  MEM <--> EXEC
  EXEC --> LANG --> SKILL
  EXEC --> SKILL
  SKILL --> ACT

  SAFE -. overrides .-> PERC
  SAFE -. overrides .-> EXEC
  SAFE -. overrides .-> SKILL
  SAFE -. overrides .-> ACT

  classDef safety fill:#ffdede,stroke:#c0392b,color:#7b241c;
  class SAFE safety;
```

**Read it as a flow of authority:** stimuli become observations, observations
become shared state, attention narrows that state, the executive decides using
memory and affect as *advisors*, and only the executive's intent — filtered by
safety — ever becomes motion.

---

## 5. Capability catalog

Each capability below is stated with the **requirements it must satisfy** in the
final state.

### 5.1 Perception (multimodal sensing)

- **Vision:** faces, people, objects, gestures, gaze direction of others, scene
  layout, reading text, low-light robustness.
- **Audition:** speech-to-text, speaker identification, sound-source direction,
  prosody/tone, non-speech sound events (a door, a fall, a name called out).
- **Touch:** contact location, pressure, texture, and social touch (a hand on
  the shoulder) across a tactile skin.
- **Proprioception:** joint positions, pose, and motion of its own body.
- **Interoception:** internal "body state" — temperature, power/battery, motor
  strain, latency, fault signals.
- **Spatial:** where it is, where things are, and a persistent map of familiar
  places.

**Requirements:** every observation carries timestamp, source device, and
confidence; perception workers **never** command motors; discovery of available
sensors happens at runtime (any body, any sensor set); raw streams are bounded
and hygienic; missing or failed sensors degrade gracefully, never crash.

### 5.2 Attention

Selects what to focus sensor, memory, and motor resources on. Handles
**habituation** (ignoring the unchanging), **inhibition-of-return** (not
re-fixating what was just handled), **social salience** (a person speaking to it
outranks background), **goal relevance**, and **curiosity** during idle time —
but is always **safety-immune** (a hazard captures attention regardless).

**Requirements:** attention decisions are explainable and bounded; safety-related
stimuli cannot be habituated away.

### 5.3 Shared world model

A single, queryable, time-decaying picture of the present: who is here, who is
speaking, what objects and hazards exist, the social situation, its own body
state, and the current safety level.

**Requirements:** every downstream layer reads the *same* world model; state
carries validity windows (TTL) so stale beliefs expire; snapshot-testable.

### 5.4 Memory (the heart of the system)

The full seven-layer human-inspired memory, at maturity:

```mermaid
flowchart TB
  IN["Observation"] --> SE["Sensory echo<br/>seconds · mostly discarded"]
  SE --> WK["Working memory<br/>current speaker · goal · turns · references"]
  WK -->|salient| EP["Episodic<br/>time-stamped autobiographical events"]
  EP -->|repeated / important| SM["Semantic<br/>facts · preferences · relationships · knowledge"]
  WK -.tunes.-> PRO["Procedural<br/>skill parameters · habits · routines"]
  EP --> SELF["Self-model<br/>body · capabilities · limits · identity"]
  subgraph META["Meta-memory (over everything)"]
    direction LR
    M1["confidence"]; M2["source type"]; M3["provenance chain"]
    M4["retrieval history"]; M5["contradiction status"]; M6["speakability"]
  end
  SM --- META
  EP --- META
  IN -.->|"idle: consolidate · summarize · decay · forget"| CONS["Consolidation"]
  CONS --> SM
  CONS --> EP

  classDef meta fill:#eef,stroke:#446;
  class META,M1,M2,M3,M4,M5,M6 meta;
```

- **Sensory echo:** very recent raw traces, mostly never promoted.
- **Working memory:** the active context window around an interaction.
- **Episodic:** autobiographical events — first meetings, surprises, errors and
  recoveries, promises made, high-salience social moments.
- **Semantic:** generalized facts, preferences, identities, relationships, and
  world knowledge, cleaner than episodes.
- **Procedural:** how-to behavior and skill parameters (gaze timing, greeting
  routines, safe-motion profiles), versioned with provenance.
- **Self-model:** the brain's memory of its own body, capabilities, limits, and
  continuous identity.
- **Meta-memory:** memory *about* memory — confidence, source type, provenance,
  retrieval count, contradiction status, and whether something is safe to say
  aloud.

**Lifecycle:** `observe → buffer → score (salience) → promote → consolidate →
semanticize → retrieve → decay/suppress/forget`, running autonomously.

**Requirements:** selective (never "store everything forever"); provenance- and
confidence-aware; conflicts are **marked, never silently overwritten**;
user-confirmed facts outrank inferences; forgetting is staged (down-rank →
suppress → purge) and reversible until purge; retrieval is cue-based and returns
ranking explanations; **nothing marked `never_say`/`internal_only` is ever
spoken.**

### 5.5 Cognition — executive and thought engine

- **Goal management:** a goal stack with safety-driven suspension and resumption.
- **Reasoning & planning:** multi-step plans toward goals, with fallback.
- **Imagination / simulation:** internally simulating outcomes ("if I say this,
  how will they react?", "what happens if I set this cup here?") before acting.
- **Theory of mind:** modeling what others know, want, and believe — including
  what *it* has told them before.
- **Decision arbitration:** turning attention + memory + affect + goals into a
  single **intent**, with safety having final say.

**Requirements:** every intent is traceable to its inputs; memory used in a
decision is cited (IDs + provenance); the model layer may *word* a response but
may never bypass retrieval, intent, or safety; deterministic fallback exists for
every model-driven step.

### 5.6 Language and communication

Natural, grounded, continuous conversation: understanding intent and reference,
grounding replies in actual memory, phrasing according to certainty ("you told
me…" vs. "I think…" vs. "I may be wrong…"), turn-taking, barge-in handling, and
multilingual capability.

**Requirements:** utterances never reference non-speakable memory; the brain can
always explain *why* it said something and *what it remembers*.

### 5.7 Affect and internal state

A modeled emotional/affective state (comfort, curiosity, concern, social warmth,
stress from fault or overload) that colors attention, expression, and dialogue
tone — and gives the android emotional *continuity*.

**Requirements:** affect is **modeled, never treated as ground truth** about
others; detected human emotion is a cue, not a fact; affect influences behavior
but never overrides safety or fabricates memory.

### 5.8 Motor and embodiment

Coordinated skill controllers for **gaze**, **eyelids/brows/facial expression**,
**neck/head pose**, **voice/speech**, **gesture**, **manipulation** (arms/hands),
and **locomotion** — expressive, socially timed, and physically safe.

**Requirements:** all motor output passes through the **actuator bridge
chokepoint** with rate limits, range limits, validation, and neutral-pose
fallback; the same virtual-skill contracts drive both a screen avatar and
physical actuators; e-stop halts motion end-to-end.

### 5.9 Learning and adaptation

Bounded, transparent learning: it tunes timing, gaze dwell, response delay,
salience thresholds, and retrieval preferences **within documented ranges**;
learns people, preferences, and routines over time; improves skills through
versioned procedural memory.

**Requirements:** no unrestricted self-modification; learned/model-generated
memory stays `model_inferred` until user-confirmed; every parameter change
carries provenance, version history, and **rollback**.

### 5.10 Self-model, metacognition, and continuity

Knows its own body and limits ("my left hand actuator is weak in cold"), knows
what it knows and how sure it is, and maintains a **single continuous identity**
across sessions, days, and even body upgrades.

**Requirements:** identity and relationships survive restarts and hardware
changes; the brain can introspect and report its own state and confidence.

---

## 6. Cross-cutting requirements (non-functional)

| Requirement | The brain must… |
|---|---|
| **Safety** | Give a safety supervisor override authority over every layer; support e-stop, watchdogs, and degraded modes; never let memory or a model drive an actuator directly. |
| **Privacy & consent** | Keep person data, transcripts, and embeddings under documented retention and speakability policy; keep secrets out of provenance; never send data off-device without explicit design and consent. |
| **Determinism & testability** | Ship every capability with deterministic behavior and replayable scenario tests before any learned variant; keep a green regression harness at all times. |
| **Performance** | Meet conversational and reflex latency budgets (perception→attention target < 100 ms; reflex/safety faster); measured, not assumed. |
| **Observability & explainability** | Emit a traceable event for every state change; explain any decision, utterance, or memory on request. |
| **Continuity** | Persist identity, relationships, and self-model across restarts and body changes. |
| **Embodiment-agnostic integration** | Plug into any compatible body through a stable body-abstraction contract with runtime capability discovery. |
| **Resource discipline** | Run core cognition on-device with a lightweight base; heavier senses/models are optional, isolated extras. |

---

## 7. The cognitive loop

The moment-to-moment cycle every waking instant:

```mermaid
sequenceDiagram
  autonumber
  participant World
  participant Perception
  participant WorldModel as World Model
  participant Attention
  participant Memory
  participant Executive
  participant Safety
  participant Skills

  World->>Perception: raw stimuli (sight, sound, touch, body)
  Perception->>WorldModel: typed observations (+confidence, +provenance)
  WorldModel->>Attention: current situational state
  Attention->>Executive: "this is what matters now"
  Executive->>Memory: retrieve by context (who/what/goal/place)
  Memory-->>Executive: facts · episodes · confidence · provenance · warnings
  Executive->>Executive: reason · plan · simulate outcomes · model the other mind
  Safety-->>Executive: constraints (may veto or override)
  Executive->>Skills: intent (speak · gaze · gesture · move)
  Skills->>World: safe, socially-timed action
  Executive->>Memory: encode outcome (observe → score → promote)
  Note over Memory: during idle — consolidate · semanticize · decay · forget
```

---

## 8. Integration into future androids

The brain is deliberately **separate from the body**. Any compatible android
plugs in through a **Body Abstraction Layer** that discovers what sensors and
actuators the chassis offers at runtime and exposes them as normalized, typed
contracts. The same brain, memory, and identity move from a screen avatar to a
tabletop head to a full humanoid without cognition changes.

```mermaid
flowchart LR
  subgraph BRAIN["Mneme Brain (one identity, one memory)"]
    CORE["Cognition core<br/>perception · attention · memory · executive · language"]
    HAL["Body Abstraction Layer<br/>runtime capability discovery<br/>normalized sensor + actuator contracts<br/>safety chokepoint"]
    CORE <--> HAL
  end

  subgraph BODIES["Interchangeable bodies — same contracts"]
    B1["💻 Virtual head<br/>(dev / screen)"]
    B2["🗣️ Tabletop robot head<br/>(eyes · voice · neck)"]
    B3["🤖 Full humanoid<br/>(+ arms · hands · locomotion)"]
  end

  HAL <--> B1
  HAL <--> B2
  HAL <--> B3
```

**Requirement:** a body upgrade is a *hardware* event, not a *personality* event.
The android that wakes up in a new body is the same "someone."

---

## 9. Safety is the outermost layer

No matter which layer produces an action, it is filtered on the way to the world:

```mermaid
flowchart TB
  ANY["Any layer's proposed action<br/>(executive intent · skill goal · reflex)"] --> L1["Skill limits<br/>rate · range · validation"]
  L1 --> L2["Actuator bridge chokepoint<br/>single path · neutral-pose fallback"]
  L2 --> L3["Safety supervisor<br/>watchdogs · e-stop · degraded-mode policy"]
  L3 --> OUT["Physical motion in the world"]
  L3 -. "can halt or override at any time" .-> ANY

  classDef safety fill:#ffdede,stroke:#c0392b,color:#7b241c;
  class L3 safety;
```

---

## 10. Capability maturity ladder

The final state is reached by climbing an explicit ladder, benchmarked against an
animal-reference progression before claiming human-comparable function. Physical
embodiment stays gated behind a readiness gate — the brain loop must prove itself
first.

```mermaid
flowchart LR
  S0["Memory core"] --> S1["Autonomous<br/>memory lifecycle"]
  S1 --> S2["Bench cognition<br/>integration"]
  S2 --> S3["Cross-platform<br/>virtual head"]
  S3 --> S4["Real perception<br/>camera + mic"]
  S4 --> S5["Conversational<br/>presence"]
  S5 --> S6["Local living lab<br/>(daily driver)"]
  S6 --> S7["Local cognitive models<br/>+ capability ladder"]
  S7 --> GATE{"Embodiment<br/>readiness gate"}
  GATE -->|passed| S8["Physical<br/>embodiment"]
  S8 --> S9["Lifelike embodied<br/>continuity"]

  classDef gate fill:#fff3cd,stroke:#b8860b,color:#7a5c00;
  class GATE gate;
```

---

## 11. What the final brain will *never* do

Even complete, Mneme deliberately excludes:

- Unrestricted self-modification or uncontrolled procedural learning.
- Treating detected emotion as objective truth.
- Direct LLM/model-to-actuator control (a model may *word*, never *drive*).
- Permanent storage of everything, or storage without provenance.
- A hard cloud dependency for core cognition.
- Any physical actuation without simulation/dry-run and safety proof first.
- Memory that silently overwrites, or speaks what it was told to keep private.

These are not limitations to be lifted later — they are what make an
"almost-alive" android **trustworthy** enough to live alongside people.

---

*This is the destination. The path is in* [`../architecture/MASTER_ROADMAP.md`](../architecture/MASTER_ROADMAP.md)*;
the feeling of arriving is in* [`ANDROID_VISION_STORY.md`](ANDROID_VISION_STORY.md)*.*

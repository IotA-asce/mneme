# Executive v0

Executive v0 is Mneme's first deterministic intent-generation and arbitration layer. It consumes local runtime state and publishes high-level intent through `RuntimeEventKind.EXECUTIVE_INTENT`.

It does not call skills, actuators, motors, servos, GPIO, serial devices, or hardware bridges. Future skill controllers may consume executive intent and decide how to act.

## Inputs

Executive v0 can consume:

- working memory snapshots or a live `WorkingMemory` object
- attention state from `attention_update` events
- world-state updates
- safety events
- recent perception events through working memory

When attached to an `EventBus`, it subscribes to perception, world-state, attention, memory-candidate, and safety events. It deliberately does not subscribe to its own `executive_intent` events.

## Models

`ExecutiveMode` currently supports:

- `normal`
- `degraded`
- `frozen`

`ExecutiveIntent` stores:

- `intent_id`
- `intent_type`
- `mode`
- `priority`
- `created_ts`
- `source`
- `confidence`
- `reason`
- optional `target_id`
- JSON payload
- optional `preempts_intent_id`

Supported initial intent types:

- `look_at_target`
- `listen`
- `respond_to_user`
- `remember_event`
- `idle_presence`
- `freeze_motion`
- `enter_degraded_mode`

## Arbitration Rules

V0 uses a fixed rule order:

1. Critical safety state emits `freeze_motion`.
2. Degraded safety state emits `enter_degraded_mode`.
3. Fresh user dialogue emits `respond_to_user`.
4. Recent explicit memory instruction emits `remember_event`.
5. Active non-self speaker emits `listen`.
6. Current attention target emits `look_at_target`.
7. Otherwise the executive emits `idle_presence`.

If a new selected intent has higher priority than the previous selected intent, it records `preempts_intent_id`.

## Memory Instructions

Explicit memory detection is deliberately simple in V0. Phrases such as "remember", "don't forget", "note that", "save this", and "keep this in mind" can produce memory handling intent after the immediate user interaction window.

Fresh dialogue still produces `respond_to_user`; if the fresh text is a memory instruction, the intent payload includes `secondary_intents: ["remember_event"]` so a later phase can coordinate response and memory promotion.

## Runtime Boundary

The boundary is:

```text
working/attention/world/safety state -> Executive -> executive_intent
```

No gaze, speech, motion, or actuator behavior is implemented here.

## Failure Behavior

If no meaningful state exists, Executive v0 emits `idle_presence`. If safety state is present and recognized as degraded or critical, it emits the corresponding safety intent even when user interaction is active.

## Verification

Tests cover:

- active user interaction priority
- safety preemption over active interaction
- degraded-mode intent
- explicit memory instruction handling
- look/listen/idle fallback intents
- JSON serialization
- runtime publication of intent events without skill events

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

## v1 Behaviors (Stage 2 / M2.4)

Additive and deterministic; default parameters reproduce v0 exactly:

- **Goal stack**: `push_goal(goal_type, payload)` / `complete_goal(goal_id)` / `current_goal`. Normal-mode intents carry `active_goal_id`/`active_goal_type`.
- **Interruption/resumption**: safety freeze/degraded intents suspend active goals (`suspended_goal_ids` in the intent payload); the first normal-mode intent after recovery reactivates them and carries `resumed_goal` once. Goals never delay or weaken safety intents.
- **Response timing** (`min_response_delay_ms`, default 0): a user turn younger than the delay yields LISTEN with reason `awaiting_turn_completion` and `response_due_in_ms`, approximating turn-completion before speaking.
- **Memory-informed responses** (optional `engine`): RESPOND_TO_USER retrieves against the user turn (full text, then deterministic cue-token fallback, longest tokens first) and carries `payload["memory"]` with fact/episode/summary IDs, retrieval warnings, and `needs_clarification=True` when warnings report conflicting fact records. The full `MemoryBundle` stays on `executive.last_memory_bundle` for the dialogue planner — intent payloads never carry memory content.
- **Idle rotation**: IDLE_PRESENCE intents rotate `idle_behavior` through `ambient_scan` → `rest_pose` → `micro_motion`.

v1 verification (`tests/test_executive_v1.py`) covers goal context, suspend/resume across a safety freeze, the timing gate, memory-informed payloads (IDs only), the clarification flag on conflicting memory, idle rotation, and v0 default preservation.

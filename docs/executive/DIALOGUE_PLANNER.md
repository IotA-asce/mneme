# Dialogue Planner v0

Status: V1 deterministic intent-level utterance planning (Stage 2 / M2.5)

`DialoguePlanner` bridges executive intent and the future speech skill: given an intent (plus the executive's retrieved `MemoryBundle`), it produces a structured `UtterancePlan` or stays silent. No LLM, no TTS — template realization over deterministic act selection. Stage 7 may swap in LLM realization behind this same interface.

## Act Selection

| Condition | Act | Plan |
|---|---|---|
| Intent mode frozen/degraded, or listen/look/idle/freeze/degraded intents | — | `None` (silence) |
| `remember_event` intent, or respond intent with a memory-instruction secondary intent | `acknowledge` | "Noted - I will remember that." |
| Respond intent whose memory context flags `needs_clarification` | `clarify` | statement slot parsed from the conflict warning |
| Respond intent with a speakable fact in the bundle | `answer` | subject/predicate/value slots + the fact as a memory reference |
| Respond intent on a greeting turn with no memory | `greet` | greeting text |
| Respond intent with nothing to say | `acknowledge` | honest "no stored answer" text |

## Speakability

Two layers: retrieval already excludes `never_say`/`internal_only`; the planner additionally drops `restricted` facts from spoken references when a `store` is available to check meta-memory. Plans never quote memory the bundle did not provide.

## Plan Shape

`UtterancePlan`: `plan_id`, `act_type`, `created_ts`, `text`, `content_slots`, `memory_refs` (`[{memory_kind, memory_id}]`), `confidence`, `intent_id` — JSON-friendly via `to_dict()`.

## Boundaries

The planner consumes intent and never generates it; it does not own the robot, publish events, or command skills (the speech skill consumes plans in Stage 5).

## Testing

`tests/test_dialogue.py`: answer slots/refs/text, clarify on conflicts, acknowledgments, greetings, silence for safety/non-speaking intents, restricted-fact exclusion, executive integration through `last_memory_bundle`, deterministic output.

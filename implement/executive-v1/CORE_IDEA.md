# Core Idea: Executive v1 (Stage 2 / M2.4)

## Problem Statement

Executive v0 arbitrates single intents with no continuity: no goal it is working toward survives an interruption, responses fire the instant a user turn lands (no turn-completion timing), decisions never consult long-term memory, and idle is a single static intent.

## Desired Outcome

Additive v1 behaviors, deterministic and contract-preserving:

- **Goal stack**: `push_goal`/`complete_goal`/`current_goal`; normal-mode intents carry the active goal context.
- **Interruption/resumption**: safety freeze/degraded intents suspend active goals (`suspended_goal_ids` in payload); the first normal-mode intent after recovery reactivates them and carries `resumed_goal`.
- **Response timing**: opt-in `min_response_delay_ms` — within the delay after a user turn the executive LISTENs (`awaiting_turn_completion`) instead of responding, approximating turn-completion.
- **Memory-informed intents**: optional `engine`; RESPOND_TO_USER retrieves against the user turn text and carries `payload["memory"]` (IDs, warnings, provenance summary — never full content), sets `needs_clarification` when retrieval warns about conflicting fact records, and keeps the full bundle on `last_memory_bundle` for the dialogue planner (M2.5).
- **Idle behaviors**: IDLE_PRESENCE intents rotate `ambient_scan` → `rest_pose` → `micro_motion` deterministically.

## Affected Systems

- `src/android_brain_memory/executive.py`, `tests/test_executive_v1.py` (new)
- `docs/executive/EXECUTIVE_V0.md` (v1 section), roadmap/status docs

## Assumptions / Constraints

- v0 contracts preserved: `min_response_delay_ms=0` and `engine=None` defaults keep existing tests green; priorities/reasons of v0 rules unchanged.
- The executive still publishes intent only — no motor commands, no skill calls; memory enrichment is read-only retrieval.

## Non-Goals

- Dialogue content planning (M2.5).
- Multi-goal scheduling beyond a stack; learned timing (Stage 7).

## Risks

- Memory retrieval inside intent selection adds latency; bounded by `max_results=3` and bench-only operation.

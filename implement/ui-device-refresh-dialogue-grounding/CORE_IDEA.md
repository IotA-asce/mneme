# UI Device Refresh and Dialogue Grounding

## Problem

The Local Living Lab UI could show only `Auto` in camera, microphone, and speaker selectors if the first device scan returned no devices. The dialogue planner also felt canned because fallback responses did not use the current turn or retrieved episodes.

## Desired Outcome

Make the UI recover from empty discovery by allowing an explicit device rescan, and make deterministic dialogue responses more grounded in facts, episodes, provenance, and the current user utterance.

## Constraints

- Do not add cloud services, LLM calls, or new dependencies.
- Keep device discovery inventory-only: do not open cameras, record audio, or play audio.
- Preserve the existing runtime, executive, memory, and skill boundaries.
- Keep lower-level modules testable independently.

## Non-Goals

- Full natural conversation.
- Local LLM response realization.
- Real capture/playback validation.
- Graphical avatar renderer beyond the current lightweight UI.

## Risks

- OS device inventory can still return empty results if permissions, OS tools, or hardware state block discovery.
- Deterministic responses are more contextual, but still not equivalent to model-generated conversation.

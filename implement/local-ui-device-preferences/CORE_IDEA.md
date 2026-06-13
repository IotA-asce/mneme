# Local UI Device Preferences — Core Idea

Date: 2026-06-13
Status: Implemented

## Problem

The first Stage 6 browser UI loaded but felt like a raw debug page. It also could not choose the host camera, microphone, or speaker. Device choice needed to be made once in the UI and then reused by both browser and terminal runs.

## Desired Outcome

- A cleaner, minimal local UI that feels more like a present runtime surface than a JSON dump.
- Saved camera/microphone/speaker selections under `.local/runtime_preferences.json`.
- `mneme ui` can set preferences.
- `mneme run` and `mneme ui` both load saved preferences.
- Terminal runs can still override device IDs explicitly.

## Constraints

- UI must not own cognition.
- No frontend framework.
- No hardware actuation.
- Saved preferences contain only local device IDs, not secrets.
- If a saved device is unavailable, runtime falls back to the first available device of that kind.

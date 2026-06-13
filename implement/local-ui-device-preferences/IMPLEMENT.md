# Local UI Device Preferences — Implementation

Date: 2026-06-13
Status: Implemented

## Plan

1. Add a small JSON-backed runtime preference store.
2. Pass selected device IDs into live vision, live speech, and speech output.
3. Add UI device selectors and a `/devices` post route.
4. Restyle the UI with a cleaner minimal presence surface and lightweight live refresh.
5. Update README, runbook, backlog, and project memory.

## Files

- `src/android_brain_memory/runtime_preferences.py`
- `src/android_brain_memory/runtime_loop.py`
- `src/android_brain_memory/live_perception.py`
- `src/android_brain_memory/presence.py`
- `src/android_brain_memory/local_ui.py`
- `src/android_brain_memory/virtual_head.py`
- `tests/test_stage6_local_living_lab.py`

## Validation

- Focused Stage 6/local UI tests.
- Live perception and conversational presence regression tests.
- Full developer check.
- Manual local UI smoke with HTML, `/state`, and device/input post paths.

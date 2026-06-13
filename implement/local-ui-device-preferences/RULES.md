# Local UI Device Preferences — Rules

Date: 2026-06-13
Status: Active

## Runtime Boundaries

- The browser UI may submit user input and preference selections only.
- Runtime, memory, attention, executive, dialogue, and skills remain server-side.
- Device preferences influence backend selection; they do not start hardware actuation.

## Persistence

- Store preferences under `.local/runtime_preferences.json`.
- Do not commit local preference files.
- Keep values to local device IDs only.

## Fallback

- If the preferred device is unavailable, fall back to the first available device of that kind.
- Terminal override flags are one-run overrides; UI selections are persistent.

# Local UI Device Preferences

Date: 2026-06-13
Status: Complete

Improved the Stage 6 Local Living Lab UI and added saved local device preferences.

The browser UI now presents a cleaner minimal runtime surface with live state refresh, avatar state, recent response, runtime metrics, and device selectors. Camera, microphone, and speaker selections are saved to `.local/runtime_preferences.json` and are reused by later `mneme ui` and `mneme run` sessions.

Terminal runs can override saved selections with explicit device ID flags.

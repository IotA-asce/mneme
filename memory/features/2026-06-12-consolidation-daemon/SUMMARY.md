# Summary: Consolidation Daemon (Stage 1 / M1.3)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `ConsolidationDaemon` (`src/android_brain_memory/consolidation_daemon.py`): a deterministic, schedulable wrapper over the one-shot `consolidate_once` pass. `tick()` enforces a minimum interval between passes (skips counted), `run_once()` forces a pass, batch size is bounded by `ConsolidationOptions.max_episodes`, every pass publishes a `memory_lifecycle` consolidation event, and `stats` accumulates passes/skips/summary counts.

Design: no threads, timers, or sleeps — time is injected and callers drive `tick()`, so the daemon is fully replay-testable; a future runtime loop or ROS timer (Stage 3) just calls `tick()` periodically. Repeat passes over unchanged episodes update summaries rather than duplicating them (content-derived summary IDs). Idle-detection triggers deferred to Stage 2.

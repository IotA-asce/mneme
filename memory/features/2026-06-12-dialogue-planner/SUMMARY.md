# Summary: Dialogue Planner v0 (Stage 2 / M2.5)

Date: 2026-06-12
Type: Feature
Status: Complete

Added `DialoguePlanner` (`src/android_brain_memory/dialogue.py`): deterministic intent-level utterance planning. Given an executive intent and the retrieved memory bundle, it selects an act — `answer` (top speakable fact with subject/predicate/value slots and a memory reference), `clarify` (when the executive's memory context flags conflicting fact records, statement parsed from the warning), `acknowledge` (memory instructions, or honest "no stored answer"), `greet`, or silence (`None`) for safety modes and non-speaking intents. Output is a structured JSON-friendly `UtterancePlan` (act, text, slots, memory_refs, confidence, intent_id).

Speakability enforced twice: retrieval excludes never_say/internal_only; the planner additionally drops restricted facts from spoken references when a store is available. Template-based realization only — Stage 7 may swap LLM realization behind the same interface. The planner consumes intent and never generates it.

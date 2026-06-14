# Findings

- Camera frames became `person_seen` observations with high confidence.
- Attention and presence tracked the visible user.
- Faster-Whisper produced live transcripts with roughly 3.8s-4.6s latency per segment.
- Mneme generated and spoke responses.
- The deterministic dialogue planner overused memory-storage language during ordinary conversation.
- Fixed-window ASR caused responses to partial user thoughts.
- Mechanical barge-in/preemption exists, but natural turn-taking does not.
- Memory conflict clarification surfaced at socially awkward times.

These findings support the next implementation focus: turn endpointing, conversation timing, social presence, and memory-policy tuning.


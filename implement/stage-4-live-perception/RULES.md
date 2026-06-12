# Stage 4 Live Perception Rules

- Live perception is opt-in.
- Fake and scripted backends must remain available for deterministic CI.
- Camera workers may capture bounded keyframes only; no continuous video archive.
- Speech workers persist transcripts; raw audio is not stored by this phase.
- Workers publish `perception_observation` and `memory_candidate` events only.
- Workers must not call executive, skill, actuator, ROS, GPIO, serial, or hardware-control code.
- Every stored raw frame or transcript must preserve source type, confidence, source ID, derivation path, and provenance.
- Command failures, missing devices, and missing permissions must produce skipped/error reports rather than crashing the runtime.
- Native media/model dependencies require a separate explicit dependency decision.

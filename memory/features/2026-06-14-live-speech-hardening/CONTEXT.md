# Context

Stage 6 had optional local speech backends and virtual speech skills, but the repository could not prove common live-speech failure behavior without real devices. The next safe M9.1 slice was to harden observability and deterministic tests before asking the current Mac microphone, ASR model, and speaker to carry daily-driver sessions.

The implementation keeps the architecture intact:

- live speech publishes observations,
- working/world/attention/executive/dialogue process the turn,
- virtual skills publish speech statuses,
- diagnostics observe and summarize behavior.

No real hardware control, cloud dependency, or new required package was added.


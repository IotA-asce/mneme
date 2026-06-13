# M8.5 + M10.1 Memory Review Loop

## Problem

Mneme could explain memory-backed responses and create non-mutating correction or forget proposals, but those proposals were only runtime snapshot data. There was no durable review queue, explicit apply/reject workflow, or benchmark coverage proving safe memory repair.

## Desired Outcome

Mneme should make memory-backed behavior reviewable and correctable without letting the model or dialogue layer silently mutate durable memory.

## Value

This makes the local brain loop less like a stateless chatbot: it can say why it answered, queue corrections, apply user-approved changes, suppress forgotten memories, and report measurable capability evidence.

## Affected Systems

- SQLite storage and migrations
- Memory review helpers
- Turn understanding and dialogue planning
- Runtime snapshots and local UI
- `mneme review` and `mneme eval cognition`
- Cognitive capability ladder

## Constraints

- No new dependencies.
- No cloud model dependency.
- Forget means staged suppression, not purge.
- Model-generated output must not become confirmed memory.
- Confirmed-vs-confirmed conflicts stay reviewable.

# Codex Context: Android Brain Project

## Project identity

Project name: **Android Brain**

Goal: build the software brain for a small-scale android robot head. The first major subsystem is a **human-inspired memory architecture** that later integrates with perception, attention, executive reasoning, and motor skills.

## End-state vision

A lifelike android head that can:

- perceive people, speech, objects, touch, body state, and internal health
- maintain a structured world model
- focus attention based on goals, salience, social relevance, and safety
- remember important events while compressing repetition into facts, summaries, and procedures
- retrieve relevant memories during conversation and task execution
- speak and act through coordinated skill controllers
- remain safe, observable, and debuggable

## V1 scope

V1 is **memory-first and bench-first**. It does not need real robot hardware.

V1 should build:

- local SQLite memory store
- memory models
- salience scoring
- episodic encoding
- semantic fact storage
- retrieval manager
- consolidation skeleton
- provenance/confidence handling
- CLI smoke tests

## Non-goals for V1

- no physical actuator control
- no real camera/audio integration
- no full ROS 2 runtime yet
- no autonomous personality simulation
- no uncontrolled self-modifying procedural memory

## Critical architecture rules

1. Workers publish observations.
2. State builders publish state.
3. Executive publishes intent.
4. Skills publish actuator goals.
5. Actuator bridge sends final commands.
6. Safety can override everything.
7. Memory never directly controls motors.
8. Memory must preserve provenance, confidence, and source type.
9. Raw observation, inference, and confirmed fact are never treated as the same thing.

## How Codex should work in this repo

- Read `AGENTS.md` before making changes.
- Prefer small, reviewable commits/patches.
- Keep the design documents updated when architecture changes.
- Preserve V1 scope unless explicitly told to expand.
- Add tests for salience, storage, retrieval, and consolidation behavior.
- Avoid adding heavy dependencies unless justified.

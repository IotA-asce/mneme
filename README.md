# Android Brain Starter Pack

This repository is the starting point for building the **brain software** of a small-scale android robot head inspired by lifelike social androids.

The first implementation target is **not** the full body. It is a bench-first brain/memory prototype that can later connect to robot-head perception and motor systems.

## What is included

- `docs/DESIGN_DOCUMENT.md` — the comprehensive design document Codex should read first.
- `docs/IMPLEMENTATION_PLAN.md` — staged build plan and milestones.
- `AGENTS.md` — project-specific instructions for coding agents.
- `CODEX_CONTEXT.md` — concise context to paste into Codex or keep open during project setup.
- `prompts/codex/` — ready-to-use Codex task prompts.
- `src/android_brain_memory/` — starter Python package for the memory subsystem.
- `storage/migrations/001_init.sql` — initial SQLite schema.
- `interfaces/` — ROS-style `.msg`, `.srv`, and `.action` interface drafts.
- `config/memory.yaml` — default memory policy and thresholds.
- `tasks/backlog.md` — initial task backlog.

## Suggested first workflow

1. Create/open this folder locally.
2. Import/select the folder as a Codex project.
3. Ask Codex to read:
   - `AGENTS.md`
   - `CODEX_CONTEXT.md`
   - `docs/DESIGN_DOCUMENT.md`
   - `docs/IMPLEMENTATION_PLAN.md`
4. Start with the prompt in `prompts/codex/00_project_intake.md`.
5. Then implement Phase 1 from `docs/IMPLEMENTATION_PLAN.md`.

## Local development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

## Canonical verification

Run the full local check:

```bash
python scripts/dev_check.py
```

This runs:

```bash
python scripts/init_db.py
python scripts/smoke_test_memory.py
python -m pytest
```

See `docs/runbooks/DEVELOPMENT.md` for the full development runbook.

## Memory API and CLI

The high-level memory facade is `android_brain_memory.MnemeMemory`. It wraps the current local memory path: migrations, salience scoring, raw trace storage, episode encoding/storage, fact upsert, retrieval, consolidation, and database inspection. Lower-level modules remain available for focused tests and direct use.

Use the CLI for JSON-oriented local runs:

```bash
python scripts/mneme_memory.py init-db
python scripts/mneme_memory.py inspect-db
python scripts/mneme_memory.py retrieve --query-text memory --max-results 3
```

The same CLI is available as a module:

```bash
python -m android_brain_memory.cli retrieve --query-text calibration
```

Primary commands:

- `init-db`
- `remember-candidate`
- `add-episode`
- `add-fact`
- `retrieve`
- `consolidate-once`
- `inspect-db`

See `docs/runbooks/MEMORY_CLI.md` for JSON payload examples.

## Stage 3 Virtual Head

The Stage 3 runtime wires the local cognition stack into one terminal virtual head:

```bash
mneme run --input "hello Mneme"
mneme run --json --input "remember that I like tea" --input "what do I like"
```

It uses typed input and fake deterministic peripherals only. Real camera, microphone, TTS, avatar rendering, ROS, and hardware remain later-stage work.

See `docs/runbooks/VIRTUAL_HEAD.md` for the runtime runbook.

This is intentionally small. The goal is to give Codex a precise, well-scoped project foundation before expanding into ROS 2 nodes, perception workers, and motor control.

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

## Initial local smoke test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/init_db.py
python scripts/smoke_test_memory.py
```

This is intentionally small. The goal is to give Codex a precise, well-scoped project foundation before expanding into ROS 2 nodes, perception workers, and motor control.

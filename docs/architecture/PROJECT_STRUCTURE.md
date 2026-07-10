# Project Structure

The current Mneme repository layout. This is a factual map of what exists on
disk; for the documentation-only map see [`docs/README.md`](../README.md), and
for the doc-system conventions see `AGENTS.md` §5–8.

> Note: the Python package is still named `android_brain_memory` (Mneme's
> former project name). The package has not been renamed yet — a rename is a
> separate, code-level change. Import paths and `.local/android_brain_memory.sqlite3`
> below reflect the real module name on purpose.

```text
mneme/
  README.md                 Project overview and current status
  AGENTS.md                 Authoritative contributor/agent ruleset and conventions
  PROJECT_CONTEXT.md        Concise orientation brief (project identity + rules summary)
  LICENSE
  pyproject.toml            Packaging, console scripts (mneme, mneme-memory), optional extras

  docs/                     Human-readable documentation (see docs/README.md for the index)
    README.md               Documentation index / map
    DESIGN_DOCUMENT.md      Comprehensive design reference
    architecture/           Architecture, roadmaps, runtime/serialization contracts, this file
    memory/                 Memory subsystem reference docs
    attention/              Attention manager design
    executive/              Executive + dialogue planner design
    safety/                 Safety and privacy decisions
    runbooks/               Operational / debugging procedures
    status/                 Dated point-in-time status snapshots and reports
    adr/                    Architecture decision records
    assets/                 Diagrams and generated images (incl. architecture_overview.mmd)

  implement/                Active implementation planning workspace (<topic>/CORE_IDEA|IMPLEMENT|RULES.md)
  memory/                   Durable project memory (MEMORY_INDEX.md + features/fixes/refactors/decisions/investigations/)
  prompts/                  Legacy agent intake/onboarding prompts (prompts/codex/)

  interfaces/               Future ROS-style message/service/action contracts
    msg/  srv/  action/

  src/
    android_brain_memory/   Python package: storage, models, salience, retrieval,
                            consolidation, runtime loop, perception, executive,
                            dialogue, attention, local models/UI, evaluation, CLI

  storage/
    migrations/             Tracked, checksummed SQL migrations (001_init.sql, ...)

  scripts/                  Developer scripts (init_db, smoke_test_memory, replay_scenario, dev_check, ...)
  tests/                    Unit, integration, replay, and contract tests
  config/                   Runtime configuration (memory.yaml, models.yaml)
  tasks/                    Working backlog (backlog.md)

  .github/                  CI workflows
  .local/                   Local, git-ignored runtime data and models (models under .local/models/)
```

## Where things go

- **New design/reference doc** → the matching `docs/<area>/`, then add a line to `docs/README.md`.
- **Dated status report** → `docs/status/` (not `docs/architecture/`).
- **Architecture decision** → `docs/adr/NNNN-slug.md`.
- **Planning a non-trivial change** → `implement/<topic-slug>/`.
- **Recording completed work** → `memory/<type>/<YYYY-MM-DD-slug>/` + update `memory/MEMORY_INDEX.md`.

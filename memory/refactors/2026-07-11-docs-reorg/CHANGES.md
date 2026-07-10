# Changes

## New files
- `docs/README.md` — documentation index / navigation map.
- `memory/refactors/2026-07-11-docs-reorg/` — this record.

## Moves / renames (git mv, history preserved)
- `docs/NODE_ARCHITECTURE.md` → `docs/architecture/NODE_ARCHITECTURE.md`
- `docs/IMPLEMENTATION_PLAN.md` → `docs/architecture/IMPLEMENTATION_PLAN.md`
- `docs/PROJECT_STRUCTURE.md` → `docs/architecture/PROJECT_STRUCTURE.md`
- `docs/architecture_overview.mmd` → `docs/assets/architecture_overview.mmd`
- `docs/architecture/REPO_STATUS.md` → `docs/status/REPO_STATUS.md`
- `docs/architecture/LIVE_LAB_STATUS_REPORT.md` → `docs/status/LIVE_LAB_STATUS_REPORT.md`
- `CODEX_CONTEXT.md` → `PROJECT_CONTEXT.md`

## Deletions
- `README.md~`, `.README.md.un~` (untracked editor junk).

## Content edits
- `docs/architecture/PROJECT_STRUCTURE.md` — full rewrite to the real layout.
- `docs/architecture/IMPLEMENTATION_PLAN.md` — added "historical" banner.
- `docs/architecture/{MASTER_ROADMAP,ROADMAP,COGNITIVE_CAPABILITY_ROADMAP}.md` — shared "roadmap set" banner.
- `docs/runbooks/{LOCAL_MODELS,LOCAL_COGNITIVE_MODELS}.md` — scope headers + cross-links.
- `docs/DESIGN_DOCUMENT.md` — title/status/§19 branding normalized; de-"Codex".
- `docs/adr/0001-memory-first-v1.md` — de-"Codex" wording.
- `PROJECT_CONTEXT.md` — project name → Mneme; de-"Codex".
- `docs/status/REPO_STATUS.md` — fixed sibling link to the co-moved report.
- `docs/architecture/COGNITIVE_CAPABILITY_ROADMAP.md` — status-doc link → `docs/status/`.
- `README.md` — status-doc link → `docs/status/`; added pointer to `docs/README.md`.
- `AGENTS.md` — §5/§6 structure aligned to reality; §19 read-order → `PROJECT_CONTEXT.md`.
- `.gitignore` — added `*~`, `*.un~`, `*.swp`, `*.swo`.

## Explicitly left unchanged
- `src/android_brain_memory/` package name and all accurate `android_brain_memory` doc references.
- Historical links in `memory/**`, `implement/**`, `prompts/codex/**`, `tasks/backlog.md`.

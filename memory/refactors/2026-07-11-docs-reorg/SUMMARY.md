# Documentation Reorganization

Date: 2026-07-11
Type: Refactor
Status: Complete

Reorganized the project documentation into a future-proof, self-documenting
structure that matches the doc system already declared in `AGENTS.md` §5–8, and
added the missing navigation entry point (`docs/README.md`).

## What changed at a glance

- **Added** `docs/README.md` — a one-line-per-doc index/map, grouped by area.
- **Separated** dated status snapshots into a new `docs/status/` directory
  (`REPO_STATUS.md`, `LIVE_LAB_STATUS_REPORT.md`), so point-in-time reports no
  longer sit among living reference docs.
- **Filed** loose `docs/` root files into their proper homes: `NODE_ARCHITECTURE.md`,
  `IMPLEMENTATION_PLAN.md`, `PROJECT_STRUCTURE.md` → `docs/architecture/`;
  `architecture_overview.mmd` → `docs/assets/`.
- **Rewrote** the badly stale `PROJECT_STRUCTURE.md` (it described a defunct
  `android_brain_starter_pack/` / `.codex` layout) to reflect the real repo.
- **Marked** `IMPLEMENTATION_PLAN.md` as historical, deferring to the roadmaps.
- **Clarified** the three layered roadmaps with a shared "roadmap set" banner,
  and disambiguated the two local-model runbooks with scope headers + cross-links.
- **Normalized branding**: product name "Android Brain" → "Mneme" and de-branded
  "Codex" references in living docs. Renamed `CODEX_CONTEXT.md` → `PROJECT_CONTEXT.md`.
- **Aligned** `AGENTS.md` §5–6 declared structure with the real directories
  (`config/` not `configs/`, `docs/adr/` not `docs/decisions/`, added `docs/status/`).
- **Deleted** editor junk (`README.md~`, `.README.md.un~`) and added `*~`/`*.un~`/
  `*.swp` patterns to `.gitignore`.

## Deliberately NOT changed

- The Python package `src/android_brain_memory/` was **not** renamed. Doc
  references to `android_brain_memory` imports and `.local/android_brain_memory.sqlite3`
  are accurate and were left intact. A full package rename is a separate,
  code-level effort (see FOLLOW_UP).
- Historical records under `memory/`, `implement/`, `prompts/codex/`, and
  `tasks/backlog.md` were left untouched — they are dated artifacts describing
  what was true when written; rewriting their links would falsify the audit trail.

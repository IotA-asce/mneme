# Context

## Why

The documentation had accumulated organically across many stages. The
subsystem reference docs (`docs/memory/`, etc.), `implement/`, and
`memory/features/` were already well structured, but several problems made the
docs feel unorganized and were likely to worsen over time:

1. **Loose files at `docs/` root** not filed into the declared subdirectories.
2. **A badly stale structure doc** (`PROJECT_STRUCTURE.md`) describing an old
   `android_brain_starter_pack/` layout with `.codex` artifacts.
3. **Naming drift** — the project renamed from "Android Brain" to "Mneme", but
   `CODEX_CONTEXT.md` and a few docs still used the old product name and
   referred to the "Codex" agent.
4. **No navigation entry point** for `docs/` — nothing tied the ~50 docs together.
5. **Dated status snapshots** (`REPO_STATUS`, `LIVE_LAB_STATUS_REPORT`) mixed in
   with living reference docs under `docs/architecture/`.
6. **Editor junk** (`README.md~`, `.README.md.un~`) untracked but not ignored.

## Approach

Owner chose "deep consolidation" but with the three roadmaps kept **layered**
(not merged), and naming normalized to "Mneme".

Guiding principle: make the repository match the doc system **already declared
in `AGENTS.md` §5–8** rather than inventing a new taxonomy, and add the one
missing piece (a `docs/README.md` index). Where the declared conventions and the
real repo disagreed, `AGENTS.md` was updated to match reality so the rulebook
and the repo stay in sync going forward.

## Key constraint discovered mid-task

The source package was never renamed from `android_brain_memory`, so the many
`android_brain_memory` references in docs are *accurate*, not stale. Rewriting
them would make the docs lie about the code, so they were left alone and the
rename was logged as follow-up.

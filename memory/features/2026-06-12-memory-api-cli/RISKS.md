# Risks

- The CLI is intentionally simple and may need a package console-script entry point after command names and JSON shapes settle.
- `remember-candidate` does not parse arbitrary prose into facts; callers must provide structured candidate, episode, and fact payloads.
- Summary retrieval is still not implemented, so consolidation summaries are inspectable but not returned through ordinary retrieval yet.
- Raw trace read/list APIs are still future work, so the CLI cannot inspect raw trace payloads directly.

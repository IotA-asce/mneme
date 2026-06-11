# Risks and Follow-Up

- Grouping is deterministic and simple; it is not semantic clustering.
- Episode tags are read from episode context because `Episode` does not yet have first-class tags.
- Decay/downranking metadata is recorded but retrieval does not consume it yet.
- Summary retrieval through `retrieve_memory()` remains future work.
- Fact extraction and contradiction detection remain future consolidation phases.

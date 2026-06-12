# Risks

- Working memory is intentionally small and bounded; it should not be expanded into an unbounded conversation log.
- Sensory echo is temporary and does not replace durable raw trace storage.
- Snapshot persistence stores only active context, not full event history.
- There is no automatic promotion from echo or working memory into episodic/semantic memory yet.
- Safety state is context only, not hardware safety enforcement.

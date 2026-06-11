# Risks

## Main risk

The design documents describe the long-term Mneme architecture, but the repository currently implements only a starter local memory prototype. Future work must avoid assuming that documented modules such as attention, executive reasoning, skills, safety supervisor, ROS runtime, or hardware integration already exist.

## Specific gaps

- Provenance is only partially persisted.
- Meta-memory table exists without runtime writes.
- Working memory table exists without model or store APIs.
- Retrieval is simple text search without documented reranking.
- Consolidation is a non-mutating placeholder.
- Conflict detection and user-confirmed precedence are not implemented.
- `config/memory.yaml` is not yet loaded by runtime code.

## Mitigation

Follow the roadmap order: storage/provenance tests first, then structured retrieval, then truth/conflict handling, then ranking, then consolidation.

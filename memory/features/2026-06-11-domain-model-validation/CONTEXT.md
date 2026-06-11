# Context

The memory prototype already had dataclass models, but they accepted invalid domain values and had no explicit dictionary serialization boundary. The design document requires source-aware, confidence-aware, JSON-friendly outputs suitable for future interface wrappers.

This change keeps the current architecture: models remain dataclasses, storage remains SQLite-backed, and interface files remain drafts. The goal is to prevent invalid data from entering core memory objects before later work adds retrieval ranking, conflict handling, provenance traversal, or ROS wrappers.

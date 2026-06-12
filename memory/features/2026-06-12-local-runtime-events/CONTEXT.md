# Context

Mneme's architecture requires workers to publish observations, state builders to publish state, the executive to publish intent, skills to publish goals/status, and safety to override when needed.

Before this feature, the repository had ROS-style interface drafts and memory-specific models, but no local runtime event vocabulary or dispatcher that could exercise those boundaries without ROS.

This feature provides a deterministic local compatibility layer for tests and demos while keeping ROS integration deferred.

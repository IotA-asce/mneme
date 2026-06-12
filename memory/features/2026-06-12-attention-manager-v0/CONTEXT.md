# Context

Mneme already had local runtime events, simulated perception workers, sensory echo, and working memory. The missing layer was a focused attention state builder between raw observations and future skills.

The architecture requires workers to publish observations and state builders to publish state. Attention must not bypass the executive or skills by issuing motor commands directly.

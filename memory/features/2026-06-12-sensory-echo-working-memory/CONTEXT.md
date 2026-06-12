# Context

Mneme's memory design starts with sensory echo and working memory before durable episodic or semantic storage. The repository had durable storage and local runtime events, but did not yet have active in-process components for those early memory layers.

This feature adds those components as local deterministic scaffolding. They observe runtime events and maintain bounded state; they do not own perception, executive decisions, skill execution, or hardware safety.

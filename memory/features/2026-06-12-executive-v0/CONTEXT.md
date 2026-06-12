# Context

Mneme's architecture requires a strict boundary between state builders, executive intent, skills, actuator goals, and safety override. Runtime events, working memory, attention state, and simulated perception were already present, but high-level intent arbitration was not yet implemented.

Executive v0 fills that gap without adding LLM calls, behavior tree dependencies, skill execution, or hardware behavior.

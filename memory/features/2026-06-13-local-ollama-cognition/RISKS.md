# Risks

- Ollama model quality and speed are not CI-verified.
- The default model may be too small for richer dialogue and reasoning later.
- The adapter only checks readiness; runtime/UI model-backed responses still need a separate bounded realization layer.
- Service-managed model verification depends on the Ollama daemon being reachable at runtime.

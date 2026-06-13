# Local Model Dialogue

Date: 2026-06-13
Status: Complete

Implemented opt-in local model-backed wording for Mneme. The runtime can build a bounded cognitive context, ask a local Ollama-backed model for structured response wording, validate the result, and fall back to deterministic dialogue text when unsafe or invalid.

The model does not own intent, memory retrieval, safety, skill goals, or durable memory writes.

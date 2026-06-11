# Future Node-Level Architecture

This document describes the future robot-head node graph. V1 does not implement these nodes yet.

## Memory nodes

```text
/perception/* + /state/*
        ↓
sensory_echo_node
        ↓
episodic_encoder_node ───→ semantic_extractor_node
        ↓                         ↓
retrieval_manager_node ←──── memory stores
        ↓
executive / dialogue planner
```

## Nodes

### sensory_echo_node
Keeps recent multimodal fragments and emits memory candidates.

### working_memory_node
Maintains current context: active speaker, current goal, last turns, active entities.

### episodic_encoder_node
Scores candidates and stores high-value events as episodes.

### semantic_extractor_node
Extracts facts, preferences, relationships, and summaries.

### retrieval_manager_node
Answers memory retrieval requests.

### consolidation_daemon_node
Runs background replay, clustering, summarization, pruning, and conflict detection.

### conflict_resolver_node
Handles contradictory facts and status transitions.

### meta_memory_node
Maintains confidence, provenance, retrieval counts, and speakability flags.

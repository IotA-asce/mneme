# Summary: Self Model v0 and Procedural Memory v0 (Stage 2 / M2.6)

Date: 2026-06-12
Type: Feature
Status: Complete — closes Stage 2 of the master roadmap

Added `self_model.py` with two memory layers riding on the existing fact machinery (no schema changes):

- **SelfModel**: identity facts about the robot under the reserved subject `self`, with one fixed fact ID per predicate so deliberate identity updates replace in place rather than triggering conflict handling. Self-queries answer through ordinary retrieval; `describe()` produces a deterministic summary. Inferred self-beliefs stay in the normal extraction path as `model_inferred`.
- **ProceduralMemory**: versioned skill parameters (`procedure:<skill>:<parameter>` predicates). Each `set_parameter` creates a new versioned fact superseding the prior one (explicit supersession chain, reasons in provenance notes); superseded versions stay queryable forever. `get_parameter`/`parameter_history`/`parameters_for_skill` for reads. No autonomous learning — parameters change only through explicit calls (Stage 7 owns bounded learning; the actuator bridge owns hard ranges).

This completes Stage 2 (Cognitive Integration on the Bench): all six milestones done, full bench chain deterministic under tests.

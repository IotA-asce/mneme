# Self Model and Procedural Memory

Status: V0 (Stage 2 / M2.6) — storage, provenance, and query layers only

Two memory layers riding entirely on the existing fact machinery (provenance, meta-memory, speakability, and retrieval come for free; no schema changes).

## Self Model (`SelfModel`)

Persistent identity facts about the robot under the reserved subject `self`:

- `set_identity_fact(predicate, value, source_type=..., confidence=..., notes=...)` — one **fixed fact ID per predicate** (`fact_self_<predicate>`), so a deliberate identity update replaces in place instead of creating a contradiction. Renaming the robot is an update, not a conflict.
- `get_identity(predicate)`, `identity_facts()` (active, sorted), `describe()` — deterministic text summary.
- Self facts answer through ordinary retrieval (`fact_subject="self"`).

Inferred self-beliefs do **not** belong here: anything a model infers about the robot goes through the normal extraction path as `model_inferred` and faces the usual conflict rules.

## Procedural Memory (`ProceduralMemory`)

Typed skill parameters under predicates `procedure:<skill>:<parameter>`:

- `set_parameter(skill, parameter, value, reason=...)` creates a **new versioned fact** (`…_v<N>`, object value carries `value`/`version`/`skill`/`parameter`) that explicitly supersedes the prior version (supersession chain + superseded status); the `reason` lands in meta-memory provenance notes.
- `get_parameter(skill, parameter, default=None)` — latest active value.
- `parameter_history(skill, parameter)` — every version in order; superseded versions stay queryable forever.
- `parameters_for_skill(skill)` — `{parameter: latest value}`.

Parameters change **only** through explicit calls. Autonomous procedural learning is a Stage 7 concern (bounded, with rollback); hard parameter ranges are enforced by the future actuator bridge, not here. Future skill controllers (Stage 5) read their timing/style values from this layer.

## Testing

`tests/test_self_model.py`: identity create/read/in-place update, deterministic listing and description, retrieval integration, parameter versioning with supersession chain and provenance notes, defaults, per-skill mappings, and queryable superseded history.

# Serialization Contract

Date: 2026-06-12
Status: V1 JSON wire contract for future ROS wrappers

Mneme's domain models serialize through `to_dict()` / `from_dict()` into JSON-safe dictionaries. This is the canonical wire format. Future ROS 2 nodes wrap these dictionaries; they must not redefine the domain models.

## Rules

1. Every transportable type provides `to_dict()` returning only JSON-safe values (str, int, float, bool, None, list, dict) and a `from_dict()` classmethod that validates on construction.
2. Enums serialize as their string values (`SourceType`, `MemoryStatus`, `Speakability`, `RuntimeEventKind`, `RuntimeTopic`).
3. Memory timestamps (`start_ts`, `end_ts`, `created_ts`, `first_seen_ts`, ...) are integer Unix seconds. Runtime event `timestamp` and `ttl_ms` are integer milliseconds.
4. Dict-valued model fields map to `*_json` string fields in ROS message drafts (`payload` → `payload_json`, `context` → `context_json`, `object_value` → `object_json`, `ranking_explanations` → `ranking_explanations_json`).
5. Derived fields are not transmitted. Currently: `RuntimeEvent.expires_at` (recomputed as `timestamp + ttl_ms`).
6. Optional fields use `None` in JSON; ROS drafts use empty strings / zero values to mean "unset", converted at the wrapper boundary.

## Covered Types

| Python type | Interface draft |
|---|---|
| `SalienceFeatures` | `msg/SalienceFeatures.msg` |
| `MemoryCandidate` | `msg/MemoryCandidate.msg` |
| `Episode` | `msg/Episode.msg` |
| `Fact` | `msg/Fact.msg` |
| `MemoryQuery` | `msg/MemoryQuery.msg` |
| `MemorySummaryRecord` | `msg/MemorySummary.msg` |
| `MemoryBundle` | `msg/MemoryBundle.msg` |
| `RuntimeEvent` | `msg/RuntimeEvent.msg` |

## Enforcement

`tests/test_interface_alignment.py` parses every interface draft and asserts two-way field alignment against `to_dict()` output under the documented mapping, plus JSON round-trips through `json.dumps`/`json.loads`. Drift between models and drafts fails CI.

When a model gains or loses a field:

1. update the model and its tests,
2. update the matching interface draft,
3. update the mapping table in `tests/test_interface_alignment.py` only if a new name mapping or derived field is introduced,
4. record the contract change in project memory (breaking changes require documentation per `AGENTS.md`).

## Non-Goals

- No generated ROS bindings, IDL tooling, or transport code in this repository yet.
- No binary serialization; JSON is sufficient for the bench prototype.

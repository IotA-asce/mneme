# Core Idea: ROS Integration Preparation

## Problem Statement

The implementation plan's Phase 6 requires the memory core to be wrappable by future ROS 2 nodes without changing domain models. Today:

- the `interfaces/` drafts predate the implemented models and have drifted (missing fact tags/supersession, no summaries in bundles, no structured query filters, no runtime event message),
- nothing enforces that the drafts and the Python models stay aligned,
- the JSON serialization contract used by `to_dict`/`from_dict` is implicit,
- node boundary notes and a launch plan exist only as a high-level node sketch.

## Desired Outcome

- `interfaces/` message/service/action drafts match the current domain models field-for-field under a documented mapping.
- A contract test parses the drafts and fails when models and interfaces drift apart.
- The JSON serialization format is documented as the wire contract future ROS wrappers will use.
- Node boundary notes and a phased future launch plan exist under `docs/architecture/`.

## User / Project Value

When ROS 2 integration starts, wrapping is mechanical: nodes serialize the existing dataclasses with the documented contract and the interface drafts are already correct. No domain model changes, no surprise schema drift.

## Affected Systems

- `interfaces/msg/`, `interfaces/srv/`, `interfaces/action/` (drafts only; still no generated bindings)
- `tests/test_interface_alignment.py` (new contract test)
- `docs/architecture/SERIALIZATION.md`, `docs/architecture/ROS_INTEGRATION_PLAN.md` (new)
- `docs/IMPLEMENTATION_PLAN.md`, `docs/architecture/ROADMAP.md`, `docs/architecture/REPO_STATUS.md`

## Assumptions

- Interface drafts remain documentation/contract artifacts; no ROS packages, colcon builds, or generated bindings are added.
- JSON (`to_dict`/`from_dict`) is the canonical serialization; ROS messages mirror it with `*_json` string fields for dict-valued data.

## Constraints

- No new dependencies, no runtime behavior changes, no ROS imports.
- Domain models must not change to fit the drafts; drafts change to fit the models.

## Non-Goals

- Actual ROS 2 packages, launch files, QoS tuning, or transport code.
- Hardware, actuator, or perception integration.
- Protocol buffers / IDL beyond the ROS msg draft format.

## Risks

- Draft `.msg` parsing in the contract test must stay tolerant of comments/blank lines; kept to a minimal line-based parser.
- Some model fields are derived (`RuntimeEvent.expires_at`); the contract documents and excludes them explicitly so the test stays honest.

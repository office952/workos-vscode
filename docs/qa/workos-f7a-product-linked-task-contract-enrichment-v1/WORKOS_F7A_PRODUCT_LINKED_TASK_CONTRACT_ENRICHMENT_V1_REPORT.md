# WORKOS F7A — Product-linked task-contract enrichment v1

## Verdict

```text
F7A PRODUCT-LINKED TASK-CONTRACT ENRICHMENT = PASS WITH DOCUMENTED NON-MATERIALIZATION WARNINGS
UPSTREAM CONTRACT QUALITY = PASS
NEW SNAPSHOT CHAIN = PASS (controlled fixture via OrderSnapshotV2 seed + EP V2 path)
EXECUTION PLAN DRAFT = PASS
MATERIALIZATION AUDIT GET = PASS
POST MATERIALIZE = NOT EXECUTED
DEC-009 = A / BLOCKED (True_CONDITIONAL scoped-B remains; F7A fixture outside next-dry)
REMOTE = UNCHANGED
Profitability = NOT READY
Production Ready = NU
```

## Identity

| Field | Value |
|------|-------|
| Repo | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Baseline HEAD (start) | `0c8a76cd` |
| Remote at start | `0c8a76cd` (0/0) |
| Stash | `wip-employee-unrelated` intact |
| UI / Pricing / Mobile | untouched |

## Owner decisions (binding)

| DEC | Policy | F7A result |
|-----|--------|------------|
| DEC-001 | `svg_geometry_analysis` non-operational; no SVG/DWG processing | Codes added to `NON_OPERATIONAL_PROCESS_CODES`; excluded from planned ops |
| DEC-002 | `premount_bar_preparation` BOM-only by default | Absent from default task_contract; retained as Aggregate op for BOM truth |
| DEC-003 | Parent `side_forming` / `return_face_bonding` canonical; `RETURN_PROFILE_*` alias | `collapse_operational_alias_rules` single owner; aliases not planned/audit candidates |
| DEC-004 | Parent `painting` canonical; `PAINTING` alias | Same collapse owner; one painting planned task |
| DEC-005 | Workcenter upstream → freeze → plan | Fixture stamps Aggregate ops with WC; preview projects `machine_requirement.workcenter` |
| DEC-006 | `estimated_minutes = null` + warning | All planned tasks null + `PLANNING_MINUTES_SOURCE_REQUIRED` |
| DEC-007 | Finish-aware DAG; no universal linear chain | Process/catalog edges preferred; linear fallback **removed**; `DAG_PROCESS_DEPENDENCIES_UNRESOLVED` when none |
| DEC-009 | A — POST materialize blocked | Audit GET only; gate hard-reject for non-scoped-B; post spy = 0 calls |

## Ownership map

| Truth | Owner | Consumer | Gap closed? |
|-------|-------|----------|-------------|
| Canonical operation | Component/dossier / modular graph | ProductAggregate | Yes — parent codes preserved |
| Module alias | Linked module / uppercase process | Aggregate provenance only | Yes — collapsed before task_rules freeze |
| Workcenter | Aggregate `operations[].workcenter` (ORR freeze) | EP preview / audit | Yes for controlled fixture; missing/ambiguous remain explicit |
| Task rule | `task_contract.task_rules` | Snapshot V2 / EP | Single driver unchanged |
| Dependencies | `_build_dependencies` (EP V2 preview) | `planned_tasks[].depends_on_task_keys` | Finish/process-aware; no linear invent |
| Estimated minutes | No validated source | Planning | Honest null + warning |
| Materializable | Planned draft + audit GET | DEC-009 gate | POST remains blocked |

## Canonical mapping (single owner)

Owner module: `backend/services/product_process_aggregate_bridge.py`

```text
RETURN_PROFILE_MACHINE_FORMING → side_forming
RETURN_PROFILE_FACE_BONDING    → return_face_bonding
PAINTING                       → painting
```

Public API: `collapse_operational_alias_rules`, `alias_parent_for`.

Applied at:

1. ProductAggregate dossier `_build_task_contract`
2. Modular live aggregate bridge (pre-existing)
3. `collect_effective_task_rules` (EP identity)

## Implementation design

1. Extend non-operational catalog (DEC-001).
2. Promote alias collapse to public single-owner API; wire dossier build + EP effective rules.
3. Skip synthetic composition-graph ops when alias parent already covered.
4. Remove EP V2 universal linear DAG fallback; warn instead.
5. Controlled fixture test proves Snapshot V2 → preview → persist idempotent → audit GET → no POST writes.

## Files changed

```text
backend/data/product_process/catalogs.py
backend/services/product_process_aggregate_bridge.py
backend/services/product_aggregate_service.py
backend/services/execution_plan_v2_frozen_task_identity_service.py
backend/services/execution_plan_v2_preview_service.py
backend/schemas/execution_plan_v2.py
backend/tests/test_f7a_product_linked_task_contract_enrichment.py
backend/tests/test_golden_pilot_task_contract_dag.py
docs/qa/workos-f7a-product-linked-task-contract-enrichment-v1/*
docs/worklog/realignment/2026-08-02_f7a_product_linked_task_contract_enrichment.md
```

## Fixture identifiers

Controlled fixture uses dynamic order id `880700 + (uuid % 200)` — not hardcoded; not 973019 / 88002.

Template: `TPL-VOLUMETRIC-LETTERS_v2`
Commercial total on fixture (separate from protected baseline): `1847.5`
Proof path: in-process `OrderSnapshotV2` seed → EP V2 preview/persist/audit (canonical services).
Commit: `31495122`

## Evidence summary

See sibling files:

- `ownership-and-architecture.md`
- `runtime-and-audit-evidence.md`
- `protected-baseline-before-after.json`
- `test-results.md`
- `warnings-and-blocked.md`

## Boundaries

| Boundary | Status |
|----------|--------|
| Commercial formula | Unchanged |
| Pricing UI / registry | Untouched |
| HR / assignment / sessions | Untouched |
| Machines capacity engine | Untouched (WC codes only) |
| Employee Mobile | Untouched |
| Graphic SVG/DWG | Not processed |
| UI / AppShell / Shop Floor | Untouched |
| Protected 973019 | Unchanged (`2d412e6e1234ae44` / 847.5) |

## Next gate

```text
F7A OWNER REVIEW
→ commit audit
→ runtime / snapshot / baseline / materialization-audit review
→ only then Owner may set DEC-009 = B for F7B controlled materialize pilot
```

Do **not** start F7B automatically.

## Direction score

```text
Architecture ≈ 76/100
Functional spine ≈ 72/100
UI/UX ≈ 70/100 (unchanged this gate)
Direction ≈ 74/100%
```

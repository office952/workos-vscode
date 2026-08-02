# F7A — Runtime / audit evidence

## Chain exercised (in-process, fresh pytest DB session)

```text
OrderSnapshotV2 (controlled fixture seed)
→ build_execution_plan_v2_preview
→ create_execution_plan_v2_from_order (×2 idempotent)
→ build_execution_plan_v2_materialization_audit_by_order_id
→ enforce_dec009_materialize_gate → HTTP 422 DEC009_MATERIALIZE_BLOCKED
```

Test: `backend/tests/test_f7a_product_linked_task_contract_enrichment.py::test_f7a_snapshot_preview_persist_audit_chain`

## Preview assertions

- Planned ops include: `face_cnc_cut`, `side_forming`, `return_face_bonding`, `painting`, packaging
- Excluded: `return_profile_machine_forming`, `return_profile_face_bonding`, `svg_geometry_analysis`, `premount_bar_preparation`
- WC: `side_forming` → `WC_LETTER_FORMING`; `painting` → `WC_ASSEMBLY`
- All `estimated_minutes is None` + `PLANNING_MINUTES_SOURCE_REQUIRED`
- DAG: bond depends on face + side; face/side independent (not mutual linear)

## Persist

- Exactly one `ExecutionPlan` for fixture order
- Second persist returns same `execution_plan_id`
- `execution_tasks_created` false/absent
- `operational_tasks` empty/absent

## Materialization audit GET

- `mode = audit_only`
- `materialization_status = blocked_needs_owner_go`
- `guards.writes_database = false`
- `guards.creates_execution_tasks = false`
- Alias RETURN_PROFILE_* not in candidates
- Patch spy on `materialize_execution_plan_v2_operational_tasks` call_count = 0
- Plan/reality row counts unchanged across audit

## POST materialize

```text
NOT CALLED
DEC-009 LIVE = A
enforce gate raises 422 for F7A fixture (outside next-dry 973019/21)
```

## Endpoints (service-level equivalent; HTTP routers unchanged)

| Action | Service / gate |
|--------|----------------|
| Preview | `build_execution_plan_v2_preview` |
| Persist draft | `create_execution_plan_v2_from_order` |
| Audit GET | `build_execution_plan_v2_materialization_audit_by_order_id` |
| POST materialize | **not invoked** |

## Commercial

Fixture commercial total `1847.5` unchanged after preview/persist/audit.  
Protected order `973019` not touched (see `protected-baseline-before-after.json`).

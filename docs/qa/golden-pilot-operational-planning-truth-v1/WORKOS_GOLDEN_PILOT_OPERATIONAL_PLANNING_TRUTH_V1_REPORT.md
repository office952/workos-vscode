# WORKOS — Golden Pilot Operational Planning Truth V1

**Stamp:** PASS WITH WARNINGS  
**Date:** 2026-08-02  
**Canonical repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Prior tip (pushed):** `9714ddd8` — Materialize golden pilot operational task graph  
**This build commit:** local only — `Establish operational planning truth`

---

## 1. Repo / runtime gate

| Signal | Value |
|--------|-------|
| Active worktree | `C:\w\psiso` |
| Stale checkout | `C:\Users\offic\workos_app_vs` — do not use |
| HEAD at start | `9714ddd8` (0/0 with origin after audit push) |
| Runtime | backend `:8000` from `C:\w\psiso\backend`, frontend `:3000` from `C:\w\psiso\frontend` |
| DB | `C:\w\psiso\backend\dev.db` |
| OD3 identity | `golden-pilot-planning-truth-v1/v1` · next_dry `973018/20` |
| Stash | `stash@{0}: wip-employee-unrelated` — intact |

---

## 2. Audit / push `9714ddd8`

Audited and pushed separately earlier in this GO. Local SHA = remote SHA = `9714ddd8`, ahead/behind `0/0` before this build.

---

## 3. Protected baseline (before = after)

| Order | Snapshot SHA | tasks_json SHA | Ops | Result |
|-------|--------------|----------------|-----|--------|
| 92401 | `f8447379…` | `02c70f7d…` | 18 | IDENTICAL |
| 973010 | `d48fd74b…` | `e75e2160…` | 12 | IDENTICAL |
| 973012 | `2884c54f…` | `1b73b6eb…` | 0 | IDENTICAL |
| 973013 | `74922aa7…` | `264c5ad1…` | 0 | IDENTICAL |
| 973015 | `e28aa9fd…` | `a21bcd6f…` | 18 | IDENTICAL |

Sessions / actuals / assignments remain **0**. `973015` is protected baseline — not rematerialized.

---

## 4. Workcenter registry found

**Canonical source:** `operation_resource_requirements` (`OperationResourceRequirement`)  
Resolver: `backend/services/operation_workcenter_resolution_service.py`  
Not used: `workcenter_rates`, Pricing Registry, CostEngine, UI labels, substring matching.

**Why 973015 WCs were null:** freeze never stamped ORR onto Aggregate; EP only copied empty aggregate/PD WC.

---

## 5. Mapping strategy (DEC-010)

```text
operation code
→ ORR direct or explicit product_system_aliases
→ exactly one allowed_workcenter_code → resolved
→ multiple allowed → ambiguous (fail-closed null)
→ empty allow-list → workcenter_not_required
→ missing mapping → source_missing null
```

Frozen at Quote Snapshot freeze → Order Snapshot copy → EP planned `machine_requirement` → materializer `workcenter` field. No live ORR re-read for frozen orders.

---

## 6. Coverage on new fixture `973018` (18 operational tasks)

| Operation | WC | Status | Source |
|-----------|----|--------|--------|
| vector_prep | WC_PREPRESS | resolved | alias→prepress |
| face_cnc_cut | WC_CNC_ROUTING | resolved | alias→cnc_cutting |
| back_cut | WC_CNC_ROUTING | resolved | alias→cnc_cutting |
| side_forming (×2) | WC_LETTER_FORMING | resolved | alias→cant_modelare |
| return_face_bonding | WC_METAL_FAB | resolved | alias→welding |
| led_install_letters | null | **ambiguous** | montaj_led → WC_LED_ASSEMBLY\|WC_ASSEMBLY |
| electrical_letters (×2) | null | **ambiguous** | same |
| qc_letters / assembly / packaging | WC_ASSEMBLY | resolved | ORR aliases |

**15/18 resolved · 3/18 ambiguous fail-closed** (owner-correct; no invent).

---

## 7. Planning minutes (DEC-011)

| Source evaluated | Verdict |
|------------------|---------|
| planning_duration_contract (vector_prep COUNT_BASED_TIME) | **Used** |
| ORR / capacity metadata | No minutes standards |
| time_assumptions dossier | Not owner-correct structured contract |
| workcenter_rates / CostEngine / /price | **Forbidden — not used** |

**Contract chosen:** Product System `planning_duration_contract` + Aggregate freeze stamp.  
**Fix applied:** flatten `quote_geometry` into duration facts; run ORR ensure-ops before duration resolve.

| Result | Count |
|--------|-------|
| Resolved | **1** — vector_prep = **10.0** (5 letters × 2 min) |
| source_missing null | **17** — never coerced to 0 |

---

## 8. Fixture IDs

| Field | Value |
|-------|-------|
| workspace_id | `25d264e6-e413-4721-a3c6-22b35a2fb263` |
| quote_id | 18 |
| Quote Snapshot V2 | 19 / `QSV2-2024-0019` |
| order_id | **973018** |
| order_code | `ORD-IV6-V2-1785674936-18` |
| plan_id | **20** |
| planned / ops / deps | 18 / 18 / 24 |
| path | freeze → pricing review → owner approval → accept → convert → EP persist → audit → materialize |
| 2nd materialize | **409** `operational_tasks_already_materialized` |

Orphan intermediate fixtures `973016`/`973017` (pre-duration-fix) were not materialized.

---

## 9. Frozen integrity

| Proof | Result |
|-------|--------|
| Quote/Order Aggregate stamps WC + minutes + provenance | PASS |
| EP preview reads frozen Aggregate only | PASS |
| Materializer preserves WC/minutes/DAG | PASS |
| In-memory mutated ORR (`WC_INVENTED_AFTER_FREEZE`) does not change preview of 973018 | PASS (`_tmp_frozen_integrity.json`) |
| Protected hashes unchanged | PASS |

---

## 10. Eligibility readiness audit (read-only)

```text
status: blocked
ready_for_employee_eligibility: false
workcenter_blocker_count: 3   # LED ambiguous ORR
planning_minutes_source_missing_count: 17
identity_stable: true
materialized: true
sessions/actuals/assignments: 0
```

Gate correctly **blocks** until Owner disambiguates `montaj_led` allow-list. Minutes gaps alone would be `ready_with_warnings`.

---

## 11. UI

**URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=973018`

| Screenshot | Path |
|------------|------|
| Full page | `screenshots/01-973018-full-page.png` |
| Task graph / WC | `screenshots/02-973018-task-graph-workcenters.png` |
| Viewport | `screenshots/03-973018-viewport.png` |
| Null minutes + ambiguous WC | `screenshots/04-973018-null-minutes-and-ambiguous-wc.png` |

**Honest opinion:** Page is readable in day/light. Task graph remains primary. WC codes and the single resolved `MIN=10` are clear; LED rows honestly show `—` + WC gap; minutes gaps do not invent zeros. Post-materialize banner noise reduced. TYPE column still echoes WC via `machine_type` (pre-existing quirk). No redesign required.

---

## 12. Tests run

**Green:**  
`test_operation_workcenter_resolution`, `test_planning_minutes_source_contract`, `test_dec009_materialize_gate`, `test_golden_pilot_task_contract_dag`, `test_execution_plan_v2_materialize`, `test_te2e_028b_formula_planning_duration` (62 targeted).  
`git diff --check` clean.

**Not run:** full pytest · full frontend suite.

---

## 13. Warnings / boundaries

**Warnings (acceptable):**  
- 3 ambiguous LED workcenter mappings (fail-closed)  
- 17 ops without planning-minute standards  
- Intermediate unused orders 973016/973017 in local DB  
- Full suites not run  
- TYPE/WC display duplication minor

**Boundaries held:** no eligibility impl · no assignments/sessions/actuals · no Inventory/Pricing/CostEngine/`/price` · no machine assignment · no protected rematerialize · no silent migration.

---

## 14. Next Owner GO

1. Disambiguate ORR `montaj_led` to a single canonical WC (`WC_LED_ASSEMBLY` **or** `WC_ASSEMBLY`) — then eligibility readiness can become `ready_with_warnings`.  
2. Optionally author more planning-duration contracts for CNC / forming / assembly (still not from rates).  
3. Then Employee Eligibility vertical slice.

**Direction:** ~94/100% toward eligibility-ready task identity.

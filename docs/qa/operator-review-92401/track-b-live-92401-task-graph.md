# Track B — Live Read-Only Review: 92401 / Plan 13 / MAT-02

**Mode:** GET + SQLite read · **no POST**  
**Date:** 2026-07-31  
**URL for Owner:** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

---

## Identity confirmation

| Field | Expected | Observed | Class |
|-------|----------|----------|-------|
| Order | 92401 | 92401 | **PASS** |
| Plan | 13 | 13 | **PASS** |
| Fixture (scoped-B) | FIX-DEC009-MAT-02 | live compat `scoped_b_fixture_id=FIX-DEC009-MAT-02` | **PASS** |
| Ops count | 18 | **18** (API + DB) | **PASS** |
| Unique task_ids | 18 | 18/18 | **PASS** |
| Foreign order_ids | 0 | 0 | **PASS** |
| Foreign plan_ids | 0 | 0 | **PASS** |
| Activation hash | 20E `e6edbb80…` | `e6edbb802ba3ab25629914a976f6679e` | **PASS** |
| Duplicate materialize | none | none | **PASS** |
| Prior 973010 | 12 unchanged | **12** · hash `15bde334…` | **PASS** |

---

## Task graph (18 ops)

| Seq | Code | machine_type (requirement class) | Module | Component family | Deps |
|-----|------|----------------------------------|--------|------------------|------|
| 1 | vector_prep | PREPRESS | — | comp_face_litere | — |
| 2 | cnc_face_cut | CNC_ROUTER | debitare_fata | comp_face_litere | vector_prep |
| 3 | cnc_back_cut | CNC_ROUTER | debitare_spate | comp_spate_litere | cnc_face_cut |
| 4 | return_profile_forming | RETURN_PROFILE_MACHINE_FORMING | modelare_cant | comp_lateral_litere | cnc_back_cut |
| 5 | return_face_bonding | RETURN_PROFILE_FACE_BONDING | asamblare | comp_lateral_litere | return_profile_forming |
| 6 | painting | WC_PAINT | finisaje | volum_aluminum… | return_face_bonding |
| 7 | vinyl_application | FACE_VINYL_APPLICATION_LABOR | colantare_fata | comp_face_litere | (chain) |
| 8 | led_installation | LED_ASSEMBLY | sistem_led | comp_led_litere | (chain) |
| 9 | electrical_wiring | ELECTRICAL_WIRING | electrica_litere | comp_led_litere | (chain) |
| 10 | mounting_template | CNC_ROUTER | sablon_montaj | comp_finisaj_litere | (chain) |
| 13 | qc_internal_check | QC_INSPECTION | — | comp_finisaj_litere | (chain) |
| 14 | packaging | PACKAGING | ambalare_livrare_montaj | comp_finisaj_litere | (chain) |
| 24 | cut_acm_panel | ACM_PANEL_CUTTING | structura_suport | ACM mounting panel | (ACM cluster) |
| 25 | fold_cassette | ASSEMBLY | structura_suport | ACM | (ACM cluster) |
| 26 | mount_acm_panel | ASSEMBLY | structura_suport | ACM | (ACM cluster) |
| 27 | v_groove_router | ACM_V_GROOVE | structura_suport | ACM | (ACM cluster) |
| 28 | return_profile_face_bonding | WC_ASSEMBLY | volum_aluminum | volum_aluminum | (volum cluster) |
| 29 | return_profile_machine_forming | WC_FORMING | volum_aluminum | volum_aluminum | (volum cluster) |

**Note:** `sequence_index` values are **not** contiguous 1–18 (gaps 11–12, 15–23). Count is still exactly 18 unique tasks — template/provenance sequence, not a missing-ops defect.

---

## Side-effect / gate confirmation (this review)

| Check | Before RO review | After RO review |
|-------|------------------|-----------------|
| Ops 92401 | 18 | **18** |
| Ops 973010 | 12 | **12** |
| Sessions | 0 | **0** |
| `execution_reality` 92401/973010 | 0/0 | **0/0** |
| Authorize source/live | False / false | **False / false** |
| DEC-009 | A / BLOCKED | **A / BLOCKED** |
| Attendance | 0 | **0** |

**Proof no writes:** only `GET` health/compat/plan + SQLite SELECT; authorize constant untouched; no POST materialize.

---

## Pricing / time

| Check | Result |
|-------|--------|
| Plan-level price/EUR/commercial fields | **Absent** |
| Task-level price/hourly fields | **Absent** |
| `estimated_time_minutes` | **null ×18** (not invented; not used as price) |
| Assigned employees | **null ×18** |
| workcenter field | **null ×18** (machine_type carries planning requirement class) |

---

## UI hardcode

| Check | Result |
|-------|--------|
| `MaterializedOpsGraph` hardcodes 92401 / 13 / MAT-02 | **NO** |
| Default without `?orderId=` | **973010** (MAT-01) — hygiene WARN |
| Load path for this review | **`?orderId=92401`** |

---

## Verdict

**PASS WITH WARNINGS** — Live 92401/13/MAT-02 envelope is correct, complete (18), scoped, and stable under RO inspection. Warnings: sequence gaps (provenance), empty `material_inputs[]`, null minutes/WC/assignee honesty, ops-graph default 973010.

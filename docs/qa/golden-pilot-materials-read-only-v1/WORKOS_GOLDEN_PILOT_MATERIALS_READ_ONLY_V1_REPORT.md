# WORKOS — Golden Pilot Materials Read-Only V1

**Date:** 2026-08-02  
**Stamp:** **PASS WITH WARNINGS**  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Canonical active repo:** `C:\w\psiso` (same remote as `workos_app_vs`; that checkout remains detached/stale at `82a713e0`)

---

## 1. Repo / runtime gate

| Check | Result |
|-------|--------|
| Initial HEAD | `cdd57629` ahead 1/0 |
| `cdd57629` audit | Owner-correct (wrap Model A; paint missing; no invent depth/zero) |
| Push `cdd57629` | **Done** → local=remote=`cdd57629` · **0/0** |
| Runtime | `:8000` uvicorn + `:3000` vite from `C:\w\psiso` |
| DB | `sqlite …/backend/dev.db` |
| Authorize | `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False` |
| Stash | `stash@{0}: wip-employee-unrelated` intact |

---

## 2. Fixtures & IDs

### Fixture A — Oracal wrap (derived linear + wrap)

| Field | ID |
|-------|-----|
| workspace_id | (see convert run; quote linked) |
| quote_id / code | `11` / `Q-GP-*` (oracal run) → order below |
| Quote Snapshot V2 | `QSN2-2026-0012` (id 12) |
| order_id | **973012** |
| execution_plan_id | **15** |
| URL | `http://127.0.0.1:3000/execution/ops-graph?orderId=973012` |

Materials: profile `10 ml` **Calculată**; Oracal wrap `0.84 mp` **Calculată**; adhesive **Sursă lipsă** + null.

### Fixture B — RAL paint (source_missing paint)

| Field | ID |
|-------|-----|
| Quote Snapshot V2 | `QSN2-2026-0013` (id 13) |
| order_id | **973013** |
| execution_plan_id | **16** |
| URL | `http://127.0.0.1:3000/execution/ops-graph?orderId=973013` |

Materials: profile `10 ml` **Calculată**; `MAT-VOPSEA-RAL` **Sursă lipsă** + null; adhesive **Sursă lipsă**.

Earlier attempt order **973011** / plan **14** also exists (same contract); primary proof uses **973012/973013**.

---

## 3. Canonical path used

```text
IntakeV6 workspace (service)
→ QuoteSnapshotV2Service.freeze (apply_technical_material_requirements)
→ pricing review → owner approval → accept
→ convert_v6_quote_to_order (PA materials copied verbatim)
→ create_execution_plan_v2_from_order (draft shell)
→ GET /execution/plan/{order_id} → frozen_technical_materials
```

No `/price`, no materialize POST, no raw snapshot INSERT, no 92401 writes.

---

## 4. Oracle vs runtime (derived)

| Case | Oracle | Runtime 973012 |
|------|--------|----------------|
| Perimeter 10 m × depth 60 | wrap `0.84` m² | **0.84 mp** Calculată |
| Linear meter | `10` ml | **10 ml** Calculată |
| No default depth 60 | missing depth → null | unit tests + freeze fail-closed |
| Paint yield | null source_missing | **973013** paint null |

---

## 5. Quote → Order semantic diff

Convert uses `_component_scope_fields_from_quote` — `product_aggregate_snapshot` copied verbatim (no recompute). Covered by `test_golden_pilot_material_quantity_freeze.py`.

---

## 6. ExecutionPlan frozen-read

`GET /api/v1/execution/plan/{order_id}` attaches `project_frozen_technical_materials` from Order Snapshot V2. Downstream does not recalculate quantities.

---

## 7. Inventory / Pricing / no-false-zero

- Technical quantity path: `technical_material_requirement_service` + formula handlers only.
- Local fix `commercial_totals_from_frozen_cpp` only for accept/convert VAT totals (commercial), not material qty.
- Null qty displayed as `—`, never `0`.

---

## 8. Baseline 92401 before/after

| Field | Before | After |
|-------|--------|-------|
| snapshot_v2_sha256 | `f8447379…c70c` | **identical** |
| tasks_json_sha256 | `02c70f7d…b0bb` | **identical** |
| materials / null / zero | 22 / 22 / 0 | **unchanged** |
| ops / sessions / actuals | 18 / 0 / 0 | **unchanged** |

---

## 9. UI

Extended existing ops-graph section **Materiale tehnice conform comenzii**:

- Status labels: Calculată / De referință / Sursă lipsă / Legacy / nespecificată
- Columns: denumire, cod, cantitate+unit, status, componentă, explicație
- Expandable provenance
- Honesty note: frozen ≠ stock / reservation / procurement

---

## 10. Screenshots

| File | Content |
|------|---------|
| `screenshots/01-973012-full-page.png` | Full page golden wrap fixture |
| `screenshots/02-973012-materials-expanded.png` | derived + source_missing |
| `screenshots/03-973012-provenance.png` | provenance expand |
| `screenshots/04-973013-paint-source-missing.png` | paint null |
| `screenshots/05-92401-legacy-expanded.png` | 22× Legacy / nespecificată |

### Visual verification steps

1. Open `…/ops-graph?orderId=973012`
2. Confirm honesty note
3. Click **Arată lista** → see 10 ml + 0.84 mp Calculată; adhesive Sursă lipsă
4. Open `…/973013` → paint Sursă lipsă + null
5. Open `…/92401` → 22 Legacy, task graph still primary

### Honest UI opinion

Page remains usable: task graph / capacity stay primary; materials section is compact, collapsed by default, and does not claim stock. Component paths are long/noisy for operators — acceptable in provenance expand; main table is clear. Empty ops envelope on new drafts is honest, not confusing once DEC-009 banner is read. Day/light tokens preserved.

---

## 11. Tests

**Ran:** golden pilot freeze; technical material contract; persist draft shell; convert suite (targeted); OpsGraph FE tests.  
**Not ran:** full pytest; full frontend suite.

---

## 12. Warnings

1. Live freeze active-scope emitted ~3 linked-module rows — `reference_only` proven in unit tests, not on these two live fixtures.
2. Duplicate same-code/different-provenance proven in unit tests; not present on these live scopes.
3. Plan draft allows `blocked_missing_task_rules` empty shell (materials RO attach) — no materialize.
4. Local E2E fixes: frozen CPP totals signature; order provenance list vs dict.
5. `workos_app_vs` path in prompt is stale; work done on `C:\w\psiso`.

---

## 13. Files changed (product commit)

- `backend/services/ops_graph_frozen_technical_materials.py`
- `backend/services/intake_v6_snapshot_authoritative_offer_service.py`
- `backend/services/order_snapshot_v2_convert_service.py`
- `backend/services/execution_plan_v2_persist_service.py`
- `backend/tests/test_golden_pilot_material_quantity_freeze.py` (+ persist/contract updates)
- `frontend/src/components/workos/OpsGraphFrozenTechnicalMaterials.tsx` (+ tests/types)
- QA report + screenshots + worklog

---

## 14. Boundaries

No inventory, procurement, material_inputs, materialize, paint yield, `/price`, SVG parse, 92401 rewrite, HR.

---

## 15. Next Owner GO

1. Authorize paint yield (if needed), **or**
2. Broaden active-scope freeze so formula-less `reference_only` + face/wrap duplicate provenance appear on one live order, **or**
3. Task-rules completeness so draft plans are not `blocked_missing_task_rules`.

**Direction:** **96/100%**

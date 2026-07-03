# BUILD-EXECUTION-SNAPSHOT-FROM-VOLUMETRIC-QUOTE

**Date:** 2026-06-07  
**Build status:** **PASS** (execution snapshot + commercial readiness gate follow-up)  
**Prior build:** BUILD-COMMERCIAL-E2E-FIXTURE (PARTIAL)  
**Related commit:** not committed (per user rule)

## Summary

Quote-derived **TPL-VOLUMETRIC-LETTERS** orders now receive an execution-ready `product_definition.layers[].processes[].type` mapping at conversion time. Plan generation returns **HTTP 201** for the commercial E2E path without weakening gate validation.

**Follow-up (2026-06-07):** `BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE` removed the E2E readiness overlay; `live_gate_can_create_commercial_quote` is now **true** for the fixture. Execution snapshot mapping from this build is unchanged.

## Relationship to BUILD_COMMERCIAL_E2E_FIXTURE

| Area | Before | After |
|------|--------|-------|
| Quote → order convert | PASS (with readiness overlay) | PASS (unchanged) |
| `/execution/:id` page load | PASS | PASS |
| Plan generation | `snapshot_incomplete` / BLK-08 | **201** with tasks |
| E2E plan assertion | Expected incomplete | Asserts **201** + tasks |

## Exact snapshot diff found

Compared **O-E2E-SPRINT33** / `test_execution_flow._complete_snapshot_dict()` (canonical `cnc_routing`, `final_assembly`) vs quote-derived order **before fix**:

| Field | Working fixture | Quote-derived (broken) |
|-------|-----------------|------------------------|
| `product_definition.layers[].processes[].type` | Canonical 20-value enum | Legacy ProductSystem heuristics: `prepress`, `cnc`, `assembly`, `wiring`, `painting`, `vinyl_application`, `return_profile_*`, `qc_inspection`, `packaging` |
| `cost_result.estimated_time_minutes` | 180 | 75 (OK — BLK-06 fallback) |
| `component_breakdown` | N/A at order layer | Present in quote Shape B wrapper but **not passed** to `OrderSnapshotService` |
| Gate blocker | None (when types canonical) | **BLK-08** on every non-canonical `process.type` |

**Root cause:** `ProductSystemService._build_layers()` maps workcenter strings to legacy types, not `CANONICAL_TASK_TYPES`. CostEngine v2 priced operation codes (`vector_prep`, `face_cnc_cut`, `assembly_letters`, etc.) live in `component_breakdown.operations_detail` but were not used to normalize order snapshot processes.

**Not the issue:** empty layers (BLK-05), missing `cost_result` (BLK-03), missing `product_id` (BLK-10).

## Mapping implemented

New module: `backend/services/order_execution_snapshot_mapper.py`

- Maps **operation codes** (primary) and **legacy process types** (fallback) → canonical task types.
- Enriches `estimated_time_minutes` from `component_breakdown.operations_detail` when process time is 0 and breakdown has real `estimated_minutes` / `hours`.
- Does **not** invent minutes for formula-priced ops with `line_total > 0` and zero time (gate uses `cost_result.estimated_time_minutes` fallback; plan service skips zero-minute processes).

Wired in:

- `OrderSnapshotService.create_from_quote(..., component_breakdown=...)`
- `orders.py` `create_order_from_quote` — extracts Shape B `component_breakdown` before unwrapping inner snapshot.

Example mappings:

| Operation / legacy | Canonical `type` |
|------------------|------------------|
| `vector_prep` / `prepress` | `file_preparation` |
| `face_cnc_cut`, `back_cut`, `mounting_template_cnc_cut` / `cnc` | `cnc_routing` |
| `side_forming` / `return_profile_machine_forming` | `edge_bending` |
| `return_face_bonding` | `welding` |
| `painting` | `volumetric_letter_assembly` |
| `vinyl_application` | `vinyl_cutting` |
| `led_install_letters` | `led_assembly` |
| `electrical_letters` / `wiring` | `led_wiring` |
| `assembly_letters` / `assembly` | `volumetric_letter_assembly` |
| `qc_letters` / `qc_inspection` | `quality_control` |
| `packaging_letters` / `packaging` | `packaging` |

## Files changed

| File | Change |
|------|--------|
| `backend/services/order_execution_snapshot_mapper.py` | **New** — canonical type + time enrichment |
| `backend/services/order_snapshot_service.py` | Apply mapper at conversion |
| `backend/routers/orders.py` | Pass `component_breakdown` from Shape B wrapper |
| `backend/tests/test_volumetric_order_execution_snapshot.py` | **New** — contract tests |
| `backend/scripts/seed_commercial_e2e_fixture.py` | Delete `execution_plan` / `execution_reality` on fixture reset |
| `frontend/e2e/commercial-chain-live.spec.ts` | Assert plan **201** + tasks; no `snapshot_incomplete` alert |
| `docs/qa/BUILD_EXECUTION_SNAPSHOT_FROM_VOLUMETRIC_QUOTE.md` | This doc |
| `docs/qa/BUILD_COMMERCIAL_E2E_FIXTURE.md` | Follow-up note |

## Backend tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest tests.test_volumetric_order_execution_snapshot tests.test_execution_flow -v
```

**Results:** 14/14 OK

- Volumetric normalization → all process types ⊆ canonical enum  
- `evaluate_gate` → `can_generate: true` (no BLK-08)  
- `ExecutionPlanService.from_order` → tasks with canonical `process_type`  
- `_complete_snapshot_dict` regression unchanged  
- `test_execution_flow` — 7/7 OK  

## E2E tests

```powershell
# seed + run (backend :8000, frontend :3000)
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npm run test:e2e:commercial-live
```

**Result:** **1 passed** (5.4s) — convert → execution → `POST /execution/plan/from-order/{id}` **201**, `tasks.length > 0`.

## Commands run

| Command | Result |
|---------|--------|
| `unittest tests.test_volumetric_order_execution_snapshot` | 7/7 OK |
| `unittest tests.test_execution_flow` | 7/7 OK |
| `scripts/seed_commercial_e2e_fixture.py` | OK |
| `npm run test:e2e:commercial-live` | 1/1 pass |

## Readiness overlay — removed (follow-up build)

Removed by `BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE`. See `docs/qa/BUILD_VOLUMETRIC_COMMERCIAL_READINESS_GATE.md`.

## Remaining blockers

1. Production volumetric commercial quote gate (`needs_review` / `ready_for_quote:false`) — owner decision, not this build.
2. Formula-priced operations often have `estimated_minutes: 0` in breakdown; plan emits tasks only for ops with positive minutes (currently `assembly_letters`, `qc_letters` for fixture) unless future costing populates durations.
3. FigJam board update not performed this session.

## No-regression checklist

- [x] Working vs quote-derived snapshot compared; gap documented  
- [x] Quote→order creates canonical execution process types for TPL-VOLUMETRIC-LETTERS  
- [x] Plan generation 201 on commercial E2E path  
- [x] No global validation weakening  
- [x] No fake placeholder snapshot values  
- [x] CostEngine formulas untouched  
- [x] Unsupported templates unmappable → still fail BLK-08  
- [x] Backend contract tests added  
- [x] Playwright commercial-live updated  

## Suggested next substantial build

**BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE** — resolve `needs_review` / `live_gate_can_create_commercial_quote` without E2E overlay, or document explicit owner acceptance policy for `needs_review` quotes.

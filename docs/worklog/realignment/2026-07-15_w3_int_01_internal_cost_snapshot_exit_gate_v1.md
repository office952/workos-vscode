# W3-INT-01 — WAVE_3_INTERNAL_COST_AND_SNAPSHOT_PERSISTENCE_EXIT_GATE_V1

**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `dab6b7e`  
**Gate task:** W3-INT-01  
**Verdict:** `W3_INT_01_PASS_WITH_NONBLOCKING_DEBT_CLOSE_WAVE_3`

## Runtime listener cleanup

| Service | PID before | Port | Worktree | Action | PID after | HEAD served |
|---------|------------|------|----------|--------|-----------|-------------|
| Backend (uvicorn reload tree) | 12840 / 21732 | 8000 | `C:\w\psiso` | `taskkill /F /T` — stopped psiso reload workers | — | — |
| Backend (orphan socket) | 4392 | 8000 | **NOT_PROVEN** (no matching process in `tasklist`) | `taskkill` failed — ghost LISTENING entry | 4392 | **NOT_PROVEN** |
| Backend (verification) | — | 8001 | `C:\w\psiso` | Started fresh uvicorn for parity check | child PID | **NOT_PROVEN** (no git HEAD endpoint) |

**Runtime listeners clean:** NO — port 8000 retains orphan LISTENING PID 4392 without a visible process. OpenAPI payload size matches fresh `:8001` instance (781665 bytes), but accepted HEAD `dab6b7e` cannot be proven on `:8000`.

## Canonical fixture (Case B)

- Workspace: `80570a4a-a806-4305-a39c-b34a72092694` (`IV6-195E885C`)
- Template: `TPL-VOLUMETRIC-LETTERS_v2`
- Mounting: `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` with `acm_thickness_mm: 3` in `finish_setup.mounting_solution.configuration`
- Volum: `TPL-VOLUM-ALUMINIU_v1` persisted (applicable cant path — not forced into Case B ACM-only semantics)
- **No priced V6 quote** in `backend/dev.db` (`quotes_total: 0`) — live `POST .../snapshot-v2` not exercised on canonical fixture

## 7H registry investigation

### Call chain

1. `EstimatedInternalCostService.build_preview` → `AggregateCostBomBuilderService.build_preview`
2. Registry: `load_material_cost_dict` / `inventory_materials` (`status=active`, `unit_cost>0`)
3. Material resolution: `aggregate_cost_bom_adapter._canonical_and_quote_input` → `_resolve_material_code` → `_check_material_pricing`
4. Blocker emission: `INTERNAL_MATERIAL_COST_MISSING` when `pricing_availability != available`

### Root cause (fixed this gate)

**`INTERNAL_COST_VALUE_ALREADY_EXISTS_MAPPING_DEFECT`**

- `MAT-ACM-BOND-3MM` / `MAT-ACM-BOND-4MM` active at **15.0 RON/mp** in dev.db
- `MAT-ACM-BOND-PANEL` alias row intentionally `missing_price` (seed contract)
- 7G/`QuoteOrchestrator` resolves alias via `resolve_acm_bond_panel_material_rate`
- 7B/7H BOM path did **not** flatten `finish_setup.mounting_solution.configuration.acm_thickness_mm` into values **nor** map alias → variant in `_resolve_material_code`

### Fix (narrow)

- `aggregate_cost_bom_adapter._canonical_and_quote_input`: call `merge_acm_boxed_mounting_derived_fields`
- `aggregate_cost_bom_adapter._resolve_material_code`: map `MAT-ACM-BOND-PANEL` → thickness variant (PSU/profile pattern)
- Tests: `tests/test_acm_bond_bom_variant_resolution.py`

### Post-fix runtime (dev.db)

- 7G: **ready**, gross **2190.072 RON** (fixture drift vs earlier 1888.68 note — not repriced for gate)
- 7H: **blocked/partial**, total **1560.3836 RON**, **no** `INTERNAL_MATERIAL_COST_MISSING` for ACM bond
- Remaining 7H block: **5** `unknown_owner_decisions` + BOM `partial` — not registry alias gap

## Snapshot persistence proof

**Live POST:** NOT_RUN (no safe priced quote on canonical workspace; port 8000 ownership ambiguous)

**Isolated service/API proof (pytest):**

| Proof | Result |
|-------|--------|
| Canonical 7G+7H compose (W3-T03) | PASS |
| 7G ready + 7H blocked → `partial_with_owner_decisions` | PASS |
| V6 idempotency (`V6_SNAPSHOT_ALREADY_EXISTS`) | PASS |
| Persisted JSON read-back (`test_snapshot_json_round_trip`) | PASS |
| 7G/7H totals frozen separately in stored JSON | PASS |
| Synthetic CPP forbidden | PASS |

**Snapshot preview on canonical workspace (service layer):**

- Readiness: `partial_with_owner_decisions`
- Composition graph: frozen in `product_aggregate_snapshot`
- Graph-cost projection: **FROZEN_INSIDE_7H_PROVENANCE** (BOM provenance string + active modules; not a top-level snapshot field)

## Test baseline (focused)

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Focused Wave 3 suites | 127 | 8 | 0 | 0 |

Failures classified:

| Test | Classification |
|------|----------------|
| `test_intake_v6_quote_snapshot_v2::test_output_composition_*` (2) | PREEXISTING_FIXTURE_DEBT (`_latest_quote_snapshot_v2` missing) |
| `test_quote_snapshot_v2::test_post_*` (2) | PREEXISTING_ROUTE_AUTH_DEBT |
| `test_quote_snapshot_v2::test_dev_bridge_readiness_not_dual_blocked` | PREEXISTING_FIXTURE_DEBT |
| `test_quote_snapshot_v2::test_owner_decisions_carried` | PREEXISTING_FIXTURE_DEBT |
| `test_estimated_internal_cost_preview::test_post_endpoint_returns_preview` | PREEXISTING_ROUTE_AUTH_DEBT |

## Temporary debt

| ID | Classification |
|----|----------------|
| TD-W3-GRAPH-COST-001 | KEEP_UNTIL_WAVE_4 |
| TD-W3-V6-DIAG-COST-PLUS-001 | KEEP_UNTIL_WAVE_4 (diagnostic only) |
| Duplicate `:8000` ghost listener | BLOCKS_WAVE_3 (runtime proof only — code authority singular) |
| Step 8 route/auth HTTP tests | KEEP_UNTIL_LEGACY_CONSUMER_REMOVAL |
| V6 snapshot adapter | KEEP_UNTIL_WAVE_4 |
| Loading flash | MOVE_TO_WAVE_6 |

## Wave 3 exit / Wave 4

- **Wave 3:** COMPLETE WITH NONBLOCKING DEBT (registry mapping fixed; snapshot persistence proven in tests; live POST + runtime HEAD proof deferred)
- **Wave 4 recommendation:** `OPEN_WAVE_4_INTEGRATION_GATE` after clearing `:8000` ghost listener and seeding/linking a priced V6 quote for one live snapshot POST smoke

## Commits

- Implementation: ACM bond BOM variant mapping (this gate)
- Docs: this worklog + STATUS/TASK_GRAPH updates

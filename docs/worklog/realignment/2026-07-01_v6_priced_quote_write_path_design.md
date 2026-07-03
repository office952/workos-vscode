# 2026-07-01 V6 Priced Quote Write Path Design

Status: docs-only design complete. No implementation changes.

## Files Read

- `docs/worklog/realignment/2026-07-01_v6_priced_quote_backend_dry_run.md`
- `docs/worklog/realignment/2026-07-01_v6_zero_quote_fast_guard.md`
- `docs/architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md`
- `docs/architecture/product-system/INTAKE_V6_CALCULATION_VISIBILITY_AND_ZERO_VALUE_HANDOFF_TRACE.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_calculation_visibility_zero_value_trace.md`
- `docs/worklog/realignment/2026-07-01_v6_priced_quote_bridge_design.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_FULL_E2E_PRODUCT_TRUTH_TO_EXECUTION_ALIGNMENT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/services/intake_v6_pricing_input_service.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/intake_v4_commercial_quote_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/routers/quotes.py`
- `backend/routers/quote_output_snapshots.py`
- `backend/routers/quote_output_composition.py`
- `backend/services/quote_output_composition_service.py`
- `backend/tests/test_intake_v6_priced_quote_dry_run.py`
- `backend/tests/test_intake_v6_zero_quote_fast_guard.py`
- `frontend/src/api/quotes.ts`
- `frontend/src/api/quoteOutputSnapshots.ts`
- `frontend/src/api/quoteOutputComposition.ts`
- `frontend/src/pages/Quotes.tsx`
- `frontend/src/components/workos/QuoteWizard.tsx`
- `frontend/src/components/workos/QuoteOutputCompositionPreview.tsx`

## Current Dry-Run Status

The V6 backend dry-run is implemented and read-only. It returns backend commercial totals, line items, material/internal trace, pricing input trace, commercial proposal trace, warnings, blockers, and explicit false persistence flags.

Validated prior to this design:

- Dry-run tests: `8 passed`.
- Dry-run + zero guard: `12 passed`.
- Dry-run does not create/update quote, write totals, create snapshot/order, call V4 draft builder, or copy frontend preview totals.

## Design Decision

The future write path should be a dedicated Intake V6 backend mutation:

`POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`

This route is `DOCUMENTED_NOT_IMPLEMENTED`. It should re-run or verify the backend V6 dry-run server-side, check expected total/hash/operator confirmation, then write only eligible quote totals and line items.

The authoritative pricing source is `intake_v6_backend_priced_dry_run` or a later approved backend source. V4/V2 draft payloads, frontend preview totals, and QuoteWizard frontend-driven payloads are forbidden as V6 commercial truth.

## Recommended Option

Recommended target: Option A first, with Option B fallback.

Option A: update existing V6 draft quote when it is clearly `V6_DRAFT_UNPRICED`, zero-valued, linked to the same workspace, and has no snapshot/order/history.

Option B: create a new V6 priced quote when the old draft has snapshot/order/history, ambiguous linkage, non-draft status, or overwrite risk.

Existing quote #6 style records:

- If no snapshot/order exists: eligible for future explicit priced write.
- If snapshot/order/history exists: do not overwrite; create a new priced quote and link/supersede through provenance.

## No Code Changes

No backend service, router, schema, database, frontend, API, Quote Snapshot runtime, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, or Employee Mobile code was changed.

## Files Created

- `docs/architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_v6_priced_quote_write_path_design.md`

## Validation

Docs diagnostics only. No tests were needed because this was a docs-only design task.

Required implementation blockers were not encountered. No implementation was performed.

## Recommended Next Safe Slice

Recommendation: `A. V6_PRICED_QUOTE_WRITE_SMALL_SLICE_NEXT`.

The small slice should implement only the backend write service/route for eligible V6 unpriced drafts, with expected-total/hash checks and provenance, and still no Quote Snapshot, Order, ProductAggregate, Task Graph, or ExecutionPlan.

## Owner GO Required

Owner GO required next: YES.

Any future mutation that writes quote totals, updates/creates quotes, creates snapshots, accepts, converts, or creates orders/tasks must wait for explicit owner GO.

## Forbidden Confirmation

- No implementation.
- No quote total write.
- No quote update.
- No quote creation.
- No DB/schema migration.
- No API changes.
- No Quote Snapshot runtime.
- No Order Snapshot.
- No ProductAggregate.
- No Task Graph.
- No ExecutionPlan.
- No frontend preview copied into quote totals.
- No V2/V4 commercial truth for V6.
- No Employee Mobile.

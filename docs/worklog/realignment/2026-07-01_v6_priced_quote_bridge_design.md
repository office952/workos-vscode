# 2026-07-01 V6 Priced Quote Bridge Design

Status: docs-only complete. No implementation changes.

## Scope

Created the design for the V6 Priced Quote Bridge: how a non-zero Intake V6 preview can later become backend-authoritative quote totals without copying frontend preview values and without turning mutable Intake V6 state into an official offer.

## Files Read

- `docs/architecture/product-system/INTAKE_V6_CALCULATION_VISIBILITY_AND_ZERO_VALUE_HANDOFF_TRACE.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_calculation_visibility_zero_value_trace.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_FULL_E2E_PRODUCT_TRUTH_TO_EXECUTION_ALIGNMENT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `docs/architecture/product-system/samples/gradi_curat_product_truth_draft.sample.json`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthReadiness.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/pages/Quotes.tsx`
- `frontend/src/api/quotes.ts`
- `frontend/src/api/quoteOutputComposition.ts`
- `frontend/src/api/quoteOutputSnapshots.ts`
- `frontend/src/components/workos/QuoteOutputCompositionPreview.tsx`
- `frontend/src/components/workos/QuoteOutputSnapshotsSection.tsx`
- `frontend/src/components/workos/QuoteWizard.tsx`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/services/intake_v4_commercial_quote_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_pricing_input_service.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/intake_v6_quote_to_order_service.py`
- `backend/routers/quotes.py`
- `backend/routers/quote_output_snapshots.py`
- `backend/services/quote_output_composition_service.py`

## Current Zero Finding

Intake V6 calculates non-zero preview values. The current draft quote path intentionally writes zero placeholders by reusing the V4 draft quote payload builder. Oferte and output composition mirror persisted quote columns, so the draft quote shows `0,00 RON` until a backend pricing action writes official totals. The V6 commercial spine correctly blocks with `QUOTE_NOT_PRICED`.

## Runtime Checked

Read-only runtime checks were performed for workspace `IV6-BB8EE3F8`, intake `IR-MR18L96M`, quote `Q-V6-IV6-BB8EE3F8-1782910533`.

Observed values:

- Intake material total: `782.38 EUR`
- Intake commercial preview: `6517.86 RON` gross, `5386.66 RON` net
- Handoff preview: `allowed=true`, `preview_only=true`
- Quote persisted totals: `0`
- Commercial spine blocker: `QUOTE_NOT_PRICED`
- Output composition commercial total: `0 RON`
- Output snapshots count: `0`

No draft/quote/order/snapshot/pricing-review/accept/convert mutation was called.

## Docs Created

- `docs/architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_v6_priced_quote_bridge_design.md`

## No Code Changes

No frontend, backend, database, schema, seed, API, Product Truth persistence, pricing runtime, Quote Snapshot runtime, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, quote/order/task creation, forced confirmation, or Employee Mobile changes were made.

## Recommended Next Slice

Recommended next slice: `C. SMALL_UI_LABEL_PLUS_BLOCKER_FIX`.

Reason: current runtime has an Intake disclaimer and V6 commercial spine blocker, but Oferte cards/detail and client-offer/output preview still show `0,00 RON` prominently for unpriced V6 drafts.

## Owner GO Required

Owner GO required next: YES.

Any reproducer that needs clicking a CTA that creates, prices, accepts, snapshots, converts, or mutates a quote/order must stop for owner GO first.

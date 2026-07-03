# Intake V6 Calculation Visibility + Zero Value Handoff Trace

Status: AUDIT_ONLY  
Date: 2026-07-01  
Runtime: `IV6-BB8EE3F8` / `IR-MR18L96M` / quote `#6`

## Scope

Audit the value path from Intake V6 calculation/preview to draft/offer/quote output. No implementation, no mutation, no persistence change, no backend/frontend/DB/pricing/ProductTruth/ProductDefinition/Quote Snapshot/Order/ExecutionPlan change.

## Sources Inspected

- `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/pages/Quotes.tsx`
- `frontend/src/lib/dataStore.ts`
- `frontend/src/api/quoteOutputComposition.ts`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/intake_v6_pricing_input_service.py`
- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/services/intake_v4_commercial_quote_service.py`
- `backend/services/intake_v4_quote_to_order_service.py`
- `backend/services/intake_v6_quote_to_order_service.py`
- `backend/routers/quotes.py`
- `backend/routers/quote_output_composition.py`
- `backend/routers/quote_output_snapshots.py`
- `backend/services/quote_output_composition_service.py`

## Runtime Observations

- Workspace found: `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`, code `IV6-BB8EE3F8`, title `IMPORT EXPORT EXIM - Litere volumetrice gradinita`.
- Material breakdown was non-zero: `estimated_cost_total=782.38 EUR`, `material_cost_total=782.38 EUR`.
- Pricing preview was ready: `is_ready_for_quote=true`, `adapter_status=warnings`, `readiness_status=ready_for_quote`.
- Pricing preview payload contained non-zero geometry/material/lighting/mounting values including perimeter, area, LED watts, module count, and grouped finish matrix.
- Handoff preview allowed draft quote creation and had no fatal blockers.
- Existing V6 quote `#6` / `Q-V6-IV6-BB8EE3F8-1782910533` was draft and unpriced: all commercial quote columns and first line item price/total were `0`.
- Quote notes contained `intake_v6_linkage_v1` with `pricing_source=intake_v6_pricing_input_preview` and `requires_pricing_review=true`.
- Commercial spine correctly reported `QUOTE_NOT_PRICED` and blocked conversion prerequisites.
- Output composition preview read quote columns and returned `commercial_summary.total=0 RON`.
- Output snapshots list for quote `#6` was empty.

## Findings

1. Intake V6 calculation visibility works for the inspected workspace. The operator can see non-zero internal/material and commercial preview values.
2. The draft quote handoff does not persist those preview values into official quote commercial columns.
3. The zero quote value is intentional at draft creation: shared V4/V6 draft payload creation writes placeholder zero totals until backend pricing review/pricing authority is used.
4. Oferte and output composition display zero because they correctly mirror persisted quote columns.
5. Acceptance/conversion guards are working; they do not treat zero as a priced quote.
6. Product Truth non-persistence is not the direct zero-value cause in this path.

## Zero Fallbacks Confirmed

- Draft quote builder writes zero line item price/total and zero commercial quote columns.
- Quote commercial totals summary coerces missing/empty totals to zero and blocks with `QUOTE_NOT_PRICED`.
- V6 pricing review total extraction rejects zero quote columns and requires either positive quote totals or frozen Snapshot V2 commercial total.
- Output composition mirrors quote columns and therefore returns zero when quote columns are zero.
- Frontend data mapping uses numeric zero defaults for missing quote fields; this is display normalization, not the root cause.

## Deliverable

Created architecture audit:

- `docs/architecture/product-system/INTAKE_V6_CALCULATION_VISIBILITY_AND_ZERO_VALUE_HANDOFF_TRACE.md`

## Recommendation For Later Work

Do not copy frontend Intake V6 preview gross/net into official quote totals. Add or reuse a backend-authoritative commercial proposal/pricing bridge, then freeze/review that value into quote commercial truth or Quote Snapshot V2 before acceptance and conversion.

Suggested later UX hardening:

- Show an explicit `Unpriced V6 draft` state in Oferte.
- Block or flag output composition preview when quote `grand_total <= 0` and no frozen commercial snapshot exists.
- Add a trace display from Intake V6 preview to quote draft payload to pricing review state.

## Validation Notes

This worklog records an audit-only pass. Runtime calls were read-only GET/fetch operations from the existing browser session. No create/update/accept/convert/snapshot/pricing mutation was called.

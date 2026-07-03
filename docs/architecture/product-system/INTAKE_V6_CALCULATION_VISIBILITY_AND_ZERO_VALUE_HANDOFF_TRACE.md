# INTAKE V6 CALCULATION VISIBILITY + ZERO VALUE HANDOFF TRACE

Status: AUDIT_ONLY  
Date: 2026-07-01  
Scope: Intake V6 calculation visibility and zero-value quote handoff trace  
Runtime inspected: `IV6-BB8EE3F8` / `IR-MR18L96M` / workspace `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3` / quote `#6`

## 1. Verdict

Verdict: PARTIAL.

Intake V6 does calculate and display non-zero commercial preview values. The inspected workspace has a non-zero material/internal total and a non-zero pricing input payload. The value does not become official quote commercial truth during draft quote creation. The existing V6 quote is intentionally created as an unpriced draft with zero quote columns and zero line item totals, then the commercial spine blocks acceptance/conversion with `QUOTE_NOT_PRICED` until a backend pricing authority supplies real totals.

The zero value is not caused by Product Truth draft builder persistence. Product Truth is preview-only and not part of this persisted quote handoff. The zero appears at the quote draft payload boundary, where the V4/V6 shared draft quote builder writes placeholder commercial totals.

## 2. Audit Constraints

No implementation was performed. No backend code, frontend code, database schema, pricing rule, ProductTruth persistence, ProductDefinition, Quote Snapshot creation, Order, ProductAggregate, or ExecutionPlan behavior was changed.

Runtime inspection was read-only. No draft quote, offer, order, snapshot, acceptance, conversion, pricing review, or mutation action was created during this audit.

## 3. Runtime Evidence

Workspace:

- `workspace_code`: `IV6-BB8EE3F8`
- Intake request: `IR-MR18L96M`
- Title: `IMPORT EXPORT EXIM - Litere volumetrice gradinita`
- Status/readiness: `ready_for_quote_preview`

Material breakdown:

- `material_cost_total`: `782.38 EUR`
- `estimated_cost_total`: `782.38 EUR`
- `contains_estimates`: `true`
- `contains_missing_prices`: `false`
- Rows: 11 materials, 8 consumables, 5 operations, 1 edge/cant operation

Pricing input preview:

- HTTP status: `200`
- `is_ready_for_quote`: `true`
- `adapter_status`: `warnings`
- `readiness_status`: `ready_for_quote`
- Fatal blockers: none
- Production counts: 19 letters, 28 cut contours, 9 inner holes, 19 material pieces, 21 volumetric pieces, 2 artwork pieces
- Non-zero payload examples: `width_mm=5086.99`, `height_mm=600.03`, `depth_mm=60`, `letter_perimeter_m=20.9727`, `return_material_perimeter_ml=31.6373`, `face_area_m2=1.2638`, `artwork_area_m2=0.8005`, `led_module_count=144`, `estimated_led_watts=108`, `required_psu_watts=140.4`, `mounting_template_area_m2=3.0523`

Observed UI preview from Intake V6:

- Internal/material cost: `782.38 EUR`
- Gross commercial preview: `6517.86 RON`
- Net commercial preview: `5386.66 RON`

Quote handoff preview:

- `handoff_allowed`: `true`
- `can_create_internal_draft_quote`: `true`
- `fatal_blockers`: `[]`
- `preview_only`: `true`

Existing linked quote:

- Quote ID: `6`
- Quote code: `Q-V6-IV6-BB8EE3F8-1782910533`
- Status: `draft`
- `subtotal`: `0`
- `discount`: `0`
- `total_before_vat`: `0`
- `vat`: `0`
- `grand_total`: `0`
- `margin_pct`: `0`
- First line item: `quantity=19`, `unit_price=0`, `total=0`
- Notes contain `intake_v6_linkage_v1` with `pricing_source=intake_v6_pricing_input_preview` and `requires_pricing_review=true`

Commercial spine:

- `quote_commercial_totals.available`: `false`
- `quote_commercial_totals.grand_total`: `0`
- `quote_commercial_totals.blocker`: `QUOTE_NOT_PRICED`
- `pricing_review.completed`: `false`
- Owner approval: missing/invalid
- Conversion blocked by: `PRICING_REVIEW_REQUIRED`, `OWNER_APPROVAL_REQUIRED`, `QUOTE_NOT_ACCEPTED`

Quote output preview/snapshots:

- Output composition commercial summary reads quote columns and returns `subtotal=0`, `vat=0`, `total=0`, `currency=RON`
- Template link status: `missing`
- Output snapshot count for quote `#6`: `0`

## 4. Calculation Surfaces

| Surface | File / API | Role | Runtime state | Audit result |
| --- | --- | --- | --- | --- |
| Intake V6 material breakdown | `GET /api/v1/intake-v6/workspaces/{workspace_id}/material-breakdown` / `backend/services/intake_v6_material_breakdown_service.py` | Builds material, consumable, operation preview through V4 registry service | Non-zero `782.38 EUR` | OK |
| Pricing input preview | `GET /api/v1/intake-v6/workspaces/{workspace_id}/pricing-input-preview` / `backend/services/intake_v6_pricing_input_service.py` | Normalizes V4 quote input preview under V6 namespace | Ready with non-zero geometry, finish, lighting, mounting fields | OK |
| Local commercial preview model | `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts` | Computes frontend-only net/gross preview from costs and commercial inputs | Non-zero gross/net shown | UI_ONLY |
| Live calculation summary | `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx` | Displays internal cost and commercial preview | Shows non-zero preview values | OK/UI_ONLY |
| Pricing input panel | `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx` | Displays adjustable preview and final preview price | Local display only | UI_ONLY |
| Quote handoff preview | `GET /api/v1/intake-v6/workspaces/{workspace_id}/quote-handoff-preview` | Confirms whether draft quote handoff is allowed | Allowed, preview-only | OK |
| Draft quote creation | `POST /api/v1/intake-v6/workspaces/{workspace_id}/create-draft-quote` / `backend/services/intake_v6_commercial_quote_service.py` | Creates guarded draft quote using pricing preview payload | Existing quote was created | NOT_PERSISTED for commercial totals |
| Draft payload builder | `backend/services/intake_v4_commercial_quote_service.py` | Shared V4/V6 draft quote payload builder | Writes quote totals and line item totals as zero | ZERO_FALLBACK |
| Oferte list/detail | `frontend/src/pages/Quotes.tsx` and `frontend/src/lib/dataStore.ts` | Maps and displays persisted quote columns | Displays zero because backend quote columns are zero | OK, source reflects persisted zero |
| Output composition preview | `backend/services/quote_output_composition_service.py` | Mirrors quote commercial columns | Returns zero commercial summary | ZERO_FALLBACK inherited from quote |
| V6 commercial spine | `backend/services/intake_v6_quote_to_order_service.py` | Requires priced quote totals or frozen Snapshot V2 totals | Blocks with `QUOTE_NOT_PRICED` | OK |

## 5. Handoff Trace Table

| Stage | File/function/API | Field name | Observed value | Expected value | Status | Risk | Recommended fix later |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Material breakdown preview | `GET material-breakdown` | `totals.estimated_cost_total` | `782.38 EUR` | Non-zero internal estimate | OK | Low | Keep read-only preview as diagnostic input. |
| Pricing input preview | `GET pricing-input-preview` | `quote_input_payload.*` | Non-zero geometry/material/lighting fields | Complete backend payload for pricing | OK | Medium due canonical trigger warnings | Resolve trigger field mismatch separately. |
| Frontend commercial preview | `buildIntakeV6OfferModel` | `subtotalNet`, `totalGross` | `5386.66 RON`, `6517.86 RON` observed in UI | Visible internal preview | UI_ONLY | High confusion if interpreted as official quote | Label/bridge later to a backend commercial proposal, not quote columns directly. |
| Handoff eligibility | `GET quote-handoff-preview` | `handoff_allowed` | `true` | Draft quote may be created | OK | Medium: allowed does not mean priced | Keep wording explicit: creates unpriced draft. |
| Draft quote service | `create_guarded_draft_quote_from_intake_v6_workspace` | `quote_input_payload` in notes/snapshot | Present with non-zero production payload | Persist trace input for review | OK | Medium: no official commercial total in quote columns | Add future commercial proposal/snapshot bridge. |
| Draft line item | `build_v4_quote_draft_payload` | `line_items[0].unit_price`, `line_items[0].total` | `0`, `0` | Draft placeholder until pricing | ZERO_FALLBACK | High visible zero in Oferte | Future bridge must price through QuoteWizard/CostEngine or frozen commercial proposal before official quote display. |
| Draft quote columns | `build_v4_quote_draft_payload` | `subtotal`, `total_before_vat`, `vat`, `grand_total`, `margin_pct` | all `0` | Unpriced draft placeholders | ZERO_FALLBACK | High: official output appears zero | Do not copy frontend preview; create backend-authoritative priced state. |
| Oferte data mapping | `mapQuoteFromDB` | `grandTotal`, `totalBeforeVAT`, `lineItems.total` | all `0` for quote #6 | Reflect persisted quote | OK | Medium: UI accurately displays an unpriced draft | Add clearer unpriced-state UX later, not hidden synthetic totals. |
| Output composition preview | `_build_commercial_summary` | `commercial_summary.total` | `0 RON` | Mirror quote columns | ZERO_FALLBACK | High if exported/previewed as commercial output | Block/flag output preview when quote is unpriced. |
| Commercial spine totals | `quote_commercial_totals_summary` / `_extract_v6_pricing_review_totals` | `grand_total`, `blocker` | `0`, `QUOTE_NOT_PRICED` | Block unpriced quote | OK | Low: guard is working | Preserve as acceptance/conversion gate. |
| Snapshot V2 fallback | `_extract_v6_pricing_review_totals` | frozen commercial total | Missing | Use only if accepted/frozen and positive | SNAPSHOT_MISSING | Medium | Future bridge may freeze backend commercial proposal before review/approval. |

## 6. Zero Fallback Inventory

Confirmed zero-producing or zero-normalizing points:

- `backend/services/intake_v4_commercial_quote_service.py`: `build_v4_quote_draft_payload` writes draft line items with `unit_price: 0` and `total: 0`, and quote columns `subtotal`, `discount`, `total_before_vat`, `vat`, `grand_total`, and `margin_pct` as `0.0`.
- `backend/services/intake_v6_commercial_quote_service.py`: V6 draft creation reuses the V4 draft payload builder and stores pricing input trace/linkage instead of official totals.
- `backend/services/intake_v4_quote_to_order_service.py`: commercial totals summary coerces missing/empty `grand_total` to `0` and marks the quote unavailable with `QUOTE_NOT_PRICED` when total is not positive.
- `backend/services/intake_v6_quote_to_order_service.py`: pricing review total extraction uses quote columns first only if `grand_total > 0`; otherwise it looks for a frozen Quote Snapshot V2 commercial total; otherwise it blocks with `QUOTE_NOT_PRICED`.
- `backend/services/intake_v6_quote_to_order_service.py`: order financial snapshot construction blocks final gross values `<= 0`.
- `backend/services/quote_output_composition_service.py`: output composition mirrors quote columns with `float(quote_obj.subtotal or 0)`, `float(quote_obj.vat or 0)`, and `float(quote_obj.grand_total or 0)`.
- `frontend/src/lib/dataStore.ts`: DB quote mapping converts missing numeric quote fields to `0` for display models.
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`: local slider/input parsing uses `Number(event.target.value) || 0`; this affects local preview controls only.

Not confirmed as the cause:

- Product Truth draft builder non-persistence. It is separate preview-only frontend TypeScript and is not the source of quote `grand_total=0` in this path.
- Material breakdown missing prices. The inspected runtime had `contains_missing_prices=false` and non-zero material totals.

## 7. Answers To Explicit Questions

Does Intake V6 calculate non-zero values? Yes. Runtime material breakdown and pricing input payload are non-zero, and the UI displays non-zero net/gross preview values.

Are those values persisted into official quote commercial columns during draft creation? No. Draft quote creation persists trace/linkage and quote input payload metadata, but official quote columns remain zero by design.

Does the draft quote preserve enough input trace to recalculate or review later? Mostly yes. `intake_v6_linkage_v1` notes include the pricing source, `requires_pricing_review=true`, and the non-zero `quote_input_payload`. It does not preserve the frontend local gross/net preview as official commercial truth.

Why does Oferte or quote output show zero? Because Oferte and output composition read persisted quote columns/line items. For quote `#6`, those persisted values are zero placeholders from draft quote creation.

Is the zero value silently accepted into acceptance/conversion? No. The commercial spine reports `QUOTE_NOT_PRICED`, pricing review is incomplete, owner approval is missing, and V6 order conversion is blocked.

Can the frontend preview be copied directly into quote totals as a fix? No. The frontend preview is a local planning preview. Official quote totals must come from backend pricing authority or a frozen commercial proposal/snapshot with governance.

Is Quote Snapshot V2 currently supplying a commercial total for quote `#6`? No. The inspected output snapshot list is empty and commercial spine has no pricing totals source.

## 8. Correct Future Bridge

The safe future bridge is not to copy `offerModel.totalGross` or `offerModel.subtotalNet` directly into quote columns.

A correct bridge should introduce or reuse a backend-authoritative commercial proposal step:

1. Intake V6 produces the non-zero quote input payload and internal material breakdown.
2. Backend pricing authority calculates a CommercialPriceProposal or QuoteWizard/CostEngine price from that payload.
3. The proposed totals are reviewed/frozen into quote commercial truth or Quote Snapshot V2.
4. Quote columns or frozen snapshot commercial fields become positive and auditable.
5. Commercial spine can complete pricing review, owner approval, acceptance, and conversion using positive backend-authoritative totals.

Potential UX hardening later:

- In Intake V6, keep commercial preview labelled as internal preview.
- In Oferte, show a distinct `Unpriced V6 draft` state instead of relying on zero totals alone.
- In output composition preview, block or strongly flag commercial output when `grand_total <= 0` and no frozen commercial snapshot exists.
- Add a read-only trace panel linking Intake V6 preview values, draft quote trace payload, and pricing review state.

## 9. Risks, Recommendation, And Forbidden Confirmation

Primary risk: operators may see a non-zero Intake V6 preview, create/open a draft quote, and then see `0 RON` in Oferte/output without understanding that this is an intentional unpriced draft boundary.

Secondary risk: output composition currently mirrors zero quote columns and can produce a preview with `0 RON`, even though it is read-only and preview-only.

Recommendation for a later implementation phase:

- Preserve the current acceptance/conversion guard.
- Add a backend commercial proposal/pricing bridge instead of frontend total copying.
- Make unpriced draft state visibly explicit in Oferte and output previews.
- Treat canonical trigger mismatch warnings as a separate ProductSystem alignment issue, not as the cause of zero totals.

Forbidden confirmation:

- No API mutation was made.
- No persistence change was made.
- No frontend runtime change was made.
- No backend runtime change was made.
- No DB change was made.
- No pricing rule was changed.
- No ProductTruth persistence was added.
- No ProductDefinition behavior was changed.
- No Quote Snapshot creation behavior was changed.
- No Order, ProductAggregate, or ExecutionPlan behavior was changed.

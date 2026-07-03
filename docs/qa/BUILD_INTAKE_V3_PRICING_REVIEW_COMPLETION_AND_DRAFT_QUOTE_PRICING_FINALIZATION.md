# BUILD — INTAKE_V3_PRICING_REVIEW_COMPLETION_AND_DRAFT_QUOTE_PRICING_FINALIZATION

**Status:** PASS (local, uncommitted)  
**Base commit:** `9c6849a` — draft quote review and pricing handoff alignment  
**Branch:** `local/integration-pr4-plus-svg-path`

## Purpose

First **pricing review completion** layer for Intake V3 guarded draft quotes: operator completes manual pricing review explicitly, quote becomes a **priced draft** (`requires_pricing_review=false`, totals on Quote + audit in `notes`) without Order, Execution, Inventory, or CostEngine.

## Pricing path audit (pre-implementation)

| Question | Answer |
|----------|--------|
| 1. Existing pricing endpoint safe for IV3 draft? | **No** — `POST /api/v1/entities/quotes/{id}/price` uses QuoteOrchestrator → CostEngine and sets `status=priced`. Out of scope. |
| 2. Usable without Order/Execution/Inventory? | Manual completion path updates Quote only. |
| 3. CostEngine side effects? | CostEngine is calculation + quote status transition on canonical price path; **not invoked** in this build. |
| 4. Quote fields updated? | `subtotal`, `discount`, `discount_pct`, `total_before_vat`, `vat` (%), `grand_total`, `notes` (linkage extended). |
| 5. Quote priced meaning | IV3 priced draft: `status=draft`, `grand_total>0`, `intake_v3_linkage_v1.pricing_review.status=completed`, `priced_draft=true`. |
| 6. `requires_pricing_review` → false | Only after POST `complete-pricing-review` with all confirmations + coherent totals. |
| 7. Accept/convert guards | Always `can_accept_quote=false`, `can_convert_to_order=false` for IV3 (separate future build). |
| 8. Normal quotes affected? | No — IV3 intake_code prefix + linkage required. |

## Variant decision: **B — Manual pricing review explicit**

Automatic CostEngine pricing (Variant A) rejected: status transition to `priced` and formula invocation violate build boundary. Notes + existing Quote monetary columns sufficient (no migration).

## Backend

### Service

`backend/services/intake_v3_quote_pricing_review_completion_service.py`

- `get_pricing_review_completion_state` / `complete_intake_v3_quote_pricing_review`
- Validates: IV3 draft only, snapshot + owner decision, confirmations, total coherence (±0.05)
- Updates linkage: `requires_pricing_review=false`, `priced_draft=true`, `pricing_review={...}`
- Duplicate blocked: `PRICING_REVIEW_ALREADY_COMPLETED`
- Pre/post Order + ExecutionPlan counts — fail-closed on side effects

### Shared helper (circular import fix)

`backend/services/intake_v3_quote_linkage_utils.py` — `is_pricing_review_completed`, `get_pricing_review_record`

### Endpoints

- `GET /api/v1/intake-v3/quotes/{quote_id}/pricing-review-state`
- `POST /api/v1/intake-v3/quotes/{quote_id}/complete-pricing-review`
- `GET /api/v1/intake-v3/workspaces/{workspace_id}/pricing-review-state`
- `POST /api/v1/intake-v3/workspaces/{workspace_id}/complete-pricing-review`

### Updated services

- `intake_v3_draft_quote_review_service.py` — `pricing_review_completed`, accept/convert always blocked for IV3
- `intake_v3_quote_pricing_handoff_service.py` — handoff `completed` after pricing review

### Tests

`backend/tests/test_intake_v3_quote_pricing_review_completion.py` — 10 scenarios per build spec

## Frontend

- `IntakeV3PricingReviewCompletionPanel.tsx` — manual pricing form + confirmations
- `IntakeV3DraftQuoteReviewPanel.tsx` — before/after pricing review copy
- API: `fetchIntakeV3PricingReviewState`, `completeIntakeV3PricingReview`
- Flow step 13: **Pricing Review**
- Quotes badges: `Pricing reviewed`, `Priced draft`
- `intakeV3QuoteCommercialGuard.ts` — completion from notes; IV3 always blocked for accept/convert

## Commands + results

```text
# Targeted backend
27 passed (pricing completion + draft review + real commercial creation)

# Backend regression (IV3 chain)
173 passed

# Frontend targeted
146 passed (IntakeV3App + flowState + guard + quoteCommercialGuidance)
```

## Boundary

- No Order / ExecutionPlan / ExecutionTask / Inventory
- No CostEngine / formula / markup / TVA global changes
- No accept / convert / send / production
- No DB migration
- No commit / push / ZIP (per build instruction)

## Next build

**INTAKE_V3_PRICED_DRAFT_ACCEPT_CONVERT_GUARDS** — enable guarded accept/convert only after priced draft + separate confirmations.

## Recommended commit message

```text
feat(intake-v3): add manual pricing review completion for IV3 priced draft quotes
```

# BUILD — INTAKE_V3_DRAFT_QUOTE_REVIEW_AND_PRICING_HANDOFF_ALIGNMENT

**Status:** PASS (local, uncommitted)  
**Base commit:** `ce31a63` — guarded draft commercial quote creation  
**Branch:** `local/integration-pr4-plus-svg-path`

## Purpose

After guarded draft quote creation (`IV3-{workspace_id}`, `status=draft`, snapshot in `notes`), expose read-only **draft quote review** and **pricing handoff alignment** so operators/commercial can audit linkage, snapshot, and blocked accept/convert paths — without Order, Execution, Inventory, or CostEngine.

## Scope

### Backend

- `intake_v3_draft_quote_review_service.py` — detect IV3 quotes, parse notes, snapshot summary, conversion guard
- `intake_v3_quote_pricing_handoff_service.py` — pricing handoff checklist (no final price, no CostEngine)
- Schemas: `IntakeV3DraftQuoteReview*` in `schemas/intake_v3.py`
- Endpoints (read-only):
  - `GET /api/v1/intake-v3/workspaces/{workspace_id}/draft-quote-review`
  - `GET /api/v1/intake-v3/quotes/{quote_id}/draft-review`
- Tests: `test_intake_v3_draft_quote_review.py`

### Frontend

- `IntakeV3DraftQuoteReviewPanel.tsx` — post-create review UI in Intake V3
- `fetchIntakeV3DraftQuoteReview` + contracts
- Flow step 12: **Draft Quote Review**
- Quotes list badges: Intake V3 / Draft / Requires pricing review
- `intakeV3QuoteCommercialGuard.ts` + `quoteCommercialGuidance` guard for IV3 `requires_pricing_review`

### Docs

- Intake V3 status/roadmap/decisions + TPL adapter notes updated

## Quote notes parsing strategy

- Reuses `intake_v3_linkage_v1` JSON in `Quotes.notes` (no migration)
- Safe parse: invalid JSON → warnings, no 500
- Detection: `intake_code` prefix `IV3-` + linkage JSON + `status=draft`

## Accept / convert guard audit

| Layer | Finding |
|-------|---------|
| `getQuoteCommercialActionVisibility` | `draft` already hides accept/convert |
| IV3 `requires_pricing_review` | Additional guard blocks accept/convert/send even if status becomes `priced` later without clearing flag |
| Backend review | `can_accept_quote=false`, `can_convert_to_order=false` for IV3 drafts |
| Normal quotes | `review_status=not_applicable`, guard returns allow |

## Boundary

- No Order / ExecutionPlan / ExecutionTask / Inventory
- No CostEngine / pricing formulas / TVA / markup changes
- No DB migration
- No commit / push / ZIP in this build run

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_draft_quote_review.py tests/test_intake_v3_real_commercial_quote_creation.py tests/test_intake_v3_real_quote_creation_enablement_readiness.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/quoteCommercialGuidance.test.ts
```

## Pending

- Explicit pricing review build (manual pricing step, clear `requires_pricing_review` only via dedicated flow)

## Recommended commit message

```
feat(intake-v3): add draft quote review and pricing handoff alignment for IV3 quotes
```

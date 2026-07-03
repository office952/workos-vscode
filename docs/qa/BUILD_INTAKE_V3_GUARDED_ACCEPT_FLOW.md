# BUILD: INTAKE_V3_GUARDED_ACCEPT_FLOW

**Date:** 2026-06-18  
**Base commit:** `8cd2b86` — priced draft accept/convert readiness audit  
**Verdict:** PASS (after tests green)

## Purpose

Enable a guarded, explicit accept flow for Intake V3 priced draft quotes without creating Orders, Execution plans/tasks, or Inventory mutations.

## Status transition audit

| Question | Answer |
|----------|--------|
| Real accepted status | **`accepted`** (Variant A — not `acceptata`) |
| Direct `draft → accepted` | **Not allowed** by `validate_transition` |
| IV3 priced draft stored as | `status=draft` with totals in quote fields + linkage |
| Chosen path | **`draft → priced → accepted`** in one guarded POST, each step validated |
| Generic quote update creates Order? | **No** |
| Dedicated accept before this build? | **No** — only generic quote status update |

## Backend

- **Service:** `backend/services/intake_v3_guarded_accept_flow_service.py`
- **Endpoints:**
  - `GET /api/v1/intake-v3/quotes/{quote_id}/accept-state`
  - `POST /api/v1/intake-v3/quotes/{quote_id}/accept`
  - `GET /api/v1/intake-v3/workspaces/{workspace_id}/accept-state`
  - `POST /api/v1/intake-v3/workspaces/{workspace_id}/accept`
- **Schemas:** `IntakeV3AcceptQuoteRequest`, `IntakeV3AcceptQuoteResponse`, `IntakeV3AcceptDecisionRecord`, `IntakeV3AcceptState`
- **Notes:** merges `intake_v3_linkage_v1.accept_decision` without removing snapshot/pricing_review/owner_decision
- **Readiness updates:** accept → `accepted`; convert stays blocked (`can_convert_now=false`)

## Validation (fail-closed)

- IV3 linkage + intake_code prefix
- pricing review completed, priced draft, final price, snapshot, owner decision
- all explicit confirmations + non-empty reason
- duplicate accept blocked via `accept_decision` record
- invalid notes JSON blocked before linkage parse
- order/plan counts unchanged after accept

## Boundary

**In scope:** Quote status + notes only via IV3 guarded endpoints  
**Out of scope:** Order, ExecutionPlan, ExecutionTask, Inventory, CostEngine, convert, client send, generic Quotes accept

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_guarded_accept_flow.py tests/test_intake_v3_priced_draft_accept_convert_readiness.py tests/test_intake_v3_quote_pricing_review_completion.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/intakeV3QuoteCommercialGuard.test.ts src/lib/quoteCommercialGuidance.test.ts
```

## Next build

**INTAKE_V3_GUARDED_CONVERT_TO_ORDER** — separate guarded convert; still no execution/inventory in same step.

## Recommended commit message

```
feat(intake-v3): add guarded accept flow for IV3 priced draft quotes
```

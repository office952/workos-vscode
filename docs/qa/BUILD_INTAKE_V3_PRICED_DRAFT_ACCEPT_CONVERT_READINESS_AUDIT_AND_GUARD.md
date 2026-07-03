# BUILD — INTAKE_V3_PRICED_DRAFT_ACCEPT_CONVERT_READINESS_AUDIT_AND_GUARD

**Status:** PASS (local, uncommitted)  
**Base commit:** `2e3e705` — manual pricing review completion for IV3 priced draft quotes  
**Branch:** `local/integration-pr4-plus-svg-path`

## Purpose

Read-only **accept/convert readiness audit** for IV3 priced draft quotes. Actions remain blocked; separate builds required for real accept or convert.

## Accept / convert / order audit

| Topic | Finding |
|-------|---------|
| Accept endpoint | **No dedicated accept API.** Frontend uses quote status update (`PATCH` quotes → `accepted`). Validated by `validate_transition` in quotes router. |
| Convert endpoint | `POST /api/v1/entities/orders/from-quote/{quote_id}` — creates **Order** (status `locked`), requires quote `priced` or `accepted`, requires `line_items` snapshot, duplicate order guard (409). |
| Accept side effects | Status change only — **no Order** from accept alone. |
| Convert side effects | Creates Order row + snapshot; document snapshot reference optional; **does not** create ExecutionPlan in same handler (execution is separate). |
| IV3 priced draft gap | IV3 manual pricing keeps `status=draft` — canonical convert path rejects (`quote_not_priced`). Accept path would need guarded draft→accepted transition. |
| Existing guard | `GET /api/v1/entities/orders/quote-acceptance-guard/{quote_id}` — order conversion eligibility (priced/sent/accepted + document snapshot). |
| IV3 risk | Using normal convert on IV3 draft would fail or bypass IV3 guards; accept+convert must be separate guarded IV3 builds. |

## Accept vs convert decision

Treated as **separate readiness tracks**:

- **accept_readiness** — priced draft + snapshot + owner decision + no order/execution
- **convert_readiness** — additionally requires accepted quote + order snapshot contracts (always blocked in this build)

This build sets:

```text
can_accept_now = false
can_convert_now = false
accept_action_enabled = false
convert_action_enabled = false
```

## Backend

### Service

`backend/services/intake_v3_priced_draft_accept_convert_readiness_service.py`

### Endpoints (read-only)

- `GET /api/v1/intake-v3/quotes/{quote_id}/accept-convert-readiness`
- `GET /api/v1/intake-v3/workspaces/{workspace_id}/accept-convert-readiness`

### Tests

`backend/tests/test_intake_v3_priced_draft_accept_convert_readiness.py`

## Frontend

- `IntakeV3AcceptConvertReadinessPanel.tsx`
- API: `fetchIntakeV3AcceptConvertReadinessByWorkspace/ByQuote`
- Flow step: **Accept/Convert Readiness**
- Quotes badges: **Accept blocked**, **Convert blocked** for IV3
- Guidance: IV3-specific copy via `getQuoteCommercialGuidance(status, quote)`

## Commands + results

```text
# Targeted backend
25 passed (accept/convert readiness + pricing completion + draft review)

# Backend regression
173 passed

# Frontend targeted
152 passed (IntakeV3App + flowState + guard + guidance)
```

## Boundary

- No accept / convert / Order / Execution / Inventory mutations
- No CostEngine / pricing formula / TVA / markup / DB schema changes
- No commit / push / ZIP

## Recommended next build

**INTAKE_V3_GUARDED_ACCEPT_FLOW** (accept only) — enable internal accept for IV3 priced draft with explicit confirmations; still no Order/Execution/Inventory.

Convert should remain a **separate** build after accept: `INTAKE_V3_GUARDED_CONVERT_TO_ORDER`.

## Recommended commit message

```text
feat(intake-v3): add priced draft accept/convert readiness audit and guards
```

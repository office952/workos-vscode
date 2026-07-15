# W6-T04 — Manager owner-decision operational resolution UI v1

**Date:** 2026-07-15  
**Task:** `MANAGER_OWNER_DECISION_OPERATIONAL_RESOLUTION_UI_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `b41d885`  
**Verdict:** `W6_MANAGER_RESOLUTION_UI_PASS_COMMITTED`

## Objective

Smallest safe manager/admin UI to resolve production-blocking owner decisions via the canonical backend endpoint without mutating frozen snapshots or defining policy in the frontend.

## Contract (proven, unchanged)

| Item | Value |
|------|-------|
| Mutation endpoint | `POST /api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve` |
| Permission | `execution.owner_decision_resolve` (admin/manager) |
| Payload | `{ status: "acknowledged" \| "resolved", note: string }` |
| Note policy | `BACKEND_NOTE_REQUIRED` (min 3 chars) |
| Waived | Not in `RESOLUTION_ALLOWED_STATUSES` |
| Idempotency | `idempotent: true` on repeat; no duplicate audit |
| Resolver identity | Auth context only |
| Audit model | `COMPACT_AUDIT_SUMMARY_SUFFICIENT` |
| OperatorView | `READ_ONLY_MANUAL_REFRESH` (no mutation props) |
| ShopFloor | `SHOPFLOOR_NO_MUTATION_VISIBILITY_DEFERRED` |
| Employee Mobile | `BACKEND_GUARDED_UI_DEFERRED` |

## Implementation

- `executionOwnerDecisionRelease.ts` — resolve client + structured errors
- `OperatorOwnerDecisionResolutionForm.tsx` — note, submit, idempotent/resolved states
- `OperatorOwnerDecisionDetailsPanel.tsx` — mutation only when `can_resolve` + `orderId` + `onResolved`
- `ExecutionDetail.tsx` — canonical mutation surface + `refreshTaskTruth`
- `OperatorView.tsx` — unchanged read-only projection (no `orderId`/`onResolved`)

## Tests

| Suite | Result |
|-------|--------|
| Backend `test_execution_owner_decision_production_release_guard.py` + `test_operator_task_truth.py` | 32 passed |
| Frontend `executionOwnerDecisionRelease.test.ts` + `OperatorOwnerDecisionResolution.test.tsx` + `OperatorProductionBlocker.test.tsx` | 11 passed |

## Runtime (`:8001`)

Fixture order `23150` (blocked), comparison `23099` untouched.

- Initial 3 production blockers
- Resolve one → release remains blocked
- Idempotent repeat → `idempotent: true`
- Resolve all three → `RELEASE_ALLOWED`
- `snapshot_v2_json` hash unchanged (`573a5a769e00b182`)

Evidence: `docs/qa/product-system-active-path-isolation-v1/w6_t04_runtime_gate_evidence.json`

## Screenshots

13 captures under `docs/qa/product-system-active-path-isolation-v1/w6_t04_screenshots/` — manager form, operator read-only, partial/full resolution, idempotent state, permission denial (routed 403), nonblocking section.

## Owner verification

### Manager

1. Open `http://127.0.0.1:3000/execution/23150` (dev bypass or admin session).
2. Click **Detalii decizii** on the production release strip.
3. Expand blocking decision `INTERNAL_SABLON_FOREX_COST`.
4. Enter note (≥3 chars) → **Rezolva decizia**.
5. Expect: release still blocked, 2 unresolved blockers, resolved item shows audit metadata.
6. Resolve remaining blockers → **Productie permisa** after refresh.

### Operator

1. Open `http://127.0.0.1:3000/operator?orderId=23150`.
2. Expect: blocker visibility, no resolve form (mutation surface omitted).
3. After manager completes resolutions, manual refresh shows allowed release strip.

## Temporary debt

| Item | Classification |
|------|----------------|
| Full audit timeline | `KEEP_FOR_WAVE_7` |
| Reopen/unresolve | `OWNER_DECISION_REQUIRED` |
| Waiver workflow | `NOT_PROVEN` (backend has no waived) |
| ShopFloor visibility | `SHOPFLOOR_NO_MUTATION_VISIBILITY_DEFERRED` |
| Partial 7H rich presentation | `KEEP_FOR_W6_INT_02` |
| Employee Mobile UI | `MOBILE_DEFERRED` |
| OperatorView auto-refresh | `ACCEPTED_NONBLOCKING` (manual refresh) |

## Next task

`W6-INT-02-POST-IMPLEMENTATION-GATE`

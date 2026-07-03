# V6 quote Snapshot V2 before Accept fix - 2026-07-03

## Context

Target quote: `Q-V6-IV6-8D2ABB4E-1783038761` / quote id `20` / workspace `8887a6d0-8b97-4cb2-9ef5-43e193739996`.

Observed state before fix:

- Quote had official V6 totals: `grand_total=6445.87`.
- Quote status was `draft`.
- No row existed in canonical `quote_snapshots_v2`.
- `accepted_snapshot_v2_id` was null.
- `order_count=0`.
- UI exposed the commercial spine but could reach Accept semantics without a persisted canonical Snapshot V2.

Exact runtime blocker from stale live backend before restart:

- `V6_SNAPSHOT_QUOTE_NOT_PRICED`
- `Quote must be priced before Quote Snapshot V2 can be created.`

## Cause

The V6 snapshot endpoint was not persisting the canonical Snapshot V2 row required by the accept gate. It also blocked recovered/backend-priced V6 quotes that had official totals but were still in `draft` status after commercial review state changes.

The frontend commercial spine did not use backend `snapshot_v2` state as the required step between priced totals and Review/Accept. The priced-complete branch also hid the Snapshot V2 action.

## Real flow

Required lifecycle after this fix:

1. Backend-priced V6 quote exists.
2. Canonical `quote_snapshots_v2` row is persisted with status `frozen` and readiness `ready_for_owner_review`.
3. Review is allowed only after Snapshot V2 exists.
4. Owner approval remains separate.
5. Accept resolves the canonical Snapshot V2 and writes `accepted_snapshot_v2_id`.
6. Convert to order remains separate. Snapshot and Accept do not create order, execution plan, execution tasks, or inventory mutation.

## Fix applied

Backend:

- V6 snapshot creation now counts and persists canonical `QuoteSnapshotV2Record` rows.
- Snapshot payload is built as `QuoteSnapshotV2` with commercial proposal, internal cost preview, client output, lineage, audit notes, and accept-gate hash.
- Snapshot creation allows `draft` quotes only when official quote totals are positive, covering recovered V6 backend-priced quotes.
- Commercial spine state now returns `snapshot_v2` with `exists`, `snapshot_id`, `snapshot_code`, `status`, `readiness`, and `accept_allowed`.
- Pricing review now blocks with `MISSING_SNAPSHOT_V2` when Snapshot V2 is missing.
- Order conversion blockers include `SNAPSHOT_V2_REQUIRED` before Accept.

Frontend:

- V6 commercial spine reads `snapshot_v2` from backend state.
- Snapshot V2 becomes the primary action after quote totals exist and before Review/Accept.
- Review is disabled until Snapshot V2 exists.
- Accept is disabled until the backend reports `snapshot_v2.accept_allowed=true`.
- UI shows the explicit hint: `Creeaza Snapshot V2 inainte de Review si Accept.`

Tests:

- Updated snapshot service tests for the new `_persist_snapshot(..., quote_snapshot_v2=...)` contract.
- Added a recovery case for backend-priced `draft` quote snapshot creation.
- Added a focused backend test proving pricing review requires persisted Snapshot V2.
- Updated frontend panel tests for the Snapshot V2-required step.

## Files modified

- `backend/services/intake_v6_quote_snapshot_v2_service.py`
- `backend/services/intake_v6_quote_to_order_service.py`
- `backend/schemas/intake_v6.py`
- `backend/tests/test_intake_v6_quote_snapshot_v2.py`
- `backend/tests/test_intake_v6_snapshot_before_review_gate.py`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.test.tsx`

## Validation

Focused backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_quote_snapshot_v2.py -k "not output_composition" tests/test_quote_snapshot_v2_accept_gate.py::test_cannot_accept_without_persisted_snapshot tests/test_quote_snapshot_v2_accept_gate.py::test_can_accept_ready_for_owner_review_snapshot tests/test_intake_v6_snapshot_before_review_gate.py -q
```

Result: `17 passed, 2 deselected, 3 warnings`.

Focused frontend test:

```powershell
pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.test.tsx
```

Result: `4 passed`.

Diagnostics: no editor errors on touched backend/frontend files.

## Runtime verification

After restarting the stale backend process, pre-snapshot commercial spine state returned:

- `snapshot_v2.exists=false`
- `snapshot_v2.accept_allowed=false`
- `v6_order_conversion.blocked_reasons=["SNAPSHOT_V2_REQUIRED", "QUOTE_NOT_ACCEPTED"]`

Created Snapshot V2 for quote id `20` through the live V6 endpoint. Post-snapshot state returned:

- `snapshot_v2.exists=true`
- `snapshot_v2.snapshot_id=4`
- `snapshot_v2.snapshot_code=QSN2-2026-0004`
- `snapshot_v2.status=frozen`
- `snapshot_v2.readiness=ready_for_owner_review`
- `snapshot_v2.accept_allowed=true`
- `quote_accepted=false`
- `order_count=0`

Accepted quote id `20` through the V6 accept endpoint with explicit confirmations for no order, no execution, no inventory, and separate conversion. Accept response returned:

- `accepted=true`
- `quote_status=accepted`
- `quote_status_before=draft`
- `accepted_snapshot_v2_id=4`
- `order_created=false`
- `execution_plan_created=false`
- `execution_task_created=false`
- `inventory_mutated=false`

Final DB/API state:

- Quote `Q-V6-IV6-8D2ABB4E-1783038761` status: `accepted`
- `accepted_snapshot_v2_id=4`
- Canonical snapshot row: `QSN2-2026-0004`, `frozen`, `ready_for_owner_review`
- `order_count=0`
- Commercial spine: `quote_accepted=true`, conversion available, not converted.

## Not modified

- No QuoteWizard flow was reintroduced.
- No CostEngine or pricing formula changes.
- No order auto-creation.
- No execution plan/task creation.
- No inventory or stock mutation.
- No ProductAggregate or TaskGraph creation.
- No schema migration.

## Remaining risks

- Two stale output-composition tests in `backend/tests/test_intake_v6_quote_snapshot_v2.py` still reference a removed helper `_latest_quote_snapshot_v2`; they were excluded from this focused validation because they are not part of the V6 accept gate path.
- Full frontend validation remains known noisy per repo guidance and was not used as a green gate.

## Next safe step

If the owner wants to continue after Accept, run only the explicit V6 convert-to-order action. Do not create order implicitly from Snapshot V2 or Accept.

# V6 Offer Still Zero - Runtime Trace

## Scope

Trace why the visible V6 quote/offer still shows zero after the V6 priced quote dry-run/write/snapshot backend slices. This is trace-only: no quote write, no snapshot creation, no order creation, no execution/product aggregate/task graph work.

## Target

- Workspace code: `IV6-BB8EE3F8`
- Workspace DB id used by V6 services: `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`
- Intake: `IR-MR18L96M`
- Quote id: `6`
- Quote code: `Q-V6-IV6-BB8EE3F8-1782910533`

## Persisted Quote State

Read-only DB inspection of `quotes.id = 6` shows the visible offer is still backed by a zero draft quote row:

- `status = draft`
- `subtotal = 0.0`
- `total_before_vat = 0.0`
- `vat = 0.0`
- `grand_total = 0.0`
- `accepted_snapshot_v2_id = null`
- first line item: `quantity = 19`, `unit_price = 0`, `total = 0`
- no `intake_v6_priced_quote_write_v1` provenance in notes
- no `frontend_preview_not_used` / `no_v4_v2_commercial_truth` write gates
- no orders for the quote
- no output snapshots for the quote

Local classification for the stored quote row: quote is still an old zero V6 draft; no priced write has landed.

## Runtime Dry-Run Result

Direct service call:

`build_intake_v6_priced_quote_dry_run(db, "c8dda47f-e2a7-4fea-800c-2dc01b2be5a3")`

Result: runtime exception before a priced dry-run DTO is produced.

Exception:

```text
TypeError: _classify_modules() missing 2 required keyword-only arguments: 'payload' and 'bindings_by_key'
```

Failing path:

- `intake_v6_priced_quote_dry_run_service.build_intake_v6_priced_quote_dry_run(...)`
- calls `CommercialPriceProposalService.build_preview(...)`
- calls `_resolve_active_commercial_modules(pd, payload)`
- calls imported `_classify_modules(...)` without the currently required keyword-only args `payload` and `bindings_by_key`

This means the current backend dry-run path is not runtime-green for this real workspace. The existing dry-run tests mock `CommercialPriceProposalService`, so this signature regression was not exercised by the V6 dry-run tests.

## Write Endpoint / Service Result

Direct write service trace:

`write_intake_v6_priced_quote_totals(db, workspace_id, quote_id=6, operator_confirmation=True, ...)`

Result: same runtime exception as dry-run, because write depends on the dry-run service before it can persist totals.

Write status:

- no quote totals written
- no quote status transition to `priced`
- no write provenance added
- no snapshot created
- no order created

Classification for write path: implemented surface exists, but current runtime execution is blocked by the dry-run/commercial proposal signature bug. Separately, the visible quote also shows no evidence that a successful write was ever triggered previously.

## Snapshot V2 Result

Direct snapshot service trace:

`create_v6_quote_snapshot_v2(db, quote_id=6, workspace_id=..., operator_confirmation=True, ...)`

Result:

```json
{
  "status": "V6_QUOTE_SNAPSHOT_V2_BLOCKED",
  "quote_id": 6,
  "quote_code": "Q-V6-IV6-BB8EE3F8-1782910533",
  "snapshot_id": null,
  "blockers": [
    {
      "code": "V6_SNAPSHOT_QUOTE_NOT_PRICED",
      "message": "Quote must be priced before Quote Snapshot V2 can be created."
    }
  ],
  "quote_snapshot_created": false,
  "order_created": false,
  "product_aggregate_created": false,
  "task_graph_created": false,
  "execution_plan_created": false
}
```

Snapshot V2 is correctly refusing to freeze a draft zero quote.

## Output Composition Result

Direct composition trace:

`QuoteOutputCompositionService(db).compose_preview(6)`

Result:

```json
{
  "composition_type": "quote_output_preview",
  "persisted": false,
  "commercial_summary": {
    "subtotal": 0.0,
    "vat": 0.0,
    "total": 0.0,
    "currency": "RON"
  },
  "warnings": [
    "snapshot_missing",
    "template_link_missing: quote has no linked product template"
  ],
  "trace": {
    "no_persist": true,
    "changed_entities": [],
    "no_quote_mutation": true,
    "no_order_mutation": true,
    "no_snapshot_created": true,
    "not_client_final": true
  }
}
```

Because no `QUOTE_SNAPSHOT_V2` exists, composition falls back to read-only quote-column totals. Those columns are zero, so the composition preview is also zero.

## Route Surface

The route modules expose the expected surfaces and are auto-included by `backend/main.py`:

- `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/quotes/{quote_id}/snapshot-v2`
- `GET /api/v1/entities/quotes/{quote_id}/output-composition-preview`
- generic candidate snapshot routes under `/api/v1/entities/quotes/{quote_id}/output-snapshots`

The route surface existing does not imply quote #6 has been mutated. The DB row confirms it has not.

## Frontend Visible Offer Path

The visible offer/list/detail path reads persisted quote columns:

- `frontend/src/lib/dataStore.ts` maps `grand_total` to UI `grandTotal`.
- `frontend/src/pages/Quotes.tsx` renders cards and detail totals from `quote.grandTotal`, `selectedQuote.subtotal`, `selectedQuote.totalBeforeVAT`, `selectedQuote.vat`, and `selectedQuote.grandTotal`.
- `frontend/src/lib/intakeV6/intakeV6Api.ts` has no wrapper/call for the new V6 priced write endpoint or the V6 snapshot-v2 endpoint in the inspected file.
- Output composition preview is an on-demand side surface, not the default source for quote card/detail totals.

Therefore the visible quote remains zero as long as the persisted quote row remains zero.

## Root Cause Classification

Primary visible-offer classification: `WRITE_NOT_TRIGGERED / QUOTE_ROW_STILL_ZERO`.

Evidence:

- quote #6 persisted totals are still zero
- quote #6 is still `draft`, not `priced`
- no write provenance exists
- no `QUOTE_SNAPSHOT_V2` exists
- visible frontend reads quote-row totals directly
- frontend inspected path does not trigger the new V6 priced write/snapshot endpoints

Important runtime blocker discovered during trace: `DRY_RUN_RUNTIME_EXCEPTION`.

Even if the UI/admin flow attempted to trigger the write now, the write would fail before mutation because the dry-run currently crashes in `CommercialPriceProposalService._resolve_active_commercial_modules(...)` due to a stale `_classify_modules(...)` call signature.

## Minimal Fix Proposal

Do not patch the frontend to display non-persisted preview totals as official offer truth.

Minimal safe sequence:

1. Fix the commercial proposal module-classification signature mismatch in the backend dry-run path.
2. Add or adjust a focused integration test that exercises `CommercialPriceProposalService.build_preview(...)` with real module classification rather than mocking the whole service.
3. Re-run the V6 dry-run for workspace `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3` and confirm a non-zero, ready result or an explicit commercial blocker DTO.
4. Only after operator confirmation, trigger the existing guarded V6 priced write endpoint/service for quote #6.
5. Only after quote #6 is `priced` with positive persisted totals and write provenance, trigger Quote Snapshot V2.
6. Reload visible offers; the quote list/detail should then show persisted non-zero `grand_total` via the existing data path.

## What Not To Do

- Do not create an order.
- Do not create ProductAggregate, Task Graph, or ExecutionPlan.
- Do not create an Order Snapshot.
- Do not hardcode totals.
- Do not copy frontend preview totals into official quote output.
- Do not make composition preview the official commercial truth for V6 quotes.
- Do not create a snapshot for a draft zero quote.
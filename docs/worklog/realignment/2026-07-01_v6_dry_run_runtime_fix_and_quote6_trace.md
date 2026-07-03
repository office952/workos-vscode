# V6 Dry-Run Runtime Fix and Quote #6 Trace

## Scope

Fix the real V6 dry-run runtime crash, prove it with a runtime-shaped backend test, then trace quote #6 write eligibility. This slice did not add new product features.

## Target

- Workspace DB id: `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`
- Workspace code: `IV6-BB8EE3F8`
- Quote id: `6`
- Quote code: `Q-V6-IV6-BB8EE3F8-1782910533`

## Crash Reproduction

Before the fix, the real dry-run call crashed:

```text
build_intake_v6_priced_quote_dry_run(db, "c8dda47f-e2a7-4fea-800c-2dc01b2be5a3")
```

Traceback:

```text
services/intake_v6_priced_quote_dry_run_service.py:145
  CommercialPriceProposalService(db).build_preview(...)

services/commercial_price_proposal_service.py:441
  active_modules = _resolve_active_commercial_modules(pd, payload)

services/commercial_price_proposal_service.py:169
  selected, optional, inactive = _classify_modules(...)

TypeError: _classify_modules() missing 2 required keyword-only arguments: 'payload' and 'bindings_by_key'
```

Expected `_classify_modules` signature:

```text
_classify_modules(
  modules,
  *,
  payload,
  finish,
  quote_geometry,
  svg_source,
  client,
  analysis_ready,
  bindings_by_key,
)
```

Actual stale call passed only `modules`, `finish`, `quote_geometry`, `svg_source`, `client`, and `analysis_ready`.

## Classifier Call-Site Audit

| Caller | File/function | Args passed before fix | Args required | Runtime-safe before fix? | Used by V6 dry-run? | Fix needed |
| --- | --- | --- | --- | --- | --- | --- |
| ProductDefinition preview | `services/product_definition_builder_service.py` / `ProductDefinitionBuilderService.build_preview` | `modules`, `payload`, `finish`, `quote_geometry`, `svg_source`, `client`, `analysis_ready`, `bindings_by_key` | same | yes | indirectly | no |
| Commercial proposal | `services/commercial_price_proposal_service.py` / `_resolve_active_commercial_modules` | missing `payload`, missing `bindings_by_key` | same | no | yes | yes |
| Estimated internal cost | `services/estimated_internal_cost_service.py` / `_resolve_active_modules` | missing `payload`, missing `bindings_by_key` | same | no | yes, as dry-run internal cost trace path | yes |

Bindings source used for the fix: `IntakeV6ModularFormContractService().get_for_template(pd.template_code).field_bindings`, keyed by `canonical_key`, matching the ProductDefinitionBuilder pattern.

## Files Changed

- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/tests/test_intake_v6_priced_quote_dry_run_runtime.py`
- `docs/worklog/realignment/2026-07-01_v6_dry_run_runtime_fix_and_quote6_trace.md`

## Root Cause

The shared `_classify_modules` helper had evolved to require the full backend payload and a `bindings_by_key` map so required field checks can resolve canonical fields through the modular form contract. Two read-only pricing/cost services still called the older signature.

The existing V6 dry-run unit tests mocked `CommercialPriceProposalService`, so they did not exercise the real classifier call path.

## Fix

Both stale call sites now build the backend field-binding map from the existing Intake V6 modular form contract and pass the real payload to `_classify_modules`:

- commercial proposal active module resolution
- estimated internal cost active module resolution

No totals were hardcoded, no V4/V2 quote builder was used, and no frontend preview values were copied.

## Tests Added

New runtime-shaped test file:

`backend/tests/test_intake_v6_priced_quote_dry_run_runtime.py`

Coverage:

- real V6 dry-run exercises the real `CommercialPriceProposalService` classifier path without TypeError;
- missing/insufficient payload returns `V6_PRICED_DRY_RUN_BLOCKED`, not a raw classifier crash;
- valid pricing input path returns either `V6_PRICED_DRY_RUN_READY` or a structured `V6_PRICED_DRY_RUN_BLOCKED` result;
- dry-run remains read-only and reports no quote/snapshot/order mutation.

## Tests Run

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_dry_run_runtime.py -q
```

Result: `3 passed, 3 warnings in 1.01s`.

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_dry_run_runtime.py tests/test_intake_v6_priced_quote_dry_run.py tests/test_intake_v6_priced_quote_write.py tests/test_intake_v6_quote_snapshot_v2.py tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Result: `50 passed, 3 warnings in 1.44s`.

Diagnostics:

- `commercial_price_proposal_service.py`: no errors
- `estimated_internal_cost_service.py`: no errors
- `test_intake_v6_priced_quote_dry_run_runtime.py`: no errors

## Real Dry-Run After Fix

Real workspace dry-run now returns a structured DTO and no longer raises `TypeError`.

Result summary:

```json
{
  "pricing_status": "V6_PRICED_DRY_RUN_BLOCKED",
  "pricing_source": "intake_v6_backend_priced_dry_run",
  "commercial_totals": {
    "subtotal_net": null,
    "vat_rate": 21.0,
    "vat_amount": null,
    "total_gross": null,
    "currency": "RON"
  },
  "line_item_count": 9,
  "dry_run_only": true
}
```

Blockers:

- `COMMERCIAL_BASIS_UNKNOWN`: commercial basis unknown for `debitare_spate`.
- `DEBITARE_SPATE_BASIS_ML_VS_M2`: owner must decide commercial basis ml vs m2 for back CNC.
- `SABLON_FOREX_COMMERCIAL_PRICE`: Forex sablon selected but separate commercial price not owner-approved.
- `AMBALARE_COMMERCIAL_RULE`: commercial packaging rule not yet owner-defined.
- `MONTAJ_COMMERCIAL_RULE`: site mounting commercial rule is future/optional, not in Step 7G numeric scope.
- `V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY`: commercial proposal status is blocked.
- `V6_PRICED_DRY_RUN_ZERO_TOTAL`: backend dry-run produced no positive official total.

Conclusion: runtime crash fixed; quote write must remain blocked until commercial rule/owner blockers are resolved.

## Quote #6 Before/After

Before write trace:

```json
{
  "status": "draft",
  "subtotal": 0.0,
  "total_before_vat": 0.0,
  "vat": 0.0,
  "grand_total": 0.0,
  "accepted_snapshot_v2_id": null,
  "notes_has_write_trace": false
}
```

After guarded write trace and rollback/no-op:

```json
{
  "status": "draft",
  "subtotal": 0.0,
  "total_before_vat": 0.0,
  "vat": 0.0,
  "grand_total": 0.0,
  "accepted_snapshot_v2_id": null,
  "notes_has_write_trace": false
}
```

No order rows and no output snapshot rows exist for quote #6.

## Write Result

Guarded write service was traced and blocked before mutation because the dry-run is structured-blocked:

```json
{
  "status": "V6_PRICED_QUOTE_WRITE_BLOCKED",
  "quote_id": 6,
  "commercial_totals": {
    "subtotal_net": null,
    "vat_rate": 21.0,
    "vat_amount": null,
    "total_gross": null,
    "currency": "RON"
  },
  "line_item_count": 9,
  "can_create_quote_snapshot": false,
  "can_accept_quote": false
}
```

Primary blocker added by write service:

- `V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED`

The dry-run blockers were also propagated. Quote #6 was not mutated.

## Snapshot Result

Snapshot V2 was checked after the blocked write trace and correctly remained blocked:

```json
{
  "status": "V6_QUOTE_SNAPSHOT_V2_BLOCKED",
  "snapshot_id": null,
  "blockers": [
    {
      "code": "V6_SNAPSHOT_QUOTE_NOT_PRICED",
      "message": "Quote must be priced before Quote Snapshot V2 can be created."
    }
  ],
  "quote_snapshot_created": false,
  "can_accept_quote": false,
  "can_create_order": false
}
```

## Output Composition Result

Composition still uses quote columns because no `QUOTE_SNAPSHOT_V2` exists:

```json
{
  "composition_type": "quote_output_preview",
  "commercial_summary": {
    "subtotal": 0.0,
    "vat": 0.0,
    "total": 0.0,
    "currency": "RON"
  },
  "warnings": [
    "snapshot_missing",
    "template_link_missing: quote has no linked product template"
  ]
}
```

It is still zero because the persisted quote is still zero and no snapshot exists.

## Frontend Path Note

Frontend source search found `endpoint_call_matches=0` for:

- `priced-quote/write`
- `snapshot-v2`

Visible quote totals are mapped from DB quote columns:

- `frontend/src/lib/dataStore.ts`: `mapQuoteFromDB`, `grandTotal: Number(e.grand_total ?? 0)`.
- `frontend/src/pages/Quotes.tsx`: quote card renders `formatQuoteMoney(quote.grandTotal, currency)`.
- `frontend/src/pages/Quotes.tsx`: quote detail renders selected quote subtotal/grand total.
- `QuoteOutputCompositionPreview` is present as a separate preview panel, not the source for the quote card total.

Frontend does not currently provide an operator action to call the V6 priced write or V6 Snapshot V2 endpoint.

## What Did Not Change

- No DB/schema migration.
- No hardcoded totals.
- No fake totals.
- No frontend preview copied.
- No V2/V4 commercial truth.
- No quote write bypass.
- No write guard bypass.
- No quote #6 mutation.
- No order creation.
- No Order Snapshot.
- No ProductAggregate.
- No Task Graph.
- No ExecutionPlan.
- No frontend redesign.
- No Employee Mobile.

## Recommendation

Recommendation: `B. MORE_BACKEND_RUNTIME_FIXES`.

Reason: the raw runtime crash is fixed, but the real V6 dry-run for quote #6's workspace is still commercially blocked by owner-rule gaps and produces no positive official total. The backend must resolve those commercial rule/owner-decision blockers before quote #6 can be safely written, snapshotted, or exposed as a non-zero official offer.

Recommended next safe slice: define/resolve the remaining commercial proposal blockers for `debitare_spate`, Forex mounting template pricing, packaging, and mounting commercial rules, then rerun the same dry-run/write trace. Do not proceed to frontend write/snapshot action until the backend dry-run returns `V6_PRICED_DRY_RUN_READY` with positive totals.
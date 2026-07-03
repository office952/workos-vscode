# 2026-07-01 V6 Priced Quote Write Small Slice

Status: implemented backend-only guarded write of official V6 quote totals to eligible existing unpriced V6 draft quotes.

## Pre-Edit Write Eligibility Audit

| Item | File/function/API | Current behavior | Can be used for V6 write? | Risk | Planned action |
| --- | --- | --- | --- | --- | --- |
| V6 dry-run service | `backend/services/intake_v6_priced_quote_dry_run_service.py` / `build_intake_v6_priced_quote_dry_run` | Recomputes backend V6 pricing input, commercial proposal, totals, line items; no persistence | Yes, as authoritative source | Low if recomputed server-side | Call it from write service; never trust client totals except mismatch guard. |
| V6 zero guard | `backend/services/intake_v6_commercial_quote_service.py` / `_block_v6_zero_commercial_truth` | Blocks legacy zero V6 draft payload before persistence | Yes, as defense-in-depth/reference | Low | Keep unchanged; write service independently requires positive totals. |
| Current quote model/columns | `backend/models/quotes.py` | Has `subtotal`, `discount`, `total_before_vat`, `vat`, `grand_total`, `margin_pct`, `line_items`, `notes`, `status`, `accepted_snapshot_v2_id` | Yes | Medium: no dedicated pricing provenance column | Write only allowed fields and store provenance in notes. |
| Quote notes JSON handling | `notes` column + V6 linkage notes | Existing V6 drafts store `intake_v6_linkage_v1` | Yes | Medium: invalid JSON possible | Preserve invalid raw notes under `legacy_notes_raw`; do not destroy. |
| Line items JSON handling | `line_items` column | Existing V6 zero draft has JSON array with zero line prices | Yes | Medium: multiple historical shapes exist | Write minimal dry-run-derived JSON array; no V4 zero shape fallback. |
| Quote status handling | `quotes.status` | Existing statuses include draft/priced/accepted and terminal states | Yes | Medium: overwrite risk | Update only draft/zero V6 quotes; block accepted/converted/terminal. |
| Existing quote price endpoint | `backend/routers/quotes.py` / `/entities/quotes/price` and `/{quote_id}/price` | Writes/creates priced quotes through QuoteOrchestrator | No for this slice | High: generic CostEngine/orchestrator semantics, not V6 dry-run source | Reference only; do not call. |
| Quote output composition service | `backend/services/quote_output_composition_service.py` | Read-only mirror of quote columns | Yes after write | Low/medium: mirrors zero before write | Leave unchanged; after write it will display persisted totals. |
| Quote snapshot router | `backend/routers/quote_output_snapshots.py` | Creates output snapshot candidates but does not mutate Quote/Order | No write now; detection only | Medium if snapshot already exists | Block quote overwrite if any output snapshot exists. |
| V4 draft builder | `backend/services/intake_v4_commercial_quote_service.py` / `build_v4_quote_draft_payload` | Creates legacy zero placeholders | No | Critical for V6 commercial truth | Forbidden in V6 write service. |

Pre-edit eligibility conclusions:

- Existing V6 zero quote can be updated safely only if it is V6-linked, workspace-matched, zero-valued, unaccepted/unconverted, has no output snapshots, has no order, and operator explicitly confirms.
- V6 draft/unpriced markers: `intake_code=IV6-{workspace_id}`, `intake_v6_linkage_v1.source_module=intake_v6`, zero quote totals, and draft/non-terminal status.
- Same workspace linkage proof: `quote.intake_code == IV6-{workspace_id}` or `intake_v6_linkage_v1.source_workspace_id == workspace_id`.
- Overwrite blockers: positive totals, status accepted/converted/terminal, any output snapshot, `accepted_snapshot_v2_id`, any order linked by `orders.quote_id`, workspace mismatch, non-V6 linkage, dry-run blocked, zero dry-run, missing line items, forbidden source, total/hash mismatch, missing operator confirmation.

## Files Changed

- `backend/services/intake_v6_priced_quote_write_service.py`
- `backend/schemas/intake_v6.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/tests/test_intake_v6_priced_quote_write.py`
- `docs/architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_v6_priced_quote_write_small_slice.md`

## Service Behavior

Service function:

- `write_intake_v6_priced_quote_totals(db, workspace_id, quote_id, expected_total_gross, expected_pricing_hash=None, operator_confirmation=True, operator_identifier=None)`

Behavior:

- Recomputes dry-run server-side with `pricing_mode="write_priced_quote"`.
- Requires backend V6 dry-run source.
- Requires positive totals and line items.
- Validates expected total and optional hash.
- Loads target quote and verifies V6/workspace linkage.
- Blocks already priced, snapshotted, accepted/converted, or ordered quote.
- Updates only quote totals, status, line items, and notes provenance.
- Returns `V6_PRICED_QUOTE_WRITTEN` or `V6_PRICED_QUOTE_WRITE_BLOCKED`.

## Endpoint Behavior

Endpoint:

- `POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`

Request:

```json
{
  "quote_id": 6,
  "expected_total_gross": 1190.0,
  "expected_pricing_hash": null,
  "operator_confirmation": true
}
```

Response shape:

- `status`
- `quote_id`
- `quote_code`
- `commercial_totals`
- `line_items`
- `pricing_trace` on success
- `blockers`
- `warnings`
- `can_create_quote_snapshot`
- `can_accept_quote=false`
- `quote_snapshot_created=false`
- `order_created=false`

## Tests Run

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_write.py -q
```

Result: `20 passed, 3 warnings in 0.75s`.

Covered:

- Successful write updates existing eligible V6 unpriced quote with positive totals.
- Line items are mapped from dry-run commercial lines.
- Notes are enriched while preserving existing notes.
- Snapshot creation becomes possible but acceptance stays false.
- Dry-run blocked prevents write.
- Zero dry-run prevents write.
- Expected total mismatch prevents write.
- Non-V6 quote prevents write.
- Workspace mismatch prevents write.
- Already priced quote prevents write.
- Snapshot exists prevents write.
- Accepted/order-linked quote prevents write.
- Missing operator confirmation prevents write.
- V4/V2 pricing source prevents write.
- Missing line items prevents write.
- Invalid notes are preserved safely.
- Static source checks prove no V4 draft builder, no quote creation, no snapshot/order/execution creation.

Additional validation and regression commands are recorded after final run in the assistant report.

Combined focused regression run:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_write.py tests/test_intake_v6_priced_quote_dry_run.py tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Result: `32 passed, 3 warnings in 0.83s`.

## Static Boundary Checks

Static boundary checks were run against the new write service and existing dry-run service.

Write service command:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; $tokens = @('build_v4_quote_draft_payload','intake_v4_commercial_quote_service','QuoteOrchestrator','ProductAggregate','ExecutionPlan','offerModel','create_snapshot(','create_order(','QuoteOutputSnapshotService','quote_output_snapshots.create'); $matches = Select-String -Path .\services\intake_v6_priced_quote_write_service.py -Pattern $tokens -SimpleMatch; if ($matches) { $matches | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }; exit 1 } else { 'PASS: no forbidden V6 write service tokens found' }
```

Result: `PASS: no forbidden V6 write service tokens found`.

Dry-run service command:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; $tokens = @('QuotesService','build_v4_quote_draft_payload','intake_v4_commercial_quote_service','QuoteOrchestrator','QuoteOutputSnapshotService','ProductAggregate','ExecutionPlan','offerModel','db.add(','db.commit(','create_order(','update_quote('); $matches = Select-String -Path .\services\intake_v6_priced_quote_dry_run_service.py -Pattern $tokens -SimpleMatch; if ($matches) { $matches | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }; exit 1 } else { 'PASS: dry-run service still has no quote write/snapshot/order tokens' }
```

Result: `PASS: dry-run service still has no quote write/snapshot/order tokens`.

Expected absent in write service:

- `build_v4_quote_draft_payload`
- `intake_v4_commercial_quote_service`
- `QuoteOrchestrator`
- snapshot creation calls
- order creation calls
- `ProductAggregate`
- `ExecutionPlan`
- `offerModel`

Expected absent in dry-run service:

- quote update/create/write calls
- snapshot/order creation
- V4 draft builder

Result: PASS.

## What Did Not Change

- No DB/schema migration.
- No quote creation.
- No Quote Snapshot runtime.
- No Order Snapshot.
- No ProductAggregate.
- No Task Graph.
- No ExecutionPlan.
- No order creation.
- No quote acceptance change.
- No frontend UI work.
- No frontend preview copied into quote totals.
- No V2/V4 commercial truth for V6.
- No Employee Mobile.

## Known Limitations

- Create-new-priced-quote fallback is not implemented.
- Frontend has no write button/action in this slice.
- Quote Snapshot V2 still must be designed/implemented separately.
- The optional pricing hash is computed from current dry-run response; no persisted dry-run id exists yet.
- `vat` is written as VAT amount for this V6 path to match output composition expectations.
- `margin_pct` is set to `0.0` because this commercial proposal path is unit-rule based and does not yet produce a meaningful persisted margin percentage.

## Recommended Next Safe Slice

Recommendation: `A. QUOTE_SNAPSHOT_V2_DESIGN_NEXT`.

Now that official V6 quote totals can be written, the next safe step is Quote Snapshot V2 design for freezing client output. Do not proceed directly to Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje, Angajati, ExecutionReality, or Employee Mobile.

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
2. Current roadmap phase: `Phase 6 — V6 priced quote write before Quote Snapshot`
3. Roadmap status: `NEXT / V6 priced quote write small slice`
4. Why this belongs here: dry-run exists and is backend-authoritative; official quote totals can now be persisted safely; snapshot/order remain blocked; prevents V2/V4 and frontend preview from becoming commercial truth.
5. What this task must NOT unlock: Quote Snapshot runtime unless separate GO, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate: PASS.
7. Roadmap implementation progress: `23/100%`.
8. Roadmap alignment score: `95/100%`.
9. Cat sunt in directia stabilita: `95/100%`.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.

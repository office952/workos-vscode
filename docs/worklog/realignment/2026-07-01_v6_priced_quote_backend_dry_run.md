# 2026-07-01 V6 Priced Quote Backend Dry-Run

Status: implemented backend-only dry-run with focused tests.

## Owner Clarification

V4 was copied forward into V6 up to calculator/draft flow. V6 now has the real commercial calculation path, while V4 remains incomplete for the current pricing path. The zero issue happened because V6 calculated non-zero values but quote handoff fell back into the incomplete legacy V4 draft builder, which wrote zero placeholders.

V4 is not valid commercial truth for V6. V4 was not deleted in this slice. V6 dry-run uses V6 backend pricing input/material breakdown/commercial calculation and avoids the V4 draft payload writer.

## Pre-Edit Source Map

| Source service/function | Input data | Output data | Has non-zero values? | Is backend-authoritative? | Can be used for dry-run? | Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `build_v6_pricing_input_preview` | V6 workspace payload parsed server-side | Quote input payload, readiness, production counts, finish summary | Yes when workspace is ready | Yes as backend-derived V6 input preview | Yes | Medium | It delegates through the V6 namespace while old V4 draft writer remains forbidden for commercial truth. |
| `get_material_breakdown_for_workspace` | V6 workspace payload and registry material pricing | Material/internal cost trace and totals | Yes for known workspace, e.g. material/internal cost trace | Yes for internal cost trace | Yes, trace only | Medium | Internal cost is not official commercial total. Used as trace, not quote price writer. |
| `CommercialPriceProposalService.build_preview` | Template code plus backend V6 quote input payload | Commercial lines, subtotal, blockers, owner decisions, provenance | Yes when rules and quantities produce subtotals | Yes as read-only backend commercial proposal | Yes | Medium | Does not write, does not use CostEngine/QuoteOrchestrator/hourly pricing. Blocks if proposal is not ready. |
| Fast guard in `intake_v6_commercial_quote_service` | Generated V6 quote payload before persistence | Blocks zero placeholder quote creation | N/A | Yes as safety guard | No for pricing | Low | Prevents V6 from using legacy zero placeholder quote as commercial truth. |
| `build_v4_quote_draft_payload` | Legacy V4-compatible payload | Zero quote totals and zero line item totals | No | No for V6 commercial truth | No | High | Explicitly forbidden for V6 priced dry-run. |
| Quote pricing router / `QuoteOrchestrator` | Quote pricing request payload | Persisted quote totals on pricing endpoints | Can produce non-zero | Yes for canonical quote pricing | Not used now | Medium | Existing write semantics are outside dry-run scope. |

## Selected Pricing Source

Selected source: backend V6 pricing input preview + read-only `CommercialPriceProposalService`, with backend material breakdown as internal trace.

Reason: this is the safest existing backend-only commercial calculation surface. It does not call the V4 draft quote builder, does not persist quotes, does not create snapshots/orders, and is already tested as read-only. It computes line subtotals from server-side rules and V6-derived quote input, then the dry-run applies backend company VAT to produce gross total.

## Files Changed

- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/tests/test_intake_v6_priced_quote_dry_run.py`
- `docs/architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_v6_priced_quote_backend_dry_run.md`

## Endpoint And Service Behavior

Service:

- `build_intake_v6_priced_quote_dry_run(db, workspace_id, pricing_mode="dry_run")`

Endpoint:

- `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`

Behavior:

- Reads V6 workspace payload.
- Builds V6 backend pricing input preview.
- Reads V6 material breakdown as internal cost trace.
- Builds read-only CommercialPriceProposal preview from V6 quote input.
- Computes `subtotal_net`, `vat_rate`, `vat_amount`, and `total_gross` only when backend commercial subtotal is positive and proposal is ready.
- Returns `V6_PRICED_DRY_RUN_BLOCKED` instead of ready zero when totals are missing or zero.
- Always returns `can_write_quote_totals=false`, `can_create_quote_snapshot=false`, and `dry_run_only=true`.

## Tests Run

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_dry_run.py -q
```

Result: `8 passed, 3 warnings in 0.70s`.

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Result: `4 passed, 3 warnings in 0.62s`.

Covered:

- Dry-run returns non-zero totals when backend pricing source is available.
- Dry-run does not create or update quote.
- Dry-run does not call V4 draft quote builder.
- Dry-run has `can_write_quote_totals=false`.
- Dry-run has `can_create_quote_snapshot=false`.
- Dry-run blocks zero totals instead of returning ready zero.
- Missing pricing source returns `V6_PRICED_DRY_RUN_BLOCKED`.
- Dry-run does not copy frontend preview totals.
- Current V6 zero quote guard still passes.

Legacy V4 full endpoint tests were not run in this slice because the focused V4 non-regression remains covered by `test_intake_v6_zero_quote_fast_guard.py` and broad integration tests are costlier.

Optional legacy V4 integration check was attempted after the focused tests:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_commercial_quote.py -q
```

Result: `6 failed, 20 warnings in 3.09s`. All failures occurred before the changed V6 dry-run path while seeding/creating V4 workspaces, with `product_system_template_not_found` for `TPL-VOLUMETRIC-LETTERS_v2`. This is recorded as an environment/fixture blocker for the optional legacy integration file, not as a V6 dry-run regression signal.

## Static Boundary Checks

Static boundary checks were run against `backend/services/intake_v6_priced_quote_dry_run_service.py`.

Command:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; $tokens = @('QuotesService','QuoteOrchestrator','build_v4_quote_draft_payload','intake_v4_commercial_quote_service','ProductAggregate','ExecutionPlan','quote_output_snapshots','offerModel','await quotes_service','db.add(','db.commit(','insert(','create_order(','update_quote('); $matches = Select-String -Path .\services\intake_v6_priced_quote_dry_run_service.py -Pattern $tokens -SimpleMatch; if ($matches) { $matches | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }; exit 1 } else { 'PASS: no forbidden dry-run call/import tokens found' }
```

Expected absent:

- `QuotesService.create`
- `QuotesService.update`
- quote total update/write
- quote insert
- snapshot create
- order create
- ProductAggregate
- ExecutionPlan
- `build_v4_quote_draft_payload`
- frontend preview import
- `offerModel`

Result: PASS.

## What Did Not Change

- No DB/schema migration.
- No quote creation.
- No quote total write.
- No quote update.
- No Quote Snapshot.
- No Order Snapshot.
- No ProductAggregate.
- No Task Graph.
- No ExecutionPlan.
- No frontend preview copied into quote totals.
- No V2/V4 commercial truth for V6.
- No V2/V4 delete/purge/refactor.
- No UI badge sweep.
- No Employee Mobile.

## Known Limitations

- The dry-run blocks if `CommercialPriceProposalService` reports partial/blocked status even when some line subtotals exist.
- It does not persist a priced quote.
- It does not freeze Quote Snapshot V2.
- It does not solve owner-decision commercial gaps; those remain blockers in the dry-run response.

## Recommended Next Safe Slice

Recommendation: `A. V6_PRICED_QUOTE_WRITE_DESIGN_NEXT`.

Design the write path before implementing it. The write path must prove that backend dry-run/pricing output is stable, reviewed, positive, and traceable before quote totals are written.

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
2. Current roadmap phase: `Phase 3 / Phase 6 bridge — backend priced dry-run before quote write`
3. Roadmap status: `NEXT / V6 backend priced quote dry-run`
4. Why this belongs here: V6 no longer may use the V4 zero quote builder; backend-authoritative commercial totals are required before quote write; official price stays out of Product Truth; quote/snapshot/order remain locked until pricing is valid.
5. What this task must NOT unlock: direct quote total write, Quote Snapshot runtime, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate: PASS.
7. Roadmap implementation progress: `20/100%`.
8. Roadmap alignment score: `92/100%`.
9. Cat sunt in directia stabilita: `92/100%`.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.

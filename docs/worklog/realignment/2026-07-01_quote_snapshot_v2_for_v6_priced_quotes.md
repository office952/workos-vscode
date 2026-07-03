# 2026-07-01 Quote Snapshot V2 for V6 Priced Quotes

Status: implemented backend Quote Snapshot V2 creation for already backend-priced V6 quotes, with focused tests and static boundary checks.

## Pre-Edit Snapshot Audit

| Surface | File/function/API | Current behavior | Creates snapshot? | Reads snapshot? | Snapshot payload shape | Uses quote totals? | Uses line_items? | V6-compatible? | Risk | Planned action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QuoteOutputSnapshot model | `backend/models/quote_output_snapshots.py` | Stores snapshot metadata, JSON text payloads, hash, status/version | N/A | N/A | Flexible text JSON columns | Can store | Can store | Yes | Low; no dedicated V2 schema | Reuse table; no migration. |
| Generic snapshot service | `backend/services/quote_output_snapshot_service.py` / `create_snapshot` | Creates candidate from live composition preview | Yes | Yes | Composition candidate | Yes, via composition | Indirect | Partially | Medium: live preview source, not V6 write provenance | Do not use as V6 authoritative creator. |
| Snapshot router | `backend/routers/quote_output_snapshots.py` | Generic candidate CRUD/lifecycle/export | Yes | Yes | Candidate DTO | Yes | Indirect | Partially | Medium if mistaken for V6 official snapshot | Leave unchanged. |
| Composition service | `backend/services/quote_output_composition_service.py` | Mirrors quote columns and output blocks | No | No before slice | Preview DTO | Yes | Template lookup only | Yes after priced write | Medium: did not prefer frozen snapshot | Add read-only latest V2 preference and missing warning. |
| Composition router | `backend/routers/quote_output_composition.py` | Returns composition preview/export | No | Via service | Preview DTO | Yes | Via service | Yes | Low | Service-level change only. |
| Quotes model/status flows | `backend/models/quotes.py`, quote routers | Holds persisted totals/status/line_items/notes | No | accepted snapshot field exists separately | Quote columns | Yes | Yes | Yes | Medium: accepted/ordered states must block | New V6 service validates status/totals. |
| Orders model | `backend/models/orders.py` | Links orders to quote_id | No | Read for guard | N/A | N/A | N/A | Yes | High if snapshot after order exists | Block if any order linked. |
| V6 write service | `backend/services/intake_v6_priced_quote_write_service.py` | Writes official totals and provenance only | No | Blocks existing snapshots | Notes provenance | Writes totals | Writes line_items | Yes | Low after tests | Require its provenance for snapshot. |
| V6 dry-run service | `backend/services/intake_v6_priced_quote_dry_run_service.py` | Read-only commercial computation | No | No | Dry-run DTO | Computes only | Computes only | Yes | Medium if used directly as snapshot truth | Do not use directly for snapshot totals. |
| Existing snapshot tests | `backend/tests/*quote*snapshot*` | None found | N/A | N/A | N/A | N/A | N/A | N/A | Medium coverage gap | Add focused tests. |
| Existing output tests | `backend/tests/*quote*output*` | None found | N/A | N/A | N/A | N/A | N/A | N/A | Medium coverage gap | Add composition tests in new file. |
| Frontend snapshot API | `frontend/src/api/quoteOutputSnapshots.ts` | Generic snapshot API exists | Calls backend | Reads backend | Generic candidate | N/A | N/A | Not needed now | Medium if wired prematurely | No frontend changes. |

Pre-edit conclusions:

- Existing snapshot table can store V2 payload without DB migration: yes.
- Snapshot payload can include V6 metadata/provenance: yes, through JSON text columns.
- Snapshot can be linked to quote_id: yes.
- Existing output composition did not read latest V2 snapshot: fixed in this slice.
- Duplicate snapshots are prevented by blocking any existing output snapshot for the quote.
- Zero/unpriced snapshots are prevented by persisted quote status and positive totals guards.
- Snapshot after order is prevented by `orders.quote_id` guard.
- Frontend preview data is prevented by write provenance flags and persisted quote totals as source.

## Files Changed

- `backend/services/intake_v6_quote_snapshot_v2_service.py`
- `backend/schemas/intake_v6.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/quote_output_composition_service.py`
- `backend/tests/test_intake_v6_quote_snapshot_v2.py`
- `docs/architecture/product-system/QUOTE_SNAPSHOT_V2_FOR_V6_PRICED_QUOTES.md`
- `docs/architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md`
- `docs/architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_quote_snapshot_v2_for_v6_priced_quotes.md`

## Service Behavior

Service:

- `create_v6_quote_snapshot_v2(db, quote_id, workspace_id, operator_confirmation=True, expected_grand_total=None, expected_pricing_hash=None, created_by=None)`

Behavior:

- Loads persisted quote.
- Validates V6/workspace linkage, priced status, positive totals, valid line items, write provenance, source flags, no duplicate snapshot, no linked order, explicit confirmation, expected total/hash.
- Persists `QuoteOutputSnapshot` with `snapshot_type="QUOTE_SNAPSHOT_V2"` and `status="approved_for_quote_output"`.
- Stores client output separately from internal trace.
- Returns `can_accept_quote=true` but keeps `can_create_order=false` and `order_snapshot_required=true`.

## Endpoint Behavior

Endpoint:

- `POST /api/v1/intake-v6/workspaces/{workspace_id}/quotes/{quote_id}/snapshot-v2`

Request:

```json
{
  "operator_confirmation": true,
  "expected_grand_total": 1190.0,
  "expected_pricing_hash": "optional-write-hash"
}
```

Response includes status, quote id/code, snapshot id/code/version, commercial totals, line items, V6 linkage, client output, internal trace, blockers/warnings, acceptance/order gates, and explicit false flags for order/product aggregate/task graph/execution plan creation.

## Tests Run

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_quote_snapshot_v2.py -q
```

Result: `15 passed, 3 warnings in 0.67s`.

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_quote_snapshot_v2.py tests/test_intake_v6_priced_quote_write.py tests/test_intake_v6_priced_quote_dry_run.py tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Result: `47 passed, 3 warnings in 0.81s`.

## Static Boundary Checks

Snapshot service:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; $tokens = @('build_v4_quote_draft_payload','intake_v4_commercial_quote_service','QuoteOrchestrator','offerModel','create_order(','ProductAggregate','TaskGraph','ExecutionPlan','Employee Mobile','writes_quote_totals','update_quote'); $matches = Select-String -Path .\services\intake_v6_quote_snapshot_v2_service.py -Pattern $tokens -SimpleMatch; if ($matches) { $matches | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" }; exit 1 } else { 'PASS: no forbidden V6 snapshot service tokens found' }
```

Result: `PASS: no forbidden V6 snapshot service tokens found`.

Write service:

Result: `PASS: no forbidden V6 write service tokens found`.

Dry-run service:

Result: `PASS: dry-run service still has no quote write/snapshot/order tokens`.

## Diagnostics

VS Code diagnostics reported no errors in touched backend files and tests.

## What Did Not Change

- No DB/schema migration.
- No quote total rewrite.
- No quote acceptance mutation.
- No order creation.
- No Order Snapshot.
- No ProductAggregate.
- No Task Graph.
- No ExecutionPlan.
- No frontend UI.
- No frontend preview copied into quote output.
- No V2/V4 commercial truth for V6.
- No CostEngine minute/hour client pricing.
- No Employee Mobile.

## Known Limitations

- Duplicate snapshot policy is strict: any existing output snapshot blocks V2 creation.
- Reprice/supersede is not implemented.
- Acceptance gate is not implemented; this slice only reports `can_accept_quote=true` after snapshot creation.
- Frontend action is not implemented.

## Recommended Next Safe Slice

Recommendation: `A. V6_QUOTE_ACCEPTANCE_GATE_DESIGN_NEXT`.

Do not proceed directly to Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje, Angajati, ExecutionReality, or Employee Mobile.

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
2. Current roadmap phase: `Phase 7 — Quote Snapshot after backend-authoritative offer`
3. Roadmap status: `QUOTE_SNAPSHOT_V2_IMPLEMENTED`
4. Why this belongs here: V6 priced quote write persists official totals; snapshot now freezes them before acceptance/order.
5. What this task must NOT unlock: Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate: PASS.
7. Roadmap implementation progress: `26/100%`.
8. Roadmap alignment score: `95/100%`.
9. Cat sunt in directia stabilita: `95/100%`.
10. Dead pieces check: PASS.
11. Owner GO required next: YES.
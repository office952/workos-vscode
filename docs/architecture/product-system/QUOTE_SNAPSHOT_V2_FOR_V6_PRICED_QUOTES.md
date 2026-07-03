# Quote Snapshot V2 for V6 Priced Quotes

Status: `QUOTE_SNAPSHOT_V2_IMPLEMENTED`  
Date: 2026-07-01  
Scope: backend implementation and focused tests for freezing already backend-priced Intake V6 quote totals. No Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, quote acceptance mutation, order creation, frontend UI, DB/schema migration, or Employee Mobile.

## Purpose

Quote Snapshot V2 freezes the official client offer payload after the guarded V6 priced quote write has persisted non-zero backend-authoritative totals.

The snapshot commercial amounts come from persisted `quotes` columns and persisted `line_items`. They do not come from Intake V6 frontend preview, `offerModel`, V4/V2 placeholder builders, CostEngine minute/hour pricing, or a fresh dry-run copy.

## Current State Before Slice

- V6 backend priced dry-run exists and is read-only.
- V6 priced quote write exists and persists official totals only to eligible existing V6 unpriced draft quotes.
- Generic quote output snapshots existed, but they saved composition-preview candidates and were not a V6 authoritative snapshot boundary.
- Existing `quote_output_snapshots` columns are sufficient for V2 JSON payloads; no migration is required.

## Snapshot V2 Payload Contract

Stored in `quote_output_snapshots` with `snapshot_type="QUOTE_SNAPSHOT_V2"`.

Payload fields are stored mainly in `variables_used_json`, `trace_json`, `commercial_summary_json`, `rendered_sections_json`, and `notes`:

- `snapshot_version="QUOTE_SNAPSHOT_V2"`
- `snapshot_kind="V6_PRICED_QUOTE_OFFICIAL_OFFER"`
- `quote`: quote id/code/status/client/workspace/intake identity
- `commercial`: subtotal, discount, total before VAT, VAT amount, grand total, currency, margin
- `line_items`: client-visible persisted quote lines
- `v6_linkage`: workspace/template/source/provenance flags
- `client_output`: offer-safe payload without internal cost trace
- `internal_trace`: pricing input trace, commercial proposal trace, internal cost summary, quote write trace
- `gates`: `can_accept_quote=true`, `can_create_order=false`, `order_snapshot_required=true`, downstream production/execution flags false
- `audit`: creator, timestamp, source, immutability marker

## Eligibility Rules

Snapshot creation is allowed only when all pass:

- quote exists;
- quote is linked to Intake V6 and workspace linkage matches;
- quote status is `priced`;
- quote is not accepted, rejected, expired, converted, or ordered;
- persisted quote totals are positive and internally valid;
- persisted `line_items` exist and client-visible totals are positive;
- notes contain `intake_v6_linkage_v1.intake_v6_priced_quote_write_v1`;
- write provenance has `frontend_preview_not_used=true`;
- write provenance has `no_v4_v2_commercial_truth=true`;
- linkage `pricing_source` is `intake_v6_backend_priced_dry_run`;
- no existing output snapshot exists for the quote;
- no linked order exists;
- operator confirmation is true;
- optional expected grand total and pricing hash match persisted quote/write provenance.

## Blocker Codes

- `V6_SNAPSHOT_QUOTE_NOT_FOUND`
- `V6_SNAPSHOT_NOT_V6_QUOTE`
- `V6_SNAPSHOT_WORKSPACE_MISMATCH`
- `V6_SNAPSHOT_QUOTE_NOT_PRICED`
- `V6_SNAPSHOT_ZERO_TOTAL`
- `V6_SNAPSHOT_INVALID_TOTALS`
- `V6_SNAPSHOT_LINE_ITEMS_MISSING`
- `V6_SNAPSHOT_LINE_ITEMS_INVALID`
- `V6_SNAPSHOT_WRITE_PROVENANCE_MISSING`
- `V6_SNAPSHOT_FRONTEND_PREVIEW_FORBIDDEN`
- `V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN`
- `V6_SNAPSHOT_ALREADY_EXISTS`
- `V6_SNAPSHOT_ORDER_EXISTS`
- `V6_SNAPSHOT_QUOTE_TERMINAL`
- `V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED`
- `V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH`
- `V6_SNAPSHOT_EXPECTED_HASH_MISMATCH`
- `V6_SNAPSHOT_NOTES_INVALID`

## Service and Endpoint Behavior

Service:

`create_v6_quote_snapshot_v2(db, quote_id, workspace_id, operator_confirmation=True, expected_grand_total=None, expected_pricing_hash=None, created_by=None)`

Endpoint:

`POST /api/v1/intake-v6/workspaces/{workspace_id}/quotes/{quote_id}/snapshot-v2`

The endpoint returns either `V6_QUOTE_SNAPSHOT_V2_CREATED` or `V6_QUOTE_SNAPSHOT_V2_BLOCKED` with blockers. It never mutates quote totals, quote status, orders, order snapshots, ProductAggregate, Task Graph, or ExecutionPlan.

## Client Output Payload

`client_output` contains client-safe title, summary, client identity, quote code, offer lines, net/VAT/gross totals, currency, validity, and terms. It intentionally excludes internal cost and pricing traces.

## Internal Trace Contract

`internal_trace` keeps write provenance and trace summaries for audit. It may include internal cost summary, pricing input trace, and commercial proposal trace, but these are never used as client pricing after snapshot creation.

## Idempotency and Immutability Policy

This slice blocks duplicate snapshot creation for any quote that already has an output snapshot. Snapshot rows are immutable in practice: updates, supersede/reprice flows, and acceptance linkage remain later slices.

## Output Composition Behavior

`QuoteOutputCompositionService.compose_preview` now prefers the latest `QUOTE_SNAPSHOT_V2` row for a quote. If present, it returns `composition_type="quote_snapshot_v2_preview"` and commercial summary from the snapshot. If absent, it still returns live quote-column preview and includes `snapshot_missing` warning.

## Acceptance and Order Gates

Snapshot creation returns `can_accept_quote=true` because the quote now has a frozen V2 snapshot payload. It still returns `can_create_order=false` and `order_snapshot_required=true`. Acceptance, order snapshot, and order creation remain separate owner-approved slices.

## Tests

Focused backend tests cover successful snapshot creation, persisted total source, line items, V6 linkage, write provenance, client/internal trace separation, accept/order flags, zero/unpriced/non-V6/workspace/line/provenance/source/duplicate/order/terminal/confirmation/expected mismatch blockers, invalid notes, quote-total immutability, no order creation, composition preference, composition missing warning, and static forbidden-token checks.

Validation result:

- `15 passed` for `tests/test_intake_v6_quote_snapshot_v2.py`.
- `47 passed` for snapshot + write + dry-run + zero guard focused regression.

## Forbidden Shortcuts

This implementation does not:

- use V4/V2 commercial truth;
- copy frontend preview totals;
- call generic QuoteWizard pricing or QuoteOrchestrator;
- recalculate from CostEngine minute/hour client pricing;
- write quote totals;
- create or mutate orders;
- create Order Snapshot;
- create ProductAggregate;
- create Task Graph;
- create ExecutionPlan;
- touch Employee Mobile;
- require DB/schema migration.

## What Remains Not Implemented

- Snapshot approval lifecycle beyond immediate `approved_for_quote_output` V2 row.
- Quote acceptance gate runtime mutation.
- Order Snapshot.
- Order creation/conversion from accepted snapshot.
- ProductAggregate, Task Graph, ExecutionPlan.
- Frontend action/button.
- Reprice/supersede snapshot flow.

Markers:

- `QUOTE_SNAPSHOT_V2_IMPLEMENTED`
- `ORDER_SNAPSHOT_NOT_IMPLEMENTED`
- `PRODUCTAGGREGATE_NOT_IMPLEMENTED`
- `TASKGRAPH_NOT_IMPLEMENTED`
- `EXECUTIONPLAN_NOT_IMPLEMENTED`

## Next Safe Slice

Recommended next: `V6_QUOTE_ACCEPTANCE_GATE_DESIGN_NEXT`.

Do not proceed directly to Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje, Angajati, ExecutionReality, or Employee Mobile.
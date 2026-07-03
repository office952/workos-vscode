# V6 Priced Quote Write Path Design

Status: `DOCUMENTED_NOT_IMPLEMENTED`  
Date: 2026-07-01  
Scope: design only. No implementation, quote write, quote update, quote creation, DB/schema migration, API change, Quote Snapshot runtime change, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, frontend preview copy, V2/V4 commercial truth for V6, or Employee Mobile change.

## 1. Purpose

Design how the backend-only Intake V6 priced quote dry-run becomes official persisted quote totals safely.

The write path must complete the V6 commercial path without falling back to incomplete V4/V2 placeholder logic. The authoritative source is the backend-generated V6 priced dry-run result, not Intake UI preview values, frontend `offerModel`, V4 draft payload totals, or internal CostEngine minute/hour details.

Everything in this document is `DOCUMENTED_NOT_IMPLEMENTED`.

## 2. Current Status

- Intake V6 preview can calculate non-zero values.
- V6 draft quote creation through the legacy zero V4 draft payload is blocked.
- V6 backend priced quote dry-run exists at `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`.
- Dry-run returns backend commercial totals, line items, pricing input trace, material/internal trace, commercial proposal trace, blockers, and warnings.
- Dry-run never creates/updates quotes, writes quote totals, creates snapshots/orders, calls `build_v4_quote_draft_payload`, or copies frontend preview totals.

Owner clarification: V4 was copied forward into V6 up to calculator/draft structure. The real commercial calculator continued in V6, while V4 stayed incomplete for current V6 pricing. Therefore V6 must complete its own commercial write path and must not use V4 as commercial truth.

## 3. Backend Write Surface Audit

| Surface | File/function/API | Writes quote totals? | Creates quote? | Creates snapshot? | Input source | V6-compatible? | Risk | Recommended use for V6 | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Existing quote price endpoint | `backend/routers/quotes.py` / `POST /api/v1/entities/quotes/price` | Yes | Yes | No Quote Output Snapshot V2; persists priced quote row from orchestrator snapshot | `QuotePriceRequest`, `QuoteOrchestrator`, ProductSystem/CostEngine-style snapshot | Not as the V6 dry-run writer | Medium/high: canonical but uses different pricing semantics and can carry cost-plus/hourly legacy risk | Reference defensive checks only: positive snapshot fields, no silent fallback, backend authority | `SAFE_REFERENCE_ONLY` |
| Existing quote reprice endpoint | `backend/routers/quotes.py` / `POST /api/v1/entities/quotes/{quote_id}/price` | Yes | No, updates existing quote | No Quote Output Snapshot V2 | `QuotePriceRequest`, `QuoteOrchestrator`, reconstructed legacy payloads when needed | Not as V6 dry-run writer | High for V6: can overwrite quote using non-V6 dry-run source and legacy reconstruction | Reference update mechanics/status guards only, not pricing source | `POSSIBLE_WRITE_SURFACE` |
| QuoteWizard pricing path | `frontend/src/components/workos/QuoteWizard.tsx` + `frontend/src/api/quotes.ts` / `priceQuote` | Backend writes via `/entities/quotes/price` | Backend creates quote | No Quote Output Snapshot V2 | User wizard inputs, template, quote input, pricing settings | Not for V6 dry-run write | High: frontend-driven payload and generic path; not the V6 dry-run contract | Do not use for V6 dry-run official write; keep separate | `FORBIDDEN_FOR_V6` |
| Quote output snapshot path | `backend/routers/quote_output_snapshots.py` / `POST /{quote_id}/output-snapshots` | No | No | Yes, creates output snapshot candidate | Quote output composition preview | Later, after priced quote write | Medium: snapshot candidate must not be used to create price | Use only after quote totals are positive and write provenance exists | `SNAPSHOT_LATER` |
| Quote output composition service | `backend/services/quote_output_composition_service.py` | No | No | No | Existing quote columns + output blocks/dossier | Read-only after write | Medium: currently mirrors zero quote columns | Use read-only display after write; before write show unpriced blocker | `SAFE_REFERENCE_ONLY` |
| V6 dry-run service | `backend/services/intake_v6_priced_quote_dry_run_service.py` | No | No | No | V6 backend pricing input + material trace + `CommercialPriceProposalService` | Yes | Low for read-only; write not implemented | Authoritative computation source for future V6 write eligibility | `SAFE_REFERENCE_ONLY` |
| V6 zero guard | `backend/services/intake_v6_commercial_quote_service.py` / `_block_v6_zero_commercial_truth` | No | Blocks zero create before persistence | No | Draft quote payload after V4 builder normalization | Yes as guard | Low: prevents known bad write | Keep as defense-in-depth; future write must pass positive totals | `SAFE_REFERENCE_ONLY` |
| V4 draft quote builder | `backend/services/intake_v4_commercial_quote_service.py` / `build_v4_quote_draft_payload` | Writes zero placeholders | Yes via callers | No | V4/V6-compatible draft payload and snapshot | No for V6 commercial truth | Critical: source of old zero quote issue | Forbidden as V6 priced write source | `FORBIDDEN_FOR_V6` / `LEGACY_ONLY` |
| V4 commercial quote service namespace | `backend/services/intake_v4_commercial_quote_service.py` | Draft placeholders only in current path | Yes for legacy V4 | No | V4 pricing input preview | No for V6 priced write | High if reused for V6 | Keep legacy-isolated only | `LEGACY_ONLY` |

Design conclusion: the future V6 write path should be a dedicated Intake V6 write service that re-runs or verifies the V6 dry-run server-side, then writes quote columns only after eligibility checks. It should not call generic QuoteWizard pricing or V4 draft builder as the commercial writer.

## 4. State Machine

| State | Source condition | Allowed action | Forbidden action | Required fields | Required approval | Can write quote totals? | Can create snapshot? | Can convert to order? | Operator-facing message |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `V6_DRY_RUN_READY` | Dry-run returns `V6_PRICED_DRY_RUN_READY`, positive subtotal/gross, positive required lines, backend source | Review totals, show provenance, request explicit write | Accept/order/snapshot as if official | `commercial_totals`, `commercial_line_items`, `pricing_source`, traces | None yet, but operator confirmation required for write | No, until write request | No | No | `Backend dry-run is ready. Official quote totals are not written yet.` |
| `V6_DRY_RUN_BLOCKED` | Dry-run returns blocked or source unavailable | Fix blockers, rerun dry-run | Write totals, snapshot, accept/order | Blocker list | N/A | No | No | No | `Priced quote dry-run is blocked. Resolve blockers before writing quote totals.` |
| `V6_WRITE_READY` | Dry-run ready plus write payload matches expected total/hash and operator confirmation is true | Execute future write mutation | Use V4/V2/frontend source, write zero, create snapshot/order | quote/workspace id, expected hash, expected total, source, write mode | Operator explicit action; owner approval flag recorded if policy requires | Yes, in future implementation | No in same slice | No | `Ready to write backend-priced V6 totals to quote.` |
| `V6_WRITE_BLOCKED_ZERO_TOTAL` | subtotal/gross/required line total is `<= 0` or missing | Return blocker; keep quote unpriced | Write zero or mark priced | totals and line check evidence | Future free-quote approval not implemented | No | No | No | `Zero total cannot become an official V6 quote price.` |
| `V6_WRITE_BLOCKED_PRODUCT_TRUTH` | Product Truth/readiness insufficient for pricing or explicitly blocked | Return Product Truth blockers | Write totals from incomplete/mutable truth | readiness status, blockers, source refs | Owner cannot bypass unless future policy defines accepted-for-pricing state | No | No | No | `Product Truth is not ready enough for official pricing.` |
| `V6_WRITE_BLOCKED_UNAPPROVED` | operator confirmation false, owner approval required and missing, hash/expected total mismatch, quote not eligible | Return approval/provenance blocker | Implicit write or overwrite | confirmation, expected total, expected hash, quote eligibility | Operator required; owner required when blockers or policy demand | No | No | No | `Explicit approval is required before writing official totals.` |
| `V6_WRITTEN_PRICED_QUOTE` | Future write succeeds and quote columns/line items/provenance are persisted | Show official totals, allow snapshot eligibility evaluation | Order conversion without snapshot/acceptance gates | quote totals, line items, notes provenance | Write operator recorded | Already written | Possibly true by eligibility | No | `Official backend-priced totals are written. Quote Snapshot is still missing.` |
| `V6_REPRICE_REQUIRED` | Source workspace/Product Truth/pricing input changed after write, expected hash mismatch, snapshot not yet approved | Rerun dry-run and re-write through explicit action | Snapshot stale totals, accept/order old totals | previous hash, current hash, change reason | Operator/owner review | Only through reprice write flow | No while stale | No | `Source changed after pricing. Reprice required before snapshot or acceptance.` |
| `V6_QUOTE_SNAPSHOT_READY` | Priced quote exists, provenance valid, no stale source, snapshot policy blockers absent | Create Quote Snapshot V2 candidate in separate slice/action | Accept/order before snapshot policy satisfied | priced quote id, provenance, output composition eligibility | Snapshot manager/owner approval per policy | No new total write | Yes | No | `Quote totals are ready for snapshot creation.` |
| `V6_QUOTE_SNAPSHOT_CREATED` | Approved/frozen Quote Snapshot V2 exists for the priced quote | Show client output from snapshot, proceed to acceptance gate | Mutate frozen quote output silently | snapshot id, status, content hash, commercial summary | Snapshot approval per policy | No, unless reprice/supersede path | Snapshot already exists | Not until accepted | `Frozen Quote Snapshot exists. Acceptance may proceed if approval gates pass.` |
| `V6_ACCEPTANCE_ALLOWED` | Priced quote + approved snapshot + acceptance policy/owner approval satisfied | Accept quote | Create order without order snapshot policy | quote status, snapshot, owner approval | Owner/client acceptance policy | No | No | After accepted/order gates | `Quote can be accepted. Order conversion remains separately gated.` |
| `V6_ACCEPTANCE_BLOCKED` | No approved snapshot, quote not priced, owner approval missing, stale source, zero totals, or blockers | Resolve blockers | Accept/order | blocker list | Depends on blocker | No | Maybe if only snapshot missing and quote is priced | No | `Acceptance is blocked until priced quote and snapshot gates are complete.` |

## 5. Write Eligibility Rules

A quote total write is allowed only when all rules pass:

1. Dry-run status is `V6_PRICED_DRY_RUN_READY`.
2. `commercial_totals.subtotal_net > 0`.
3. `commercial_totals.total_gross > 0`.
4. `commercial_line_items` are present and all required/client-visible lines have positive `subtotal`/`total` values.
5. `blockers` is empty or every blocker is explicitly classified as non-commercial/non-blocking by a future owner-approved policy.
6. `pricing_source` is `intake_v6_backend_priced_dry_run` or a later approved backend source.
7. Source is backend-generated, not frontend preview, `offerModel`, or mutable client-supplied totals.
8. No V4/V2 commercial truth is used.
9. Product Truth readiness is sufficient, or the source is explicitly marked accepted for pricing with audit trail.
10. Operator/owner explicitly triggers `write priced quote totals`.
11. Request `expected_total_gross` matches the server recomputed dry-run total.
12. Request `expected_pricing_hash` matches the server recomputed pricing hash.
13. Target quote is eligible for selected write mode.
14. No approved Quote Snapshot or Order already depends on the target quote unless the mode creates a new priced quote instead.

If any rule fails: no write, return blocker, keep quote unpriced.

Zero policy: total `0` always blocks write unless a future owner-approved free quote path exists. Free quote path is not implemented and not designed as part of this slice.

Suggested blocker codes:

- `V6_PRICED_QUOTE_WRITE_DRY_RUN_NOT_READY`
- `V6_PRICED_QUOTE_WRITE_ZERO_TOTAL`
- `V6_PRICED_QUOTE_WRITE_MISSING_LINE_ITEMS`
- `V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE`
- `V6_PRICED_QUOTE_WRITE_FRONTEND_SOURCE_FORBIDDEN`
- `V6_PRICED_QUOTE_WRITE_V4_V2_SOURCE_FORBIDDEN`
- `V6_PRICED_QUOTE_WRITE_PRODUCT_TRUTH_BLOCKED`
- `V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED`
- `V6_PRICED_QUOTE_WRITE_OWNER_APPROVAL_REQUIRED`
- `V6_PRICED_QUOTE_WRITE_HASH_MISMATCH`
- `V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH`
- `V6_PRICED_QUOTE_WRITE_TARGET_QUOTE_LOCKED`
- `V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS`
- `V6_PRICED_QUOTE_WRITE_ORDER_EXISTS`

## 6. Write Request/Response Contract

`DOCUMENTED_NOT_IMPLEMENTED`

Recommended route:

`POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`

This route fits the existing Intake V6 workspace router and keeps the source boundary explicit. It should be added only in a future implementation slice.

Request payload:

```json
{
  "dry_run_id": null,
  "workspace_id": "workspace-v6",
  "quote_id": 6,
  "pricing_source": "intake_v6_backend_priced_dry_run",
  "pricing_mode": "write_priced_quote",
  "operator_confirmation": true,
  "owner_approval_required": true,
  "expected_total_gross": 6517.86,
  "expected_pricing_hash": "server-computed-pricing-hash",
  "write_mode": "update_existing_v6_draft"
}
```

Allowed `write_mode` values:

- `update_existing_v6_draft`
- `create_new_priced_quote`

Response payload:

```json
{
  "status": "V6_PRICED_QUOTE_WRITTEN",
  "quote_id": 6,
  "quote_code": "Q-V6-IV6-BB8EE3F8-1782910533",
  "commercial_totals": {
    "subtotal_net": 5386.66,
    "discount": 0,
    "total_before_vat": 5386.66,
    "vat": 1131.2,
    "vat_rate": 21,
    "total_gross": 6517.86,
    "currency": "RON"
  },
  "line_items": [],
  "pricing_trace": {
    "pricing_source": "intake_v6_backend_priced_dry_run",
    "pricing_hash": "server-computed-pricing-hash",
    "dry_run_generated_at": "server timestamp",
    "no_v4_v2_commercial_truth": true
  },
  "blockers": [],
  "warnings": [],
  "can_create_quote_snapshot": true,
  "can_accept_quote": false,
  "contract_status": "DOCUMENTED_NOT_IMPLEMENTED"
}
```

Blocked response:

```json
{
  "status": "V6_PRICED_QUOTE_WRITE_BLOCKED",
  "quote_id": 6,
  "quote_code": "Q-V6-IV6-BB8EE3F8-1782910533",
  "commercial_totals": null,
  "line_items": [],
  "pricing_trace": {
    "pricing_source": "intake_v6_backend_priced_dry_run",
    "no_v4_v2_commercial_truth": true
  },
  "blockers": [
    {
      "code": "V6_PRICED_QUOTE_WRITE_ZERO_TOTAL",
      "message": "Zero total cannot become an official V6 quote price."
    }
  ],
  "warnings": [],
  "can_create_quote_snapshot": false,
  "can_accept_quote": false,
  "contract_status": "DOCUMENTED_NOT_IMPLEMENTED"
}
```

## 7. Update Existing vs Create New Quote Decision

Recommendation: target Option A first, with Option B fallback.

Option A: update existing V6 draft quote.

Pros:

- Keeps same quote id/code.
- Preserves UI continuity and existing links.
- Correctly repairs quote #6-style records when they are known unpriced V6 drafts.
- Matches existing in-place pricing mechanics in `POST /entities/quotes/{quote_id}/price`, but with V6-specific source checks.

Cons:

- Mutates a previously unpriced draft.
- Needs strong provenance and previous-total audit.
- Must prevent accidental overwrite of priced/snapshotted/ordered quotes.

Option B: create new V6 priced quote.

Pros:

- Clean separation from old zero draft.
- Avoids mutating invalid historical records.
- Cleaner audit when a zero quote already moved downstream.

Cons:

- Duplicates quote objects.
- Needs linkage between old draft and new priced quote.
- UI must avoid showing both as equivalent active offers.

Target rule:

- Use Option A only when the existing quote is a V6 draft/unpriced quote, has zero commercial totals, has no approved/pending Quote Snapshot, has no order/conversion history, and has V6 linkage matching the workspace.
- Use Option B when the draft already has snapshot/order/history, quote status is not `draft`, linkage is ambiguous, or overwrite risk is non-zero.

Existing quote #6 handling:

- If quote #6 has no snapshot/order: eligible for future explicit `update_existing_v6_draft` priced write after dry-run and approval checks pass.
- If quote #6 has snapshot/order/history: do not overwrite; create a new V6 priced quote and link it to quote #6 as `supersedes_unpriced_quote_id` / `superseded_by_priced_quote_id` in notes/provenance if no schema field exists.

No implementation now.

## 8. Fields To Write

Quote columns to write in future implementation:

- `subtotal`: from `commercial_totals.subtotal_net`.
- `discount`: from write policy, default `0` unless dry-run/result carries explicit discount.
- `discount_pct`: default `0` unless explicit approved discount exists.
- `total_before_vat`: from `commercial_totals.subtotal_net` after discount policy.
- `vat`: VAT amount, not VAT percent, aligned with current quote column use in output composition.
- `grand_total`: from `commercial_totals.total_gross`.
- `margin_pct`: only if available/meaningful from backend commercial proposal; otherwise `0` or null-preserving policy documented in notes.
- `status`: `priced` if existing quote status transition allows it.
- `line_items`: JSON-serialized client-visible commercial lines and trace wrapper.
- `notes`: enrich with `intake_v6_linkage_v1.priced_quote_write_v1` provenance.

Line item fields:

- `name` / `description`
- `quantity`
- `unit`
- `unit_price`
- `total`
- `source_component`
- `module_code`
- `component_code`
- `pricing_rule_code`
- `pricing_source`
- `client_visible`
- `internal_cost` optional trace only, never used as client price
- `warnings`

Must not write:

- frontend `offerModel` totals;
- frontend-only preview values as official totals;
- internal CostEngine minute/hour details as client pricing;
- mutable live Intake fields without trace/hash;
- V4/V2 placeholder totals;
- Quote Snapshot data in the same write slice.

## 9. Provenance / Notes Contract

Add or enrich `notes` JSON under `intake_v6_linkage_v1.priced_quote_write_v1`.

Suggested provenance fields:

```json
{
  "intake_v6_linkage_v1": {
    "source_module": "intake_v6",
    "source_workspace_id": "workspace-v6",
    "source_workspace_code": "IV6-BB8EE3F8",
    "pricing_source": "intake_v6_backend_priced_dry_run",
    "requires_pricing_review": false,
    "priced_quote_write_v1": {
      "contract_status": "DOCUMENTED_NOT_IMPLEMENTED",
      "dry_run_generated_at": "server timestamp",
      "write_timestamp": "server timestamp",
      "write_operator": "user id/email",
      "pricing_input_hash": "server hash",
      "expected_pricing_hash": "client supplied hash checked by server",
      "expected_total_gross": 6517.86,
      "commercial_proposal_trace": {},
      "pricing_input_trace": {},
      "internal_cost_trace": {},
      "product_truth_reference": {
        "status": "runtime_product_truth_not_persisted_or_accepted_for_pricing",
        "readiness_snapshot": {}
      },
      "previous_unpriced_quote_totals": {
        "subtotal": 0,
        "total_before_vat": 0,
        "vat": 0,
        "grand_total": 0
      },
      "write_mode": "update_existing_v6_draft",
      "no_v4_v2_commercial_truth": true,
      "frontend_preview_not_used": true,
      "quote_snapshot_created": false,
      "order_created": false
    }
  }
}
```

The provenance must be server-computed at write time. Client-supplied hashes/expected totals are guard inputs only, not commercial truth.

## 10. Quote Snapshot V2 Relation

Priced quote write is not Quote Snapshot V2.

After priced quote totals are written:

- Quote Snapshot V2 is still not automatically created.
- `can_create_quote_snapshot` may become true when snapshot eligibility checks pass.
- `can_accept_quote` remains false until an approved/frozen Quote Snapshot exists, unless a future explicit policy exception is approved.
- Output/client offer should use snapshot once available.
- Order conversion remains blocked until accepted quote plus order snapshot policy passes.

Exact gate:

- Priced quote write stores official backend quote totals.
- Quote Snapshot V2 freezes official commercial/product truth for client output.
- Acceptance should require an approved Quote Snapshot V2 or an explicit owner-approved exception.
- Order conversion should require accepted quote and downstream order snapshot/readiness policy.

Current design policy: no acceptance without snapshot.

## 11. Oferte / Output Behavior After Write

Before write:

- Show V6 draft as unpriced.
- Show zero blocker / `QUOTE_NOT_PRICED` / `V6_DRAFT_UNPRICED`.
- Do not present zero as official commercial truth.
- Allow read-only dry-run display if available.

After write:

- Show official persisted totals from quote columns.
- Remove zero blocker.
- Show pricing provenance: source, write timestamp, operator, dry-run hash, no V4/V2 truth.
- Show snapshot missing warning until Quote Snapshot V2 exists.
- Keep order conversion blocked until snapshot and acceptance gates pass.

If write is blocked:

- Show exact backend blocker code/message.
- Keep quote unpriced.
- Do not create snapshot/order.

## 12. Test Plan

Backend tests for future implementation:

1. Ready dry-run writes positive quote totals only with explicit action.
2. Zero dry-run blocks write.
3. Missing line items blocks write.
4. V4/V2 source blocks write.
5. Frontend preview source blocks write.
6. Existing V6 unpriced quote can be updated if no snapshot/order.
7. Quote with snapshot/order cannot be overwritten.
8. Notes/provenance stores dry-run trace, pricing hash, previous totals, operator, timestamp, and `no_v4_v2_commercial_truth=true`.
9. `can_create_quote_snapshot=true` after successful write when snapshot eligibility passes.
10. `can_accept_quote=false` until snapshot exists.
11. No ProductAggregate/ExecutionPlan created.
12. Existing zero guard still passes.
13. Dry-run still does not write.
14. Expected total mismatch blocks write.
15. Pricing hash mismatch blocks write.
16. Existing priced quote uses revision/reprice rules, not silent overwrite.

Frontend tests later:

- Unpriced draft shows blocker before write.
- Priced quote shows persisted totals after write.
- Snapshot missing warning shown after write before snapshot.
- Write blocked response displays exact backend blocker.
- Order conversion remains disabled until snapshot/acceptance gates pass.

## 13. Forbidden Shortcuts

Future implementation must not:

- Call `build_v4_quote_draft_payload` in V6 write service.
- Copy frontend `offerModel` totals.
- Accept `grand_total` / `total_gross` `0`.
- Create Quote Snapshot in the same slice unless owner explicitly approves a snapshot slice.
- Create Order.
- Create ProductAggregate or ExecutionPlan.
- Use V2/V4 as commercial truth.
- Calculate commercial price by hour/minute.
- Use CostEngine internal minute/hour details as client price.
- Mutate quote totals without expected hash/total guard.
- Overwrite a snapshotted/ordered quote.

## 14. Recommended Implementation Slices

1. `V6_PRICED_QUOTE_WRITE_SMALL_SLICE`: add backend write service and route behind explicit action; update only eligible unpriced V6 draft; no snapshot/order.
2. `V6_PRICED_WRITE_PROVENANCE_HARDENING`: add pricing hash and source drift checks if not completed in slice 1.
3. `V6_PRICED_QUOTE_UI_ACTION`: add controlled UI action and blocked-state display, still no snapshot/order.
4. `V6_QUOTE_SNAPSHOT_ELIGIBILITY_AFTER_WRITE`: enable snapshot eligibility after priced write.
5. `V6_QUOTE_SNAPSHOT_RUNTIME`: create/freeze Quote Snapshot V2 in separate owner-approved slice.

Recommended next safe slice: `V6_PRICED_QUOTE_WRITE_SMALL_SLICE` after owner GO.

## 15. Open Questions

1. Should `vat` column store VAT amount for all V6 writes? Current output composition reads it as amount; generic quote price endpoints currently assign `snapshot.pricing.vat_pct` to `vat` in some paths, so future implementation should verify column semantics before write.

## Implemented Snapshot Slice — Quote Snapshot V2 for V6 Priced Quotes

Status: `QUOTE_SNAPSHOT_V2_IMPLEMENTED` on 2026-07-01.

Implemented backend-only Quote Snapshot V2 creation for already backend-priced V6 quotes:

- Service: `backend/services/intake_v6_quote_snapshot_v2_service.py`
- Endpoint: `POST /api/v1/intake-v6/workspaces/{workspace_id}/quotes/{quote_id}/snapshot-v2`
- Tests: `backend/tests/test_intake_v6_quote_snapshot_v2.py`
- Design: `docs/architecture/product-system/QUOTE_SNAPSHOT_V2_FOR_V6_PRICED_QUOTES.md`

The snapshot freezes persisted quote totals and line items only after V6 write provenance is present. It blocks zero/unpriced/non-V6/workspace-mismatched/duplicate/ordered/terminal/frontend-preview/V2-V4-source cases. Output composition now prefers an existing `QUOTE_SNAPSHOT_V2` row and reports `snapshot_missing` otherwise.

Markers:

- `QUOTE_SNAPSHOT_V2_IMPLEMENTED`
- `ORDER_SNAPSHOT_NOT_IMPLEMENTED`
- `PRODUCTAGGREGATE_NOT_IMPLEMENTED`
- `TASKGRAPH_NOT_IMPLEMENTED`
- `EXECUTIONPLAN_NOT_IMPLEMENTED`
2. Should `margin_pct` remain `0` when using unit commercial rules without internal cost margin, or should margin confidence be stored separately in notes only?
3. What exact Product Truth readiness signal is sufficient before official pricing while runtime canonical Product Truth persistence is still not implemented?
4. Should a future `dry_run_id` be persisted, or is server recompute plus hash enough for first write slice?
5. Should free quotes be supported as a separate owner-approved policy? Current answer: no.

## Roadmap Alignment Checkpoint

1. Roadmap source used: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
2. Current roadmap phase: `Phase 6 bridge design — V6 priced quote write before Quote Snapshot`
3. Roadmap status: `NEXT / V6 priced quote write path design`
4. Why this belongs here: dry-run exists and proves backend-authoritative totals can be generated; next risk is persisting official commercial totals safely; this keeps quote write before snapshot/order; this prevents V2/V4 or frontend preview from becoming commercial truth.
5. What this task must NOT unlock: Quote Snapshot runtime, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.
6. Re-audit gate: PASS.
7. Roadmap implementation progress: `20/100% docs-only write design`.
8. Roadmap alignment score: `94/100%`.
9. Cat sunt in directia stabilita: `94/100%`.
10. Dead pieces check: PASS for this design slice; V4 remains legacy-isolated and forbidden as V6 commercial truth.
11. Owner GO required next: YES.

## Implemented Small Slice — V6 Priced Quote Write

Status: `V6_PRICED_QUOTE_WRITE_IMPLEMENTED` on 2026-07-01.

Implemented backend-only guarded quote total write from the V6 backend dry-run result:

- Service: `backend/services/intake_v6_priced_quote_write_service.py`
- Endpoint: `POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`
- Request schema: `IntakeV6PricedQuoteWriteRequest`
- Tests: `backend/tests/test_intake_v6_priced_quote_write.py`

The endpoint writes only to an eligible existing V6 unpriced draft quote. It does not create a quote, create a Quote Snapshot, create an Order, create ProductAggregate, create Task Graph, create ExecutionPlan, or touch frontend UI.

Implemented eligibility rules:

- Recomputes V6 priced quote dry-run server-side.
- Requires dry-run status `V6_PRICED_DRY_RUN_READY`.
- Requires `pricing_source=intake_v6_backend_priced_dry_run`.
- Requires positive `commercial_totals.subtotal_net` and `commercial_totals.total_gross`.
- Requires positive commercial line items.
- Requires expected total to match server recomputed total.
- Optionally checks expected pricing hash when supplied.
- Requires target quote exists and is V6-linked.
- Requires quote linkage to match workspace.
- Requires target quote is still zero/unpriced.
- Blocks accepted/converted/terminal quote statuses.
- Blocks if any output snapshot exists.
- Blocks if an Order exists for the quote.
- Blocks if `accepted_snapshot_v2_id` is already set.
- Requires explicit operator confirmation.
- Preserves invalid notes as `legacy_notes_raw` instead of destroying them.

Fields written:

- `status="priced"`
- `subtotal`
- `discount=0.0`
- `discount_pct=0.0`
- `total_before_vat`
- `vat` as VAT amount from dry-run
- `grand_total`
- `margin_pct=0.0`
- `line_items` JSON mapped from dry-run commercial lines
- `notes` JSON enriched with `intake_v6_priced_quote_write_v1`

Line item mapper writes:

- `description` / `name`
- `quantity`
- `unit`
- `unit_price`
- `total`
- `source_component`
- `module_code`
- `component_code`
- `pricing_rule_code`
- `pricing_source=intake_v6_backend_priced_dry_run`
- `client_visible=true`
- `warnings`

Provenance notes include:

- `workspace_id`
- `workspace_code`
- `intake_code`
- `pricing_source`
- `dry_run_generated_at`
- `write_timestamp`
- `write_operator`
- `expected_total_gross`
- `written_total_gross`
- `pricing_hash`
- `pricing_input_trace`
- `commercial_proposal_trace`
- `internal_cost_trace_summary`
- `previous_unpriced_quote_totals`
- `no_v4_v2_commercial_truth=true`
- `frontend_preview_not_used=true`
- `quote_snapshot_created=false`
- `order_created=false`

Blockers implemented:

- `V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED`
- `V6_PRICED_QUOTE_WRITE_ZERO_TOTAL`
- `V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH`
- `V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE`
- `V6_PRICED_QUOTE_WRITE_WORKSPACE_MISMATCH`
- `V6_PRICED_QUOTE_WRITE_ALREADY_PRICED`
- `V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS`
- `V6_PRICED_QUOTE_WRITE_ORDER_EXISTS`
- `V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED`
- `V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE`
- `V6_PRICED_QUOTE_WRITE_LINE_ITEMS_MISSING`

Boundary markers:

- `V6_PRICED_QUOTE_WRITE_IMPLEMENTED`
- `QUOTE_SNAPSHOT_RUNTIME_NOT_IMPLEMENTED`
- `ORDER_SNAPSHOT_NOT_IMPLEMENTED`
- `PRODUCTAGGREGATE_NOT_IMPLEMENTED`
- `TASKGRAPH_NOT_IMPLEMENTED`
- `EXECUTIONPLAN_NOT_IMPLEMENTED`

What remains not implemented:

- Quote Snapshot V2 runtime creation/approval.
- Order Snapshot.
- Quote acceptance changes.
- Order conversion changes.
- Create-new-priced-quote fallback.
- Frontend write action.
- ProductAggregate, Task Graph, ExecutionPlan, Utilaje/Workcenters, Angajati/Skills/Capacity, ExecutionReality, Employee Mobile.

# V6 Priced Quote Bridge Design

Status: `DOCUMENTED_NOT_IMPLEMENTED`
Scope: design only; no frontend, backend, database, API, schema, seed, Product Truth persistence, pricing runtime, Quote Snapshot runtime, Order Snapshot, ProductAggregate, Task Graph, ExecutionPlan, quote creation, order creation, task creation, forced confirmation, or Employee Mobile changes.

## Purpose

This document defines how a non-zero Intake V6 preview can safely become an official quote total in the future without copying mutable UI preview values into persisted quote columns.

The bridge must preserve three boundaries:

- Intake V6 preview is review information, not an offer.
- Product Truth/pricing input is the source of priced intent, not the official price itself.
- Official quote totals are backend-authoritative and become client-usable only after pricing review, owner approval, and Quote Snapshot V2 rules allow it.

## Current Zero Path

Observed path for workspace `IV6-BB8EE3F8` / quote `Q-V6-IV6-BB8EE3F8-1782910533`:

| Stage | Current status | Evidence |
| --- | --- | --- |
| Intake V6 live calculation | `PREVIEW_NON_ZERO` | Intake page shows internal estimate `782.38 EUR`, commercial preview gross `6517.86 RON`, preview net `5386.66 RON`. |
| Pricing input preview | `PREVIEW_NON_ZERO` | Backend preview is ready, with no fatal blockers and production counts/geometry/material values. |
| Handoff preview | `HANDOFF_ALLOWED_PREVIEW_ONLY` | `quote-handoff-preview` allows internal draft quote creation and marks `preview_only=true`. |
| Draft quote write | `DRAFT_ZERO_PLACEHOLDER` | V6 draft service reuses V4 draft payload builder; line item `unit_price`, line `total`, `subtotal`, `total_before_vat`, `vat`, and `grand_total` are written as `0`. |
| Commercial spine | `QUOTE_NOT_PRICED` | V6 quote-to-order service blocks pricing review/conversion because quote totals are not positive and no frozen snapshot total exists. |
| Oferte/output display | `OUTPUT_DISPLAYS_PERSISTED_ZERO` | Oferte cards/detail and client-offer preview show `0,00 RON`; output composition mirrors quote columns. |
| Quote Snapshot | `SNAPSHOT_MISSING` | Runtime output snapshots list for quote #6 returns count `0`. |

The zero is introduced intentionally at the draft boundary, not by the Intake V6 calculator. The current draft quote is an internal review placeholder and must remain unpriced until a backend pricing bridge writes official totals.

## Target Priced Quote Bridge

The target bridge is:

`Intake V6 confirmed Product Truth / pricing input -> backend CommercialPriceProposal/priced quote computation -> priced quote totals -> pricing review -> owner approval -> Quote Snapshot V2 -> acceptable offer/order snapshot`

Target rule: a value may become official only if it is recomputed or verified server-side from a stable source payload and persisted by a backend pricing boundary. The bridge must never trust `offerModel.totalGross`, `subtotalNet`, or any other mutable frontend preview number as the persisted quote total.

The future bridge should create a separate priced action from the existing unpriced draft action. The existing draft action remains valid for `V6_DRAFT_UNPRICED`; the new bridge is responsible for `V6_PRICED_REVIEW_REQUIRED` and later states.

## Quote States

Proposed V6 quote state model, docs-only:

| State | Meaning | Allowed next movement |
| --- | --- | --- |
| `V6_DRAFT_UNPRICED` | Draft exists, persisted totals are zero placeholders, quote is internal review only. | Load pricing readiness, show unpriced label, allow priced bridge dry-run in future. |
| `V6_PREVIEW_AVAILABLE` | Intake V6 preview has non-zero internal/commercial numbers, but no backend official price exists. | Show preview only; do not treat as offer value. |
| `V6_PRICING_READY` | Product Truth/pricing input has enough confirmed source data for backend pricing attempt. | Future backend priced dry-run or priced quote action. |
| `V6_PRICED_REVIEW_REQUIRED` | Backend has computed and persisted non-zero quote totals, but pricing review is not complete. | Pricing review only. |
| `V6_PRICED_APPROVED` | Pricing review and owner commercial approval are complete. | Quote Snapshot V2 creation/approval path. |
| `V6_QUOTE_SNAPSHOT_CREATED` | Frozen commercial snapshot exists and is attached. | Acceptable quote path, subject to policy. |
| `V6_ACCEPTABLE` | Quote can be accepted and converted according to backend guards. | Accept/convert, still no ExecutionPlan unlock here. |
| `V6_BLOCKED_ZERO_TOTAL` | A quote has zero official total where a priced/client-ready state is requested. | Block with explicit reason; owner-approved free exception required if intentional. |

## Visibility Rules

UI and API responses should distinguish preview, placeholder, official priced quote, and frozen snapshot:

- Intake V6 may show internal and commercial preview values with preview-only copy.
- Oferte quote cards and detail should not display `0,00 RON` for V6 draft placeholders as if it were a valid commercial total.
- Required UI copy for an unpriced V6 draft: `Draft nepretuit — Intake V6 are preview intern, dar oferta oficiala nu a fost generata.`
- Quote detail may show raw persisted totals only with a clear `unpriced draft` state when `grand_total <= 0` and V6 linkage requires pricing review.
- Client-offer preview and output composition should block or clearly mark zero commercial summaries for V6 unpriced drafts.
- Quote Snapshot V2 and acceptance surfaces must never use Intake V6 preview values as fallback official totals.
- Output export/download should be disabled or guarded when the commercial total is zero due to unpriced draft status.

Recommended blocker/warning codes:

- `V6_DRAFT_UNPRICED`
- `QUOTE_NOT_PRICED`
- `V6_OFFICIAL_TOTAL_MISSING`
- `V6_ZERO_TOTAL_BLOCKED`
- `V6_PREVIEW_NOT_OFFICIAL`
- `QUOTE_SNAPSHOT_V2_MISSING`

## Backend-Authoritative Pricing Boundary

The future backend boundary must answer these questions before writing official quote totals:

- Which immutable source payload was priced?
- Which pricing rules/version produced the totals?
- Which warnings/blockers were present?
- Which operator/owner action authorized persistence?
- Which quote columns and line items were written?
- Which snapshot/provenance record can later prove the total was not copied from a mutable UI preview?

The boundary should accept stable identifiers and source payload hashes, not frontend totals. It may read Intake V6/Product Truth/pricing input data server-side, run `CommercialPriceProposal` or a designated quote pricing adapter, and then persist quote totals only if all required pricing outputs are present and positive.

`POST /api/v1/entities/quotes/{quote_id}/price` already demonstrates the correct defensive shape for canonical quote pricing: backend computation, required price fields, and no silent fallback. The V6 bridge can reuse that discipline, but the exact adapter from V6 Product Truth/pricing input to commercial quote pricing remains `DOCUMENTED_NOT_IMPLEMENTED`.

## Data Contract

All contracts in this section are `DOCUMENTED_NOT_IMPLEMENTED`.

### V6 Priced Quote Bridge Request

```json
{
  "contract_status": "DOCUMENTED_NOT_IMPLEMENTED",
  "quote_id": 6,
  "source_module": "intake_v6",
  "source_workspace_id": "c8dda47f-e2a7-4fea-800c-2dc01b2be5a3",
  "source_workspace_code": "IV6-BB8EE3F8",
  "source_intake_request_code": "IR-MR18L96M",
  "source_product_truth_version": "product_truth_v1",
  "source_pricing_input_version": "intake_v6_pricing_input_preview_v1",
  "source_payload_hash": "server_computed_hash_required",
  "requested_action": "price_v6_draft_quote",
  "requested_by": "owner_or_pricing_operator_id"
}
```

### V6 Backend Pricing Result

```json
{
  "contract_status": "DOCUMENTED_NOT_IMPLEMENTED",
  "status": "priced_review_required",
  "quote_id": 6,
  "currency": "RON",
  "price": {
    "subtotal_net": 5386.66,
    "vat_amount": 1131.20,
    "grand_total": 6517.86,
    "vat_percent": 21.0
  },
  "line_items": [
    {
      "source_component_id": "volumetric_letters_primary",
      "description": "Litere volumetrice gradinita",
      "quantity": 19,
      "unit_price": "server_computed",
      "total": "server_computed"
    }
  ],
  "provenance": {
    "pricing_engine": "commercial_price_proposal_or_quote_pricing_adapter",
    "pricing_rules_version": "server_version_required",
    "source_payload_hash": "server_computed_hash_required",
    "computed_at": "server_timestamp",
    "computed_by": "server_actor"
  },
  "blockers": [],
  "warnings": []
}
```

Numbers above use the current observed runtime preview as an example only. They are not an instruction to persist those values.

### V6 Zero Blocker Response

```json
{
  "contract_status": "DOCUMENTED_NOT_IMPLEMENTED",
  "status": "blocked_zero_total",
  "blockers": [
    {
      "code": "V6_ZERO_TOTAL_BLOCKED",
      "message": "V6 quote cannot become client-ready with zero official total unless an owner-approved free quote policy is attached."
    }
  ]
}
```

## Zero Handling Policy

Zero is valid only for these cases:

- `V6_DRAFT_UNPRICED`, where zero means placeholder and must be labeled as such.
- Technical preview/read-only composition, where zero is accompanied by `QUOTE_NOT_PRICED` or equivalent warning.
- Explicit owner-approved free quote, with separate provenance and a reason code such as `OWNER_APPROVED_FREE_QUOTE`.

Zero is invalid for:

- pricing review completion,
- owner commercial approval,
- client-ready offer display,
- Quote Snapshot V2 creation/approval,
- accept quote,
- convert to order,
- output export presented as commercial offer.

Invalid zero should block with `V6_ZERO_TOTAL_BLOCKED` plus the more specific missing-state code, for example `QUOTE_NOT_PRICED` or `QUOTE_SNAPSHOT_V2_MISSING`.

## Quote Snapshot V2 Relation

Quote Snapshot V2 is downstream from backend-authoritative pricing. It should freeze official commercial truth after the quote has non-zero official totals, pricing review, and owner approval.

Quote Snapshot V2 must not pull totals from Intake V6 preview or Product Truth directly. It may reference source payload/provenance hashes for traceability, but the frozen commercial amounts must come from the persisted backend-priced quote or an explicitly attached priced commercial snapshot.

The current runtime has no output snapshots for quote #6. Therefore any future snapshot path remains blocked until a backend-priced total exists.

## Future Implementation Slices

1. `UI_LABEL_UNPRICED_DRAFT_FIRST`: Label V6 zero drafts as unpriced across Oferte card/detail/client-offer/output surfaces; block output export for unpriced drafts.
2. `BACKEND_PRICED_QUOTE_DRY_RUN_DESIGN_NEXT`: Add a backend dry-run contract that recomputes V6 commercial proposal server-side and returns proposed official totals without persisting.
3. `V6_PRICED_QUOTE_WRITE`: Add a guarded backend mutation that persists priced totals only from server-computed output and writes provenance.
4. `PRICING_REVIEW_STATE_WIRE`: Allow pricing review completion only when official totals are positive or an owner-approved free policy exists.
5. `QUOTE_SNAPSHOT_V2_ATTACH`: Freeze approved commercial totals into Quote Snapshot V2 and expose read-only output composition from that snapshot.

Only the first two slices are safe to consider next without changing pricing runtime behavior. Any mutating priced quote write needs explicit owner GO.

## Runtime Observation

Runtime checked read-only on 2026-07-01:

- URL: `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`
- Workspace: `IV6-BB8EE3F8`, id `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`
- Quote: `Q-V6-IV6-BB8EE3F8-1782910533`, id `6`
- Intake material total: `782.38 EUR`
- Intake commercial preview: `6517.86 RON` gross, `5386.66 RON` net
- Handoff preview: allowed, `preview_only=true`
- Quote persisted totals: `subtotal=0`, `total_before_vat=0`, `vat=0`, `grand_total=0`
- First line item: quantity `19`, `unit_price=0`, `total=0`
- Commercial spine blocker: `QUOTE_NOT_PRICED`
- Output composition commercial summary: subtotal `0`, VAT `0`, total `0`, currency `RON`
- Output snapshots: count `0`
- Oferte page shows V6 spine blocker but still prominently shows `0,00 RON` in quote cards/detail/client-offer preview.

No mutating CTA or endpoint was used during this observation.

## Forbidden Now

Do not implement these in this phase:

- Frontend/backend runtime changes.
- Database, schema, seed, or API changes.
- Product Truth persistence.
- Pricing runtime changes.
- ProductDefinition/ProductSystem runtime changes.
- Quote Snapshot runtime changes.
- Order Snapshot, ProductAggregate, Task Graph, or ExecutionPlan.
- Quote/order/task creation.
- Forced confirmations.
- Employee Mobile changes.
- Copying Intake UI preview totals into quote totals.
- Clicking CTAs that create, price, accept, snapshot, convert, or mutate a quote/order.

## Roadmap Alignment Checkpoint

- Roadmap source: `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- Current roadmap phase: `Phase 3 / Phase 6 boundary design — Product Truth to CommercialPriceProposal bridge`
- Status: `NEXT / V6 priced quote bridge design before implementation`
- Progress: `17/100% docs-only bridge design`
- Owner GO required next: YES

## Recommended Next Safe Slice

Recommended next slice: `C. SMALL_UI_LABEL_PLUS_BLOCKER_FIX`.

Reason: current runtime already blocks V6 conversion with `QUOTE_NOT_PRICED`, but Oferte cards/detail and client-offer/output surfaces still display `0,00 RON` as a prominent quote value. The smallest safe next change is to label and guard unpriced V6 drafts before introducing any backend priced quote computation or persistence.

## Fast Guard Implementation Note

Status: `IMPLEMENTED_BACKEND_GUARD_ONLY` on 2026-07-01.

The first practical backend slice chose option A from the fast-guard plan: V6 draft quote creation now blocks when the legacy V4 draft payload would persist zero commercial totals and zero line item prices for an Intake V6 quote. The guard returns `V6_QUOTE_PRICING_NOT_CONNECTED` with the message: `Intake V6 has preview values, but official V6 priced quote bridge is not implemented yet.`

This does not price the quote, does not copy frontend preview totals, and does not change legacy V4 placeholder draft behavior. It only prevents V6 from silently presenting the V4/V2 zero placeholder as commercial truth.

## Implemented Dry-Run Slice — V6 Backend Priced Quote Dry-Run

Status: `V6_PRICED_DRY_RUN_IMPLEMENTED` on 2026-07-01.

Implemented backend-only dry-run service and read-only endpoint:

- Service: `backend/services/intake_v6_priced_quote_dry_run_service.py`
- Endpoint: `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`

Pricing source used:

- V6 backend pricing input preview from `build_v6_pricing_input_preview`.
- V6 backend material breakdown trace from `get_material_breakdown_for_workspace`.
- Backend read-only `CommercialPriceProposalService` for commercial line items and subtotal.
- Company VAT from backend commercial settings.

The dry-run response includes:

- `pricing_status`: `V6_PRICED_DRY_RUN_READY` or `V6_PRICED_DRY_RUN_BLOCKED`
- `commercial_totals`: `subtotal_net`, `vat_rate`, `vat_amount`, `total_gross`, `currency`
- `commercial_line_items`
- `internal_cost_trace`
- `pricing_input_trace`
- `commercial_proposal_trace`
- `warnings`
- `blockers`
- `can_write_quote_totals=false`
- `can_create_quote_snapshot=false`
- `dry_run_only=true`
- explicit persistence flags showing no quote, snapshot, or order write

Blockers:

- `V6_PRICED_DRY_RUN_SOURCE_MISSING` when the backend pricing source is missing or unavailable.
- `V6_PRICED_DRY_RUN_ZERO_TOTAL` when backend dry-run cannot produce a positive commercial subtotal.
- Commercial proposal blockers/owner decision blockers are propagated into the dry-run result.

Boundary markers:

- `V6_PRICED_DRY_RUN_IMPLEMENTED`
- `QUOTE_TOTAL_WRITE_NOT_IMPLEMENTED`
- `QUOTE_SNAPSHOT_RUNTIME_NOT_IMPLEMENTED`
- `V2_V4_COMMERCIAL_TRUTH_FOR_V6_FORBIDDEN`

The dry-run does not use `build_v4_quote_draft_payload`, does not create or update quotes, does not create snapshots or orders, and does not copy frontend preview totals into quote totals. V4 remains legacy-isolated; it is not commercial truth for V6.

Next slice: design the V6 quote total write path only after owner GO. The write path must persist only backend-authoritative dry-run/pricing output, not V4 placeholders or frontend preview values.

## Implemented Write and Snapshot Slices

Status: `V6_PRICED_QUOTE_WRITTEN_IMPLEMENTED` and `QUOTE_SNAPSHOT_V2_IMPLEMENTED` on 2026-07-01.

After the dry-run, the guarded write slice now persists official V6 quote totals for eligible existing unpriced draft quotes. The Quote Snapshot V2 slice now freezes those persisted totals into `quote_output_snapshots` with `snapshot_type="QUOTE_SNAPSHOT_V2"`.

The bridge now has this implemented backend sequence:

```text
V6 backend priced dry-run
-> guarded V6 priced quote write
-> Quote Snapshot V2 from persisted quote totals
```

Still not implemented:

- `ORDER_SNAPSHOT_NOT_IMPLEMENTED`
- `PRODUCTAGGREGATE_NOT_IMPLEMENTED`
- `TASKGRAPH_NOT_IMPLEMENTED`
- `EXECUTIONPLAN_NOT_IMPLEMENTED`

Recommended next safe slice: `V6_QUOTE_ACCEPTANCE_GATE_DESIGN_NEXT`.

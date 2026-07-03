# BUILD — INTAKE_V3_REAL_COMMERCIAL_QUOTE_CREATION_GUARDED_DRAFT_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `b4c7279` — owner decision record and snapshot policy contracts  
**Verdict:** PASS (local, uncommitted)

---

## 1. Scope

First **real Quote write** from Intake V3, guarded:

- Owner decision explicit in request
- Snapshot payload attached in existing `Quotes.notes` JSON
- Anti-duplicate check via `Quotes.intake_code = IV3-{workspace_id}`
- Full readiness chain validated before create
- Quote created as **`draft` only**
- **No** Order, ExecutionPlan, ExecutionTask, Inventory, CostEngine, pricing formula changes

## 2. Quote model / linkage audit

### Existing `Quotes` model (`backend/models/quotes.py`)

| Field | Use in this build |
|-------|-------------------|
| `code` | Generated `Q-IV3-{workspace_code}-{timestamp}` |
| `status` | `draft` |
| `intake_id` | `NULL` (no Intake V1/V2 linkage) |
| `intake_code` | **`IV3-{workspace_id}`** — anti-duplicate lookup key |
| `client_name` | From workspace `client_request.client_name` |
| `line_items` | JSON string — single line, zero pricing |
| `notes` | JSON bundle with `intake_v3_linkage_v1` snapshot + owner decision |
| totals (`subtotal`, `grand_total`, …) | `0` — Variant B pricing |

No dedicated `source_module`, `metadata`, or `quote_input` columns on `Quotes`.  
**No DB migration required.**

### Status values in repo

`draft`, `priced`, `sent`, `viewed`, `negotiating` (see `backend/routers/quotes.py`).

### Endpoints intentionally **not** used

- `POST /api/v1/entities/quotes/from-intake/{intake_id}` — Intake V1/V2 only
- `POST /api/v1/entities/quotes/price` — would invoke CostEngine (out of scope)

### Endpoint added

`POST /api/v1/intake-v3/workspaces/{workspace_id}/create-draft-quote`

Requires authenticated user (`get_current_user`).

## 3. Persistence strategy

```json
{
  "human_summary": "Draft quote from Intake V3 workspace … Requires pricing review.",
  "intake_v3_linkage_v1": {
    "source_module": "intake_v3",
    "source_workspace_id": "<workspace_id>",
    "requires_pricing_review": true,
    "pricing_source": "intake_v3_preview_only",
    "owner_decision": { … },
    "snapshot": { … policy sections … },
    "integrity_markers": {
      "raw_analysis_not_production_truth": true,
      "confirmed_model_production_truth": true,
      "holes_not_letters": true
    }
  }
}
```

Anti-duplicate: `QuotesService.list_by_field("intake_code", "IV3-{workspace_id}")`.

## 4. Pricing decision — Variant B

- No CostEngine call
- `requires_pricing_review = true`
- `pricing_source = intake_v3_preview_only`
- Totals remain zero on draft row

## 5. Owner decision capture

Captured at request time into snapshot + `notes` linkage:

- `owner_user_id`, `owner_display_name` from `UserResponse`
- `decision_status = approved`, `approval_checkbox = true`, non-empty `decision_reason`
- `decision_timestamp`, `approved_workspace_id`, bridge hash marker, snapshot policy version

Blocked with `OWNER_DECISION_REQUIRED` / `OWNER_IDENTITY_UNCLEAR` when missing.

## 6. Guard chain (`validate_real_quote_creation_allowed`)

Validates: workspace exists, not archived, template `TPL-VOLUMETRIC-LETTERS`, confirmed production model, finish assignment, quote readiness not blocked, prequote review present, full policy chain built, safety confirmations, expected bridge/enablement status match, snapshot buildable, no duplicate quote.

Does **not** block on preview-only markers (`BRIDGE_DISABLED_BY_POLICY`, `REAL_QUOTE_CREATION_NOT_ENABLED`) — this build is the guarded exception with explicit owner approval.

## 7. Files

**Created**

- `backend/services/intake_v3_real_commercial_quote_creation_service.py`
- `backend/tests/test_intake_v3_real_commercial_quote_creation.py`
- `frontend/src/components/workos/intake-v3/IntakeV3CreateDraftQuotePanel.tsx`
- `docs/qa/BUILD_INTAKE_V3_REAL_COMMERCIAL_QUOTE_CREATION_GUARDED_DRAFT_FOUNDATION.md`

**Modified**

- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `frontend/src/lib/intakeV3/api.ts`, `contracts.ts`, `flowState.ts`, `flowState.test.ts`
- `frontend/src/pages/IntakeV3App.tsx`, `IntakeV3App.test.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3CommandBar.tsx`, `IntakeV3PreviewShell.tsx`, `IntakeV3FlowStepper.tsx`
- Intake V3 + TPL docs (status, roadmap, decisions, adapters)

## 8. Tests

| Suite | Result |
|-------|--------|
| `test_intake_v3_real_commercial_quote_creation.py` + readiness + bridge | **30 passed** |
| Intake V3 regression (15 files) | **153 passed** |
| `IntakeV3App.test.tsx` + `flowState.test.ts` | **120 passed** |

## 9. Boundary confirmation

- No Order / ExecutionPlan / ExecutionTask / Inventory mutation
- No CostEngine / pricing formula / TVA / markup changes
- No push, no ZIP, no commit in this build step
- Readiness GET endpoints remain read-only

## 10. Open questions

- Future build may add dedicated quote linkage table or `quote_input` attachment before `/price`
- Owner decision persistence is per-quote in `notes` — no separate audit table yet
- Readiness GET still reports `can_create_quote_now=false` by design (policy contract unchanged)

## 11. Recommended commit message

```
feat(intake-v3): add guarded draft commercial quote creation from workspace

Create draft Quote rows from Intake V3 with owner approval, snapshot in notes, IV3 intake_code anti-duplicate, and no order/execution/inventory/CostEngine side effects.
```

# BUILD_INTAKE_V4_QUOTE_TO_ORDER_AND_OWNER_APPROVAL_PACK

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `403518eadee87727c0ae35f30e46ea48205dc4cb` |
| Build | V4 quote → order commercial spine + owner approval (no real tasks) |

## Working tree status (off-scope — do NOT commit)

- V2/V3 operator workspace WIP (`intake-v3/*`, AuthContext, etc.)
- `tmp/` scripts and atoms exports
- E2E specs off-scope
- This build touches **only** Intake V4 quote/order spine files listed below

## Build flags

```txt
creates_execution_tasks=false
writes_execution_plan=false
stock_consumption=false
owner_approval_persisted=true
v4_quote_to_order_enabled=true
can_generate_real_tasks=false
```

## Files audited (Part 1)

| Area | Path |
|------|------|
| Quote model | `backend/models/quotes.py`, `backend/services/quotes.py` |
| V4 draft quote | `backend/services/intake_v4_commercial_quote_service.py` |
| IV3 pricing review | `backend/services/intake_v3_quote_pricing_review_completion_service.py` |
| IV3 accept | `backend/services/intake_v3_guarded_accept_flow_service.py` |
| IV3 convert | `backend/services/intake_v3_guarded_convert_to_order_service.py` |
| IV3 linkage utils | `backend/services/intake_v3_quote_linkage_utils.py` |
| Order model | `backend/models/orders.py`, `backend/services/orders.py` |
| V4 readiness | `backend/services/intake_v4_order_bound_task_readiness_service.py` |
| Execution plan | `backend/models/execution_plan.py` |

### A. Quote model and statuses

1. **V4 draft quote** uses standard `Quotes` ORM via `create_guarded_draft_quote_from_intake_v4_workspace`.
2. **Statuses:** `draft`, `priced`, `sent`, `in_negociere`, `accepted`, `rejected`, `expired` (lifecycle via `validate_transition`).
3. **Draft / priced / accepted:** draft = unpriced handoff; priced = intermediate after pricing review path; accepted = commercial approval (`IV3_ACCEPTED_STATUS` = `accepted`, reused for V4).
4. **`requires_pricing_review`:** stored in `intake_v4_linkage_v1.requires_pricing_review`; cleared by `pricing_review.status=completed` record under linkage key `pricing_review`.
5. **`intake_v4_linkage_v1`:** quote `notes` JSON root key; contains snapshot, quote_input, flags, decisions.
6. **Notes/snapshot:** full workspace snapshot under `linkage.snapshot`; commercial totals on quote columns after pricing review.
7. **IV3 accept/convert:** dedicated guarded services on `/api/v1/intake-v3/quotes/{id}/…`; reject non-`IV3-*` intake codes (`NOT_IV3_QUOTE`).
8. **IV3 guards preserved:** IV3 paths unchanged; V4 uses parallel V4-only service with `is_iv4_quote()` guard (`NOT_IV4_QUOTE`).

### B. Order model and convert flow

1. **Order:** `backend/models/orders.py` — `Orders` table.
2. **Creation today:** IV3 `convert_v3_quote_to_order`; V4 adds `convert_v4_quote_to_order`.
3. **Fields:** `code`, `quote_id`, `client_name`, `status`, `total_amount`, `snapshot_line_items`, `notes`, `readiness_snapshot`, `locked_at`.
4. **Frozen snapshot:** `snapshot_line_items` JSON (IV3/V4 pattern); V4 adds `intake_v4_order_linkage_v1` + handoff snapshots.
5. **`orders.quote_id`:** direct FK-style link; duplicate guard via `check_existing_order_for_iv3_quote` (generic by quote_id).
6. **Initial V4 order status:** `locked` (`IV3_ORDER_STATUS_LOCKED`).
7. **Order-bound readiness:** requires quote accepted, order exists, order status in `{locked, in_production, confirmed}`, no execution plan.
8. **Duplicate risk:** blocked at convert with `ORDER_ALREADY_EXISTS`.

### C. Current V4 draft quote

1. **`create-draft-quote`** creates draft `Quotes` row, `intake_code=IV4-{workspace_id}`, attaches snapshot + `requires_pricing_review=true`.
2. **Snapshot in notes:** `quote_input_payload`, `workspace_payload_snapshot`, integrity rules, analysis hash.
3. **Was missing (now added):** V4-native pricing review completion, owner approval, accept, convert.
4. **Preserved:** draft create guards, analysis hash sync, no order/execution/inventory on draft create.

## Files changed

| File | Change |
|------|--------|
| `backend/services/intake_v4_quote_to_order_service.py` | **NEW** commercial spine service |
| `backend/services/intake_v4_quote_linkage_utils.py` | **NEW** V4 linkage helpers |
| `backend/routers/intake_v4_quotes.py` | **NEW** quote-level endpoints |
| `backend/schemas/intake_v4.py` | Request/response schemas + readiness fields |
| `backend/services/intake_v4_order_bound_task_readiness_service.py` | pricing_review / owner_approval / v4_order_conversion |
| `backend/tests/test_intake_v4_quote_to_order_owner_approval.py` | **NEW** 29 tests |
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | API client + types |
| `frontend/src/components/workos/intake-v4/IntakeV4QuoteCommercialSpinePanel.tsx` | **NEW** action panel |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Wire panel |

## V4 commercial transition design

Single service `intake_v4_quote_to_order_service.py`:

- `complete_v4_pricing_review` — manual totals, sets `requires_pricing_review=false`, quote stays `draft`
- `persist_v4_owner_approval` — `owner_approval_v1` with analysis_hash + acknowledgments
- `accept_v4_quote` — draft→priced→accepted, guards pricing/approval/hash/readiness
- `convert_v4_quote_to_order` — single locked Order, frozen V4 snapshot, no ExecutionPlan
- `get_v4_commercial_spine_state` — UI/readiness helper

Safety counters: Orders + ExecutionPlan counts before/after each mutating step.

## Endpoints

| Method | Path |
|--------|------|
| GET | `/api/v1/intake-v4/quotes/{quote_id}/commercial-spine-state` |
| GET | `/api/v1/intake-v4/workspaces/{workspace_id}/commercial-spine-state` |
| POST | `/api/v1/intake-v4/quotes/{quote_id}/complete-pricing-review` |
| POST | `/api/v1/intake-v4/quotes/{quote_id}/owner-approval` |
| POST | `/api/v1/intake-v4/quotes/{quote_id}/accept` |
| POST | `/api/v1/intake-v4/quotes/{quote_id}/convert-to-order` |
| GET | `/api/v1/intake-v4/workspaces/{id}/order-bound-task-readiness` (extended response) |

## Order frozen snapshot shape

`orders.snapshot_line_items` JSON:

- `source_intake_version=V4`, `source_workspace_id`, `source_quote_id`, `analysis_hash`, `template_code`
- `workspace_payload_snapshot`, `quote_input_payload`
- `owner_approval_snapshot`, `pricing_review_snapshot`, `accept_decision_snapshot`
- `handoff_snapshots`: material breakdown, production handoff preview, task dry-run summary
- `no_execution_plan_created=true`, `execution_plan_created=false`, `inventory_mutated=false`

## UI changes

`IntakeV4QuoteCommercialSpinePanel` on Review step:

- Pricing review / owner approval / accept / convert buttons (disabled when blocked)
- Explicit copy: no real tasks, no execution plan, no stock
- Order id after convert; refresh + readiness reload

## What this build does NOT do

- No `ExecutionTask` creation
- No `ExecutionPlan` create/update
- No `execution_plan.tasks_json` writes
- No stock consumption or reservations
- No CostEngine / Pricing Registry changes
- No Employee Mobile changes
- No real task generation (`can_generate_real_tasks` stays false)

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_quote_to_order_owner_approval.py -q
# 29 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_order_bound_task_readiness.py -q
# 18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py -q
# 11 passed
```

Note: combined multi-file pytest run can hit module-scope event-loop fixture conflict; run separately.

## Frontend tests

No dedicated Vitest harness for Intake V4 commercial spine panel yet (Review step loads panel via existing workspace hook). UI verified via component wiring only.

## PASS / FAIL

**PASS** — all PASS criteria met (see build spec).

## Pricing review totals policy (post-fix)

- **Variant A implemented:** `complete-pricing-review` does **not** accept commercial totals from UI.
- Backend reads totals exclusively from the priced `Quotes` row (`grand_total`, `subtotal`, `vat`, etc.).
- If quote is unpriced (`grand_total <= 0`), endpoint returns **`QUOTE_NOT_PRICED`** and flow stays blocked.
- Request schema uses `extra=forbid` — sending `subtotal`/`total`/etc. from UI returns **422** validation error.
- Pricing review linkage records `pricing_totals_source=quote_columns` and `pricing_totals_captured=true`.
- Order snapshot inherits totals from quote/pricing review — **never** from UI placeholders.
- Operator must price via **QuoteWizard** before Intake V4 pricing review completion.

## Risks remaining

- Combined pytest module ordering still fragile for V4 client fixtures.
- Order snapshot handoff sub-services may capture `{error, captured:false}` for edge workspaces without failing convert.
- `can_generate_real_tasks` remains false until controlled execution plan write build.

## Next recommended builds

1. `BUILD_TPL_VOLUMETRIC_OPERATION_KEYS_ALIGNMENT_PACK`
2. `BUILD_INTAKE_V4_CONTROLLED_EXECUTION_PLAN_WRITE_PACK` (only after alignment + owner approval path confirmed in staging)

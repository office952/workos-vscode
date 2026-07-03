# BUILD_INTAKE_V4_INTERNAL_DRAFT_QUOTE_CONFIRMATION_POLICY

## Purpose

Gate Intake V4 **internal draft quote** creation behind explicit operator confirmation, split **fatal blockers** from **review-only warnings**, and keep client send / accept / order / production blocked when artwork or pricing review warnings remain.

## Owner decision

- `finish_setup_incomplete` → **fatal** for internal draft quote
- Operator confirmation → **required** for internal draft
- `artwork needs_decision` → **warning** (allows internal draft, review-only)
- `artwork needs_decision` → **blocker** for client send / accept / order / production

## Fatal blockers (internal draft)

- missing SVG / analysis (`missing_svg_analysis`, `missing_svg_analysis_json`, `degraded_child_parts_analysis`)
- layer roles incomplete
- `finish_setup_not_confirmed` / `finish_setup_incomplete`
- missing required RAL/Oracal color (`missing_face_oracal_color:*`, `missing_ral_color:*`, `missing_return_oracal_color:*`)
- invalid geometry (`missing_quote_geometry*`)
- pricing baseline unavailable (empty `quote_input` baseline)
- lighting config invalid when illuminated (`lighting_config_invalid:*`)
- `operator_confirmation_missing`
- hash sync failures at create time (`analysis_hash_mismatch`, `missing_client_analysis_hash`)

## Review warnings (internal draft allowed, review-only)

- `artwork_execution_undecided:*`
- `manual_pricing_review_required`
- `material_availability_warning` / `material_availability:*`
- `template_pricing_code_missing` (non-critical optional pricing)

When warnings exist:

- `requires_pricing_review = true`
- `client_send_allowed = false`
- `accept_allowed = false`
- `convert_to_order_allowed = false`
- `production_allowed = false`

## Operator confirmation

**Persisted field:** `payload.finish_setup.internal_draft_quote_confirmed` (default `false`)

**Endpoint:** `PUT /api/v1/intake-v4/workspaces/{id}/internal-draft-quote-confirmation`

**Invalidation:** reset to `false` on finish setup save, layer role changes, SVG/analysis bundle changes (non-replace path), SVG reupload.

**UI:** Confirm step checkbox — *Confirm finisajele și datele de ofertare pentru draft intern*

## Quote handoff preview

`GET .../quote-handoff-preview` returns:

- `can_create_internal_draft_quote`
- `requires_operator_confirmation`
- `operator_confirmation_complete`
- `fatal_blockers[]`
- `review_warnings[]`
- `client_send_allowed`, `accept_allowed`, `convert_to_order_allowed`, `production_allowed`
- `status_label`: `READY_FOR_INTERNAL_DRAFT_REVIEW` when warnings only (no fatals)

## Create draft quote

`POST .../create-draft-quote` requires:

- `confirm_internal_draft_quote: true`
- persisted `internal_draft_quote_confirmed: true`
- no fatal blockers

Creates `status=draft` quote with snapshot flags blocking client/order/production handoff.

**Explicit errors:** `INTERNAL_DRAFT_CONFIRMATION_REQUIRED`, `INTERNAL_DRAFT_QUOTE_BLOCKED`

## Send / accept / order / production boundary

No V4 client-send or convert-to-order endpoints changed in this build. Draft quote snapshot + linkage persist:

- `client_send_allowed: false`
- `convert_to_order_allowed: false`
- `production_allowed: false`
- `internal_draft_review_only: true` when review warnings present

## Files changed

| Area | Files |
|------|-------|
| Policy | `backend/services/intake_v4_internal_draft_quote_policy_service.py` |
| Color fatal | `backend/services/intake_v4_finish_truth_service.py` |
| Quote handoff | `backend/services/intake_v4_commercial_quote_service.py` |
| Persistence | `backend/services/intake_v4_workspace_service.py` |
| Schema | `backend/schemas/intake_v4.py` |
| Router | `backend/routers/intake_v4_workspaces.py` |
| UI | `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx` |
| Readiness | `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.ts` |
| API types | `frontend/src/lib/intakeV4/intakeV4Api.ts` |

## Tests

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./test_policy.db'
$env:JWT_SECRET_KEY='local-dev-secret'
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_internal_draft_quote_confirmation_policy.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_commercial_quote.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx
```

**Results (2026-06-23):**

- Policy tests: **7 passed**
- Commercial quote tests (isolated): **6 passed**
- Frontend scoped tests: **9 passed**

## Runtime smoke (PBL)

Workspace: `IV4-4B172FD4` / `0f300dcf-0b77-4fc1-affd-6e2a20329804`

**Deferred in-agent** — requires live stack + operator session. Manual checklist:

1. Confirm finish setup in Review
2. Confirm Summary values OK
3. Handoff shows fatal blockers when finish incomplete
4. After operator internal confirmation with only `artwork needs_decision`:
   - Badge `READY_FOR_INTERNAL_DRAFT_REVIEW`
   - Create internal draft allowed
   - Draft has `requires_pricing_review=true`, client/order/production flags false
5. No order/tasks/stock

Mark test drafts: `INTERNAL TEST DRAFT — DO NOT SEND — PBL`

## Remaining blockers / boundary

- V4 client-send / quote-accept / convert-to-order UI not in scope — enforced via snapshot flags only
- Full `validate:frontend` still has unrelated TS debt
- Material breakdown fatal path not wired separately (relies on geometry + pricing baseline)
- Pytest module fixture isolation: run policy + commercial quote test files separately if `seeded_db` conflicts

## Out of scope (confirmed)

- No Pricing Registry / CostEngine / inventory / ExecutionPlan / tasks_json / stock consumption
- No push in this build

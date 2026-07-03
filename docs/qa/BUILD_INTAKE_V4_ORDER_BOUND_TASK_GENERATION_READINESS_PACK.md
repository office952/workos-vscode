# BUILD_INTAKE_V4_ORDER_BOUND_TASK_GENERATION_READINESS_PACK

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `8539061630e9febb0ee9bdf432bca2598cf7d290` |
| Build | Order-bound task generation readiness (read-only guard) |

## Working tree before (dirty, off-scope — do NOT commit)

- V2/V3 operator workspace WIP (`intake-v3/*`, `useIntakeV3OperatorWorkspace.ts`, etc.)
- `tmp/` scripts and atoms exports
- E2E specs off-scope (`intake-v4-pbl-complex-desktop.spec.ts`, etc.)
- Audit/atoms docs untracked

## Purpose

Extend Intake V4 from **task generation dry-run contract** to **order-bound task generation readiness**: explicit answer to “Can this V4 workspace generate real production tasks for a real Order?” without creating `ExecutionTask`, writing `execution_plan.tasks_json`, or mutating Quote/Order/Production.

**Build flags (always false in this build):**

```txt
creates_execution_tasks=false
writes_to_production=false
stock_consumption=false
dry_run_only=true
order_bound_readiness=true
```

## Files audited

| Area | Path |
|------|------|
| V4 commercial quote | `backend/services/intake_v4_commercial_quote_service.py` |
| V4 task dry-run | `backend/services/intake_v4_task_generation_dry_run_service.py` |
| V4 handoff preview | `backend/services/intake_v4_production_handoff_preview_service.py` |
| V4 template contract | `backend/services/intake_v4_template_option_contract_service.py` |
| V3 quote linkage utils | `backend/services/intake_v3_quote_linkage_utils.py` |
| V3 convert/order lookup | `backend/services/intake_v3_guarded_convert_to_order_service.py` |
| V3 order production readiness | `backend/services/intake_v3_order_production_readiness_service.py` |
| Execution plan model | `backend/models/execution_plan.py` |
| Orders model | `backend/models/orders.py` |

## Files modified / added

| File | Change |
|------|--------|
| `backend/services/intake_v4_order_bound_task_readiness_service.py` | **NEW** readiness orchestrator |
| `backend/services/intake_v4_commercial_quote_service.py` | `parse_intake_v4_linkage_from_notes()` |
| `backend/schemas/intake_v4.py` | Readiness response schemas; removed duplicate dry-run schema block |
| `backend/services/intake_v4_workspace_service.py` | Workspace wrapper |
| `backend/routers/intake_v4_workspaces.py` | GET endpoint |
| `backend/tests/test_intake_v4_order_bound_task_readiness.py` | **NEW** 18 tests |
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | Types + API client |
| `frontend/src/components/workos/intake-v4/IntakeV4OrderBoundTaskReadinessPanel.tsx` | **NEW** UI panel |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Load + render panel |

## Audit — Quote / Order / Production

### Quote / draft quote (Intake V4)

1. **Entity:** standard `Quotes` ORM row created via `create_guarded_draft_quote_from_intake_v4_workspace`.
2. **Workspace linkage:** `intake_code = IV4-{workspace_id}`; notes JSON key `intake_v4_linkage_v1`.
3. **Snapshot fields:** `source_workspace_id`, `source_workspace_code`, `quote_input_payload`, `workspace_payload_snapshot`, `policy_version`, `integrity_rules` (`CLIENT_ANALYSIS_HASH_SYNCED`, `DRAFT_QUOTE_REQUIRES_PRICING_REVIEW`, …).
4. **`requires_pricing_review`:** always `true` on V4 draft create; cleared only via pricing review completion flow (shared IV3 linkage helpers).
5. **Acceptance:** IV3 pattern — `accept_decision.status=approved` and/or quote `status=accepted`.
6. **Relevant statuses:** `draft`, `sent`, `in_negociere`, `accepted`.
7. **Conversion guard:** V4 has no guarded convert yet; V3 uses `intake_v3_guarded_convert_to_order_service`.
8. **Audit:** quote create logs `Draft quote created from Intake V4: quote_id=…`.

### Order

9. **Creation:** V3 guarded convert (`POST …/convert-to-order`); V4 path not implemented yet.
10. **Quote → Order:** `orders.quote_id`; lookup via `check_existing_order_for_iv3_quote` (generic by `quote_id`).
11. **Statuses:** `locked`, `in_production`, `confirmed` = ready; `cancelled`/`completed`/`delivered` = terminal.
12. **Production ready:** locked order + no duplicate execution plan (V3 readiness pattern).
13. **Fields:** `order_id`, `order_code`, `quote_id` exist; no dedicated `workspace_id` on Order — trace via quote `intake_code` / linkage snapshot.
14. **Execution plan:** `execution_plan` table per `order_id`; `tasks_json` JSON array.
15. **Anti-duplicate:** readiness blocks when `ExecutionPlan` count > 0 for order.

### Production

16. **Real tasks:** generated into `execution_plan.tasks_json` from frozen order snapshot (Execution router / blueprint services) — **not** from Intake V4 workspace directly.
17. **`execution_plan.tasks_json`:** yes — canonical planned tasks JSON.
18. **`ExecutionTask`:** no separate ORM; tasks are dicts inside plan JSON (+ `execution_reality.tasks_json`).
19. **Services:** `execution_task_assignment_service`, order production blueprint, execution router.
20. **Out of scope this build:** all writes above, CostEngine, stock, Employee Mobile.

## Endpoint

```http
GET /api/v1/intake-v4/workspaces/{workspace_id}/order-bound-task-readiness
```

Read-only. Returns `IntakeV4OrderBoundTaskReadinessResponse`.

## Readiness response contract (summary)

- `readiness_mode`: `order_bound_task_generation_readiness`
- `linked_quote` / `linked_order` summaries
- `can_generate_real_tasks`: always `false` in this build
- `can_generate_reason`: primary blocking code
- `owner_confirmation_required`: always `true`
- `dry_run_summary`, `idempotency_summary`
- `pricing_status`, `template_contract_status`, `analysis_hash_status`
- `future_generation_contract` (`intake_v4_task_generation_v1`)

## Readiness rules

### A. Analysis / Intake

- Analysis boundary blockers propagate
- Hash sync blockers
- Finish setup not confirmed
- Layer roles incomplete
- Unsupported template (`template_out_of_scope`)
- Template option contract critical blockers

### B. Commercial

- `quote_missing`
- `quote_snapshot_invalid`
- `requires_pricing_review`
- `quote_not_accepted`
- `quote_status_not_ready` (draft/sent/in_negociere)
- `quote_snapshot_hash_mismatch`
- `quote_snapshot_workspace_id_mismatch`

### C. Order

- `order_missing`
- `order_not_linked_to_quote`
- `order_status_not_ready_for_production`
- `order_already_has_execution_plan`
- `order_terminal_status`
- `order_client_missing`

### D. Dry-run

- `dry_run_critical_blockers`
- `dry_run_no_task_candidates`
- `dry_run_all_provisional`
- `dry_run_idempotency_plan_missing`

### E. Confirmation

- `owner_confirmation_required` (marker only — no real confirmation UI in this build)

## Future generation contract

```json
{
  "contract_version": "intake_v4_task_generation_v1",
  "target_entity": "Order",
  "target_order_id": null,
  "requires_owner_confirmation": true,
  "requires_idempotency_check": true,
  "requires_analysis_hash_sync": true,
  "requires_quote_accepted": true,
  "requires_order_ready": true,
  "would_create_execution_tasks": false,
  "would_write_execution_plan": false,
  "next_action_label": "Create production tasks",
  "next_action_enabled": false
}
```

## Boundary guarantees (this build)

| Guarantee | Status |
|-----------|--------|
| Endpoint read-only | Yes — `GET` only, no DB writes or status mutations |
| Creates `ExecutionTask` | No |
| Writes `execution_plan.tasks_json` | No |
| Mutates Quote / Order / Production | No |
| Accept / convert quote | No |
| `can_generate_real_tasks` | Always `false` in this build (**intentional** — gate only) |
| `owner_confirmation_required` | Marker only — **not** a real operator confirmation flow |
| Real task generation | **Separate follow-up build** (`intake_v4_task_generation_v1` contract) |

## What this build does NOT do

- No `ExecutionTask` creation
- No `execution_plan` / `tasks_json` writes
- No Order/Quote status changes
- No quote accept/convert
- No stock consumption/reservation
- No CostEngine / Pricing changes
- No real “Create production tasks” button
- No V2/V3 dirty file changes
- No commit/push (await owner confirmation)

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_order_bound_task_readiness.py -q
# 18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py tests/test_intake_v4_production_handoff_preview.py -q
# 17 passed
```

Note: running all three files in one pytest invocation can hit a pre-existing `seeded_db` module-scope **event-loop conflict between test modules** (pytest-asyncio / Windows). This is a **combined-run harness issue**, not a failure of this build — each module passes when run separately (35 passed total).

## Frontend tests

Vitest **not run** — panel is presentational (maps API response); no new client-side logic beyond fetch + display. Types added in `intakeV4Api.ts`.

## Result

**PASS** — all PASS criteria met for this build boundary.

## Commit recommendation

Recommend a **scoped commit** (V4 readiness only) after owner review:

```txt
feat(intake-v4): add order-bound task generation readiness guard

Read-only readiness layer before real ExecutionTask creation: quote/order
linkage, dry-run summary, idempotency preview, future generation contract.
No production writes.
```

Exclude V2/V3 WIP, `tmp/`, and off-scope E2E from the commit.

## Follow-ups

1. Owner approval UI (real confirmation gate)
2. Controlled real `ExecutionTask` / `execution_plan` write build
3. Idempotency storage + regeneration policy
4. Duplicate prevention at write time
5. V4 guarded accept + convert to order
6. Order production binding hardening
7. Employee assignment + Mobile visibility
8. Stock reservation (separate build)

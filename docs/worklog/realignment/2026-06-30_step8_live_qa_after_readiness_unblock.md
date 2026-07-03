# Step 8 Live QA After Readiness Unblock — 2026-06-30

## Status

**BLOCKED_BACKEND_STALE**

Live QA stopped at stale-check gate. HTTP preview on `:8000` still returns `blocked_snapshot_conflict` for paper QA payload. Code at HEAD `c8d86d1` expects `partial_with_owner_decisions`. No freeze/accept/convert writes performed.

## Scope

Controlled live QA after readiness unblock. **No** app/backend/frontend start or restart by agent. **No** code changes.

## Architecture readback

Confirmed: Step 8 freeze/accept/convert ≠ Step 9; ExecutionPlan/tasks out of scope; commercial/internal separate; no `/price`/CE/QO; order snapshot V2 is copy not reprice; `partial_with_owner_decisions` may need owner ack at accept.

**Alignment: ALIGNED** (not exercised live)

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `c8d86d1` — `fix(step8): unblock dev snapshot readiness` |
| Unexpected code changes | None |

## Backend stale check

| Check | Result |
|-------|--------|
| `GET http://127.0.0.1:8000/health` | **200** `{"status":"healthy"}` |
| `POST .../preview/TPL-VOLUMETRIC-LETTERS_v2` + `_step8_qa_quote_input()` | **200**; `readiness=blocked_snapshot_conflict`; commercial/internal **blocked** |
| Expected (code `c8d86d1`) | `readiness=partial_with_owner_decisions` |
| **Stale** | **YES** |
| Backend restart by owner | **NO** (agent did not restart) |

### Owner restart (manual)

From repo root:

```powershell
cd C:\Users\offic\Desktop\workos-active
npm run dev:backend
```

Or stop existing uvicorn on `:8000` first, then re-run. After restart, re-run this QA task from stale-check → backup → freeze → accept → convert.

## Backup

**Not created** — stopped before any live write (stale gate).

Rollback N/A for this run.

## Baseline DB counts (read-only)

| Table | Count |
|-------|-------|
| `intake_v6_workspaces` | 67 |
| `quote_snapshots_v2` | 1 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| `quotes` with `accepted_snapshot_v2_id` | **0** |

Sample workspaces: `4cbd138f-...` / `46a6bc8f-...` — `ready_for_quote_preview` (candidate identity after restart).

Sample quotes: ids 1–4, all `draft`, `accepted_snapshot_v2_id=null`, `grand_total=0`.

## Safe payload source

- Helper: `backend/tests/test_quote_snapshot_v2.py` — `_step8_qa_quote_input()` (paper sablon)
- Template: `TPL-VOLUMETRIC-LETTERS_v2`
- Expected readiness (fresh backend): `partial_with_owner_decisions`

## Persist identity (for follow-up after restart)

Freeze persist requires `quote_id` **or** `workspace_id` in freeze body. Candidates exist in DB but were **not** used (stale STOP).

Accept additionally requires V6 `pricing_review` + `owner_approval` gates on quote linkage (per `accept_v6_quote`).

## Freeze / Accept / Convert

| Stage | Result |
|-------|--------|
| Freeze | **NOT RUN** |
| Accept | **NOT RUN** |
| Convert | **NOT RUN** |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**122 passed**

## Files changed

Worklog only (this file).

## No-side-effects confirmation

No code, UI, migration, seed, DB writes, backup, freeze/accept/convert API calls, order/plan/task creation, app/backend/frontend start, push, work in `C:\Users\offic\workos`.

## Next recommended step

**Owner restarts backend manually**, then **re-run Step 8 live QA after readiness unblock** — stale preview must show `partial_with_owner_decisions` before backup and freeze with `workspace_id` or `quote_id`.

## Roadmap awareness

Step 8 readiness fix is in repo (`c8d86d1`); live runtime not yet validated. Step 9 remains **BLOCKED**.

**Cât sunt în direcția stabilită: 87/100%**

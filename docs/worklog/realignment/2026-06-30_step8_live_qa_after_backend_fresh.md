# Step 8 Live QA After Backend Fresh — 2026-06-30

## Status

**BLOCKED_BACKEND_NOT_RUNNING**

Owner reported manual backend start via `.\scripts\start-dev.ps1` or `.\scripts\dev-backend.ps1`. Agent probe: **connection refused** on `http://127.0.0.1:8000/health`. Live preview/freeze/accept/convert **not run**. No backup. DB unchanged.

## Scope

QA only — no code, no app/backend/frontend start by agent, no DB manual writes, no Step 9, no push.

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `7b171bc` — `docs(step8): record VS Code app audit` |
| Unexpected code changes | None (worklog-only delta expected; prior untracked worklogs remain) |

## Health

| Probe | Result |
|-------|--------|
| `GET http://127.0.0.1:8000/health` | **FAILED** — `Unable to connect to the remote server` |

## Freshness (preview paper QA)

| Probe | Result |
|-------|--------|
| `POST …/quote-snapshot-v2/preview/TPL-VOLUMETRIC-LETTERS_v2` | **NOT RUN** (no listener on `:8000`) |
| Expected readiness | `partial_with_owner_decisions` |
| Stale signal | **Cannot verify** — backend unreachable |

### Paper payload reference

From `backend/tests/test_quote_snapshot_v2.py` → `_step8_qa_quote_input()` (paper sablon via `mounting_template_material_type="paper"`).

## Safe identity (read-only DB verify — still valid)

| Type | Value | Status |
|------|-------|--------|
| Workspace | `96009ff3-a20b-40d7-a8c7-540e48058526` | `IV6-AA7F2532`, `ready_for_quote_preview` |
| Quote | `id=1` — `Q-V6-IV6-AA7F2532-1782719582` | `draft`, `accepted_snapshot_v2_id=null` |

Identity exists; live persist path not exercised.

## Backup

**Not created** — stopped before any HTTP write (health gate failed).

## Baseline DB counts (read-only)

| Table / metric | Count |
|----------------|-------|
| `quote_snapshots_v2` | 1 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| `execution_tasks` | N/A — table not present in `dev.db` |
| `quotes.accepted_snapshot_v2_id` set | 0 |

## Freeze / Accept / Convert

| Stage | Endpoint | Result |
|-------|----------|--------|
| Freeze | `POST /api/v1/product-system/quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS_v2` | **NOT RUN** |
| Accept | `POST /api/v1/intake-v6/quotes/{quote_id}/accept` | **NOT RUN** |
| Convert | `POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order` | **NOT RUN** |

## DB verification after live chain

N/A — no live writes.

## No execution side effects

Confirmed by absence of live run: no new `execution_plan`, no new orders, no `accepted_snapshot_v2_id` set.

## Tests (in-process, independent of live HTTP)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**Result:** `122 passed` in ~5s.

Runtime preview/freeze/accept/convert remain **unvalidated live** despite green pytest.

## Owner unblock procedure

1. Start backend (owner terminal):

   ```powershell
   cd C:\Users\offic\Desktop\workos-active
   .\scripts\dev-backend.ps1
   ```

   Or full stack with stale detection:

   ```powershell
   .\scripts\start-dev.ps1
   ```

2. Verify health:

   ```powershell
   Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
   ```

3. Verify freshness — preview must return `readiness=partial_with_owner_decisions` (not `blocked_snapshot_conflict`).

4. Re-run this live QA task (backup → freeze with `quote_id=1` or workspace UUID → accept → convert).

## Next recommended step

Owner starts backend and confirms health + preview freshness, then re-run Step 8 live QA (same task spec).

## Roadmap

| Item | Status |
|------|--------|
| Step 8 pytest / preview logic | **VALIDATED** (122 pass) |
| Step 8 live freeze → accept → convert | **NOT VALIDATED** (backend down) |
| Overall Step 8 | **PARTIAL_WITH_GUARDS** |
| Step 9 | **BLOCKED** until live Step 8 chain passes |
| 7I / 10 / 11 | Unchanged — registry owner decisions + profitability actuals remain future scope |

**Cat sunt in directia stabilita: 88/100%**

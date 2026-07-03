# Step 8 Live Freeze → Accept → Convert QA — 2026-06-30

## Status

**PASS_WITH_GUARDS** (live freeze **PASS**; accept **BLOCKED** on quote prerequisite `PRICING_REVIEW_REQUIRED`; convert **NOT RUN**)

Backend was already running via `.\scripts\dev-backend.ps1`. Health and paper preview freshness confirmed before writes. Live freeze persisted dual Quote Snapshot V2 on safe IV6 identity. Accept blocked because quote 1 is an unpriced draft (`grand_total=0`, `pricing_review_v1=null`, `owner_approval_v1=null`). Pytest chain **122 passed**.

## Scope

QA only — no code, UI, migration, Alembic, seed, `/price`, CostEngine, QuoteOrchestrator, execution_plan/tasks, Step 9, push. Agent did not start backend/frontend.

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `0c637c2` — `docs(step8): record live qa after backend fresh` |
| Unexpected code changes | None |

## Health + freshness

| Probe | Result |
|-------|--------|
| `GET /health` | **200** `{"status":"healthy"}` |
| Preview paper QA | **200**, `readiness=partial_with_owner_decisions`, not `blocked_snapshot_conflict` |
| `commercial_status` | `blocked` |
| `internal_status` | `partial` |
| Backend fresh | **Yes** — dev registry bridge active |

## Safe identity (read-only verify)

| Type | Value | Valid |
|------|-------|-------|
| Workspace | `96009ff3-a20b-40d7-a8c7-540e48058526` — `IV6-AA7F2532`, `ready_for_quote_preview` | Yes |
| Quote | `id=1` — `Q-V6-IV6-AA7F2532-1782719582`, `draft`, `accepted_snapshot_v2_id=null` | Yes |

Linkage on quote 1 (pre-freeze):

| Field | Value |
|-------|-------|
| `requires_pricing_review` | `true` |
| `pricing_review_v1` | **null** |
| `owner_approval_v1` | **null** |
| `grand_total` | `0.0` |

## Backup

| Item | Value |
|------|-------|
| Path | `backend/dev.backup-before-step8-live-freeze-accept-convert-20260630-132501.db` |
| Size | 9,236,480 bytes |
| Tracked | No (ignored backup) |

**Rollback:**

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
Copy-Item .\dev.backup-before-step8-live-freeze-accept-convert-20260630-132501.db .\dev.db -Force
```

## Baseline DB counts (before freeze)

| Table / metric | Count |
|----------------|-------|
| `intake_v6_workspaces` | 67 |
| `quote_snapshots_v2` | 1 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| `execution_tasks` | table absent |
| quotes with `accepted_snapshot_v2_id` | 0 |

## Freeze result

| Field | Value |
|-------|-------|
| Endpoint | `POST /api/v1/product-system/quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS_v2` |
| Body | `_step8_qa_quote_input()` paper sablon + `quote_id=1` + `workspace_id=96009ff3-…` |
| HTTP | **200** |
| `readiness` | `partial_with_owner_decisions` |
| `persist_status` | **`persisted`** |
| `snapshot_id` | **2** |
| `snapshot_code` | **QSN2-2026-0002** |
| `quote_snapshots_v2` after | **2** (+1) |
| Orders / execution_plan | unchanged (2 / 1) |

## Accept result

| Field | Value |
|-------|-------|
| Endpoint | `POST /api/v1/intake-v6/quotes/1/accept` |
| HTTP | **422** |
| Error | `PRICING_REVIEW_REQUIRED` |
| Message | Pricing review must be completed before accept. |
| Missing prerequisite | `pricing_review_v1` not completed; quote unpriced (`grand_total=0`) |
| `accepted_snapshot_v2_id` after | **null** (unchanged) |
| Orders / execution_plan | unchanged |

Body included `confirm_owner_decisions_acknowledged=true` and all accept confirmations — blocked **before** snapshot accept gate on pricing review.

**Not reached:** `OWNER_APPROVAL_MISSING` (would fail next after pricing review without `POST …/owner-approval`).

## Convert result

**NOT RUN** — accept did not succeed.

Endpoint (for next rerun): `POST /api/v1/intake-v6/quotes/1/convert-to-order`

## DB verification (after chain attempt)

| Table / metric | After freeze | After accept attempt |
|----------------|--------------|----------------------|
| `quote_snapshots_v2` | 2 | 2 |
| `quotes` | 4 | 4 |
| `orders` | 2 | 2 |
| `execution_plan` | 1 | 1 |
| `accepted_snapshot_v2_id` on quote 1 | null | null |

Latest persisted snapshot row:

| Field | Value |
|-------|-------|
| `id` | 2 |
| `snapshot_code` | QSN2-2026-0002 |
| `quote_id` | 1 |
| `workspace_id` | 96009ff3-a20b-40d7-a8c7-540e48058526 |
| `readiness` | partial_with_owner_decisions |
| `status` | draft |

Pre-existing order `88001` still references snapshot `1` from prior fixture — not created by this QA.

## No execution side effects

| Check | Result |
|-------|--------|
| `execution_plan` count | **1 → 1** |
| `execution_tasks` | table absent |
| New orders | **No** |
| Step 9 | **Not started** |

## No `/price`, CostEngine, QuoteOrchestrator

Freeze/accept HTTP paths compose 7G/7H preview services only. Convert not invoked. Pytest suite includes import guards and convert service boundary tests — all green.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**Result:** **122 passed** (~5s)

## Owner verification checklist

| Where | What to check |
|-------|----------------|
| Freeze | `POST …/quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS_v2` → `persist_status=persisted`, `QSN2-2026-0002` |
| Accept | `POST …/intake-v6/quotes/1/accept` → currently **422 PRICING_REVIEW_REQUIRED** |
| Convert | blocked until accept succeeds |
| DB | `quote_snapshots_v2.id=2`, `quotes.accepted_snapshot_v2_id` still null on quote 1 |
| Backup | `backend/dev.backup-before-step8-live-freeze-accept-convert-20260630-132501.db` |
| Worklog | this file |

## Next recommended step

On quote 1, complete IV6 prerequisites via API (not manual DB):

1. `POST /api/v1/intake-v6/quotes/1/complete-pricing-review` — **requires priced quote totals** (`grand_total>0` today blocks with `QUOTE_NOT_PRICED`);
2. `POST /api/v1/intake-v6/quotes/1/owner-approval`;
3. Re-run accept with `confirm_owner_decisions_acknowledged=true` against persisted snapshot `2`;
4. Then convert.

Alternative: use a controlled fixture quote with completed pricing review + owner approval + same workspace, or owner prices quote 1 in QuoteWizard first.

## Roadmap

| Item | Status |
|------|--------|
| Live freeze (Step 8) | **VALIDATED** |
| Live accept + convert (Step 8) | **NOT VALIDATED** — quote prerequisite gap |
| Overall Step 8 | **PARTIAL_WITH_GUARDS** (raised from stale-only; full chain still open) |
| Step 9 | **BLOCKED** until live accept→convert passes |
| 7I / 10 / 11 | Unchanged |

**Cat sunt in directia stabilita: 91/100%**

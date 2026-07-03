# Step 8 Persistent Snapshot Schema APPLY — 2026-06-30

## Status

**PASS_WITH_GUARDS** — schema already at s56-equivalent via `create_all`; Alembic not stamped; upgrade skipped intentionally.

## Scope

OWNER GO: backup `dev.db`, verify Alembic state, apply s53–s56 if needed, schema verification, targeted pytest, health check.

**Not done:** new migration, schema changes, code changes, Alembic upgrade (unsafe without stamp), runtime manual freeze, push.

## Architecture readback summary

- Step 8 freeze persists dual snapshot (7G commercial + 7H internal separate).
- Freeze must not call `/price`, CostEngine, QuoteOrchestrator, or create order/plan/task.
- Step 9/10/7I remain subsequent scope.

**Alignment:** **ALIGNED**

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD before | `a9121be` — docs(step8): plan persistent quote snapshot schema |
| Working tree | Clean except older untracked worklogs |
| Unexpected code/migration changes | **None** |

## Alembic state

| | Value |
|---|--------|
| **current before** | Empty — no `alembic_version` table in `backend/dev.db` |
| **heads** | `s50_execution_plan_prepared_by_clarification_target`, `s56_add_execution_plan_source_metadata` (multi-head repo) |
| **s53–s56 in history** | **Yes** — chain s52→s53→s54→s55→s56 |
| **upgrade run** | **Skipped** — schema already present via `Base.metadata.create_all`; blind upgrade would risk duplicate DDL |
| **current after** | Unchanged (no `alembic_version`) |

## Backup

| | Value |
|---|--------|
| Dev DB | `C:\Users\offic\Desktop\workos-active\backend\dev.db` |
| Backup path | `C:\Users\offic\Desktop\workos-active\backend\dev.backup-before-step8-apply-20260630-115311.db` |
| Backup exists | **Yes** (9,236,480 bytes) |
| Git tracking | **No** — `dev.db` and `dev.backup*` in `.gitignore` |

## Schema verification (read-only)

| Check | Result |
|-------|--------|
| `quote_snapshots_v2` table | **YES** — full column set |
| `quotes.accepted_snapshot_v2_id` | **YES** |
| `orders.quote_snapshot_v2_id` | **YES** |
| `orders.snapshot_v2_json` | **YES** |
| `execution_plan.source_quote_snapshot_v2_id` | **YES** (+ related source metadata columns) |

Equivalent to migrations **s53–s56** already applied by ORM bootstrap.

## Tests

**Primary command:**

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:APP_ENV='development'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe -m pytest tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_schema.py tests/test_order_snapshot_v2_convert.py tests/test_orders_update_immutability.py -q
```

**Result:** **110 passed** in ~4.9s

Covers: dry-run, freeze persist, accept gate, order schema/convert, immutability (individual + batch).

**Optional 7G/7H:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py -q
```

**Result:** **36 passed**


## Runtime verification

| Check | Result |
|-------|--------|
| `GET http://127.0.0.1:8000/health` | **200** |
| Manual freeze API | **Not run** — no ad-hoc payload; pytest freeze persist tests are authoritative |

## Files changed (this task)

- `docs/worklog/realignment/2026-06-30_step8_persistent_snapshot_schema_apply.md` only (committed)

## No-side-effects confirmation

- No new migration, no code, no frontend/UI
- No `/price`, CostEngine, QuoteOrchestrator, Pricing Registry
- No order/execution_plan/task creation
- No seed, no push, no work in `C:\Users\offic\workos`
- `dev.db` / backup not committed

## Rollback plan (not executed)

1. Restore: `Copy-Item .\dev.backup-before-step8-apply-20260630-115311.db .\dev.db -Force`
2. If Alembic ever stamped: `alembic downgrade s52_add_intake_v3_workspaces` (only on stamped DBs)

## Owner verification

**No browser UI.**

| Surface | How |
|---------|-----|
| Worklog | This file |
| Schema | `PRAGMA table_info` on `quote_snapshots_v2`, `quotes`, `orders`, `execution_plan` |
| Tests | Command above → 110 passed |
| Alembic | `alembic current` → empty until owner GO for **stamp** (separate task) |

## Guard note

`alembic_version` missing is expected for local `create_all` dev bootstrap. **Do not** run `alembic upgrade` on this DB without owner GO for **stamp-to-head** strategy — risk of duplicate migrations.

## What remains

- Optional: Alembic stamp s56 after owner GO (separate task)
- Step 8 freeze endpoint runtime QA on dev stack with known workspace payload
- Docs sync: Step 8 persist status in roadmap
- Step 8 accept gate QA on live stack

## Next recommended step

**Step 8 freeze endpoint runtime QA** on dev stack with workspace payload from tests (no new quote/order).

## Roadmap awareness

| Item | Status |
|------|--------|
| Position | Step 8 persistence schema **present** on dev DB |
| Step 9 | Not in this task |
| Step 10 | PARTIAL / deferred |
| 7I | NOT STARTED |
| **Cât sunt în direcția stabilită** | **76/100%** |

## Commit

Message: `docs(step8): record persistent snapshot schema apply`

HEAD before: `a9121be`

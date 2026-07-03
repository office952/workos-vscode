# Step 8 Live QA Rerun After Backend Restart — 2026-06-30

## Status

**BLOCKED_BACKEND_STALE** (backend unreachable on `:8000`)

Owner claimed manual backend restart before this rerun. Agent health check: **connection refused** on `http://127.0.0.1:8000/health`. Live preview/freeze/accept/convert **not run**. No backup. DB unchanged.

## Scope

QA only — no code, no app/backend/frontend start, no DB manual writes, no Step 9.

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `70d004d` |
| Unexpected code changes | None |

## Backend fresh check

| Probe | Result |
|-------|--------|
| `GET /health` | **FAILED** — unable to connect to remote server |
| Preview paper QA | **NOT RUN** (no listener on `:8000`) |
| Fresh vs stale | **Cannot verify** — process not reachable |

### Interpretation

Previous run: backend answered health but served stale readiness (`blocked_snapshot_conflict`). This run: **no process on `:8000`**. Owner must ensure backend is **running** with code at `c8d86d1`/`70d004d` before rerun.

Recommended owner command (from repo root):

```powershell
cd C:\Users\offic\Desktop\workos-active
npm run dev:backend
```

Then verify:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
# Preview must show readiness=partial_with_owner_decisions (not blocked_snapshot_conflict)
```

## Safe identity (identified, not used)

| Type | Candidate | Notes |
|------|-----------|-------|
| `workspace_id` | `96009ff3-a20b-40d7-a8c7-540e48058526` (`IV6-AA7F2532`, `ready_for_quote_preview`) | Matches quote 1 workspace code pattern |
| `quote_id` | `1` — `Q-V6-IV6-AA7F2532-1782719582` | `draft`, `accepted_snapshot_v2_id=null` |
| Payload | `_step8_qa_quote_input()` paper sablon | From `test_quote_snapshot_v2.py` |

Accept likely still requires `pricing_review` + `owner_approval` on quote linkage (not verified live).

## Backup

**Not created** — stopped before writes.

Rollback N/A.

## Baseline DB counts

| Table | Count |
|-------|-------|
| `intake_v6_workspaces` | 67 |
| `quote_snapshots_v2` | 1 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| `accepted_snapshot_v2_id` set | 0 |

## Freeze / Accept / Convert

| Stage | Result |
|-------|--------|
| Freeze | **NOT RUN** |
| Accept | **NOT RUN** |
| Convert | **NOT RUN** |

## Tests

**122 passed** (same suite as prior Step 8 QA tasks).

## Files changed

Worklog only.

## No-side-effects confirmation

No code, UI, migration, seed, DB writes, API writes, order/plan/task, backend start, push, `C:\Users\offic\workos`.

## Next recommended step

Owner starts backend and confirms preview `partial_with_owner_decisions`, then **re-run this live QA task** with backup → freeze (`workspace_id` or `quote_id`) → accept → convert.

## Roadmap awareness

Step 8 live chain still unvalidated on HTTP. Step 8 **PARTIAL_WITH_GUARDS**. Step 9 **BLOCKED**.

**Cât sunt în direcția stabilită: 87/100%**

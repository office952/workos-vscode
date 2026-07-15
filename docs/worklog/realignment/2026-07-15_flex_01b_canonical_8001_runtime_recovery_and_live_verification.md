# FLEX-01B — Canonical :8001 runtime recovery and live verification

**Task:** `FLEX-01B-CANONICAL-8001-RUNTIME-RECOVERY-AND-LIVE-VERIFICATION`  
**Date:** 2026-07-15  
**Starting HEAD:** `2ee15af`  
**Verdict:** `FLEX_01B_CANONICAL_8001_RUNTIME_RECOVERY_COMPLETE`  
**Review:** `APPROVE`

---

## 1. Status

Canonical backend on `127.0.0.1:8001` recovered. OpenAPI and live GET verified. Stability recheck PASS. No code changes.

## 2. Starting HEAD

`2ee15af` — FLEX-01A operation completion semantics commit.

## 3. Initial listener state

| Port | LISTENING count | Notes |
|------|-----------------|-------|
| 8001 | 7 | Ghost parent PIDs: 14768, 16184, 26172, 29012, 4984, 34560, 36680 |
| 3000 | 1 | Vite PID 27096 from `C:\w\psiso\frontend` |

## 4. PID evidence

**Ghost parents (unresolvable):** All 7 PIDs — `Get-Process` NOT FOUND, `Win32_Process` empty.

**Living orphan workers (spawn children):**

| Worker PID | Parent ghost PID |
|------------|------------------|
| 30884 | 14768 |
| 35012 | 16184 |
| 37708 | 26172 |
| 3756 | 29012 |
| 29952 | 4984 |
| 33428 | 34560 |
| 36044 | 36680 |

**Temp backends (FLEX-01A verification):** 15268, 23416 (:18012), 32008, 28392 (:8012)

**Initial runtime symptom:** `/health` 200, OpenAPI route **MISSING** on :8001.

## 5. Root cause

Orphaned uvicorn `--reload` worker processes from prior stack starts. Parent reloader processes exited; TCP table retained ghost parent PIDs; stale workers served pre-FLEX-01A code. `start-dev.ps1` reused stale backend because `Test-BackendDevReady` passes on `/health` alone without OpenAPI route freshness check.

## 6. Processes stopped

- Orphan workers: 29952, 36044, 37708, 33428, 35012, 3756, 30884
- Temp backends: 32008, 28392, 15268, 23416
- Frontend (restart): 27096

## 7. Processes preserved

No unknown or foreign processes killed. Node helper PIDs unrelated to stack left intact.

## 8. Restart command

```powershell
npm run dev:stack
```

## 9. New PID state

| Service | PID | Command |
|---------|-----|---------|
| Backend (listener) | 9476 | `python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload` |
| Backend (worker) | 34936 | `spawn_main(parent_pid=9476)` |
| Frontend | 9328 | `vite --host 127.0.0.1 --port 3000` |
| Stack launcher | 35600 | `npm run dev:stack` |

**Listener count after recovery:** 1 on :8001, 1 on :3000.

## 10. Working directory proof

- Stack root: `C:\w\psiso` (from `dev.ps1` output and frontend cmdline)
- Backend uses `C:\w\psiso\backend\.venv` via start-dev job
- Branch: `feature/product-system-active-path-isolation-v1`

## 11. Health verification

```
GET http://127.0.0.1:8001/health → 200 {"status":"healthy"}
```

Stability recheck: PASS (same PID 9476).

## 12. OpenAPI verification

```
GET http://127.0.0.1:8001/openapi.json
Path present: /api/v1/operator/orders/{order_id}/task-collaboration-read
```

Stability recheck: PASS.

## 13. Live GET verification

```
GET http://127.0.0.1:8001/api/v1/operator/orders/23099/task-collaboration-read
```

| Field | Value |
|-------|-------|
| HTTP status | 200 |
| order_id | 23099 |
| contract_version | execution_task_collaboration_read/v1 |
| task_count | 13 |
| sample_task_id | node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep |
| optional_principal | employee_id=4 (Putaru Sandu), source=execution_plan |
| actual_workers | [] |
| all_sessions_closed | false |
| operation_completed | false |
| operation_completion_source | active_sessions_remain |
| legacy_or_derived_task_status | in_progress |

## 14. Stability verification

After 15s wait:

- Listener count :8001 = 1
- Backend PID 9476 alive
- Health, OpenAPI route, GET 200 — all PASS

## 15. Tests

```
pytest tests/test_execution_task_collaboration_read.py -q → 19 passed
pytest tests/test_task_work_sessions.py tests/test_execution_task_assignment.py tests/test_employee_mobile_tasks.py::test_claim_success_assigns_and_lists_in_my_tasks -q → 13 passed
```

## 16. DB writes

`backend/dev.db` mtime unchanged before/after live GET → **0 operational writes**.

## 17. Independent review

Separate reviewer verdict: **APPROVE** — listener identification correct, no foreign kills, canonical worktree confirmed, OpenAPI + live GET on 8001, zero DB writes, no code/tooling changes, FLEX-02 not started.

## 18. Compound knowledge

`.compound-engineering/flex-01b-canonical-8001-runtime-recovery/compound-knowledge.md`

## 19. Files changed

- `.compound-engineering/flex-01b-canonical-8001-runtime-recovery/compound-knowledge.md` (new)
- `docs/worklog/realignment/2026-07-15_flex_01b_canonical_8001_runtime_recovery_and_live_verification.md` (new)

No application code changes.

## 20. Commit

Docs-only commit on branch tip: `docs(runtime): verify canonical collaboration read endpoint`

## 21. Blocked scope confirmation

- No FLEX-02
- No DB / UI / Product System / snapshot changes
- No startup script modifications (tooling defect documented for owner GO)

## 22. Next safe step

**OWNER REVIEW FLEX-01B** — do not authorize FLEX-02.

## 23. Direction score

**9/10** — Canonical runtime recovered; FLEX-01A live gate unblocked on :8001. Remaining gap: `start-dev.ps1` health-only reuse (owner tooling decision).

---

## Delivery footer

| Field | Value |
|-------|-------|
| Initial 8001 listeners | 7 (ghost parents) |
| Root cause | Orphan uvicorn reload workers + start-dev health-only reuse |
| Canonical backend PID | 9476 |
| Canonical frontend PID | 9328 |
| Backend worktree | C:\w\psiso |
| Backend health | PASS |
| OpenAPI route on 8001 | YES |
| Live GET on 8001 | PASS |
| Stability recheck | PASS |
| Operational DB writes | 0 |
| Code changed | NO |
| Runtime tooling changed | NO |
| FLEX-02 started | NO |
| Verdict | FLEX_01B_CANONICAL_8001_RUNTIME_RECOVERY_COMPLETE |

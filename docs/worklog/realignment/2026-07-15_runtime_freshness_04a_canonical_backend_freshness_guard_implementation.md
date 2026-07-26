# RUNTIME-FRESHNESS-04A — Canonical backend freshness guard implementation

## 1. Status

**COMPLETE** — `RUNTIME_FRESHNESS_04A_CANONICAL_BACKEND_FRESHNESS_GUARD_COMPLETE`

## 2. Starting HEAD

`3535378`

## 3. Owner decisions R1–R7

| ID | Decision |
|----|----------|
| R1 | FIX TOOLING NOW |
| R2 | OPTION E — HYBRID (health + OpenAPI routes + process tree) |
| R3 | SAME-WORKTREE STALE: auto-stop only after full proof |
| R4 | OTHER WORKTREE = BLOCK, no auto-stop |
| R5 | FOREIGN ON 8001 = BLOCK, no kill |
| R6 | ACCEPT 5-ROUTE MANIFEST V1 |
| R7 | TOOLING ONLY, no backend application code |

## 4. Plan readback

Implemented `.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/plan.md`: durable dev-stack guard so `health=200` + stale OpenAPI/runtime is not accepted as backend ready.

## 5. Existing tooling reused

- `scripts/_workos-dev-contract.ps1` — port contract, listener helpers, stale listener tests
- `scripts/start-dev.ps1` — job-based backend start, `Wait-ForService`, frontend resolution
- `scripts/dev.ps1` / `npm run dev:stack` — canonical entry
- `scripts/canonical_startup_contract.test.mjs` — port/proxy contract tests extended

## 6. Files inspected

- `scripts/start-dev.ps1`, `scripts/_workos-dev-contract.ps1`, `scripts/dev.ps1`
- `.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/plan.md`
- `.compound-engineering/flex-01b-canonical-8001-runtime-recovery/compound-knowledge.md`
- `backend/dependencies/auth.py` (dev bypass token for live GET only)

## 7. Files changed

| File | Change |
|------|--------|
| `scripts/_workos-dev-backend-freshness.ps1` | New freshness helper |
| `scripts/workos-canonical-openapi-paths.json` | Manifest v1 |
| `scripts/_workos-dev-contract.ps1` | Venv-path listener canonical check |
| `scripts/start-dev.ps1` | Freshness integration |
| `scripts/canonical_startup_contract.test.mjs` | Scenarios A–L |
| `.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/compound-knowledge.md` | Compound knowledge |

## 8. Manifest contract

- Path: `scripts/workos-canonical-openapi-paths.json`
- Version: `1`
- Five template paths (no entity IDs, no Intake V3, no QA-only paths)
- Empty/malformed/duplicate → fail closed in `Get-WorkOsCanonicalOpenApiManifest`

## 9. Freshness classification

Structured evaluation via `Get-WorkOsBackendFreshnessClassification`: `current_and_ready`, `backend_absent`, `canonical_routes_missing`, `health_failed`, `openapi_failed`, `same_worktree_stale` (via routes), `foreign_process`, `other_worktree`, `ambiguous_process_tree`, `multiple_listeners`.

## 10. Process ownership rules

- Same-worktree: `.venv` under project root, `main:app` uvicorn, spawn lineage
- Other-worktree: different root via venv path → block
- Foreign: non-WorkOS uvicorn or non-uvicorn → block
- Ambiguous non-uvicorn → block; all-uvicorn ambiguous may proceed to route check (documented limitation)

## 11. Listener enumeration

`Get-WorkOsBackendPortListeners` collects all listen rows, dedupes by PID, never first-row-only.

## 12. Controlled stop behavior

`Stop-WorkOsBackendProcessTreeControlled` — only for `controlled_stop` recommendation; same-worktree stale or missing routes with resolvable uvicorn tree; confirms port release with bounded retries.

## 13. Retry/timeout behavior

OpenAPI: 3×500 ms; port release: 20×250 ms; startup health via existing `Wait-ForService`.

## 14. Contract tests

```
npm run test:startup-contract → 26/26 PASS
```

Scenarios A–L covered (absent, reuse, stale routes, foreign block, ghost worker, other worktree, OpenAPI retry, multi-listener, empty/malformed manifest, missing route diagnostics, legacy port contract).

## 15. Runtime verification

1. Stopped prior stack (PIDs 9328, 9476, 34936)
2. Ports confirmed free
3. `npm run dev:stack` → backend PID 29072, frontend 9404
4. Health 200; OpenAPI all 5 routes OK
5. Live GET order 23099 → 200, contract v1, 13 tasks
6. 15s stability recheck → 1 listener, health 200
7. Second `start-dev.ps1` → reuse message, listener count unchanged

## 16. Second-start reuse verification

```
Backend already running on port 8001 (freshness=current_and_ready, PID=29072)
All services already running - no duplicate processes started.
listeners_before=1 listeners_after=1
```

## 17. DB verification

`backend/dev.db` mtime unchanged across live GET (`2026-07-15T13:09:21.0991559Z`). Operational writes: **0**.

## 18. Regression tests

| Command | Result |
|---------|--------|
| `pytest tests/test_execution_task_collaboration_read.py -q` | 19 passed |
| `pytest tests/test_task_work_sessions.py … -q` | 13 passed |

## 19. Independent review

- Reviewer independent: **YES** (Bugbot subagent on uncommitted 04A diff)
- Verdict: **APPROVE_WITH_EXPLICIT_LIMITATION**
- Finding: system-python uvicorn with all-ambiguous ownership can reuse when health+routes pass (lines 597–602) — documented as known limitation; foreign/other-worktree still blocked
- Blockers closed: no foreign/other-worktree kill paths; no health-only path in backend resolution

## 20. Compound knowledge

`.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/compound-knowledge.md`

## 21. Behavior-change check

**YES** — dev startup no longer accepts health-only backend reuse; stale/missing OpenAPI routes trigger controlled stop or block.

## 22. Blocked scope

Backend app, frontend, DB schema, FLEX-02, fingerprint endpoint — not touched.

## 23. Dead pieces

None discovered. Temporary `scripts/_eval-freshness.ps1` removed before commit.

## 24. Commit

Pending `/ce-commit` with message `fix(runtime): reject stale canonical backend reuse`.

## 25. What remains

Owner review RUNTIME-FRESHNESS-04A; optional hardening of system-python worktree proof if owners require stricter same-worktree evidence.

## 26. Next safe step

**OWNER REVIEW RUNTIME-FRESHNESS-04A** — do not authorize FLEX-02 automatically.

## 27. Direction score

**88/100** — Tooling guard closes FLEX-01B recurrence class on canonical stack; explicit limitation on global-Python uvicorn reuse is honest and bounded by OpenAPI manifest.

# RUNTIME-FRESHNESS-04 — Canonical backend route guard (plan)

**Task:** `RUNTIME-FRESHNESS-04-CANONICAL-BACKEND-ROUTE-GUARD`  
**Date:** 2026-07-15  
**Starting HEAD:** `509ae65`  
**Mode:** Cursor Plan Mode + `/ce-plan`  
**Verdict:** `RUNTIME_FRESHNESS_04_PLAN_READY`  
**Implementation:** NO (plan only)

---

## 1. Status

Technical plan complete. Tooling-only freshness guard designed. Awaiting owner GO before implementation.

## 2. Motivation

FLEX-01B recovered canonical `:8001` after stale uvicorn orphan workers passed health-only reuse. Tooling defect documented; not fixed in FLEX-01B per scope boundary.

## 3. Root cause readback

- `Test-BackendDevReady` = `/health` AND `Test-IntakeV3OperatorWorkspaceRoutesOk`
- `$required = @()` → OpenAPI gate is no-op
- `Resolve-PortService` reuses when probe passes; stale cleanup only when probe fails
- Ghost uvicorn parents + living spawn workers served pre-FLEX-01A code

## 4. Research performed (read-only)

| Workstream | Scope |
|------------|-------|
| A — Startup tooling | `start-dev.ps1`, `_workos-dev-contract.ps1`, `dev.ps1`, `dev-backend.ps1`, `canonical_startup_contract.test.mjs` |
| B — Strategy options | A–E evaluated; hybrid recommended |
| C — Route candidates | operator, execution, intake-v6 surfaces audited in routers |

## 5. Recommended strategy

**Option E — Hybrid:** health + required OpenAPI routes + process-tree classification.

No backend fingerprint endpoint in minimal variant.

## 6. Required route set (proposed manifest v1)

1. `/api/v1/operator/orders/{order_id}/task-collaboration-read`
2. `/api/v1/operator/orders/{order_id}/task-truth`
3. `/api/v1/operator/tasks`
4. `/api/v1/execution/plan/{order_id}`
5. `/api/v1/intake-v6/workspaces`

## 7. Process safety highlights

- Enumerate all listeners (fix first-only `Get-PortListener`)
- Resolve ghost parent → `spawn_main` children before stop
- Foreign process: BLOCKER, no kill
- Wrong worktree: BLOCKER (default)
- Same-worktree stale: controlled stop of resolved tree

## 8. Files proposed for implementation (post-GO)

- `scripts/_workos-dev-backend-freshness.ps1` (new)
- `scripts/_workos-dev-contract.ps1`
- `scripts/start-dev.ps1`
- `scripts/workos-canonical-openapi-paths.json` (new)
- `scripts/canonical_startup_contract.test.mjs`

## 9. Owner decisions

R1–R7 documented in plan. Awaiting owner review.

## 10. Blocked scope

Implementation, backend code, DB, UI, FLEX-02, auto-push, PR.

## 11. Artifacts

| Artifact | Path |
|----------|------|
| Plan | `.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/plan.md` |
| Worklog | `docs/worklog/realignment/2026-07-15_runtime_freshness_04_canonical_backend_route_guard_plan.md` |

## 12. Next safe step

**OWNER REVIEW RUNTIME-FRESHNESS-04** — do not start implementation without GO.

## 13. Direction score

**9/10** — Directly addresses FLEX-01B tooling gap with minimal, evidence-backed design. Blocked only on owner decision.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Cursor mode | PLAN MODE |
| Compound command | `/ce-plan` |
| Implementation | NO |
| Code changes | NO |
| Recommended strategy | E — Hybrid |
| Required routes | 5 (see §6) |
| Owner decisions | 7 (R1–R7) |
| Verdict | RUNTIME_FRESHNESS_04_PLAN_READY |

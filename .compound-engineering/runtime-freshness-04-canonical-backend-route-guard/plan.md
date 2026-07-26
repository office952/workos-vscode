# RUNTIME-FRESHNESS-04 — Canonical Backend Freshness Guard (Implementation Plan)

**Task:** `RUNTIME-FRESHNESS-04-CANONICAL-BACKEND-ROUTE-GUARD`  
**Date:** 2026-07-15  
**Starting HEAD:** `509ae65`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Artifact readiness:** Plan only — **no implementation in this task**  
**Verdict target:** `RUNTIME_FRESHNESS_04_PLAN_READY` (pending owner GO for tooling)

---

## Summary

FLEX-01B proved that canonical `:8001` can answer `/health` with HTTP 200 while serving **stale code** (OpenAPI missing FLEX-01A routes). Root cause is tooling: `scripts/start-dev.ps1` reuses any backend that passes `Test-BackendDevReady`, which is effectively **health-only** because `$required = @()` in `Test-IntakeV3OperatorWorkspaceRoutesOk`.

This plan designs a **tooling-only freshness guard** so `health 200 + stale OpenAPI` is never accepted as runtime ready. Recommended strategy: **Option E (Hybrid)** — health + required OpenAPI routes + improved process classification — without new backend endpoints, DB changes, or kill-all behavior.

---

## Problem Frame

| Symptom | Evidence (FLEX-01B) |
|---------|---------------------|
| Stale backend reused | `Resolve-PortService` returned `Ready=$true` when `/health` OK |
| OpenAPI stale | `task-collaboration-read` absent from `:8001/openapi.json` |
| Ghost listeners | 7 `LISTENING` rows; parent PIDs unresolvable; spawn workers alive |
| Manual recovery worked | Kill orphan workers → `npm run dev:stack` → route present |

**Invariant to enforce:** Canonical dev backend is ready only when it is **healthy**, serves **current-worktree code** (proxied by OpenAPI route presence), and is owned by a **classifiable WorkOS process tree**.

---

## Root Cause Readback (Workstream A)

### 1. Where is health-only acceptance?

```176:182:scripts/start-dev.ps1
function Test-BackendDevReady {
    $healthUrl = "$(Get-WorkOsBackendUrl)/health"
    if (-not (Test-HttpOk -Url $healthUrl)) {
        return $false
    }
    return (Test-IntakeV3OperatorWorkspaceRoutesOk)
}
```

```127:141:scripts/start-dev.ps1
function Test-IntakeV3OperatorWorkspaceRoutesOk {
    ...
    $required = @()
    ...
    return $true   # always, if OpenAPI parses
}
```

**Causal chain:** `$required` empty → OpenAPI parse success → `Test-BackendDevReady` true whenever `/health` OK.

### 2. What conditions permit stale reuse?

```200:208:scripts/start-dev.ps1
    $ready = & $HealthProbe
    if ($ready) {
        Write-Host "$ServiceName already running on port $Port ..."
        return @{ Occupied = $true; Ready = $true; ... }
    }
```

Stale cleanup (`Test-WorkOsBackendListenerStale` + `Stop-Process`) runs **only when health probe fails** (lines 211–245). A stale-but-healthy backend never enters that branch.

### 3. Existing OpenAPI route verification helper?

**Yes, but neutered:** `Test-IntakeV3OperatorWorkspaceRoutesOk` fetches `/openapi.json` and checks `$required` paths. Same pattern in `Write-BackendDevReadyDiagnostics`. Infrastructure exists; list is empty.

Historical context: three Intake V3 paths were removed per `dev-readiness-active-route-analysis.md` because V3 HTTP router is deprecated. Replacement list was never populated.

### 4. Existing canonical route list?

| Location | Status |
|----------|--------|
| `scripts/start-dev.ps1` `$required` | **Empty** |
| `backend/tests/test_intake_v3_operator_workspace_runtime_routes.py` | V3 routes only (deprecated HTTP) |
| `scripts/canonical_startup_contract.test.mjs` | Port/proxy contract only |
| `.compound-engineering/flex-01b-*/compound-knowledge.md` | Operational manual check |

No versioned canonical route manifest for **active** surfaces.

### 5. Existing worktree / process command-line verification?

**Partial, flawed for uvicorn --reload:**

```65:78:scripts/_workos-dev-contract.ps1
function Test-WorkOsBackendListenerCanonical {
    ...
    if ($cmdLower -notmatch [regex]::Escape($rootNorm)) { return $false }
}
```

Uvicorn cmdline is `python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload` — **no project root in command line**. Canonical check fails for legitimate backends unless path appears elsewhere (it does not). Worktree proof must use:

- `ExecutablePath` → `.venv\Scripts\python.exe` under expected `backend/`
- Spawn worker cmdline `parent_pid=<reloader>`
- Optional: compare `backend/main.py` mtime vs process start time (weak signal)

### 6. How is backend stopped today?

| Mechanism | Behavior |
|-----------|----------|
| Ctrl+C during frontend log stream | `Stop-Job` backend + frontend jobs |
| `Resolve-PortService` stale path | `Stop-Process -Id $listener.PID` (often ghost parent — ineffective) |
| Manual | User kills PIDs on 8001/3000 |
| `dev-backend.ps1` | Foreground uvicorn; Ctrl+C only |

No PID files, no graceful shutdown helper, no orphan-worker sweep.

### 7. Why did workers survive reloader death?

Uvicorn `--reload` spawns `multiprocessing.spawn` children. Parent reloader exited; TCP table retained ghost parent `OwningProcess`; living workers continued serving HTTP. `Stop-Process` on ghost PID is a no-op.

### 8. Minimal change to prevent recurrence?

Populate `$required` with a **small active-route set** and restructure `Resolve-PortService` so **freshness failure triggers controlled stale cleanup** even when `/health` passes. Add **orphan worker resolution** before stop decisions.

---

## Options Evaluation (Workstream B)

| Criterion | A: OpenAPI routes | B: Fingerprint endpoint | C: PID/worktree | D: Always restart | E: Hybrid |
|-----------|-------------------|-------------------------|-----------------|-------------------|-----------|
| Safety vs stale code | **High** | **High** | Medium | **High** | **High** |
| Complexity | Low | Medium–High | Medium | Low | Medium |
| Speed | Fast (~1 HTTP) | +1 HTTP | CIM queries | Slow (always boot) | Fast |
| False positive (reject good) | Low if routes stable | Low | **High** (cmdline gaps) | None | Low |
| False negative (accept stale) | Low | Low if HEAD tracked | **High** | None | Low |
| Windows / uvicorn reload | Good | Good | **Poor** (ghost PID) | Good | **Good** (with spawn resolution) |
| Other worktrees | Neutral | Neutral if fingerprint scoped | Risky | Neutral | Neutral with policy |
| Developer UX | Good (reuse when fresh) | Good | Fragile | Poor | Good |
| Backend code change | **No** | **Yes** (new/extended endpoint) | No | No | **No** |
| Tooling change | **Yes** | Yes + backend | Yes | Yes | **Yes** |
| Compatibility | Aligns with 2026-06 BUILD fix intent | New contract | Fixes incomplete | Breaks idempotent goal | Best fit |

**Option B note:** `/api/v1/system/version` exists but does not expose git HEAD. Fingerprint endpoint is **owner decision R7+separate** — not in minimal variant.

**Option D note:** Rejected as default — contradicts idempotent `dev:stack` design and slows every start by ~4s+.

**Recommendation:** **Option E** — health + required OpenAPI routes + process-tree classification. Validated without new backend endpoint, DB, or kill-all.

---

## Recommended Strategy

### Freshness predicate (all must pass for reuse)

```
BackendFresh =
  Test-HttpOk(/health)
  AND Test-CanonicalOpenApiRoutes(required_paths)
  AND Test-WorkOsBackendProcessTreeAcceptable(ProjectRoot, Port)
```

### On failure taxonomy

| Class | Detection | Action |
|-------|-----------|--------|
| **Fresh canonical** | All predicates pass; single listener | Reuse (current behavior, but correct) |
| **Stale WorkOS** | Health OK, routes missing OR wrong-era OpenAPI | Stop **resolved** process tree (reloader + spawn children), restart |
| **Orphan worker** | Ghost parent PID + living `spawn_main(parent_pid=*)` | Stop children only (proven pattern from FLEX-01B) |
| **Foreign process** | Port occupied, not uvicorn/WorkOS | **BLOCKER** — print PID/cmdline, exit 1, **no kill** |
| **Wrong worktree** | Uvicorn from different checkout's `.venv` | **Owner policy R4** — default BLOCKER or stop-with-warning |
| **Ambiguous / multi-listener** | >1 LISTENING without resolution | **STOP** + diagnostic; no kill-all |

### Rename for clarity (implementation phase)

- `Test-IntakeV3OperatorWorkspaceRoutesOk` → `Test-CanonicalBackendOpenApiRoutesOk` (or keep name, change behavior + comment)
- Centralize `$script:WorkOsCanonicalBackendRequiredOpenApiPaths` in `_workos-dev-contract.ps1` or new `_workos-dev-backend-freshness.ps1`

---

## Required Route Set (Proposed)

Versioned manifest: `scripts/workos-canonical-openapi-paths.json` (or inline in contract script with header comment `manifest_version: 1`).

| # | OpenAPI path | Why stable | Component proved | Legitimate removal? | Guard fit |
|---|--------------|------------|------------------|---------------------|-----------|
| 1 | `/api/v1/operator/orders/{order_id}/task-collaboration-read` | FLEX-01A shipped HEAD `2ee15af`; regression-tested | Execution collaboration read | Only if FLEX retracted | **Primary stale detector** (FLEX-01B) |
| 2 | `/api/v1/operator/orders/{order_id}/task-truth` | W6-T01 canonical operator truth | Operator execution truth | Unlikely — core operator | Operator surface alive |
| 3 | `/api/v1/operator/tasks` | Long-lived shop-floor listing | Operator task index | Unlikely | Core operator router mounted |
| 4 | `/api/v1/execution/plan/{order_id}` | Execution layer v1 contract | Execution plan read | Unlikely — handoff spine | Execution spine alive |
| 5 | `/api/v1/intake-v6/workspaces` | Active intake (V3 HTTP deprecated) | Intake V6 workspace list | Only if V6 retired | Intake canonical surface |

**Explicitly excluded from guard:**

- Intake V3 workspace paths (deprecated `_deprecated_router`, per `dev-readiness-active-route-analysis.md`)
- `/api/v1/operational-registry/employees` — stable but not necessary for stale-code detection; add in manifest v2 if owner wants registry proof
- Experimental / feature-flagged routes
- Frontend routes (separate frontend freshness out of scope)

**Manifest maintenance rule:** Adding a route requires owner-visible manifest version bump + worklog entry. Removing a route requires proof it is deprecated in code, not merely failing on old builds.

---

## Process Safety Design

### Listener discovery

```powershell
# Enumerate ALL listeners (not first-only)
Get-NetTCPConnection -LocalPort $Port -State Listen
# Cross-check: netstat -ano | findstr ":$Port" | findstr LISTENING
```

**Fix `Get-PortListener`:** Today returns `$conns[0]` only — misses multi-listener state (FLEX-01B had 7).

### Resolve real serving PID

```
1. If OwningProcess resolvable AND cmdline matches uvicorn --port N → candidate reloader
2. If OwningProcess ghost (Get-Process/CIM empty) → search Win32_Process for spawn_main(parent_pid=ghost)
3. If spawn children found → stale tree candidates
4. If none resolvable but HTTP responds → classify AMBIGUOUS, fail closed
```

### Worktree proof (without backend code)

Accept backend when **any** of:

- Reloader job uses `backend\.venv\Scripts\python.exe` from `$ProjectRoot\backend`
- `Start-Job` backend (fresh start path) — trust by construction
- For reuse path: `.venv` path normalized contains `$ProjectRoot` (case-insensitive)

Reject reuse (not auto-kill foreign) when:

- Uvicorn from another path (e.g. `C:\other\worktree\backend\.venv`)
- System python on unexpected port without WorkOS markers

### Stop policy

| Target | Stop allowed? |
|--------|---------------|
| Confirmed orphan `spawn_main` worker | **Yes** |
| Confirmed stale WorkOS reloader + children | **Yes** (children first, then reloader) |
| Foreign process | **No** — BLOCKER |
| Unknown | **No** — BLOCKER + owner review |
| Same-worktree stale (routes missing) | **Yes** after owner R3 (default: yes) |

### IPv4 / IPv6

Canonical contract binds `127.0.0.1` only (`_workos-dev-contract.ps1`). Probe `LocalAddress -eq 127.0.0.1`. Flag `0.0.0.0` / `::` listeners as diagnostic warning.

### Ghost parent PID

Do not `Stop-Process` ghost PID alone. Always resolve children first (FLEX-01B proven pattern).

---

## Implementation Boundary

### Files likely permitted (owner GO required)

| File | Change |
|------|--------|
| `scripts/start-dev.ps1` | Wire freshness into `Resolve-PortService`, `Wait-ForService`, diagnostics |
| `scripts/_workos-dev-contract.ps1` | Route manifest, fix canonical cmdline check, spawn resolver |
| `scripts/_workos-dev-backend-freshness.ps1` | **New** — probes, classification, diagnostics (keeps start-dev.ps1 readable) |
| `scripts/canonical_startup_contract.test.mjs` | Assert non-empty required routes, manifest version |
| `docs/worklog/realignment/...` | Implementation evidence |

### Files forbidden (this plan)

- `backend/**` application code (routers, services, schemas)
- `frontend/**`
- DB, migrations, seeds
- Product System, snapshots, FLEX read model
- `package.json` / npm scripts (unless owner expands scope)

### Backend fingerprint endpoint

If owner later wants **Option B** supplement:

- Extend `GET /api/v1/system/version` with optional `git_head` / `started_at` in dev only
- **Separate owner decision** — not in minimal tooling-only implementation

---

## Proposed Implementation Units (Post-GO)

### U1. Canonical OpenAPI path manifest

- **Goal:** Single versioned source of truth for required routes
- **Files:** `scripts/workos-canonical-openapi-paths.json`, load helper in `_workos-dev-contract.ps1`
- **Tests:** `canonical_startup_contract.test.mjs` — manifest non-empty, paths are absolute OpenAPI templates

### U2. OpenAPI freshness probe

- **Goal:** Replace empty `$required` check with manifest-driven validation
- **Files:** `scripts/_workos-dev-backend-freshness.ps1`, `scripts/start-dev.ps1`
- **Approach:** Fetch `/openapi.json` with 5s timeout, 2 retries, 500ms backoff; fail closed on parse error
- **Tests:** Node contract test parses PS1 and asserts probe calls manifest

### U3. Process tree resolver

- **Goal:** Ghost parent → spawn child mapping; multi-listener enumeration
- **Files:** `scripts/_workos-dev-backend-freshness.ps1`, `scripts/_workos-dev-contract.ps1`
- **Approach:** `Get-WorkOsBackendListenerSnapshot` returns structured evidence object
- **Tests:** Documented manual scenarios E, H; optional mocked CIM in future Pester (not required v1)

### U4. Resolve-PortService freshness integration

- **Goal:** Stale-but-healthy triggers cleanup + restart, not reuse
- **Files:** `scripts/start-dev.ps1`
- **Logic change:**

```
if port occupied:
  if BackendFresh: reuse
  elseif StaleWorkOs: stop resolved tree → free port → start job
  elseif Foreign: BLOCKER exit 1
  else: BLOCKER exit 1
```

### U5. Diagnostics and operator messaging

- **Goal:** Actionable output (missing routes, PIDs, cmdlines, recommended action)
- **Files:** `scripts/start-dev.ps1` (`Write-BackendDevReadyDiagnostics` enhancement)
- **Output:** `missing_paths`, `listener_count`, `ghost_parent`, `spawn_children`, `worktree_match`

### U6. Contract tests

- **Goal:** Prevent regression to `$required = @()`
- **Files:** `scripts/canonical_startup_contract.test.mjs`
- **Scenarios:** Manifest includes collaboration-read path; start-dev references manifest loader

---

## Test Strategy (Implementation Phase)

| Scenario | Expected behavior |
|----------|-------------------|
| **A — backend absent** | Start job; `Wait-ForService` passes only after health + routes |
| **B — backend current** | Classified fresh; reuse; no new job |
| **C — backend stale** | Health OK, route missing; classified stale; stop tree; restart; routes present |
| **D — foreign process** | BLOCKER; PID + cmdline printed; exit 1; process untouched |
| **E — ghost worker** | Ghost parent detected; children listed; children stopped; port freed |
| **F — wrong worktree** | Not reused; per R4 policy (default BLOCKER) |
| **G — OpenAPI fetch fail** | Retries exhausted; fail closed; clear diagnostic |
| **H — multiple listeners** | All enumerated; cleanup if all WorkOS stale; else STOP |

**Automated v1:** Node contract tests (static analysis + manifest). **Manual:** Scenarios C, E, H documented in worklog template.

---

## Runtime Acceptance Plan (Post-Implementation)

Implementation GO must demonstrate:

1. Listener evidence (count = 1 after recovery)
2. PID evidence (reloader + optional child)
3. Worktree evidence (`.venv` under `C:\w\psiso\backend`)
4. `/health` 200
5. `/openapi.json` parse OK
6. All manifest routes present
7. Controlled restart path exercised at least once (scenario C or fresh start)
8. Stability wait ≥15s + recheck
9. Live GET on collaboration-read (order 23099) — 200, read-only
10. **0 DB writes**

**FAIL if based only on:** `/health`, single HTTP 200, TestClient, or assumed PID correctness.

---

## Stop Conditions (Implementation Blocked If)

- Cannot classify foreign vs WorkOS without kill-all → **mitigated** by uvicorn/cmdline/.venv rules; escalate if insufficient
- Worktree undeterminable → use `.venv` path heuristic; block if owner requires stricter proof
- Windows admin required → plan avoids elevation; kernel ghost class (port 8000 anomaly) remains separate playbook
- Route list unstable → manifest versioning + owner review on changes
- Kill-all required → **blocked** — design forbids
- Backend fingerprint required for minimal fix → **not required**; defer Option B
- Cross-worktree harm → default BLOCKER on foreign/wrong-tree
- Full startup rewrite → **not needed** — surgical changes to `Resolve-PortService` + probes

---

## Owner Decisions (R1–R7)

| ID | Question | Plan recommendation |
|----|----------|---------------------|
| **R1** | Fix tooling now or defer? | **Fix now** — FLEX-01B proved recurrence risk; tooling-only, low blast radius |
| **R2** | Strategy A/B/C/D/E? | **E — Hybrid** (health + OpenAPI manifest + process tree) |
| **R3** | Auto-stop stale backend same worktree? | **Yes** — matches 2026-06 BUILD intent; stop resolved tree only |
| **R4** | Backend from other worktree? | **BLOCKER** (do not reuse, do not auto-kill) — print evidence |
| **R5** | Foreign process on 8001? | **STOP mandatory** — exit 1, no kill |
| **R6** | Required route set? | **5 paths** (table above); manifest `v1` |
| **R7** | Implementation authorized? | **Tooling only** — no backend application code in v1 |

---

## Blocked Scope

- Implementation until owner GO on R1–R7
- Backend fingerprint endpoint (Option B)
- FLEX-02, participants_json, DB, UI, Product System, snapshots
- Auto-push, PR (this planning task)

---

## Risks

| Risk | Mitigation |
|------|------------|
| Route removed legitimately → startup fails | Manifest version bump process; CI contract test |
| OpenAPI slow on cold start | Retry in `Wait-ForService` (already 45×2s window) |
| Ghost PID recurrence | Spawn child resolution in U3 |
| `Test-WorkOsBackendListenerCanonical` false negative | Fix `.venv` path check; don't rely on root in cmdline |
| Developer running two worktrees on 8001 | R4 BLOCKER with clear message |

---

## Next Safe Step

**OWNER REVIEW RUNTIME-FRESHNESS-04** — confirm R1–R7, then authorize tooling implementation as a bounded build (no FLEX-02, no backend code).

---

## Sources

- `scripts/start-dev.ps1`, `scripts/_workos-dev-contract.ps1`, `scripts/dev.ps1`
- `.compound-engineering/flex-01b-canonical-8001-runtime-recovery/compound-knowledge.md`
- `.compound-engineering/product-system-active-path-isolation-v1/dev-readiness-active-route-analysis.md`
- `docs/qa/BUILD_INTAKE_V3_OPERATOR_WORKSPACE_RUNTIME_CONNECTIVITY_FIX.md`
- `docs/worklog/realignment/2026-07-15_flex_01b_canonical_8001_runtime_recovery_and_live_verification.md`

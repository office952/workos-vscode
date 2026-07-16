# Runtime Verification — V2 Pilot Proof Attempt #2

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF`  
**Verdict:** `FAIL_RUNTIME`  
**Date:** 2026-07-13  

## Pre-start gate

| Check | Expected | Actual |
|-------|----------|--------|
| Location | `C:\w\psiso` | `C:\w\psiso` |
| Git root | `C:\w\psiso` | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` | match |
| HEAD | `9366a74` | match |
| Port 8000 free | yes | yes |
| Port 3000 free | yes | yes |
| Parser validation | PASS | PASS (script executed) |
| Figma plugin | active | active + authenticated |

## Stack start (attempt 1 of 1)

- **WORKOS_PYTHON:** `C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe`
- **Command:** `npm run dev:stack`
- **Coordinator PID:** 8316
- **Result:** Backend job id=5 started; `Wait-ForService` timed out; backend job stopped; frontend never launched

### Failure signature

```
Backend health check did not pass - recent job output:
  health_ok     = True
  openapi_parse = ok
  missing_paths = /api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments, ...
```

### Root cause

`Test-BackendDevReady` in `scripts/start-dev.ps1` requires Intake V3 operator workspace routes in OpenAPI. On HEAD `9366a74`, `intake_v3_workspaces.py` uses `_deprecated_router` (disabled from auto-discovery). Routes are not registered → gate fails despite healthy backend.

**Classification:** `DEV_READINESS_GATE_STALE_INTAKE_V3_CHECK`

## Listener / PID proof

| Phase | :8000 | :3000 | Backend PID | Frontend PID |
|-------|-------|-------|-------------|--------------|
| During wait | LISTENING 3052 | none | 3052 | none |
| After coordinator exit | free | free | stopped | none |

## Health gate

| Endpoint | During stack | After exit |
|----------|--------------|------------|
| `/health` | 200 | down |
| `/openapi.json` | 200 | down |
| frontend `:3000` | unreachable | unreachable |

**Gate:** FAIL

## Workstreams

| WS | Status |
|----|--------|
| A health | FAIL |
| B identity live | BLOCKED |
| C dossier live | BLOCKED |
| D snapshot live | BLOCKED |
| E UI+Figma | PARTIAL (Figma only) |
| F scope | PASS |

## Supplementary test evidence

`pytest tests/test_product_system_identity_boundary.py tests/test_dossier_true_isolation.py tests/test_dossier_consumption_policy.py -q` → **40 passed** (`TEST_PROVEN_RUNTIME_NOT_MUTATED`)

## Runtime-phase discipline

- Application code: **not modified**
- Artifacts: `docs/qa/product-system-active-path-isolation-v1/RUNTIME_PROOF_REPORT.md`, this file, worklog

## Next action

Owner GO → update `Test-BackendDevReady` / `Test-IntakeV3OperatorWorkspaceRoutesOk` to match live router surface → re-authorize runtime proof (single stack).

---

## Stale gate fix — `PRODUCT_SYSTEM_DEV_READINESS_GATE_STALE_INTAKE_V3_FIX_V1`

| Field | Value |
|-------|--------|
| Verdict | `STALE_GATE_FIX_PASS` |
| Change | Removed 3 deprecated Intake V3 paths from `$required` in `Test-IntakeV3OperatorWorkspaceRoutesOk` and `Write-BackendDevReadyDiagnostics` |
| Classification | `STALE_LEGACY_PATH_CHECK_REMOVED` |
| Parser validation | PASS (zero errors) |
| Runtime started | NO |
| Ready for `/ce-debug` | YES (pending safety gate) |

---

## V2 Pilot Runtime Proof — FINAL RETRY (2026-07-14)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_FINAL_RETRY`  
**Verdict:** `FAIL_CAPABILITY_TRUTH`

### Pre-start gate

| Check | Result |
|-------|--------|
| Location / git root | `C:\w\psiso` |
| Branch / HEAD | `feature/product-system-active-path-isolation-v1` / `9366a74` |
| Ports 8000/3000 free | YES |
| ArmouryCrateControlInterface | Stopped |
| Figma plugin | YES (ERP PUBLIMEDIA) |
| Runtime app changes | NO |

### Stack start (1 of 1)

| Field | Value |
|-------|--------|
| Command | `npm run dev:stack` |
| WORKOS_PYTHON | `C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe` |
| Coordinator PID | 9272 |
| Backend PID | 11352 (:8000) |
| Frontend PID | 20616 (:3000) |
| Backend ready | 4s |
| Frontend ready | 4s |
| Result | **PASS** — stale gate fix confirmed |

### Stability (T+0 and T+8s)

| Endpoint | Status |
|----------|--------|
| `/health` | 200 |
| `/openapi.json` | 200 |
| frontend `:3000` | 200 |
| Duplicate listeners | none |
| Premature cleanup | none |

### Fixture blocker

`backend/dev.db` probe:

- `product_templates`: **0**
- `product_blueprint_dossier`: **0**
- snapshot tables: **MISSING**

### Workstreams

| WS | Result |
|----|--------|
| A health/stability | PASS |
| B identity live | PARTIAL (legacy 422 proven; canonical 404 empty DB) |
| C dossier V2 live | BLOCKED |
| D snapshot/execution | PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA |
| E UI + Figma | PARTIAL (shell OK; catalog empty vs Figma 7:6) |
| F scope | PASS |

### Live identity highlights

- `TPL-VOLUMETRIC-LETTERS` → **422** `rejected_alias` (PASS)
- `TPL-VOLUMETRIC-LETTERS_v2` → **404** `template_not_found` (empty DB)
- `template-availability` → `count=0`

### Screenshots

Six runtime PNGs + two Figma refs under `docs/qa/product-system-active-path-isolation-v1/`.

### Next action

Owner-approved seed/fixture for V2 templates (and optional snapshots) → re-run single-stack runtime proof.

---

## Controlled fixture activation — Phase 2 (2026-07-14)

**Task:** `PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_V1`  
**Verdict:** **`FIXTURE_ACTIVATION_PASS`**

| Check | Result |
|-------|--------|
| Target DB | `C:\w\psiso\backend\dev.db` proven |
| Backup | `dev.pre-product-system-v2-seed.db` |
| `seed_sync_all` | exit **0**, **1 run** |
| Three canonical templates | **present** |
| ACM/Premount capability | **PASS** (policy) |
| Legacy `TPL-VOLUMETRIC-LETTERS` | **removed** (cleanup, no refs) |
| Forbidden tables | **unchanged** |
| Stack started | **NO** (per task) |

**Next:** Phase 3 read-only verification → `/ce-debug` final runtime proof.

---

## V2 Pilot Runtime Proof — POST SEED (2026-07-14)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_POST_SEED`  
**Verdict:** **`PASS_V2_PILOT_WITH_LEGACY_BRIDGE`**  
**Snapshot sub-verdict:** **`PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA`**

### Pre-start gate

| Check | Result |
|-------|--------|
| Location / git root | `C:\w\psiso` |
| Branch / HEAD | `feature/product-system-active-path-isolation-v1` / `9366a74` |
| Seed rerun | **NO** |
| Figma plugin | YES — ERP PUBLIMEDIA / office@p-media.ro |
| Runtime app changes | **NO** |

### Stack start (1 of 1)

| Field | Value |
|-------|--------|
| Command | `npm run dev:stack` |
| WORKOS_PYTHON | `C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe` |
| Coordinator | single owner |
| Backend PID | 11352 (reused existing :8000 listener) |
| Frontend PID | 12712 (:3000) |
| Health / OpenAPI / frontend | **200 / 200 / 200** |

### Fixture state (post-seed)

| Table | Rows |
|-------|------|
| `product_templates` | 8 (3 canonical active) |
| `product_blueprint_dossier` | 4 |
| `quote_snapshots_v2` | 0 |
| `orders` | 0 |
| `execution_plan` | 0 |

### Workstreams

| WS | Result |
|----|--------|
| A health/stability | **PASS** |
| B identity live | **PASS** (canonical + trim/case; legacy 422; unknown 404) |
| C dossier V2 live | **PASS** (metadata-only; operator readonly; admin entity inspect) |
| D capability/aggregate | **PASS** (Premount form 404 documented) |
| E snapshot/execution | **PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA** |
| F UI + Figma | **PARTIAL** (catalog populated; Premount list gap; tab naming vs Figma) |
| G scope | **PASS** |

### Live identity highlights

- Canonical templates → aggregate **200**, stored canonical casing in response
- Legacy `TPL-VOLUMETRIC-LETTERS` compile → **422** `rejected_alias`
- Unknown alias → **404** `template_not_found`
- `template-availability` → **offerable_count=3**

### Screenshots

Six post-seed runtime PNGs under `docs/qa/product-system-active-path-isolation-v1/01`–`06`.

### Ready for `/ce-code-review`

**YES**


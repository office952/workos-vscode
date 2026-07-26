## Worklog — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

**Date:** 2026-07-13  
**Base HEAD:** `82a713e`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Isolated worktree:** `C:\\w\\psiso`  
**Original dirty workspace untouched:** YES

### Summary

Implemented an explicit canonical template identity boundary and enforced it on all Product System “compilation/preview” routes to prevent silent alias writes.\n\nCorrected premount usage-mode policy to match owner truth (root offerable + linked child, not internal-only).

### Key changes

- Added explicit identity resolution contract in `services/template_architecture_scope.py`.\n- Enforced canonical-only identity (reject legacy alias) in Product System compilation routers.\n- Added bounded traceability entries in ProductDefinition provenance and ProductAggregate warnings.\n- Updated premount policy in `services/template_usage_mode_policy.py`.\n- Added targeted pytest coverage.

### Tests run

Used existing backend venv python from the original workspace (read-only reuse):
- `backend/tests/test_template_architecture_scope.py`
- `backend/tests/test_product_system_identity_boundary.py`

Result: **PASS** (8 tests)

### Runtime verification

**Not achieved** within allowed attempt budget (2x `npm run dev:stack`).

Observed behavior in both attempts:
- Backend logged repeated `GET /health` and `GET /openapi.json` as **HTTP 200**.
- Orchestration still reported: `Backend health check did not pass` and exited before starting frontend.

Root-cause post-mortem artifacts:
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-attempt-analysis.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-root-cause-review.md`

---

## V2 Pilot Runtime Proof — 2026-07-13 (attempt 3)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF`  
**Verdict:** `FAIL_RUNTIME`

### Pre-start

- Worktree/branch/HEAD gate: PASS (`C:\w\psiso`, `feature/product-system-active-path-isolation-v1`, `9366a74`)
- Ports 8000/3000: free before start

### Stack start (2 attempts)

Both `npm run dev:stack` with `WORKOS_PYTHON=C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe` failed **before** backend/frontend processes started.

**Root cause:** PowerShell `ParserError` in `scripts/start-dev.ps1` line 170 — Unicode em-dash in `Write-BackendDevReadyDiagnostics` catch string breaks script parse.

### Runtime phase discipline

- Application code: **not modified** during this runtime session
- Artifacts: `docs/qa/product-system-active-path-isolation-v1/RUNTIME_PROOF_REPORT.md`, updated `runtime-verification.md`

### Blocked workstreams

Health, identity matrix (live), dossier authority (live), snapshot/execution, UI routes, screenshots, Figma comparison — all blocked by stack failure.

### Unblock

Owner GO for minimal ASCII fix on `scripts/start-dev.ps1:170`, then re-run runtime proof.

---

## Parser fix — `PRODUCT_SYSTEM_START_DEV_PARSER_FIX_V1` (owner GO)

- **Prior:** two runtime attempts failed with `ParserError` at line 170 before any process creation.
- **Fix:** `unknown — OpenAPI` → `unknown - OpenAPI` (ASCII hyphen only).
- **Validation:** `powershell -NoProfile` + `[Parser]::ParseFile` → zero errors (**PASS**).
- **Runtime:** not started in this task.
- **Semantics:** `PARSER_FIX_ONLY`; readiness predicate unchanged.
- **Next:** repository safety gate → confirm Figma plugin → `/ce-debug` (single recovery attempt).

---

## V2 Pilot Runtime Proof — 2026-07-13 (recovery attempt, post-parser-fix)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF`  
**Verdict:** `FAIL_RUNTIME`

### Pre-start

- Worktree/branch/HEAD: PASS (`C:\w\psiso`, `feature/product-system-active-path-isolation-v1`, `9366a74`)
- Ports 8000/3000: free
- Parser validation: PASS
- Figma plugin: ACTIVE_AND_AUTHENTICATED

### Stack start (1 attempt — task limit)

`npm run dev:stack` with `WORKOS_PYTHON` set:

- Backend job id=5 started (PID 3052 on :8000)
- `/health` and `/openapi.json` returned **200** during wait
- `Test-BackendDevReady` failed: three deprecated Intake V3 operator routes absent from OpenAPI
- Coordinator stopped backend; frontend **never** started

**Root cause:** `DEV_READINESS_GATE_STALE_INTAKE_V3_CHECK` — `_deprecated_router` in `intake_v3_workspaces.py` not auto-registered; `start-dev.ps1` still requires those paths.

### Supplementary evidence (not runtime substitute)

- `pytest` identity + dossier subset: **40 passed**
- Figma file `911Q6oRKcEursrRoT4Qj0h`: frames `7:6`, `7:18`, `7:29` verified; dossier operator/admin frames absent

### Artifacts

- `docs/qa/product-system-active-path-isolation-v1/RUNTIME_PROOF_REPORT.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-verification.md`
- Figma reference PNGs: `01-canonical-catalog.png`, `02-canonical-product-detail-letters.png`, `figma-ref-unavailable-7-29.png`

### Unblock

Owner GO for readiness-gate alignment in `scripts/start-dev.ps1` (remove or replace stale Intake V3 path check), then re-run runtime proof.

---

## Stale dev readiness gate fix — `PRODUCT_SYSTEM_DEV_READINESS_GATE_STALE_INTAKE_V3_FIX_V1`

**Verdict:** `STALE_GATE_FIX_PASS`

### Evidence (read-only workstreams A/B)

- `intake_v3_workspaces.py`: `_deprecated_router` only; comment confirms disabled from auto-discovery
- `main.py`: auto-includes `router` / `admin_router` only — three stale paths intentionally absent from OpenAPI

### Exact fix

Removed from `$required` arrays in `scripts/start-dev.ps1`:

1. `/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments`
2. `/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation`
3. `/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan`

**Post-fix readiness predicate:** `Test-HttpOk(/health)` + OpenAPI fetch/parse success (empty required-path list).

### Validation

- Parser: **PASS** (zero errors)
- Runtime started: **NO**
- Application/Intake code changed: **NO**

### Next gate

Repository safety gate → `/ce-debug` → single `npm run dev:stack` → parallel workstreams A–F + Figma/runtime screenshots.

---

## V2 Pilot Runtime Proof — FINAL RETRY (2026-07-14)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_FINAL_RETRY`  
**Verdict:** `FAIL_CAPABILITY_TRUTH`

### Safety gate

PASS — worktree `C:\w\psiso`, branch `feature/product-system-active-path-isolation-v1`, HEAD `9366a74`, ports free, main workspace untouched.

### Stack (1 start)

- `npm run dev:stack` with `WORKOS_PYTHON` → **SUCCESS**
- Backend PID 11352 (:8000), frontend PID 20616 (:3000)
- Stale Intake V3 gate fix **confirmed**: backend ready 4s, frontend ready 4s
- Stability recheck after 8s: both listeners alive, `/health` 200, frontend 200

### Root runtime blocker

Empty `backend/dev.db`:

- `product_templates`: 0
- `product_blueprint_dossier`: 0
- snapshot tables: missing

### Live proofs

| Area | Result |
|------|--------|
| Legacy alias compile reject | PASS (422 + metadata) |
| Canonical template acceptance | BLOCKED (404, no seed) |
| Catalog ACM/Letters/Premount | FAIL (0 products) |
| Dossier V2 authority live | BLOCKED |
| Snapshot chain | PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA |
| UI unavailable deep links | PARTIAL (matches Figma 7:29 pattern) |
| Figma catalog vs runtime | BLOCK (empty vs 7:6 cards) |
| Screenshots 01–06 | PASS |
| Scope (no app changes) | PASS |

### Artifacts updated

- `.compound-engineering/product-system-active-path-isolation-v1/final-report.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-verification.md`
- `.compound-engineering/product-system-active-path-isolation-v1/decision-log.md`
- `.compound-engineering/product-system-active-path-isolation-v1/risk-register.md`
- `docs/qa/product-system-active-path-isolation-v1/RUNTIME_PROOF_REPORT.md`

### Delivery footer

| Field | Value |
|-------|--------|
| Runtime started | YES |
| Stack starts | 1 |
| Backend stable | YES |
| Frontend stable | YES |
| Application opened | YES |
| Figma plugin used | YES |
| Runtime screenshots complete | YES |
| V2 Dossier isolated (live) | NO |
| Identity runtime proven | PARTIAL |
| Capability truth proven | NO |
| Snapshot/execution | PARTIAL |
| Application code changed | NO |
| Ready for `/ce-code-review` | YES (implementation) |
| Verdict | FAIL_CAPABILITY_TRUTH |

### Unblock

Owner GO → seed V2 product templates (and optional snapshot fixtures) into `backend/dev.db` → re-run runtime proof (single stack, no runtime data mutation).

---

## Fixture activation audit — `PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_AUDIT_V1` (2026-07-14)

**Verdict:** `PARTIAL_SEED_FOUND_SNAPSHOT_FIXTURE_MISSING`

### Stack shutdown

- Stopped runtime PIDs 11352/20616; frontend :3000 free; backend process absent; :8000 shows stale LISTENING ghost entry (PID 11352, no live process).

### Findings

| Area | Result |
|------|--------|
| Canonical Product System seed | **YES** — `backend/scripts/seed_sync_all.py` |
| Three template codes | Covered by pipeline (`seed_tpl_volumetric_letters_v2` + `seed_tpl_acm_boxed_mounting_support_v1`) |
| Idempotent | YES (`test_seed_integrity_guard.py`) |
| Snapshot V2 chain seed | **NO** production command |
| DB target for dev stack | `C:\w\psiso\backend\dev.db` |
| DB mutated | NO |
| Scope | PASS |

### Recommended activation (not executed)

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///C:/w/psiso/backend/dev.db'
# ... other dev env vars ...
cd C:\w\psiso\backend
C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe -m scripts.seed_sync_all
```

### Next gate

**STOP_FOR_OWNER_GO** → controlled seed → V2 runtime proof final retry → `/ce-code-review`.

---

## Controlled fixture activation — Phase 2 (2026-07-14)

**Task:** `PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_V1`  
**Verdict:** **`FIXTURE_ACTIVATION_PASS`**

Owner GO received. Executed once:

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///C:/w/psiso/backend/dev.db'
python -m scripts.seed_sync_all  # exit 0
```

- Backup: `backend/dev.pre-product-system-v2-seed.db`
- Canonical templates: Letters v2, ACM boxed mounting, Premount structure — **present**
- Dossier rows: 4 (metadata/provenance)
- Module links: 3
- Intake/quotes/orders/snapshots: **0 → 0**
- Legacy `TPL-VOLUMETRIC-LETTERS`: deleted by cleanup (expected)
- No stack started; no app code changed by seed

**Ready for final runtime proof:** YES

---

## POST SEED runtime proof — Phase 3 (2026-07-14)

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_POST_SEED`  
**Verdict:** **`PASS_V2_PILOT_WITH_LEGACY_BRIDGE`**

Single stack (`npm run dev:stack`), backend reused PID 11352, frontend PID 12712. Health/OpenAPI/frontend 200.

### Proven live

- Populated catalog (no empty DB state)
- Canonical identity matrix (exact/trim/case → stored canonical code)
- Legacy alias compile reject 422 `rejected_alias`
- ACM + Premount capability flags (root_offerable, linked_child_offerable, internal_only=false)
- V2 dossier metadata-only boundary (operator readonly; entity API 4 rows)
- Six runtime screenshots replaced with post-seed captures

### Partial / follow-up

- Snapshot chain: `quote_snapshots_v2=0`, `orders=0`, `execution_plan=0` → **PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA**
- Premount not in operational catalog card list (direct URL works)
- Premount ProductDefinition 404 → `ROOT_OFFERABLE_WITHOUT_CURRENT_FORM_CONTRACT`
- Blueprint Dossier studio Active (0) vs 4 entity rows

### Scope

No application code changes during runtime phase. Artifacts: `RUNTIME_PROOF_REPORT.md`, compound verification files, worklog.

**Ready for `/ce-code-review`:** YES

---

## Final code review — 2026-07-14

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_FINAL_CODE_REVIEW`  
**Verdict:** **`APPROVE_WITH_NON_BLOCKING_FOLLOWUPS`**

- P0/P1: 0; architecture isolation PASS for V2 pilot
- Non-blocking: Premount catalog FE parity, ProductDefinition form backlog, Dossier studio list, snapshot fixtures
- No app code / DB changes during review

**Ready for `/ce-compound`:** YES

---

## Compound closeout — 2026-07-14

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_COMPOUND`  
**Verdict:** **`COMPOUND_COMPLETE`**

Reusable knowledge: `.compound-engineering/product-system-active-path-isolation-v1/compound-knowledge.md`

Core lesson: V2 pilot canonical path proven; full WorkOS E2E and repo-wide dossier isolation **not** claimed.

No app code, DB, or runtime during compound phase.

**Ready for owner commit GO:** YES → `/ce-commit` (not auto-invoked)



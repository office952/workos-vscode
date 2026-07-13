## Decision log — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### 2026-07-13 — Worktree isolation

- **Decision**: Use a short-path worktree at `C:\\w\\psiso` due to Windows path-length issues.
- **Why**: initial worktree checkout under repo root failed with “Filename too long”.

### 2026-07-13 — Identity boundary enforcement

- **Decision**: Enforce canonical template codes at all active compilation endpoints (ProductSystem preview/compile routes).
- **Why**: prevents silent identity redirection; legacy aliases remain as explicit read bridge only.

### 2026-07-13 — Premount capability policy correction

- **Decision**: Update `template_usage_mode_policy.py` to make premount root-offerable + linked-child allowed + not internal-only.
- **Why**: matches owner truth; no DB/migration required; prevents premount being downgraded to internal-only by policy.

### 2026-07-13 — Runtime root-cause classification for dev-stack failure

- **Decision**: Classify the observed `dev:stack` failure as a backend readiness-gate failure (not disproven by HTTP 200 on `/health`).
- **Why**: orchestration defines backend “ready” as `Test-HttpOk(/health)` **and** OpenAPI schema path validation (`Test-IntakeV3OperatorWorkspaceRoutesOk`), so 200s alone do not imply PASS.

### 2026-07-13 — Stale Intake V3 dev readiness gate removal (owner GO)

- **Decision**: Remove three deprecated Intake V3 OpenAPI path requirements from `scripts/start-dev.ps1` readiness checks.
- **Classification**: `STALE_LEGACY_PATH_CHECK_REMOVED`
- **Evidence**: `_deprecated_router` excluded from `main.py` auto-discovery; runtime attempt showed `/health` 200 + `/openapi.json` 200 but gate failed on missing paths.
- **Preserved**: health check, OpenAPI fetch/parse, ports, timeouts, retries, job lifecycle, exit behavior.
- **Not changed**: Intake V3 backend, application code, ports, runtime.
- **Parser validation**: PASS (zero errors).
- **Runtime started**: NO (per task boundary).
- **Next**: repository safety gate → `/ce-debug` single stack runtime proof.


### 2026-07-13 — /ce-work dossier consumption hardening (confirmed defect)

- **Decision**: Introduce shared `dossier_consumption_policy.py` and enforce approved-only + canonical identity match at consumer surfaces (aggregate, intake-contract, output-blocks).
- **Why**: dossier behavior-bearing JSON was consumed without a shared gate; closeout requires deterministic ignore/reject with traceable provenance.
- **Scope respected**: no Dossier CRUD/RBAC changes.

### 2026-07-13 — /ce-work identity proof-first (fix applied after failing endpoint-backed tests)

- **Verdict**: **`IDENTITY_LOOKUP_FIX_REQUIRED`** (not `IDENTITY_NO_CODE_CHANGE_REQUIRED`).
- **Reproduced failures**: uppercase canonical gate output did not match mixed-case DB/registry keys → 404 on aggregate/product-definition; empty mini-module registry lookup.
- **Minimal fixes applied** (proven lookup boundaries only):
  - `product_aggregate_service._load_template` — case-insensitive DB lookup
  - `mini_module_registry_service.get_by_template` — normalized index lookup
  - `product_definition_builder_service.build_preview` — use DB-stored `aggregate.template_code` for downstream registry/form lookups
  - `acm_quote_input_helpers.is_acm_boxed_mounting_standalone_root_template` — normalized comparison
- **Normalization spec unchanged**: `normalize_template_code` (strip + uppercase) not rewritten.

### 2026-07-13 — /ce-work runtime diagnostics (owner-approved, diagnostics-only)

- **Decision**: Add `Write-BackendDevReadyDiagnostics` in `scripts/start-dev.ps1` on readiness failure paths only.
- **Why**: disambiguate health OK vs OpenAPI path predicate failure without changing readiness semantics.
- **Runtime start**: still **NOT authorized** until joint review after this report.

### 2026-07-13 — OWNER GO: `PRODUCT_SYSTEM_START_DEV_PARSER_FIX_V1`

- **Decision**: Replace Unicode em-dash with ASCII hyphen-minus on `scripts/start-dev.ps1` line 170 only.
- **Why**: `npm run dev:stack` failed with PowerShell `ParserError` before backend/frontend process creation (two documented runtime attempts).
- **Before**: `Write-Host "  missing_paths = (unknown — OpenAPI fetch/parse failed)"`
- **After**: `Write-Host "  missing_paths = (unknown - OpenAPI fetch/parse failed)"`
- **Classification**: `PARSER_FIX_ONLY` — readiness predicate, paths, ports, timeouts, retries, lifecycle unchanged.
- **Parser validation**: PASS (`powershell -NoProfile` + `[Parser]::ParseFile`, zero errors).
- **Runtime started**: NO (per task boundary).
- **Next gate**: repository safety → Figma plugin available → `/ce-debug` (single recovery stack attempt).

### 2026-07-14 — FINAL RETRY runtime proof verdict

- **Decision**: Record verdict `FAIL_CAPABILITY_TRUTH` despite successful stack start.
- **Why**: empty `backend/dev.db` blocks live proof of catalog visibility, ACM/Premount capability truth, canonical acceptance, dossier authority, and populated Figma reconciliation.
- **Stack evidence**: single `npm run dev:stack` PASS; backend 11352, frontend 20616; health/OpenAPI/frontend 200; stability recheck PASS.
- **Identity live**: legacy alias compile reject **proven** (422 + metadata); canonical paths return 404 due to missing seed rows (not identity regression).
- **Snapshot**: `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` — no snapshot tables in dev.db.
- **Runtime mutation**: forbidden and not performed.
- **Next**: owner GO for fixture seed outside runtime phase → re-run proof.

### 2026-07-14 — Fixture activation audit (`PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_AUDIT_V1`)

- **Decision**: Record verdict `PARTIAL_SEED_FOUND_SNAPSHOT_FIXTURE_MISSING`.
- **Finding**: Canonical catalog activation path is existing `scripts/seed_sync_all.py` (idempotent, repo-owned, covers all three V2 template codes + dossier metadata + module links).
- **Gap**: No production seed for Quote Snapshot V2 → Order Snapshot V2 → ExecutionPlan V2 chain; test helpers only.
- **DB target**: `npm run dev:stack` resolves to `C:\w\psiso\backend\dev.db`; operator must set `DATABASE_URL` explicitly when seeding (avoid main-workspace path from AGENTS example).
- **Action**: STOP_FOR_OWNER_GO before any seed execution.

### 2026-07-14 — Phase 2 controlled fixture activation (Owner GO)

- **Decision**: Execute `seed_sync_all` once against `C:\w\psiso\backend\dev.db`.
- **Verdict**: **`FIXTURE_ACTIVATION_PASS`**
- **Evidence**: exit 0; three canonical templates + dossiers + module links; forbidden commercial/intake tables remain 0.
- **Legacy cleanup**: `TPL-VOLUMETRIC-LETTERS` deleted by existing cleanup guard (expected).
- **Next**: Phase 3 fixture verification → final `/ce-debug` runtime proof.

### 2026-07-14 — POST SEED runtime proof verdict

- **Decision**: Record verdict **`PASS_V2_PILOT_WITH_LEGACY_BRIDGE`** with snapshot sub-verdict **`PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA`**.
- **Why**: After `FIXTURE_ACTIVATION_PASS`, single-stack runtime proves V2 identity isolation, dossier metadata-only boundary, ACM/Premount capability truth, and populated catalog/UI; snapshot chain remains unseeded by design.
- **Stack evidence**: one `npm run dev:stack`; backend 11352 (reused), frontend 12712; health/OpenAPI/frontend 200.
- **Identity live**: canonical 200 + trim/case normalization; legacy compile 422 `rejected_alias`; unknown 404.
- **Dossier live**: 4 approved entity rows; operator Dossier tab readonly; no compiler authority from dossier JSON at runtime consumers (V2 pilot scope).
- **Known gaps (non-blocking for pilot)**: Premount missing from operational catalog cards; Premount ProductDefinition 404; Blueprint Dossier studio list Active (0).
- **Runtime mutation**: forbidden and not performed.
- **Next**: `/ce-code-review` on implementation branch.

### 2026-07-14 — Final code review verdict

- **Decision**: Record **`APPROVE_WITH_NON_BLOCKING_FOLLOWUPS`**.
- **Why**: V2 pilot establishes one canonical active path; no P0/P1; identity rejection and dossier metadata-only boundary proven; gaps are FE parity, Premount form contract, snapshot fixtures — non-blocking per commit rules.
- **P2 follow-ups**: Premount catalog card; Blueprint Dossier Active (0); FE `activeTemplateScope` parity drift.
- **Next**: `/ce-compound` closeout → owner scoped commit.

### 2026-07-14 — Compound closeout (`PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_COMPOUND`)

- **Decision**: Record **`COMPOUND_COMPLETE`**; reusable knowledge captured in `compound-knowledge.md`.
- **Scope**: Documentation/synthesis only — no app code, no DB, no runtime, no staging/commit.
- **Core lesson locked**: V2 pilot canonical path proven ≠ full WorkOS E2E or repo-wide dossier isolation.
- **Ready for owner commit GO**: **YES** (with explicit include/exclude list in `final-report.md`).
- **Next**: `/ce-commit` (owner action; not auto-invoked).


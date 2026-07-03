# BUILD_INTAKE_V4_BOUNDARY_CONTRACT_LOCK

**Date:** 2026-06-20  
**Status:** PASS (scoped boundary build)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `6029885836173c443eb49dff6732693f623e195c`  
**Commit:** none (awaiting confirmation)

---

## Purpose

Lock Intake V4 orchestrator boundaries per `docs/audit/INTAKE_V4_ALIGNMENT_AUDIT.md` §19 — without feature sprawl, new templates, ACM/bond, or hardcoded commercial prices.

---

## Working tree before changes

Dirty tree (uncommitted V4 WIP + unrelated V3/V2 edits). This build touched **only** Intake V4 boundary files, tests, and this QA doc. `tmp/` not modified.

---

## Files modified

### Backend

| File | Change |
|------|--------|
| `backend/services/intake_v4_quote_geometry_service.py` | Added `resolve_v4_quote_geometry()` — single canonical derive from nest2 + layer roles |
| `backend/services/intake_v4_analysis_boundary_service.py` | **New** — persist gate blockers + `assert_v4_analysis_boundary_or_raise` |
| `backend/services/intake_v4_finish_adapter.py` | `_resolve_v4_quote_geometry` delegates to canonical resolver |
| `backend/services/intake_v4_workspace_service.py` | Hash change clears `quote_geometry`; finish/pricing/breakdown gates |
| `backend/services/intake_v4_material_breakdown_service.py` | Removed `OWNER_FALLBACK_PRICES`; registry lookup via V3 `_lookup_registry_price`; ACM sheet price lines removed |
| `backend/services/intake_v4_commercial_quote_service.py` | Quote handoff includes analysis boundary blockers |
| `backend/schemas/intake_v4.py` | Default `price_source` → `"missing"` |
| `backend/tests/test_intake_v4_analysis_boundary.py` | **New** |
| `backend/tests/test_intake_v4_material_breakdown.py` | No hardcoded cost assertions |
| `backend/tests/test_intake_v4_workspace.py` | Analysis-bundle seed helpers; 422 gate tests |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/lib/intakeV4/intakeV4AnalysisIdentity.ts` | **New** — SHA-256 hash, sync/unsaved detection |
| `frontend/src/lib/intakeV4/intakeV4Readiness.ts` | Review/Confirm gated on persisted + hash-synced analysis |
| `frontend/src/lib/intakeV4/intakeV4Contracts.ts` | `localFileHash`, `unsavedAnalysis` state |
| `frontend/src/lib/intakeV4/intakeV4WorkspaceReducer.ts` | Stale invalidation on `ANALYZER_START`; hash on persist |
| `frontend/src/lib/intakeV4/useIntakeV4Workspace.ts` | Computes local file hash on analyze |
| `frontend/src/lib/intakeV4/intakeV4QuoteGeometry.ts` | `resolveQuoteGeometryForWorkspace` — no stale persisted metrics |
| `frontend/src/lib/intakeV4/intakeV4Readiness.test.ts` | **New** |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` | Blocked UI + fetch keyed on `analysisIdentityKey` |
| `frontend/src/components/workos/intake-v4/atoms/IntakeV4SmartBanner.tsx` | Unsaved analysis banner |

---

## 1. Analysis snapshot persist gate

**Frontend:** `canAccessIntakeV4Step(review|confirm)` requires `isAnalysisReadyForReview`:

- `svg_analysis_json` persisted
- `svg_source.file_hash` present
- `localFileHash === persisted file_hash`
- `layer_role_setup.confirmation_status === complete`
- `unsavedAnalysis === false`

**Backend:** `assert_v4_analysis_boundary_or_raise` on:

- `GET material-breakdown`
- `GET pricing-input-preview`
- `PUT finish-setup`

**Review/Confirm** cannot proceed on local-only analyzer state without `PUT analysis-bundle`.

---

## 2. Stale state invalidation (re-upload)

On `ANALYZER_START`:

- Clears layers, roles, analyzer report, `localFileHash`
- Sets `unsavedAnalysis: true`, forces step `layers`

On backend `save_analysis_bundle` hash change:

- Clears `finish_setup` and `quote_geometry`

Review step:

- Clears breakdown/pricing/dry-run when `!analysisReady`
- Refetches on `analysisIdentityKey` (hash + run + `updated_at`), not `updated_at` alone

Geometry display uses `resolveQuoteGeometryForWorkspace` — persisted `quote_geometry` only when hash synced.

---

## 3. Single geometry derive

**Backend canonical function:** `resolve_v4_quote_geometry()` in `intake_v4_quote_geometry_service.py`

Used by:

- `intake_v4_finish_adapter._resolve_v4_quote_geometry`
- `intake_v4_material_breakdown_service`
- `intake_v4_pricing_input_service` (via adapter path geometry)
- `intake_v4_analysis_boundary_service`

**Rule:** When `svg_analysis_json` + `layer_role_setup` exist, metrics always derive from `build_quote_geometry_from_analysis` — stale persisted perimeter/area values are not preferred.

---

## 4. Pricing boundary — OWNER_FALLBACK_PRICES removed

| Before | After |
|--------|-------|
| Hardcoded EUR in `OWNER_FALLBACK_PRICES` | `MATERIAL_REGISTRY_CODES` (codes only) |
| `price_source=owner_fallback` always | `price_source=missing` until registry hit |
| `MAT-CANT-ALUMINIU` generic | `MAT-PROFIL-LATERAL-LITERE-{depth}MM` via `PROFILE_DEPTH_MM_TO_VARIANT_CODE` |
| PSU flat 25 EUR | Variant code from `psu_configuration` watts |
| ACM sheet priced in breakdown | Sheet nesting qty-only warning (`sheet_nesting_qty_only`) |

Prices resolved via `inventory_materials` lookup (`_lookup_registry_price` from V3). **No Pricing Foundation build required** for this change — missing registry → `contains_missing_prices: true`, cost total 0.

---

## 5. ProductSystem alignment

Unchanged read-only binding (`intake_v4_product_system_service.py`). Task preview still consumes `operations_json` gates. No duplicate operation catalog in V4.

Missing registry prices reported as breakdown warnings / `contains_missing_prices`, not invented in intake.

---

## 6. Analyzer boundary (confirmed)

- `frontend/src/lib/svgAnalyzer/nesting/buildNestingReport.ts`: `NESTING_GRANULARITY = 'child-parts'`
- No Layer group / Child parts selector in V4 UI
- Layer role confirmation separate from nesting (Pas 1 vs nesting report in JSON only)
- No DXF/CNC export added to Intake V4

Legacy `POST .../svg` server parse remains for layer-role draft only — **not** sufficient for Review/Confirm (no `svg_analysis_json`).

---

## Tests run

### Backend (PASS)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_analysis_boundary.py tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_quote_geometry.py tests/test_intake_v4_workspace.py tests/test_intake_v4_pricing_input.py tests/test_intake_v4_finish_adapter.py -q
```

**Result:** 34 passed

### Frontend (PASS)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4 src/lib/svgAnalyzer
```

**Result:** 11 files, 29 passed

### Not run / off-scope

| Target | Reason |
|--------|--------|
| `tests/test_intake_v4_commercial_quote.py` | Setup error: `seed_build4_templates` / `db_manager.async_session_maker` None — pre-existing env fixture issue, not introduced by this build |
| Playwright `e2e/intake-v4-pbl-complex-desktop.spec.ts` | Not run (manual/E2E follow-up) |
| `validate:frontend` | Repo-wide TS debt — out of scope |

---

## PASS criteria checklist

| Criterion | Status |
|-----------|--------|
| Review/Confirm blocked after re-upload without persist | ✅ |
| Analysis persist = real gate (backend + frontend) | ✅ |
| file_hash / analysis identity in readiness | ✅ |
| No hardcoded commercial prices in V4 breakdown | ✅ |
| ProductSystem/Pricing boundary respected | ✅ |
| Nesting child-parts-only | ✅ (unchanged, verified) |
| No per-template analyzer | ✅ |
| No ACM/casetare bond activation | ✅ |
| Scoped tests green | ✅ |

---

## Remaining blockers for production-ready

1. **Deprecate/remove** legacy `POST .../svg` from operator UX (still used internally for layer draft in tests)
2. **Pricing / Prices Foundation** — populate `inventory_materials` so breakdown shows registry prices instead of `missing` (separate build; not required to remove hardcoding)
3. **E2E** stable Playwright on analysis-bundle → Review → Confirm path
4. **QuoteWizard** hydrate from IV4 snapshot linkage (Phase C from audit)
5. **Frontend TS debt** full gate

---

## Recommended next build

1. **V4 pilot volumetric E2E** — Playwright on persist gate + finish confirm + draft quote  
2. **Pricing / Prices Foundation** — only if operator needs non-zero informative costs in dev/staging  
3. **Casetare bond adapter** — after volumetric pilot cutover decision

---

## Boundary

**In scope:** persist gate, stale invalidation, single geometry derive, registry-only breakdown pricing, readiness tests.

**Out of scope:** CostEngine changes, new templates, ACM, DXF export, UI polish, commits without user confirmation.

---

## E2E addendum: V4 pilot volumetric (2026-06-20)

**Spec:** `frontend/e2e/intake-v4-boundary-pilot-volumetric.spec.ts`  
**Fixture:** `frontend/src/lib/svgAnalyzer/fixtures/pbl-complex.svg` (repo)  
**Re-upload fixture:** `frontend/e2e/fixtures/volumetric-letters-reupload.svg` (minimal)

### Scenarios (3/3 PASS)

| Test | Verifies |
|------|----------|
| `blocks Review before analysis-bundle persist` | Progress Review disabled + smart banner unsaved |
| `analysis-bundle → Review → Confirm with registry-safe breakdown` | Full pilot + API: no `owner_fallback`, quote_input geometry sync, Confirm step |
| `re-upload invalidates Review until re-persisted` | Review blocked after new SVG; perimeter changes after re-persist |

### Command

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-boundary-pilot-volumetric.spec.ts
```

**Result:** 3 passed (~6s) with dev stack on :8000/:3000

### E2E-support changes (minimal)

- `frontend/e2e/helpers/intakeV4Live.ts` — workspace/breakdown/pricing fetch helpers
- `IntakeV4ProgressBar.tsx` — `data-testid="intake-v4-progress-step-{layers|review|confirm}"`

### Note on `intake-v4-pbl-complex-desktop.spec.ts`

Still depends on desktop path `C:\Users\offic\Desktop\pbl-complex.svg` — not run in this build; new spec uses repo fixture and is the canonical boundary pilot gate.

### Combined build status

**BOUNDARY_CONTRACT_LOCK + E2E pilot:** PASS scoped (unit + E2E boundary spec green).

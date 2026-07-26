# Worklog — AcmPanel matching QA DXF measured UI proof v1

**Build:** `WORKOS_ACM_PANEL_MATCHING_QA_DXF_MEASURED_UI_PROOF_V1`  
**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Prerequisite HEAD:** `94148b8` (live DXF attachment screenshots)

## Verdict

**PASS** — dedicated QA workspace `IV6-13D39D32` matches golden double-fold DXF, measured UI + CPP quantities proven; `IV6-DB2F86B7` unchanged (unavailable, no golden attachment).

## What was done

1. Seeded QA Intake V6 workspace with AcmPanel config **2000×300 / L1=100 / L2=30 / fold_count=2 / p1**.
2. Uploaded golden `backend/tests/fixtures/acm_panel_dxf/2-pliuri-100x30.dxf` via real bind path.
3. Runtime proof JSON: measured CUT/V exact; CPP cut=5.499412, v=10.000004; gates false; IV6 before/after control.
4. Playwright matrix 20/20 PASS on FE `:3011` / BE `:8011`.
5. Minimal product fix so Review hydrate/persist does not wipe `acm_panel_instance` (required for measured UI survival).

## QA workspace

| Field | Value |
|-------|--------|
| workspace_code | `IV6-13D39D32` |
| workspace_id | `a7a74172-ad09-4f93-b0f5-f89fe5b9aad9` |
| template | `TPL-VOLUMETRIC-LETTERS_v2` (letters + AcmPanel support path) |
| component_instance_id | `acm_qa_double_fold_2000x300` |
| DXF | `2-pliuri-100x30.dxf` |
| measured | CUT 5.499412 · V L1 5.4 · V L2 4.600004 · V total 10.000004 |

Scaffold: read-only copy of IV6 SVG/analysis/layer roles so Review is `analysisReady` (placeholder SVG caused analysis-bundle + empty finish autosave). AcmPanel commercial geometry is QA overlay, not IV6 2000×350.

## Product fix (narrow)

| File | Change |
|------|--------|
| `frontend/src/lib/intakeV6/intakeV4Api.ts` | `acm_panel_instance` on finish type |
| `frontend/src/lib/intakeV6/acmPanel/finishSetupAcmHydrate.ts` | pure hydrate helper for AcmPanel finish fields |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | hydrate + sync signature via helper |
| `backend/services/acm_panel_domain_service.py` | upsert/preserve keep existing instance when FE omits it |

### Regression tests

| Suite | Result |
|-------|--------|
| `backend/tests/test_acm_panel_domain_coalesce_v1.py` | 5 passed (incl. autosave omit + analysis race) |
| `frontend/.../finishSetupAcmHydrate.test.ts` | 3 passed |

### Hydrate bug (exact)

`finishFromPayload` in Review built the form without `acm_panel_instance`. Unconfirmed finish always set `selectorPendingSave`, so autosave PUT omitted the instance. Coalesce then dropped measured `production_geometry` (especially after analysis-bundle rewrote layer roles away from `support_panel`). Fix: hydrate AcmPanel fields into the form + coalesce preserve/upsert when instance is omitted.

## Evidence

`docs/audits/_evidence/2026-07-20_acm-panel-matching-qa-dxf-measured-ui/`

- `runtime-proof.json`, `iv6-before.json`, `iv6-after.json`, `qa-workspace.json`
- `seed_and_proof.py`, `capture-ui.mjs`, `screenshot-report.json`, `shots/01–20`
- `screenshots-status.md`

## Boundaries respected

No DXF generator · no IV6 mutation · no rates/Offer/Order/Execution · no migrations · no UI redesign · capture blocked finish-setup/analysis-bundle writes.

## Next

Owner review. Prefer docs/evidence (+ hydrate fix) commit when requested.

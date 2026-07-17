# Worklog — SVG closed-contour → Alucobond cased-panel V1

| Field | Value |
|-------|-------|
| Task | `SVG_ANALYZER_CLOSED_CONTOUR_TO_ALUCOBOND_CASED_PANEL_V1` |
| Owner GO | `GO_SVG_ANALYZER_CLOSED_CONTOUR_TO_ALUCOBOND_CASED_PANEL_V1` |
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `aea2376` |
| Feature commit | `223aba4` |
| Start | `SVG_CLOSED_CONTOUR_ALUCOBOND_BUILD_IN_PROGRESS` |
| Final | `SVG_CLOSED_CONTOUR_ALUCOBOND_BUILD_COMPLETE_WITH_GUARDS` |

## Stages

| # | Timestamp (local) | Note |
|---|-------------------|------|
| 1 | baseline | Dirty tree protected; fixture SHA `afce1e6f…`; bytes 17827; not copied |
| 2 | parser audit | Reuse nest2 `analyzeSvgString` + ParsedSvgDocument; no parallel parser |
| 3 | identity audit | Primary: `contour_id = cc_<geometry_hash>`; `el-N` support only |
| 4 | PD audit | `finish_setup.svg_support_selection` + `mounting_solution` ACM template |
| 5 | impl FE | closed-contour detect/score + Alucobond panel + preview overlay |
| 6 | impl BE | ACM config passthrough + canonical_values projection + inactive isolation |
| 7 | tests | FE contour 6 PASS; Intake SVG step 11 PASS; BE PD 3 PASS |
| 8 | runtime proof | 21 closed contours; top polygon `cc_60db6024`; SHA unchanged |
| 9 | docs | contracts + audit + this worklog |
| 10 | commit | exact-path feature + worklog (after PASS) |

## Fixture

- Path: Desktop external (not in repo)
- SHA before/after identical
- Unit ambiguity: Corel cm → viewBox-as-mm guard

## Guards remaining

1. Physical mm not authoritative without owner scale confirmation (unit_ambiguity).
2. Full click-path screenshots on seeded Intake workspace not captured this pass.
3. Broader `svgAnalyzer` suite has pre-existing fixture ENOENT / logo-name failures unrelated to this build.
4. No CPP / tasking / DXF / process DAG activation (by design).

## Key files

### Created

- `frontend/src/lib/svgAnalyzer/closed-contour/closedContourTypes.ts`
- `frontend/src/lib/svgAnalyzer/closed-contour/closedContourCandidates.ts`
- `frontend/src/lib/svgAnalyzer/closed-contour/closedContourCandidates.test.ts`
- `frontend/src/lib/svgAnalyzer/closed-contour/alucobondCasedPanelSelection.ts`
- `frontend/src/lib/intakeV6/intakeV6SvgPreviewContourOverlay.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6AlucobondContourPanel.tsx`
- `backend/tests/test_svg_support_selection_product_definition.py`
- `docs/architecture/SVG_CLOSED_CONTOUR_SELECTION_CONTRACT.md`
- `docs/architecture/ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md`
- `docs/audits/2026-07-17_svg_alucobond_real_fixture_validation.md`
- `docs/audits/_runtime_fixture_proof.json`

### Modified

- `frontend/src/lib/svgAnalyzer/analyzer/analyzeSvg.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/types.ts`
- `frontend/src/lib/svgAnalyzer/index.ts`
- `frontend/src/lib/intakeV6/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6SvgPreviewCanvas.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersFileConfirmPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6SvgPreviewInspectDialog.tsx`
- `backend/services/mounting_solution_service.py`
- `backend/services/product_definition_builder_service.py`

## Dead pieces (report only)

- Color-based layer highlight remains for **layers** (pre-existing); contour scoring does not use color.
- `el-N` remains parse-order secondary id — primary selection identity is geometry hash.
- No duplicate SVG parser introduced.
- No DXF / CPP hooks added.

## Next safe step

**Option 1 — OWNER REVIEW OF REAL SVG ALUCOBOND SELECTION**

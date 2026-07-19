# Worklog — Intake V6 Support Role Truth Repair

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline / audit hash:** `4dede53d8fd220d0773da318f6e7384bdd532048` (`docs(intake-v6): audit layer role and template wiring`)  
**Visual pilot accepted:** `f39c260`  
**Acceptance stack:** FE `http://127.0.0.1:3000` (proxy `BACKEND_PORT=8003`) · BE `http://127.0.0.1:8003`

---

## Root cause

`guessLayerAutoRole` short-circuited every `pseudo:*` fill to `face` / high. ACM grey panel and letter fills were both proposed as Vector Litere. Correct ACM binding existed only after operator correction.

Secondary:

- FinishSetup Contur suport failed when analysis-bundle was not yet persisted, and letter-binding sync called FinishSetup while roles were incomplete (generic Contur suport error).
- Server `POST …/svg` omitted `svg_source_text` / nest2 analysis → empty Page 1.
- Progress treated Confirmare like Review once analysis ready.

---

## Chosen algorithm

1. Soften pseudo short-circuit; fall through to metrics (multi-shape → face).
2. Post-pass `refineLayerRoleProposalsWithGeometry` using sibling complexity, filled/bbox area, and outer closed-contour dimension match — **no color**.
3. Strong support → propose `support_panel` (still pending confirmation).
4. Flush analysis-bundle with explicit confirmation before SUPPORT_CONTOUR FinishSetup; segmented proposal separate.
5. Persist `svg_source_text` on server upload; FE bridge re-runs canonical client analyzer.
6. Confirmare access requires analysis ready **and** product composition confirmed; Review stays open.

---

## Rejected shortcuts

- Grey/color ACM heuristic  
- Fixture filename hardcodes  
- Auto-confirm support / segmented / composition  
- Second analyzer / PD–Aggregate redesign  
- Design System expansion / Montaj / pricing  

---

## Changed files (repair boundary)

- `frontend/src/lib/svgAnalyzer/analyzer/guessLayerAutoRole.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/refineLayerRoleProposalsWithGeometry.ts` (new)
- `frontend/src/lib/svgAnalyzer/analyzer/analyzeSvg.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/analyzeLayers.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/guessLayerAutoRole.supportProposal.test.ts` (new)
- `frontend/src/lib/intakeV6/intakeV6ServerUploadHydrationBridge.ts` (new)
- `frontend/src/lib/intakeV6/intakeV6ServerUploadHydrationBridge.test.ts` (new)
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.test.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx`
- `backend/services/intake_v6_workspace_service.py`
- QA pack + worklog under `docs/qa/intake-v6-support-role-truth-repair-2026-07-19/` and this file

---

## Tests

Focused Vitest: support proposal, hydration bridge, readiness Confirmare gate, associatePrimarySupportContour — PASS.  
Backend `test_early_svg_support_finish_setup_v1.py` — run with repair commit.  
Pre-existing fail: `ana-maria-layer-roles` stroke-only logo names (unrelated).

---

## Runtime evidence

`docs/qa/intake-v6-support-role-truth-repair-2026-07-19/runtime/repair_live_summary.json`

- ACM client: grey proposed Contur suport; SUPPORT_CONTOUR → ACM template; reload keeps; no FinishSetup error  
- Simple letters: face only; no false support  
- Server upload: `svg_source_text` stored; Page 1 hydrated with same proposals  

Screenshots: `docs/qa/intake-v6-support-role-truth-repair-2026-07-19/screenshots/`

---

## Remaining risks

- Bridge depends on FE proxy targeting the BE that stores `svg_source_text` (`BACKEND_PORT=8003` for acceptance).  
- Ambiguous multi-panel SVGs without letter siblings stay `unknown` (by design).  
- Confirmare now requires composition confirmation for step access — operators must finish composition in Review.

---

## Next recommendation

One coherent build after owner GO: resume letter Design System polish **only** if wiring remains green on mandatory fixtures — do not expand DS globally yet.

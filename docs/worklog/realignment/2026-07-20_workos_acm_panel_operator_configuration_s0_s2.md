# Worklog — WORKOS_ACM_PANEL_OPERATOR_CONFIGURATION_S0_S2

**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD before:** `7c72250271471dba88ff753543cb9096b8b797c1`

## Plan Mode

- Large-files audit approved (B).
- UI 21st/Figma audit approved.
- Freeze: SvgAnalyzer atomic path / preserve / finishPersistChain — **not modified**.
- ReviewStep = mount only; AcmPanel logic in lib + `acm-panel/` components.

## Capabilities

| Cap | Used |
|-----|------|
| Vitest | yes |
| pytest coalesce | yes |
| Playwright screenshots | yes |
| API runtime IV6-DB2F86B7 | yes |
| 21st/Figma new research | no — reused audit evidence |

## Boundaries delivered

1. `acmPanel/resolveInstance.ts` + `uiReadModel.ts`
2. `IntakeV6ProductComponentList.tsx`
3. `IntakeV6AcmPanelInspector.tsx` (+ validation rail, fundal summary, config region)
4. `acmPanel/operatorPatch.ts` — single write-path

## LOC / effects

| Metric | Before | After |
|--------|-------:|------:|
| ReviewStep lines | ~3757 | ~3816 (+~59 mount wiring) |
| ReviewStep useEffect | 24 | 24 |
| New acm-panel UI files | 0 | 6 |
| New acmPanel lib files | 0 | 3 (+tests) |

## Legacy Fundal

When `acmPanelUiModel.exists`: editable ACP field grid hidden; `IntakeV6AcmPanelFundalSummary` + navigate to inspector. Segmented panel moved to inspector (not duplicated).

## Runtime note (IV6-DB2F86B7)

After confirm construction: top-level `acm_panel_instance` present; `fold_count` authority `operator_confirmed`; `composition_status` remains `unconfirmed`; composition UI shows honesty inconsistency when product composition was previously confirmed without instance axis.

## Tests

- Vitest: uiReadModel, operatorPatch, instantiate, composition panel, component list — pass
- pytest: `test_acm_panel_domain_coalesce_v1` — 3 passed

## Evidence

`docs/audits/_evidence/2026-07-20_acm-panel-operator-s0-s2/`

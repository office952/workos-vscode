# Worklog — AcmPanel commercial geometry deduction v1

**Build:** `WORKOS_ACM_PANEL_COMMERCIAL_GEOMETRY_DEDUCTION_V1`  
**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Prerequisite HEAD:** `b136f07` (matching QA measured UI PASS)

## Verdict

**PASS (implementation)** — offer-time CUT/V from per-panel commercial deduction when DXF absent; measured DXF remains optional override; Final/Offer/Execution stay blocked.

## Principle

```text
Oferta deduce suficient de bine.
Productia va confirma exact mai tarziu.
```

## What was done

1. Added `build_commercial_deduction_panel_metrics` (blank-based single/double, `fold_sides=all`).
2. Wired `resolve_production_geometry_metrics`: measured → commercial deduction → unavailable; stale measured → deduction.
3. Retired face-perimeter `proxy_rectangular` as CUT/V authority (legacy status still consumable if present).
4. CPP / dry-run consume `commercial_deduced*`; warning `cut_v_quantity_source=commercial_deduction`.
5. Minimal UI: source label, multi-panel note, DXF optional copy (no ReviewStep logic growth).
6. Tests, runtime proof, screenshots.

## Golden deduction

| Case | CUT | V L1 | V L2 | V tot |
|------|-----|------|------|-------|
| Single 2000×300 L1=100 | 5.400000 | 5.400000 | 0 | 5.400000 |
| Double 2000×300 L1=100 L2=30 | 5.640000 | 5.400000 | 4.600000 | 10.000000 |

Measured oracle (double): CUT 5.499412 / V 10.000004 — delta OK for quoting.

## Runtime (control / measured QA)

| Workspace | Path | CUT | V | Gates |
|-----------|------|-----|---|-------|
| `IV6-DB2F86B7` | `commercial_deduced` | 7.176 | 12.128 | all false |
| `IV6-13D39D32` | `measured` / `imported_dxf` | 5.499412 | 10.000004 | all false |

## Evidence

`docs/audits/_evidence/2026-07-20_acm-panel-commercial-geometry-deduction/`

- `runtime_proof.py` → `runtime-proof.json` (`ok: true`)
- `capture-ui.mjs` → `screenshot-report.json` (9/9 PASS)
- `shots/01–09`

## Tests run

| Suite | Result |
|-------|--------|
| `test_acm_commercial_geometry_deduction_v1.py` | pass |
| `test_acm_production_geometry_metrics_v1.py` | pass |
| `test_acm_commercial_geometry_v1.py` | pass |
| `test_acm_panel_pricing_preview_cpp_v1.py` | pass |
| `test_acm_production_geometry_attachment_v1.py` | pass |
| `test_acm_panel_domain_coalesce_v1.py` | pass (regression) |
| FE `acmPanelCommercialPreviewDisplay.test.ts` + `productionGeometryApi.test.ts` | 8 pass |

## Boundaries respected

No DXF generator · no production workspace · no corner/tolerance engines · no parallel contract · no rate changes · no Offer/Order/Execution writes · no migrations · no substantial `IntakeV6ReviewStep.tsx` changes · hydrate/measured binding untouched.

## Next

Owner review of honesty (commercial vs measured) and CUT/V quantity shifts vs prior face-perimeter proxy.

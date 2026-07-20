# Worklog — ACM Panel production geometry metrics + pricing truth v1

**Build:** `WORKOS_ACM_PANEL_PRODUCTION_GEOMETRY_METRICS_AND_PRICING_TRUTH_V1`  
**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** preparatory metrics contract + measured DXF paths; Slice C proxy retained only when eligible

## Purpose

Introduce a single canonical production-geometry metrics contract, measure CUT / V L1 / V L2 from owner golden DXFs (SPLINE + ACI color), and feed Pricing quantities honestly. Replace Slice C rectangular perimeter proxy only where the fallback policy allows.

## Ownership (binding)

```text
AcmPanel configuration
→ panel geometry
→ measured production metrics
→ CPP quantities
→ Pricing Registry rates
→ provisional preview
```

Pricing consumes quantities only; does not generate DXF, CNC paths, L1/L2 ownership, semantic mapping, or operation order.

## Files (feature)

| Area | Path |
|------|------|
| ACI map | `backend/services/acm_aci_semantic_mapping.py` |
| DXF measure | `backend/services/acm_dxf_path_measurement.py` |
| Metrics contract | `backend/services/acm_production_geometry_metrics.py` |
| Wire | `backend/services/acm_commercial_geometry.py` |
| Dry-run | `backend/services/intake_v6_priced_quote_dry_run_service.py` |
| Dev dep | `backend/requirements-dev.txt` (`ezdxf`) |
| Fixtures | `backend/tests/fixtures/acm_panel_dxf/` |
| Tests | `backend/tests/test_acm_production_geometry_metrics_v1.py` (+ commercial/pricing updates) |
| FE | `acmPanelCommercialPreviewDisplay.ts`, types, `AcmPanelProvisionalPricingBlock.tsx` |

## ACI mapping (v1)

Source: owner golden `un-pliu.dxf` + `2-pliuri-100x30.dxf` (all entities `Layer 1`, type `SPLINE`).

| ACI | Semantic |
|-----|----------|
| 256 (ByLayer) | CUT |
| 250 | CUT |
| 1 | V_GROOVE_L1 |
| 242 | V_GROOVE_L2 |
| other | UNKNOWN → warning, excluded from totals |

Version: `acm_aci_semantic_mapping_v1`. Not owned by Pricing.

## Golden results (measured)

| | Single | Double |
|--|--------|--------|
| CUT ml | 5.400000 | 5.499412 |
| V L1 ml | 5.400000 | 5.400000 |
| V L2 ml | 0 | 4.600004 |
| V total ml | 5.400000 | 10.000004 |

SPLINE flatten distance: 0.01 mm; compare tolerance: `5e-5` ml.

## Fallback

`proxy_rectangular` only for single-fold, L2=0, fold_sides=all, rectangular, no cutouts/special corners, no measured metrics. Otherwise `quantity_unavailable` + gates blocked.

## IV6-DB2F86B7 (runtime)

- Face area remains **0.700** mp (assembly 2000×350).
- Operator fold is double-fold (L2 active) → path status **unavailable** (not silent 5.4).
- Preview provisional; final / Offer / Execution blocked.
- Warnings include `double_fold_proxy_forbidden`, `l2_active_proxy_forbidden`, `quantity_unavailable`.

Evidence: `docs/audits/_evidence/2026-07-20_acm-panel-production-geometry-metrics/runtime-proof.json`.

## Pricing policy

- One commercial V line: `acm_v_groove` quantity = `v_groove_total_ml`.
- CUT line consumes `cut_length_ml`.
- Six rates unchanged; no hourly; no second V rate.

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_production_geometry_metrics_v1.py tests/test_acm_commercial_geometry_v1.py tests/test_acm_panel_pricing_preview_cpp_v1.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/acmPanel/acmPanelCommercialPreviewDisplay.test.ts src/components/workos/intake-v6/AcmPanelProvisionalPricingBlock.test.tsx

.\.venv\Scripts\python.exe docs\audits\_evidence\2026-07-20_acm-panel-production-geometry-metrics\runtime_proof.py
```

## Boundary

No rate changes, Offer/Order/Execution, task_rules, operation DAG, Blueprint redesign, Inventory writes, migrations, seeds, Figma, 21st.dev, golden hardcoding in production logic.

## Next

Owner review of honesty on IV6 (unavailable paths vs prior proxy 5.4). Optional: wire operator-imported DXF into instance for measured source on live fixtures.

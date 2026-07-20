# WORKOS_ACM_PANEL_COMMERCIAL_GEOMETRY_DEDUCTION_V1

| Field | Value |
|-------|--------|
| Status | **IMPLEMENTED — awaiting owner review** |
| Date | 2026-07-20 |
| Prerequisite HEAD | `b136f07` (matching QA measured UI PASS) |
| Branch | `feature/product-system-active-path-isolation-v1` |

## Principle

```text
Oferta deduce suficient de bine.
Productia va confirma exact mai tarziu.
```

DXF measured = optional override. Not required for Pricing Preview.

## What shipped

1. Per-panel `build_commercial_deduction_panel_metrics` (single/double, `fold_sides=all`).
2. Resolve path: measured → commercial deduction → unavailable (stale → deduction).
3. CPP/dry-run consume `commercial_deduced*`; gates stay blocked.
4. Minimal UI copy: source label, multi-panel note, DXF optional.
5. Tests + runtime proof + screenshots + worklog.

## Formulas (fold_sides=all)

See worklog / owner GO. Golden:

| Case | CUT | V L1 | V L2 | V tot |
|------|-----|------|------|-------|
| Single 2000×300 L1=100 | 5.400000 | 5.400000 | 0 | 5.400000 |
| Double 2000×300 L1=100 L2=30 | 5.640000 | 5.400000 | 4.600000 | 10.000000 |

## Hard boundaries respected

No DXF generator · no production workspace · no corner/tolerance engines · no parallel contract · no rate changes · no Offer/Order/Execution · no migrations · no substantial `IntakeV6ReviewStep.tsx` growth.

## Evidence

`docs/audits/_evidence/2026-07-20_acm-panel-commercial-geometry-deduction/`

## Worklog

`docs/worklog/realignment/2026-07-20_acm_panel_commercial_geometry_deduction_v1.md`

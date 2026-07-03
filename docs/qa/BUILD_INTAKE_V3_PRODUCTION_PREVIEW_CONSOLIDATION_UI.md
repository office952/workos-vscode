# BUILD — INTAKE_V3_PRODUCTION_PREVIEW_CONSOLIDATION_UI

**Verdict:** PASS  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `7f9c93c`  
**Date:** 2026-06-19

## Purpose

Consolidate Intake V3 production-preview panels into a single **Production Preview** container with overview, grouped expandable sections, and centralized warnings/blockers — **frontend-only**, no backend logic changes.

## Audit — existing panels (before)

| Order | Panel | Role |
|-------|-------|------|
| 1 | Order Production Readiness | Handoff audit |
| 2 | Layer Role Confirmation | **Operator input** (stays outside) |
| 3 | Layer Role Propagation | Geometry/layers preview |
| 4 | Geometry Metrics | Geometry/layers preview |
| 5 | Path Perimeter Classification | Geometry/layers preview |
| 6 | Material Breakdown | Materials preview |
| 7 | Material Availability | Materials preview |
| 8 | Procurement Preview | Procurement decisions preview |
| 9 | Production Task Dry-Run | Task handoff preview |

**Repeated data:** readiness status, geometry status, material shortage counts, procurement counts, task dry-run summary scattered across panels.  
**Warnings:** per-panel lists with overlapping themes (shortage, stale snapshot, owner decision).

## Strategy chosen: **frontend-only aggregation**

No new backend endpoint. Helper `productionPreviewSummary.ts` aggregates existing fetch responses already loaded in `IntakeV3App`.

## What stays active input

- **Layer Role Confirmation** — remains **outside** Production Preview (operator edits SVG layer roles).

## What moved under Production Preview

Container `IntakeV3ProductionPreviewPanel` groups:

1. **Overview** — consolidated status + readiness panel  
2. **Geometry & Layers** — propagation, geometry metrics, perimeter classification  
3. **Materials & Stock** — breakdown + availability  
4. **Procurement Decisions** — procurement preview  
5. **Task Handoff Preview** — task dry-run  

Sub-panels remain mounted (hidden when section collapsed) so existing testids/copy stay accessible.

## Warnings / blockers centralization

- `collectProductionPreviewWarnings()` — merges warnings from all preview responses  
- `collectProductionPreviewBlockers()` — readiness blockers + task dry-run blockers  
- `deriveProductionPreviewOverallStatus()` — ready / partial / blocked / decision_required / unknown  

Policies unchanged: owner decision = warning/decision, not auto-blocker for execution.

## Flow stepper

Existing step IDs preserved. Added optional `group: "Production Preview"` on steps from production readiness audit through task dry-run (excluding layer role confirmation). FlowStepper shows group label on grouped steps.

## Boundary (confirmed)

- Read-only UI consolidation only  
- No ExecutionPlan / ExecutionTask / WorkSession  
- No Inventory / StockMovement / PO / CostEngine  
- No Order/Quote status or pricing mutation  
- No Generate Tasks / Start Production / Reserve / Purchase buttons  

## Files changed

### Frontend (new)
- `frontend/src/lib/intakeV3/productionPreviewSummary.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionPreviewPanel.test.tsx`

### Frontend (updated)
- `frontend/src/pages/IntakeV3App.tsx`
- `frontend/src/pages/IntakeV3App.test.tsx`
- `frontend/src/lib/intakeV3/flowState.ts`
- `frontend/src/lib/intakeV3/flowState.test.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3FlowStepper.tsx`

### Docs
- This file + intake-v3 status/roadmap/readiness/decisions/handoff updates

## Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3ProductionPreviewPanel.test.tsx src/components/workos/intake-v3/IntakeV3ProcurementPreviewPanel.test.tsx src/components/workos/intake-v3/IntakeV3MaterialAvailabilityPanel.test.tsx src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
# 189 passed

## Open questions

- Optional backend `production-preview-summary` endpoint if mobile/owner dashboard needs single fetch  
- Default expanded sections per operator role (owner vs shop floor)  
- Collapse state persistence per workspace  

## Recommended next build

`INTAKE_V3_PRODUCTION_HANDOFF_EXECUTION_GUARD` or owner dashboard consuming optional backend summary endpoint.

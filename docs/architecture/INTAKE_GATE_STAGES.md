# Intake Gate Stages (BUILD-INTAKE-GATE-CONDITIONAL)

Follow-up to [INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md](./INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md).

## Problem

Generic unresolved intakes (`product_family` empty) showed terrain audit, fiscal/CUI lookup, template CTAs, and quote readiness blockers before the operator selected a work type.

## Stage model

| Stage | Condition | Visible | Hidden |
|-------|-----------|---------|--------|
| **0** | `product_family` empty, no template | Client/context, description, delivery (info only), **Alege tip lucrare** | Terrain, CUI, spec editor, vector, quote handoff, product readiness |
| **1** | Work type known, not quote-ready | Template workspace, spec editor, conditional terrain if install | — |
| **2** | Quote-critical inputs sufficient | Preliminary simulation, estimate blockers | — |
| **3** | Commercial quote requirements met | Commercial quote gate, fiscal when needed | — |

Implementation: `frontend/src/lib/intakeGateStages.ts` + conditional render in `IntakeDetail.tsx` (generic shell only).

## Delivery sync (BUILD-DELIVERY-SYNC)

Terrain visibility is driven by `requiresTerrainAudit()` in `frontend/src/lib/intakeDeliverySemantics.ts`:

- Stage 0 → never terrain, even if `delivery_install`
- Stage 1+ with install → terrain panel active
- Stage 1+ without install → terrain N/A; existing site data preserved

## Boundaries preserved

- Readiness policy (`intakeReadiness.ts`) unchanged — Stage 0 only filters **display**.
- Volumetric workspace (`TemplateWorkspaceRouter`) unchanged.
- `Product001IntakeSpecEditor`, SVG/vector pathway, CostEngine, pricing untouched.

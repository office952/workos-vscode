# Figma-ready structure — Product System authoring (co-design)

| Field | Value |
|-------|--------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Date | 2026-07-20 |
| Rule | **Do not invent FINAL frame IDs.** Existing Intake frames are authority for operator runtime. PS authoring frames below are proposed structure for designer write — implement UI against contract freeze now. |

## Existing Intake frames (verified via MCP)

| Frame | Node ID | Role |
|-------|---------|------|
| FINAL — Confirmare 1440×900 | `66:2` | Operator confirm; checkbox → ConfirmJobProductTruth |
| Configurare | `64:2` | Config |
| Iluminare | `65:2` | Lighting |
| Montaj | `65:106` | Mounting |
| PinFooter | `67:18` | Sticky footer pattern (handoff / continue) |

## Proposed Product System authoring frames (NOT FINAL — no invented IDs)

Create under a new page e.g. `PS — Authoring Studio` (designer assigns IDs):

1. **PS Template Authoring Shell** — tabs: Overview / Composition / Components / Contracts / Materials / Dossier / Runtime preview / E2E Readiness / Version & publication  
2. **Component Contract + Used-by** — child/dual-role PT, usage_mode, instance_schema_id  
3. **Blueprint Dossier Studio split** — tree + editor + validation/readiness rail + sticky save/validate/check/publish  
4. **Publication states** — DRAFT / VALIDATED / E2E_CHECKED / PUBLISHED / DEPRECATED / ARCHIVED; badge `active ≠ published`  
5. **Readiness PASS / BLOCKED** — aluminiu inactive = honest BLOCKED, no fake PASS  

## UI implemented against contract (code)

| Surface | Route / component |
|---------|-------------------|
| Publication panel | `ProductTemplatePublicationPanel` on Product Template + Dossier Studio |
| Component contracts | `ComponentContractUsedByPanel` |
| E2E Readiness | `ProductE2EReadinessPanel` |
| Sticky footer | `blueprint-dossier-sticky-publish-footer` |
| Confirmare wiring | existing `useIntakeV6FinalHandoff` → confirm-job |

## Pattern reuse from PinFooter `67:18`

Sticky bottom bar: status text left + primary CTA right; dark `#111827` / border `#2a364a`.

# Intake Readiness Stages

Display-only staged readiness for Work Intake → Quote flow. **Does not change** CostEngine, pricing, backend `ready_for_quote` semantics, or quote/order creation policy.

## Stages

| Stage ID | Label (RO) | Purpose | Blocks |
|----------|------------|---------|--------|
| `stage0_unresolved` | Intake nerezolvat | Capture context; choose work type | Product form, simulation, commercial quote |
| `stage1_spec` | Specificație începută | Complete quote-critical spec fields | Simulation until minimum inputs exist |
| `stage2_simulation` | Gata pentru simulare | Preliminary cost preview | Commercial quote until commercial gates met |
| `stage3_commercial_quote` | Gata pentru ofertă comercială | Draft/send commercial offer | Production handoff until production details |
| `stage4_production` | Gata pentru producție | Order/production handoff | — |

**Working stage** = first incomplete stage. **Current stage** = highest achieved (or legacy `ready_for_quote` → commercial).

## `ready_for_quote` compatibility

- Backend / intake status `ready_for_quote` remains the **legacy commercial flag** (“Gata pt. Ofertă”).
- UI button **Marchează Gata pt. Ofertă** still uses `evaluateIntakeReadyPrerequisites()` — unchanged policy.
- Preliminary simulation may be available at **stage 2** before commercial gates pass.
- Staged panel clarifies: simulation ≠ commercial quote ≠ production.

## Simulation vs commercial vs production

| Concern | Simulation | Commercial quote | Production |
|---------|--------------|------------------|------------|
| Envelope W×H×D | Required | Required | Required |
| Geometry metrics (area, perimeter, count) | Required (CostEngine) | Required | Required |
| PSU, paint tubes, face/mounting enums | Required for `volumetricQuoteInputStepValid` | Required | Required |
| Assignee, description, delivery | No | Yes (mark ready) | Yes |
| Terrain audit | No (unless CostEngine needs install cost now — not current) | Yes when delivery+install | Extended (access, verified photos) |
| Vector file / review | No for rough estimate | Yes (`missingForFinalQuote`) | Final verification |
| Oracal / RAL metadata | No | Yes when finish selected | Confirmed for production |
| CUI / fiscal | No | Business rule via mark-ready only if already in prerequisites | Order stage if required |

## TPL-VOLUMETRIC-LETTERS rules

Source of truth for simulation inputs: `volumetricQuoteInputStepValid` + `buildVolumetricQuotePrepSummary` + `isSimulateInputReady`.

### Simulation blockers

- Template confirmed (`TPL-VOLUMETRIC-LETTERS`)
- `width_mm`, `height_mm`, `depth_mm` / `return_depth_mm` envelope
- `letter_face_area_m2`, `letter_perimeter_m`, `letter_count`
- `return_depth_mm` (30/60/80/100)
- `selected_psu_watts`, `paint_tube_count`
- Face finish / mounting enums (defaults applied in quote flow state)

### Commercial quote blockers (additive to mark-ready)

- All `evaluateIntakeReadyPrerequisites` items
- `missingForFinalQuote` from `volumetricIntakeFormPrep.ts` (vector, Oracal, RAL, ACM template, etc.)
- Terrain audit when `requiresInstallAudit`

### Production blockers (informational)

- Final vector verification
- Oracal/RAL confirmations when applicable
- Site access + verified location photos when install delivery

### SVG geometry parser

- Suggested width/height do **not** auto-complete simulation readiness.
- Perimeter/area remain simulation blockers until operator applies/confirms.
- `vector_suggested_*` fields are never auto-promoted to costing metrics.

## Implementation

Central helper: `frontend/src/lib/intakeReadinessStages.ts`

Exports:

- `buildIntakeReadinessStages()`
- `evaluateSimulationReadiness()`
- `evaluateCommercialQuoteReadiness()`
- `evaluateProductionReadiness()`
- `groupMissingReasonsByStage()`
- `getStageLabel()` / `getStageDescription()`

UI consumers:

- `ReadinessGatePanel` — staged groups + simulation hint
- `IntakeActionSummary` — staged missing summary
- `TemplateStatusPanel` — active stage label
- `VolumetricLettersQuoteFlow` — simulate button gated by `isSimulateInputReady` only

## Non-goals

- No pricing / CostEngine changes
- No quote or order creation
- No Reference Catalogs
- No new templates
- No incompatible `product_spec_json` changes
- No bypass of real blockers or fake completed fields

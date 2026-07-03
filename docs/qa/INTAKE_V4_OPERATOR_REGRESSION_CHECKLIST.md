# Intake V4 Operator Regression Checklist

## Purpose

This document is the working memory for the Intake V4 volumetric letters operator flow.
Before any future change in this area, inspect this checklist. After the change, verify that the prior fixes still hold.

Scope: `TPL-VOLUMETRIC-LETTERS`, Intake V4 operator/review/confirm flow, SVG vector analysis, finish setup, cant/volum, LED, template options, material/pricing previews.

## Working Rule From Now On

- Before implementing a new request, read this file and identify which protected behaviors may be affected.
- Keep the change narrow. Do not refactor unrelated ProductSystem, Pricing, CostEngine, Inventory, QuoteWizard, or legacy WorkIntake areas unless explicitly asked.
- After implementing, run targeted tests for the touched area plus the regression tests listed here.
- If UI text/behavior changes, manually smoke the live operator screen when the stack is running.
- In the final summary, mention which protected behaviors were checked and which commands were run.

## Completed / Protected Behaviors

### SVG and Geometry

- SVG import for Intake V4 operator was audited with the real `gradi-curat.svg` workflow.
- Vector elements must not be skipped. All vector artwork/logo/emblem paths must be classified, surfaced, or explicitly handled.
- Corel reference perimeter target for the real file was documented as `3163.8198 cm` / `31.638198 m`.
- Logo/emblem vector perimeters are part of the job truth when they are vector objects; they must not disappear from geometry or cant review.
- Mounting template area must cover the full graphic footprint, not only selected letter pieces.
- `Arie sablon montaj` is a square-meter value and should be displayed with `m2`/`m²` semantics.

### Cant / Volum

- `Perimetru cant total` is the real/canonical job perimeter, not the priced quantity with waste.
- `Cant pentru pret` is separate from real perimeter and may include waste.
- Cant/volum supports mixed layer depths such as `60`, `80`, and future `100` mm.
- Cant/volum summaries must show distribution by layer/group, depth, finish, and scope where relevant.
- The cant card and confirm summary must not show contradictory totals, for example a header total that differs from the depth distribution total.
- If backend material rows split cant into `return_material` plus `artwork_return_*`, Review and Confirm must display the summed real perimeter. For `gradi-curat.svg`, this is `31.638 m`, while priced cant with waste is separate.
- Live `Calcul live` must include artwork/logo cant costs in `Cant`; for the current `gradi-curat.svg` audit this produces `113.90 EUR` and `Materiale folosite > Cant / volum` shows `31.64 m`.
- `Finish / Material` in confirm is the granular source of truth; do not add duplicate vague tables.
- Per-layer finish rows should show letter layers and artwork/logo layers clearly.
- Main operator/confirm summaries must not display `Goluri / interioare`; holes remain calculation-only for perimeter/CNC/material logic.
- Confirm summary must show `Litere volumetrice` and `Embleme / logo` with lighting status where available.

### Finishes and Roll Widths

- Oracal face finishes `641`, `651`, and `8500` default to `1000 mm` roll width.
- Persisted payloads must also receive that roll width default; it is not only a visual dropdown default.
- Operator-selected roll width must be preserved if it is valid.
- Live `Materiale folosite` must split Oracal face vinyl by series, for example `Oracal 651` and `Oracal 8500`, instead of collapsing mixed series into one vague `Oracal` row.
- Oracal used for cant/volum must remain separate from face vinyl rows, for example `Oracal 651 / cant volum`.
- Live `Calcul live` must use one detailed ledger table, not a vague upper aggregate plus a second material list.
- Live `Calcul live` must show separate rows for `Plexiglas 3 mm / față litere` and `Plexiglas 3 mm / embleme/logo` when both letter and emblem areas are known.
- Live `Calcul live` must expose CNC and print service operation prices from backend `operation_rows`; missing edge operation rates must remain visible as `tarif lipsă`.
- At 1280x720 viewport, the Review live calculation panel must show `Material / Consum / Preț` without hiding the price column or creating horizontal page overflow.
- `print transparent` and `print translucent` selections must persist after autosave/autoconfirm.
- `logo stanga` and `logo dreapta` default to `Translucent`; `Transparent` remains optional but not default.
- Confirm summary `Print / Laminare` must say `present` when artwork execution is decided. It may say `pending artwork decision` only while an actual `needs_decision`/warning exists.
- Finish audit scope included colant, vopsit RAL, colantare plexiglas, colantare cant, and vopsire.
- RAL spray material is calculated from painted cant only: `ceil(painted_return_m / 15 m per tub)`.
- Owner RAL spray price reference is `50 RON/tub`; V4 uses the existing owner-confirmed registry equivalent of `10 EUR/tub`.
- `Materiale folosite` must show `Vopsea RAL spray / cant volum` as a separate material row, not merged into cant profile or Oracal.
- Mixed cant finishes must not force global `volume_finish=paint_after_face_miter_bond`; that global flag is allowed only when all active letter returns are RAL painted.
- `Lipire cant / volum` operation is owner-priced at `5 EUR/ml`, calculated from total graphic/cant perimeter (`return_material_perimeter_ml`), not from client-offered total and not only from letter-only perimeter.

### Diacritics / Encoding

- Intake V4 operator-facing UI must not display mojibake such as `Ã`, `Ä`, `È`, `Â`, `â€`, or replacement characters.
- Backend JSON for the Intake V4 workspace and material breakdown must preserve UTF-8 strings.
- Main Intake V4 operator text should use Romanian diacritics for visible labels where Romanian wording is used.
- PowerShell table output may display UTF-8 as mojibake; verify real data with Node/fetch or browser DOM before treating it as persisted corruption.

### Print, Lamination, and Consumables

- Print material price target discussed: `1.5 EUR`.
- Print service price target discussed: `8.5 EUR`.
- Lamination price target discussed: `5 EUR`.
- These are plus TVA where applicable.
- Consumables to keep coherent: cables, adhesive, mounting accessories/connectors.
- Mounting accessories/connectors policy: `5%` of internal fabrication/confection costs, without commercial markup and not calculated from the client-offered total.

### LED and Lighting

- LED must be visible and hard to miss in the UI.
- LED should be enabled by default for this volumetric letters template.
- LED module default is `0.75 W`.
- Light color default is `neutral`.
- Letter LED calculation and emblem/logo LED calculation are separate concerns.
- Letter LED may use its own line/perimeter logic.
- Emblem/logo LED modules are calculated from area/placement rules, not from the same letter perimeter formula.
- Emblem/logo illumination is active by default and Review shows only the real choices: luminous by area or non-luminous.
- LED strip keeps continuous-line logic; module placement is separate.
- Operator-facing LED/emblem UI text must not use confusing `outbox` wording; use emblem area / illumination status language.
- Existing emblem module rule recorded:
  - module size: `7.5 cm x 1.5 cm`;
  - for `60 mm` cant/volum: `4 cm` spacing on line, `8 cm` spacing on columns;
  - for `80 mm`: add `2 cm` to distances;
  - for `100 mm`: add another `2 cm`;
  - distance to edge must not exceed `7 cm`;
  - rules must be configuration-ready for future larger distances/lightboxes, not buried as UI-only magic.

### Template and ProductSystem Dominance

- ProductSystem/template rules must dictate the form, not ad hoc hardcoded UI that contradicts the template.
- Template-owned options must remain aligned with `TPL-VOLUMETRIC-LETTERS`.
- For `TPL-VOLUMETRIC-LETTERS`, `Spate litere` is always present; `Fara spate` must not appear as a Review option.
- Default backing is `Forex 10 mm fara sanfren`.
- `Sanfren spate Forex` is not a separate duplicate checkbox. Back bevel is represented only by the backing mode: `fara sanfren` vs `cu sanfren`.
- Mounting template, backing, LED, cant, and finish fields should be derived from template/product policy where possible.
- Any future ProductSystem alignment change must check confirm, review, material breakdown, and handoff behavior together.

### Autosave / Confirmation Flow

- Manual `Salveaza draft` and `Confirma finisaje` buttons were removed from Review.
- Finish setup autosaves/autoconfirms after each relevant form change.
- Preview/material prices should refresh from the persisted workspace after autosave.
- Old unconfirmed finish setups should become pending-save and be autosaved to confirmed state.
- Autosave must guard against stale server responses overwriting newer local edits.

### Quote Handoff / Confirm

- Confirm handoff must not create a circular blocker: when `operator_confirmation_missing` blocks handoff, the internal draft confirmation checkbox must remain enabled if finish setup and ProductSystem binding are otherwise valid.
- Review warnings for vector/artwork should be stated as review warnings, not as false generic claims that print/lamination is undecided.

### Current Runtime Expectations

- Backend port: `127.0.0.1:8000`.
- Frontend port: `127.0.0.1:3000`.
- Frontend route commonly used for operator checks: `/intake-v4/.../operator` or `/dashboard`.
- `validate:frontend` is not the repo truth gate because existing TS debt is documented in `AGENTS.md`.

## Pending Requests Not Yet Implemented

- No collected pending requests in this checklist at the time of the latest repair batch.

## Regression Test Set

Run the narrowest relevant subset for the change. For most Intake V4 review/confirm work, start with:

```powershell
cd frontend
npm.cmd test -- src/lib/intakeV4/intakeV4FaceFinishOptions.test.ts src/lib/intakeV4/intakeV4LetterGroups.test.ts src/lib/intakeV4/intakeV4FinishPayloadSync.test.ts src/lib/intakeV4/intakeV4FinishHydration.test.ts src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts src/lib/intakeV4/intakeV4ConfirmSummary.test.ts src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.test.tsx src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.test.tsx src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx
```

For geometry/analyzer/perimeter changes, add:

```powershell
cd frontend
npm.cmd test -- src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts src/lib/intakeV4/intakeV4QuoteGeometry.test.ts src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx src/components/workos/intake-v4/IntakeV4GeometryPanel.test.tsx
```

For LED changes, add:

```powershell
cd frontend
npm.cmd test -- src/lib/intakeV4/intakeV4FinishLighting.test.ts src/lib/intakeV4/intakeV4LedLighting.test.ts
```

For backing/emblem/default control changes, add:

```powershell
cd frontend
npm.cmd test -- src/components/workos/intake-v4/IntakeV4BackingAndEmblemSection.test.tsx src/components/workos/intake-v4/IntakeV4ReviewBackingSelect.test.tsx
```

Build check for frontend changes:

```powershell
cd frontend
npm.cmd run build
```

Known caveat: Vite may emit existing CSS/chunk warnings. Do not report build as failed unless the command exits non-zero.

## Manual Smoke Checklist

- Import or open the real Intake V4 operator workspace.
- Confirm header geometry/perimeter and cant card perimeter use the same canonical value.
- Confirm cant distribution rows do not sum to a conflicting number.
- Change one face finish to Oracal `651`; roll width should be `1000 mm`.
- Change artwork/logo `Translucent` or `Transparent`; wait for autosave; selection must persist.
- Change cant depth on separate layers; summary must show separate depth groups.
- Confirm `Finish / Material` has granular layer rows without duplicated vague summary rows.
- Confirm LED section defaults and visibility after any lighting change.
- Confirm template options do not contradict ProductSystem rules.
- Confirm mixed Oracal face finishes show separate `Materiale folosite` rows per series.
- Confirm rendered Intake V4 text has no mojibake and no obvious Romanian labels missing diacritics.

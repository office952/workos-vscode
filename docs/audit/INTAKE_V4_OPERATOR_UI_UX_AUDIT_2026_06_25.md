# Intake V4 Operator UI/UX Audit - 2026-06-25

Scope: `TPL-VOLUMETRIC-LETTERS`, workspace `9fe22974-1f65-4bce-847d-02d74bb16e05`, file `gradi-curat.svg`, operator flow steps 1/2/3.

## Verified Truth Signals

- The real file is loaded in the operator workspace: `gradi-curat.svg`.
- Total vector perimeter is preserved in the header and confirm surfaces: `31.638 m` / `31.64 m`.
- Step 3 no longer exposes `Goluri / interioare` in the operator summary.
- `Spate litere` does not expose `Fără spate`.
- No mojibake was detected in the browser DOM during live checks.
- Live calculation now separates `Oracal 651`, `Oracal 8500`, and `Oracal 651 / cant volum`.
- Live calculation now exposes CNC operation prices from backend `operation_rows`.
- Live calculation now separates `Plexiglas 3 mm / față litere` from `Plexiglas 3 mm / embleme/logo`.
- Confirm handoff no longer has a circular blocker: operator internal confirmation is enabled when the missing confirmation itself blocks handoff.

## Step 1 - Layers / SVG Analyzer

What works:

- The file status, dimensions, layer count, and vector perimeter are visible early.
- All six layers are confirmed and roles are persisted.
- The current screen correctly avoids showing holes as business-facing summary data.

Problems:

- The layer role table is too verbose because each layer visually repeats the entire role option vocabulary.
- The operator has no strong visual map showing which layer is a letter group and which layer is artwork/logo.
- Labels mix operator language with implementation language: `SVG Analyzer`, `Pseudo-layer`, `Kind`, `Auto`, `State`.
- The instruction text still talks about implementation details such as analyzer/motor behavior instead of production decisions.

Recommended direction:

- Replace repeated role dropdown text with one compact row per layer: color swatch, layer name, detected type, chosen production role, status.
- Add a vector preview / layer map next to the table.
- Surface only exceptions: unclassified, low confidence, missing artwork file, missing production method.

## Step 2 - Review / Finish Setup

What works:

- ProductSystem/template rules dominate more than before: backing, LED, cant, template area, and material choices are aligned.
- LED defaults and emblem lighting are visible and active.
- The live calculation panel is now useful because it shows quantity and price per material/operation.

Problems:

- The left form still becomes tall and repetitive when multiple letter groups and emblem layers exist.
- Operator attention is split between geometry, finish rows, template options, LED, cant details, and live pricing.
- The bottom toast can cover the lower action area at 720px viewport height.
- Some copy is still mixed Romanian/English (`Review`, `Confirm`, `Load SVG`, `Quote handoff`).

Recommended direction:

- Keep a persistent job truth strip at top: dimensions, total perimeter, template, status.
- Use a three-column workbench: layer/group list, selected group editor, live calculation ledger.
- Show repeated group settings as a matrix with inline overrides instead of full stacked cards.
- Keep `Calcul live` always visible and wide enough for `Material / Consum / Preț`.

## Step 3 - Confirm / Handoff

What works:

- Confirm summary distinguishes `Litere volumetrice` and `Embleme / logo`.
- Finish/material rows are granular enough to audit face/cant/artwork choices.
- Review warnings now state vector/artwork attention explicitly instead of implying print/lamination is undecided.

Problems:

- Handoff information is structurally mixed: fatal blockers, review warnings, policy confirmations, and quote creation live in one block.
- The operator needs a clear checklist of what can be resolved now vs. what remains a review warning.
- The "quote handoff" section still feels more technical than operational.

Recommended direction:

- Split handoff into three lanes: `Rezolvă acum`, `Atenționări review`, `Acțiuni blocate`.
- Keep operator confirmation active when it is the blocker being resolved.
- Use Romanian labels consistently for user-facing controls.

## Proposed Prototype

Standalone HTML mockup:

`docs/mockups/intake-v4-operator-flow-proposal.html`

The mockup uses the same real job signals from this audit and proposes:

- a persistent top job truth strip;
- a layer map + compact layer classification table for Step 1;
- a focused finish matrix + live cost ledger for Step 2;
- a gate/checklist handoff layout for Step 3.

This is a design artifact only. It does not mutate the app or backend.

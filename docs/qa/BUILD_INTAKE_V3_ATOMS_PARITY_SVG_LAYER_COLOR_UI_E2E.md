# BUILD_INTAKE_V3_ATOMS_PARITY_SVG_LAYER_COLOR_UI_E2E

**Date:** 2026-06-19  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** Operator Workspace SVG layer/color/font evidence + 3-step UI parity — no CostEngine, Inventory, tasks, PO.

---

## Context

Audit E2E Atoms vs V2/V3 identified that V3 built production layer truth exclusively from path-only `path_geometry_summary`, dropping polygon/rect layers, color evidence, fill subgroups, and readable UI swatches.

Fixture: `tmp/atoms-export/uploads/pbl-color.svg` (CorelDRAW 2020, 3 layers: Cadru, Litere_x0020_volumetrice, Emblema).

---

## Root cause

`build_layer_path_geometry_from_svg_text` collected only `<path>` inside any group (including `<defs>`), while layer role draft used that list exclusively. Emblema (510 polygons) and Cadru (10 rects) never entered operator layer snapshot.

---

## Backend implemented

| Area | Change |
|------|--------|
| `intake_v3_svg_drawable_layer_summary.py` | New drawable analyzer: path/polygon/rect/circle/ellipse/text per layer; skip defs/clipPath/metadata; color extraction (fill/stroke/style/inherited); fill subgroups; font evidence |
| `intake_v3_svg_layer_path_geometry.py` | Merge drawable summary + path metrics; exclude defs from path walk |
| `intake_v3_layer_role_confirmation_service.py` | Enhanced auto-role (reference, printed_artwork, face); persist color/font evidence on layers |
| `schemas/intake_v3.py` | `IntakeV3LayerColorEvidence`, `IntakeV3LayerFontEvidence`, extended metrics |

### pbl-color PASS criteria (backend)

- 3 layers: Cadru, Litere_x0020_volumetrice, Emblema
- Cadru: 10 rects, stroke #2B2A29, auto_role `reference`
- Litere: 2 paths, fill groups #E31E24 / #393185, auto_role `face`
- Emblema: 510 polygons, multicolor, auto_role `printed_artwork`
- No defs/clipPath layer
- Font: `converted_to_paths`, no fake font-family

---

## Frontend implemented

| Area | Change |
|------|--------|
| `layerRoleConfirmationContracts.ts` | color_evidence, font_evidence types |
| `operatorWorkspaceHelpers.ts` | element summary, swatches, fill groups, font notes |
| `operatorWorkspaceThreeStepViewModel.ts` | layersStep fields + workspaceFontNote |
| `OperatorWorkspaceLayerCard.tsx` | Swatches, multicolor badge, element summary, font note |
| `OperatorWorkspaceLayersStep.tsx` | Layer cards list + workspace font banner |
| `operatorWorkspacePresentation.tsx` | Typography tokens 11–14px (Atoms-aligned readability) |
| three-step components | Removed 7–10px operational text |

### V2 logic adapted

- Fill subgroup grouping from `svgLetterGroups.ts` / `deriveGroupsFromFill` concept → backend `fill_groups` in color evidence
- `ColorRegistrySelect` remains in layer setup (existing wiring); cards show detected SVG colors first

### Atoms visual discipline kept

- Dark cards, clear hierarchy, swatches 16px, layer names 14px, evidence 12px
- 3-step flow dominant; legacy tabs collapsed

### Rejected from Atoms (not ported)

- Mock scenario hardcoded stats, voice/copilot, confetti, LED strip demo

---

## Tests

### Backend

```powershell
cd backend
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_svg_layer_path_geometry.py -q
```

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV3/operatorWorkspaceThreeStepViewModel.test.ts `
  src/pages/IntakeV3OperatorWorkspaceApp.test.tsx `
  src/components/workos/intake-v3/operator-workspace/three-step/operatorWorkspaceTypography.test.ts
```

---

## Runtime E2E

1. Start stack: `npm run dev:stack`
2. Open `/intake-v3/e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf/operator`
3. Upload `tmp/atoms-export/uploads/pbl-color.svg`
4. Verify: 3 layer cards/chips, red/blue swatches on Litere, multicolor Emblema, Cadru reference, font note, Review/Confirm OK

---

## PASS/FAIL

| PASS | FAIL |
|------|------|
| 3 operator layers on pbl-color | ≤2 layers or missing Emblema/Cadru |
| Fill swatches #E31E24 / #393185 | Single aggregated letter layer only |
| Emblema printed_artwork + multicolor | Forced volumetric Oracal |
| UI readable without zoom (≥12px body) | 7–10px operational text |
| Targeted pytest + vitest green | Missing pbl-color tests |

---

## Partea a doua (backlog)

- Per-subgroup finish confirmation as production truth
- Inventory automation, ExecutionTask/Plan, PO/SupplierOrder
- Font recovery beyond path conversion
- Full ColorRegistry inline per card (beyond current layer setup wiring)

---

## Boundary confirmations

- No commit / no push (this build)
- No CostEngine / Inventory / StockMovement / ExecutionTask / PO
- No parser security weakening
- No reserve/PSU allocator changes
- `tmp/` and `backend/dev.db` not committed
- SVG fixture not committed

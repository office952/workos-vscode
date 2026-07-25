# Letters face material display lock — plexiglas 3mm PMMA - opal

**Date:** 2026-07-23  
**Status:** Applied (display/name only — codes unchanged)

## Owner lock

Exact operator-facing name for letter-face stock:

`plexiglas 3mm PMMA - opal`

Stable registry code remains `MAT-ACP-FATA-LITERE` (legacy “ACP” in code only — not ACM/Bond panel).

## Canonical constants

| Layer | Location |
|-------|----------|
| Backend | `backend/seeds/material_canonical_naming.py` → `LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME` |
| Frontend | `frontend/src/lib/materials/lettersFacePlexiMaterialDisplay.ts` |

## Surfaces aligned

- Inventory seeds / owner price seed name patch
- Intake V4/V5/V6 material breakdown & live calc labels
- Gradi logical list face material line
- Shared CNC face cutting/bevel material_name + display_name
- Product System FACE process strip + estimate drafts
- Frontend material naming catalog
- Structure subtitle override: `Vizual față — plexiglas 3mm PMMA - opal` (no more «plexi/acrilic»)
- Template seed `comp_face_litere` name + dossier/output-block copy for Letters
- Product System catalog description / TemplateGeneral / production guidance

## Out of scope

- Code rename / CostEngine formula identity change
- Vinyl/print FINISH names
- Other plexi thicknesses (5 mm / 10 mm variants stay separate)

## Live DB

Re-run owner confirmed prices seed so existing `MAT-ACP-FATA-LITERE` rows pick up the locked `name` (seed skips only when price **and** name already match).

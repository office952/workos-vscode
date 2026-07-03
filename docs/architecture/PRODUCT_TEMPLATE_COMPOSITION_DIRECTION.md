# Product Template Composition Direction

**Status:** Accepted direction / implementation not fully built  
**Date:** 2026-06-09  
**Layer:** Architecture & business direction (documentation only)  
**Audience:** Product owner, Cursor agents, developers  
**Responsibility:** Defines how WorkOS ProductSystem templates compose for intake, costing, and quotes — without changing runtime behaviour in this document.

**Related (read-only context):**

- `docs/architecture/TPL_VOLUMETRIC_LETTERS_MOUNTING_STRUCTURE_BOUNDARY.md` — mounting bridge vs future structure template (uses legacy name `TPL-STRUCTURA-LITERE` in places)
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` — what letters CostEngine calculates today
- `docs/architecture/VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md` — V2 handoff vs QuoteWizard
- `frontend/src/lib/svgGeometryLayerRoles.ts` — letter vs support/frame geometry buckets (runtime guard, partial)
- `docs/architecture/SVG_FINISH_ASSIGNMENT_AND_LETTER_GROUPS_DIRECTION.md` — per-group face/return finishes inside a letters layer (multicolor SVG)

### Three direction layers (orthogonal)

| Layer | Document | Question answered |
|-------|----------|-------------------|
| **Template composition** | This document | Which ProductSystem template owns letters, bars, ACM, services? |
| **Layer semantic mapping** | Planned: SVG Layer Semantic Mapping Direction | What role does each SVG layer play (letters vs frame vs emblem)? |
| **Finish assignment** | `SVG_FINISH_ASSIGNMENT_AND_LETTER_GROUPS_DIRECTION.md` | How are subgroups inside a letters layer executed (face, cant, backing, materials)? |

Layer role mapping alone is **not** sufficient for colour/material — finish assignment resolves that inside `TPL-VOLUMETRIC-LETTERS`.

---

## Scope

This document locks the **correct decomposition** of sign products into ProductSystem templates in WorkOS:

- **One template = one product responsibility**, not a monolith that silently absorbs letters, support bars, ACM panels, mounting labour, and transport.
- **Final commercial offers may compose multiple templates/modules** when the job requires them.
- **SVG analysis may yield separate metrics** for letters, support/frame, and assembly; each metric stream must map to the correct future template — never into letter perimeter/area by default.

This is a **direction lock**. It does not activate new templates, CostEngine paths, DB fields, or quote pricing rules.

---

## Non-goals

This document and the build that introduces it **do not**:

- implement `TPL-SUPPORT-BARS`, `TPL-METAL-SUPPORT-STRUCTURE`, or `TPL-ACM-CASSETTED-PANEL` end-to-end;
- modify CostEngine formulas or `QuoteOrchestrator` commercial rules;
- change database schema, migrations, or `product_templates` activation for experimental templates;
- change quote/document/PDF output composition;
- change Material Registry or Inventory;
- implement full SVG semantic layer mapping or multi-template quote runtime;
- remove the existing **temporary mounting bridge** inside `TPL-VOLUMETRIC-LETTERS` (`steel_bars` / `aluminum_bars` / `acm_panel` enum + simplified premount costing) — that bridge is documented elsewhere and must shrink over time, not expand.

---

## Core decision

**`TPL-VOLUMETRIC-LETTERS` remains dedicated exclusively to volumetric channel letters.**

It must **not** become the canonical home for:

- metal support bars or welded frames;
- ACM / Dibond / Alucobond casetted panels;
- structural labour (cut, weld, assembly of support);
- panel casetting, V-groove, panel frame carpentry;
- transport or site installation as a full product line.

Those concerns belong to **separate templates** (below) and to **future quote composition**, not to letter geometry or letter CostEngine inputs.

---

## Composition model

A real job may combine modules. Example composition (logical, not yet a runtime orchestrator):

```
Job offer (future)
├── TPL-VOLUMETRIC-LETTERS          (required when job includes 3D letters)
├── TPL-SUPPORT-BARS                (optional — premount / frame bars)
│   └── alt. code: TPL-METAL-SUPPORT-STRUCTURE
├── TPL-ACM-CASSETTED-PANEL         (optional — casetted ACM backing panel)
├── Installation / mounting service (optional — site labour)
└── Transport / logistics           (optional)
```

**Mounting context rule:** Letters can be installed in multiple ways (direct wall, on bars, on ACM panel, future supports). The **installation method** informs which **optional modules** are included in the offer; it does not justify merging bar/panel costing into the letters template.

---

## Template responsibility table

| Template / module | Responsibility | Primary inputs | Must not calculate | Future status |
|-------------------|----------------|----------------|--------------------|---------------|
| **`TPL-VOLUMETRIC-LETTERS`** | Letter faces (plexi), return/cant, letter backing, LED modules/strips, PSU for letters, CNC per letter, chamfer, edge bonding, per-letter wiring, letter spacers/fasteners, letter finishes (RAL / Oracal / vinyl) | `letter_perimeter_m`, `letter_face_area_m2`, `letter_count`, `return_depth_mm`, illumination, face/return finish, `mounting_system` *selection only* | Bar ml from SVG rectangles; frame weld labour; ACM panel area/casetting; structural paint; merging support layer perimeter into `letter_perimeter_m` | **Active** — sole fully wired V2 + quote template today |
| **`TPL-SUPPORT-BARS`** (proposed) / **`TPL-METAL-SUPPORT-STRUCTURE`** (alt.) | Support profiles (steel/aluminium), bar length, cut, weld/assembly, structural paint, fasteners, structural mount labour; relationship to letters without absorbing letter metrics | Profile type & dimensions, total bar length, bar count, material, finish; future: `vector_suggested_support_*` / frame metrics from SVG | Letter perimeter, letter face area, LED, letter CNC, letter return depth | **Not built** — seeds/docs may reference `TPL-STRUCTURA-LITERE` as earlier name |
| **`TPL-ACM-CASSETTED-PANEL`** | ACM sheet (3/4 mm), panel area, casetting depth, rear lip, V-groove, bends, inner frame, panel fixings, optional panel graphic/vinyl, panel mount labour | Panel width/height, depth, ACM thickness, area; future: support_panel SVG metrics | Letter count/perimeter; bar profile costing; letter LED | **Seeded / inactive** — not operator-activated in WorkIntake V2 or QuoteWizard |
| **Installation / mounting service** | Site install labour, anchors, lift/access, method-specific fixings at wall | Terrain audit, access, height, method | Material BOM for letters or structure (references other templates) | Partially captured in intake terrain; no dedicated template |
| **Transport service** | Delivery / logistics line | Distance, vehicle, handling | Production BOM | Intake `delivery_type` only; no template |

---

## `TPL-VOLUMETRIC-LETTERS` — in-scope vs out-of-scope

### In scope (letters product)

- Letter face graphics / plexiglass face
- Return (cant) aluminium, depth, finish
- Letter back / backing (Forex/PVC)
- LED system (modules/strips), colour, density
- PSU sizing/allocation **for letters**
- CNC, visual chamfer, edge bonding
- Per-letter cabling
- Letter-only spacers/fasteners
- Letter finishes: RAL paint tubes, Oracal/vinyl face options
- Letter geometry: perimeter, face area, letter count
- Operator choice of **mounting method** enum (context for which sibling templates apply)

### Out of scope (must not be absorbed)

- Metal support bars as a engineered product line
- Welded frames / structural metalwork
- ACM / Dibond / Alucobond **casetted panel** fabrication
- Inner panel frames, casetting, V-groove, panel bends
- Structural support painting / welding
- Using support/frame SVG metrics in `letter_perimeter_m` or `letter_face_area_m2`
- Treating red guide lines, notes, or non-production SVG layers as quote metrics

### Known temporary bridge (shrink, do not extend)

Today the letters template still includes a **simplified premount bar bridge** (`mounting_system` = `steel_bars` / `aluminum_bars`, heuristic bar ml). That is **not** the target architecture. New bar/frame capability must target **`TPL-SUPPORT-BARS`** (or `TPL-METAL-SUPPORT-STRUCTURE`), not new letter-template fields.

---

## SVG interpretation rule

After server SVG upload and layer analysis, WorkOS may persist **separate suggestion fields**:

| Metric stream | Example fields | Feeds |
|---------------|----------------|-------|
| Letters layer | `vector_suggested_letter_perimeter_m`, `vector_suggested_letter_face_area_m2`, `vector_suggested_letter_layer_width_mm`, `vector_suggested_letter_count` | **`TPL-VOLUMETRIC-LETTERS`** quote metrics only |
| Support / frame layer | `vector_suggested_support_width_mm`, `vector_suggested_frame_*`, `vector_suggested_support_area_m2` | **Future** `TPL-SUPPORT-BARS` / structure template — **candidate data only today** |
| Assembly envelope | `vector_suggested_assembly_width_mm`, `vector_suggested_assembly_height_mm` | Display / alignment; letter template may use letter-layer bbox, not support bbox |

**Hard rules:**

1. Support/frame metrics **must not** be merged into letter perimeter, face area, or letter count.
2. Unknown or unmapped layers require operator confirmation or safe ignore — no silent default to letters.
3. Red guide lines, notes, registration marks, and dimension guides **must not** enter quote metrics.
4. Full semantic layer mapping is a **future build**; until then, preserve separated server fields and apply only letter-stream fields to `TPL-VOLUMETRIC-LETTERS`.

Runtime helpers: `frontend/src/lib/svgGeometryLayerRoles.ts`, `backend/services/work_intake_svg_spec_mapper.py` (`_build_geometry_suggestion_fields`).

---

## Product examples

| Scenario | Templates in offer (future composition) | Letters template receives |
|----------|----------------------------------------|---------------------------|
| Letters direct on wall | `TPL-VOLUMETRIC-LETTERS` | Letter geometry + LED + finishes; `mounting_system = direct_wall` |
| Letters on steel/aluminium bars | `TPL-VOLUMETRIC-LETTERS` + `TPL-SUPPORT-BARS` | Letter metrics only; bar profile/length from structure template |
| Letters on ACM casetted panel | `TPL-VOLUMETRIC-LETTERS` + `TPL-ACM-CASSETTED-PANEL` | Letter metrics; panel area/casetting from ACM template |
| Letters on ACM panel + bars/frame | `TPL-VOLUMETRIC-LETTERS` + `TPL-ACM-CASSETTED-PANEL` + `TPL-SUPPORT-BARS` | Each module keeps its own inputs; no monolith template |

---

## What exists today (audit snapshot)

| Area | Exists? | Notes |
|------|---------|-------|
| `TPL-VOLUMETRIC-LETTERS` ProductSystem template | Yes | Backend seeds, CostEngine, dossier, WorkIntake V2 config, `VolumetricLettersQuoteFlow` |
| `TPL-ACM-CASSETTED-PANEL` template seed | Yes | Inactive for quote; SVG layer mapping tests; **not** V2 operator path |
| `TPL-SUPPORT-BARS` / structure template | No | Documented as `TPL-STRUCTURA-LITERE` in older boundary doc |
| Multi-template **quote** composition runtime | No | One `product_template` per quote price call today |
| Child template / optional module registry | No | No formal composition graph in DB |
| SVG layer → template mapping | Partial | `svg_layer_template_mapping.py`, analysis service; not full semantic confirmation UX |
| Letter vs support geometry separation | Partial | Server mapper + `svgGeometryLayerRoles.ts` + `mergeServerSvgGeometrySuggestionsIntoSpec` (letters only to quote metrics) |
| Quote output composition preview | Yes | `QuoteOutputCompositionService` — **document/display** preview for one quote, not multi-template BOM |
| Workspace module composition | Yes | UI layout modules only (`TEMPLATE_INTAKE_WORKSPACE_MODULES.md`) — not product template composition |

---

## Future build candidates

Execute as **separate bounded builds** after this direction lock:

1. **SVG Layer Semantic Mapping** — operator-confirmed roles, unknown-layer policy, guide-line exclusion.
2. **SVG Finish Assignment & Visual Letter Groups** — per-group face/return/backing; see `SVG_FINISH_ASSIGNMENT_AND_LETTER_GROUPS_DIRECTION.md`.
3. **`TPL-SUPPORT-BARS` Foundation** (or `TPL-METAL-SUPPORT-STRUCTURE`) — dossier, quote_input, registry profiles, SVG bar length rules.
4. **`TPL-ACM-CASSETTED-PANEL` Foundation** — activate only with dedicated intake + CostEngine + tests.
5. **Quote Template Composition** — multi-template price snapshot, line items per module, single commercial offer header.
6. **Commercial Document Composition Display** — customer-facing breakdown by module without exposing internal CostEngine.

Until those builds ship, agents must **not** expand `TPL-VOLUMETRIC-LETTERS` to absorb support bars, ACM panels, or structural labour.

---

## Agent checklist (before changing templates)

- [ ] Does the change keep letter perimeter/area sourced only from letter layers?
- [ ] Does it avoid adding structural or ACM CostEngine logic to the letters template?
- [ ] If SVG metrics are used, are support/frame fields stored separately and excluded from letter quote_input?
- [ ] Is a new template activation explicitly tasked — not assumed from seeds?
- [ ] Are CostEngine, DB schema, and quote pricing formula untouched unless in a dedicated build?

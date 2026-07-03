# SVG Finish Assignment and Letter Groups Direction

**Status:** Accepted direction / implementation not fully built  
**Date:** 2026-06-09  
**Layer:** Architecture & business direction (documentation only)  
**Audience:** Product owner, Cursor agents, developers  
**Responsibility:** Defines how visual groups inside SVG letter layers map to production finishes and material quantities for `TPL-VOLUMETRIC-LETTERS` — without changing runtime behaviour in this document.

**Related direction documents:**

- `docs/architecture/PRODUCT_TEMPLATE_COMPOSITION_DIRECTION.md` — which template owns letters vs support vs ACM
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_MOUNTING_STRUCTURE_BOUNDARY.md` — structure vs letters boundary
- Planned companion: **SVG Layer Semantic Mapping Direction** — layer role assignment (letters vs frame vs emblem); role mapping alone does not solve per-color finish assignment

---

## Scope

Real-world SVG files often place **multiple production-relevant colours inside a single semantic letters layer**. WorkOS must eventually support:

- **letter groups / execution groups** derived from SVG visuals but **confirmed by the operator**;
- **component-level finishes** per group (face, return/cant/volume, backing);
- **material quantities** calculated per group and component (area, perimeter, count);
- **merge/split** decisions when two similar reds are not the same production material.

This document locks that model. It does not ship UI, CostEngine changes, or new persistence shapes.

---

## Non-goals

This document and its introducing build **do not**:

- implement a full finish-assignment UI;
- modify CostEngine formulas or material lines;
- change database schema or `product_spec_json` contract;
- change quote pricing formula or `QuoteOrchestrator`;
- activate new ProductSystem templates;
- modify SVG parser logic or path metrics extraction;
- auto-map every SVG fill to an Oracal catalogue code;
- generate commercial document / PDF finish breakdown;
- replace the existing **single global** face/return finish fields in WorkIntake V2 (they remain interim until a dedicated build).

---

## Core decision

A **single semantic SVG layer** (e.g. `Litere_x0020_volumetrice`) may contain **multiple visual letter groups**.

WorkOS must **not** assume:

- one Oracal colour per template;
- one Oracal colour per layer;
- that two close reds in SVG are automatically the same foil/material order;
- that an SVG `fill` hex is a confirmed production material without operator assignment.

**Confirmed production data** drives costing and material ordering — not raw SVG paint attributes alone.

---

## Conceptual model

### SVG Layer

Semantic container with a **role** (from future layer semantic mapping):

| Role (examples) | Purpose |
|-----------------|--------|
| `letters_geometry` / `volumetric_letters` | Letter shapes for `TPL-VOLUMETRIC-LETTERS` |
| `metal_frame` / `support` | Frame/bars — separate template, not letter groups |
| `support_panel` | ACM/panel — separate template |
| `emblem` / `artwork` | Multicolor logo — operator decision required |
| `guide` / `annotation` | Must not enter quote metrics |

### Letter Group / Execution Group

A **subgroup inside a letters layer**, usually **suggested** from SVG fill/stroke similarity but **confirmed** by the operator.

| Property | Meaning |
|----------|---------|
| `groupId` | Stable id within intake/spec |
| `sourceLayerName` | Parent SVG layer |
| `sourceFillColor` / `sourceStrokeColor` | Suggestion only (hex) |
| `elementIds` | SVG element references for highlight |
| `faceAreaM2`, `perimeterM`, `elementCount` | Metrics **for this group only** |
| `operatorStatus` | `suggested` \| `confirmed` \| `ignored` \| `merged` |

### Component Finish

Finish applied **per component** of a letter group, not one global finish for the whole job:

| Component | Examples |
|-----------|----------|
| **Face / front** | Oracal 651/641/8500, print+laminare, coloured plexi, translucent film, paint, none |
| **Return / cant / volume** | Standard aluminium stock (white/black), RAL paint, Oracal-wrapped return, painted aluminium |
| **Backing / spate** | Forex thickness, aluminium back, other — when relevant to costing |

### Material Assignment

Operator-confirmed mapping from group + component → **real material**:

- Oracal series + code + roll width;
- RAL code + paint system;
- print/laminate specification;
- aluminium return depth + finish system.

### Material Quantity

Computed **per group and component** for ordering and costing inputs:

| Component | Typical quantity basis |
|-----------|------------------------|
| Face / folie / print | Group `faceAreaM2` |
| Return / cant | Group `perimeterM` × depth |
| CNC / bonding / paint tubes | Group `elementCount` or perimeter rules (CostEngine build) |
| LED | May remain job-level or split per group in future — out of scope here |

---

## Required future UI behavior

For a confirmed letters layer (e.g. `Litere volumetrice`), the operator workspace must eventually show:

| UI element | Purpose |
|------------|---------|
| Group list | One row per letter group (colour swatch, hex, label) |
| Element count | How many paths/shapes in group |
| Estimated area / perimeter | From geometry split per group |
| Canvas highlight | Select group → highlight matching SVG elements |
| Face settings | Material type, Oracal/RAL/print, code, roll width |
| Return/cant settings | Depth, stock vs RAL vs Oracal wrap, colour |
| Backing settings | When applicable |
| Confirm / ignore / merge | Operator status per group |
| Merge/split tool | For close colours — see Close colour rule |

### Conceptual example (two groups, one layer)

**Group red (`#E31E24`):**

- Face: plexiglas 3 mm + Oracal red (code TBD by operator)
- Return: aluminium 0.6 mm, 60 mm, Oracal-wrapped red *or* white *or* RAL — operator choice
- Backing: Forex 10 mm
- Quantities: face m², perimeter m, count — **for red elements only**

**Group blue (`#393185`):**

- Face: plexiglas 3 mm + Oracal blue
- Return: aluminium 0.6 mm, 60 mm, finish **independent** of red group
- Backing: Forex 10 mm
- Quantities: separate from red group

---

## Close colour rule

Two similar reds (e.g. `#E31E24` and `#E02020`) must **not** auto-merge.

| Step | Behaviour |
|------|-----------|
| Suggestion | WorkOS may flag “similar colour” and propose merge candidate |
| Decision | Operator chooses: **merge** into one production finish **or** **keep separate** |
| Costing / ordering | Uses **confirmed** assignment only |
| SVG raw fill | Never authoritative for material SKU |

---

## Component-level finish rule

A colour group is **not** only “face colour”.

Each group may specify **independent** finishes:

| Combination | Valid? |
|-------------|--------|
| Red face + red return | Yes |
| Red face + white return | Yes |
| Blue face + black return | Yes |
| Print face + RAL return | Yes |
| Oracal face + standard aluminium return | Yes |
| Coloured plexi face + Oracal-wrapped return | Yes |

**Current interim model (today):** WorkIntake V2 uses **job-level** fields (`face_finish_type`, `face_vinyl_*`, `return_finish_system`, `return_color`, `paint_ral_code`, …) — sufficient for single-colour jobs only.

---

## Relationship with `TPL-VOLUMETRIC-LETTERS`

| Rule | Detail |
|------|--------|
| Template ownership | Letter groups and their component finishes belong to **`TPL-VOLUMETRIC-LETTERS`** |
| Geometry | Group metrics sum into letter template inputs only when confirmed; support/frame layers excluded |
| Return/cant | Part of the letter product — **may differ per group** |
| Support bars / ACM panel | **Not** letter groups — see `PRODUCT_TEMPLATE_COMPOSITION_DIRECTION.md` |
| CostEngine (future) | Must accept per-group inputs or aggregated confirmed totals — dedicated build |

---

## Relationship with SVG layer semantic mapping

Two orthogonal concerns:

```
SVG upload
  → Layer Semantic Mapping     (WHAT is this layer?)
       letters | frame | emblem | guide | panel
  → Finish Assignment          (HOW are letter subgroups executed?)
       groups inside letters layer → face + return + backing per group
```

**Example:** `Litere_x0020_volumetrice`

1. Semantic mapping → `letters_geometry`
2. Finish assignment → groups:
   - `#E31E24` red group → face + return assignments
   - `#393185` blue group → face + return assignments

Semantic mapping **does not** replace finish assignment.

---

## Reference case: `publi-cadru-fx.svg`

Real customer file (not necessarily in repo). Observed structure:

### Layer `Cadru`

| Observation | Direction |
|---------------|-----------|
| 10 rectangles, `fill: none`, `stroke: #2B2A29` | **Support/frame candidate** |
| Not letter geometry | Excluded from letter groups |
| Multiple traverses/bars | Future `TPL-SUPPORT-BARS` / structure template |
| Stroke colour | Reference only — not production finish for letters |

### Layer `Litere_x0020_volumetrice`

| Observation | Direction |
|---------------|-----------|
| 2 paths | One semantic letters layer |
| Fills `#E31E24` and `#393185` | **Two letter groups** minimum |
| Stroke `#2B2A29` | Outline reference — not auto Oracal |
| Required | Per-group face + return assignment |

### Layer `Litere`

| Observation | Direction |
|---------------|-----------|
| 2 paths, same fills as volumetric layer | **Ambiguous duplicate** |
| Operator must confirm | Display copy, print layer, secondary face, or ignore |
| Must not auto-merge | With `Litere_x0020_volumetrice` without explicit operator merge |

### Layer `Emblema`

| Observation | Direction |
|---------------|-----------|
| Many polygons, many colours | **Multicolor artwork** |
| Must not auto-split | Into dozens of Oracal groups |
| Operator decisions | Print+laminare, emblem production, separate template, or display-only / ignore |
| Not default letter groups | Unless operator maps to production |

---

## Foundation implementation (2026-06-09)

Runtime foundation (WorkIntake V2 only — not CostEngine):

- `frontend/src/lib/workIntakeV2/svgLetterGroups.ts` — derive groups from SVG fill on primary letters layer
- `product_spec_json` fields: `svgLetterGroups`, `letterGroupFinishAssignments`, `svgArtworkLayersPending`
- `V2LetterGroupFinishesSection` in production stage — per-group face + return/cant assignment UI
- Global finish fields remain fallback until CostEngine consumes per-group assignments

---

## What exists today (audit snapshot)

| Area | Exists? | Location / notes |
|------|---------|------------------|
| Global face finish | Yes | `face_finish_type`, `face_vinyl_*` on `IntakeProductSpec`; V2ProductionStage section „Față / folie” |
| Global return finish | Yes | `return_color`, `return_finish_system`, `return_ral_*`, `return_oracal_*`; V2 section „Cant / volum” |
| Global RAL (cant paint) | Yes | `paint_ral_code`, `paint_ral_name`, `volume_finish` |
| Quote input mapping | Yes | `volumetricQuoteInput.ts` — single set of finish fields → `quote_input` |
| Color registry (Oracal/RAL UI) | Yes | `frontend/src/lib/colorRegistry/` — picker for **one** face/return selection |
| SVG fill/stroke → groups | **No** | Parser extracts geometry metrics, not per-fill groups |
| `finish_groups` / `letter_groups` | **No** | No types or persistence |
| Per-group area/perimeter | **No** | Metrics are layer-level or job-level |
| Component finish per group | **No** | |
| Group highlight preview | **No** | Letter preview mocks exist; not SVG-group-aware |
| Quote snapshot finish breakdown | **No** | Snapshot stores job-level pricing + quote_input |
| Layer roles (partial) | Yes | `svgGeometryLayerRoles.ts`, `svgIntakeFlow.ts` — letter vs frame vs panel |

**Conclusion:** Current system supports **one global Oracal/RAL/finish path per intake** — insufficient for `publi-cadru-fx.svg` and similar production files.

---

## Suggested future data shape (conceptual only)

Not implemented. Illustrates intended persistence for a future build:

```ts
type SvgLetterGroup = {
  groupId: string;
  sourceLayerName: string;
  sourceFillColor?: string;
  sourceStrokeColor?: string;
  visualLabel: string;
  elementIds: string[];
  faceAreaM2?: number;
  perimeterM?: number;
  elementCount?: number;
  operatorStatus: "suggested" | "confirmed" | "ignored" | "merged";
};

type LetterComponentFinishAssignment = {
  groupId: string;
  face?: {
    materialType:
      | "oracal"
      | "print_laminate"
      | "colored_plexiglas"
      | "translucent_film"
      | "paint"
      | "none";
    materialCode?: string;
    colorCode?: string;
    colorName?: string;
  };
  returnCant?: {
    materialType:
      | "aluminum_return"
      | "painted_aluminum"
      | "oracal_wrapped_aluminum"
      | "standard_aluminum";
    depthMm?: number;
    materialCode?: string;
    colorCode?: string;
    colorName?: string;
  };
  backing?: {
    materialType?: "forex" | "aluminum" | "other";
    materialCode?: string;
    finishNotes?: string;
  };
  confirmedByOperator: boolean;
};
```

Aggregation into CostEngine `quote_input` is a **separate bounded build** (per-group lines vs rolled-up totals with audit trail).

---

## Future build candidates

Execute separately after this direction lock:

1. **SVG Layer Semantic Mapping Direction** (document + foundation)
2. **SVG Finish Assignment & Visual Letter Groups Foundation** — types, persistence sketch, server suggestions
3. **Letter Group Highlight Preview** — SVG canvas selection by group
4. **Component Finish Assignment UI** — face + return + backing per group
5. **Per Group Material Quantity Calculation** — split area/perimeter from paths by fill
6. **Quote Snapshot Finish Assignments** — immutable commercial record per group
7. **Commercial Document Finish Breakdown** — customer-facing lines by finish group
8. **Material Ordering by Confirmed Finish Group** — procurement view

---

## Agent checklist

- [ ] Does the change avoid treating one global `face_vinyl_code` as sufficient for multicolor SVGs?
- [ ] Are SVG fills treated as suggestions until operator confirms material assignment?
- [ ] Are support/frame/emblem layers excluded from automatic Oracal grouping?
- [ ] Are close colours left separable until operator merges?
- [ ] Are face and return finishes documentable independently per group?
- [ ] Are CostEngine, DB schema, and SVG parser unchanged unless in a dedicated build?

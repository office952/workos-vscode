# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** 0df2c79 | **Branch:** main

---

## Architecture chain

```text
workspace payload
  → ProductDefinition (linked segments, finish confirmed per segment)
  → ProductAggregateService.build(logo) + compose_from_product_definition
  → aggregate materials/operations (face + finish + dossier mapping_only)
  → AggregateCostBomBuilderService → aggregate_cost_bom_adapter
  → costable_materials / costable_operations (no mapping_only filter)
  → EstimatedInternalCostService (pass-through; must not dedupe)
```

**Principles confirmed:**

- ProductDefinition compiles product — **unchanged**
- ProductAggregate owns row identity — **fix here + seed + BOM guard**
- EIC must not repair upstream duplicates
- Two segments = separate consumption; duplicate inside one segment = defect

---

## Producers

| Producer | File/function |
|---|---|
| Face child rows | `seed_tpl_volumetric_logo_v1._component_from_spec` → `product_aggregate_service._materials_from_rows` / `_operations_from_rows` |
| Finish child rows | Same chain |
| Dossier mapping_only | `product_aggregate_service.build` lines 172–191 (`status=mapping_only`) |
| Workspace namespace | `product_aggregate_workspace_composition_service._namespace_*` |
| Dedupe | `_dedupe_materials` / `_dedupe_operations` (component_ref in key) |
| Cost BOM | `aggregate_cost_bom_adapter` lines 970–1095 (all active-module rows → costable) |
| EIC | `estimated_internal_cost_service` loops `bom.costable_*` verbatim |

---

## Current cardinality (probe confirmed)

Per segment: print_media **3**, laminate_media **3**, print op **2**, lam op **2**, app op **2**.

---

## Existing cardinality tests

**None** assert 1:1 per segment. Tests only check presence (`print_media in material_codes`), segment disjoint refs, `>= 2` print ops across two segments.

---

## Preferred direction vs seed truth

| Aspect | Owner preferred | Seed today | Resolution |
|---|---|---|---|
| Artwork media | finish only | face + finish duplicate | Remove from face seed; filter |
| Print/lam ops | finish only | face only | **Move to finish seed** |
| Application | finish | finish | OK |
| Face | substrate + CNC | also artwork (wrong) | Remove artwork from face |

**Pilot contract:** `logo_finish diferențiază print/vinyl/laminare` — supports finish ownership.

---

## logo_print_finish task

Dossier task prices `logo_finish_application` — does **not** bundle print/lam into single BOM operation. Three separate ops remain valid after dedupe.

---

## EIC consumers

- Materials: `ARTWORK_OWNED_LOGO_MATERIAL_CODES` = print_media, laminate_media
- Operations: `ARTWORK_OWNED_LOGO_OPERATION_CODES` = print, lam, application
- Quantity: `_artwork_finish_area_for_segment` — **unchanged by this task**
- Rates: all missing — **must stay** until parent catalog

---

## All 7 DEC decisions

**CLOSED** in `decision-log.md` — finish-owned artwork model.

# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Implementation Log

**Phase:** IMPLEMENTATION COMPLETE  
**Accepted HEAD before:** `0df2c79`  
**Branch:** main

---

## Phase A — Seed/template contract realignment

**Inspected:** `backend/seeds/seed_tpl_volumetric_logo_v1.py` face and finish child specs; prior audit probe baseline (3/3/2/2/2 per segment).

**Changed:**
- Face child (`TPL-VOLUMETRIC-LOGO-FACE_v1`): removed `print_media`, `laminate_media`, `logo_face_print`, `logo_face_laminate`. Retained `logo_face_material`, `logo_face_cnc_cut`.
- Finish child (`TPL-VOLUMETRIC-LOGO-FINISH_v1`): added `logo_face_print`, `logo_face_laminate` (seq 1–2); retained `logo_finish_application` (seq 3), `print_media`, `laminate_media`.

**Tests:** `test_seed_face_child_excludes_artwork_materials_and_operations`, `test_seed_finish_child_includes_artwork_materials_and_operations`.

**Results:** PASS — seed contract matches canonical ownership matrix.

**Blockers:** none.

**Forbidden scope:** no live reseed, no DB migration, no rate values.

**Next step:** Layer B ownership filter.

---

## Phase B — ProductAggregate ownership filter

**Inspected:** `product_aggregate_workspace_composition_service.py` dedupe keyed on `component_ref`; dossier rows namespaced to `linked_segment::{segment}`.

**Changed:**
- New `backend/services/logo_artwork_cost_ownership.py` — concept+segment+canonical-component contract.
- Composition service filters materials/operations through `include_*_in_composed_aggregate` after namespace/dedupe.

**Tests:** per-segment cardinality, face exclusion, mapping_only exclusion, two-segment independence, partial states.

**Results:** PASS — 1 row per concept per segment on composed aggregate and Cost BOM.

**Blockers:** none.

**Forbidden scope:** no EIC dedupe, no generic material_code/operation_code collapse.

**Next step:** Layer C BOM guard.

---

## Phase C — Cost BOM defensive guard

**Inspected:** `aggregate_cost_bom_adapter.py` emitted all composed rows as costable.

**Changed:** defensive skip via same ownership helper; `CostBomSkippedItem` reason `non_canonical_logo_owner` for suppressed rows.

**Tests:** aggregate/BOM cardinality parity; EIC logo operation lines; letters-only regression.

**Results:** PASS.

**Blockers:** none.

**Forbidden scope:** guard is defensive only — not primary ownership source.

**Next step:** targeted test suite + runtime probe.

---

## Phase D — Tests and probe

**Changed:**
- `backend/tests/test_logo_artwork_bom_ownership_dedupe.py` (new, 13 tests).
- `backend/tests/test_estimated_internal_cost_logo_operations.py` — print op refs `comp_logo_finish::{segment}`.

**Runtime probe** (`test_runtime_bom_inventory_probe_report`, fixture `confirmed_bindings_payload`):

| Segment | Concept | Count | Owner |
|---|---|---:|---|
| logo-stanga | print_media | 1 | comp_logo_finish::logo-stanga |
| logo-stanga | laminate_media | 1 | comp_logo_finish::logo-stanga |
| logo-stanga | logo_face_print | 1 | comp_logo_finish::logo-stanga |
| logo-stanga | logo_face_laminate | 1 | comp_logo_finish::logo-stanga |
| logo-stanga | logo_finish_application | 1 | comp_logo_finish::logo-stanga |
| logo-dreapta | (same five concepts) | 1 each | comp_logo_finish::logo-dreapta |

**Baseline → after:** 3/3/2/2/2 per segment → **1/1/1/1/1** per segment.

**Results:** PASS.

**Blockers:** none.

**Forbidden scope:** historical fixture unchanged; probe uses isolated in-memory DB.

**Next step:** validation + review + commit.

---

**IMPLEMENTATION COMPLETE**

# W2-T01 — Product Definition Composition Contract Resumption V1

**Task:** `W2-T01` / `PRODUCT_DEFINITION_COMPOSITION_CONTRACT_RESUMPTION_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `5f4aed0`  
**Application baseline:** `6637aa2`  
**Date:** 2026-07-14  
**Verdict:** `W2_PD_COMPOSITION_PASS_COMMITTED`

## Scope

Deterministic Product Definition composition layer (Cases A–D) between canonical Intake truth and Product Aggregate. No pricing, vector, or new operator UI.

## Root cause

Product Definition preview used stale form bindings (`client.width_mm`, `finish_setup.mounting_system`, `quote_geometry.letter_face_area_m2`) without read-only enrichment from canonical Intake sources (`quote_geometry`, `mounting_solution`). Composition graph builder existed but canonical value resolution left false `missing_required` blockers on live fixture.

## Implementation

| File | Change |
|------|--------|
| `backend/services/product_definition_composition_contract.py` | Cases A–D graph, frozen mounting resolution, stable node/edge IDs |
| `backend/services/product_definition_builder_service.py` | Wire composition; enrich canonical values (geometry + mounting projection) |
| `backend/schemas/product_definition.py` | Composition schema types on `ProductDefinitionPreview` |
| `backend/tests/test_product_definition_composition_contract.py` | 21 composition + enrichment tests |
| `backend/tests/test_product_definition_builder.py` | Align stale dossier component count assertion |

## Classifications

| Contract | Classification |
|----------|----------------|
| `mounting_system` | `DERIVED_COMPATIBILITY_FIELD_REQUIRED` — projected from `mounting_solution`; canonical wins |
| `width_mm` / `height_mm` | `SVG_ANALYSIS_OUTPUT` — prefer `quote_geometry` over empty `client` |
| `letter_face_area_m2` | `PRODUCT_DEFINITION_DERIVATION` — alias `quote_geometry.face_area_m2` |
| `volum_aluminum_module_template_code` | `INTAKE_CONFIRMED_INPUT` — fixture gap remains |
| Vector | `NONBLOCKING_FOR_COMPOSITION` |
| Test infra (`test_finish_target_runtime_capture.py`) | `PREEXISTING_INFRA_DEBT_NONBLOCKING` |

## Temporary debt

**TD-W2-PD-001** — `mounting_system` compatibility projection in `_build_canonical_values`. Canonical `mounting_solution` is authority; projection is read-only for legacy module bindings (`finisaje`, `structura_suport` trigger alignment). Removal when W2-T02 consumers read composition graph / `frozen_mounting_solution` only.

## Tests

| Suite | Result |
|-------|--------|
| `test_product_definition_composition_contract.py` | 21/21 PASS |
| `test_product_definition_builder.py` | PASS |
| `test_product_system_identity_boundary.py` | 28/28 PASS |
| `test_finish_target_runtime_capture.py` (isolated) | 10/10 PASS, 0 collection errors |

## Runtime (IR-MRJS4VIK / `80570a4a-a806-4305-a39c-b34a72092694`)

After backend reload:

- `composition_mode`: `single_child` (Case B)
- Nodes: `root_product` + `mounting_panel` (ACM)
- Edge: letters → ACM `visual_mounting_support`
- `missing_required`: `['volum_aluminum_module_template_code']` only (genuine Intake persistence gap)
- Canonical: `mounting_system=acm_panel`, geometry from `quote_geometry`

Fixture not mutated.

## W2-INT-01 readiness

**PARTIAL YES** — Cases A–D, mounting mapping, geometry ownership, vector classification coherent in PD. Aggregate explicit graph consumption deferred to **W2-T02**.

## Next

`W2-T02` — Aggregate handoff without re-inference.

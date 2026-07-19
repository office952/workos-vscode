# AUTHORITY SPLIT CHECKPOINT — Montaj

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `392d6e1` (audit)  
**Visual candidate:** `5336734`  
**Runtime:** FE `:3000` · BE `:8003` (both 200)  
**ACM WS:** `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` (`IV6-EA145E74`)  
**Foreign WIP:** present — will not stage  

## Owner decisions (locked)

| ID | Decision |
|----|----------|
| D1 | Fundal/ACM/segmentation = PRODUCT TRUTH; not disabled by commercial scope |
| D2 | ACM + `mounting_scope=none` is valid; no PD/Aggregate blocker solely from commercial none |
| D3 | Single-panel → `power_supply_service_corner`; Segmented → `electrical_connection_management` |
| D4 | Accesorii 5% = manufacturing consumable; pricing-only; not Montaj blocker; independent of scope |
| D5 | Template commercial; inactive under scope none; legacy retained but inactive |

## Current ACM runtime values (audit baseline)

| Key | Value |
|-----|-------|
| mounting_scope | `none` |
| mounting_solution | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| mounting_template_enabled | `true` (legacy persisted) |
| mounting_template_material_type | `forex` |
| power_supply_service_corner | `null` |
| segmented_background.status | `PROPOSED` (API) / UI claimed CONFIRMED (contradiction) |
| svg_support_selection | confirmed ALUCOBOND_CASED_PANEL |

## Exact sources

| Concern | Source |
|---------|--------|
| mounting_scope | `finish_setup.mounting_scope` · FE `mountingScope.ts` · BE `mounting_scope_service.py` |
| mounting_solution | `finish_setup.mounting_solution` · FE/BE mounting_solution* |
| mounting_template_* | `finish_setup` · FE ReviewStep under `mountingPrepActive` · CPP `_sablon_enabled` |
| power_supply_service_corner | `finish_setup` · process resolver · multi-source save coalesce |
| electrical_connection_management | nested under `segmented_background` |
| Accesorii | `intake_v4_material_breakdown_service._build_mounting_accessories_percent_row` · 5% · not scope-gated |

## Blockers to repair

### MOUNTING_SCOPE_INACTIVE

- **Where:** `product_definition_composition_contract.py:475-476`
- **Predicate:** `if solution and not frozen.prep_active`
- **Bug:** Treats any resolved solution (including ACM product) as commercial-prep-gated
- **Also:** child inclusion at `:503` requires `frozen.prep_active`, so ACM child is omitted from graph when scope=none
- **Contract conflict:** `mounting_solution_service.is_mounting_solution_composition_active` already says ACM active at scope none
- **Aggregate surface:** `COMPOSITION_GRAPH_BLOCKED` via `product_aggregate_explicit_composition_service.py`
- **Test to invert:** `test_mounting_scope_inactive_with_selected_child` expects blocker today — must become ACM-valid

### PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED

- **Where:** `product_process_resolver_service.py:394-401` (`support_type == alucobond_cased` && missing corner)
- **Aggregate:** `PROCESS_RESOLVER_{code}` prefix in aggregate bridge
- **Repair:** When segmented electrical authority is CONFIRMED+complete, do not require legacy single-panel corner

## Compatibility risks

1. Legacy `mounting_template_enabled=true` with scope none — retain inactive, no delete (D5)
2. Legacy `mounting_system` fallback — leave; do not delete keys
3. Metal premount still gated by prep scope (intentional per `is_mounting_solution_composition_active`)
4. Installation_template still requires prep
5. Existing test expects MOUNTING_SCOPE_INACTIVE for ACM+none — update to new authority
6. No schema/migration required — JSON finish_setup only

## Schema/migration necessary?

**NO.** Interpretation + compiler + readiness + UI. Prefer retained-but-inactive for legacy template.

## Implementation plan (post-checkpoint)

1. Track A: composition uses `is_mounting_solution_composition_active`; ACM never emits MOUNTING_SCOPE_INACTIVE for scope none
2. Track B: prove/fix segmented confirm persist + UI status from finish only
3. Track C: resolver respects segmented electrical completeness
4. Track D: template inactive downstream under scope none
5. Track E: Accesorii operator copy + ensure not Montaj blocker
6. Tracks F–K: PD/Agg/Confirmare/UI/persistence/tests/runtime

**STOP before migration/seed/formula change/task redesign.**

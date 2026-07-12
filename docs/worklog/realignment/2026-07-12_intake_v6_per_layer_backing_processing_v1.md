# Intake V6 per-layer Forex backing processing v1

**Date:** 2026-07-12  
**Task:** INTAKE_V6_STEP2_SLICE_B_PER_LAYER_BACKING_PROCESSING_V1  
**HEAD before:** b45d3e3

## Scope

Moved `finish_setup.backing_mode` from global operator truth to per-layer `letter_group_finishes[]` / `artwork_finishes[]` rows.

## Changes

- Backend schema: optional `backing_mode` on letter group + artwork finish rows.
- `resolve_layer_backing_mode()` compatibility reader — explicit layer value wins; legacy global seeds missing rows only.
- Material breakdown CNC: per-layer back CNC aggregation via `build_volumetric_letters_cnc_operation_rows_with_layer_backing`.
- Frontend: backing selector on each applicable layer card (BACK sold scope); global row removed.
- Payload sync: when any layer owns `backing_mode`, seed siblings from legacy global once and strip global fields from save body.

## Validation

- `pytest tests/test_intake_v6_per_layer_backing_processing.py` — 16 passed
- Targeted Vitest: letter groups, artwork, payload sync, backing row — 49 passed

## Boundary

No LIGHTING/ELECTrical split, no pricing formula changes, no DB migration, no ProductDefinition/Aggregate changes.

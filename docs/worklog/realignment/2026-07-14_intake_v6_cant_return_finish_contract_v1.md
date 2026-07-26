# W1-L-CANT — INTAKE_V6_CANT_RETURN_FINISH_CONTRACT_V1

**Date:** 2026-07-14  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `911616d`  
**Fixture:** `IR-MRJS4VIK` / workspace `80570a4a-a806-4305-a39c-b34a72092694`

## Lane reservation

| Field | Value |
|-------|-------|
| Reserved truth path | cant/return finish from per-layer `finish_setup` → `product_truth.components.return_cant` → runtime capture / readiness / review |
| Canonical owner | Per-layer `letter_group_finishes[]` / `artwork_finishes[]` with aggregate in `product_truth.components.return_cant.instances` |
| Backend writers | `return_cant_product_truth_bridge`, `return_cant_finish_truth_service`, `intake_v4_finish_truth_service` |
| Frontend writers | Intake V6 finish step layer cards (`intakeV4ReturnCantBridge`) |
| Capture/readiness | `return_cant_runtime_state`, `form_system_contract_backbone_service` overlay |
| Review consumer | `buildReturnCantCanonicalRuntimeFromPayload` → `mapReturnCantTruthFieldsReadonly` |
| Collision risk | Shares `finish_setup` with W1-L-FINISH — serialized after `911616d` |

## Root cause

Backend already persisted confirmed `return_cant` instances (`white_aluminum`, depth 60 mm). Review step readonly mapper lacked `canonicalRuntime` from `product_truth`, so operator blockers falsely included `RETURN_CANT_MATERIAL_MISSING` and `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING`. Depth was not the defect.

## Implementation

1. `return_cant_finish_truth_service.py` — save-time per-layer hydration and stale Oracal/RAL clearing on method change.
2. `return_cant_runtime_state.py` — aggregate runtime state from persisted instances for capture overlay.
3. `returnCantCanonicalRuntimeFromProductTruth.ts` — map `product_truth` → readonly mapper `canonicalRuntime`.
4. `IntakeV6ReviewStep.tsx` — wire canonical runtime into review awareness.

## Verification

| Gate | Result |
|------|--------|
| Backend focused tests | 60 passed (`test_return_cant_finish_truth`, bridge, spine, backbone) |
| Frontend focused tests | 8 passed (canonical runtime + readonly mapper) |
| Runtime capture blockers | No `RETURN_CANT_MATERIAL_MISSING` / `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` |
| Pricing preview | `is_ready_for_quote: true` |
| Review UI | No cant operator blocker banner; technical perimeter warnings remain |
| Fixture mutation | Read-only inspection — `RUNTIME_FIXTURE_CHANGED: NO` |

## Protected lanes

Mounting spine, finish persistence (`911616d`), handoff merge — unchanged.

## Vector (TE2E-007)

`unclassified_vector_artwork_requires_decision` remains on fixture — classified **NONBLOCKING_FOR_WAVE_1** (optional W1-L-VECTOR after W1-INT-02).

## Screenshot

`docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/w1-l-cant-review-step-after.png`

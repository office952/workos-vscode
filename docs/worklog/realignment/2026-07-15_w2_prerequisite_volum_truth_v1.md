# W2-PREREQUISITE-VOLUM-TRUTH — INTAKE_V6_VOLUM_ALUMINUM_MODULE_TECHNICAL_TRUTH_V1

**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `548258f`  
**Verdict:** `W3_VOLUM_TRUTH_PASS_COMMITTED`

## Classification

**`COMPONENT_OPTION_INPUT_RESOLVED_TO_TEMPLATE`**

- Physical meaning: aluminum return/cant/lateral module (`TPL-VOLUM-ALUMINIU_v1`) for `modelare_cant` on volumetric letters.
- Intake persists operator selection or accepts Product System unique-link resolution.
- Product Definition composes explicit `volum_aluminum` graph child when code present.
- Field name retained — matches Product System `trigger_field` on module link.

## Canonical owner

| Layer | Owner |
|-------|-------|
| Applicability | `intake_v6_volum_aluminum_module_truth_service` |
| Resolution source | Product System `product_template_module_links` |
| Persistence | Intake `finish_setup.volum_aluminum_module_template_code` on save |
| Graph node | Product Definition composition contract |
| Cost | 7B/7H via `modelare_cant` when graph includes volum child |

## Applicability

Required for **`TPL-VOLUMETRIC-LETTERS_v2`** when cant truth is active (`return_depth_mm` > 0 and return finish not inactive).  
**Not** required for standalone ACM root templates or products without cant.  
Case B (letters + ACM mounting) **still requires** volum module for letter cant — mounting child is separate.

## Implementation

- `backend/services/intake_v6_volum_aluminum_module_truth_service.py`
- Wired into `save_finish_setup_for_intake_v6_workspace`
- UI: volum module select enabled by cant applicability, not mounting prep scope
- Tests: `test_intake_v6_volum_aluminum_module_truth.py` (+ snapshot graph preservation)

## Wave 3 exit note

Live snapshot POST/idempotency proof remains a Wave 3 exit gate item (not in this task).

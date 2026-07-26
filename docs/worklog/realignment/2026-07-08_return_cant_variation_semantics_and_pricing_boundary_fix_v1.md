# 2026-07-08 - return cant variation semantics and pricing boundary fix v1

HEAD before:

- `baa9541`

HEAD after:

- pending at write time

Decision drafted:

- `RETURN_CANT_VARIATION_SEMANTICS_READY_FOR_ADAPTER`

Files read:

- `docs/architecture/product-system/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT.md`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_intake_v6_variations_truth_capture_audit_v1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN.md`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishModel.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `backend/services/shared_edge_cant_rules.py`

Files touched:

- `docs/architecture/product-system/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY.md`
- `docs/qa/return-cant-variation-semantics-and-pricing-boundary-2026-07-08/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY_FIX_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_variation_semantics_and_pricing_boundary_fix_v1.md`

Local hypothesis confirmed:

- the preset options `Alb`, `Negru`, `Auriu`, `Argintiu` are stock color semantics, not separately costed finish semantics;
- only `Oracal 651` and `Vopsit RAL` remain extra finish cost semantic variants;
- width remains the primary material cost driver.

Key outcomes:

1. `stock_color` is now explicit as semantic family.
2. `finish_variant.type` is the correct future adapter target, more precise than a flat `finish_type` concept.
3. `pricing_keys.finish_extra` must be absent for `stock_color`.
4. Oracal and RAL selectors must be preserved as structured selectors.

Validation planned:

- `git diff --check`
- no build
- no tests

Roadmap awareness checkpoint:

- note: `9/10`
- position: final semantic cleanup immediately before adapter
- dead pieces check: no dead variation family found; previous ambiguity around stock colors is now resolved
- alignment with target direction: `92/100%`

Next recommended prompt:

- `RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1`

Constraint to carry forward:

- map `Alb/Negru/Auriu/Argintiu` to `stock_color` with no extra finish pricing key; preserve Oracal and RAL structured selectors and emit blocker instead of invented pricing keys when alignment is missing.
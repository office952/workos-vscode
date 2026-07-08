# 2026-07-08 - return cant truth field capture readonly contract adapter v1

HEAD before:

- `c357681`

HEAD after:

- pending at write time

Files read:

- `docs/architecture/product-system/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY.md`
- `docs/qa/return-cant-variation-semantics-and-pricing-boundary-2026-07-08/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY_FIX_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_variation_semantics_and_pricing_boundary_fix_v1.md`
- `docs/architecture/product-system/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT.md`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT_V1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnCantBridge.ts`
- `frontend/src/lib/intakeV6/intakeV4ReturnCantBridge.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishModel.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnCantBridge.test.ts`

Files touched:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `docs/worklog/realignment/2026-07-08_return_cant_truth_field_capture_readonly_contract_adapter_v1.md`

Why this location is safe:

1. the adapter is a pure frontend library helper colocated with existing Intake V6 Product Truth read-only mapping code;
2. it does not introduce UI behavior, backend endpoints, or pricing writes;
3. it consumes already existing runtime row structures and emits a contract-shaped read model only.

Implementation notes:

1. `Vector Litere` and `Vector Logo` stay separated as distinct instance entries.
2. `Alb/Negru/Auriu/Argintiu` map to `stock_color` and never emit a finish extra pricing key.
3. `Oracal 651` and `Vopsit RAL` stay structured selector references with reusable catalog boundary warnings.
4. `quote_geometry.letter_perimeter_m` stays context-only and does not unlock confirmed perimeter.

Tests planned for this slice:

- targeted Vitest for `returnCantTruthFieldCaptureReadonlyAdapter.test.ts`

Remaining blockers expected by design:

- `components.face.confirmed_perimeter` still missing as confirmed dependency
- `components.return_cant.confirmation_state` still missing canonically
- `components.return_cant.material_profile` still missing canonically
- `paint_target` still missing for RAL
- Oracal cant pricing alignment still not clean
- RAL cant pricing alignment still not fully proven

Pricing boundary confirmation:

- material cost stays in `/inventory/pricing`
- labor cost stays in `/inventory/pricing`
- no numeric price or cost is stored by the adapter
- stock color has no extra finish cost key
- no pricing keys are invented

Reusable catalog boundary confirmation:

- Oracal stays a reusable catalog reference, not a private return_cant concept
- RAL stays a reusable catalog reference, not a private return_cant concept
- stock colors are treated as operational references for a future reusable boundary
- no catalog UI or CRUD is introduced

Analyzer boundary confirmation:

- analyzer/geometry may supply perimeter evidence only
- analyzer does not confirm truth
- analyzer does not provide cost or price
- Product Truth remains the confirmation owner

Forbidden scope confirmation:

- no component root
- no component quote
- no Logo offerability changes
- no Pricing changes
- no Quote/Order changes
- no Execution changes
- no ProductAggregate changes
- no TaskGraph changes
- no ExecutionPlan changes
- no DB / seed / migration
- no UI new surface
- no public endpoint

Next recommended prompt:

- `REUSABLE_FINISH_CATALOGS_BOUNDARY_AUDIT_V1`
# 2026-07-08 - return cant truth fields readonly mapper implementation v1

HEAD before:

- `354a81a`

HEAD after:

- pending at write time

Fisiere citite:

- `RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION.md`
- `RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_CONTRACT.md`
- `RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT.md`
- `RETURN_CANT_COMPONENT_PREVIEW_READINESS_REMEDIATION.md`
- `FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/product_definition_builder_service.py`

Fisiere atinse:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `docs/worklog/realignment/2026-07-08_return_cant_truth_fields_readonly_mapper_implementation_v1.md`

De ce locul ales este sigur:

- mapperul sta langa Product Truth draft, unde exista deja state read-only pentru `components.returnCant.*`;
- poate primi separat `quote_geometry.letter_perimeter_m` ca evidence/context, fara sa il promoveze la dependency truth;
- nu schimba UI, backend, ProductDefinition sau runtime writes;
- ramane un helper intern strict diagnostic.

Teste vizate pentru acest slice:

- missing fields -> blockers
- `quote_geometry.letter_perimeter_m` -> `context_only`
- `return_depth_mm` hydrated/fallback -> nu deblocheaza readiness
- lipsa `components.face.confirmed_perimeter` -> blocker explicit
- `confirmation_state != confirmed` -> blocked

Teste rulate:

- `npm.cmd run test -- src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- rezultat: 1 file, 6 teste, toate passed

Blockers ramasi asteptati la runtime:

- `components.face.confirmed_perimeter` lipsa explicit
- `components.return_cant.material_profile` lipsa
- `components.return_cant.layer_group_ids` lipsa
- `components.return_cant.confirmation_state` lipsa
- `components.return_cant.perimeter_source` lipsa
- color split incomplet pe path canonic

Forbidden scope confirmation:

- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB / seed / migration
- fara UI nou
- fara endpoint public nou

Next recommended prompt:

- `RETURN_CANT_COMPONENT_PREVIEW_READONLY_BLOCKED_STATE_UI_AWARENESS_V1`
# 2026-07-08 - return cant component truth field capture plan v1

HEAD before:

- `a9b36b1`

HEAD after:

- pending at write time

Fisiere citite:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantBlockedStateAwarenessPanel.tsx`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION.md`
- `docs/architecture/product-system/RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT.md`
- `docs/architecture/product-system/FORM_SYSTEM_FIELD_CONTRACT_MAP.md`
- `docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`
- `docs/architecture/product-system/MATERIAL_COLOR_CATALOGS_AND_INVENTORY_KEY_MODEL_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_component_preview_readonly_blocked_state_ui_awareness_v1.md`

Fisiere atinse:

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN.md`
- `docs/qa/return-cant-component-truth-field-capture-plan-2026-07-08/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_component_truth_field_capture_plan_v1.md`

Ipoteza locala confirmata:

- exista deja suficiente suprafete read-only si contractuale pentru a descrie un plan clar de capturare a field-urilor lipsa, fara implementare runtime;
- boundary-ul de Pricing este suficient de explicit ca sa tina costul si pretul in afara componentei.

Decizie:

- `RETURN_CANT_FIELD_CAPTURE_PLAN_READY`

Rezumat de directie:

- componenta detine formula, dependency requirements si pricing lookup keys;
- Pricing detine cost material, cost manopera si pret/tarif;
- Analyzer sugereaza geometria si layer evidence;
- Product Truth confirma field-urile si dependency-ul pe `face`;
- ProductDefinition consuma truth-ul confirmat, nu il inventeaza.

Validare planificata pentru acest slice:

- `git diff --check`
- fara build
- fara teste, deoarece nu se atinge cod runtime

Next recommended prompt:

- `RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1`
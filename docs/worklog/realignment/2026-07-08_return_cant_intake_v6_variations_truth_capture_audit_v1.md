# 2026-07-08 - return cant Intake V6 variations truth capture audit v1

HEAD before:

- `8237d9a`

HEAD after:

- pending at write time

Verdict drafted:

- `RETURN_CANT_VARIATIONS_AUDIT_READY_FOR_ADAPTER`

Rute auditate:

- `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`
- `http://127.0.0.1:3000/intake-v6/IR-MR18L96M/operator`
- `http://127.0.0.1:3000/inventory/pricing`

Fisiere citite:

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN.md`
- `docs/qa/return-cant-component-truth-field-capture-plan-2026-07-08/RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_component_truth_field_capture_plan_v1.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantBlockedStateAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishModel.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/volumetricQuoteInput.ts`
- `frontend/src/lib/pricingRegistry.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/volumetric_material_rate_resolver.py`
- `backend/services/shared_edge_cant_rules.py`
- `backend/services/intake_v4_ral_paint_rules_service.py`
- `docs/architecture/product-system/FORM_SYSTEM_FIELD_CONTRACT_MAP.md`
- `docs/architecture/product-system/MATERIAL_COLOR_CATALOGS_AND_INVENTORY_KEY_MODEL_V1.md`
- `docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`

Fisiere atinse:

- `docs/architecture/product-system/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT.md`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_intake_v6_variations_truth_capture_audit_v1.md`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/return-cant-letters-review-zone.png`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/return-cant-logo-variation-card.png`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/pricing-return-profile-variants.png`
- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/pricing-return-operations.png`

Findings locked:

1. `Vector Litere` si `Vector Logo` au ambele cant per row in UI-ul actual.
2. Taxonomia reala de cant este aceeasi pentru ambele:
   - `Alb`
   - `Negru`
   - `Auriu`
   - `Argintiu`
   - `Vopsit RAL`
   - `Oracal 651`
   - depth `30 / 60 / 80 / 100`
3. Materialul de profil are pricing live separat pe latimi `30/60/80/100`.
4. Laborul de cant are pricing live separat ca operatii, dar generic per ml, nu per depth.
5. `Oracal 651` pentru cant foloseste inca partial `shared_edge_cant_rules` owner pricing path, ceea ce ramane gap de alignment fata de Pricing Registry.
6. Product Truth canonic ramane lipsa pentru `material_profile`, `layer_group_ids`, `confirmation_state`, `perimeter_source` si `face.confirmed_perimeter`.

Ipoteza locala confirmata:

- auditul variatiilor este suficient pentru a porni adapterul read-only, dar adapterul trebuie sa respecte taxonomia reala si sa nu inventeze pricing keys sau component confirmation.

Validation planned for this slice:

- `git diff --check`
- docs-only + screenshots-only scope check
- fara build
- fara teste

Roadmap awareness checkpoint:

- nota: `8/10`
- pozitie: imediat inainte de `RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1`
- dead pieces check: nu s-au gasit variatii moarte; s-a gasit un gap real pe Oracal cant pricing alignment
- directia stabilita: `88/100%`

Next recommended prompt:

- `RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1`

Cu constrangerea:

- mapeaza variatiile reale auditate exact asa cum sunt azi; nu inventa labor keys per depth si nu transforma `Confirmat in Pasul 1` sau `quote_geometry.letter_perimeter_m` in truth confirmed.
# RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1

## Verdict

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_BRIDGE_PLAN_BLOCKED
```

## Scope checked

- docs-only plan / audit
- no UI changes
- no Pricing changes
- no adapter changes
- no Product Truth writes
- no runtime bridge implementation
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration
- no seed run

## Accepted HEAD

- `ef30518`

## Decision summary

Planul este blocat pentru implementare directa deoarece infrastructura actuala ofera:

1. traseu clar de persistare `finish_setup`;
2. derivari backend additive pe payload;
3. draft builder si readonly mappers pentru `return_cant`;

dar nu ofera inca:

1. un container canonic persistat pentru `components.return_cant.instances.<instance_key>`;
2. o sursa runtime confirmata pentru `components.face.confirmed_perimeter`;
3. o stare explicita de confirmare a componentei `return_cant`;
4. aliniere completa intre readonly adapter si pricing keys finale verificate.

## Existing runtime infrastructure found

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` construieste si salveaza `finish_setup`.
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` expune `saveFinishSetup(...)` si `confirmProductComposition(...)`.
- `frontend/src/lib/intakeV6/intakeV6Api.ts` are deja endpoint-urile necesare de persistare workspace.
- `backend/services/intake_v6_workspace_service.py` este punctul corect pentru derivari runtime persistate.
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` construieste Product Truth draft in memorie.
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts` defineste blockers si campuri canonice readonly.
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts` defineste target paths per instance in mod readonly.

## Missing runtime infrastructure / blockers

- lipseste containerul runtime canonic `components.return_cant.instances.<instance_key>` in payloadul real;
- lipseste runtime source pentru `components.face.confirmed_perimeter`;
- lipseste component-level `confirmation_state` pentru `return_cant`;
- `productTruthDraftBuilder` foloseste inca modelul legacy `components.returnCant.*`;
- `form_system_contract_backbone_service.py` foloseste inca `components.return.*`;
- readonly adapterul inca indica pricing key targets legacy/lowercase in locul codurilor finale uppercase pentru cant labor/paint material/paint labor.

## Product Truth target paths

```text
components.return_cant.instances.<instance_key>.finish_variant.type
components.return_cant.instances.<instance_key>.finish_variant.stock_color_label
components.return_cant.instances.<instance_key>.finish_variant.vinyl.material_family
components.return_cant.instances.<instance_key>.finish_variant.vinyl.series
components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code
components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference
components.return_cant.instances.<instance_key>.finish_variant.paint.system
components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference
components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor
components.return_cant.instances.<instance_key>.geometry.perimeter_source
components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m
components.return_cant.instances.<instance_key>.layer_group_ids
components.return_cant.instances.<instance_key>.confirmation_state
```

## Confirmation rules

- `quote_geometry.letter_perimeter_m` este context only.
- nu poate deveni `confirmed_perimeter_m` fara sursa confirmata Product Truth / component.
- `Confirmat in Pasul 1` nu este `return_cant.confirmation_state = confirmed`.
- Pasul 1 confirma ownership / layers, nu component truth complet.
- bridge-ul trebuie sa ramana blocat daca lipsesc perimeter confirmat, layer mapping sau component confirmation.

## E2E terminology dictionary

UI:

- `Culoare Stoc`
- `Folie autocolanta`
- `Vopsit RAL`

Technical/Product Truth/backend:

- `stock_color`
- `vinyl_application`
- `paint_application`

Catalog:

- `stock_color_label`
- `vinyl.series`
- `vinyl.color_code`
- `paint.system = RAL`
- `paint.ral_code`

Pricing:

- `material_profile_width`
- `vinyl_material`
- `vinyl_application_labor`
- `ral_paint_material_by_width`
- `ral_paint_labor`

Legacy transitional only:

- `oracal`
- `ral_paint`
- `PAINTING`
- `MAT-VOPSEA-RAL`
- `VINYL_APPLICATION`
- `FACE_VINYL_APPLICATION_LABOR`

## Bridge readiness matrix summary

- `finish variant type`: source exists, canonical write blocked by missing runtime instance container.
- `stock color label`: readonly derivation exists, canonical write missing.
- `vinyl series / color / catalog reference`: partial row sources exist, canonical persisted object missing.
- `paint system / RAL / catalog reference`: partial row sources exist, canonical persisted object missing.
- `material_profile_width`: verified pricing key exists, writer missing.
- `vinyl_material`: verified pricing source exists, writer missing.
- `vinyl_application_labor`: final pricing key exists, readonly target still legacy-lowercase.
- `ral_paint_material_by_width`: final pricing keys exist, readonly target still legacy pattern.
- `ral_paint_labor`: final pricing key exists, readonly target still legacy-lowercase.
- `layer_group_ids`: evidence exists as context only, canonical assignment missing.
- `confirmed_perimeter`: blocked, no canonical runtime source.
- `confirmation_state`: blocked, no explicit component-level field.

## Validation

- read-only code/document audit only
- `git diff --check`
- no tests required
- no build required

## Next recommended prompt

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1
```
# FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1

Date: 2026-07-08
Project: WorkOS
Mode: docs-only / read-only audit

## 1. Safety gate

Comenzi rulate:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git status --short --untracked-files=no
git diff --check
```

Rezultat:

- accepted HEAD: `875371e`
- staged files inainte de lucru: none
- tracked diffs inainte de lucru: none
- untracked parked lanes: prezente
- actiune pe untracked parked lanes: niciuna
- verdict safety gate: poate continua docs-only audit

## 2. Scope

Scopul acestui slice:

- harta explicita component -> field -> source/state -> Product Truth path -> required -> ProductDefinition consequence;
- clasificare canonica a ownership-ului;
- mapare MVP pentru `return_cant`;
- blockers si readiness rules pentru preview-ul read-only viitor.

Confirmare de boundary:

- fara implementare backend;
- fara implementare frontend;
- fara UI nou;
- fara endpoint nou;
- fara Product Truth write changes;
- fara component root;
- fara component quote;
- fara Pricing / Quote / Order / Execution;
- fara ProductAggregate / TaskGraph / ExecutionPlan;
- fara DB / seed / migration.

## 3. Fisiere inspectate

Contracte anterioare:

- `docs/architecture/product-system/COMPONENT_OWNED_TRUTH_BEFORE_COMPONENT_CALCULATION_CONTRACT.md`
- `docs/qa/component-owned-truth-before-calculation-2026-07-08/COMPONENT_OWNED_TRUTH_BEFORE_COMPONENT_CALCULATION_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-08_component_owned_truth_before_component_calculation_contract_v1.md`
- `docs/architecture/product-system/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT.md`
- `docs/qa/intake-v6-component-calculation-preview-contract-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_preview_contract_v1.md`
- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_READINESS_AUDIT_V1.md`
- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/screenshots_index.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_readiness_audit_v1.md`

Backend read-only:

- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/pre_order_technical_preview_readonly_service.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`

Frontend read-only:

- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`

## 4. Matrix summary

Constatarea centrala:

```text
Ownership-ul pe componente exista partial, dar Product Truth path-urile nu sunt inca unificate intre Backbone, Product Truth draft si ProductDefinition consequence trace.
```

Rezumat pe componente:

- `face`: are owner clar, dar materialul, grosimea si target-ul de finish raman partial fallback sau pending.
- `return_cant`: este cel mai apropiat de MVP, dar ii lipsesc `material_profile`, `perimeter_source`, `layer_group_ids` si `confirmation_state` ca truth explicit de componenta.
- `back`: are `backing_mode`, dar materialul si geometry source sunt inca prea implicite.
- `lighting`: are mode si cateva chei electrice, dar multe sunt fallback/hydrated si nu pot fi tratate ca truth confirmat.
- `finish`: are target si artwork split partial, dar `target` vs `finishTarget` nu este inca unificat.
- `premount_support`: cel mai mare risc semantic; `mounting_system` si `metal_support_required` nu trebuie confundate cu support truth.
- `logo_linked_child`: ramane context linked-only, nu root si nu offerability.
- `product_context`: important pentru guards si dependency-uri, dar nu este owner de input calculabil pentru componenta.

## 5. Return/cant MVP map

### Fields partial ready

- `return_depth_mm`
- `return_finish_type`
- `return_oracal_code` sau echivalent color code

### Fields dependency-only

- `letter_perimeter_m`
- `quote_geometry.confirmed`
- `svg.selected_layer_group`

### Fields missing as component truth

- `material_profile`
- `perimeter_source`
- `layer_group_ids`
- `confirmation_state`

### Return/cant MVP verdict

Verdict:

```text
partial_ready
```

Motive:

- adancimea este prezenta, dar vine des ca hydrated/fallback;
- perimetrul exista doar ca dependency root/face, nu ca dependency path explicita;
- materialul de profil lipseste ca field explicit de componenta;
- confirmarea operatorului este dispersata, nu component-scoped.

## 6. Product Truth path contract

Path-uri recomandate pentru MVP `return_cant`:

- `components.return_cant.return_depth_mm`
- `components.return_cant.perimeter_source`
- `components.return_cant.material_profile`
- `components.return_cant.finish_type`
- `components.return_cant.color_target`
- `components.return_cant.layer_group_ids`
- `components.return_cant.confirmation_state`

Status actual:

- niciunul dintre aceste path-uri nu este inca unificat exact asa in tot codul;
- exista variante partiale in backbone si draft builder;
- tocmai aceasta nealiniere justifica harta de ownership din acest task.

## 7. Blockers

Blockers minimi documentati pentru preview-ul viitor:

- `RETURN_CANT_DEPTH_MISSING`
- `RETURN_CANT_PERIMETER_MISSING`
- `RETURN_CANT_MATERIAL_MISSING`
- `RETURN_CANT_FINISH_MISSING`
- `RETURN_CANT_COLOR_TARGET_MISSING`
- `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED`
- `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`
- `COMPONENT_ROOT_BLOCKED`
- `COMPONENT_QUOTE_BLOCKED`

## 8. Risks

Riscuri principale:

- default-urile din `finishFromPayload()` pot fi confundate cu truth confirmat;
- `components.return.depth_mm` vs `components.returnCant.depthMm` creeaza ambiguitate de path;
- `components.finish.target` vs `components.finish.finishTarget` creeaza ambiguitate de owner/path;
- `quote_input.metal_support_required` poate fi confundat cu support truth, desi este doar derived consequence;
- runtime overlays din UI pot relaxa warnings locale, dar nu inlocuiesc backbone truth.

## 9. No-code confirmation

Confirmat:

- nu s-a modificat cod runtime;
- nu s-a modificat UI runtime;
- nu s-a creat endpoint;
- nu s-a activat component root;
- nu s-a activat component quote;
- nu s-au facut schimbari Pricing / Quote / Order / Execution;
- nu s-au facut schimbari ProductAggregate / TaskGraph / ExecutionPlan;
- nu s-au facut DB writes, migrations, seed changes sau seed runs.

## 10. Forbidden scope confirmation

Acest task a ramas in boundary-ul permis:

- fara code changes;
- fara preview implementation;
- fara UI implementation;
- fara API nou;
- fara component root;
- fara component quote;
- fara Logo offerability;
- fara Pricing;
- fara Quote/Order;
- fara Execution;
- fara ProductAggregate;
- fara TaskGraph;
- fara ExecutionPlan;
- fara DB/seed/migration.

## 11. Recommended next slice

Prompt recomandat:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Motiv:

- acest task a fixat baza de ownership si blockers;
- urmatorul pas poate construi preview-ul read-only pentru `return_cant` fara sa pretinda component root sau component quote.
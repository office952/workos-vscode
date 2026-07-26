# Return Cant Truth Fields Readonly Mapper Contract

## 1. Purpose

Acest document defineste contractul minim pentru un mapper read-only foarte ingust care raporteaza starea field-urilor canonice `return_cant` fara sa modifice runtime behavior.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = read_only_mapper
```

Acest slice nu implementeaza:

- component preview complet;
- pricing;
- quote/order/execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- UI nou;
- endpoint public nou;
- DB writes, seeds sau migrations.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_MAPPER_BLOCKED
```

Clarificare:

- contractul mapperului este gata;
- implementarea cod read-only este amanata intentionat;
- blocajul nu este de directie, ci de suprafata de input insuficient stabilizata.

## 3. Why The Small Code Mapper Is Not Safe Yet

Varianta B a fost evaluata local in jurul celor mai apropiate abstractions care deja modeleaza Product Truth read-only.

Check-ul care a disconfirmat implementarea mica in cod:

```text
ProductTruth draft-ul curent nu pastreaza explicit quote_geometry.letter_perimeter_m,
iar path-ul explicit face.confirmed_perimeter nu exista inca pe un read model canonic.
```

Evidenta locala:

- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts` expune in `ProductTruthGeometryInput` doar `return_material_perimeter_ml`, nu si `letter_perimeter_m`;
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` persista in draft `geometry.returnMaterialPerimeterMl`, nu `quote_geometry.letter_perimeter_m`;
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts` nu are inca fields canonice `components.return_cant.*`; are doar `components.returnCant.depthMm`, `finishType`, `colorCode`;
- `backend/services/intake_v6_modular_form_contract_service.py` expune `letter_perimeter_m` doar ca root geometry binding, nu ca dependency path component-owned;
- `backend/services/form_system_contract_backbone_service.py` documenteaza `return.material` ca missing si `svg.selected_layer_group` ca owner-valid gate, dar nu furnizeaza inca `components.return_cant.perimeter_dependency.face_confirmed_perimeter`.

Consecinta:

```text
Un helper de cod introdus acum ar trebui fie sa inventeze campuri lipsa,
fie sa confunde root geometry cu dependency truth,
fie sa comprime naming debt-ul actual intr-un read model care ar parea mai matur decat este.
```

Asta ar incalca contractul stabilit anterior.

## 4. Mapper Goal

Cand va fi implementat, mapperul trebuie sa construiasca o structura:

```text
return_cant_truth_fields_readonly
```

cu scop strict de clasificare si raportare:

- field prezent sau lipsa;
- source/state;
- component-owned path tinta;
- dependency path tinta;
- blocker;
- readiness.

## 5. Output Contract

Structura minima obligatorie:

```text
component_scope
root_template
root_type
quote_mode
fields[]
  - field_key
  - product_truth_path
  - current_value
  - source_state
  - owner
  - required_for_mapper
  - required_for_preview_later
  - blocker_if_missing
  - readiness
dependencies[]
  - dependency_key
  - dependency_path
  - current_value
  - source_state
  - readiness
  - blocker_if_missing
blockers[]
overall_readiness
```

Campuri optionale permise, dar nu obligatorii:

- `fallback_context_path`
- `derived_consequence_path`
- `notes[]`
- `required_when`

## 6. Canonical Fields Map

### 6.1 `material_profile`

| key | value |
|---|---|
| `field_key` | `return_cant.material_profile` |
| `product_truth_path` | `components.return_cant.material_profile` |
| `owner` | `return_cant` |
| `current_observed_source` | lipsa in read models actuale |
| `current_value` | `null` |
| `source_state_now` | `missing` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | `true` |
| `blocker_if_missing` | `RETURN_CANT_MATERIAL_MISSING` |
| `readiness_now` | `blocked` |

Nota:

- consequencele ProductDefinition sau mini-module registry pot fi raportate ulterior doar ca `derived_consequence_path`;
- ele nu pot deveni primary truth pentru acest field.

### 6.2 `perimeter_source`

| key | value |
|---|---|
| `field_key` | `return_cant.perimeter_source` |
| `product_truth_path` | `components.return_cant.perimeter_source` |
| `owner` | `return_cant` |
| `current_observed_source` | root geometry binding only |
| `current_value` | `quote_geometry.letter_perimeter_m` doar ca fallback context |
| `source_state_now` | `fallback_context_only` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | `true` |
| `blocker_if_missing` | `RETURN_CANT_PERIMETER_MISSING` |
| `readiness_now` | `blocked` |

Regula:

```text
Perimeter source poate afisa root geometry ca fallback context,
dar nu poate debloca readiness fara dependency explicita confirmed.
```

### 6.3 `perimeter_dependency.face_confirmed_perimeter`

| key | value |
|---|---|
| `field_key` | `return_cant.perimeter_dependency.face_confirmed_perimeter` |
| `product_truth_path` | `components.return_cant.perimeter_dependency.face_confirmed_perimeter` |
| `owner` | `derived_dependency` |
| `dependency_path` | `components.face.confirmed_perimeter` |
| `current_observed_source` | lipsa ca path explicit |
| `current_value` | `null` |
| `source_state_now` | `missing_explicit_dependency` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | `true` |
| `blocker_if_missing` | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `readiness_now` | `blocked` |

Regula canonica:

```text
return_cant.perimeter_dependency = face.confirmed_perimeter
```

Interdictii:

- `quote_geometry.letter_perimeter_m` nu inlocuieste acest dependency path;
- SVG suggestion nu inlocuieste acest dependency path.

### 6.4 `color_target.oracal_code`

| key | value |
|---|---|
| `field_key` | `return_cant.color_target.oracal_code` |
| `product_truth_path` | `components.return_cant.color_target.oracal_code` |
| `owner` | `return_cant` |
| `current_observed_source` | `return_oracal_code` generic, partial |
| `current_value` | posibil prezent doar in forme partiale |
| `source_state_now` | `partial_or_generic` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | doar cand `finish_type` cere Oracal |
| `blocker_if_missing` | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `readiness_now` | `blocked_if_required` |

### 6.5 `color_target.ral_code`

| key | value |
|---|---|
| `field_key` | `return_cant.color_target.ral_code` |
| `product_truth_path` | `components.return_cant.color_target.ral_code` |
| `owner` | `return_cant` |
| `current_observed_source` | lipsa |
| `current_value` | `null` |
| `source_state_now` | `missing` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | doar cand `finish_type` cere RAL |
| `blocker_if_missing` | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `readiness_now` | `blocked_if_required` |

### 6.6 `color_target.paint_target`

| key | value |
|---|---|
| `field_key` | `return_cant.color_target.paint_target` |
| `product_truth_path` | `components.return_cant.color_target.paint_target` |
| `owner` | `return_cant` |
| `current_observed_source` | lipsa |
| `current_value` | `null` |
| `source_state_now` | `missing` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | doar cand `finish_type` cere paint |
| `blocker_if_missing` | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `readiness_now` | `blocked_if_required` |

### 6.7 `layer_group_ids`

| key | value |
|---|---|
| `field_key` | `return_cant.layer_group_ids` |
| `product_truth_path` | `components.return_cant.layer_group_ids` |
| `owner` | `return_cant` |
| `current_observed_source` | layer roles si group finishes separate |
| `current_value` | doar evidence dispersata |
| `source_state_now` | `dependency_unmapped` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | `true` |
| `blocker_if_missing` | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` |
| `readiness_now` | `blocked` |

### 6.8 `confirmation_state`

| key | value |
|---|---|
| `field_key` | `return_cant.confirmation_state` |
| `product_truth_path` | `components.return_cant.confirmation_state` |
| `owner` | `return_cant` |
| `current_observed_source` | confirmari dispersate in setup, layers si geometry |
| `current_value` | `null` ca field explicit |
| `source_state_now` | `missing_component_field` |
| `required_for_mapper` | `true` |
| `required_for_preview_later` | `true` |
| `blocker_if_missing` | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` |
| `readiness_now` | `blocked` |

## 7. Dependency Contract

Mapperul viitor trebuie sa raporteze explicit dependency-urile minime.

### 7.1 Required dependency row

| key | value |
|---|---|
| `dependency_key` | `face_confirmed_perimeter` |
| `dependency_path` | `components.face.confirmed_perimeter` |
| `target_component_path` | `components.return_cant.perimeter_dependency.face_confirmed_perimeter` |
| `current_value` | `null` pana la explicit path |
| `source_state_now` | `missing_explicit_dependency` |
| `fallback_context_path` | `quote_geometry.letter_perimeter_m` |
| `readiness_now` | `blocked` |
| `blocker_if_missing` | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |

### 7.2 Derived group dependency

| key | value |
|---|---|
| `dependency_key` | `confirmed_layer_groups` |
| `dependency_path` | `svg.selected_layer_refs[]` si layer role confirmation |
| `target_component_path` | `components.return_cant.layer_group_ids` |
| `current_value` | evidence partiala |
| `source_state_now` | `dependency_unmapped` |
| `readiness_now` | `blocked` |
| `blocker_if_missing` | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` |

## 8. Mandatory Readiness Rule

Regula obligatorie pentru `overall_readiness`:

```text
overall_readiness = blocked
```

daca oricare dintre urmatoarele lipseste sau nu este `confirmed`:

- `return_cant.material_profile`
- `return_cant.perimeter_source`
- `return_cant.perimeter_dependency.face_confirmed_perimeter`
- `return_cant.layer_group_ids`
- `return_cant.confirmation_state = confirmed`

Regula de culoare:

- daca `finish_type` cere Oracal, `color_target.oracal_code` trebuie `confirmed`;
- daca `finish_type` cere RAL, `color_target.ral_code` trebuie `confirmed`;
- daca `finish_type` cere paint, `color_target.paint_target` trebuie `confirmed`.

## 9. Classification Rules

Mapperul viitor trebuie sa respecte explicit urmatoarele reguli:

1. `fallback` sau `hydrated` poate fi afisat, dar nu poate da readiness.
2. `ProductDefinition-derived` poate fi afisat ca downstream consequence, dar nu poate deveni primary truth.
3. `SVG suggestion` poate fi afisat ca suggestion, dar nu poate deveni `confirmed`.
4. root geometry poate fi context, dar nu poate inlocui dependency path-ul explicit.

## 10. Minimal Safe Implementation Surface Later

Implementarea viitoare nu trebuie sa porneasca dintr-un helper care consuma doar `ProductTruthDraft` in forma actuala.

Suprafata minima sigura trebuie sa poata vedea simultan:

- `quote_geometry.letter_perimeter_m` ca fallback context;
- layer role confirmations;
- finish setup return fields;
- candidate truth path-urile canonice ale componentei;
- blocker vocabulary-ul deja stabilit.

Pana atunci, contractul ramane docs-only.

## 11. Recommended Next Slice

Prompt recomandat:

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1
```

Dar numai dupa ce suprafata de input poate exprima explicit:

- `quote_geometry.letter_perimeter_m`;
- `components.face.confirmed_perimeter` sau echivalent read-only explicit;
- target path-urile `components.return_cant.*` fara sa inventeze truth.
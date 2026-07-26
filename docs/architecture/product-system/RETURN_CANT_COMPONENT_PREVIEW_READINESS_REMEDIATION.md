# Return Cant Component Preview Readiness Remediation

## 1. Purpose

Acest document inchide explicit decizia de readiness pentru candidatul de component scope `return_cant` in cadrul boundary-ului curent:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = pregatire pentru read_only_preview
```

Scopul este strict docs-only / read-only mapping audit. Nu implementeaza preview runtime, UI, endpoint, Product Truth writes, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB writes, seeds sau migrations.

## 2. Final Decision

Decizia obligatorie pentru slice-ul curent este:

```text
RETURN_CANT_BLOCKED_WITH_EXPLICIT_FIELDS
```

Aceasta nu inseamna ca directia este gresita.

Inseamna doar ca, pe baza codului actual, `return_cant` nu poate fi numit onest:

```text
RETURN_CANT_READY_FOR_READONLY_PREVIEW
```

pentru ca lipsesc inca fields minime de component truth sau dependency-urile minime nu sunt exprimate pe path-uri canonice.

## 3. Core Rule Applied To Return/Cant

Regula aplicata aici ramane:

```text
O componenta poate fi calculata sau previzualizata onest doar daca inputurile required exista ca truth de componenta sau ca dependency explicita confirmata.
```

Ce nu este suficient:

- fallback din `finishFromPayload()`;
- hydration din `finish_setup` fara confirmare component-scoped;
- consequence derivata in ProductDefinition;
- helper UI sau display summary;
- context root/geometry fara dependency path explicita.

## 4. Read-Only Evidence Summary

Codul citit confirma urmatoarele:

- backbone declara `return.material` cu `state=missing` si blocker `RETURN_CANT_MATERIAL_MISSING`;
- backbone declara `return.depth_mm` cu `state=hydrated` si nota explicita ca default-ul 60 mm nu este confirmed truth pana la acceptare operator;
- modular form contract expune `return_depth_mm`, `return_finish_type`, `return_oracal_code` si `letter_perimeter_m`, dar nu expune inca un field canonic `perimeter_source` sau `material_profile`;
- mini-module registry pentru `modelare_cant` consuma `return_depth_mm`, `return_finish_type`, `return_oracal_code`, `letter_perimeter_m` si alege profil material prin depth gate, adica materialul este consequence cunoscuta downstream, nu truth explicit upstream;
- Product Truth draft builder construieste `components.returnCant.depthMm`, `components.returnCant.finishType`, `components.returnCant.colorCode`, dar nu construieste inca `materialProfile`, `perimeterSource`, `layerGroupIds` sau `confirmationState` ca fields proprii;
- Review foloseste default-uri pentru `return_depth_mm` si `return_finish_type`, ceea ce confirma ca o parte din date exista doar ca fallback/hydrated, nu ca truth confirmat;
- Confirm foloseste `quote_geometry.letter_perimeter_m` si readiness globale, dar nu introduce un owner nou pentru dependency-ul perimetrului.

## 5. Canonical Field Set For Return/Cant

Pentru `return_cant`, setul minim canonic de fields pentru un preview read-only onest este:

- `return_depth_mm`
- `perimeter_source`
- `perimeter_dependency.face_confirmed_perimeter`
- `material_profile`
- `finish_type`
- `color_target.oracal_code`
- `color_target.ral_code`
- `color_target.paint_target`
- `layer_group_ids`
- `confirmation_state`

Observatie:

- codul actual are doar o parte din aceste concepte;
- celelalte trebuie documentate ca lipsa explicita, nu mascate prin derivari sau implied UI semantics.

## 6. Return/Cant Readiness Table

| field_key | component | target_component_owner | product_truth_path | source_state_required | current_source_state | required_for_preview | required_for_calculation_later | blocker_if_missing | can_use_for_return_cant_mvp | risk | recommended_action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `return_depth_mm` | `return_cant` | `return_cant` | propus `components.return_cant.return_depth_mm`; azi backbone `components.return.depth_mm`; draft `components.returnCant.depthMm` | `confirmed` | `hydrated` sau `fallback` daca vine din default | da | da | `RETURN_CANT_DEPTH_MISSING` sau `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` | partial | default-ul 60 mm poate fi confundat cu truth | unificare path si confirmation gate explicit |
| `perimeter_source` | `return_cant` | `return_cant` consuma, `face` produce | propus `components.return_cant.perimeter_source` | `derived_dependency_confirmed` | lipsa ca field explicit; doar context `quote_geometry.letter_perimeter_m` | da | da | `RETURN_CANT_PERIMETER_MISSING` | nu | dependency ascunsa in root geometry ar falsifica preview-ul | documenteaza si foloseste dependency explicita |
| `perimeter_dependency.face_confirmed_perimeter` | `return_cant` | `face` upstream, `return_cant` dependency | propus `components.return_cant.perimeter_dependency.face_confirmed_perimeter` | `confirmed` | lipsa ca path; doar `geometry.confirmed` / `letter_perimeter_m` | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | nu | nu exista inca dovada explicita ca perimetrul este detinut de face ca truth confirmat | blocker formal pana la dependency path clar |
| `material_profile` | `return_cant` | `return_cant` | propus `components.return_cant.material_profile`; backbone partial `components.return.material` | `confirmed` | missing | da | da | `RETURN_CANT_MATERIAL_MISSING` | nu | registry-ul alege profil material downstream, dar asta nu este truth upstream | adauga field explicit in slice separat |
| `finish_type` | `return_cant` | `return_cant` | propus `components.return_cant.finish_type`; draft `components.returnCant.finishType` | `confirmed` | `hydrated` sau mixed | da | da | `RETURN_CANT_FINISH_MISSING` | partial | finish type exista, dar naming si state nu sunt canonice | unificare path si source_state |
| `color_target.oracal_code` | `return_cant` | `return_cant` | propus `components.return_cant.color_target.oracal_code`; draft `components.returnCant.colorCode` | `confirmed` cand finish_type cere Oracal | `unknown` sau `hydrated` | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | partial | codul actual nu separa clar Oracal de alte target-uri | separare explicita pe subfields |
| `color_target.ral_code` | `return_cant` | `return_cant` | propus `components.return_cant.color_target.ral_code` | `confirmed` cand finish_type cere paint/RAL | missing | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | nu | lipsa separarii RAL inseamna ca color target ramane ambiguu | adauga explicit in contract |
| `color_target.paint_target` | `return_cant` | `return_cant` | propus `components.return_cant.color_target.paint_target` | `confirmed` cand finish_type cere paint | missing | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | nu | fara acesta nu poti spune clar daca tinta este vopsea sau wrap | adauga explicit in contract |
| `layer_group_ids` | `return_cant` | `return_cant` | propus `components.return_cant.layer_group_ids` | `confirmed` sau `derived_dependency_confirmed` | missing ca field; doar layer roles si group finishes separate | da | da | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | nu | lipsa segmentarii pe grupuri poate produce preview eronat pe cant | dependency explicita din layer roles confirmate |
| `confirmation_state` | `return_cant` | `return_cant` | propus `components.return_cant.confirmation_state` | `confirmed` | missing ca field component-scoped; doar `finish_setup.confirmed`, group rows si geometry mixed | da | da | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | nu | confirmarea globala nu echivaleaza cu confirmare de componenta | camp explicit si gating separat |

## 7. Field Classification Verdict

### Ready

Niciun field required nu este in starea `COMPONENT_OWNED_CONFIRMED` pe un path canonic unificat care sa permita singur verdictul `RETURN_CANT_READY_FOR_READONLY_PREVIEW`.

### Partial

- `return_depth_mm`
- `finish_type`
- `color_target.oracal_code` in forma actuala incompleta

### Missing

- `material_profile`
- `perimeter_source`
- `perimeter_dependency.face_confirmed_perimeter` ca path explicit
- `color_target.ral_code`
- `color_target.paint_target`
- `layer_group_ids`
- `confirmation_state`

### Fallback/Hydrated only

- `return_depth_mm`
- `return_finish_type`
- `return_oracal_code` in multe cazuri

### Dependency-only

- `quote_geometry.letter_perimeter_m`
- `geometry.confirmed`
- `svg.selected_layer_group`
- layer role confirmation state

### ProductDefinition-derived only

- `return_profile_linear_meter`
- `layers[].materials.MAT-PROFIL-LATERAL-LITERE-*`
- `line_items.cost_result.materials.return_profile`

Acestea nu sunt primary truth.

## 8. Why The Decision Is Blocked, Not Ready

`return_cant` ramane blocat cu fields explicite deoarece lipsesc simultan trei lucruri obligatorii:

1. un field explicit pentru dependency-ul de perimetru;
2. un field explicit pentru material/profile truth;
3. un field component-scoped pentru confirmation state.

Mai exista si o a patra problema relevanta:

4. color target nu este impartit canonic intre Oracal, RAL si paint target.

Fara acestea, orice preview read-only ar consuma implicit root geometry, fallback-uri sau consecinte ProductDefinition si ar depasi contractul de ownership stabilit anterior.

## 9. What Would Be Needed For Ready

Pentru a schimba verdictul in:

```text
RETURN_CANT_READY_FOR_READONLY_PREVIEW
```

ar trebui dovedite simultan urmatoarele:

- `return_depth_mm` exista pe un path canonic si are state `confirmed`;
- `material_profile` exista ca primary component truth;
- `perimeter_source` exista ca dependency explicita si upstream-ul este confirmat;
- `finish_type` este pe path canonic si confirmat;
- `color_target` este separat explicit pe cazurile necesare;
- `layer_group_ids` exista sau este derivat explicit din layer roles confirmate;
- `confirmation_state` este component-scoped, nu doar global.

## 10. Forbidden Shortcuts For This Slice

Interdictii confirmate:

- nu trata `finishFromPayload()` ca truth confirmat;
- nu trata `geometry.confirmed` ca substitute pentru `face.confirmed_perimeter`;
- nu trata `return_profile_linear_meter` ca dovada ca `material_profile` exista deja in truth;
- nu trata `return_oracal_code` ca reprezentare completa pentru toate color target-urile;
- nu trata confirmarea globala `finish_setup.confirmed` ca `return_cant.confirmation_state`.

## 11. Recommended Next Slice

Prompt recomandat dupa acest document:

```text
TASK — RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT_V1
```

Acest prompt ar trebui sa ramana docs-only si sa defineasca strict:

- dependency path-ul pentru perimetru;
- field-ul `material_profile`;
- split-ul `color_target`;
- field-ul `confirmation_state`;
- regula de derivare pentru `layer_group_ids`.

Abia dupa acel pas, promptul recomandat revine la:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```
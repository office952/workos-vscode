# Form System Component Field Ownership Map

## 1. Purpose

Acest document defineste harta explicita:

```text
component -> field -> source/state -> Product Truth path -> required for calculation -> ProductDefinition consequence
```

Scopul este strict docs-only, read-only, si pregateste slice-ul urmator:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Acest document nu implementeaza preview, UI, API, runtime write behavior, component root, component quote, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB writes, migrations sau seed changes.

## 2. Core Rule

Regula obligatorie:

```text
Component-owned truth before component calculation.
```

Interpretare canonica:

- orice field required pentru calculul unei componente trebuie sa aiba owner de componenta;
- daca field-ul provine din alta componenta, el trebuie marcat ca dependency explicita;
- daca field-ul vine din Product Template, ramane default/fallback pana intra pe component truth path cu source/state clar;
- daca field-ul este UI-only, nu poate fi input de calcul;
- daca field-ul este ProductDefinition-derived, poate fi consequence downstream, nu truth primar.

Forbidden shortcut:

```text
Nu lua date din Product Template si nu le numi component truth.
```

## 3. Field Ownership Classification

### `COMPONENT_OWNED_CONFIRMED`

Field-ul este detinut de componenta, se afla pe component truth path si este confirmat. Poate participa la preview calculabil.

### `COMPONENT_OWNED_PENDING`

Field-ul apartine componentei, dar nu este inca confirmat sau are blocker activ.

### `COMPONENT_OWNED_FALLBACK`

Field-ul apartine componentei ca destinatie, dar valoarea actuala este fallback sau hydrated runtime, deci nu este truth confirmat.

### `DERIVED_DEPENDENCY`

Field-ul este necesar componentei, dar provine explicit din alta componenta sau din geometria radacinii si trebuie pastrat ca dependency declarata.

Exemplu obligatoriu pentru MVP-ul return/cant:

```text
return_cant.perimeter_dependency = face.confirmed_perimeter
```

### `PRODUCT_CONTEXT_ONLY`

Field de context de produs. Poate ajuta afisarea sau boundary-ul, dar nu este truth al componentei.

### `PRODUCT_TEMPLATE_DEFAULT`

Default venit din template sau din Review hydration. Nu devine truth final pana nu ajunge pe component path cu source/state clar.

### `UI_DISPLAY_ONLY`

Valoare afisata in UI sau helper de ecran. Nu poate fi folosita ca input de calcul.

### `PRODUCT_DEFINITION_DERIVED`

Consequence derivata in ProductDefinition sau in quote_input. Poate fi consum downstream, nu input primar.

### `MISSING_COMPONENT_TRUTH`

Camp necesar, dar absent de pe component truth path sau absent ca path unificat in sistem.

## 4. Current Reality Check

Auditul read-only arata trei straturi diferite care trebuie separate clar:

- Form System Backbone defineste owner, source/state, blocker si candidate truth path pentru un subset de fields;
- Product Truth draft builder construieste structuri pe componente, dar foloseste uneori alte path-uri sau chei decat backbone-ul;
- ProductDefinition consuma canonical values si module state, dar nu este owner de truth.

Cea mai importanta constatare pentru acest slice:

```text
Exista ownership partial, dar nomenclatura Product Truth path nu este inca unificata intre backbone, Product Truth draft si consecintele ProductDefinition.
```

Exemple reale observate:

- backbone: `components.return.depth_mm`
- draft builder: `components.returnCant.depthMm`
- backbone: `components.return.material`
- draft builder: nu exista inca material explicit pe `returnCant`
- backbone: `components.finish.target`
- draft builder: `components.finish.finishTarget`

Aceasta nu este o cerinta de implementare in acest task, ci un blocker documentat pentru slice-urile viitoare.

## 5. Component Field Map

Tabelul de mai jos este harta principala ceruta pentru ownership field-by-field. `required_for_preview` si `required_for_calculation_later` sunt evaluate strict pentru component-scoped read-only preview si pentru viitorul calcul controlat, nu pentru quote oficial.

| component | field_key | label | required_for_preview | required_for_calculation_later | current_location | current_owner | target_component_owner | product_truth_path | source_state | classification | product_definition_key | blocker_if_missing | dependency_if_any | can_use_for_return_cant_mvp? | risk | recommended action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| face | `svg.selected_layer_group` | Layer/grup selectat | da | da | backbone + layer role setup | `svg_layer_roles` | `face` | `svg.selected_layer_refs[]` | missing pana la confirmare | `PRODUCT_CONTEXT_ONLY` | indirect in ProductDefinition layer roles | `SELECTED_FACE_LAYER_MISSING` | n/a | nu | fara layer refs, fata si cant raman ancorate in sugestii | cere confirmare operator si mapare explicita spre face/layer ownership |
| face | `face.material` | Material fata | da | da | backbone missing; draft fallback din `finish.face_material_family` | `fallback_default` azi, tinta `face` | `face` | exista azi `components.face.material`; draft real foloseste `components.face.materialFamily` | missing in backbone, fallback in draft | `COMPONENT_OWNED_PENDING` | material role pentru `comp_face_litere` | `FACE_MATERIAL_MISSING` / `FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION` | n/a | nu | fallback-ul poate fi confundat cu truth confirmat | unificare path si confirmare explicita |
| face | `face.thickness_mm` | Grosime fata | partial | da | doar draft builder fallback | `fallback_default` | `face` | propus `components.face.thickness_mm`; real azi `components.face.thicknessMm` | fallback | `COMPONENT_OWNED_FALLBACK` | influenteaza downstream face material/component role | `FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION` | n/a | nu | lipsa path unificat | documenteaza ca path propus si cere slice separat de write/model alignment |
| face | `face.finish_artwork_target` | Tinta finisaj/artwork fata | da | da | backbone missing; draft explicit | `finish_artwork` | `finish` | backbone `components.finish.target`; draft `components.finish.finishTarget` | blocked daca lipseste | `COMPONENT_OWNED_PENDING` | `layers[].components.comp_face_litere` si modul finisaje | `FACE_FINISH_TARGET_MISSING` / `FINISH_TARGET_MISSING` | n/a | partial | tinta de finisaj este critica si azi neuniforma | unificare `target` vs `finishTarget` si confirmare explicita |
| return_cant | `return.depth_mm` | Adancime cant | da | da | backbone hydrated; Review default; draft `returnCant.depthMm` | `return_cant` ca intentie, dar cu valoare hydrated/fallback | `return_cant` | backbone `components.return.depth_mm`; draft `components.returnCant.depthMm` | hydrated sau fallback pana la confirmare | `COMPONENT_OWNED_FALLBACK` | `return_depth_mm` | `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` / `RETURN_CANT_DEPTH_MISSING` | n/a | da, partial | default-ul 60 mm nu este truth confirmat | path unificat + confirmation state separat |
| return_cant | `return.material` | Material/profil cant | da | da | backbone missing; modul registry il implica prin depth gate | `manual_input` lipsa | `return_cant` | backbone `components.return.material`; propus canonical `components.return_cant.material_profile` | missing | `MISSING_COMPONENT_TRUTH` | materiale `MAT-PROFIL-LATERAL-LITERE-*` in `modelare_cant` | `RETURN_CANT_MATERIAL_MISSING` | poate depinde de `return_depth_mm` pentru profil | nu | modulul stie consecinta, dar truth-ul material lipseste | adauga ca path propus si blocker obligatoriu |
| return_cant | `return.perimeter_source` | Sursa perimetru cant | da | da | `quote_geometry.letter_perimeter_m`, module binding, draft geometry | `derived_dependency` | `return_cant` consuma, `face` sau geometry produce | propus `components.return_cant.perimeter_source`; azi doar context `letter_perimeter_m` | hydrated sau confirmed doar daca geometry.confirmed | `DERIVED_DEPENDENCY` | `letter_perimeter_m`, `return_profile_linear_meter` | `RETURN_CANT_PERIMETER_MISSING` | `face.confirmed_perimeter` sau geometry root confirmata | da, cu dependency explicita | mare risc daca este ascuns in Product Template | documenteaza dependency explicita, nu ownership ascuns |
| return_cant | `return.finish_type` | Finisaj cant | da | da | `finish_setup.return_finish_type`, group finishes, draft | `return_cant` | `return_cant` sau `finish` boundary, cu owner clar pentru cant | propus `components.return_cant.finish_type`; azi draft `components.returnCant.finishType` | hydrated daca vine din setup, confirmed daca tot setup.confirmed | `COMPONENT_OWNED_PENDING` | `return_finish_type` | `RETURN_CANT_FINISH_MISSING` | n/a | da, partial | finish-ul cant exista, dar nu are path snake_case unificat | unificare path si confirmation state |
| return_cant | `return.color_target` | Tinta culoare / RAL / Oracal / vopsea | da | da | `finish_setup.return_oracal_code`, `return_finish_type`, group finishes | astazi partial intre `return_cant` si `finish` | `return_cant` pentru MVP | propus `components.return_cant.color_target`; draft real `components.returnCant.colorCode` | unknown sau hydrated | `COMPONENT_OWNED_PENDING` | material/finisaj downstream in `modelare_cant` | `RETURN_CANT_COLOR_TARGET_MISSING` | depinde de `return.finish_type` | da, partial | codul de culoare nu distinge inca clar Oracal vs RAL vs vopsea la nivel de truth path | documenteaza path propus si gating pe finish_type |
| return_cant | `return.layer_group_ids` | Layer/grupuri pentru cant | partial | da | layer role setup si letter_group_finishes | `product_context` astazi | `return_cant` | propus `components.return_cant.layer_group_ids` | suggested sau hydrated | `MISSING_COMPONENT_TRUTH` | influenteaza consecinte pe group finish rows | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | depinde de layer roles confirmate | partial | lipsa group source face segmentarea preview-ului neclara | propune path si marker de dependency din layer roles |
| return_cant | `return.confirmation_state` | Stare confirmare operator | da | da | implicit in `finish_setup.confirmed`, group confirmations, geometry.confirmed | `product_context` | `return_cant` | propus `components.return_cant.confirmation_state` | mixed | `MISSING_COMPONENT_TRUTH` | downstream readiness only | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | depinde de depth/finish/color/perimeter | da, ca blocker, nu ca value | lipseste un camp component-scoped de confirmare | propune camp explicit, fara implementare |
| back | `back.backing_mode` | Mod spate | da | da | `finish_setup.backing_mode`, draft `back.backingMode` | `back` cu hydration | `back` | propus `components.back.backing_mode`; real `components.back.backingMode` | hydrated/fallback | `COMPONENT_OWNED_FALLBACK` | `backing_mode` | `BACKING_MODE_CONFIRMATION_REQUIRED` | n/a | nu | spatele ramane partial dependent de fallback | unificare naming si confirmare |
| back | `back.material` | Material spate | partial | da | draft only, derivat din backing mode | `derived_dependency` | `back` | real `components.back.material` | hydrated prin alias | `COMPONENT_OWNED_PENDING` | `backing_mode` consequence | `BACK_MATERIAL_MISSING` | depinde de `backing_mode` | nu | materialul este prea implicit | documenteaza ca blocker pana la camp explicit |
| back | `back.bevel_enabled` | Bevel spate | partial | partial | finish_setup + draft | `back` | `back` | propus `components.back.bevel_enabled`; real `components.back.bevelEnabled` | manual/hydrated | `COMPONENT_OWNED_PENDING` | `back_bevel_enabled` | optional, dar neconfirmat | n/a | nu | nu este blocant pentru return MVP | mentine ca optional/context |
| lighting | `lighting.type` | Tip iluminare | context | da | backbone fallback + Review default + draft | `lighting_led` cu fallback | `lighting` | backbone `components.lighting.illumination_type`; draft `components.lighting.lightingSystemType` | fallback/hydrated | `COMPONENT_OWNED_FALLBACK` | `lighting_system_type` | `LIGHTING_MODE_CONFIRMATION_REQUIRED` | n/a | nu | camp important, dar neconfirmat si nealiniat ca nume | nu intra in return MVP; pastreaza debt-ul documentat |
| lighting | `lighting.led_module_count` | Numar module LED | nu | da | finish_setup + draft electrical | `lighting/electrical` | `lighting` | propus `components.lighting.led_module_count` | unknown/hydrated | `COMPONENT_OWNED_PENDING` | `led_module_count` | `LIGHTING_LED_COUNT_MISSING` | depinde de geometry si mode | nu | poate parea complet doar pentru ca este afisat in UI | exclude din return MVP |
| lighting | `lighting.strategy_profile` | Profil strategie LED | nu | context | backbone only | `product_system_contract` | `lighting` ca context, nu truth primar | `components.lighting.strategy_profile` | warning | `PRODUCT_CONTEXT_ONLY` | contract/reference only | none | n/a | nu | foarte usor de confundat cu input de calcul | marcheaza explicit ca non-primary truth |
| finish | `finish.finish_target` | Tinta finisaj | da | da | backbone + draft | `finish_artwork` | `finish` | backbone `components.finish.target`; draft `components.finish.finishTarget` | blocked sau pending | `COMPONENT_OWNED_PENDING` | modul `finisaje`, `letter_group_finishes` | `FINISH_TARGET_MISSING` | poate depinde de face/return/artwork scope | partial | naming dublu si target implicit in UI | unificare path si boundary finish/artwork |
| finish | `finish.print_required` | Necesar print | nu pentru return MVP | da | derivat din artwork rows in draft | `finish/artwork` | `finish` sau `artwork` child | real `components.finish.printRequired` | hydrated/manual | `COMPONENT_OWNED_PENDING` | artwork/finish downstream only | `PRINT_REQUIRED_UNKNOWN` | depinde de artwork decisions | nu | este derivat din execution_type, inca necanonic | pastreaza separat de return MVP |
| finish | `finish.lamination_required` | Necesara laminare | nu pentru return MVP | da | derivat din artwork rows in draft | `finish/artwork` | `finish` sau `artwork` child | real `components.finish.laminationRequired` | hydrated/manual | `COMPONENT_OWNED_PENDING` | artwork/finish downstream only | `LAMINATION_REQUIRED_UNKNOWN` | depinde de artwork decisions | nu | nu este relevant pentru return cant MVP | exclude din MVP |
| premount_support | `mounting.support_option` | Optiune montaj/suport | context | da | backbone hydrated + Review default | `mounting_support` cu hydration | `mounting` | backbone `components.mounting.system`; draft `components.mounting.mountingSystem` | hydrated/fallback | `COMPONENT_OWNED_FALLBACK` | `mounting_system` | `MOUNTING_SYSTEM_CONFIRMATION_REQUIRED` | n/a | nu | nu trebuie reciclat drept support truth | mentine separat de support |
| premount_support | `support.support_required` | Suport necesar | nu pentru return MVP | da | draft only, din `support_required` sau bridge | `derived_dependency` sau unknown | `support` | real `components.support.supportRequired` | suggested/unknown | `MISSING_COMPONENT_TRUTH` | `metal_support_required` consequence only | `SUPPORT_REQUIRED_UNKNOWN` | poate veni din mounting bridge sau SVG evidence | nu | exemplul clasic de bridge necanonic | cere first-class support field separat |
| premount_support | `quote_input.metal_support_required` | Trigger suport metal derivat | nu | nu ca truth primar | quote_input/ProductDefinition canonical values | `product_definition_derived` | niciun owner de componenta | nu este component truth path | derived_readonly | `PRODUCT_DEFINITION_DERIVED` | `metal_support_required` | n/a | derivat din `mounting_system` | nu | nu trebuie confundat cu support truth | marcheaza permanent ca derived consequence, nu input primar |
| logo_linked_child | `linked_templates.logo` | Context logo linked child | nu | context | linked composition metadata | `product_context` | `logo_linked_child` doar ca context | `linked_templates.logo` | suggested/readonly | `PRODUCT_CONTEXT_ONLY` | linked runtime segments | `LOGO_NOT_OFFERABLE` daca e tratat ca root | depinde de letters root | nu | risc major de a confunda context cu offerability | mentine blocat pentru root/quote |
| product_context | `root.template_code` | Root template | da ca boundary | da ca boundary | workspace payload / backbone root | `product_context` | `product_context` | `metadata.templateCode` sau backbone root | hydrated | `PRODUCT_CONTEXT_ONLY` | root binding context | `ROOT_NOT_OWNER_VALID` | n/a | nu | boundary numai, nu input de calcul component | pastreaza doar ca badge / guard |
| product_context | `quote_geometry.letter_perimeter_m` | Perimetru litere root | da pentru cant, dar numai ca dependency | da | quote_geometry + modular bindings | `derived_dependency` | `face` produce / `return_cant` consuma | nu este inca path component-owned clar | hydrated sau confirmed daca geometry.confirmed | `DERIVED_DEPENDENCY` | `letter_perimeter_m` | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | `face.confirmed_perimeter` | da, ca dependency | daca ramane root-only, preview-ul cant nu este onest | cere dependency path explicit |

## 6. Return/Cant MVP Field Map

MVP-ul viitor pentru `return_cant` trebuie sa ramana read-only si sa lucreze numai cu campurile minime necesare pentru preview scoped.

### Verdict rapid pe campurile MVP

| field | este component-owned acum? | este confirmed? | este fallback/hydrated? | este derivat din face/root? | este UI-only? | este ProductDefinition-derived? | ce lipseste pentru read-only preview? |
|---|---|---|---|---|---|---|---|
| `return_depth_mm` | partial | nu garantat | da | nu | nu | nu | confirmation state separat si path unificat |
| `perimeter_source` | nu ca field propriu | depinde de geometry.confirmed | da, prin geometry | da | nu | nu | dependency explicita `face.confirmed_perimeter` sau path echivalent |
| `material_profile` | nu | nu | n/a | depinde de depth gate | nu | consecinta modul, nu truth | field propriu pe component truth path |
| `finish_type` | partial | nu garantat | da | nu | nu | nu | path unificat si confirmare |
| `color_target` | partial | nu | da/unknown | depinde de finish type | nu | nu | distinctie clara RAL vs Oracal vs vopsea |
| `layer_group_ids` | nu | nu | suggested/hydrated | da, din layer roles | nu | nu | mapare explicita catre cant |
| `confirmation_state` | nu | nu | mixed | poate ingloba root confirm | nu | nu | field explicit de componenta |

### Return/Cant MVP verdict

Fields gata doar partial:

- `return_depth_mm`
- `return_finish_type`
- `return_oracal_code` sau echivalent color code

Fields care exista doar ca dependency/context:

- `letter_perimeter_m`
- `svg.selected_layer_group`
- `geometry.confirmed`

Fields lipsa ca truth de componenta:

- `material_profile`
- `perimeter_source`
- `layer_group_ids`
- `confirmation_state`

Concluzie:

```text
return_cant nu este blocked architectural, dar nu este inca ready_for_readonly_preview fara formalizarea dependency path-ului pentru perimetru si fara primul set de fields component-owned lipsa.
```

## 7. Product Truth Path Contract

Tabelul de mai jos propune nomenclatura canonica pentru return/cant, dar marcheaza clar daca path-ul exista deja in cod sau este doar propus.

| canonical_path | status | realitatea curenta in cod | fallback? | confirmed? | required pentru MVP? | cine il scrie in viitor | cine il consuma downstream |
|---|---|---|---|---|---|---|---|
| `components.return_cant.return_depth_mm` | propus | backbone are `components.return.depth_mm`; draft are `components.returnCant.depthMm` | da | nu garantat | da | viitor Product Truth write layer, nu in acest task | preview return_cant, ProductDefinition `return_depth_mm`, modul `modelare_cant` |
| `components.return_cant.perimeter_source` | propus | azi doar `quote_geometry.letter_perimeter_m` + dependency implicita | da | doar daca geometry.confirmed | da | viitor dependency mapper | preview return_cant, ProductDefinition trace, module cost context |
| `components.return_cant.material_profile` | propus | backbone are `components.return.material`; draft nu are material explicit | n/a | nu | da | viitor form truth writer | `modelare_cant`, material role selection |
| `components.return_cant.finish_type` | propus | draft `components.returnCant.finishType`; backbone `return_finish_type` | da | nu garantat | da | viitor Product Truth write layer | `modelare_cant`, finish gate |
| `components.return_cant.color_target` | propus | draft `components.returnCant.colorCode`; setup `return_oracal_code` | da/unknown | nu | da | viitor Product Truth write layer | finisaj/material consequences |
| `components.return_cant.layer_group_ids` | propus | azi layer roles si group finishes sunt separate | n/a | nu | da | viitor layer-to-component mapper | scoped preview rows, finish routing |
| `components.return_cant.confirmation_state` | propus | azi doar confirmari dispersate in `finish_setup.confirmed`, group rows, geometry | n/a | mixed | da | viitor Product Truth write layer | readiness gating |

Regula de contract:

- pentru MVP, un path poate fi folosit doar daca este `COMPONENT_OWNED_CONFIRMED` sau `DERIVED_DEPENDENCY` cu upstream confirmat;
- `PRODUCT_TEMPLATE_DEFAULT`, `UI_DISPLAY_ONLY` si `PRODUCT_DEFINITION_DERIVED` nu deblocheaza preview calculabil.

## 8. Dependency Rules

### Reguli obligatorii

1. Daca un field apartine altei componente, el trebuie modelat ca dependency explicita.
2. Daca un field vine din root geometry, trebuie sa existe source/state si owner clar pentru componenta care il consuma.
3. Product Template poate oferi default-uri, dar nu poate masca truth-ul final.
4. ProductDefinition poate consuma consecinte, dar nu poate deveni owner de input primar.
5. UI poate afisa sau overlay-ui valori, dar nu schimba backbone truth de una singura.

### Dependency canonica pentru return/cant

Forma recomandata:

```text
components.return_cant.perimeter_source = {
  dependency_kind: "face_geometry",
  source_path: "components.face.confirmed_perimeter",
  fallback_context_path: "quote_geometry.letter_perimeter_m",
  source_state: "confirmed"
}
```

Acest task nu implementeaza structura de mai sus. O documenteaza ca regula minima pentru slice-ul urmator.

## 9. Blockers And Readiness Rules

### Minimum blockers pentru return/cant preview

- `RETURN_CANT_DEPTH_MISSING`
- `RETURN_CANT_PERIMETER_MISSING`
- `RETURN_CANT_MATERIAL_MISSING`
- `RETURN_CANT_FINISH_MISSING`
- `RETURN_CANT_COLOR_TARGET_MISSING`
- `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED`
- `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`
- `COMPONENT_ROOT_BLOCKED`
- `COMPONENT_QUOTE_BLOCKED`

### Readiness levels

#### `blocked`

Lipsesc inputuri required sau boundary-ul este invalid.

#### `partial_ready`

Exista unele inputuri folosibile pentru diagnostic, dar cel putin un field required este pending, fallback sau dependency neconfirmata.

#### `ready_for_readonly_preview`

Toate inputurile minime sunt prezente, source/state este clar, iar dependency-urile sunt explicite si confirmate. Nu inseamna pret oficial.

#### `ready_for_future_calculation`

Componenta este complet pregatita pentru calcul viitor owner-approved in afara acestui task. Nu inseamna component root sau component quote.

### Readiness verdict actual pentru return/cant

```text
partial_ready
```

Motiv:

- adancimea si finisajul exista partial;
- perimetrul exista doar ca dependency root/face, nu ca dependency path explicita;
- material_profile si confirmation_state lipsesc ca truth de componenta.

## 10. UI Contract For Future Preview

Acesta este contract de UI, nu implementare.

Pentru `return_cant` preview, UI-ul viitor trebuie sa afiseze:

- component scope badge: `Cant / lateral`
- root badge: `TPL-VOLUMETRIC-LETTERS_v2`
- boundary badges:
  - `read-only`
  - `no component root`
  - `no component quote`
  - `no order`
  - `no execution`
- field table:
  - `field`
  - `value`
  - `source/state`
  - `Product Truth path`
  - `blocker/warning`
- outputs preview:
  - `perimeter`
  - `cant height`
  - `material/profile`
  - `finish/color`
  - `operation trace: modelare_cant / bonding / finish`
- explicit label:
  - `no official price`
- interdictii:
  - fara CTA pentru quote
  - fara CTA pentru order
  - fara CTA pentru execution

Note obligatorii:

- orice valoare `hydrated` sau `fallback` trebuie afisata ca neconfirmata;
- orice valoare dependency trebuie sa arate upstream owner-ul;
- orice valoare ProductDefinition-derived trebuie afisata doar ca downstream consequence.

## 11. Forbidden Shortcuts

Sunt interzise urmatoarele shortcut-uri:

- folosirea `finishFromPayload()` defaults ca si cum ar fi truth confirmat;
- folosirea `quote_input.metal_support_required` ca support truth primar;
- folosirea `ProductDefinition canonical values` ca dovada de ownership;
- folosirea `linked_templates.logo` ca argument pentru root sau quote readiness;
- ascunderea perimetrului return/cant in product root fara dependency explicita;
- tratarea overlay-urilor runtime din UI ca dovada de truth confirmat.

## 12. Recommended Next Slice

Prompt recomandat:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Boundary minim recomandat pentru acel slice:

- fara component root;
- fara component quote;
- fara write Product Truth nou in acelasi pas, daca owner nu da GO separat;
- numai read-only preview;
- folosire stricta a field map-ului si blocker-elor documentate aici.
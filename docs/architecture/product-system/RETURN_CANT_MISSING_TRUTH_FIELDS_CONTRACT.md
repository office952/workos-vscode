# Return Cant Missing Truth Fields Contract

## 1. Purpose

Acest document defineste contractul strict pentru field-urile lipsa necesare ca `return_cant` sa devina candidat real pentru un component-scoped read-only preview in boundary-ul curent.

Boundary-ul ramane neschimbat:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = pregatire pentru read_only_preview
```

Acest document nu implementeaza preview runtime, nu calculeaza componenta, nu creeaza endpoint, nu activeaza component root, nu activeaza component quote si nu modifica Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB, seeds sau migrations.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_TRUTH_FIELDS_CONTRACT_READY
```

Clarificare importanta:

- contractul pentru field-urile lipsa este gata;
- runtime-ul `return_cant` nu devine prin asta gata pentru preview;
- runtime-ul ramane blocat pana cand campurile si dependency path-urile documentate aici exista efectiv in sistem.

## 3. Contract Rule

Regula obligatorie:

```text
Un field required pentru return_cant preview trebuie sa fie fie component-owned confirmed, fie dependency explicita confirmed.
```

Nu sunt acceptate ca truth final:

- fallback;
- hydrated;
- suggested;
- ProductDefinition-derived consequences;
- UI display-only values.

## 4. Canonical Missing Fields

Field-urile lipsa care trebuie definite contractual sunt:

- `material_profile`
- `perimeter_source`
- `perimeter_dependency.face_confirmed_perimeter`
- `color_target.oracal_code`
- `color_target.ral_code`
- `color_target.paint_target`
- `layer_group_ids`
- `confirmation_state`

Context existing but insufficient:

- `return_depth_mm`
- `return_finish_type`
- `return_oracal_code`
- `quote_geometry.letter_perimeter_m`
- `geometry.confirmed`
- `svg.selected_layer_group`

## 5. Contract Per Field

### 5.1 `material_profile`

Canonical field key:

```text
return_cant.material_profile
```

Canonical Product Truth path:

```text
components.return_cant.material_profile
```

Owner:

```text
return_cant
```

Source candidates permise:

- operator manual selection;
- future structured selection derived from allowed profile families for cant;
- optional future policy mapper that narrows valid profiles from `return_depth_mm`.

Source candidates nepermise ca truth final:

- mini-module registry material consequence singura;
- ProductDefinition output materials;
- implicit depth gate fara field explicit.

Allowed source states:

- `manual_pending`
- `confirmed`
- `blocked`

Required confirmation state:

- `confirmed`

Relatia cu Product Template defaults:

- Product Template poate sugera familia de profil compatibila cu adancimea;
- nu poate scrie truth final doar prin default sau prin downstream consequence.

Blocker daca lipseste:

```text
RETURN_CANT_MATERIAL_MISSING
```

ProductDefinition consequence:

- selectia materialelor `MAT-PROFIL-LATERAL-LITERE-*`;
- outputs legate de `return_profile_linear_meter`;
- downstream lines pentru `materials.return_profile`.

Implementation action:

- adauga field explicit in viitorul read-only mapper / Product Truth writer slice;
- nu deriva truth-ul direct din `modelare_cant` outputs.

### 5.2 `perimeter_source`

Canonical field key:

```text
return_cant.perimeter_source
```

Canonical Product Truth path:

```text
components.return_cant.perimeter_source
```

Owner:

```text
return_cant
```

Rol:

- acest field nu detine valoarea geometrica in sine;
- el detine declaratia canonica despre sursa dependentei de perimetru.

Sursa permisa:

- `face.confirmed_perimeter` ca dependency explicita;
- doar temporar ca context fallback: `quote_geometry.letter_perimeter_m`, dar fara a debloca preview-ul.

Regula obligatorie:

```text
return_cant.perimeter_dependency = face.confirmed_perimeter
```

Allowed source states:

- `suggested`
- `hydrated`
- `manual_pending`
- `confirmed`
- `blocked`

Required confirmation state pentru preview:

- `confirmed`

Blocker daca lipseste:

```text
RETURN_CANT_PERIMETER_MISSING
```

ProductDefinition consequence:

- foloseste `letter_perimeter_m` pentru `return_profile_linear_meter`;
- alimenteaza downstream `RETURN_PROFILE_MACHINE_FORMING` trace;
- nu devine owner de truth prin ProductDefinition.

Implementation action:

- mapare explicita intre source path si dependency metadata;
- fallback-ul root geometry ramane doar context de warning.

### 5.3 `perimeter_dependency.face_confirmed_perimeter`

Canonical field key:

```text
return_cant.perimeter_dependency.face_confirmed_perimeter
```

Canonical Product Truth path:

```text
components.return_cant.perimeter_dependency.face_confirmed_perimeter
```

Owner:

```text
derived_dependency
```

Required source state:

- `confirmed`

Ce se intampla daca exista doar root geometry:

- se poate afisa `fallback_context_path = quote_geometry.letter_perimeter_m`;
- verdictul ramane `blocked` sau `partial_ready`, nu preview ready.

Ce se intampla daca exista doar SVG suggestion:

- verdictul ramane `blocked`;
- suggestion-ul nu este suficient pentru dependency geometry truth.

Blocker daca nu exista confirmed perimeter:

```text
RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED
```

ProductDefinition consequence:

- permite rationale trace pentru `letter_perimeter_m` consumption;
- nu inlocuieste source owner-ul face.

Implementation action:

- dependency path explicit in read-only mapper slice;
- fara a reinventa geometry ownership in ProductDefinition.

### 5.4 `color_target`

Color target trebuie impartit explicit in trei subfields canonice.

#### `color_target.oracal_code`

Canonical field key:

```text
return_cant.color_target.oracal_code
```

Canonical Product Truth path:

```text
components.return_cant.color_target.oracal_code
```

Aplicabilitate:

- aplicabil cand `finish_type` cere wrap / Oracal.

Allowed source states:

- `hydrated`
- `manual_pending`
- `confirmed`
- `blocked`

Required state pentru preview:

- `confirmed`

Blocker daca finish-ul cere Oracal si codul lipseste:

```text
RETURN_CANT_COLOR_TARGET_MISSING
```

#### `color_target.ral_code`

Canonical field key:

```text
return_cant.color_target.ral_code
```

Canonical Product Truth path:

```text
components.return_cant.color_target.ral_code
```

Aplicabilitate:

- aplicabil cand `finish_type` cere RAL / paint.

Allowed source states:

- `manual_pending`
- `confirmed`
- `blocked`

Required state pentru preview:

- `confirmed`

Blocker daca finish-ul cere RAL si codul lipseste:

```text
RETURN_CANT_COLOR_TARGET_MISSING
```

#### `color_target.paint_target`

Canonical field key:

```text
return_cant.color_target.paint_target
```

Canonical Product Truth path:

```text
components.return_cant.color_target.paint_target
```

Aplicabilitate:

- aplicabil cand `finish_type` cere vopsire, dar nu doar un cod Oracal.

Allowed source states:

- `manual_pending`
- `confirmed`
- `blocked`

Required state pentru preview:

- `confirmed`

Blocker daca finish-ul cere paint target si acesta lipseste:

```text
RETURN_CANT_COLOR_TARGET_MISSING
```

#### Exclusivitate

Regula de exclusivitate:

- `oracal_code`, `ral_code` si `paint_target` sunt alternative conditionale;
- exact subsetul cerut de `finish_type` trebuie sa fie `confirmed`;
- celelalte pot fi `not_required`.

ProductDefinition consequence pentru color target:

- determina material role si operation trace pentru paint vs wrap;
- nu reprezinta singur source of truth daca nu exista `finish_type` confirmat.

Implementation action:

- split explicit al `color_target` in mapper slice;
- nu reosi o singura cheie `colorCode` pentru toate modurile.

### 5.5 `layer_group_ids`

Canonical field key:

```text
return_cant.layer_group_ids
```

Canonical Product Truth path:

```text
components.return_cant.layer_group_ids
```

Owner:

```text
return_cant
```

Legatura cu SVG/layer groups:

- se alimenteaza din layer/group roles operator-confirmed;
- poate folosi `letter_group_finishes` numai ca material de context, nu ca dovada suficienta de truth.

Diferenta intre suggested layer si operator-confirmed layer group:

- `suggested` inseamna doar analyzer hint;
- `operator-confirmed` inseamna group assignment valid pentru truth.

Allowed source states:

- `suggested`
- `manual_pending`
- `confirmed`
- `blocked`

Required state pentru preview:

- `confirmed`

Blocker daca exista doar analyzer suggestion:

```text
RETURN_CANT_LAYER_GROUP_SOURCE_MISSING
```

ProductDefinition consequence:

- segmentare corecta a group-specific finish/depth inputs;
- evita preview-ul care combina grupuri gresit.

Implementation action:

- dependency explicita din `svg.selected_layer_refs[]` si din layer roles confirmate;
- nu trata `groupFinishes.confirmed` singur ca substitute pentru source mapping.

### 5.6 `confirmation_state`

Canonical field key:

```text
return_cant.confirmation_state
```

Canonical Product Truth path:

```text
components.return_cant.confirmation_state
```

Owner:

```text
return_cant
```

Valori permise:

- `unconfirmed`
- `suggested`
- `hydrated`
- `fallback`
- `manual_pending`
- `confirmed`
- `blocked`

Regula obligatorie:

```text
doar confirmation_state = confirmed poate debloca component read-only preview
```

Cum se calculeaza semantic:

- `unconfirmed`: field-urile minime nu au fost inca evaluate;
- `suggested`: exista doar analyzer/UI suggestion;
- `hydrated`: valoare prezenta din payload/runtime, dar neconfirmata;
- `fallback`: valoare provenita din default;
- `manual_pending`: operatorul a atins/selectat date, dar nu exista confirmare canonica finala;
- `confirmed`: toate inputurile required sunt confirmate si dependency-urile sunt explicite;
- `blocked`: lipseste cel putin un input required sau dependency required.

Blocker daca lipseste sau nu este `confirmed`:

```text
RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED
```

ProductDefinition consequence:

- doar permite consum downstream safe;
- nu produce el insusi confirmarea.

Implementation action:

- camp agregat component-scoped in viitorul mapper sau Product Truth writer slice.

## 6. Mandatory Table

| field_key | product_truth_path | owner | source_state_required | current_state | required_for_preview | required_for_calculation_later | blocker_if_missing | product_definition_consequence | implementation_action |
|---|---|---|---|---|---|---|---|---|---|
| `return_cant.material_profile` | `components.return_cant.material_profile` | `return_cant` | `confirmed` | `missing` | da | da | `RETURN_CANT_MATERIAL_MISSING` | selecteaza material roles `MAT-PROFIL-LATERAL-LITERE-*` | field explicit nou |
| `return_cant.perimeter_source` | `components.return_cant.perimeter_source` | `return_cant` | `confirmed` dependency metadata | `missing` | da | da | `RETURN_CANT_PERIMETER_MISSING` | justifica `letter_perimeter_m` consumption | dependency metadata explicita |
| `return_cant.perimeter_dependency.face_confirmed_perimeter` | `components.return_cant.perimeter_dependency.face_confirmed_perimeter` | `derived_dependency` | `confirmed` | `missing` | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | trace pentru `return_profile_linear_meter` | dependency path explicit |
| `return_cant.color_target.oracal_code` | `components.return_cant.color_target.oracal_code` | `return_cant` | `confirmed` cand necesar | `partial` | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | wrap material/operation routing | split explicit din `colorCode` |
| `return_cant.color_target.ral_code` | `components.return_cant.color_target.ral_code` | `return_cant` | `confirmed` cand necesar | `missing` | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | paint routing | field explicit nou |
| `return_cant.color_target.paint_target` | `components.return_cant.color_target.paint_target` | `return_cant` | `confirmed` cand necesar | `missing` | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` | paint semantics complete | field explicit nou |
| `return_cant.layer_group_ids` | `components.return_cant.layer_group_ids` | `return_cant` | `confirmed` | `missing` | da | da | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | group-scoped finish/depth consequence | mapping explicit din layer roles |
| `return_cant.confirmation_state` | `components.return_cant.confirmation_state` | `return_cant` | `confirmed` | `missing` | da | da | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | readiness gating | field agregat nou |

## 7. Entry Rule For Read-Only Preview

`return_cant` poate intra in read-only preview numai daca:

- `return_depth_mm` este `confirmed`;
- `material_profile` este `confirmed`;
- `finish_type` este `confirmed` sau explicit `not_required`;
- `color_target` este `confirmed` daca finish-ul il cere;
- `layer_group_ids` sunt operator-confirmed;
- `confirmation_state = confirmed`;
- `face.confirmed_perimeter` este disponibil ca dependency explicita;
- niciun fallback/hydrated value nu este folosit ca truth final.

## 8. Remaining Runtime Blockers

Desi contractul este gata, runtime-ul ramane blocat pana cand exista implementare pentru:

- `material_profile`
- `perimeter_source`
- `perimeter_dependency.face_confirmed_perimeter`
- split complet `color_target`
- `layer_group_ids`
- `confirmation_state`

## 9. Recommended Next Slice

Prompt recomandat dupa acest contract:

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_SLICE_V1
```

Reason:

- contractul lipsurilor este acum explicit si suficient de precis;
- urmatorul pas poate implementa doar mapper-ul read-only pentru aceste fields, fara preview complet, fara UI nou si fara runtime commercial side effects.
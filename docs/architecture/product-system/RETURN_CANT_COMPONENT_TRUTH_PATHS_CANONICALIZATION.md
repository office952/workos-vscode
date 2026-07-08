# Return Cant Component Truth Paths Canonicalization

## 1. Purpose

Acest document canonizeaza path-urile Product Truth minime pentru `return_cant` si dependency-ul explicit pe `face`, astfel incat un viitor mapper read-only sa poata raporta onest field-urile componentei fara sa inventeze truth din fallback, hydrated state, SVG suggestion sau ProductDefinition-derived consequences.

Boundary-ul acestui slice ramane strict:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = truth_paths_canonicalization
```

Acest document nu implementeaza:

- component root;
- component quote;
- official price;
- commercial preview;
- order;
- execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- UI nou;
- endpoint public nou;
- DB writes, seeds sau migrations.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_CANONICAL_PATHS_READY_FOR_MAPPER_IMPLEMENTATION
```

Clarificare importanta:

- runtime-ul nu are inca aceste path-uri implementate complet;
- dar schema canonica este acum suficient de precisa pentru urmatorul pas de implementare a mapperului read-only;
- aceasta decizie nu inseamna `preview ready` si nu inseamna `calculation ready`.

## 3. Canonicalization Rule

Regula obligatorie:

```text
Product Template poate compune si poate da defaults sau hydration,
dar truth-ul tehnic final pentru return_cant trebuie sa stea pe component-owned paths,
iar dependency-urile de la alte componente trebuie exprimate explicit.
```

Consecinte:

- `fallback` poate fi afisat, dar nu deblocheaza readiness;
- `hydrated` poate fi afisat, dar nu deblocheaza readiness;
- `SVG suggestion` poate fi afisat, dar nu deblocheaza readiness;
- `ProductDefinition-derived` poate fi afisat doar ca downstream consequence;
- root geometry poate ramane evidence/context, nu owner de truth pentru componenta.

## 4. Canonical Root Schema

Schema canonica pentru `return_cant` este:

```text
components.return_cant
  depth_mm
  material_profile
  finish_type
  color_target
    oracal_code
    ral_code
    paint_target
  layer_group_ids
  confirmation_state
  perimeter_source
  perimeter_dependency
    face_confirmed_perimeter
      value
      unit
      source_state
      source_path
      confirmed_at
      confirmed_by
```

Schema canonica pentru dependency-ul pe `face` este:

```text
components.face.confirmed_perimeter
  value
  unit
  source_state
  source_path
  layer_group_ids
  confirmation_state
```

## 5. Canonical Paths Inventory

### 5.1 Return cant component-owned paths

| canonical_path | owner component | source allowed | source_state required | fallback allowed | ProductDefinition-derived allowed as primary truth | SVG suggestion allowed as primary truth | required for mapper | required for preview later | blocker if missing |
|---|---|---|---|---|---|---|---|---|---|
| `components.return_cant.depth_mm` | `return_cant` | operator-confirmed finish/setup input | `confirmed` | da | nu | nu | da | da | `RETURN_CANT_DEPTH_MISSING` sau `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` |
| `components.return_cant.material_profile` | `return_cant` | operator selection sau future constrained selection | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_MATERIAL_MISSING` |
| `components.return_cant.finish_type` | `return_cant` | operator-confirmed finish input | `confirmed` | da | nu | nu | da | da | `RETURN_CANT_FINISH_MISSING` |
| `components.return_cant.color_target.oracal_code` | `return_cant` | operator-confirmed color target | `confirmed` cand finish cere Oracal | da | nu | nu | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `components.return_cant.color_target.ral_code` | `return_cant` | operator-confirmed color target | `confirmed` cand finish cere RAL | nu | nu | nu | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `components.return_cant.color_target.paint_target` | `return_cant` | operator-confirmed paint target | `confirmed` cand finish cere paint | nu | nu | nu | da | da | `RETURN_CANT_COLOR_TARGET_MISSING` |
| `components.return_cant.layer_group_ids` | `return_cant` | operator-confirmed layer/group selection mapped catre componenta | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` |
| `components.return_cant.confirmation_state` | `return_cant` | component-scoped readiness gate rezultat din inputs confirmed | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` |
| `components.return_cant.perimeter_source` | `return_cant` | dependency declaration catre face perimeter | `confirmed` | da, doar context | nu | nu | da | da | `RETURN_CANT_PERIMETER_MISSING` |

### 5.2 Return cant explicit dependency path

| canonical_path | owner component | source allowed | source_state required | fallback allowed | ProductDefinition-derived allowed as primary truth | SVG suggestion allowed as primary truth | required for mapper | required for preview later | blocker if missing |
|---|---|---|---|---|---|---|---|---|---|
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.value` | `derived_dependency` from `face` | `components.face.confirmed_perimeter.value` | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.unit` | `derived_dependency` from `face` | same dependency object | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.source_state` | `derived_dependency` from `face` | same dependency object | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.source_path` | `derived_dependency` from `face` | same dependency object | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.confirmed_at` | `derived_dependency` from `face` | same dependency object | `confirmed` | nu | nu | nu | nu | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.return_cant.perimeter_dependency.face_confirmed_perimeter.confirmed_by` | `derived_dependency` from `face` | same dependency object | `confirmed` | nu | nu | nu | nu | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |

### 5.3 Face upstream dependency source

| canonical_path | owner component | source allowed | source_state required | fallback allowed | ProductDefinition-derived allowed as primary truth | SVG suggestion allowed as primary truth | required for mapper | required for preview later | blocker if missing |
|---|---|---|---|---|---|---|---|---|---|
| `components.face.confirmed_perimeter.value` | `face` | operator-confirmed geometry read model | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.face.confirmed_perimeter.unit` | `face` | operator-confirmed geometry read model | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.face.confirmed_perimeter.source_state` | `face` | operator-confirmed geometry read model | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.face.confirmed_perimeter.source_path` | `face` | operator-confirmed geometry read model | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |
| `components.face.confirmed_perimeter.layer_group_ids` | `face` | confirmed selected layer refs for face-owned groups | `confirmed` | nu | nu | nu | da | da | `SELECTED_FACE_LAYER_MISSING` |
| `components.face.confirmed_perimeter.confirmation_state` | `face` | face geometry confirmation gate | `confirmed` | nu | nu | nu | da | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` |

## 6. Runtime Mapping Status

### 6.1 Paths existente in runtime, dar necanonice sau incomplete

| runtime reality | status fata de schema canonica |
|---|---|
| `components.return.depth_mm` in backbone | exista, dar cu component key si naming necanonice |
| `components.returnCant.depthMm` in Product Truth draft | exista, dar camelCase si fara schema `components.return_cant.*` |
| `finish_setup.return_finish_type` | exista doar ca source input/hydration, nu path canonical final |
| `finish_setup.return_oracal_code` | exista doar partial pentru un subcaz color target |
| `quote_geometry.letter_perimeter_m` | exista ca root geometry evidence/context |
| `svg.selected_layer_refs[]` | exista ca owner-valid selection gate, dar nu e mapat inca la `components.return_cant.layer_group_ids` |

### 6.2 Paths lipsa complet in runtime

- `components.return_cant.material_profile`
- `components.return_cant.finish_type` ca snake_case canonical path
- `components.return_cant.color_target.oracal_code`
- `components.return_cant.color_target.ral_code`
- `components.return_cant.color_target.paint_target`
- `components.return_cant.layer_group_ids`
- `components.return_cant.confirmation_state`
- `components.return_cant.perimeter_source`
- `components.return_cant.perimeter_dependency.face_confirmed_perimeter.*`
- `components.face.confirmed_perimeter.*`

### 6.3 Fallback or context-only paths

- `quote_geometry.letter_perimeter_m`
- `geometry.confirmed`
- `finish_setup.confirmed`
- Review defaults pentru `return_depth_mm`
- Review defaults pentru `return_finish_type`

Acestea pot fi afisate de mapper ca evidence sau fallback, dar nu pot debloca readiness.

### 6.4 ProductDefinition-derived only

- `return_profile_linear_meter`
- `materials.return_profile`
- `MAT-PROFIL-LATERAL-LITERE-*`

Acestea pot fi mentionate numai ca downstream consequence si nu pot deveni primary truth.

## 7. Canonical Dependency Rules

### 7.1 Perimeter dependency

Regula canonica obligatorie:

```text
components.return_cant.perimeter_dependency.face_confirmed_perimeter
```

trebuie sa reflecte explicit:

```text
components.face.confirmed_perimeter
```

si nu poate fi reconstruit local doar din:

- `quote_geometry.letter_perimeter_m`;
- `geometry.confirmed`;
- SVG analyzer suggestion.

### 7.2 Perimeter source declaration

`components.return_cant.perimeter_source` nu detine valoarea geometrica.

El detine declaratia canonica:

```text
source_kind = dependency
source_component = face
source_path = components.face.confirmed_perimeter
fallback_context_path = quote_geometry.letter_perimeter_m
```

### 7.3 Layer group ownership

`components.return_cant.layer_group_ids` trebuie sa vina din operator-confirmed layer/group selection.

Nu este suficient:

- auto-role suggestion;
- `letter_group_finishes` singur;
- group rows hydrate fara selectie confirmata.

## 8. Canonical Confirmation Rules

### 8.1 Return cant confirmation

`components.return_cant.confirmation_state = confirmed` este obligatoriu pentru preview ulterior.

Acest field nu este sinonim cu:

- `finish_setup.confirmed`;
- `geometry.confirmed`;
- confirmarea unui singur group row.

El trebuie sa reprezinte faptul ca setul minim pentru `return_cant` este confirmed ca truth component-owned sau dependency confirmed.

### 8.2 Face perimeter confirmation

`components.face.confirmed_perimeter.confirmation_state = confirmed` este obligatoriu pentru a debloca dependency-ul de perimetru.

## 9. Readiness Gate For Mapper Later

Schema este considerata gata pentru implementarea mapperului daca mapperul aplica strict urmatoarele reguli:

1. raporteaza `blocked` cand lipseste orice path required;
2. afiseaza fallback/context-only separat de canonical truth;
3. afiseaza ProductDefinition-derived separat de primary truth;
4. nu promoveaza `quote_geometry.letter_perimeter_m` la dependency confirmed;
5. nu promoveaza `finish_setup.confirmed` la `components.return_cant.confirmation_state`.

## 10. Why This Is Ready For Mapper Implementation

Task-ul anterior era blocat pentru ca nu exista o schema canonica suficient de precisa.

Dupa acest document:

- fiecare field required are un canonical path clar;
- dependency-ul pe `face` are un upstream path clar;
- distingem explicit component-owned, dependency, fallback/context-only si ProductDefinition-derived;
- exista blocker vocabulary clar pentru fiecare lipsa;
- naming debt-ul actual este documentat si delimitat fata de schema tinta.

Prin urmare, pasul urmator poate implementa un mapper read-only strict de clasificare fara sa fie nevoit sa ghiceasca unde trebuie sa stea truth-ul.

## 11. Remaining Runtime Blockers After Canonicalization

Canonicalizarea rezolva schema, nu implementarea.

Blockers ramasi la runtime:

- path-urile canonice nu sunt inca scrise in read models actuale;
- `components.face.confirmed_perimeter` nu exista inca explicit;
- `components.return_cant.confirmation_state` nu exista inca explicit;
- `components.return_cant.layer_group_ids` nu este inca mapat din selected confirmed groups;
- color split-ul complet nu exista inca in Product Truth draft.

Acestea nu mai blocheaza definirea mapperului, ci doar implementarea lui.

## 12. Recommended Next Slice

Prompt recomandat:

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1
```
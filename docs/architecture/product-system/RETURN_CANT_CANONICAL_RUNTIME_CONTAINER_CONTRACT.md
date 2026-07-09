# Return Cant Canonical Runtime Container Contract

## 1. Purpose

Acest document defineste contractul canonic final pentru containerul runtime Product Truth al componentei `return_cant`.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
mode = canonical_runtime_container_contract
```

Acest document nu implementeaza:

- runtime bridge;
- Product Truth writes;
- UI changes;
- Pricing changes;
- adapter changes;
- builder changes;
- backbone migration;
- DB migration / seed;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY
```

Semnificatie exacta:

1. exista suficienta claritate pentru a fixa shape-ul final al containerului runtime `return_cant`;
2. shape-ul final poate fi definit fara a implementa writer-ul runtime;
3. compatibilitatea cu formele legacy poate fi documentata fara ambiguitate critica;
4. bridge-ul runtime ramane in continuare blocat pana la inchiderea slice-urilor urmatoare.

## 3. Why This Contract Is Ready Now

Auditul confirma urmatoarele ancore locale:

1. `backend/services/intake_v6_workspace_service.py` este punctul corect pentru viitorul write runtime, dar nu impune deja un alt shape final;
2. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts` si `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts` folosesc deja tinta canonica `components.return_cant...` ca model readonly, chiar daca nu exista writer;
3. `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` si `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts` raman legacy (`components.returnCant`) si confirma nevoia de compatibilitate explicita, nu lipsa de informatie pentru shape-ul final;
4. `backend/services/form_system_contract_backbone_service.py` confirma ca `components.return.*` este path vechi de backbone, nu tinta finala.

Concluzie: blockerul actual este de contract si ownership, nu de imposibilitate de definire a shape-ului final.

## 4. Canonical Container Contract

Containerul final canonic este:

```text
components.return_cant = {
  version: "v1",
  instances: {
    <instance_key>: {
      instance_key: string,
      source_kind: "letter_group" | "artwork_layer",
      source_ref: {
        group_key?: string,
        layer_key?: string
      },
      layer_group_ids: string[],
      material_profile: {
        width_mm: 30 | 60 | 80 | 100
      },
      finish_variant: {
        type: "stock_color" | "vinyl_application" | "paint_application",
        stock_color_label?: string,
        vinyl?: {
          material_family: "Folie autocolanta PVC",
          series: "Oracal 641" | "Oracal 651" | "Oracal 8500",
          color_code?: string,
          catalog_reference?: string
        },
        paint?: {
          system: "RAL",
          ral_code?: string,
          catalog_reference?: string
        }
      },
      pricing_keys: {
        material_profile_width?: string,
        vinyl_material?: string,
        vinyl_application_labor?: string,
        ral_paint_material_by_width?: string,
        ral_paint_labor?: string
      },
      geometry: {
        perimeter_source: "confirmed_component_truth" | "evidence_only" | "missing",
        confirmed_perimeter_m?: number,
        evidence_perimeter_m?: number
      },
      confirmation_state: "missing" | "draft" | "blocked" | "confirmed",
      blockers: string[]
    }
  }
}
```

## 5. Canonical Normalization Choices

Acest contract fixeaza doua normalizari importante fata de shape-uri partiale sau propuse anterior.

### 5.1 `layer_group_ids` este camp de instanta, nu camp in `source_ref`

Decizie:

- `source_ref` pastreaza cheia stabila de origine: `group_key` sau `layer_key`;
- `layer_group_ids` ramane la nivelul instantei, in acelasi obiect cu `confirmation_state` si `geometry`.

Rationale:

1. target paths-urile readonly existente indica deja `components.return_cant.instances.<instance_key>.layer_group_ids`;
2. `layer_group_ids` este o legatura operationala a instantei finale, nu doar un identificator de origine;
3. mentinerea lui la nivelul instantei evita dublarea intre `source_ref` si `geometry` / `confirmation_state`.

### 5.2 `material_profile.pricing_key` nu intra in contractul final

Decizie:

- `material_profile` ramane structural si contine doar `width_mm`;
- cheia de pricing pentru profil lateral traieste numai in `pricing_keys.material_profile_width`.

Rationale:

1. duplicarea aceleiasi chei in `material_profile.pricing_key` si `pricing_keys.material_profile_width` ar crea doua surse de adevar;
2. toate referintele de pricing trebuie sa stea intr-un singur owner block: `pricing_keys`;
3. `material_profile` trebuie sa descrie profilul selectat, nu sa dubleze contractul Pricing.

## 6. Instance Key Rules

Regulile canonice finale pentru `instance_key` sunt:

1. pentru `Vector Litere` / letter group:

```text
instance_key = letter_group:<group_key>
```

2. pentru `Vector Logo` / artwork layer:

```text
instance_key = artwork_layer:<layer_key>
```

3. daca lipseste `group_key` sau `layer_key`, `instance_key` nu se inventeaza;
4. index numeric instabil nu este permis ca `instance_key` final;
5. cheile brute actuale folosite readonly, de tip `pseudo:maria` sau `logo-1`, pot servi ca evidence / transitional source rows, dar nu sunt contractul final al instantei;
6. bridge-ul viitor poate deriva `instance_key` doar din cheia stabila de business, nu din pozitia randului sau ordinea din array.

Regula de blocare:

```text
missing group_key or layer_key => no synthetic instance_key => source row remains blocked
```

## 7. Compatibility Policy

Politica de compatibilitate este:

1. `components.returnCant` = legacy / transitional only;
2. `components.return` = backbone legacy path only;
3. target final = `components.return_cant`;
4. bridge-ul viitor poate citi legacy pentru migration / fallback / context, dar nu trebuie sa scrie final in path-uri legacy;
5. builder-ul actual care produce `components.returnCant` trebuie aliniat intr-un slice ulterior sau acoperit printr-un compatibility layer explicit;
6. este interzis sa se scrie simultan si final in `components.return_cant` si final in `components.returnCant` fara contract explicit de dual-write, iar acest task nu autorizeaza un astfel de contract;
7. backbone-ul care expune azi `components.return.material` si `components.return.depth_mm` ramane legacy read-model evidence pana la migrarea la contractul final.

Regula de compatibilitate minima pentru viitorul bridge:

```text
legacy read allowed
legacy final write forbidden
dual final write forbidden
```

## 8. Owner Layer Map

| zone | owner_layer | responsibility | non-owner responsibility forbidden here |
|---|---|---|---|
| Intake V6 UI | user-facing selection layer | labels, raw selections, per-row finish choices | nu confirma singur Product Truth final |
| readonly adapter | evidence / mapping layer | mapari readonly, blockers, pricing refs readonly, catalog refs readonly | nu scrie runtime, nu confirma componenta |
| Product Truth runtime container | canonical runtime state | selected confirmed refs, canonical finish variant, blockers, confirmation state, geometry source state | nu calculeaza preturi, nu inventeaza component confirmation |
| Pricing | pricing contract layer | coduri finale de pricing si valorile lor comerciale | nu detine UI labels, nu detine component truth confirmation |
| Catalog | catalog contract layer | cod, culoare, serie, swatch, catalog reference | nu stocheaza cost sau pret in containerul Product Truth |
| Product System component | formula / input requirements | defineste ce cere componenta `return_cant` pentru downstream | nu scrie singur runtime truth |
| Analyzer | geometry evidence layer | evidence geometry, selected layers, suggestions | nu promoveaza evidence la confirmed perimeter |

## 9. Container Readiness Rules

Containerul poate exista in `blocked` sau `draft` chiar daca unele date sunt prezente.

### 9.1 Cand containerul poate exista in `blocked`

Containerul sau instanta poate exista in `blocked` daca lipseste cel putin una dintre urmatoarele:

1. `geometry.confirmed_perimeter_m` dintr-o sursa confirmata owner-safe;
2. `confirmation_state = confirmed` la nivel de componenta / instanta;
3. `layer_group_ids` canonice pentru instanta;
4. `vinyl.color_code` cand `finish_variant.type = vinyl_application`;
5. `paint.ral_code` cand `finish_variant.type = paint_application`;
6. cheia de pricing obligatorie pentru varianta curenta.

### 9.2 Cand containerul nu are voie sa fie `confirmed`

Containerul NU trebuie sa devina `confirmed` doar pentru ca:

1. Pasul 1 este confirmat;
2. row-ul din `finish_setup` este `confirmed`;
3. `finish_setup.confirmed = true`;
4. analyzerul a produs perimeter;
5. `quote_geometry.letter_perimeter_m` exista si este marcat `confirmed` in contextul geometry payload.

### 9.3 Interpretarea starilor

1. `missing` = instanta nu are inca suficiente campuri canonice pentru evaluare normala;
2. `draft` = instanta are shape partial si intent recognoscibil, dar nu are confirmation / dependency complete;
3. `blocked` = shape-ul este format, dar exista blockere explicite care interzic downstream unlock;
4. `confirmed` = toate campurile obligatorii sunt prezente, dependencies canonice sunt confirmate, iar blockerele sunt goale.

## 10. Field Matrix

| field | required | owner | source_now | final_path | can_be_written_in_future_bridge | blocker_if_missing | legacy_equivalent |
|---|---|---|---|---|---|---|---|
| version | yes | Product Truth runtime container | none today | `components.return_cant.version` | yes | `RETURN_CANT_CONTAINER_VERSION_MISSING` | none |
| instances | yes | Product Truth runtime container | none today | `components.return_cant.instances` | yes | `RETURN_CANT_INSTANCES_CONTAINER_MISSING` | none |
| instance_key | yes | Product Truth runtime container | readonly source row keys only | `components.return_cant.instances.<instance_key>.instance_key` | yes | `RETURN_CANT_INSTANCE_KEY_MISSING` | raw `group_key` / `layer_key` only |
| source_kind | yes | Product Truth runtime container | inferable from `letter_group_finishes[]` / `artwork_finishes[]` | `components.return_cant.instances.<instance_key>.source_kind` | yes | `RETURN_CANT_SOURCE_KIND_MISSING` | none |
| group_key | conditional for letter group | Intake V6 UI raw source -> Product Truth runtime container | `finish_setup.letter_group_finishes[].group_key` | `components.return_cant.instances.<instance_key>.source_ref.group_key` | yes | `RETURN_CANT_GROUP_KEY_MISSING` | `group_key` |
| layer_key | conditional for artwork layer | Intake V6 UI raw source -> Product Truth runtime container | `finish_setup.artwork_finishes[].layer_key` | `components.return_cant.instances.<instance_key>.source_ref.layer_key` | yes | `RETURN_CANT_LAYER_KEY_MISSING` | `layer_key` |
| layer_group_ids | yes | Product Truth runtime container | selected layer refs / layer role setup / readonly evidence only | `components.return_cant.instances.<instance_key>.layer_group_ids` | yes | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | none |
| material_profile.width_mm | yes | Product Truth runtime container | `return_depth_mm` hydrated from finish setup | `components.return_cant.instances.<instance_key>.material_profile.width_mm` | yes | `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` | `components.returnCant.depthMm`, `components.return.depth_mm` |
| finish_variant.type | yes | Product Truth runtime container | `return_finish_type` plus readonly normalization | `components.return_cant.instances.<instance_key>.finish_variant.type` | yes | `RETURN_CANT_FINISH_MISSING` | `components.returnCant.finishType` |
| stock_color_label | conditional for stock color | Catalog reference surfaced through Product Truth runtime container | readonly adapter normalization from `return_finish_type` | `components.return_cant.instances.<instance_key>.finish_variant.stock_color_label` | yes | `RETURN_CANT_STOCK_COLOR_LABEL_MISSING` | none |
| vinyl.series | conditional for vinyl | Catalog | `materialCode` / readonly adapter inference | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.series` | yes | `RETURN_CANT_VINYL_SERIES_MISSING` | legacy Oracal token only |
| vinyl.color_code | conditional for vinyl | Catalog | `return_oracal_code` / per-row color code | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code` | yes | `RETURN_CANT_VINYL_COLOR_CODE_MISSING` | `components.returnCant.colorCode` |
| vinyl.catalog_reference | conditional for vinyl | Catalog | readonly derived only | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference` | yes | `RETURN_CANT_VINYL_CATALOG_REFERENCE_MISSING` | none |
| paint.system | conditional for paint | Catalog / Product Truth runtime container | readonly normalization from `return_finish_type = ral_paint` | `components.return_cant.instances.<instance_key>.finish_variant.paint.system` | yes | `RETURN_CANT_PAINT_SYSTEM_MISSING` | none |
| paint.ral_code | conditional for paint | Catalog | `return_oracal_code` reused today as legacy field | `components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code` | yes | `RETURN_CANT_RAL_CODE_MISSING` | `components.returnCant.colorCode` |
| paint.catalog_reference | conditional for paint | Catalog | readonly derived only | `components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference` | yes | `RETURN_CANT_PAINT_CATALOG_REFERENCE_MISSING` | none |
| pricing_keys.material_profile_width | yes | Pricing contract surfaced in Product Truth runtime container | verified by pricing registry; not written in runtime yet | `components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width` | yes | `RETURN_CANT_PROFILE_PRICING_KEY_MISSING` | none |
| pricing_keys.vinyl_material | conditional for vinyl | Pricing contract surfaced in Product Truth runtime container | readonly adapter points to transitional vinyl key evidence | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material` | yes | `RETURN_CANT_VINYL_MATERIAL_ALIGNMENT_REQUIRED` | none |
| pricing_keys.vinyl_application_labor | conditional for vinyl | Pricing contract surfaced in Product Truth runtime container | readonly adapter uses legacy lowercase labor target | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor` | yes | `RETURN_CANT_VINYL_APPLICATION_LABOR_ALIGNMENT_REQUIRED` | `return_cant_vinyl_application_labor` |
| pricing_keys.ral_paint_material_by_width | conditional for paint | Pricing contract surfaced in Product Truth runtime container | readonly adapter uses width-specific legacy lower-case target | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width` | yes | `RETURN_CANT_RAL_PAINT_PRICING_ALIGNMENT_REQUIRED` | `ral_paint_material_<width>mm` |
| pricing_keys.ral_paint_labor | conditional for paint | Pricing contract surfaced in Product Truth runtime container | readonly adapter uses legacy labor target | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor` | yes | `RETURN_CANT_RAL_PAINT_LABOR_ALIGNMENT_REQUIRED` | `ral_paint_application_labor` |
| geometry.perimeter_source | yes | Product Truth runtime container | quote geometry and face dependency only as evidence | `components.return_cant.instances.<instance_key>.geometry.perimeter_source` | yes | `RETURN_CANT_PERIMETER_SOURCE_MISSING` | legacy readonly `perimeter_source` expectation only |
| geometry.confirmed_perimeter_m | conditional for confirmed state | Product Truth runtime container with face dependency | no canonical source today | `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m` | yes, after source contract | `RETURN_CANT_PERIMETER_MISSING` | none |
| geometry.evidence_perimeter_m | optional but recommended | Analyzer evidence surfaced through Product Truth runtime container | `quote_geometry.letter_perimeter_m` context only | `components.return_cant.instances.<instance_key>.geometry.evidence_perimeter_m` | yes | none | `quote_geometry.letter_perimeter_m` context only |
| confirmation_state | yes | Product Truth runtime container | no explicit component field today | `components.return_cant.instances.<instance_key>.confirmation_state` | yes, after confirmation contract | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | none |
| blockers | yes | Product Truth runtime container | readonly blockers only | `components.return_cant.instances.<instance_key>.blockers` | yes | `RETURN_CANT_BLOCKER_LIST_MISSING` | readonly mapper / adapter blocker arrays only |

## 11. Practical Rules For Future Bridge Writers

Reguli obligatorii pentru viitorul writer runtime:

1. nu inventeaza `instance_key` daca lipseste cheia de business;
2. nu scrie target final in `components.returnCant`;
3. nu scrie target final in `components.return.*`;
4. nu promoveaza `quote_geometry.letter_perimeter_m` la `geometry.confirmed_perimeter_m`;
5. nu scrie `confirmation_state = confirmed` doar din Step 1, row `confirmed` sau `finish_setup.confirmed`;
6. nu trateaza targetele legacy de Pricing ca finale;
7. nu dual-write in legacy si canonical final path in acelasi slice fara contract explicit separat.

## 12. Recommended Next Slice

Slice-ul urmator recomandat ramane:

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```

Rationale:

1. contractul containerului este acum definit si nu mai este blockerul structural principal;
2. adapterul readonly este singurul strat care emite deja target paths apropiate de forma finala si inca pastreaza referinte Pricing legacy;
3. alinierea adapterului la cheile finale reduce riscul ca viitorul bridge sa se sprijine pe aliasuri gresite;
4. builder-ul legacy si backbone-ul legacy raman probleme reale, dar dupa acest contract ele sunt clar incadrate ca compatibility / migration concerns, nu ca blocker structural mai critic decat pricing-target alignment.

Nota de disciplina:

- acest next slice nu trebuie sa implementeze runtime write;
- acest next slice trebuie sa trateze si faptul ca source row keys actuale nu sunt `instance_key` finale, dar fara a declara inca writer runtime.

## 13. Recommended Next Prompt

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```# Return Cant Canonical Runtime Container Contract

## 1. Purpose

Acest document defineste contractul canonic pentru containerul runtime Product Truth al componentei `return_cant`.

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = canonical_runtime_container_contract
root_template = TPL-VOLUMETRIC-LETTERS_v2
```

Acest document nu implementeaza:

- runtime bridge;
- Product Truth writes;
- UI changes;
- Pricing changes;
- adapter changes;
- builder/backbone/mapper compatibility code;
- DB migration / seed;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY
```

Semnificatie exacta:

1. shape-ul final pentru containerul runtime poate fi definit fara ambiguitate critica;
2. regulile de `instance_key`, ownership si compatibility pot fi fixate docs-only;
3. implementarea writer-ului runtime ramane interzisa in acest slice;
4. contractele legacy raman blocker de implementare, nu blocker de definire a shape-ului final.

## 3. Why This Slice Is Ready

Auditul confirma suficienta informatie pentru a fixa contractul final:

1. `returnCantTruthFieldsReadonlyMapper.ts` trateaza deja `components.return_cant` ca tinta canonica asteptata;
2. `returnCantTruthFieldCaptureReadonlyAdapter.ts` foloseste deja baza per-instance `components.return_cant.instances.<instance_key>`;
3. `productTruthDraftBuilder.ts` si `productTruthTypes.ts` confirma clar ce este legacy si ce nu poate fi promovat tacit;
4. `form_system_contract_backbone_service.py` confirma ca `components.return.*` este vechiul path si are nevoie de migrare;
5. `intake_v6_workspace_service.py` confirma ca viitorul writer trebuie sa fie derivare persist-time, deci acest task poate ramane strict contract-only.

Contractul este deci `READY`, chiar daca implementarea ramane blocata pana la slice-urile urmatoare.

## 4. Canonical Container Shape

Containerul final pentru runtime Product Truth `return_cant` este:

```ts
components.return_cant = {
  version: "v1",
  instances: {
    [instance_key: string]: {
      instance_key: string,
      source_kind: "letter_group" | "artwork_layer",
      source_ref: {
        group_key?: string,
        layer_key?: string,
      },
      layer_group_ids: string[],
      material_profile: {
        width_mm: 30 | 60 | 80 | 100,
      },
      finish_variant: {
        type: "stock_color" | "vinyl_application" | "paint_application",
        stock_color_label?: string,
        vinyl?: {
          material_family: "Folie autocolanta PVC",
          series: "Oracal 641" | "Oracal 651" | "Oracal 8500",
          color_code?: string,
          catalog_reference?: string,
        },
        paint?: {
          system: "RAL",
          ral_code?: string,
          catalog_reference?: string,
        },
      },
      pricing_keys: {
        material_profile_width?: string,
        vinyl_material?: string,
        vinyl_application_labor?: string,
        ral_paint_material_by_width?: string,
        ral_paint_labor?: string,
      },
      geometry: {
        perimeter_source: "confirmed_component_truth" | "evidence_only" | "missing",
        confirmed_perimeter_m?: number,
        evidence_perimeter_m?: number,
      },
      confirmation_state: "missing" | "draft" | "blocked" | "confirmed",
      blockers: string[],
    },
  },
}
```

### 4.1 Canonical adjustments versus earlier draft notation

Doua ajustari sunt deliberate si obligatorii:

1. `layer_group_ids` este top-level in fiecare instanta, nu doar in `source_ref`.
   Rationale: mapperul readonly il trateaza deja ca field canonic first-class si depinde de el separat de identificatorul sursei.
2. `material_profile.pricing_key` nu este field canonic separat.
   Rationale: cheia de pricing trebuie sa existe intr-un singur loc canonic, sub `pricing_keys.material_profile_width`, pentru a evita doua adevaruri concurente in acelasi container.

## 5. Canonical Semantics By Section

### 5.1 Container level

- `components.return_cant.version` fixeaza schema runtime pentru acest subtree.
- `components.return_cant.instances` este un map determinist, nu o lista ordonata.
- lipsa unei instante valide inseamna lipsa cheii in `instances`, nu inventarea unei intrari partial-identificate.

### 5.2 Instance level

- fiecare instanta reprezinta exact un owner runtime `return_cant` derivat fie dintr-un `letter_group`, fie dintr-un `artwork_layer`.
- `instance_key` este cheia canonica de stabilitate pentru write/read/audit.
- `blockers` este lista explicita de motive pentru care instanta poate exista in `draft` sau `blocked`.

### 5.3 Source and geometry

- `source_ref.group_key` se foloseste numai pentru `source_kind = letter_group`.
- `source_ref.layer_key` se foloseste numai pentru `source_kind = artwork_layer`.
- `layer_group_ids` este setul normalizat de refs care leaga instanta de runtime-ul SVG/operator.
- `geometry.evidence_perimeter_m` poate reflecta context cum ar fi `quote_geometry.letter_perimeter_m`.
- `geometry.confirmed_perimeter_m` poate fi prezent numai dintr-o sursa confirmata owner-safe, nu din analyzer context.

### 5.4 Finish and pricing

- `finish_variant.type` este semantica tehnica finala.
- label-urile user-facing raman in UI; contractul runtime stocheaza numai truth-ul necesar downstream.
- `pricing_keys.*` sunt referinte catre contracte/cataloage de pricing, nu preturi sau costuri materializate.

## 6. Instance Key Rules

Regulile canonice pentru `instance_key` sunt:

1. pentru `Vector Litere` / letter group:

```text
instance_key = letter_group:<group_key>
```

2. pentru `Vector Logo` / artwork layer:

```text
instance_key = artwork_layer:<layer_key>
```

3. daca lipseste `group_key` pentru un row de tip letter group, instanta nu se inventeaza si containerul ramane `blocked` prin absenta unei instante write-safe;
4. daca lipseste `layer_key` pentru un row de tip artwork layer, instanta nu se inventeaza si containerul ramane `blocked`;
5. nu se foloseste index numeric instabil, pozitie in array, sau ordinea curenta a row-urilor ca `instance_key` final;
6. cheia din map si `instance_key` din obiect trebuie sa fie identice textual;
7. `group_key` si `layer_key` nu se amesteca in acelasi namespace fara prefixul canonic de mai sus.

## 7. Compatibility Policy

Politica obligatorie de compatibilitate este:

1. `components.returnCant` = legacy / transitional only;
2. `components.return` = legacy backbone old path only;
3. targetul final unic este `components.return_cant`;
4. viitorul bridge poate citi legacy pentru migration/context, dar nu trebuie sa scrie final in path-urile legacy;
5. daca builder-ul actual produce `components.returnCant`, slice-ul urmator care il atinge trebuie sa il alinieze sau sa introduca un compatibility layer explicit;
6. nu se accepta dual-write permanent in `components.returnCant` si `components.return_cant`;
7. nu se accepta promovarea `components.return.*` la target final doar pentru ca backbone-ul existent inca emite acele path-uri;
8. compatibilitatea este read-for-migration, nu write-for-forever.

## 8. Owner Layer Map

| zone | owner layer | exact responsibility | explicit non-responsibility |
|---|---|---|---|
| Intake V6 UI | UI / review flow | user-facing labels, row selections, raw edit state | nu defineste singur component truth confirmed |
| readonly adapter | mapping / evidence layer | normalizeaza evidence, target paths readonly, blocker language | nu scrie runtime si nu decide truth final |
| Product Truth runtime container | canonical truth layer | selected confirmed refs, intent, blockers, final per-instance shape | nu calculeaza preturi si nu inventeaza confirmation |
| Pricing | pricing contract layer | detine key registry, cost/pret rules, formula references | nu detine component confirmation sau geometry truth |
| Catalog | finish/color catalog layer | cod, culoare, serie, catalog reference | nu detine pricing si nu confirma component truth |
| Product System component | component contract layer | formula/input requirements pentru return_cant | nu scrie direct UI review state |
| Analyzer | geometry evidence layer | evidence-only geometry si layer suggestions | nu promoveaza `confirmed_perimeter_m` |

## 9. Container Readiness Rules

Containerul poate exista in `blocked` state daca lipseste oricare dintre urmatoarele:

1. confirmed perimeter valid;
2. component confirmation explicita;
3. `layer_group_ids` deterministe;
4. color code necesar pentru variantul vinyl sau RAL;
5. pricing key reference necesara pentru variantul selectat.

Containerul nu trebuie sa fie `confirmed` doar pentru ca:

1. Pasul 1 este confirmat;
2. row-ul din finish setup este `confirmed`;
3. `finish_setup.confirmed` este `true`;
4. analyzerul a produs un perimeter;
5. exista doar `quote_geometry.letter_perimeter_m`.

Semantica minima pentru `confirmation_state`:

- `missing`: instanta nu are inca source confirmation field propriu;
- `draft`: instanta are intent si enough structure pentru runtime presence, dar nu are toate dependintele owner-confirmed;
- `blocked`: instanta este localizata, dar are blockers expliciti care interzic truth confirmed;
- `confirmed`: instanta are source refs, perimeter source si blockers rezolvati conform contractelor urmatoare.

## 10. Field Matrix

| field | required | owner | source_now | final_path | can_be_written_in_future_bridge | blocker_if_missing | legacy_equivalent |
|---|---|---|---|---|---|---|---|
| version | yes | Product Truth runtime container | missing as canonical runtime subtree | `components.return_cant.version` | yes | `RETURN_CANT_CONTAINER_VERSION_MISSING` | none |
| instances | yes | Product Truth runtime container | missing as canonical runtime subtree | `components.return_cant.instances` | yes | `RETURN_CANT_INSTANCE_CONTAINER_MISSING` | none |
| instance_key | yes | Product Truth runtime container | readonly adapter base only | `components.return_cant.instances.<instance_key>.instance_key` | yes, only when deterministic | `RETURN_CANT_INSTANCE_KEY_MISSING` | source row key only |
| source_kind | yes | Product Truth runtime container | inferred readonly from `letter_group_finishes[]` / `artwork_finishes[]` | `components.return_cant.instances.<instance_key>.source_kind` | yes | `RETURN_CANT_SOURCE_KIND_MISSING` | none |
| group_key | conditional for `letter_group` | Product Truth runtime container | `finish_setup.letter_group_finishes[].group_key` | `components.return_cant.instances.<instance_key>.source_ref.group_key` | yes | `RETURN_CANT_GROUP_KEY_MISSING` | `letter_group_finishes[].group_key` |
| layer_key | conditional for `artwork_layer` | Product Truth runtime container | `finish_setup.artwork_finishes[].layer_key` | `components.return_cant.instances.<instance_key>.source_ref.layer_key` | yes | `RETURN_CANT_LAYER_KEY_MISSING` | `artwork_finishes[].layer_key` |
| layer_group_ids | yes | Product Truth runtime container | selected refs / layer evidence / readonly context only | `components.return_cant.instances.<instance_key>.layer_group_ids` | yes, after mapping contract | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | no stable legacy equivalent |
| material_profile.width_mm | yes | Product Truth runtime container | hydrated row `return_depth_mm` | `components.return_cant.instances.<instance_key>.material_profile.width_mm` | yes | `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` | `components.returnCant.depthMm`, `components.return.depth_mm` |
| finish_variant.type | yes | Product Truth runtime container | `return_finish_type` normalized readonly | `components.return_cant.instances.<instance_key>.finish_variant.type` | yes | `RETURN_CANT_FINISH_MISSING` | `components.returnCant.finishType` |
| stock_color_label | conditional for `stock_color` | Catalog | readonly adapter normalization from legacy finish token | `components.return_cant.instances.<instance_key>.finish_variant.stock_color_label` | yes | `RETURN_CANT_STOCK_COLOR_LABEL_MISSING` | none |
| vinyl.series | conditional for `vinyl_application` | Catalog | readonly adapter inference from finish/material evidence | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.series` | yes | `RETURN_CANT_VINYL_SERIES_MISSING` | none |
| vinyl.color_code | conditional for `vinyl_application` | Catalog | `return_oracal_code` / row color code | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code` | yes | `RETURN_CANT_VINYL_COLOR_CODE_MISSING` | `components.returnCant.colorCode` |
| vinyl.catalog_reference | conditional for `vinyl_application` | Catalog | readonly derived only | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference` | yes | `RETURN_CANT_VINYL_CATALOG_REFERENCE_MISSING` | none |
| paint.system | conditional for `paint_application` | Catalog | readonly normalization from `ral_paint` token | `components.return_cant.instances.<instance_key>.finish_variant.paint.system` | yes | `RETURN_CANT_RAL_SYSTEM_MISSING` | none |
| paint.ral_code | conditional for `paint_application` | Catalog | `return_oracal_code` reused today for RAL evidence | `components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code` | yes | `RETURN_CANT_RAL_CODE_MISSING` | `components.returnCant.colorCode` |
| paint.catalog_reference | conditional for `paint_application` | Catalog | readonly derived only | `components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference` | yes | `RETURN_CANT_RAL_CATALOG_REFERENCE_MISSING` | none |
| pricing_keys.material_profile_width | yes | Pricing contract | depth-to-key readonly mapping | `components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width` | yes | `RETURN_CANT_PROFILE_PRICING_KEY_MISSING` | no stable legacy final; today only readonly mapping |
| pricing_keys.vinyl_material | conditional for `vinyl_application` | Pricing contract | readonly evidence only | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material` | yes | `RETURN_CANT_VINYL_MATERIAL_ALIGNMENT_REQUIRED` | no canonical legacy equivalent |
| pricing_keys.vinyl_application_labor | conditional for `vinyl_application` | Pricing contract | legacy readonly target only | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor` | yes, after alignment | `RETURN_CANT_VINYL_APPLICATION_LABOR_ALIGNMENT_REQUIRED` | `return_cant_vinyl_application_labor` |
| pricing_keys.ral_paint_material_by_width | conditional for `paint_application` | Pricing contract | legacy readonly target only | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width` | yes, after alignment | `RETURN_CANT_RAL_PAINT_PRICING_ALIGNMENT_REQUIRED` | `ral_paint_material_<width>mm` |
| pricing_keys.ral_paint_labor | conditional for `paint_application` | Pricing contract | legacy readonly target only | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor` | yes, after alignment | `RETURN_CANT_RAL_PAINT_LABOR_ALIGNMENT_REQUIRED` | `ral_paint_application_labor` |
| geometry.perimeter_source | yes | Product Truth runtime container | quote geometry context only or missing | `components.return_cant.instances.<instance_key>.geometry.perimeter_source` | yes | `RETURN_CANT_PERIMETER_MISSING` | mapper proto field `components.return_cant.perimeter_source` |
| geometry.confirmed_perimeter_m | conditional for confirmed geometry | Product Truth runtime container | missing canonical source | `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m` | yes, only after source contract | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | none |
| geometry.evidence_perimeter_m | optional but recommended when evidence exists | Analyzer / evidence layer | `quote_geometry.letter_perimeter_m` | `components.return_cant.instances.<instance_key>.geometry.evidence_perimeter_m` | yes | none | `quote_geometry.letter_perimeter_m` |
| confirmation_state | yes | Product Truth runtime container | missing canonical field; only row/global evidence exists | `components.return_cant.instances.<instance_key>.confirmation_state` | yes, after confirmation contract | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | row `confirmed`, `finish_setup.confirmed`, Step 1 confirmation as non-equivalent evidence only |
| blockers | yes | Product Truth runtime container | readonly blocker language exists | `components.return_cant.instances.<instance_key>.blockers` | yes | `RETURN_CANT_BLOCKERS_FIELD_MISSING` | scattered warnings/blockers in readonly layers |

## 11. Implementation Constraints For Future Bridge

Viitorul bridge are voie sa scrie acest container numai daca:

1. scrie exclusiv in `components.return_cant` ca target final;
2. nu promoveaza `quote_geometry.letter_perimeter_m` la `confirmed_perimeter_m`;
3. nu trateaza Pasul 1, row confirmed sau `finish_setup.confirmed` ca `confirmation_state = confirmed`;
4. nu scrie preturi sau costuri, doar referinte si truth fields;
5. nu scrie in paralel in `components.returnCant` sau `components.return.*`.

## 12. Recommended Next Slice

Urmatorul slice recomandat dupa acest contract este:

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```

Rationale:

1. contractul structural este acum fixat in acest document;
2. urmatorul risc executabil cel mai mic este faptul ca readonly adapterul inca foloseste trei targete legacy de pricing;
3. builder/backbone compatibility raman importante, dar dupa acest slice ele sunt deja incadrate de politica de compatibilitate si nu mai concureaza cu shape-ul final;
4. adapter alignment reduce riscul ca orice implementare ulterioara sa inghete chei legacy in jurul noului container canonic.

## 13. Mandatory Forbidden Scope Reminder

Raman interzise pentru acest slice:

1. runtime bridge implementation;
2. Product Truth writes;
3. UI changes;
4. Pricing changes;
5. adapter code changes;
6. preview / quote / order / execution changes;
7. DB migration / seed;
8. promovarea `quote_geometry.letter_perimeter_m` la `confirmed_perimeter_m`;
9. folosirea `components.returnCant` sau `components.return.*` ca target final.
# Return Cant Component Truth Field Capture Plan

## 1. Purpose

Acest document defineste planul docs-only pentru capturarea field-urilor lipsa ale componentei `return_cant` in Product Truth, fara sa modifice Pricing, fara sa mute costuri sau preturi in componenta si fara sa implementeze preview sau calculation runtime.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = field_capture_plan
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
RETURN_CANT_FIELD_CAPTURE_PLAN_READY
```

Clarificare:

- planul de capturare este suficient de clar pentru un slice urmator de contract adapter / writer read-only;
- runtime-ul curent ramane `RETURN_CANT_MAPPER_BLOCKED`;
- componenta nu devine prin acest document preview ready si nu devine calculation ready.

## 3. Owner Rule Set

Regulile owner confirmate pentru acest plan sunt:

1. Componenta `return_cant` detine formula, quantity basis, input requirements, dependency requirements si pricing lookup keys, dar nu detine valori de cost sau pret.
2. Pricing ramane autoritatea pentru cost material, cost manopera, tarif per ml si orice regula comerciala sau interna de cost.
3. Analyzer poate sugera `perimeter_m` si layer/group evidence, dar nu confirma truth si nu da pret.
4. Product Truth confirma field-urile de componenta si dependency-ul pe `face`.
5. ProductDefinition consuma truth-ul confirmat si nu inventeaza truth upstream.
6. CommercialPriceProposal / Pricing vine doar dupa truth completeness.

## 4. Component Formula Boundary

Formula component-owned acceptata pentru `return_cant` este:

```text
component: return_cant
quantity_basis: ml
required_quantity_input: components.face.confirmed_perimeter.value
quantity_formula: return_cant.quantity_ml = components.face.confirmed_perimeter.value
analyzer_required_input: perimeter_m suggestion
pricing_required_keys:
  - return_cant.material_profile.material_cost_per_ml
  - return_cant.labor.cost_per_ml
pricing_boundary:
  - all material and labor costs remain in /inventory/pricing
  - component stores no price and no cost values
```

Reguli obligatorii:

- `quote_geometry.letter_perimeter_m` poate ramane context / suggestion, nu dependency confirmed;
- `components.face.confirmed_perimeter.value` este singurul input acceptat pentru quantity formula viitoare;
- orice cost material sau cost manopera ramane lookup downstream in Pricing.

## 5. Capture Surface Plan

Planul separa clar cele 4 roluri:

### 5.1 Form System

- captureaza inputurile operator-confirmed pentru depth, finish, color target si material profile;
- expune source/state explicit;
- nu calculeaza pret si nu decide readiness comercial.

### 5.2 Intake V6 Review

- ramane locul cel mai apropiat pentru operator confirmation pe `return_cant`;
- suprafata candidata ramane `Review > Finisaje > Finisaje pe layer` pentru fields operator-facing;
- poate afisa read-only state/blockers, dar nu devine preview final.

### 5.3 Product Truth Draft / Writer Slice

- normalizeaza field-urile actuale necanonice (`components.returnCant.*`, `finish_setup.*`, `quote_geometry.*`) in path-urile canonice `components.return_cant.*` si `components.face.confirmed_perimeter.*`;
- separa explicit confirmed truth de hydrated/fallback/context-only;
- scrie dependency mirror-ul `components.return_cant.perimeter_dependency.face_confirmed_perimeter.*` numai dupa ce `components.face.confirmed_perimeter.*` este confirmed.

### 5.4 Pricing Registry Boundary

- continua sa detina costuri si tarife la ruta `http://127.0.0.1:3000/inventory/pricing`;
- componenta transmite doar lookup intent / pricing keys necesare;
- niciun field de Product Truth din acest plan nu stocheaza cost sau pret.

## 6. Exact Field Capture Matrix

| field_key | canonical Product Truth path | component owner | input source | source_state initial | required confirmation action | UI location candidate | mapper effect after capture | ProductDefinition consequence | pricing key needed | pricing value remains in Pricing | blocker inchis | blocker ramas dupa acest field singur |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `return_cant.depth_mm` | `components.return_cant.depth_mm` | `return_cant` | `finish_setup.return_depth_mm` / letter-group cant depth | `hydrated` sau `manual_pending` | operator confirma depth-ul pe componenta | `Review > Finisaje > cant fields` | trece din `hydrated_only` la `component_truth_confirmed` pentru depth | permite selectie corecta de variant pentru `MAT-PROFIL-LATERAL-LITERE-*` downstream | `return_cant.material_profile.material_cost_per_ml` indirect prin profil/depth | da | `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` sau `RETURN_CANT_DEPTH_MISSING` | raman material, finish, color, layer groups, perimeter, confirmation state |
| `return_cant.material_profile` | `components.return_cant.material_profile` | `return_cant` | selector Form System pentru profil/material de cant, eventual restrans de depth | `missing` | operator alege si confirma profilul/materialul de cant | `Review > Finisaje > cant fields` sau viitor subfield Form System | inchide blockerul de material si da owner truth upstream | alimenteaza material intent / resolver pentru `MAT-PROFIL-LATERAL-LITERE-*` | `return_cant.material_profile.material_cost_per_ml` | da | `RETURN_CANT_MATERIAL_MISSING` | raman depth, finish, color, layer groups, perimeter, confirmation state |
| `return_cant.finish_type` | `components.return_cant.finish_type` | `return_cant` | `finish_setup.return_finish_type` / group cant finish | `hydrated` sau `manual_pending` | operator confirma finish-ul component-owned | `Review > Finisaje > cant fields` | permite mapperului sa aplice corect conditional color target required | directioneaza downstream la families/processes compatibile, fara sa fie el insusi pricing | none direct; doar gate pentru ce lookup-uri de finish vor fi necesare mai tarziu | da | `RETURN_CANT_FINISH_MISSING` | raman color, layer groups, perimeter, confirmation state |
| `return_cant.color_target.oracal_code` | `components.return_cant.color_target.oracal_code` | `return_cant` | selector culoare Oracal cand finish-ul cere wrap | `missing` sau `hydrated` | operator confirma codul Oracal | `Review > Finisaje > cant fields` | inchide blockerul conditional de color target pentru caz Oracal | permite downstream material/process trace fara a promova UI registry la pricing | none in acest plan; culoarea poate influenta selectie material/process dar costul ramane in Pricing | da | `RETURN_CANT_COLOR_TARGET_MISSING` cand finish-ul cere Oracal | raman celelalte fields |
| `return_cant.color_target.ral_code` | `components.return_cant.color_target.ral_code` | `return_cant` | selector RAL cand finish-ul cere paint/RAL | `missing` | operator confirma codul RAL | `Review > Finisaje > cant fields` | inchide blockerul conditional de color target pentru caz RAL | directioneaza downstream catre proces/finish corect | none in acest plan; valorile de cost/tarif pentru paint raman in Pricing | da | `RETURN_CANT_COLOR_TARGET_MISSING` cand finish-ul cere RAL | raman celelalte fields |
| `return_cant.color_target.paint_target` | `components.return_cant.color_target.paint_target` | `return_cant` | selector target de vopsire cand finish-ul cere paint | `missing` | operator confirma paint target-ul | `Review > Finisaje > cant fields` | inchide blockerul conditional de paint target | ofera ProductDefinition un finish target explicit, nu inventat | none in acest plan | da | `RETURN_CANT_COLOR_TARGET_MISSING` cand finish-ul cere paint | raman celelalte fields |
| `return_cant.layer_group_ids` | `components.return_cant.layer_group_ids` | `return_cant` | mapare din `svg.selected_layer_refs[]` + layer roles confirmate | `missing` | operator confirma layer/group selection si legatura la componenta | `Pas 1 Straturi` + reflectare read-only in `Review > Finisaje` | muta evidence-ul din `context_only` la `component_truth_confirmed` pentru group ownership | downstream trace-ul poate explica ce litere/logo intra in cant scope | none | da | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | raman perimeter, confirmation state si orice field neconfirmat |
| `return_cant.confirmation_state` | `components.return_cant.confirmation_state` | `return_cant` | gate compus peste toate inputurile minime confirmed | `missing_component_field` | operator confirma explicit setul minim al componentei, nu doar un singur field | `Review > Finisaje` sau viitor gate read-only in `Confirmare` | deblocheaza doar cand toate required fields + dependency sunt confirmed | ofera downstream gate clar ca setul minim al componentei este complet | none | da | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | poate ramane blocat daca dependency sau alte fields lipsesc |
| `return_cant.perimeter_source` | `components.return_cant.perimeter_source` | `return_cant` | declaratie explicita de dependency pe `components.face.confirmed_perimeter` cu fallback context `quote_geometry.letter_perimeter_m` | `context_only` sau `manual_pending` | operator / Form System confirma ca sursa canonica este dependency-ul de la `face` | `Review > Finisaje` read-only + viitor field contract backend | mapperul nu mai trateaza root geometry ca singura dovada si separa clar dependency-ul de context | ProductDefinition poate consuma sursa declarata fara sa deduca local ownership | `return_cant.labor.cost_per_ml` indirect prin quantity basis validat | da | `RETURN_CANT_PERIMETER_MISSING` | ramane nevoie de `components.face.confirmed_perimeter` confirmed |
| `face.confirmed_perimeter` | `components.face.confirmed_perimeter` | `face` | geometry helper + layer roles confirmate + operator confirmation | `missing_explicit_dependency` sau `suggested` | operator confirma perimetrul de fata ca dependency truth, nu doar geometry context | `Pas 1 Straturi` + `Review geometry` + viitor Form System read model | dependency row trece din `dependency_missing/context_only` la `component_truth_confirmed` | permite consum downstream onest al cantitatii ml pentru return_cant | `return_cant.labor.cost_per_ml` si orice pricing downstream pe ml depind de acest quantity input, dar nu stocheaza cost aici | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | pot ramane fields component-owned neconfirmate |
| `return_cant.perimeter_dependency.face_confirmed_perimeter.*` | `components.return_cant.perimeter_dependency.face_confirmed_perimeter.*` | `derived_dependency` | mirror din `components.face.confirmed_perimeter.*` dupa confirmare | `missing` | nu se confirma separat; se reflecta numai dupa ce dependency source este confirmed | writer / adapter intern, read-only first | mapperul vede dependency explicit pe componenta, fara reconstructie locala | ProductDefinition poate urmari rationale trace fara sa inventeze geometry ownership | none | da | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | nicio valoare daca source-ul `face.confirmed_perimeter` nu este confirmed |

## 7. Pricing Boundary Plan

Regula explicita pentru toate field-urile din matrice:

1. Componenta stocheaza cel mult pricing lookup keys si dependency gates.
2. Componenta nu stocheaza cost material.
3. Componenta nu stocheaza cost manopera.
4. Componenta nu stocheaza pret sau tarif.
5. Valorile raman in Pricing Registry la `/inventory/pricing`.

Cheile minime necesare pentru faza urmatoare de integrare sunt:

```text
return_cant.material_profile.material_cost_per_ml
return_cant.labor.cost_per_ml
```

Acestea sunt intentii de lookup, nu valori.

## 8. Analyzer Boundary Plan

Analyzer ramane limitat la:

- `perimeter_m` suggestion;
- layer/group evidence;
- geometry source provenance.

Analyzer nu face:

- truth confirmation;
- price lookup;
- cost lookup;
- readiness unlock.

Consecinta:

- `quote_geometry.letter_perimeter_m` poate ramane in Product Truth doar ca context / fallback evidence;
- nu poate deveni `components.face.confirmed_perimeter` fara un pas explicit de confirmare.

## 9. Field Capture Sequence Recommendation

Ordinea recomandata pentru slice-urile urmatoare este:

1. contract adapter read-only pentru `components.face.confirmed_perimeter` si `components.return_cant.perimeter_source`
2. contract adapter read-only pentru `components.return_cant.depth_mm`, `finish_type`, `layer_group_ids`
3. contract adapter read-only pentru `components.return_cant.material_profile`
4. contract adapter read-only pentru `components.return_cant.color_target.*`
5. gate derivation pentru `components.return_cant.confirmation_state`
6. abia dupa toate acestea, evaluare noua pentru preview-readiness

## 10. Closed vs Remaining Blockers

Blockers inchisi de acest plan:

- lipsa unui plan clar pentru unde se captureaza fiecare field;
- confuzia intre formula component-owned si pricing authority;
- confuzia intre analyzer suggestion si Product Truth confirmation;
- confuzia intre ProductDefinition consequence si upstream truth owner.

Blockers ramasi dupa acest plan:

- nu exista inca adapter / writer pentru path-urile canonice `components.return_cant.*`;
- nu exista inca read model explicit pentru `components.face.confirmed_perimeter.*`;
- `material_profile` nu are inca selector/runtime truth writer dedicat;
- `layer_group_ids` nu are inca mapare canonica din selected layer refs catre componenta;
- `confirmation_state` nu are inca gate writer explicit.

## 11. Next Recommended Prompt

Prompt-ul recomandat dupa acest plan este:

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```
# Return Cant Intake V6 Variations Truth Capture Audit

## 1. Purpose

Acest document auditeaza variatiile reale `return_cant` deja existente in Intake V6 si le mapeaza catre Product Truth si Pricing keys, fara implementare runtime.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = variations_truth_capture_audit
```

Acest document nu implementeaza:

- component root;
- component quote;
- official price;
- commercial preview;
- adapter runtime;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB writes, seed sau migration;
- endpoint public nou;
- UI nou.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_VARIATIONS_AUDIT_READY_FOR_ADAPTER
```

Semnificatie exacta:

- variatiile reale existente in UI sunt suficient de clare pentru un slice urmator de `RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1`;
- adapterul trebuie sa mapeze variatiile reale observate, nu sa inventeze altele noi;
- verdictul READY nu inseamna ca Pricing este complet canonizat pentru toate finish-urile de cant;
- blocker-ele ramase sunt blocker-e de canonical Product Truth si de pricing alignment punctual, nu blocker-e pentru auditul de variatii.

## 3. Routes Audited

Rutele folosite in audit:

1. `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`
2. `http://127.0.0.1:3000/intake-v6/IR-MR18L96M/operator`
3. `http://127.0.0.1:3000/inventory/pricing`

Interpretare:

- `IR-MRBMAK7Z` este ruta relevanta pentru `TPL-VOLUMETRIC-LETTERS_v2` si arata shell-ul principal de litere volumetrice cu linked logo;
- `IR-MR18L96M` nu este ruta root corecta pentru Letters, dar este utila ca ruta read-only pentru contrastul `Vector Logo` deoarece expune clar un card de logo-only candidate;
- Pricing a fost verificat read-only pe pagina live, fara editari.

## 4. Observed UI Reality

### 4.1 `Vector Litere`

Pe ruta `IR-MRBMAK7Z`, zona `Review > Finisaje > Finisaje pe layer` afiseaza `Vector Litere` cu 4 grupuri:

- `pseudo maria (blue)`
- `pseudo soare (red)`
- `pseudo ana (green)`
- `pseudo gradinita (orange)`

Toate cele 4 grupuri afiseaza in cardul compact:

- un finish de fata separat;
- un rezumat de cant separat;
- cant rezumat actual `Alb · 60 mm`.

Rezumatul extras din UI real:

```text
pseudo maria (blue) -> Oracal 651 · 053 Light blue | Alb · 60 mm
pseudo soare (red) -> Oracal 641 · 020 Golden yellow | Alb · 60 mm
pseudo ana (green) -> Oracal 641 · 020 Golden yellow | Alb · 60 mm
pseudo gradinita (orange) -> Oracal 641 · 020 Golden yellow | Alb · 60 mm
```

Concluzie:

- fiecare `Vector Litere` poate avea cant propriu;
- structura actuala este per `group_key`, nu doar globala;
- finish-ul de cant si depth-ul de cant sunt deja per-row in UI.

### 4.2 `Vector Logo`

Pe ruta `IR-MR18L96M`, zona `Review > Finisaje > Finisaje pe layer` afiseaza `Vector Logo` cu 1 row:

- `Logo 1`

Cardul extins arata explicit:

- metoda de personalizare fata: `Fără finisaj`, `Oracal 641`, `Oracal 651`, `Oracal 8500`, `Print + laminare`;
- rola fata pentru metodele care o cer;
- metadata per row pentru sursa SVG si pozitie;
- confirmare `Vector Logo confirmat in Pasul 1`;
- aceeasi suprafata de cant ca la litere:
  - `Alb`
  - `Negru`
  - `Auriu`
  - `Argintiu`
  - `Vopsit RAL`
  - `Oracal 651`
  - depth `30 / 60 / 80 / 100`

Concluzie:

- fiecare `Vector Logo` poate avea cant propriu;
- cantul de logo este modelat per `artwork row`, nu prin configuratie globala-only;
- `Vector Logo` are mai multa variatie pe fata decat `Vector Litere`, dar cantul foloseste aceeasi taxonomie de baza.

## 5. Real Variation Inventory

### 5.1 Real cant finish options in current UI

Taxonomia explicita observata in cod/UI pentru `return_cant` este:

| UI option | Internal token | Color input? | Notes |
|---|---|---|---|
| `Alb` | `white_aluminum` | nu | stock/aluminum style finish |
| `Negru` | `black_aluminum` | nu | stock/aluminum style finish |
| `Auriu` | `gold_aluminum` | nu | stock/aluminum style finish |
| `Argintiu` | `mirror_silver` sau legacy `standard_aluminum` | nu | stock/aluminum style finish |
| `Vopsit RAL` | `ral_paint` | da, conditional | foloseste picker RAL |
| `Oracal 651` | `oracal_wrapped` | da, conditional | foloseste picker Oracal 651 |

Nu exista in UI actual:

- picker generic `paint_target` separat pentru cant;
- selector explicit `material_profile`;
- selector explicit `perimeter_source`;
- selector explicit `confirmation_state` pentru componenta `return_cant`.

### 5.2 Real depth options in current UI

Lista reala de depth observata in UI este:

| UI label | mm | source | state today |
|---|---|---|---|
| `30` | `30` | `ALLOWED_RETURN_DEPTH_MM` | selectable |
| `60` | `60` | `ALLOWED_RETURN_DEPTH_MM` | selectable; hidratat in rutele auditate |
| `80` | `80` | `ALLOWED_RETURN_DEPTH_MM` | selectable |
| `100` | `100` | `ALLOWED_RETURN_DEPTH_MM` | selectable |

Custom depth:

- UI-ul poate afisa si o valoare custom deja salvata, dar taxonomia owner actuala ramane `30 / 60 / 80 / 100`.

## 6. Vector Type Audit

### 6.1 `Vector Litere`

| question | answer |
|---|---|
| are nevoie de cant? | da, in shell-ul volumetric letters actual cantul este parte fireasca a row-ului |
| poate avea cant propriu? | da, per `letter_group_finish` row |
| are `layer_group_ids` proprii? | doar implicit prin `group_key`; nu exista inca path canonic `components.return_cant.layer_group_ids` |
| are perimeter propriu? | doar evidence partial; nu exista inca `components.face.confirmed_perimeter` per component truth |
| are `material_profile` propriu? | nu, lipseste field explicit |
| are depth proprie? | da, per row |
| are finish propriu? | da, per row |
| are color target propriu? | da, conditional pentru `Oracal 651` si `RAL` |
| are pricing key propriu? | material da, derivat din depth; labor nu, este inca generic per ml |

### 6.2 `Vector Logo`

| question | answer |
|---|---|
| are nevoie de cant? | poate avea, iar UI-ul actual deja expune blocul de cant pe fiecare row de logo |
| poate avea cant propriu? | da, per `artwork_finish` row |
| are `layer_group_ids` proprii? | doar implicit prin `layer_key`; nu exista inca path canonic `components.return_cant.layer_group_ids` |
| are perimeter propriu? | partial, prin row perimeter/evidence in servicii helper; nu exista inca dependency truth explicit |
| are `material_profile` propriu? | nu, lipseste field explicit |
| are depth proprie? | da, per row |
| are finish propriu? | da, per row |
| are color target propriu? | da, conditional pentru `Oracal 651` si `RAL` |
| are pricing key propriu? | material da, derivat din depth; labor generic per ml |

## 7. Mandatory Audit Matrix

| ui_surface | vector_type | variation | field_key | current_ui_source | current_state | product_truth_path | pricing_key_needed | pricing_boundary | blocker | recommended_action |
|---|---|---|---|---|---|---|---|---|---|---|
| `Review > Finisaje > Vector Litere` | `Vector Litere` | stock cant finish | `return_finish_type` | `letter_group_finishes[].return_finish_type` | hydrated per row | `components.return_cant.finish_type` | none direct for stock finish token; material/labor keys downstream | price stays in Pricing | finish stays non-canonical until adapter | map directly from row token to canonical finish path |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | depth 30/60/80/100 | `return_depth_mm` | `letter_group_finishes[].return_depth_mm` | hydrated per row | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | material cost stays in Pricing | no canonical writer yet | adapter should map row depth to canonical depth |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | Oracal cant | `return_oracal_code` | conditional `ColorRegistrySelect` on row | missing or hydrated depending on row | `components.return_cant.color_target.oracal_code` | currently needs Oracal wrap material alignment; live page has `MAT-ORACAL-651`, preview rules use `edge_cant_oracal_651` | cost stays in Pricing | cant Oracal wrap not aligned cleanly to live Pricing Registry key | adapter captures truth; follow-up pricing alignment should replace preview-only owner rule |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | RAL cant | `return_oracal_code`/`return_oracal_name` used as RAL payload | conditional `ColorRegistrySelect` on row | missing or hydrated depending on row | `components.return_cant.color_target.ral_code` | `MAT-VOPSEA-RAL` | cost stays in Pricing | no canonical `paint_target`; color field naming still legacy | adapter should map legacy row color into canonical `ral_code`; keep `paint_target` blocked |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | row ownership | `group_key` | `letter_group_finishes[].group_key` | confirmed as UI row identity, non-canonical for component truth | `components.return_cant.layer_group_ids[]` | none | no price in component | missing canonical layer-group path | adapter should map `group_key` into canonical layer ownership evidence |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | row confirmation | `confirmed` | `letter_group_finishes[].confirmed` | confirmed or hydrated row-level only | `components.return_cant.confirmation_state` | none | no price in component | row confirmed is not component confirmed | derive canonical component confirmation later, not from single row alone |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | stock cant finish | `return_finish_type` | `artwork_finishes[].return_finish_type` | hydrated/manual per row | `components.return_cant.finish_type` | none direct | price stays in Pricing | no canonical writer yet | adapter should support artwork rows same as letters |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | depth 30/60/80/100 | `return_depth_mm` | `artwork_finishes[].return_depth_mm` | hydrated/manual per row | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | material cost stays in Pricing | no canonical writer yet | adapter should support depth per artwork row |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | Oracal cant | `return_oracal_code` | conditional `ColorRegistrySelect` on artwork row | missing or hydrated | `components.return_cant.color_target.oracal_code` | same gap as letters: `MAT-ORACAL-651` live vs preview-only `edge_cant_oracal_651` | cost stays in Pricing | live cant Oracal key model not yet clean | capture truth first, then align pricing source |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | RAL cant | `return_oracal_code`/`return_oracal_name` used as RAL payload | conditional `ColorRegistrySelect` on artwork row | missing or hydrated | `components.return_cant.color_target.ral_code` | `MAT-VOPSEA-RAL` | cost stays in Pricing | `paint_target` missing and naming legacy | capture `ral_code`; keep paint-target blocker explicit |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | row ownership | `layer_key` | `artwork_finishes[].layer_key` | confirmed as row identity, non-canonical for component truth | `components.return_cant.layer_group_ids[]` | none | no price in component | no canonical layer ownership writer | adapter should map artwork `layer_key` into layer ownership evidence |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | row confirmation | `confirmed` and `Confirmat in Pasul 1` | `artwork_finishes[].confirmed` plus layer role step-one confirmation | step-one confirmed or row confirmed | `components.return_cant.confirmation_state` | none | no price in component | step-one confirm is not component confirm | do not promote step-one badge to component confirmed |
| `Review > Finisaje > Return/cant diagnostic` | `Vector Litere` + `Vector Logo` | dependency source | `quote_geometry.letter_perimeter_m` | readonly mapper evidence | context_only | `components.return_cant.perimeter_source` + `components.face.confirmed_perimeter` | `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING` depend on quantity input | price stays in Pricing | canonical dependency not yet written | adapter should keep geometry as evidence-only and wait for face confirmed perimeter |
| `Review > Finisaje > Return/cant diagnostic` | `Vector Litere` + `Vector Logo` | component confirmation gate | `components.return_cant.confirmation_state` | not present in runtime writer | missing | `components.return_cant.confirmation_state` | none | no price in component | blocker remains explicit | adapter should emit blocked canonical path until owner-confirmed fields exist |
| `Pricing Registry` | `Vector Litere` + `Vector Logo` | material variants by depth | profile material key | live Pricing page | owner-confirmed | downstream material resolver only | `MAT-PROFIL-LATERAL-LITERE-30MM`, `-60MM`, `-80MM`, `-100MM` | all costs remain in Pricing | none for material depth variants | use current live codes exactly, not synthetic alias names |
| `Pricing Registry` | `Vector Litere` + `Vector Logo` | labor operations | operation keys | live Pricing page | owner-confirmed | downstream operation resolver only | `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING` | all costs remain in Pricing | no depth-specific labor variant today | adapter should not invent depth-specific labor keys |

## 8. Cant Depth Variation Audit

| UI name | mm | source | state | proposed Product Truth path | pricing key needed | separate material cost in Pricing? | separate labor cost in Pricing? | blocker |
|---|---|---|---|---|---|---|---|---|
| `30 mm` | `30` | `ALLOWED_RETURN_DEPTH_MM` / row select | selectable | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-30MM` | da | nu, labor generic | no canonical writer |
| `60 mm` | `60` | `ALLOWED_RETURN_DEPTH_MM` / row select | selectable; route shows saved/hydrated | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-60MM` | da | nu, labor generic | no canonical writer |
| `80 mm` | `80` | `ALLOWED_RETURN_DEPTH_MM` / row select | selectable | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-80MM` | da | nu, labor generic | no canonical writer |
| `100 mm` | `100` | `ALLOWED_RETURN_DEPTH_MM` / row select | selectable | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-100MM` | da | nu, labor generic | no canonical writer |

Owner conclusion:

- Pricing are cost separat per latime pentru material;
- Pricing nu are in acest moment cost separat per latime pentru labor;
- laborul actual este un pair generic per ml:
  - `RETURN_PROFILE_MACHINE_FORMING`
  - `RETURN_PROFILE_FACE_BONDING`

Aceasta nu blocheaza truth capture adapter-ul, dar blocheaza orice model fals care ar inventa `labor_cost_per_ml` per depth fara owner/runtime evidence.

## 9. Finish Audit

| finish | where visible in UI | how it saves now | how it confirms now | Product Truth path | pricing key needed | price/cost remains in Pricing | blocker |
|---|---|---|---|---|---|---|---|
| `Alb` | letters + logo cant select | row `return_finish_type` | row `confirmed` only, not component confirmed | `components.return_cant.finish_type` | none direct beyond profile + labor downstream | da | no canonical writer |
| `Negru` | letters + logo cant select | row `return_finish_type` | row `confirmed` only | `components.return_cant.finish_type` | none direct beyond profile + labor downstream | da | no canonical writer |
| `Auriu` | letters + logo cant select | row `return_finish_type` with `gold_aluminum` | row `confirmed` only | `components.return_cant.finish_type` | none direct beyond profile + labor downstream | da | no canonical writer |
| `Argintiu` | letters + logo cant select | row `return_finish_type` `mirror_silver` / legacy `standard_aluminum` | row `confirmed` only | `components.return_cant.finish_type` | none direct beyond profile + labor downstream | da | legacy alias normalization needed |
| `Vopsit RAL` | letters + logo cant select + RAL picker | legacy row color fields | row `confirmed` only | `components.return_cant.color_target.ral_code` | `MAT-VOPSEA-RAL` plus generic labor keys | da | no `paint_target`; legacy field names |
| `Oracal 651` | letters + logo cant select + Oracal picker | legacy row color fields | row `confirmed` only | `components.return_cant.color_target.oracal_code` | live material family evidence `MAT-ORACAL-651`, but current cant preview uses `edge_cant_oracal_651` owner rule | da | pricing alignment gap for cant-specific Oracal wrap |

Important clarification:

- `culoare aleasa din lista` exista numai ca picker conditionat pentru Oracal si RAL;
- nu exista un al treilea color picker generic separat pentru stock finishes;
- `paint_target` nu exista ca field UI separat in acest moment.

## 10. Current Save / Hydrate / Confirm Behavior

### 10.1 Letters

- sursa curenta: `finish_setup.letter_group_finishes[]`;
- depth si finish de cant se salveaza per group row;
- orice patch pe row seteaza `confirmed: false` pana la reconfirmare;
- `group.confirmed === true` inseamna row confirmed, nu `components.return_cant.confirmation_state = confirmed`.

### 10.2 Logo

- sursa curenta: `finish_setup.artwork_finishes[]`;
- depth si finish de cant se salveaza per artwork row;
- logo are si confirmare separata pentru fata/personalizare;
- `Confirmat in Pasul 1` este confirmare de strat/rol, nu confirmare canonica a componentei `return_cant`.

### 10.3 Product Truth impact

Current save/hydrate/confirm states raman:

- `hydrated`;
- `manual`;
- `context_only`;
- `suggested`;
- `row_confirmed_only`.

Acestea nu devin automat:

- `components.return_cant.confirmation_state = confirmed`;
- `components.face.confirmed_perimeter`;
- `components.return_cant.material_profile`.

## 11. Pricing Mapping Audit

### 11.1 Live Pricing evidence

Pricing page live a confirmat explicit:

- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `MAT-VOPSEA-RAL`
- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`

### 11.2 Actual audited key model

Modelul actual real, aliniat la UI si Pricing, este:

```text
material profile by depth:
  30 -> MAT-PROFIL-LATERAL-LITERE-30MM
  60 -> MAT-PROFIL-LATERAL-LITERE-60MM
  80 -> MAT-PROFIL-LATERAL-LITERE-80MM
  100 -> MAT-PROFIL-LATERAL-LITERE-100MM

generic labor keys per ml:
  RETURN_PROFILE_MACHINE_FORMING
  RETURN_PROFILE_FACE_BONDING

conditional paint material:
  MAT-VOPSEA-RAL
```

### 11.3 Oracal cant wrap gap

Audit finding important:

- UI permite `Oracal 651` pentru cant la litere si logo;
- Pricing page live expune `MAT-ORACAL-651` ca material general de vinyl;
- preview-ul de cant foloseste inca `shared_edge_cant_rules` cu `material_key = edge_cant_oracal_651` si owner price fallback, nu un pricing-registry cant key curat.

Consecinta:

- truth capture adapter-ul poate captura legitim `oracal_code`;
- adapter-ul nu trebuie sa inventeze un pricing key nou;
- follow-up de pricing alignment este necesar pentru `Oracal 651` pe cant daca se vrea consum/commercial boundary complet curat.

Acesta este un gap real, dar nu blocheaza auditul de variatii.

## 12. Formula Without Prices

Formula component-owned ramane:

```text
component: return_cant
quantity_basis: ml
required_quantity_input: components.face.confirmed_perimeter.value
analyzer_required_input: perimeter_m suggestion
quantity_formula: return_cant.quantity_ml = components.face.confirmed_perimeter.value
pricing_required_keys:
  - return_cant.<variation>.material_cost_per_ml
  - return_cant.<variation>.labor_cost_per_ml
pricing_boundary:
  - material/labor costs remain in /inventory/pricing
  - component stores no cost and no price values
```

Audit clarification for current runtime:

- `return_cant.<variation>.material_cost_per_ml` este sustinut real prin material variants per depth;
- `return_cant.<variation>.labor_cost_per_ml` nu este sustinut literal de Pricing live;
- runtime-ul actual are generic labor keys per ml, nu labor-per-depth keys;
- adapter-ul de truth capture trebuie sa pastreze taxonomia reala si sa nu inventeze chei noi.

## 13. Pricing Boundary Confirmation

Ramane obligatoriu:

1. cost material ramane in Pricing;
2. cost manopera ramane in Pricing;
3. pret/tarif ramane in Pricing;
4. cost separat pe latime/variatie de cant pentru material ramane in Pricing;
5. orice reguli comerciale interne raman in Pricing;
6. componenta nu stocheaza cost sau pret.

## 14. Analyzer Boundary Confirmation

Ramane obligatoriu:

1. analyzer sugereaza perimetrul;
2. analyzer nu confirma truth;
3. analyzer nu da pret/cost;
4. Product Truth confirma dependency-ul de perimetru;
5. `quote_geometry.letter_perimeter_m` nu devine `components.face.confirmed_perimeter` prin audit.

## 15. Remaining Blockers

Blockers ramasi dupa audit:

1. lipseste runtime writer pentru `components.return_cant.*`;
2. lipseste runtime writer pentru `components.face.confirmed_perimeter.*`;
3. lipseste `material_profile` explicit in UI/runtime;
4. lipseste `paint_target` explicit pentru cant;
5. lipseste canonical `layer_group_ids` pentru a uni letters/artwork rows in component truth;
6. `Confirmat in Pasul 1` si `group.confirmed` nu sunt echivalente cu `components.return_cant.confirmation_state`;
7. `Oracal 651` pentru cant nu este inca aliniat curat la un pricing-registry cant key dedicat, fiind partial pe `shared_edge_cant_rules` owner pricing path.

## 16. Why READY, Not BLOCKED

Auditul este READY pentru adapter deoarece:

1. variatiile reale sunt observabile si stabile in UI;
2. depth taxonomy este explicita si are mapare live in Pricing;
3. litere si logo folosesc aceeasi taxonomie de baza pentru cant;
4. diferentele relevante dintre `Vector Litere` si `Vector Logo` sunt clare si pot fi mapate read-only;
5. blocker-ele ramase sunt de canonical write/alignment, nu de necunoastere a variatiilor.

## 17. Next Recommended Prompt

Prompt-ul recomandat dupa acest audit este:

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```

Cu instructiune explicita suplimentara:

```text
Adapterul trebuie sa mapeze variatiile reale observate in UI, fara sa inventeze labor keys per depth si fara sa promoveze step-one/logo/geometry evidence la truth confirmed.
```
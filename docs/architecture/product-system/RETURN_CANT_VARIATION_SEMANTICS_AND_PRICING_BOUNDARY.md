# Return Cant Variation Semantics And Pricing Boundary

## 1. Purpose

Acest document corecteaza semantic contractul variatiilor `return_cant` auditate anterior, fara modificari de runtime.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = return_cant
mode = variation_semantics_fix
```

Acest document nu implementeaza:

- adapter runtime;
- Product Truth writes;
- UI nou;
- Pricing changes;
- component quote;
- component root;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan;
- DB / seed / migration.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_VARIATION_SEMANTICS_READY_FOR_ADAPTER
```

Semnificatie:

- adapterul urmator are acum semantica owner-corecta pentru a interpreta optiunile UI existente;
- `Alb`, `Negru`, `Auriu`, `Argintiu` nu mai trebuie tratate ca finisaje costabile separat;
- `Oracal 651` si `Vopsit RAL` raman singurele variatii de extra finish cost semantic;
- Pricing ramane sursa unica pentru cost si pret.

## 3. Core Semantic Correction

Auditul anterior a folosit termenul generic `stock finish` pentru preset-urile:

- `Alb`
- `Negru`
- `Auriu`
- `Argintiu`

Corectia owner obligatorie este:

1. aceste optiuni nu sunt `finisaje costabile separat`;
2. ele reprezinta `Culoare Stoc` pentru profil / cant deja vopsit sau disponibil ca varianta operationala de furnizor;
3. costul lor vine din profilul material si din latimea / adancimea cantului;
4. ele nu trebuie sa emita pricing key separat pentru `finish extra`;
5. operatorul trebuie sa vada culoarea aleasa, chiar daca nu exista cost suplimentar de finish.

## 4. Corrected Semantic Variants

Variatiile reale si corectate sunt:

### 4.1 `stock_color`

- UI label semantic: `Culoare Stoc`
- current UI options:
  - `Alb`
  - `Negru`
  - `Auriu`
  - `Argintiu`
- extra finish cost: `false`
- cost source: profil / latime cant
- component role: retine eticheta operationala de culoare, nu costul

### 4.2 `oracal`

- current UI option: `Oracal 651`
- extra finish cost: `true`
- cost source: Pricing
- width matters: `true`
- UI selector preserved:
  - cod Oracal
  - culoare vizuala

### 4.3 `ral_paint`

- current UI option: `Vopsit RAL`
- extra finish cost: `true`
- cost source: Pricing
- width matters: `maybe/confirm from Pricing`
- UI selector preserved:
  - cod RAL
  - culoare vizuala

## 5. Mandatory Matrix

| current_ui_option | corrected_semantic_variant | stock_color_label | extra_finish_cost | pricing_source | width_affects_cost | product_truth_target | adapter_rule | blocker |
|---|---|---|---|---|---|---|---|---|
| `Alb` | `stock_color` | `Alb` | `false` | `material_profile_width` | `true` | `components.return_cant.instances.<instance_key>.finish_variant.type = stock_color` + `stock_color_label = Alb` | emit `stock_color`; do not emit separate finish pricing key | no runtime Product Truth writer yet |
| `Negru` | `stock_color` | `Negru` | `false` | `material_profile_width` | `true` | `components.return_cant.instances.<instance_key>.finish_variant.type = stock_color` + `stock_color_label = Negru` | emit `stock_color`; do not emit separate finish pricing key | no runtime Product Truth writer yet |
| `Auriu` | `stock_color` | `Auriu` | `false` | `material_profile_width` | `true` | `components.return_cant.instances.<instance_key>.finish_variant.type = stock_color` + `stock_color_label = Auriu` | emit `stock_color`; do not emit separate finish pricing key | no runtime Product Truth writer yet |
| `Argintiu` | `stock_color` | `Argintiu` | `false` | `material_profile_width` | `true` | `components.return_cant.instances.<instance_key>.finish_variant.type = stock_color` + `stock_color_label = Argintiu` | emit `stock_color`; normalize legacy `standard_aluminum` / `mirror_silver` into stock color semantics | alias normalization still required |
| `Oracal 651` | `oracal` | n/a | `true` | `/inventory/pricing` | `true` | `components.return_cant.instances.<instance_key>.finish_variant.type = oracal` + `oracal_code` | preserve selector code + color; emit required finish pricing key only if real aligned key exists; otherwise emit alignment blocker | cant Oracal pricing key alignment remains incomplete |
| `Vopsit RAL` | `ral_paint` | n/a | `true` | `/inventory/pricing` | `maybe/confirm from Pricing` | `components.return_cant.instances.<instance_key>.finish_variant.type = ral_paint` + `ral_code` + optional `paint_target` | preserve selector code + color; emit RAL pricing key only if real aligned key exists; otherwise emit alignment blocker | `paint_target` missing and width-to-price semantic not fully proven |

## 6. Rules Locked By This Matrix

### 6.1 Stock color rules

Pentru `Alb`, `Negru`, `Auriu`, `Argintiu`:

1. `corrected_semantic_variant = stock_color`
2. `extra_finish_cost = false`
3. `pricing_source = material_profile_width`
4. `width_affects_cost = true`
5. componenta nu stocheaza cost sau pret
6. adapterul nu emite `finish_extra` pricing key separat
7. adapterul poate emite `stock_color_label`

### 6.2 Oracal rules

Pentru `Oracal 651`:

1. `corrected_semantic_variant = oracal`
2. `extra_finish_cost = true`
3. `pricing_source = /inventory/pricing`
4. `width_affects_cost = true`
5. selectorul UI cu cod + culoare se pastreaza
6. adapterul trebuie sa emita pricing key real sau blocker de alignment
7. adapterul nu inventeaza pricing key

### 6.3 RAL paint rules

Pentru `Vopsit RAL`:

1. `corrected_semantic_variant = ral_paint`
2. `extra_finish_cost = true`
3. `pricing_source = /inventory/pricing`
4. `width_affects_cost = maybe/confirm from Pricing`
5. selectorul UI cu cod + culoare se pastreaza
6. adapterul trebuie sa emita pricing key real sau blocker de alignment
7. adapterul nu inventeaza pricing key

## 7. Product Truth Semantic Target

Targetul semantic pentru viitorul adapter este:

```text
components.return_cant.instances.<instance_key>.finish_variant.type =
  stock_color | oracal | ral_paint

components.return_cant.instances.<instance_key>.finish_variant.stock_color_label
components.return_cant.instances.<instance_key>.finish_variant.oracal_code
components.return_cant.instances.<instance_key>.finish_variant.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint_target
components.return_cant.instances.<instance_key>.depth_mm
components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.finish_extra
```

Clarificari obligatorii:

1. `pricing_keys.*` sunt referinte, nu valori de pret sau cost;
2. `instances.<instance_key>` este viitorul mod corect de a exprima row ownership pentru letters si artwork rows, fara sa inventeze component root separat;
3. `paint_target` poate ramane lipsa / blocked cand UI-ul nu il furnizeaza;
4. `stock_color_label` este informatie operationala, nu pricing value.

## 8. Instance Key Rule

Adapterul urmator trebuie sa derive `instance_key` din row ownership-ul existent:

- pentru `Vector Litere`: din `letter_group_finishes[].group_key`
- pentru `Vector Logo`: din `artwork_finishes[].layer_key`

Regula:

- nu unifica fortat `Vector Litere` si `Vector Logo` intr-un singur field global;
- nu pierde row-level ownership;
- nu confunda `group_key` sau `layer_key` cu `components.face.confirmed_perimeter`.

## 9. Future Adapter Rule

Adapterul urmator trebuie sa transforme:

- `Alb` -> `stock_color`
- `Negru` -> `stock_color`
- `Auriu` -> `stock_color`
- `Argintiu` -> `stock_color`
- `Oracal 651` -> `oracal`
- `Vopsit RAL` -> `ral_paint`

Adapterul NU trebuie sa transforme:

- `Alb`, `Negru`, `Auriu`, `Argintiu` in pricing keys de finish separat;
- `Culoare Stoc` in cost suplimentar;
- lipsa de pricing key Oracal sau RAL in valoare estimata inventata;
- selectorul UI de Oracal sau RAL in text simplu;
- `quote_geometry.letter_perimeter_m` in `components.face.confirmed_perimeter`.

## 10. Pricing Boundary

Boundary-ul explicit ramane:

1. cost material ramane in Pricing;
2. cost manopera ramane in Pricing;
3. cost Oracal ramane in Pricing;
4. cost RAL / vopsire ramane in Pricing;
5. componenta nu stocheaza pret sau cost;
6. componenta doar cere pricing keys.

### 10.1 Stock color boundary

Pentru `stock_color`:

- nu exista cost suplimentar de finish;
- costul material vine din varianta de profil pe latime;
- laborul ramane in Pricing, dar nu este un finish extra key.

### 10.2 Oracal boundary

Pentru `oracal`:

- latimea conteaza pentru consumul material;
- Pricing trebuie sa ramana autoritatea pentru costul Oracal;
- daca cheia de pricing nu este clar aliniata, adapterul emite blocker, nu estimare inventata.

### 10.3 RAL boundary

Pentru `ral_paint`:

- Pricing trebuie sa ramana autoritatea pentru costul de vopsire;
- daca width sensitivity nu este suficient de clara din Pricing, adapterul pastreaza blockerul de alignment;
- adapterul nu deduce singur formula finala de pret.

## 11. UI Preservation Rule

Se pastreaza explicit:

1. selectorul Oracal cu cod + culoare;
2. selectorul RAL cu cod + culoare;
3. diferentele actuale dintre row-urile `Vector Litere` si `Vector Logo`.

Nu se face:

1. inlocuire cu input text simplu pentru Oracal;
2. inlocuire cu input text simplu pentru RAL;
3. reducerea `stock_color` la text de pricing;
4. simplificare care ar pierde semantica operatorului.

Pentru `stock_color`:

- UI viitor poate ramane lista sau text operational controlat;
- nu trebuie sa introduca cost suplimentar semantic.

## 12. Alignment With Existing Plan

Acest document rafineaza semantic planul anterior astfel:

1. `finish_type` nu mai este suficient conceptual pentru a descrie cele 3 familii semantice;
2. `finish_variant.type` este modelul semantic mai corect pentru adapterul urmator;
3. `stock_color` trebuie tratat separat de `oracal` si `ral_paint`;
4. `pricing_keys.finish_extra` este optional si trebuie omis pentru `stock_color`.

## 13. Remaining Blockers

Blockers ramasi dupa aceasta clarificare:

1. nu exista inca writer runtime pentru `components.return_cant.instances.*`;
2. nu exista inca `material_profile` explicit;
3. nu exista inca `paint_target` explicit;
4. Oracal cant pricing alignment ramane partial pe `shared_edge_cant_rules`;
5. relatia exacta width-to-price pentru `ral_paint` nu este complet dovedita din Pricing live.

Aceste blockers nu opresc clarificarea semantica a adapterului.

## 14. Next Recommended Prompt

Prompt-ul recomandat dupa acest document este:

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```

Cu instructiunea obligatorie:

```text
Mapeaza preset-urile Alb/Negru/Auriu/Argintiu la stock_color fara extra finish pricing key. Pastreaza Oracal si RAL ca variatii costabile separat numai cand exista pricing key real sau blocker explicit. Nu inventa pricing keys.
```
# Return Cant Component Confirmation Contract

## 1. Purpose

Acest document defineste contractul canonic pentru:

```text
components.return_cant.instances.<instance_key>.confirmation_state
```

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = component_confirmation_contract
root_template = TPL-VOLUMETRIC-LETTERS_v2
```

Acest document nu implementeaza:

- runtime writer;
- Product Truth writes;
- UI changes;
- Pricing changes;
- adapter changes;
- runtime DB changes;
- seed / migration;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_READY
```

Semnificatie exacta:

1. semantica pentru `return_cant` component confirmation poate fi definita docs-only, fara writer runtime;
2. semnalele actuale de workflow pot fi separate clar de confirmarea canonica de componenta;
3. starea `confirmed` poate fi constransa explicit prin reguli owner-safe;
4. urmatorul blocker real ramane sursa valida pentru `geometry.confirmed_perimeter_m`, nu definirea starilor de confirmare.

## 3. Why This Contract Is Ready

Auditul actual confirma urmatoarele:

1. `layer_role_setup.confirmation_status` si `layer.confirmation_state` reprezinta confirmare Step 1 pentru layer ownership, nu confirmare de componenta `return_cant`;
2. `finish_setup.confirmed` reprezinta confirmarea blocului Review pentru setup de finisaje, nu confirmare canonica de componenta;
3. `letter_group_finishes[].confirmed` si `artwork_finishes[].confirmed` reprezinta confirmarea unui rand / unei alegeri UI, nu confirmare de componenta Product Truth;
4. `product_composition_confirmed.confirmed` reprezinta confirmarea compozitiei propuse la nivel de workspace, nu confirmare per instanta `return_cant`;
5. `internal_draft_quote_confirmed` este un gate separat pentru draft comercial intern si depinde de `finish_setup.confirmed`, dar nu defineste Product Truth final;
6. mapper-ul readonly si adapterul readonly trateaza deja lipsa `components.return_cant...confirmation_state` ca blocker explicit, deci lipsa contractului este de semantics/ownership, nu de loc in model.

Concluzie:

```text
existing confirmation signals != canonical return_cant component confirmation
```

## 4. Confirmation State Contract

Campul final este:

```text
components.return_cant.instances.<instance_key>.confirmation_state
```

Setul final de valori este:

- `missing`
- `draft`
- `blocked`
- `confirmed`

Camp optional recomandat:

```text
components.return_cant.instances.<instance_key>.confirmation_source
```

Valori permise pentru `confirmation_source` cand `confirmation_state = confirmed`:

- `operator_component_confirmation`
- `system_migration_verified`
- `imported_verified_truth`

Valori interzise ca sursa finala de `confirmed`:

- `step1_layer_confirmation`
- `finish_setup_confirmation`
- `row_confirmation`
- `analyzer_evidence`

## 5. Meaning Of Each State

### 5.1 `missing`

Instanta nu are inca date suficiente pentru evaluare normala.

Exemple:

- lipseste `instance_key` stabil;
- lipseste `source_kind` / `source_ref`;
- nu exista finish intent recognoscibil pentru instanta;
- nu exista mapping util catre `layer_group_ids` sau datele sursa sunt prea incomplete.

### 5.2 `draft`

Instanta are intent recognoscibil si shape partial, dar nu exista confirmare explicita de componenta.

Exemple:

- exista `return_finish_type` si `width_mm`;
- exista selectie de Oracal / RAL / stock color;
- exista randuri UI confirmate sau finish setup salvat;
- lipseste inca actiunea explicita de component confirmation ori lipsesc dependencies esentiale.

### 5.3 `blocked`

Instanta este suficient de formata incat putem numi clar ce lipseste, dar downstream unlock este interzis.

Exemple:

- lipsesc pricing keys obligatorii pentru varianta aleasa;
- `geometry.confirmed_perimeter_m` nu exista dintr-o sursa valida;
- exista numai evidence geometry;
- lipseste layer mapping final;
- exista conflict intre surse sau exista doar path legacy.

### 5.4 `confirmed`

Instanta poate fi tratata ca Product Truth component-level confirmat numai daca toate conditiile obligatorii sunt indeplinite si confirmarea a fost facuta explicit la nivelul componentei / instantei.

## 6. Required Conditions For `confirmed`

`components.return_cant.instances.<instance_key>.confirmation_state` poate deveni `confirmed` doar daca exista toate:

1. `instance_key` stabil si owner-safe;
2. `source_kind` valid;
3. `source_ref` valid;
4. `layer_group_ids` sau mapping echivalent valid si canonizat;
5. `material_profile.width_mm` valid;
6. `finish_variant.type` valid;
7. pricing keys obligatorii prezente pentru varianta aleasa;
8. `geometry.confirmed_perimeter_m` valid dintr-o sursa acceptata de contract;
9. actiune explicita de component confirmation;
10. `confirmation_source` permis pentru starea finala;
11. fara blockers active;
12. instanta nu traieste doar pe path-uri legacy.

Regula compacta:

```text
complete canonical instance + valid confirmed perimeter + explicit component confirmation + zero active blockers => confirmed
```

## 7. What Cannot Set `confirmed`

Urmatoarele nu pot promova automat `confirmation_state = confirmed`:

1. Pasul 1 `layer_role_setup.confirmation_status = complete`;
2. `layer.confirmation_state = confirmed`;
3. `finish_setup.confirmed = true`;
4. `letter_group_finishes[].confirmed = true`;
5. `artwork_finishes[].confirmed = true`;
6. prezenta unei selectii Oracal / RAL / stock color;
7. prezenta pricing keys in evidence;
8. analyzer perimeter;
9. `quote_geometry.letter_perimeter_m`;
10. `product_composition_confirmed.confirmed = true`;
11. `internal_draft_quote_confirmed = true`.

Regula de disciplina:

```text
workflow confirmation, row confirmation, selection presence, pricing presence, and analyzer evidence are insufficient as final component confirmation
```

## 8. Canonical Confirmation Blockers

Lista canonica minima recomandata pentru blocker-ele de confirmation:

- `RETURN_CANT_INSTANCE_KEY_MISSING`
- `RETURN_CANT_SOURCE_KIND_MISSING`
- `RETURN_CANT_SOURCE_REF_MISSING`
- `RETURN_CANT_LAYER_MAPPING_MISSING`
- `RETURN_CANT_PROFILE_WIDTH_MISSING`
- `RETURN_CANT_FINISH_VARIANT_INCOMPLETE`
- `RETURN_CANT_PRICING_KEYS_MISSING`
- `RETURN_CANT_CONFIRMED_PERIMETER_MISSING`
- `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING`
- `RETURN_CANT_GEOMETRY_EVIDENCE_ONLY`
- `RETURN_CANT_LEGACY_PATH_ONLY`

Semantica recomandata:

- `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING` exista cand toate celelalte dependencies pot fi aproape gata, dar lipseste actiunea explicita de confirmare a componentei;
- `RETURN_CANT_GEOMETRY_EVIDENCE_ONLY` exista cand avem doar analyzer perimeter sau `quote_geometry.letter_perimeter_m`, nu confirmed perimeter contract-safe;
- `RETURN_CANT_LEGACY_PATH_ONLY` exista cand datele sunt disponibile doar prin `components.returnCant` sau alte path-uri transitional-only.

## 9. Signal Matrix

| signal | current_source | can_set_confirmation_state | target_state | reason | risk_if_used_as_confirmed |
|---|---|---|---|---|---|
| Step 1 confirmed | `layer_role_setup.confirmation_status`, `layers[].confirmation_state` | no | `draft` or `blocked` | confirma ownership-ul layerelor, nu component truth-ul `return_cant` | poate promova gresit selectie de layer la confirmare de componenta |
| layer role selected | `confirmed_role` / `auto_role` | no | `draft` | semnal structural util pentru source mapping | poate ascunde lipsa confirmarii explicite si a dependencies canonice |
| finish_setup.confirmed | `finish_setup.confirmed` | no | `draft` or `blocked` | confirma blocul Review ca payload de workflow | poate fi confundat cu Product Truth final, desi nu verifica component-level semantics |
| row confirmed | `letter_group_finishes[].confirmed`, `artwork_finishes[].confirmed` | no | `draft` | confirma un rand / o alegere de UI | poate promova o selectie locala la adevar component-level |
| Oracal selected | `return_oracal_code`, row fields | no | `draft` | semnal de intent pentru vinyl | selectie de culoare fara perimeter/layer mapping/pricing complete |
| RAL selected | `return_oracal_code` reinterpretat ca RAL | no | `draft` | semnal de intent pentru paint | selectie de culoare fara confirmed geometry si fara action de component confirmation |
| stock color selected | `return_finish_type` normalized | no | `draft` | finish intent recognoscibil | intentul nu inseamna adevar component-level confirmat |
| pricing keys present | readonly pricing evidence / runtime registry alignment | no | `draft` or `blocked` | dependency obligatorie, dar nu actiune de confirmare | poate confunda readiness comercial cu component truth confirmation |
| analyzer perimeter present | analyzer / preview geometry evidence | no | `blocked` | evidence util pentru estimare | analyzer evidence nu este sursa owner-safe pentru confirmed perimeter |
| quote_geometry.letter_perimeter_m present | `quote_geometry` | no | `blocked` | context geometry util | camp contextual, nu confirmed component perimeter |
| product composition confirmed | `product_composition_confirmed.confirmed` | no | `draft` or `blocked` | confirma compozitia propusa la nivel workspace | poate promova confirmarea ansamblului la confirmare falsa pe fiecare instanta `return_cant` |
| explicit component confirmation | viitor `confirmation_source` + action scoped to instance | yes | `confirmed` only if all prerequisites pass; otherwise `blocked` | singura sursa owner-safe pentru component truth final | fara guard-uri stricte poate confirma date incomplete sau legacy-only |

## 10. Separation Of Confirmation Domains

Separarea obligatorie a domeniilor este:

1. Step 1 confirmation = layer ownership / layer roles confirmation;
2. finish setup confirmation = confirmarea payload-ului de finisaje din Review;
3. row confirmation = confirmarea randului sau alegerii de UI;
4. product composition confirmation = confirmarea compozitiei propuse la nivelul workspace-ului;
5. component truth confirmation = confirmarea explicita a instantei canonice `return_cant`.

Regula de ownership:

```text
no cross-promotion is allowed from 1-4 into 5 without explicit component confirmation plus canonical dependency completeness
```

## 11. Recommended Runtime Shape

Shape minim recomandat pentru instanta canonica:

```text
components.return_cant.instances.<instance_key> = {
  ...
  confirmation_state: "missing" | "draft" | "blocked" | "confirmed",
  confirmation_source?: "operator_component_confirmation" | "system_migration_verified" | "imported_verified_truth",
  blockers: string[]
}
```

Reguli:

1. `confirmation_source` este obligatoriu cand `confirmation_state = confirmed`;
2. `confirmation_source` lipseste sau este null in `missing`, `draft`, `blocked`;
3. daca `confirmation_source` este interzis, writer-ul viitor trebuie sa respinga starea `confirmed`.

## 12. Practical Rules For Future Writers

Viitorul writer runtime trebuie sa respecte:

1. nu scrie `confirmed` fara `confirmation_source` permis;
2. nu mapeaza Step 1 `confirmed` direct la component `confirmed`;
3. nu mapeaza `finish_setup.confirmed` direct la component `confirmed`;
4. nu mapeaza `row.confirmed` direct la component `confirmed`;
5. nu trateaza `product_composition_confirmed` ca substitut pentru component confirmation per instanta;
6. nu promoveaza `quote_geometry.letter_perimeter_m` la `geometry.confirmed_perimeter_m`;
7. nu confirma o instanta care exista doar in `components.returnCant` sau alt path legacy.

## 13. Recommended Next Slice

Slice-ul urmator recomandat este:

```text
RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1
```

Rationale:

1. semantica pentru `confirmation_state` este acum separata clar de semnalele curente de workflow;
2. cel mai mare blocker ramas pentru `confirmed` este sursa valida a lui `geometry.confirmed_perimeter_m`;
3. fara acel contract, orice writer runtime ar risca sa promoveze geometry evidence only la confirmed truth.

## 14. Recommended Next Prompt

```text
RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1
```
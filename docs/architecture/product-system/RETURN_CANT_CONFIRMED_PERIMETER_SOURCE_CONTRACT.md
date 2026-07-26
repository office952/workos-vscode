# Return Cant Confirmed Perimeter Source Contract

## 1. Purpose

Acest document defineste contractul canonic pentru sursa valida a campului:

```text
components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m
```

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = confirmed_perimeter_source_contract
root_template = TPL-VOLUMETRIC-LETTERS_v2
```

Acest document nu implementeaza:

- runtime writer;
- Product Truth writes;
- UI changes;
- Pricing changes;
- adapter changes;
- runtime DB changes;
- seed / migration execution;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_READY
```

Semnificatie exacta:

1. exista suficienta claritate pentru a separa perimeter evidence de perimeter truth confirmat;
2. sursele actuale din analyzer / quote geometry / UI pot fi clasificate fara ambiguitate critica ca evidence-only sau forbidden-as-confirmed;
3. sursele permise pentru `confirmed_perimeter_m` pot fi fixate docs-only, fara writer runtime;
4. implementarea writer-ului ramane totusi blocata de contractul incomplet pentru layer mapping si source ownership per instanta.

## 3. Why This Contract Is Ready

Auditul actual confirma urmatoarele:

1. `returnCantTruthFieldsReadonlyMapper.ts` trateaza `quote_geometry.letter_perimeter_m` ca `context_only`, blocat, si nu ca dependency confirmat;
2. `returnCantTruthFieldCaptureReadonlyAdapter.ts` emite warning de geometry context si blocker `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`;
3. `productTruthDraftBuilder.ts` si `productTruthTypes.ts` tin `returnMaterialPerimeterMl` si `geometry.confirmed` doar ca geometry / workflow draft fields, nu ca runtime `return_cant` confirmed truth;
4. `IntakeV6ReviewStep.tsx` si geometry display helpers calculeaza si afiseaza perimeter metrics pentru operator, dar nu scriu un field runtime canonic confirmat;
5. backend geometry services produc perimeter derivat din analyzer / path geometry, nu un `return_cant` confirmed perimeter owner-safe;
6. singurul dependency mai apropiat de confirmed geometry este `components.face.confirmed_perimeter`, dar acesta este un dependency separat, nu contractul final pentru `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m`.

Concluzie:

```text
current perimeter signals = evidence and dependency context
current perimeter signals != canonical confirmed return_cant perimeter truth
```

## 4. Canonical Geometry Shape

Shape-ul canonic final pentru geometry per instanta este:

```text
components.return_cant.instances.<instance_key>.geometry = {
  perimeter_source: "missing" | "evidence_only" | "operator_confirmed" | "imported_verified_truth" | "system_migration_verified",
  evidence_perimeter_m?: number,
  confirmed_perimeter_m?: number,
  confirmed_perimeter_source?: "operator_confirmed" | "imported_verified_truth" | "system_migration_verified",
  confirmed_perimeter_at?: string,
  confirmed_by?: string,
  blockers: string[]
}
```

Reguli structurale:

1. `perimeter_source` este obligatoriu;
2. `confirmed_perimeter_source` este obligatoriu cand `confirmed_perimeter_m` exista;
3. `confirmed_perimeter_at` si `confirmed_by` sunt obligatorii pentru sursele confirmate care promit provenance auditabila;
4. `blockers` exista mereu, chiar daca este array gol;
5. `evidence_perimeter_m` si `confirmed_perimeter_m` nu sunt sinonime si nu se dual-populeaza automat prin copiere.

## 5. Meaning Of Each Source State

### 5.1 `missing`

Nu exista inca nici evidence usable, nici perimeter confirmat owner-safe.

### 5.2 `evidence_only`

Exista perimeter derivat sau afisat din analyzer / quote geometry / UI diagnostics, dar nu exista actiune explicita de confirmare a perimeterului pentru instanta canonica.

### 5.3 `operator_confirmed`

`confirmed_perimeter_m` a fost confirmat explicit de operator pentru instanta canonica, cu provenance si audit.

### 5.4 `imported_verified_truth`

`confirmed_perimeter_m` vine dintr-o sursa externa importata, deja verificata, cu provenance owner-safe.

### 5.5 `system_migration_verified`

`confirmed_perimeter_m` a fost materializat printr-o migrare sau reconciliere controlata, cu audit si sursa verificabila.

## 6. Required Field Rules

Regulile canonice minime sunt:

1. `quote_geometry.letter_perimeter_m` poate popula numai `evidence_perimeter_m`;
2. cand sursa este `quote_geometry.letter_perimeter_m`, `perimeter_source` trebuie sa fie `evidence_only`;
3. `quote_geometry.letter_perimeter_m` nu poate popula `confirmed_perimeter_m`;
4. `quote_geometry.letter_perimeter_m` nu poate seta `confirmation_state = confirmed`;
5. raw analyzer perimeter si raw path geometry nu pot popula direct `confirmed_perimeter_m`;
6. UI display metrics, inclusiv valori de tip operator display perimeter, nu pot popula direct `confirmed_perimeter_m`;
7. `confirmed_perimeter_m` poate proveni numai din una dintre sursele permise pentru confirmed truth;
8. `confirmed_perimeter_m` nu poate fi copiat automat din `evidence_perimeter_m` fara actiune explicita de confirmare sau provenance verificata.

## 7. Accepted Sources For `confirmed_perimeter_m`

Sunt acceptate numai:

1. confirmare explicita de operator, scoped la instanta canonica;
2. imported verified truth, cu provenance si audit;
3. system migration verified, cu audit si provenance.

Campuri de provenance obligatorii pentru sursele confirmate:

1. `instance_key` stabil;
2. `confirmed_perimeter_source` valid;
3. `confirmed_perimeter_at` valid;
4. `confirmed_by` sau owner/system actor echivalent;
5. mapping valid catre `layer_group_ids` si/sau `source_ref`;
6. unitate in metri.

## 8. Forbidden Sources For `confirmed_perimeter_m`

Urmatoarele sunt explicit interzise ca sursa finala pentru perimeter confirmat:

1. raw analyzer output;
2. raw `quote_geometry.letter_perimeter_m`;
3. layer geometry evidence;
4. Step 1 confirmed;
5. layer role selected;
6. `finish_setup.confirmed`;
7. row confirmed;
8. pricing keys present;
9. product composition confirmed.

Regula compacta:

```text
workflow confirmation, row confirmation, selection presence, pricing presence, and analyzer geometry evidence are insufficient as confirmed perimeter truth
```

## 9. Validation Rules

`confirmed_perimeter_m` este valid doar daca toate sunt adevarate:

1. este numar finit;
2. este `> 0`;
3. unitatea este metri;
4. este legat de un `instance_key` stabil;
5. este legat de `layer_group_ids` si/sau `source_ref` valide;
6. `confirmed_perimeter_source` este permis;
7. nu a fost promovat prin copiere automata din evidence fara confirmare;
8. daca exista si `evidence_perimeter_m`, discrepanta peste toleranta permisa trebuie sa produca blocker;
9. provenance-ul actorului si timestamp-ului este prezent pentru sursele confirmate.

Regula pentru conflict:

```text
abs(evidence_perimeter_m - confirmed_perimeter_m) > configured_perimeter_tolerance_m => RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT
```

Acest document cere existenta blocker-ului de conflict, dar nu fixeaza numeric `configured_perimeter_tolerance_m`; acel prag trebuie aprobat in slice-ul de implementare / policy asociat writer-ului.

## 10. Canonical Blockers

Lista canonica minima este:

- `RETURN_CANT_CONFIRMED_PERIMETER_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_ONLY`
- `RETURN_CANT_PERIMETER_CONFIRMATION_MISSING`
- `RETURN_CANT_PERIMETER_SOURCE_INVALID`
- `RETURN_CANT_PERIMETER_UNIT_INVALID`
- `RETURN_CANT_PERIMETER_NON_POSITIVE`
- `RETURN_CANT_PERIMETER_INSTANCE_MISMATCH`
- `RETURN_CANT_PERIMETER_LAYER_MAPPING_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT`

Semantica minima:

1. `RETURN_CANT_CONFIRMED_PERIMETER_MISSING` apare cand starea cere perimeter confirmat, dar campul lipseste;
2. `RETURN_CANT_PERIMETER_EVIDENCE_ONLY` apare cand exista doar `evidence_perimeter_m`;
3. `RETURN_CANT_PERIMETER_CONFIRMATION_MISSING` apare cand exista un candidat numeric dar lipseste actiunea / provenance de confirmare;
4. `RETURN_CANT_PERIMETER_SOURCE_INVALID` apare cand sursa declarata nu este permisa pentru confirmed truth;
5. `RETURN_CANT_PERIMETER_UNIT_INVALID` apare cand unitatea nu este metri;
6. `RETURN_CANT_PERIMETER_NON_POSITIVE` apare cand valoarea este zero, negativa sau nefinita;
7. `RETURN_CANT_PERIMETER_INSTANCE_MISMATCH` apare cand perimeterul este atasat altei instante decat `instance_key` tinta;
8. `RETURN_CANT_PERIMETER_LAYER_MAPPING_MISSING` apare cand lipseste mapping-ul valid catre layers/source_ref;
9. `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT` apare cand evidence si confirmed truth diverge peste toleranta admisa.

## 11. Source Matrix

| source | current_field | can_populate_evidence_perimeter_m | can_populate_confirmed_perimeter_m | required_provenance | allowed_state | risk_if_promoted |
|---|---|---|---|---|---|---|
| `quote_geometry.letter_perimeter_m` | `quote_geometry.letter_perimeter_m` | yes | no | none beyond evidence trace | `evidence_only` | promoveaza geometry context la truth confirmat fara actiune owner-safe |
| analyzer perimeter | analyzer layer/path perimeter fields | yes | no | analyzer trace only | `evidence_only` | sugestia analyzer devine fals confirmed perimeter |
| layer geometry evidence | `path_geometry_summary`, layer perimeters, derived return perimeter | yes | no | layer/path evidence trace | `evidence_only` | confunda geometry derivata cu truth confirmat per componenta |
| manually confirmed operator perimeter | future operator-scoped canonical action | yes | yes | `instance_key`, actor, timestamp, valid layer mapping | `operator_confirmed` | daca guard-urile lipsesc, poate confirma instanta gresita sau mapping incomplet |
| imported verified truth | future import payload | yes | yes | import provenance, source id, actor/system trace, valid layer mapping | `imported_verified_truth` | import neverificat poate suprascrie truth-ul local |
| system migration verified | controlled migration/reconciliation payload | yes | yes | migration id, audit trail, source trace, valid layer mapping | `system_migration_verified` | migrare fara audit poate materializa un perimeter gresit ca adevar final |
| `finish_setup.confirmed` | `finish_setup.confirmed` | no | no | none | none | confirma workflow Review, nu perimeter truth |
| row confirmed | `letter_group_finishes[].confirmed`, `artwork_finishes[].confirmed` | no | no | none | none | confirma alegere UI, nu perimeter per instanta |
| Step 1 confirmed | `layer_role_setup.confirmation_status`, `layers[].confirmation_state` | no | no | none | none | confirma roluri/layers, nu perimeter truth |
| product composition confirmed | `product_composition_confirmed.confirmed` | no | no | none | none | promoveaza confirmarea compozitiei globale la confirmed perimeter fals |

## 12. Relationship With `confirmation_state`

Relatia canonica este:

1. `confirmation_state = confirmed` nu este permis daca `confirmed_perimeter_m` lipseste;
2. `perimeter_source = evidence_only` obliga blocker `RETURN_CANT_PERIMETER_EVIDENCE_ONLY`;
3. daca `confirmed_perimeter_m` exista dar lipseste component confirmation, instanta ramane `draft` sau `blocked`, nu `confirmed`;
4. daca exista component confirmation dar lipseste `confirmed_perimeter_m`, instanta ramane `blocked`;
5. perimeter confirmation si component confirmation sunt dependente, dar nu sunt acelasi lucru;
6. `confirmed_perimeter_m` valid este necesar, dar nu suficient, pentru `confirmation_state = confirmed`.

Regula compacta:

```text
no confirmed component truth without valid confirmed perimeter truth
```

## 13. Practical Writer Rules

Viitorul writer runtime trebuie sa respecte:

1. nu promoveaza `quote_geometry.letter_perimeter_m` la `confirmed_perimeter_m`;
2. nu trateaza `geometry.confirmed` din payload-ul generic ca dovada suficienta pentru `return_cant` confirmed perimeter;
3. nu mapeaza raw analyzer perimeter direct la confirmed perimeter;
4. nu trateaza `finish_setup.confirmed`, row confirmed sau Step 1 confirmed ca substitute pentru perimeter confirmation;
5. nu scrie `confirmed_perimeter_m` fara provenance si mapping valid;
6. nu permite `confirmation_state = confirmed` cand geometry este doar `evidence_only`.

## 14. Decision On Next Slice

Desi contractul de sursa pentru perimeter este `READY`, urmatorul slice recomandat nu este writer implementation plan, deoarece layer mapping / source ownership nu este suficient inchis.

Semnale care arata blockerul ramas:

1. mapper-ul readonly emite `SELECTED_LAYER_REFS_NOT_MAPPED_TO_RETURN_CANT`;
2. mapper-ul readonly emite `LAYER_CONFIRMATION_EXISTS_BUT_COMPONENT_MAPPING_MISSING`;
3. `layer_group_ids` si `source_ref` raman frecvent `context_only` sau missing, chiar cand exista quote geometry si Step 1 confirmation.

Decizia pentru next slice este:

```text
RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1
```

## 15. Recommended Next Prompt

```text
RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1
```
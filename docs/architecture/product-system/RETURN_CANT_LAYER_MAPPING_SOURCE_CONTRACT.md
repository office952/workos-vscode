# Return Cant Layer Mapping Source Contract

## 1. Purpose

Acest document defineste contractul canonic pentru sursa si mapping-ul instantelor runtime:

```text
components.return_cant.instances.<instance_key>
```

Focus-ul acestui slice este strict pe:

- `instance_key`
- `source_kind`
- `source_ref`
- `group_key`
- `layer_key`
- `layer_group_ids`

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = layer_mapping_source_contract
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
RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_READY
```

Semnificatie exacta:

1. exista deja surse stabile suficiente pentru `group_key` si `layer_key` in fluxul curent;
2. contractul poate fixa clar cum devin aceste surse `instance_key`, `source_kind`, `source_ref` si `layer_group_ids` canonice;
3. lipsa actuala este de contract si promotion rules, nu de inexistenta surselor brute;
4. dupa acest contract, urmatorul slice poate fi writer implementation plan, nu audit suplimentar de sursa.

## 3. Why This Contract Is Ready

Auditul confirma urmatoarele:

1. `deriveLetterGroupsFromAnalyzer()` construieste `group_key` din `entry.layerKey` pentru layere cu rol `face` si geometrie valida de litere;
2. `deriveArtworkFinishesFromAnalyzer()` construieste `layer_key` din `entry.layerKey` pentru layere artwork/logo recunoscute;
3. `finish_setup.letter_group_finishes[]` si `finish_setup.artwork_finishes[]` persista deja `group_key` si `layer_key` ca chei de rand;
4. `layer_role_setup.layers[]` persista `layer_key`, optional `layer_id`, `layer_name`, `auto_role`, `confirmed_role`, `confirmation_state`;
5. readonly adapterul foloseste deja `source_row_key = group_key | layer_key` si recunoaste explicit ca `layer_group_ids` sunt astazi doar row-id evidence in lipsa unui contract mai strict;
6. readonly mapperul foloseste `selectedLayerRefs` si layerele Step 1 doar ca `context_only`, nu ca mapping final;
7. testele existente arata aceeasi separare:
   - `pseudo:maria` / `pseudo:ana` / `logo-dreapta` sunt deja chei stabile de lucru;
   - labels ca `Vector Litere` si `Vector Logo` sunt roluri semantice, nu chei finale.

Concluzie:

```text
stable row keys exist now
stable runtime mapping rules do not exist yet
```

## 4. Current Source Audit

### 4.1 `group_key`

Surse actuale observate:

1. `finish_setup.letter_group_finishes[].group_key`
2. `deriveLetterGroupsFromAnalyzer()` -> `group_key: entry.layerKey`
3. backend/frontend tests pentru letter groups folosesc aceeasi cheie ca identity de rand

Semantica actuala:

- identifica randul de finish pentru un grup de litere;
- este deja suficient de stabil pentru a deveni baza lui `instance_key` la `source_kind = letter_group`;
- nu trebuie inlocuit cu label UI sau index numeric.

### 4.2 `layer_key`

Surse actuale observate:

1. `finish_setup.artwork_finishes[].layer_key`
2. `layer_role_setup.layers[].layer_key`
3. `deriveArtworkFinishesFromAnalyzer()` -> `layer_key: entry.layerKey`
4. backend/frontend tests pentru artwork/logo folosesc aceeasi cheie ca identity de rand

Semantica actuala:

- identifica randul artwork/logo si layerul sursa;
- este deja suficient de stabil pentru a deveni baza lui `instance_key` la `source_kind = artwork_layer`;
- nu trebuie inlocuit cu display name, position hint sau label UI.

### 4.3 `layer_group_ids`

Surse actuale observate:

1. `layer_role_setup.layers[].layer_key` si optional `layer_id`
2. `selectedLayerRefs` din readonly mapper
3. `letterGroupIdsBySourceKey` / `artworkLayerIdsBySourceKey` din readonly adapter input
4. `path_geometry_summary` / analyzer layer ids ca evidence pentru layere reale

Semantica actuala:

- astazi este frecvent doar evidence sau mapping partial;
- nu este inca promovat canonic dintr-o regula owner-safe unitara;
- lipsa sau ambiguitatea lui trebuie sa blocheze `confirmed`.

### 4.4 Layer roles si labels

Surse actuale observate:

1. `confirmed_role` / `auto_role` in `layer_role_setup.layers[]`
2. owner labels `Vector Litere` si `Vector Logo`
3. artwork heuristics si analyzer role suggestions

Semantica actuala:

- pot defini `source_kind` cand sunt confirmate si coerente;
- nu pot defini singure `instance_key`;
- sunt semantic role labels, nu identity keys.

## 5. Canonical Mapping Contract

Fiecare instanta `return_cant` trebuie sa aiba:

```text
instance_key
source_kind
source_ref
layer_group_ids
```

Relatia canonica este:

1. `source_kind` spune ce tip de sursa owner-semantica avem;
2. `source_ref` pastreaza cheia stabila de origine;
3. `instance_key` este derivat deterministic din `source_kind` + cheia stabila de origine;
4. `layer_group_ids` leaga instanta canonica de layerele reale care o sustin;
5. labels si roluri UI pot exista ca evidence/context, dar nu inlocuiesc cheia de origine.

## 6. Final `source_kind` Contract

Valorile finale permise sunt:

- `letter_group`
- `artwork_layer`

Reguli:

1. `letter_group` este permis doar cand sursa canonica are `group_key` valid;
2. `artwork_layer` este permis doar cand sursa canonica are `layer_key` valid;
3. `Vector Litere` si `Vector Logo` sunt labels de rol pentru UI / evidence, nu valori finale de `source_kind`;
4. `source_kind` nu se deduce din index, label vizual sau ordine in array.

## 7. Final `instance_key` Contract

Regulile canonice finale sunt:

### 7.1 Pentru Vector Litere

```text
source_kind = letter_group
instance_key = letter_group:<group_key>
source_ref.group_key = <group_key>
```

### 7.2 Pentru Vector Logo

```text
source_kind = artwork_layer
instance_key = artwork_layer:<layer_key>
source_ref.layer_key = <layer_key>
```

### 7.3 Interdictii explicite

Sunt interzise ca baza pentru `instance_key`:

1. index numeric instabil;
2. label UI;
3. `layer_name` sau display name fara cheie stabila;
4. fallback inventat cand lipseste `group_key` sau `layer_key`;
5. concatenari din culoare, finish sau pozitie de rand.

Regula compacta:

```text
missing stable key => no canonical instance_key
```

## 8. Final `source_ref` Contract

Shape-ul canonic final este:

```text
source_ref: {
  group_key?: string;
  layer_key?: string;
  source_label?: string;
  source_role?: "Vector Litere" | "Vector Logo";
}
```

Decizii canonice:

1. `group_key` este obligatoriu pentru `source_kind = letter_group`;
2. `layer_key` este obligatoriu pentru `source_kind = artwork_layer`;
3. `source_label` este display/evidence only;
4. `source_role` este semantic role / UI role only;
5. cheia finala ramane `group_key` sau `layer_key`;
6. `layer_group_ids` nu se muta in `source_ref`.

Rationale pentru excluderea `layer_group_ids` din `source_ref`:

1. contractul containerului a fixat deja `layer_group_ids` la nivel de instanta;
2. `layer_group_ids` este o legatura operationala a mapping-ului final, nu doar metadată de origine;
3. dublarea lui in `source_ref` ar crea doua locuri canonice pentru acelasi mapping.

## 9. Final `layer_group_ids` Contract

`layer_group_ids` este lista canonica a layer ids-urilor reale care sustin instanta.

Reguli:

1. pentru `letter_group`, `layer_group_ids` trebuie sa contina layer id-ul sau layer keys-urile reale asociate grupului de litere;
2. pentru `artwork_layer`, `layer_group_ids` trebuie sa contina layerul artwork/logo asociat sau gruparea reala de layere corespunzatoare;
3. poate fi derivat din analyzer / `layer_role_setup` / payload mapping controlat, dar nu din label UI;
4. daca mapping-ul actual este doar `source_row_key -> [source_row_key]`, acesta ramane evidence-only pana la confirmarea sursei reale;
5. `layer_group_ids` este obligatoriu pentru `confirmed`;
6. lipsa sau ambiguitatea lui trebuie sa blocheze component confirmation;
7. `layer_group_ids` poate avea un singur element sau mai multe, dar fiecare element trebuie sa fie layer identity real, nu descriere text.

Regula de siguranta:

```text
row id echo alone != confirmed layer mapping truth
```

## 10. Canonical Blockers

Lista canonica minima este:

- `RETURN_CANT_INSTANCE_KEY_MISSING`
- `RETURN_CANT_SOURCE_KIND_MISSING`
- `RETURN_CANT_SOURCE_REF_MISSING`
- `RETURN_CANT_GROUP_KEY_MISSING`
- `RETURN_CANT_LAYER_KEY_MISSING`
- `RETURN_CANT_LAYER_GROUP_IDS_MISSING`
- `RETURN_CANT_LAYER_MAPPING_AMBIGUOUS`
- `RETURN_CANT_LAYER_ROLE_UNSUPPORTED`
- `RETURN_CANT_LAYER_MAPPING_LEGACY_ONLY`

Semantica minima:

1. `RETURN_CANT_INSTANCE_KEY_MISSING` apare cand nu exista `group_key` sau `layer_key` suficient pentru cheia finala;
2. `RETURN_CANT_SOURCE_KIND_MISSING` apare cand rolul sau sursa nu permite clasificarea canonica;
3. `RETURN_CANT_SOURCE_REF_MISSING` apare cand lipseste obiectul minim de provenienta;
4. `RETURN_CANT_GROUP_KEY_MISSING` apare pentru `letter_group` fara `group_key` valid;
5. `RETURN_CANT_LAYER_KEY_MISSING` apare pentru `artwork_layer` fara `layer_key` valid;
6. `RETURN_CANT_LAYER_GROUP_IDS_MISSING` apare cand nu exista mapping operational catre layere reale;
7. `RETURN_CANT_LAYER_MAPPING_AMBIGUOUS` apare cand mai multe surse se bat pentru aceeasi instanta fara regula stabila de alegere;
8. `RETURN_CANT_LAYER_ROLE_UNSUPPORTED` apare cand rolul confirmat nu este compatibil cu `letter_group` sau `artwork_layer`;
9. `RETURN_CANT_LAYER_MAPPING_LEGACY_ONLY` apare cand singura informatie disponibila traieste doar in `components.returnCant`, labels sau mapping-uri transitional-only.

## 11. Source Matrix

| source | current_field | can_define_source_kind | can_define_instance_key | can_define_layer_group_ids | required_for_confirmed | risk_if_used_directly |
|---|---|---|---|---|---|---|
| Vector Litere | owner role label / `confirmed_role = face` | yes | no | no | no | label-ul semantic poate fi confundat cu identity finală |
| Vector Logo | owner role label / `confirmed_role = printed_artwork` | yes | no | no | no | label-ul semantic poate fi confundat cu identity finală |
| `group_key` | `finish_setup.letter_group_finishes[].group_key` | yes with role context | yes for `letter_group` | indirectly, not alone | yes | poate rămâne doar row identity dacă nu este legat de layer ids reale |
| `layer_key` | `finish_setup.artwork_finishes[].layer_key`, `layer_role_setup.layers[].layer_key` | yes with role context | yes for `artwork_layer` | indirectly, often yes | yes | poate fi folosit greșit ca display key fără mapping operațional complet |
| layer role label | `auto_role` / `confirmed_role` / owner labels | yes | no | no | no | rolul nu înlocuiește cheia stabilă |
| source label | `layer_name`, `display_name`, `source_layer_name`, `original_detected_label` | no | no | no | no | label-urile se pot schimba și nu sunt owner-safe ca identity |
| artwork layer id | `layer_id` / analyzer layer id for artwork | yes with role context | sometimes, if same as stable `layer_key` | yes | yes | poate deveni ambiguu dacă `layer_id` și `layer_key` diverg fără regulă explicită |
| letter group id | analyzer face layer key / grouped face layer ids | yes with role context | sometimes, if tied to `group_key` | yes | yes | fără mapping explicit poate genera dubluri sau coliziuni între grup și layer |
| finish setup row | `letter_group_finishes[]` / `artwork_finishes[]` | partially | partially | no, not by itself | no | row-ul este payload de workflow, nu mapping final complet |
| analyzer layer ids | `layer_role_setup.layers[].layer_key`, `layer_id`, `path_geometry_summary` | yes with confirmed role | indirectly | yes | yes | analyzerul oferă evidence, nu confirmare automată de component truth |
| Product Truth draft legacy `components.returnCant` | draft fields `depthMm`, `finishType`, `colorCode` | no | no | no | no | legacy draft nu conține mapping canonic per instanță |
| canonical `components.return_cant` | future runtime container | yes | yes | yes | yes | nu este sursă brută curentă; devine target după bridge |

## 12. Relationship With `confirmation_state`

Relatia canonica este:

1. daca `instance_key` lipseste, instanta este `missing` sau `blocked`;
2. daca `source_kind` lipseste, instanta este `blocked`;
3. daca `source_ref` lipseste, instanta este `blocked`;
4. daca `layer_group_ids` lipsesc, instanta nu poate fi `confirmed`;
5. daca mapping-ul este ambiguu, instanta este `blocked`;
6. doar mapping stabil + component confirmation + confirmed perimeter poate permite `confirmed`.

Regula compacta:

```text
stable mapping is necessary but not sufficient for confirmed component truth
```

## 13. Practical Writer Rules

Viitorul writer runtime trebuie sa respecte:

1. nu inventeaza `instance_key` cand lipseste `group_key` sau `layer_key`;
2. nu foloseste `Vector Litere` / `Vector Logo` ca identitate finala;
3. nu foloseste `layer_name`, `display_name` sau `source_label` ca identity canonica;
4. nu foloseste indexul randului ca fallback de cheie;
5. nu trateaza `selectedLayerRefs` sau `confirmedLayerKeys` ca mapping final fara regula de promotion explicita;
6. nu trateaza ecoul `source_row_key -> [source_row_key]` ca mapping final confirmat fara source verification;
7. nu promoveaza date legacy-only la `confirmed` fara mapping canonic explicit.

## 14. Decision On Next Slice

Acest contract este suficient de clar pentru a permite planul de implementare al runtime bridge-ului.

Decizia pentru next slice este:

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1
```

Rationale:

1. sursele brute pentru `group_key` si `layer_key` exista deja in frontend/backend payloads si teste;
2. contractul de promotion la `instance_key` si `source_ref` este acum explicit;
3. `layer_group_ids` este definit ca dependency obligatorie pentru `confirmed`, cu blockere clare pentru lipsa sau ambiguitate;
4. blockerul ramas este de implementare controlata, nu de lipsa a sursei fundamentale.

## 15. Recommended Next Prompt

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1
```
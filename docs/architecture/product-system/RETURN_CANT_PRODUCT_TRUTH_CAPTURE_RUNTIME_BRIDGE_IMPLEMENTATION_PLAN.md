# Return Cant Product Truth Capture Runtime Bridge Implementation Plan

## 1. Purpose

Acest document fixeaza planul de implementare pentru viitorul bridge care va captura Product Truth runtime canonic pentru componenta `return_cant` din datele persistate ale workspace-ului Intake V6.

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = runtime_bridge_implementation_plan
root_template = TPL-VOLUMETRIC-LETTERS_v2
```

Acest document nu implementeaza:

- runtime bridge;
- Product Truth writes;
- UI changes;
- Pricing changes;
- runtime DB changes;
- seeds / migration execution;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_READY
```

Semnificatie exacta:

1. exista un punct de integrare backend suficient de clar pentru writer-ul runtime;
2. sursele de input necesare pentru bridge exista deja in payload-ul Intake V6;
3. regulile de output, blocare si compatibilitate pot fi fixate fara implementare;
4. bridge-ul poate fi implementat incremental, cu teste locale si fara extindere de scope in alte sisteme.

## 3. Why This Plan Is Ready Now

Auditul actual confirma urmatoarele:

1. `backend/services/intake_v6_workspace_service.py` controleaza persistenta pentru `finish_setup`, `layer_role_setup`, `svg_analysis_json` si `quote_geometry`;
2. `save_finish_setup_for_intake_v6_workspace()` este primul loc in care toate input-urile necesare pentru `return_cant` exista simultan intr-o forma normalizata owner-safe;
3. `upload_svg_to_intake_v6_workspace()`, `save_analysis_bundle_for_intake_v6_workspace()` si `save_layer_roles_for_intake_v6_workspace()` pot invalida sau rescrie premisele mapping-ului, deci trebuie sa participe la cleanup sau rerun controlat;
4. schema `IntakeV4WorkspacePayload` nu declara inca un camp runtime Product Truth, iar `_parse_payload()` foloseste validare Pydantic, deci bridge-ul nu poate fi introdus robust fara extinderea explicita a payload-ului;
5. nu exista in cod un writer runtime canonic pentru `components.return_cant`, doar layere readonly si shape-uri legacy.

Concluzie:

```text
primary write hook is known
input surfaces are known
schema preservation gap is known
```

## 4. Exact Future Integration Point

### 4.1 Primary write hook

Punctul principal de integrare trebuie sa fie in:

```text
backend/services/intake_v6_workspace_service.py
save_finish_setup_for_intake_v6_workspace()
```

Hook-ul exact recomandat este:

1. dupa `normalize_intake_v6_finish_setup(request)`;
2. dupa ce `payload_raw["finish_setup"]` a fost actualizat cu forma normalizata;
3. dupa refresh-ul local pentru `product_composition_recommendation` si eventualele warnings de dossier;
4. inainte de `_parse_payload(payload_raw)` si inainte de `_persist_payload(...)`.

Forma intentionata a wiring-ului:

```text
payload_raw["finish_setup"] = normalized...
apply_product_composition_recommendation(payload_raw)
apply_v6_pricing_preview_derived_state(payload_raw)
apply_return_cant_runtime_product_truth_bridge(payload_raw)
payload = _parse_payload(payload_raw)
return await _persist_payload(...)
```

Rationale:

1. bridge-ul trebuie sa consume forma finala normalizata a `finish_setup`, nu input UI brut;
2. bridge-ul trebuie sa ruleze in backend, nu in builder-ul readonly din frontend;
3. hook-ul trebuie sa fie suficient de aproape de persistenta incat sa rescrie slice-ul runtime dintr-o singura sursa de adevar.

### 4.2 Required invalidation hooks

Mutatorii urmatori trebuie sa faca cleanup sau rerun controlat al aceluiasi bridge:

1. `upload_svg_to_intake_v6_workspace()`
2. `save_analysis_bundle_for_intake_v6_workspace()`
3. `save_layer_roles_for_intake_v6_workspace()`

Regula exacta:

1. daca `finish_setup` este sters sau devine implicit invalid dupa inlocuirea SVG-ului, se sterge si slice-ul runtime `return_cant` din payload;
2. daca `layer_role_setup` se schimba iar `finish_setup` inca exista, bridge-ul trebuie rerulat pe noile date persistate;
3. cleanup-ul trebuie sa fie component-scoped si sa nu atinga alte componente Product Truth din viitor.

## 5. Payload Preservation Requirement

Inainte de implementarea bridge-ului, payload-ul workspace trebuie extins cu un camp explicit pentru runtime Product Truth.

Cerinta minima:

1. `IntakeV4WorkspacePayload` / `IntakeV6WorkspacePayload` trebuie sa declare un camp dedicat pentru containerul runtime Product Truth;
2. `_parse_payload()` nu trebuie sa piarda output-ul bridge-ului la urmatorul save;
3. writer-ul bridge-ului nu are voie sa se bazeze pe chei arbitrare nedeclarate in payload.

Regula de ordine:

```text
schema preservation first
runtime bridge second
```

## 6. Exact Bridge Inputs

Bridge-ul trebuie sa consume exclusiv date persistate sau normalizate backend-side, nu state frontend ephemeral.

### 6.1 Required inputs

1. `payload_raw["finish_setup"]`
2. `payload_raw["layer_role_setup"]`
3. `payload_raw["quote_geometry"]`
4. `payload_raw["product_composition_confirmed"]` ca gate contextual, nu ca sursa finala de component confirmation
5. `record.template_code` / `payload.product_binding.template_code`

### 6.2 Exact fields consumed

Din `finish_setup`:

1. `letter_group_finishes[]`
2. `artwork_finishes[]`
3. `return_finish_type`
4. `return_depth_mm`
5. `return_oracal_code`
6. `return_oracal_name`
7. `confirmed`
8. per-row `group_key`, `layer_key`, `return_finish_type`, `return_depth_mm`, `return_oracal_code`, `return_oracal_name`, `confirmed`

Din `layer_role_setup`:

1. `layers[].layer_key`
2. `layers[].layer_id`
3. `layers[].layer_name`
4. `layers[].auto_role`
5. `layers[].confirmed_role`
6. `layers[].confirmation_state`

Din `quote_geometry`:

1. `letter_perimeter_m`
2. `geometry_source`
3. `confirmed`

### 6.3 Allowed derived inputs

Bridge-ul poate deriva deterministic:

1. `source_kind` din tipul randului si rolurile confirmate;
2. `instance_key` din `group_key` sau `layer_key`;
3. `material_profile.width_mm` din depth-ul confirmat sau explicit selectat;
4. `pricing_keys.*` din maparile fixe deja contractate pentru `return_cant`;
5. `geometry.evidence_perimeter_m` din `quote_geometry.letter_perimeter_m`.

Bridge-ul nu are voie sa derive automat:

1. `confirmation_state = confirmed`;
2. `geometry.confirmed_perimeter_m` din evidence geometry;
3. `layer_group_ids` canonice din simplu row-id echo;
4. preturi sau costuri comerciale.

## 7. Exact Bridge Outputs

Bridge-ul trebuie sa scrie exclusiv containerul runtime canonic pentru componenta `return_cant` in noua sectiune runtime Product Truth a payload-ului workspace.

Output-ul exact, relativ la runtime Product Truth root, este:

```text
components.return_cant = {
  version: "v1",
  instances: {
    <instance_key>: {
      instance_key,
      source_kind,
      source_ref,
      layer_group_ids?,
      material_profile,
      finish_variant,
      pricing_keys,
      geometry,
      confirmation_state,
      blockers
    }
  }
}
```

Writer-ul trebuie sa scrie:

1. shape complet pentru fiecare instanta canonica materializabila;
2. array explicit de `blockers` per instanta;
3. `pricing_keys` doar ca referinte de pricing, nu valori;
4. `geometry.evidence_perimeter_m` cand exista doar evidence;
5. `geometry.confirmed_perimeter_m` numai din surse permise de contract.

Writer-ul nu trebuie sa scrie:

1. `components.returnCant` ca tinta finala;
2. `components.return` ca tinta finala;
3. preturi sau costuri runtime;
4. artificii de tip dual final write.

## 8. State Rules

### 8.1 Instance creation rules

1. `letter_group_finishes[]` produce candidati `source_kind = letter_group`;
2. `artwork_finishes[]` produce candidati `source_kind = artwork_layer`;
3. `instance_key = letter_group:<group_key>` pentru letter groups;
4. `instance_key = artwork_layer:<layer_key>` pentru artwork rows;
5. daca lipseste cheia stabila, bridge-ul nu inventeaza o instanta canonica.

### 8.2 Mapping rules

1. `group_key` si `layer_key` raman sursa de identitate;
2. `layer_group_ids` se scrie numai cand mapping-ul real catre layere este determinabil univoc din datele persistate;
3. echo-ul simplu `[group_key]` sau `[layer_key]` nu trebuie promovat ca mapping confirmat final;
4. mapping ambiguu sau absent produce blocker.

### 8.3 Geometry rules

1. `quote_geometry.letter_perimeter_m` poate popula numai `geometry.evidence_perimeter_m`;
2. in lipsa unei surse confirmate, `geometry.perimeter_source = evidence_only` sau `missing`;
3. bridge-ul initial trebuie sa accepte ca multe instante vor ramane blocate pe perimeter.

### 8.4 Confirmation rules

1. `finish_setup.confirmed`, `row.confirmed`, Step 1 confirmed si `product_composition_confirmed.confirmed` nu pot seta singure `confirmation_state = confirmed`;
2. bridge-ul initial poate produce `draft` sau `blocked` in mod legitim;
3. `confirmed` este interzis pana cand exista sursa valida de component confirmation si perimeter confirmat.

## 9. Legacy Compatibility Rules

1. bridge-ul poate citi `components.returnCant` si `components.return` numai ca evidence sau parity context, nu ca target final;
2. builder-ul frontend `productTruthDraftBuilder.ts` ramane legacy/preview si nu devine writer runtime;
3. readonly mapperul si readonly adapterul raman consumatori de evidence si audit, nu writers;
4. daca exista forme legacy in payload sau in consumatori downstream, bridge-ul nu trebuie sa le rescrie ca final output;
5. orice rescriere a slice-ului runtime trebuie sa fie full replace pentru `components.return_cant`, nu patch incremental din state legacy partial.

Regula compacta:

```text
legacy read allowed
legacy final write forbidden
frontend draft writer forbidden
```

## 10. Suggested Helper Shape

Implementarea trebuie sa introduca un helper pur backend-side, de exemplu:

```text
services/intake_v6_return_cant_runtime_product_truth_bridge.py
```

Interfata minima recomandata:

```text
build_return_cant_runtime_product_truth(payload_raw, template_code) -> dict
apply_return_cant_runtime_product_truth_bridge(payload_raw, template_code) -> None
clear_return_cant_runtime_product_truth(payload_raw) -> None
```

Separarea este necesara pentru:

1. teste unitare pure pe derivare;
2. wiring minim in workspace service;
3. cleanup controlat pe mutatori de invalidare.

## 11. Test Matrix

### 11.1 Pure helper unit tests

1. letter group row cu `group_key` valid produce `instance_key = letter_group:<group_key>`;
2. artwork row cu `layer_key` valid produce `instance_key = artwork_layer:<layer_key>`;
3. `white_aluminum`, `oracal`, `ral_paint` se normalizeaza la `finish_variant` si `pricing_keys` corecte;
4. `quote_geometry.letter_perimeter_m` intra doar in `evidence_perimeter_m`;
5. lipsa `layer_group_ids` reale produce blockers, nu mapping fals confirmat;
6. lipsa component confirmation mentine starea `draft` sau `blocked`;
7. lipsa cheii stabile nu produce instanta sintetica.

### 11.2 Backend service tests

1. `save_finish_setup_for_intake_v6_workspace()` persista noul slice runtime dupa save valid;
2. `_parse_payload()` pastreaza noul camp runtime Product Truth dupa extinderea de schema;
3. `save_layer_roles_for_intake_v6_workspace()` reruleaza bridge-ul cand `finish_setup` exista;
4. `upload_svg_to_intake_v6_workspace()` curata slice-ul runtime cand `finish_setup` este invalidat;
5. `save_analysis_bundle_for_intake_v6_workspace()` curata sau reruleaza corect, in functie de calea de update.

### 11.3 Readonly and consumer recheck

1. mapperul readonly poate primi in viitor canonical runtime real fara a schimba semantica blockerelor;
2. orice frontend recheck ramane read-only si limitat la awareness / mapper fixtures;
3. nu se introduc modificari UI in acest slice de implementare.

### 11.4 Runtime smoke

1. save workspace cu `finish_setup` valid;
2. citire API workspace si confirmare prezenta `components.return_cant` in sectiunea runtime Product Truth;
3. verificare read-only ca instantele apar `blocked` sau `draft` unde lipsesc confirmation/perimeter contracts;
4. nicio schimbare in pricing runtime sau quote/order flows.

## 12. Implementation Sequence

### A. Pure derivation helper

1. adauga campul de payload runtime Product Truth;
2. adauga helper pur pentru build/clear `return_cant` runtime container;
3. encodeaza doar regulile deja contractate.

### B. Unit tests

1. adauga fixture-uri focused pentru letter groups, artwork rows, logo-only si geometry evidence;
2. blindeaza regulile de blocker si interdictiile de auto-confirm.

### C. Wire helper into workspace save path

1. apeleaza helperul in `save_finish_setup_for_intake_v6_workspace()`;
2. foloseste full replace pentru slice-ul `components.return_cant`;
3. mentine scope-ul limitat la `TPL-VOLUMETRIC-LETTERS_v2`.

### D. Backend service tests

1. confirma persistenta noului slice;
2. confirma cleanup-ul pe invalidare;
3. confirma ca alte mutatii nu corup payload-ul.

### E. Frontend awareness / mapper recheck only if needed

1. revalideaza fixture-urile readonly doar daca apar contract changes de path;
2. fara UI edits.

### F. Runtime smoke via API/UI read-only

1. save real workspace data;
2. verifica payload/API;
3. eventual citire read-only din Review awareness fara modificari UI.

## 13. Risks And Guardrails

Riscuri principale:

1. introducerea unui camp nedeclarat in payload care este pierdut de `_parse_payload()`;
2. confuzia dintre geometry evidence si confirmed perimeter;
3. promovarea row confirmation la component confirmation;
4. dual write accidental in path-uri legacy;
5. rerun incomplet dupa schimbarea layerelelor sau a SVG-ului.

Guardrails obligatorii:

1. helper pur cu teste unitare inainte de wiring;
2. cleanup explicit pe mutatori de invalidare;
3. `confirmed` interzis fara toate preconditiile canonice;
4. no pricing values in Product Truth;
5. no UI-driven runtime writes.

## 14. Exit Criteria For The Future Implementation Slice

Implementarea viitoare poate fi declarata completa doar daca:

1. save-ul de `finish_setup` persista containerul runtime `return_cant` in payload;
2. `_parse_payload()` pastreaza acel container pe toate mutatiile relevante;
3. invalidarea pe SVG/layer changes este acoperita;
4. testele pure si service-level pentru bridge sunt verzi;
5. runtime smoke confirma prezenta noului slice fara regressii de pricing sau UI.
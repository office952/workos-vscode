# Return Cant Product Truth Bridge Blocker Alignment Plan

## 1. Purpose

Acest document fixeaza planul de aliniere pentru blockerele care trebuie rezolvate inainte de orice implementare runtime write pentru Product Truth `return_cant`.

Boundary fix pentru acest slice:

```text
component_scope = return_cant
mode = bridge_blocker_alignment_plan
root_template = TPL-VOLUMETRIC-LETTERS_v2
```

Acest document nu implementeaza:

- runtime bridge;
- Product Truth writes;
- UI changes;
- Pricing changes;
- adapter changes;
- endpoint public nou;
- DB migration / seed;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_BRIDGE_BLOCKERS_ALIGNMENT_READY
```

Semnificatie exacta:

1. blockerele sunt suficient de bine localizate si separate pe owner layers;
2. ordinea obligatorie a slice-urilor urmatoare poate fi stabilita fara ambiguitate critica;
3. implementarea runtime bridge ramane interzisa acum, dar nu mai lipseste claritatea de plan;
4. primul slice recomandat poate fi lansat imediat ca docs/contract slice independent.

## 3. Current State Summary

Auditul confirma urmatoarele:

1. persistarea canonica a workspace-ului V6 trece prin `finish_setup` in backend, nu printr-un container Product Truth runtime separat;
2. `save_finish_setup_for_intake_v6_workspace(...)` este punctul corect pentru viitoare derivari additive pe payload;
3. infrastructura `return_cant` Product Truth existenta este numai readonly / draft / awareness;
4. builder-ul si contractele actuale inca expun forme legacy (`components.returnCant`, `components.return.*`);
5. adapterul readonly inca referentiaza pricing targete legacy pentru 3 sloturi critice;
6. `quote_geometry.letter_perimeter_m` exista doar ca evidence/context si nu poate fi promovat direct.

## 4. Existing Infrastructure By Layer

### 4.1 Frontend save/runtime layer

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` construieste `finish_setup` si salveaza prin `saveCurrentFinish(...)`.
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts` persista `finish_setup` si hidrateaza workspace-ul inapoi prin `FINISH_SETUP_PERSIST_SUCCESS`.

### 4.2 Backend persistence layer

- `backend/services/intake_v6_workspace_service.py` scrie `payload_raw["finish_setup"]` si ruleaza derivari additive existente.
- pattern-ul corect pentru viitorul bridge este derivare persist-time in acelasi serviciu, nu endpoint separat.

### 4.3 Product Truth readonly/draft layer

- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` construieste `ProductTruthDraft` doar in memorie.
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts` defineste campuri canonice asteptate si blockerele lor.
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts` defineste target paths per-instance si pricing refs readonly.

### 4.4 Backbone / contract layer

- `backend/services/form_system_contract_backbone_service.py` foloseste inca `components.return.material` si `components.return.depth_mm`.
- asta confirma ca bridge-ul nu trebuie implementat inainte de un slice explicit de contract alignment.

## 5. Blocker Alignment Map

| blocker | current_state | final_required_state | owner_layer | safe_next_slice | implementation_allowed_now | risk_if_ignored |
|---|---|---|---|---|---|---|
| canonical container pentru `components.return_cant.instances.<instance_key>` | nu exista container runtime persistat; exista doar target paths readonly | contract canonic documentat pentru container, instance key, obiecte child si status fields | Product Truth contract + backend payload contract | `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1` | no | bridge-ul ar scrie intr-o forma instabila sau ar dubla state legacy |
| source canonic pentru `components.face.confirmed_perimeter` | mapperul readonly stie dependența, dar runtime real nu o emite | o sursa explicita, confirmabila, owner-safe pentru `components.face.confirmed_perimeter` | geometry / Product Truth source contract | `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1` | no | s-ar promova ilegal `quote_geometry.letter_perimeter_m` la truth confirmat |
| explicit `return_cant.confirmation_state` | lipseste complet; exista doar `finish_setup.confirmed`, row `confirmed`, Step 1 confirmation | semantica explicita pentru `pending | blocked | confirmed` la nivel component/instance | Product Truth confirmation contract | `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1` | no | bridge-ul ar confunda confirmation de UI/row/layer cu Product Truth final |
| migration/compatibility de la `components.returnCant` la `components.return_cant` | builderul si testele folosesc `components.returnCant` | contract de compatibilitate documentat: legacy read path acceptat temporar, target final numai `components.return_cant` | Product Truth types + draft compatibility contract | `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1` | no | viitorul cod ar introduce doua adevaruri concurente si testele ar ancora forma gresita |
| contract backbone paths de la `components.return` la `components.return_cant` | backbone-ul are `components.return.material` si `components.return.depth_mm` | backbone-ul trebuie sa emita doar targete finale `components.return_cant...` sau missing-target placeholders explicite | form/backbone contract layer | `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1` | no | UI awareness si downstream contracte ar ramane pe path-uri moarte |
| adapter pricing target legacy -> pricing target final | adapterul readonly inca referentiaza `return_cant_vinyl_application_labor`, `ral_paint_material_<width>mm`, `ral_paint_application_labor` | readonly adapter si testele lui trebuie sa refere codurile finale verificate | readonly adapter / pricing-reference contract | `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1` | yes, dar numai ca slice separat readonly | bridge-ul ar scrie pricing refs gresite sau ar pastra aliasuri tranzitorii |
| `layer_group_ids` canonical mapping | exista doar context din `selected_layer_refs[]`, `layer_role_setup` si row keys | regula documentata pentru maparea `group_key`/`layer_key` la `instance_key` si `layer_group_ids` | Product Truth contract + layer mapping rules | `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1` | no | instanta `return_cant` nu poate fi legata determinist de sursa SVG/operator |
| `finish_setup.confirmed` vs component confirmation | mapperul readonly il marcheaza explicit non-canonical | separare contractuala: `finish_setup.confirmed` = form persistence state, nu component truth state | Product Truth confirmation contract | `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1` | no | implementarea ar activa prematur quote-safe truth |
| Step 1 confirmation vs component truth confirmation | Step 1 da doar layer ownership/selection evidence | separare contractuala explicita intre layer ownership confirmation si component truth confirmation | Product Truth confirmation contract | `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1` | no | operatorii si codul ar trata gresit Pasul 1 ca GO pentru return_cant truth |

## 6. Ordered Next Slices

Ordinea corecta si obligatorie este:

### A. `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`

Scope:

1. defineste containerul final `components.return_cant.instances.<instance_key>`;
2. defineste forma minima a fiecarui instance object;
3. defineste politica de compatibilitate cu legacy `components.returnCant`;
4. defineste mapping-ul pentru `layer_group_ids` si `instance_key`;
5. nu scrie runtime si nu modifica UI.

De ce este primul:

1. toate celelalte slice-uri trebuie sa stie tinta finala;
2. fara container canonic, nici confirmation contract, nici perimeter source, nici bridge write nu au path final stabil;
3. backbone-ul si builder-ul legacy nu pot fi aliniate corect fara aceasta tinta.

### B. `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`

Scope:

1. aliniaza readonly adapterul la pricing keys finale verificate:
   - `RETURN_CANT_VINYL_APPLICATION_LABOR`
   - `MAT-VOPSEA-RAL-CANT-30MM`
   - `MAT-VOPSEA-RAL-CANT-60MM`
   - `MAT-VOPSEA-RAL-CANT-80MM`
   - `MAT-VOPSEA-RAL-CANT-100MM`
   - `RETURN_CANT_RAL_PAINT_LABOR`
2. actualizeaza testele focusate readonly adapter;
3. nu scrie Product Truth.

De ce este al doilea:

1. este independent de runtime write;
2. elimina aliasurile legacy dintr-un strat already-readonly;
3. reduce riscul ca viitorul bridge sa se bazeze pe coduri gresite.

### C. `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1`

Scope:

1. defineste ce inseamna explicit `confirmation_state` pentru `return_cant`;
2. separa clar:
   - Step 1 confirmation
   - row confirmed
   - finish_setup confirmed
   - component truth confirmed
3. defineste blockers si non-promotion rules.

De ce urmeaza dupa A/B:

1. are nevoie de path-ul final canonic din A;
2. trebuie sa opereze peste pricing refs deja normalizate in adapter/readiness language.

### D. `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1`

Scope:

1. defineste sursa valida pentru `confirmed_perimeter_m`;
2. interzice explicit promovarea automata din `quote_geometry.letter_perimeter_m`;
3. defineste relatia cu `components.face.confirmed_perimeter` si evidence/context fallback.

De ce vine dupa C:

1. confirmed perimeter nu are sens fara confirmation semantics;
2. contractul de sursa trebuie sa se lege de regula “cand are voie sa devina confirmed”.

### E. `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_V1`

Permis numai dupa A-D.

Scope ulterior:

1. derivare persist-time in `save_finish_setup_for_intake_v6_workspace(...)`;
2. write runtime pentru `components.return_cant.instances.<instance_key>`;
3. fara quote/order/execution side effects in acelasi slice.

## 7. First Recommended Slice

Primul slice recomandat este:

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1
```

Rationale:

1. este blockerul structural care tine toate celelalte blockere nerezolvabile in mod curat;
2. builderul legacy `components.returnCant` si backbone-ul legacy `components.return.*` arata ca tinta finala nu este inca contractata;
3. confirmation, perimeter source si runtime bridge write nu pot fi stabilite fara path final si politica de compatibilitate;
4. adapter pricing alignment este important, dar nu defineste singur unde vor fi scrise acele refs.

## 8. Mandatory Rules For Follow-up Slices

Reguli care raman obligatorii pentru toate slice-urile urmatoare:

1. nu se foloseste `components.returnCant` ca target final;
2. nu se foloseste `components.return.*` ca target final;
3. nu se folosesc pricing targete legacy ca finale;
4. `quote_geometry.letter_perimeter_m` ramane context only pana la contract explicit;
5. Pasul 1 nu este component confirmation;
6. `finish_setup.confirmed` nu este component confirmation;
7. niciun slice intermediar nu are voie sa scrie Product Truth final inainte ca A-D sa fie inchise.

## 9. Recommended Next Prompt

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1
```
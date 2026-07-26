# Return Cant Product Truth Capture Runtime Bridge Plan

## 1. Purpose

Acest document fixeaza planul pentru bridge-ul runtime de capture Product Truth pentru `return_cant`, fara implementare runtime si fara schimbari de UI, Pricing, adapter, Quote, Order sau Execution.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
mode = product_truth_capture_runtime_bridge_plan
```

Acest document nu implementeaza:

- UI nou sau UI refactor;
- Product Truth writes;
- adapter runtime writes;
- Pricing changes;
- calculation / preview;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan;
- endpoint public nou;
- migration / seed.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_BRIDGE_PLAN_BLOCKED
```

Semnificatie exacta:

1. punctul corect de integrare pentru bridge-ul viitor a fost identificat;
2. dictionarul terminologic E2E poate fi fixat fara ambiguitate;
3. target paths pentru `return_cant` pot fi definite;
4. implementarea nu este inca un slice mic sigur, deoarece lipsesc contractul runtime canonic si sursele confirmate necesare pentru write.

## 3. Existing Runtime Infrastructure Found

### 3.1 Frontend runtime save path

Exista deja un traseu clar de persistare Intake V6:

1. `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
   - construieste payload-ul curent prin `buildCurrentFinishBody(...)`;
   - persista prin `saveCurrentFinish(...)`;
   - include `letter_group_finishes[]` si `artwork_finishes[]` in `finish_setup`.
2. `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
   - expune `saveFinishSetup(...)` si `confirmProductComposition(...)`;
   - persista workspace-ul prin endpoint-urile existente;
   - hidrateaza inapoi workspace-ul persistat.
3. `frontend/src/lib/intakeV6/intakeV6Api.ts`
   - are deja `PUT /workspaces/{workspace_id}/finish-setup`;
   - are deja `PUT /workspaces/{workspace_id}/product-composition-confirmation`.

### 3.2 Backend persistence path

Exista deja un punct backend corect pentru viitorul bridge derivat:

1. `backend/services/intake_v6_workspace_service.py`
   - `save_finish_setup_for_intake_v6_workspace(...)` normalizeaza `finish_setup` si il persista in `payload_raw["finish_setup"]`;
   - ruleaza deja derivari additive pe payload, de exemplu:
     - `apply_product_composition_recommendation(payload_raw)`
     - `apply_v6_pricing_preview_derived_state(payload_raw)`
2. pattern-ul repo-ului arata ca state derivat runtime se adauga in backend in timpul persistarii workspace-ului, fara endpoint public nou.

### 3.3 Existing read-only Product Truth infrastructure

Exista deja infrastructura read-only relevanta:

1. `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
   - construieste un draft Product Truth in memorie din `finish_setup`, `layer_role_setup` si `quote_geometry`;
   - nu persista nimic.
2. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
   - defineste campurile canonice asteptate pentru `return_cant`;
   - marcheaza explicit lipsa de mapping / confirmation / perimeter ca `blocked`.
3. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
   - defineste target paths per instance pentru `components.return_cant.instances.<instance_key>`;
   - produce doar referinte readonly si blockers.
4. `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
   - foloseste `buildProductTruthDraft(...)` si `mapReturnCantTruthFieldsReadonly(...)` doar pentru awareness.

## 4. Runtime Bridge Target

Bridge-ul viitor trebuie sa consume date runtime existente si sa scrie un runtime Product Truth canonic pentru fiecare instanta `return_cant`, fara sa scrie costuri si fara sa confirme implicit dependinte neconfirmate.

### 4.1 Input surface

Input-ul minim necesar pentru bridge:

- `finish_setup.letter_group_finishes[]`
- `finish_setup.artwork_finishes[]`
- `layer_role_setup` / selected or confirmed layer refs
- stare explicita de confirmare a componentei
- sursa real confirmata pentru perimeter, daca exista
- output-ul adapterului readonly ca evidence / mapping aid
- referintele de Pricing keys deja verificate pentru `return_cant`

### 4.2 Output target paths

```text
components.return_cant.instances.<instance_key>.finish_variant.type =
  stock_color | vinyl_application | paint_application

components.return_cant.instances.<instance_key>.finish_variant.stock_color_label

components.return_cant.instances.<instance_key>.finish_variant.vinyl.material_family
components.return_cant.instances.<instance_key>.finish_variant.vinyl.series
components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code
components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference

components.return_cant.instances.<instance_key>.finish_variant.paint.system
components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference

components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor

components.return_cant.instances.<instance_key>.geometry.perimeter_source
components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m
components.return_cant.instances.<instance_key>.layer_group_ids
components.return_cant.instances.<instance_key>.confirmation_state
```

### 4.3 Correct implementation point

Pe baza infrastructurii actuale, punctul corect pentru bridge-ul viitor este backend persist-time derivation in:

`backend/services/intake_v6_workspace_service.py`

mai exact in `save_finish_setup_for_intake_v6_workspace(...)`, dupa:

1. normalizarea lui `finish_setup`;
2. persistarea `payload_raw["finish_setup"]`;
3. availability-ul `layer_role_setup`, `quote_geometry` si `product_composition_confirmed` din acelasi payload.

Rationale:

1. backend-ul este sursa canonica a `payload_json`;
2. exista deja pattern derivat additiv pe payload;
3. se evita divergenta intre state local frontend si state persistat;
4. nu necesita endpoint public nou.

## 5. Confirmation Rules

Reguli obligatorii pentru implementarea viitoare:

1. `quote_geometry.letter_perimeter_m` este doar evidence/context.
2. `quote_geometry.letter_perimeter_m` nu poate deveni `confirmed_perimeter_m` fara confirmare Product Truth/component explicita.
3. `Confirmat in Pasul 1` nu este suficient pentru `components.return_cant.instances.<instance_key>.confirmation_state = confirmed`.
4. Pasul 1 confirma ownership / layer roles, nu component truth complet.
5. bridge-ul trebuie sa ramana `blocked` daca lipsesc:
   - `layer_group_ids` reale pentru instanta;
   - `confirmed_perimeter_m` din sursa confirmata;
   - `confirmation_state` explicit de componenta.
6. bridge-ul nu are voie sa promoveze automat row-level `confirmed=true` din `letter_group_finishes[]` sau `artwork_finishes[]` la component confirmation.
7. bridge-ul nu are voie sa promoveze `finish_setup.confirmed = true` la `return_cant.confirmation_state = confirmed`.

## 6. E2E Terminology Dictionary

### 6.1 UI user-facing

- `Culoare Stoc`
- `Folie autocolanta`
- `Vopsit RAL`

### 6.2 Technical / backend / Product Truth

- `stock_color`
- `vinyl_application`
- `paint_application`

### 6.3 Catalog

- `stock_color_label`
- `vinyl.series` = `Oracal 641` / `Oracal 651` / `Oracal 8500`
- `vinyl.color_code`
- `paint.system = RAL`
- `paint.ral_code`

### 6.4 Pricing

- `material_profile_width`
- `vinyl_material`
- `vinyl_application_labor`
- `ral_paint_material_by_width`
- `ral_paint_labor`

### 6.5 Legacy / transitional only

Acesti termeni nu pot deveni Product Truth final pentru `return_cant`:

- `oracal`
- `ral_paint`
- `PAINTING`
- `MAT-VOPSEA-RAL`
- `VINYL_APPLICATION`
- `FACE_VINYL_APPLICATION_LABOR`

## 7. Bridge Readiness Matrix

| requirement | source_exists | runtime_source | target_path | can_write_now | blocker | next_action |
|---|---|---|---|---|---|---|
| finish variant type | yes, partial | `finish_setup.letter_group_finishes[].return_finish_type`, `finish_setup.artwork_finishes[].return_finish_type` | `components.return_cant.instances.<instance_key>.finish_variant.type` | no | no canonical runtime instance container is persisted today | define runtime container contract and instance key policy |
| stock color label | yes, partial | `return_finish_type` mapped through readonly adapter | `components.return_cant.instances.<instance_key>.finish_variant.stock_color_label` | no | stock color label is derived readonly only, not persisted canonical truth | add canonical writer mapping for stock colors |
| vinyl series | yes, partial | `materialCode` / current UI path, adapter infers `641` or `651` | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.series` | no | current runtime is still finish-setup centric and only partially models series | define canonical field write and preserve UI terminology |
| vinyl color code | yes, partial | `return_oracal_code` / per-row `colorCode` | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code` | no | legacy `return_oracal_code` is not canonical per-instance Product Truth | map row source to per-instance canonical target |
| vinyl catalog reference | yes, derived only | readonly adapter builds `vinyl_color_catalog:*` reference | `components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference` | no | catalog reference exists only as readonly derived evidence | define persisted reference format |
| paint system | yes, partial | `return_finish_type = ral_paint` plus readonly adapter normalization | `components.return_cant.instances.<instance_key>.finish_variant.paint.system` | no | no canonical persisted paint object today | add canonical paint object contract |
| RAL code | yes, partial | per-row `return_oracal_code` / `colorCode` reused for RAL | `components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code` | no | current source field name is legacy and overloaded | map to canonical `paint.ral_code` |
| paint catalog reference | yes, derived only | readonly adapter builds `paint_color_catalog:RAL:*` reference | `components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference` | no | reference is readonly only | define persisted catalog reference format |
| material profile width key | yes | depth from row + verified pricing keys | `components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width` | no | bridge writer missing; no canonical instance payload | write verified uppercase pricing key by width |
| vinyl material key | yes, but alignment required | verified pricing registry plus series selection | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material` | no | no canonical writer; current readonly evidence still marks material alignment boundary | write final verified material code from pricing contract |
| vinyl labor key | yes, but mismatched in readonly adapter | pricing contract verified as `RETURN_CANT_VINYL_APPLICATION_LABOR` | `components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor` | no | readonly adapter still references lowercase legacy target `return_cant_vinyl_application_labor` | align writer contract to verified uppercase key before implementation |
| RAL material by width key | yes, but mismatched in readonly adapter | pricing contract verified as `MAT-VOPSEA-RAL-CANT-{30|60|80|100}MM` | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width` | no | readonly adapter still references legacy target `ral_paint_material_<width>mm` | align writer contract to verified uppercase material keys before implementation |
| RAL labor key | yes, but mismatched in readonly adapter | pricing contract verified as `RETURN_CANT_RAL_PAINT_LABOR` | `components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor` | no | readonly adapter still references legacy target `ral_paint_application_labor` | align writer contract to verified uppercase labor key before implementation |
| layer group ids | partial | `layer_role_setup.layers[]`, `svg.selected_layer_refs[]`, row keys | `components.return_cant.instances.<instance_key>.layer_group_ids` | no | mapper marks existing evidence as context only; no canonical assignment of rows to component instance ids | define instance-key-to-layer-group mapping contract |
| confirmed perimeter | no | only `quote_geometry.letter_perimeter_m` context exists | `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m` | no | no backend or frontend canonical runtime source for `components.face.confirmed_perimeter` | create confirmed perimeter source contract first |
| confirmation state | no | only `finish_setup.confirmed`, row `confirmed`, and Step 1 confirmation evidence | `components.return_cant.instances.<instance_key>.confirmation_state` | no | no explicit component confirmation field exists; current evidence is insufficient by policy | define component-level confirmation contract first |

## 8. Blockers

Blockerele exacte care tin verdictul pe `BLOCKED`:

1. nu exista in runtime un container canonic persistat pentru `components.return_cant.instances.<instance_key>`;
2. nu exista o sursa runtime canonica pentru `components.face.confirmed_perimeter` in backend sau frontend;
3. nu exista o stare explicita de component confirmation pentru `return_cant`; doar evidence partial (`finish_setup.confirmed`, row `confirmed`, Step 1 confirmation);
4. `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` ramane pe model legacy `components.returnCant.*`, nu pe noul contract per-instance;
5. `backend/services/form_system_contract_backbone_service.py` ramane pe path-uri vechi de tip `components.return.*`, nu pe `components.return_cant.instances.*`;
6. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts` inca referentiaza key targets legacy pentru trei pricing slots:
   - `return_cant_vinyl_application_labor`
   - `ral_paint_material_<width>mm`
   - `ral_paint_application_labor`
   in locul key-urilor finale verificate;
7. ReviewStep foloseste mapper-ul readonly fara `canonicalRuntime`, ceea ce confirma ca runtime writer-ul nu exista inca.

## 9. Smallest Safe Next Slice

Nu este sigur sa se mearga direct la `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_V1`.

Slice-ul necesar inainte de implementare trebuie sa fie un contract/alignment slice care:

1. fixeaza containerul runtime canonic pentru `components.return_cant.instances.<instance_key>`;
2. fixeaza sursa pentru `components.face.confirmed_perimeter` sau alternativa confirmata owner-safe;
3. fixeaza component confirmation semantics pentru `return_cant`;
4. aliniaza key references din readonly adapter la codurile Pricing finale deja verificate;
5. decide mapping-ul dintre row keys (`group_key` / `layer_key`) si `instance_key`.

## 10. Recommended Next Prompt

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1
```
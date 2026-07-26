# INTAKE_V6_COMPONENT_CALCULATION_READINESS_AUDIT_V1

Date: 2026-07-08
Project: WorkOS
Mode: read-only audit / docs-only

## 1. Safety gate

Commands run:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git status --short --untracked-files=no
git diff --check
```

Result:
- accepted HEAD before audit: `29d8d84`
- staged files before audit: none
- tracked diffs before audit: none
- preexisting untracked parked lanes: present
- action taken on parked lanes: none
- safety verdict: audit could proceed

## 2. Scope

Goal:
- verify whether Intake V6 is structurally ready for future controlled per-component calculation inside the current product-root direction
- verify this without activating component root, component quote, downstream execution, pricing authority, or Logo root offerability

In scope:
- Product System read-only inspection
- Form System backbone read-only inspection
- Intake V6 modular form read-only inspection
- ProductDefinition preview path read-only inspection
- Pre-order technical preview read-only inspection
- UI runtime check with screenshots when available

Out of scope:
- new code
- new UI behavior
- component root
- component quote
- Pricing / Quote / Order / Execution activation
- DB writes / migrations / seeds
- extra cleanup around `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`

Out-of-scope stale note:
- stale mounting alias references remain out of scope unless they appear in active code/runtime; no new cleanup was performed in this audit

## 3. Files inspected

Contracts and recent reports:
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/qa/product-system-template-ui-alignment-2026-07-08/PRODUCT_SYSTEM_TEMPLATE_UI_ALIGNMENT_AND_COMPONENT_OWNED_CALCULATION_AUDIT_V1.md`
- `docs/qa/active-template-scope-alignment-2026-07-08/ACTIVE_TEMPLATE_SCOPE_FRONTEND_BACKEND_ALIGNMENT_AUDIT_AND_GUARD_V1.md`
- `docs/qa/mounting-finish-alias-canonicalization-2026-07-08/MOUNTING_AND_FINISH_ALIAS_CANONICALIZATION_AUDIT_V1.md`
- `docs/qa/stale-mounting-alias-cleanup-2026-07-08/DOCS_ONLY_STALE_MOUNTING_ALIAS_REFERENCE_CLEANUP_V1.md`
- corresponding worklogs from `docs/worklog/realignment/`

Backend:
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/pre_order_technical_preview_readonly_service.py`
- `backend/services/template_usage_mode_policy.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/active_template_scope.py`

Frontend:
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/features/product-system/templateWorkflow.ts`
- `frontend/src/api/blueprintDossier.ts`
- `frontend/src/lib/activeTemplateScope.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.ts`
- `frontend/src/lib/intakeV6/preOrderTechnicalPreviewApi.ts`
- `frontend/src/lib/intakeV6/intakeV6ComponentQuestionDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6LedLighting.ts`
- `frontend/src/lib/intakeV6/intakeV4LedLighting.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ModularFormAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/PreOrderTechnicalPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLightingSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`

## 4. Canonical findings summary

Confirmed canonical roots and roles:
- current Work Intake root: `TPL-VOLUMETRIC-LETTERS_v2`
- current root type: `product_template`
- current quote mode: `product_total`
- shared components are technical/shared units, not roots
- `TPL-VOLUMETRIC-LOGO_v1` remains candidate / linked child only / not Work Intake root

Confirmed canonical component templates:
- face: `TPL-VOLUMETRIC-FACE_v1`
- back: `TPL-VOLUMETRIC-BACK_v1`
- return/cant: `TPL-VOLUM-ALUMINIU_v1`
- lighting: `TPL-VOLUMETRIC-LED_v1`
- finish: `TPL-VOLUMETRIC-FINISH_v1`
- premount/support: `TPL-METAL-PREMOUNT-STRUCTURE_v1`

Confirmed central boundary:
- component calculation readiness is not component root
- component calculation readiness is not component quote
- current direction supports component-owned truth inside one product-root flow

## 5. Component readiness matrix

| component concept | canonical template code | current role | Product System visibility | Form System field ownership | Intake V6 visibility | Product Truth path exists? | ProductDefinition consumption exists? | has required dimensions? | has material rule? | has operation rule? | has validation/blockers? | can be calculated alone later? | what is missing? | owner gate required? | risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| face | `TPL-VOLUMETRIC-FACE_v1` | shared technical component in letters/logo composition | yes, shared component + shared base | yes: face fields, face finish target, layer role ownership | yes, through Finisaje and Product Truth draft | yes, `components.face.*` and finish target path | yes, face module and aggregate component roles | partial yes: area exists, contour depends on SVG/layer truth | partial yes: fallback defaults exist, explicit canonical control still partial | yes: face cut/CNC preview references exist | yes: face material/thickness fallback blockers | partial yes | explicit canonical face material/thickness control, stronger confirmed truth state, isolated face preview control | yes for future standalone behavior | fallback defaults can be confused with confirmed truth |
| return/cant | `TPL-VOLUM-ALUMINIU_v1` | required linked child module / shared component | yes | yes: return depth, return finish, module activation | yes, in Finisaje and cant-specific rows | yes, `components.return.*`, `return_depth_mm`, `return_finish_type` | yes, module refs and component roles | yes: perimeter and depth are modeled | yes: profile/material and ORACAL/RAL flow exist | yes: return forming / bonding / painting ops | yes: depth/material confirmation blockers | yes, best candidate after face | explicit isolated return preview control, clearer dependency on confirmed face geometry, stronger confirmation semantics | yes for future standalone behavior | dependency on perimeter truth and face geometry can leak monolith assumptions |
| back | `TPL-VOLUMETRIC-BACK_v1` | shared technical back panel | yes | partial yes: backing mode, bevel | yes, under Iluminare & spate | partial yes, back is modeled in Product Truth draft and backbone | yes, back module and aggregate roles exist | partial: area comes from face area proxy, not dedicated back geometry | partial yes: backing mode exists, material rule more implicit | yes: back cut preview_only references exist | yes: back remains partial in backbone/contracts | partial | explicit back material field, dedicated back confirmation state, isolated back preview logic | yes for future standalone behavior | back is still represented too much as sibling of lighting/backing group, not independent surface |
| lighting | `TPL-VOLUMETRIC-LED_v1` | shared primary LED module; logo uses strategy/profile source | yes, strongest shared strategy story in Product System | yes: lighting system, led count, PSU fields | yes, Iluminare tab + confirm summary | partial yes, `components.lighting.*` and electrical warnings exist | yes, module refs, operations, canonical values | partial: perimeter/area inputs exist, but zoning/circuits/service access are missing | partial yes: LED/PSU material roles exist | partial yes: install/test ops exist, but formula boundaries remain partial | yes: lighting mode confirmation and unresolved warnings | partial | explicit lighting zones, circuits, service access, stronger PSU blocker semantics, future logo strategy truth | yes for future standalone behavior | easy to over-read as ready-for-pricing while it is still preview/readiness only |
| finish | `TPL-VOLUMETRIC-FINISH_v1` | shared finish/artwork boundary | yes | yes, but spread across face/cant/artwork/mounting-template fields | yes, Finisaje tab is rich | partial yes, draft separates finish target/artwork/print/lamination | yes, finish module is consumed by ProductDefinition | partial: geometry comes from face/return/artwork, not finish-owned dimensions | yes: ORACAL/RAL and print/lamination choices exist | partial yes: apply/finish preview-only references exist | yes: finish target missing, artwork decision missing, fallback notes | partial | canonical finish target field in UI, split print vs lamination persisted truth, cleaner service/material boundary | yes for future standalone behavior | finish still blends service/material/artwork and job-level fallback semantics |
| premount/support | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | optional addon support structure | yes | partial yes: `mounting_system` is canonical intake field, support bridge remains derived | yes, Montaj tab + confirm summary | partial yes, `components.mounting.*` and support warning path exist | yes, optional module refs and derived canonical values exist | partial: width and derived bar length exist; no first-class component dimensions | partial yes: bar material/profile derived from mounting system | yes: premount prep ops exist | yes: trigger mismatch warning and support/mounting blockers | partial | first-class support_required/support_type fields, clean separation support vs mounting scope, removal of bridge ambiguity | yes for future standalone behavior | strongest risk of semantic confusion between support structure, mounting method and later execution scope |
| logo candidate | `TPL-VOLUMETRIC-LOGO_v1` | candidate product / linked child composition | yes, candidate product only | partial, through shared contracts and logo-specific strategy notes | visible in composition and Review linked segments | partial, linked runtime segments exist | partial, ProductDefinition can expose linked segments, not root flow | partial yes via artwork/logo geometry | partial yes | partial yes | yes: root blocked, offerability blocked | partial, but not now | owner GO, Product Truth, modular form, ProductDefinition, pricing, runtime offerability | yes, explicit owner GO | high risk if UI/agents confuse linked child with offerable root |
| letters root | `TPL-VOLUMETRIC-LETTERS_v2` | only owner-valid root | yes | yes | yes | yes | yes | yes | yes | yes | yes | not applicable as component-only | keep product-root boundary while exposing component-scoped readiness | no extra owner gate for current root | monolith risk remains if component-owned truths are not surfaced explicitly enough |

## 6. Product System findings

Observed in code and UI:
- Product System now shows the six shared volumetric components explicitly
- Letters is `offerable`
- Logo is `candidate / not Work Intake`
- shared LED remains a primary shared module, while logo lighting is a strategy/profile source
- Product System proves composition and reuse clearly

Readiness implication:
- Product System already teaches that face/back/return/finish/lighting/premount are component-like technical units
- it does not yet provide an operator-facing concept of `calculeaza doar componenta`
- current Product System detail/editor still reads partly like parent-template orchestration rather than per-component calculation console

Verdict:
- good structural direction
- insufficient by itself for operator-controlled per-component calculation

## 7. Form System findings

Confirmed:
- Form System backbone blocks `component_template` roots and `component_only` quote mode
- shared component template codes return `COMPONENT_ROOT_BLOCKED`
- backbone fields already carry owner component, source type, state and Product Truth path candidate
- fields explicitly distinguish `suggested`, `hydrated`, `fallback`, `missing`, `confirmed`
- readiness model explicitly preserves blockers and downstream no-write safety

Meaning:
- the repo already contains the semantic machinery needed to reason about component-owned truth
- this is enough for readiness auditing and future preview/control slices
- this is not the same as a live per-component calculate action

Key blocker pattern:
- operator confirmation remains the Product Truth boundary
- broad/global blockers still remain even when a single field row can be visually relaxed at runtime

## 8. Intake V6 findings

Confirmed from code and UI:
- Review is split in tabs that map well to component-owned domains: `Finisaje`, `Iluminare`, `Montaj`
- Finish rows separate face, cant and artwork concerns
- LED configuration, PSU sizing display, backing mode and mounting system are visible in operator flow
- Confirm step summarizes prepared components without implying final root/quote changes
- modular form awareness panel says explicitly that the product summary is not final price and does not generate tasks

Important limitations:
- there is no operator control named or equivalent to `doar fata`, `doar cant`, `doar spate`, `doar lighting`
- the flow is still anchored in one letters-root workspace
- some fields remain fallback/hydrated until confirmed
- support/premount still relies on a bridge from `mounting_system` to derived `metal_support_required`

Verdict:
- Intake V6 is component-aware and readiness-aware
- Intake V6 is not yet component-calculation-controlled

## 9. Product Truth path findings

Strong signs of readiness:
- `productTruthDraftBuilder` builds per-component structures for face, back, return_cant, finish, artwork, support, mounting, electrical
- states are explicit: `suggested`, `hydrated`, `fallback`, `confirmed`
- blockers are attached to components, not just to a global quote shell

Weak spots:
- face material/thickness still depend on owner-approved fallback until explicit confirmation
- finish target is still not first-class enough in current UI/runtime truth
- support is inferred from SVG/mounting bridge when first-class support truth is absent
- lighting remains partial around zones/circuits/service access

Verdict:
- Product Truth path exists for every audited component concept
- not every path is equally strong or equally confirmed

## 10. ProductDefinition consumption findings

Confirmed:
- ProductDefinition preview consumes modular form contract + aggregate + optional workspace payload
- it classifies selected/optional/inactive modules
- it carries canonical values and validation results
- it preserves no-pricing/no-write boundary

Meaning:
- there is already a read-only consumer that can express component-scoped readiness consequences
- this is a strong sign that future per-component calculation preview can be added without first creating component roots

Missing:
- explicit per-component standalone preview contract
- explicit component-scoped module selection intent from operator
- stronger distinction between optional addon, inactive, pending and calculable-alone

## 11. Component-by-component verdict

### Face

Verdict: `PARTIAL_READY`

What exists:
- face area
- face finish interaction
- face-owned module and Product Truth path
- face cut operation references

What is missing:
- canonical explicit face material/thickness control without fallback dependence
- dedicated face-only preview surface

Can calculate separately later:
- yes, partial

### Return / cant

Verdict: `MOST_READY`

What exists:
- perimeter
- depth
- finish and color registries
- module activation and return operations

What is missing:
- explicit isolated operator intent for return-only calculation
- stronger separation from parent geometry assumptions

Can calculate separately later:
- yes

### Back

Verdict: `PARTIAL_READY_WITH_GAP`

What exists:
- backing mode
- bevel state
- ProductDefinition path
- back operation references

What is missing:
- more explicit back material and dedicated back-owned geometry confirmation

Can calculate separately later:
- partial

### Lighting

Verdict: `PARTIAL_READY_WITH_AUDIT_DEBT`

What exists:
- LED module count from perimeter
- strip/module load computation
- PSU sizing proposal
- UI section with detailed LED/PSU preview

What is missing:
- zoning
- circuits
- service access
- stronger warnings for electrical edge cases
- explicit logo lighting Product Truth strategy path

Can calculate separately later:
- partial

### Finish

Verdict: `PARTIAL_READY_WITH_BOUNDARY_BLUR`

What exists:
- ORACAL/RAL registry-backed choices
- print/lamination modeled in UI and Product Truth draft
- face/cant/artwork split exists

What is missing:
- canonical first-class finish target control
- persisted split print_required vs lamination_required truth
- clearer material vs service vs artwork boundary

Can calculate separately later:
- partial

### Premount / support

Verdict: `PARTIAL_READY_WITH_SEMANTIC_RISK`

What exists:
- optional addon module
- mounting system field
- derived support activation
- module outputs and operations

What is missing:
- first-class support_required/support_type truth
- clean separation support vs mounting scope
- removal of trigger mismatch bridge dependency

Can calculate separately later:
- partial

### Logo candidate

Verdict: `LINKED_ONLY_NOT_READY_FOR_ROOT`

What exists:
- linked child participation
- shared component participation
- candidate visibility in Product System
- linked runtime segment context in Review

What is missing:
- owner GO
- explicit root offerability contract
- full Product Truth and ProductDefinition path as independent root

Can calculate separately later:
- partial as linked child, no as root now

## 12. General answers to audit questions

### A. General readiness

1. Intake V6 este pregatit conceptual pentru component calculation?
   - Da, conceptual si contractual, dar nu operator-controlat end-to-end.
2. Exista structura de fields pe component ownership?
   - Da.
3. Exista source/state mapping suficient?
   - Da, pentru audit/readiness; partial pentru standalone control.
4. Exista valori confirmate vs fallback/hydrated/suggested?
   - Da, explicit.
5. Exista Product Truth path pentru fiecare componenta?
   - Da, dar cu maturitati diferite.
6. Exista ProductDefinition consumption clar?
   - Da, read-only si fara pricing.
7. Exista blockers per componenta?
   - Da.
8. Exista risc de monolit in `TPL-VOLUMETRIC-LETTERS_v2`?
   - Da, daca UI continua sa ascunda prea mult ownership-ul componentelor sub un singur flow de produs.

### B. Face-only

- Date necesare: layer/face mapping, area, face material, thickness, face finish target.
- Dimensiuni/suprafata: exista.
- Material face: exista doar partial, cu fallback implicit.
- Finish interaction: exista.
- Operatie debitare: exista ca preview/reference.
- Lipsa pentru standalone: control explicit material/thickness + preview/selector de componenta.

### C. Return/cant-only

- Date necesare: perimeter, return depth, finish type, material/color.
- Lungime/perimetru/cant height: exista.
- Material/profile/cant: exista.
- Operatie aplicare/formare cant: exista.
- Dependenta de face cut: exista prin geometria parinte.
- Lipsa pentru standalone: intent/operator selector si separare mai clara de geometria radacina.

### D. Back-only

- Date necesare: backing mode, material, bevel, area.
- Material back: partial.
- CNC/cut operation: exista ca preview/reference.
- Interactiune cu LED/mounting: exista, dar nu este independenta.
- Lipsa: control material explicit si adevar confirmat dedicat back.

### E. Lighting-only

- Date necesare: perimeter sau strip length, lighting mode, module wattage, PSU, eventual zones.
- Surface/area/density: exista partial.
- LED module count: exista.
- PSU sizing: exista.
- Warning/blocker PSU: exista partial.
- Lipsa: zones, circuits, service access, edge-case semantics.

### F. Finish-only

- Finish poate fi calculat separat?
  - Partial, dar nu curat inca.
- Este material/service sau doar field?
  - Este un boundary mixt material + service + artwork.
- Oracal/RAL/print/laminare sunt registry-backed sau hardcoded?
  - ORACAL/RAL sunt registry-backed in UI relevante; print/lamination au si reguli/options hardcoded de roll width/layout.
- Exista risc de pricing direct?
  - Da, daca cineva confunda finisajul configurat cu pret final; UI actual incearca sa previna asta.
- Lipsa: split canonical al target-ului si al serviciilor print/lamination.

### G. Premount/support

- Este calculabil separat?
  - Partial, doar ca readiness direction.
- Este piesa fizica, support profile, metadata sau operation support?
  - In modelul actual este optional addon fizic + operation support, dar semantica suport/montaj este inca amestecata.
- Exista risc sa fie confundat cu montaj operational?
  - Da.
- Exista risc sa intre in Execution?
  - Nu in acest slice, deoarece no-write boundary este clar; dar semantic confusion exista.
- Lipsa: first-class support truth si trigger alignment curat.

### H. Logo candidate

- Poate participa ca linked child/candidate?
  - Da.
- Este blocat ca Work Intake root?
  - Da.
- Are aceleasi componente ca letters sau profile proprii?
  - Partajeaza baza comuna, dar are profile/strategy sources proprii, mai ales la lighting si logo-specific modules.
- Ce lipseste pentru future owner-approved root?
  - Owner GO, root offerability, Product Truth complet, ProductDefinition dedicat, pricing boundary separat.
- Ce nu trebuie activat acum?
  - root, quote, offerability, downstream.

## 13. UI screenshot evidence

Captured routes:
- `http://127.0.0.1:3000/product-system`
- `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`

Captured screenshots:
- `01_product_system_overview.png`
- `02_product_system_components.png`
- `03_product_system_letters_root.png`
- `04_intake_v6_review.png`
- `05_intake_v6_confirm.png`
- `06_intake_v6_form_system_backbone.png`

Notes:
- Product System route loaded cleanly and exposed shared modules plus Letters/Logo statuses
- Intake V6 route loaded Review and Confirmare surfaces successfully
- one console 404 was observed during Intake V6 route load, but the operator workspace still rendered and was usable for read-only audit

## 14. Honest UI opinion

Ce este clar:
- Product System spune bine povestea de shared components
- Review tabs separa bine Finisaje / Iluminare / Montaj
- Confirmare spune clar ca nu este pret final si ca nu creeaza comanda/executie/stoc
- Backbone awareness panel comunica bine ideea de source/state/Product Truth

Ce este confuz:
- `Support` versus `Mounting` inca se pot amesteca semantic
- `Spate` sta prea aproape de `Iluminare/backing`, nu ca un component ownership de sine statator
- finish boundary ramane prea compactat intre fata/cant/artwork/template

Ce pare hardcodat:
- multe reguli de display si unele optiuni de finish/roll width sunt clar hardcoded in UI helpers
- component question badges sunt explicit display-only si nu sunt autoritate runtime

As accepta UI ca owner?
- pentru directia de readiness si component ownership: da, cu rezerve
- pentru a lansa `calculeaza doar componenta`: nu inca

Ce trebuie imbunatatit in urmatorul slice:
- selector read-only clar de component scope
- map explicit component -> fields -> Product Truth path -> ProductDefinition consequence
- separare mai curata support vs mounting
- clarificare back ca boundary separat

UI verdict:
- `UI_PASS_WITH_SCREENSHOTS_AND_RISK`

## 15. Missing pieces before implementation

Mandatory before any implementation slice:
- explicit component field ownership map consumabil in UI si audit
- read-only component calculation preview contract per component scope
- stronger canonical controls for face material/thickness
- stronger back-owned truth
- finish target explicit si split print/lamination truth
- support_required/support_type first-class fields
- lighting zones/circuits/service access model
- operator-facing component selector that does not change root type or quote mode

## 16. Forbidden scope confirmation

- no component root
- no component quote
- no `root_type=component_template`
- no `quote_mode=component_only`
- no Logo offerability activation
- no Pricing activation change
- no Quote/Order activation change
- no Execution activation change
- no ProductAggregate change
- no TaskGraph change
- no ExecutionPlan change
- no DB writes
- no migrations
- no seed changes
- no cleanup around `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`

## 17. Recommended next slice

Recommended next slice:
- `INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT_V1`

Reason:
- readiness is already visible in contracts, Product Truth draft, ProductDefinition preview, and UI
- the missing piece is not Pricing or Execution
- the missing piece is an explicit read-only component-scoped preview/selector contract that stays inside product-root boundaries

Alternative narrower preparatory slice:
- `FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1`

## 18. Roadmap awareness checkpoint

Nota directie: 8/10

Cat sunt in directia stabilita: 84%

Why not higher:
- direction is strong in contracts and read-only previews
- operator control for per-component calculation is not explicit yet
- some components still depend on fallback/hydrated or bridge semantics

Dead pieces check:
- no new dead runtime/code paths introduced by this audit
- stale mounting alias remained out of scope and was not expanded into a side-task

Forbidden scope check:
- passed

UI proof check:
- passed with screenshots

## 19. Final audit verdict

Central answer:

```text
Da, Intake V6 este pregatit partial si credibil pentru directia de component calculation controlat in viitor,
dar numai ca product-root flow component-aware, nu ca root/quote separat acum.
```

Per component later-separate calculation potential:
- face: partial yes
- return/cant: yes
- back: partial yes
- lighting: partial yes
- finish: partial yes
- premount/support: partial yes
- logo candidate: linked-child partial only, not root

Root conclusion:
- architecture and read-only runtime direction are good enough for a dedicated preview/contract slice
- they are not yet good enough for direct implementation of `calculeaza doar componenta`
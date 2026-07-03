# PRODUCT SYSTEM — TEMPLATE WORKFLOW BUILDER / TASK ORDERING

## Scope

Phase 1 audit + read-only workflow preview.

Phase 2 local preview implemented in frontend only.

Explicitly out of scope:

- DB changes
- migrations
- seed changes
- Cost Engine changes
- Quote / Order changes
- execution task persistence
- Intake V6 mutations
- SVG analyzer changes
- AssemblyPreview backend changes
- persistent drag/drop

## 1. Cine stabileste ordinea azi

### A. Structural / Blueprint order

Current source of truth:

- `backend/models/product_blueprint_dossier.py`
  - order is stored implicitly inside `sections_json`
- `backend/services/product_aggregate_service.py`
  - `_component_display_order_map(...)` reads component order from dossier sections
  - `ProductAggregateComponent.display_order` is explicit
  - `ProductAggregateModule.display_order` exists in schema, but may be absent in payloads
- `backend/models/product_template_module_links.py`
  - no `sort`, no `display_order`, no `order_index`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
  - Blueprint vertical uses module display order when present
  - fallback derives module order from `aggregate.components[*].source_template_code -> display_order`

Conclusion:

- blueprint order is explicit at component level in dossier/aggregate;
- link-table order is accidental because the link table has no sort field.

### B. Operational / Assembly preview order

Current source:

- `backend/schemas/intake_v6_assembly.py`
  - `OperationCandidate` has no explicit sequence/order field
  - `ConsolidatedTask` has no explicit sequence/order field
- `backend/services/intake_v6_assembly_preview_service.py`
  - candidates are emitted in component iteration order from `assembly.component_instances`
  - consolidated tasks are built from grouping keys and dictionary insertion order
  - dependencies are labels/groups such as `dependency_group`, not a full ordered workflow chain

Conclusion:

- assembly preview has operational grouping, but no explicit stable production workflow sequence;
- current order is mostly incidental: component iteration + grouping behavior.

### C. Execution order

There are two execution-adjacent read models today:

1. `ExecutionPlanV2Preview`
   - `backend/schemas/execution_plan_v2.py`
   - `PlannedTaskPreview.sequence_index` is explicit
   - `backend/services/execution_plan_v2_preview_service.py`
     - sorts task rules by `ProductAggregateTaskRule.sequence`
     - then derives simple linear dependencies between consecutive tasks

2. `ProductSystemExecutionPreviewService`
   - `backend/services/product_system_execution_output_service.py`
   - reads `production_operations.sequence_index` explicitly
   - reads `task_templates` ordered by DB `id ASC`
   - final operation order is explicit if `production_operations.sequence_index` exists
   - final task-template order is only partially explicit because task templates themselves are not ordered beyond row id

Persisted execution plan:

- `backend/models/execution_plan.py`
  - stores `tasks_json` as the persisted output envelope
  - no relational `execution_tasks.order_index` model exists in this repo snapshot

Conclusion:

- execution order is explicit in some preview/planning layers (`sequence`, `sequence_index`),
- but not unified across Product System, Assembly preview, and task template rows.

## 2. Problems identified

1. Blueprint order, production workflow order, and execution task order are not separated clearly in the Product System UI.
2. Link table does not own structural order.
3. Assembly preview groups work candidates but does not model a human-readable ordered workflow.
4. Execution preview can carry order, but that order is downstream and should not be mistaken for blueprint structure.
5. There is no owner-facing read model today for recommended production steps per product template.

## 3. The 3 order types

### Blueprint order

Purpose: how the product is composed.

Examples:

1. Face
2. Finish
3. Return
4. Back
5. Lighting
6. Mounting

### Workflow / Production order

Purpose: how the product should be executed in the workshop.

Examples:

1. Artwork review
2. Print / laminate if needed
3. Nesting prep
4. Face cut
5. Back cut
6. Return prep
7. Assembly
8. Electrical
9. QC
10. Packing

### Execution task order

Purpose: real order of tasks after order acceptance.

Must later be derived from:

- workflow template
- order conditions
- operation candidates
- consolidated tasks
- dependencies

Rule:

- execution order must not be derived directly from blueprint order.

## 4. Phase 1 implementation

Frontend-only read-only implementation added:

- `frontend/src/features/product-system/templateWorkflow.ts`
  - `TemplateWorkflow`
  - `WorkflowStep`
  - default recommended workflows for:
    - `TPL-VOLUMETRIC-LETTERS_v2`
    - `TPL-VOLUMETRIC-LOGO_v1`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
  - new `Workflow productie` section in product-template cards
  - compact read-only step list
  - stable step numbering
  - title + short description
  - badges for component / finish / labor / material / QC
  - optional condition badge when relevant
  - disabled informational control:
    - `Drag & drop va fi disponibil dupa persistenta workflow.`

No backend, DB, or seed change was made.

## 5. Recommended read model contract

```ts
TemplateWorkflow {
  template_code
  version
  status
  source
  steps[]
}

WorkflowStep {
  step_id
  order_index
  title
  description
  step_type
  component_refs[]
  finish_refs[]
  labor_operation_refs[]
  material_role_refs[]
  machine_type
  workcenter
  role_required
  condition_label
  depends_on_step_ids[]
  produces[]
  quality_checks[]
  is_optional
  is_enabled
}
```

This is intentionally frontend-only in Phase 1, but designed to become a future persisted contract.

## 6. Default workflow — TPL-VOLUMETRIC-LETTERS_v2

Implemented read-only recommended steps:

1. Verificare fisiere si layere
2. Pregatire nesting fata litere
3. Debitare fata litere
4. Debitare spate
5. Pregatire cant / volum
6. Print / folie / laminare, daca exista
7. Asamblare corp litere
8. Montaj LED
9. Cablare si sursa
10. Test electric
11. Pregatire montaj
12. QC final / ambalare

## 7. Default workflow — TPL-VOLUMETRIC-LOGO_v1

Implemented read-only recommended steps:

1. Verificare logo si zone artwork
2. Print / laminare artwork, daca exista
3. Pregatire nesting fata logo
4. Debitare fata logo
5. Debitare spate logo
6. Pregatire cant / volum logo
7. Aplicare folie / artwork pe fata, daca exista
8. Asamblare corp logo
9. Montaj LED
10. Cablare si sursa
11. Test lumina
12. Pregatire montaj
13. QC final / ambalare

## 8. Drag/drop Phase 2 implementation

Implemented now in frontend only:

1. drag handle per workflow step
2. local reordering in UI
3. immediate dependency-order validation
4. local preview status: recommended vs unsaved local preview
5. reset to recommended order

Deliberately not implemented yet:

1. persistent save
2. DB contract
3. backend validation endpoint
4. execution integration

Minimum dependency validations:

- `electrical_test` after `install_led_modules`
- `laminate` after `print`
- `assembly` after face/back/return cutting/prep
- `packing` after final QC

Owner override is allowed locally in preview, but warnings remain visible when dependency order is broken.

## 9. Tests / validation

Focused frontend tests added/updated in:

- `frontend/src/features/product-system/TemplateLibraryView.test.tsx`

Validated:

1. letters workflow preview renders
2. logo workflow preview renders
3. steps show title + description
4. order is stable
5. optional steps show condition badge
6. drag/drop local reorder works in Phase 2 preview
7. dependency violations are surfaced immediately in preview
8. reset restores recommended order

Commands run:

- `pnpm.cmd --dir C:\Users\offic\workos_app_vs\frontend exec vitest run src/features/product-system/TemplateLibraryView.test.tsx`
- `pnpm.cmd --dir C:\Users\offic\workos_app_vs\frontend build`

Build passed. Existing non-blocking build warnings remain outside this task.

## 10. Not touched

- DB schema
- backend services for aggregate / assembly preview / execution
- migrations
- seeds
- Cost Engine
- Quote / Order logic
- persisted execution tasks
- Intake V6 runtime behavior
- SVG analyzer

## 11. Recommended next step

Phase 3 should introduce a persisted workflow contract owned by Product System, separate from:

- blueprint component order
- assembly preview grouping
- execution plan materialization

That persistence layer should become the only place where drag/drop order is saved, versioned, and validated before Phase 4 execution starts using it.

## Correction — Workflow editor moved out of product card

Owner feedback:

- workflow-ul este prea important ca sa ramana desfasurat inline in cardul principal din Product System;
- cardul trebuie sa ramana curat;
- editorul trebuie accesat separat, intr-un spatiu dedicat, fara ruta noua in aceasta etapa.

Ce era gresit:

- Phase 2 local a fost functional corect,
- dar lista lunga de pasi, drag handles, warning-uri detaliate si reset-ul erau randate direct in cardul de produs,
- ceea ce incarca excesiv UI-ul principal si amesteca sumarul template-ului cu editorul de workflow.

Ce a fost pastrat:

- `frontend/src/features/product-system/templateWorkflow.ts`
- helper-ele de reorder local
- helper-ele de validare
- reset la recommended workflow
- testele pentru reorder / warning / reset, rescrise pe noua suprafata UI

Ce a fost mutat:

- lista completa de pasi
- drag/drop local
- warning-urile detaliate
- badge-urile detaliate pe pas
- controlul de reset

Cum arata cardul acum:

- cardul produs afiseaza doar sumarul workflow:
  - numar pasi
  - status `Recomandat` sau `Draft local`
  - `Workflow valid` sau `X avertizari`
  - actiune `Configureaza workflow`

Cum se acceseaza editorul:

- click pe `Configureaza workflow`
- se deschide un `Sheet` lateral dedicat in aceeasi pagina
- fara router nou
- fara persistenta

Ce contine panelul dedicat:

- header cu `Workflow productie — TEMPLATE_CODE`
- family/template context
- status `Recomandat · Nepersistat` sau `Draft local · Nepersistat`
- numar pasi
- warning count
- notice clar ca draftul este local si nu afecteaza executia reala
- lista completa de pasi
- drag/drop local
- warning-uri detaliate atat in sumar, cat si langa pasii afectati
- reset la recommended workflow
- footer explicit: persistenta va veni in Phase 3

State behavior confirmat:

- drafturile locale sunt pastrate per `template_code`
- map local: `workflowDraftsByTemplateCode`
- inchiderea panelului nu reseteaza draftul
- reset-ul afecteaza doar template-ul activ
- reorder pe logo nu modifica letters si invers
- warning count din card este calculat separat pentru fiecare template

Ce ramane pentru Phase 3:

- contract persistent/versionat pentru `TemplateWorkflow`
- audit al formei contractului
- persistenta reala
- reguli de validare persistente
- integrarea ulterioara in execution doar dupa aprobarea UI si a contractului

## Correction — Slim product template cards

Owner feedback:

- in tabul `Template-uri produs`, cardurile de produs erau in continuare prea inalte;
- sectiunile `Blueprint vertical`, `Module obligatorii` si lista mare `Layer 01 / Layer 02 / ...` ocupau mult loc;
- pentru un catalog cu multe template-uri, aceasta prezentare ar fi produs prea mult scroll si zgomot vizual.

Ce ocupa prea mult loc:

- blocul expandat de sub fiecare product template;
- randarea child modules ca mini-carduri mari sub template;
- titlurile child-template-urilor tehnice direct in fluxul principal al tabului de produse.

Ce a fost scos din card:

- `Blueprint vertical`
- `Module obligatorii`
- lista `Layer XX`
- randurile mari cu `TPL-VOLUMETRIC-LOGO-FACE_v1`, `...-FINISH_v1`, `...-BACK_v1` sub template-ul parinte

Unde se vad acum modulele:

- ca chips compacte in cardul produsului;
- in tabul `Componente / module reutilizabile`;
- prin actiunea `Vezi componente`, care muta utilizatorul in tabul tehnic si evidentiaza componentele folosite de template-ul curent.

Cum se acceseaza workflow:

- prin `Configureaza workflow` din cardul slim;
- editorul complet se deschide in panelul lateral dedicat deja introdus anterior.

Cum arata acum cardul:

- header compact cu `template_code`, badge-urile existente si family label;
- chips compacte pentru componente;
- sumar workflow pe o singura zona compacta:
  - `12 pasi` / `13 pasi`
  - `Recomandat` / `Draft local`
  - `Workflow valid` / `X avertizari`
- actiuni compacte:
  - `Vezi componente`
  - `Configureaza workflow`

Ce ramane pentru next step:

- daca ownerul vrea si mai mult control, `Componente / module reutilizabile` poate primi un filtru mai explicit per template;
- optional, in viitor poate exista un panel separat `Vezi componente` cu rezumat compact per product template;
- Phase 3 ramane neschimbat: persistenta/versionarea `TemplateWorkflow` dupa aprobarea UI.
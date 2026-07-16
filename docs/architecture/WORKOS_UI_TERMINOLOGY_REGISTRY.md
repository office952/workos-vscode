# WorkOS UI Terminology Registry

> **WAVE 0 FOUNDATION POLICY** · **Romanian-first** · **NOT UI IMPLEMENTATION**  
> Build: **W0-B3** · GO: `GO_W0_B3_SHARED_FOUNDATION_POLICIES` · Date: 2026-07-16  
> Companion: `docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md`  
> Seed source (analysis): `docs/qa/workos-complete-page-system-figma-direction-study-v1/03_UI_UX_ROMANIAN_TERMINOLOGY_REGISTRY.md`  
> Display fields align with W0-B1: `display_label_ro` · `technical_alias` · `translation_key` · `description_ro`

---

## 1. Registry entry model

| Field | Purpose |
|-------|---------|
| `term_id` | Stable id (`term.product_system`) |
| `internal_term` | English/internal concept name |
| `display_label_ro` | Default operator UI label |
| `technical_alias` | Secondary EN/tech label |
| `translation_key` | Future i18n key |
| `context` | navigation / systems / pages / statuses / actions / fields / errors / technical / business |
| `allowed_variants` | Acceptable synonyms |
| `forbidden_variants` | Do not use |
| `status` | `RECOMMENDED` · `OWNER_GATED` · `APPROVED` · `DEPRECATED` |
| `owner` | Registry owner |
| `authority_reference` | Doc / Figma / OD |
| `last_validated_at` | Date |
| `notes` | Constraints |

**Categories:** navigation · systems · pages · statuses · actions · fields · errors · technical concepts · business concepts

Rules:

- No page-specific duplicate translations outside this registry.
- Technical identifiers (`TPL-*`, UUIDs, API fields) are not operator labels.
- Disputed terms remain `OWNER_GATED` until OD.

---

## 2. Seed registry (recommendations)

Status legend: **R** = RECOMMENDED · **G** = OWNER_GATED · **A** = already used consistently in RO nav (treat as de facto approved for that surface)

| term_id | internal_term | display_label_ro | technical_alias | translation_key | context | status | forbidden_variants | notes |
|---------|---------------|------------------|-----------------|-----------------|---------|--------|--------------------|-------|
| term.product_system | Product System | Catalog produse | Product System | nav.product_system | navigation | APPROVED | Sistem Produse | OD-TERM-01 owner-approved display (UI not applied yet) |
| term.product_family | Product Family | Familie produs | Product Family | system.product_family | systems | R | | |
| term.product_template | Product Template | Șablon produs | Product Template | system.product_template | systems | R | | Keep `TPL-*` EN |
| term.dossier | Template Dossier | Dossier șablon | Dossier | system.dossier | technical | G | Dosar tehnic as BOM | OD-01: metadata only |
| term.module | Module | Modul | Module | system.module | systems | R | | |
| term.linked_module | Linked Module | Modul legat | Linked Module | system.linked_module | systems | R | | |
| term.sold_module | Sold Module | Modul vândut | Sold Module | system.sold_module | business | R | | |
| term.sold_scope | Sold Scope | Domeniu vândut | Sold Scope / offer_scope | system.sold_scope | business | R | | API keeps `offer_scope` |
| term.form_system | Form System | Sistem formular | Form System | system.form_system | systems | R | | |
| term.intake_v6 | Intake V6 | Intake V6 | Intake V6 | system.intake_v6 | systems | R | | Version label may stay |
| term.workspace | Workspace | Spațiu de lucru | Workspace | system.workspace | business | APPROVED | | OD-TERM-07; UUID stays EN |
| term.product_definition | ProductDefinition | Definiție produs | ProductDefinition / PD | system.product_definition | technical | APPROVED | | OD-TERM-05; PD debug OK |
| term.product_aggregate | ProductAggregate | Structura tehnică a produsului | ProductAggregate / BOM | system.product_aggregate | technical | APPROVED | Fișă de lucru | OD-TERM-06 |
| term.readiness | Readiness | Pregătire | Readiness | status.readiness | statuses | R | | |
| term.missing_fields | Missing Fields | Câmpuri lipsă | Missing Fields | fields.missing | fields | R | | |
| term.work_intake | Work Intake | Preluare lucrare | Work Intake | nav.work_intake | navigation | APPROVED | | OD-TERM-02; UI not applied yet |
| term.quote | Quote | Ofertă | Quote | nav.quotes | navigation | A | | Nav RO |
| term.order | Order | Comandă | Order | nav.orders | navigation | A | | |
| term.execution_plan | ExecutionPlan | Plan de execuție | ExecutionPlan | system.execution_plan | systems | R | | ≠ reality |
| term.execution_reality | Execution Reality | Realitate execuție | Execution Reality | system.execution_reality | systems | R | | |
| term.workcenter | Workcenter | Centru de lucru | Workcenter / WC | system.workcenter | technical | R | | WC in debug |
| term.inventory | Inventory | Inventar | Inventory | nav.inventory | navigation | A | | Nav “Inventar & OC” |
| term.pricing | Pricing | Tarife | Pricing | nav.pricing | navigation | APPROVED | | OD-TERM-04; not commercial SoT |
| term.machines | Machines | Utilaje | Machines | nav.utilaje | navigation | A | | |
| term.employees | Employees | Angajați | Employees | nav.employees | navigation | A | | |
| term.attendance | Attendance | Pontaj | Attendance | nav.attendance | navigation | A | | |
| term.module_chain | Module Chain | Harta sistemelor | Module Chain | system_map.title | navigation | APPROVED | | OD-TERM-08; technical route stays `/modules` |
| term.governance | Governance | Guvernanța sistemului | System Governance | governance.title | navigation | APPROVED | | OD-TERM-09; route stays `/governance` |
| term.documentation_center | Documentation Center | Centrul de documentație | Documentation Center | docs.center.title | navigation | R | | Route planned `/documentation` |
| term.source_of_truth | Source of Truth | Sursă de adevăr | Source of Truth | governance.source_of_truth | technical | R | | |
| term.boundary | Boundary | Limită | Boundary | governance.boundary | technical | R | | |
| term.handoff | Handoff | Transfer | Handoff | system.handoff | technical | R | | |
| term.ready | Ready | Gata | Ready | status.ready | statuses | R | | |
| term.draft | Draft | Ciornă | Draft | status.draft | statuses | R | | |
| term.partial | Partial | Parțial | Partial | status.partial | statuses | R | | |
| term.blocked | Blocked | Blocat | Blocked | status.blocked | statuses | R | | |
| term.preview | Preview | Previzualizare | Preview | status.preview | statuses | R | | |
| term.stale | Stale | Învechit | Stale | status.stale | statuses | R | | |
| term.save | Save | Salvează | Save | action.save | actions | R | | |
| term.confirm | Confirm | Confirmă | Confirm | action.confirm | actions | R | | |
| term.continue | Continue | Continuă | Continue | action.continue | actions | R | | |
| term.back | Back | Înapoi | Back | action.back | actions | R | | |
| term.cancel | Cancel | Anulează | Cancel | action.cancel | actions | R | | |
| term.control_tower | Control Tower | Control Tower | Control Tower | nav.control_tower | navigation | APPROVED | | OD-TERM-03 brand EN |
| term.shop_floor | Shop Floor | Shop Floor | Shop Floor | nav.shop_floor | navigation | APPROVED | | OD-TERM-03 brand EN |

---

## 3. Owner decisions — APPROVED DISPLAY DIRECTION (2026-07-16)

Recorded under `GO_W0_B2_DOCUMENTATION_INDEX_READ_MODEL`.  
**Display-language only. UI labels not applied in application code in this build.**  
Technical routes/IDs unchanged (e.g. `/modules`, `ModuleChain`, `product_system`).

Plain-language pack: [`WORKOS_UI_TERMINOLOGY_OWNER_DECISION_PACK.md`](./WORKOS_UI_TERMINOLOGY_OWNER_DECISION_PACK.md)

| ID | Approved display_label_ro | technical_alias | Notes |
|----|---------------------------|-----------------|-------|
| OD-TERM-01 | Catalog produse | Product System | Not Sistem Produse |
| OD-TERM-02 | Preluare lucrare | Work Intake | |
| OD-TERM-03 | Control Tower / Shop Floor | (same EN brands) | Keep English |
| OD-TERM-04 | Tarife | Pricing | |
| OD-TERM-05 | Definiție produs | ProductDefinition / PD | PD debug OK |
| OD-TERM-06 | Structura tehnică a produsului | ProductAggregate / BOM | Forbid Fișă de lucru |
| OD-TERM-07 | Spațiu de lucru | Workspace | |
| OD-TERM-08 | Harta sistemelor | Module Chain | Route remains `/modules` |
| OD-TERM-09 | Guvernanța sistemului | System Governance | Route remains `/governance` |
| OD-TERM-10 | (policy) Romanian primary; safe Romanian fallback for missing operator strings; technical EN only in debug/admin | — | Softens earlier “EN tech as last resort for operators” |
| OD-TERM-11 | Operator UI Romanian; API/IDs/logs/debug may stay technical English | — | |

Resolved without OD (already consistent RO nav): Ofertă, Comandă, Execuție, Inventar, Utilaje, Angajați, Pontaj, Setări, Clienți.

---

## 4. Forbidden practices

- Shipping UI string changes under W0-B3 (policy only)
- Inventing synonyms per page
- Using ENGLISH status chips next to Romanian for the same status without registry entry
- Declaring terms APPROVED without owner when status is OWNER_GATED

---

## 5. Maintenance

After each UI/terminology-affecting build: update this registry + Documentation Impact Gate class `TERMINOLOGY_UPDATE`. Supersede rows with `DEPRECATED` rather than silent overwrite.

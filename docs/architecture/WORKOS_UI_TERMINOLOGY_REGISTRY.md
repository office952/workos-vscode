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
| term.product_system | Product System | Sistem produs | Product System | nav.product_system | navigation | G | Sistem Produse (unapproved) | Nav currently EN |
| term.product_family | Product Family | Familie produs | Product Family | system.product_family | systems | R | | |
| term.product_template | Product Template | Șablon produs | Product Template | system.product_template | systems | R | | Keep `TPL-*` EN |
| term.dossier | Template Dossier | Dossier șablon | Dossier | system.dossier | technical | G | Dosar tehnic as BOM | OD-01: metadata only |
| term.module | Module | Modul | Module | system.module | systems | R | | |
| term.linked_module | Linked Module | Modul legat | Linked Module | system.linked_module | systems | R | | |
| term.sold_module | Sold Module | Modul vândut | Sold Module | system.sold_module | business | R | | |
| term.sold_scope | Sold Scope | Domeniu vândut | Sold Scope / offer_scope | system.sold_scope | business | R | | API keeps `offer_scope` |
| term.form_system | Form System | Sistem formular | Form System | system.form_system | systems | R | | |
| term.intake_v6 | Intake V6 | Intake V6 | Intake V6 | system.intake_v6 | systems | R | | Version label may stay |
| term.workspace | Workspace | Spațiu de lucru | Workspace | system.workspace | business | G | | UUID stays EN |
| term.product_definition | ProductDefinition | Definiție produs | ProductDefinition / PD | system.product_definition | technical | G | | PD OK in debug |
| term.product_aggregate | ProductAggregate | Agregat tehnic | ProductAggregate | system.product_aggregate | technical | G | Fișă de lucru | |
| term.readiness | Readiness | Pregătire | Readiness | status.readiness | statuses | R | | |
| term.missing_fields | Missing Fields | Câmpuri lipsă | Missing Fields | fields.missing | fields | R | | |
| term.work_intake | Work Intake | Preluare lucrare | Work Intake | nav.work_intake | navigation | G | | Nav currently EN |
| term.quote | Quote | Ofertă | Quote | nav.quotes | navigation | A | | Nav RO |
| term.order | Order | Comandă | Order | nav.orders | navigation | A | | |
| term.execution_plan | ExecutionPlan | Plan de execuție | ExecutionPlan | system.execution_plan | systems | R | | ≠ reality |
| term.execution_reality | Execution Reality | Realitate execuție | Execution Reality | system.execution_reality | systems | R | | |
| term.workcenter | Workcenter | Centru de lucru | Workcenter / WC | system.workcenter | technical | R | | WC in debug |
| term.inventory | Inventory | Inventar | Inventory | nav.inventory | navigation | A | | Nav “Inventar & OC” |
| term.pricing | Pricing | Tarife | Pricing | nav.pricing | navigation | G | Prețuri registru alt. | Not commercial SoT |
| term.machines | Machines | Utilaje | Machines | nav.utilaje | navigation | A | | |
| term.employees | Employees | Angajați | Employees | nav.employees | navigation | A | | |
| term.attendance | Attendance | Pontaj | Attendance | nav.attendance | navigation | A | | |
| term.module_chain | Module Chain | Harta sistemelor | Module Chain | system_map.title | navigation | G | Lanț module as primary | Primary RO = Harta; alias Module Chain |
| term.governance | Governance | Guvernanța sistemului | System Governance | governance.title | navigation | G | | |
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
| term.control_tower | Control Tower | Control Tower | Control Tower | nav.control_tower | navigation | G | | Brand EN candidate |
| term.shop_floor | Shop Floor | Shop Floor | Shop Floor | nav.shop_floor | navigation | G | | Brand EN candidate |

---

## 3. Owner decisions (ambiguous only)

| ID | Issue | Variants | Recommendation | Impact | Blocks | Proposed answer |
|----|-------|----------|----------------|--------|--------|-----------------|
| OD-TERM-01 | Product System nav label | Product System / Sistem produs / Sistem Produse | **Sistem produs**; forbid Sistem Produse | Nav + PS chrome | UI polish waves | A: Sistem produs |
| OD-TERM-02 | Work Intake nav label | Work Intake / Preluare lucrare | **Preluare lucrare** | Comercial nav | Intake polish | A: Preluare lucrare |
| OD-TERM-03 | Keep Control Tower / Shop Floor EN | EN vs RO | Keep EN as **brand** aliases | Ops nav | Cosmetic only | A: keep EN brand |
| OD-TERM-04 | Pricing label | Pricing / Tarife / Prețuri registru | **Tarife** | Resurse nav | Pricing polish | A: Tarife |
| OD-TERM-05 | ProductDefinition UI | Definiție produs / PD / ProductDefinition | Operator: **Definiție produs**; debug: PD | Embed panels | Wave 3 | A: Definiție produs |
| OD-TERM-06 | ProductAggregate UI | Agregat tehnic / Aggregate / BOM | **Agregat tehnic**; forbid Fișă de lucru | Embed panels | Wave 3 | A: Agregat tehnic |
| OD-TERM-07 | Workspace operator term | Spațiu de lucru / Workspace | **Spațiu de lucru** | Intake | Wave 2 | A: Spațiu de lucru |
| OD-TERM-08 | Module Chain secondary alias | Module Chain / Lanț module | Primary **Harta sistemelor**; alias **Module Chain** | `/modules` honesty | W0-B4 | A: as recommended |
| OD-TERM-09 | Governance secondary alias | Governance / System Governance | Primary **Guvernanța sistemului**; alias **System Governance** | `/governance` honesty | W0-B5 | A: as recommended |
| OD-TERM-10 | Locale fallback | RO-only vs RO→EN tech | Fallback: RO registry → technical EN | i18n | G-W0-I18N | A: RO→EN tech |
| OD-TERM-11 | Debug/operator language split | Same RO vs EN debug | Operator RO; debug panels may show EN technical | All pages | None | A: split allowed |

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

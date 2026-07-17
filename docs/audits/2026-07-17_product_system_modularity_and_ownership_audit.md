# Product System Modularity and Ownership E2E Audit

**Date:** 2026-07-17  
**Build:** `PRODUCT_SYSTEM_MODULARITY_AND_OWNERSHIP_E2E_AUDIT`  
**Mode:** Audit only — no implementation, schema, seed, or migration  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `7960bcafb11630da4c5c80cc50907201604678f0`  
**Remote:** `https://github.com/office952/workos-vscode.git`  
**Runtime:** FE `:3000`, BE `:8001` (probed)

---

## 0. Verdict (audit)

```text
PRODUCT_SYSTEM_MODULARITY_OWNER_GATES_READY
IMPLEMENTATION = STOP
MODULARITY MODEL = REWORK (concept normalization before expansion)
```

Open structural conflicts (do not continue renderer/template expansion until decided):

1. **COMPONENT_TEMPLATE_MODEL_CONFLICT** — no first-class Component Template table; “component” means 4+ incompatible things.
2. **SETTINGS_OWNERSHIP_CONFLICT** — options/defaults split across Product System contract, frontend maps, company settings, workspace.
3. **MODULE_CAPABILITY_CONFLATION** — “capability” in catalog ≠ UI interaction capability; mini-modules are Letters-only and falsely look generic.

---

## 1. Repository gate

| Check | Result |
|-------|--------|
| Repo | `C:/w/psiso` |
| Remote | match |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `7960bca` (matches latest renderer pilot report) |
| Dirty tree | large unrelated dirty tree — **not modified** |
| Staged | none for this audit |
| Application code | **unchanged** |

---

## 2. Current concept dictionary

| Concept | Current implementation | Current meaning | Owner | Consumers | Reusable scope | Problems |
|---------|------------------------|-----------------|-------|-----------|----------------|----------|
| Product Family | DB `product_families` + seed `CANONICAL_FAMILIES` (14) | Slug grouping + optional `default_template_id` | Product Families registry | Intake family field, template denormalized `family_id` | Global catalog | Does not own modules/settings/pricing; orphan family_ids on child templates |
| Product Template | DB `product_templates` (one table for roots + modules) | Root/orchestrator **or** linked child/module row | Product System seeds + scope policy | Availability, PD, Aggregate, Intake binding | Template-specific; links enable reuse | Dual role of same table; version = code suffix only |
| Component Template | **No dedicated table** | Overloaded: BOM `components_json` row; linked child TPL; policy `component_only` codes (often missing DB); inactive `TPL-COMP-LETTER-*` | Mixed / aspirational | Form backbone, FE maps, Aggregate dossier | Intended reusable — **not proven** | Primary ownership conflict |
| Mini-Module | Code registry `mini_module_registry_volumetric_v2.py` | Logical operational capability over dossier/child | Product System (code) | Form contract, PD, Aggregate mapping | **Letters v2 only** today | Names look generic; apply_to is pilot-only |
| Capability | FE catalog label Standalone/Linked/Both; mobile action flags | Catalog usage mode **or** runtime action permission | FE + policy / mobile backend | Product System UI cards | Not a product semantic | Conflated with mini-module / React |
| Module Link | DB `product_template_module_links` | Parent→child template activation + mapping | Product System seeds | Aggregate modules, PD composition | Per parent template | Trigger fields can mismatch Intake |
| Operation Template | `operations_json` on product_templates + commercial/internal rule catalogs | Process step with formula/workcenter | Template JSON + registries | Aggregate ops, CostEngine, CPP rules, Plan | Mixed catalogs | Duplicate op catalogs across CE/CPP/EIC |
| Task Template | Dossier task rules + plan materialization | Execution task projection | Dossier / ExecutionPlan path | Shop floor, Post-Job | Job-specific after plan | Not same as operation template |
| Formula Definition | Ops `formula_id`, planning_duration_contract, CE formulas | Quantity/duration computation | Product System / Aggregate / CE (split) | Minutes ≠ money (TE2E-028) | Template/module scoped | Multiple formula owners |
| Intake Section | FE Review shells + pilot `render_sections` | UI grouping | Mixed PS / FE | Operator UI | Pilot sections PS; rest FE | Lighting/finish/montaj risk becoming Intake concepts |
| Intake Field | Bindings + FE controls | Operator-editable fact path | Mixed | Workspace, PD | Pilot metadata PS | Options often FE |
| ProductDefinition Fact | PD preview compile | Validated canonical configuration | ProductDefinition | Aggregate | Job-specific compile | Must not invent defaults (policy) |
| ProductAggregate Component | Resolved components | Technical BOM truth | Aggregate | CPP measurements, Plan | Derived from PD | |
| ProductAggregate Operation | Resolved ops + minutes | Technical ops + planning duration | Aggregate | Plan, Post-Job | Derived | Minutes ≠ commercial price |
| Commercial Measurement | `letters_commercial_measurement_service` | Non-monetary qty for CPP | Aggregate (Letters) | CPP 7G | Letters pilot | Fallback to workspace paths |
| Pricing Key | Registry codes / rule `registry_pricing_code` | Lookup key into rates | Pricing Registry / commercial rules | CPP | Company/product | Ambiguous when reconstructed from workspace |
| Pricing Rule | `commercial_rules_volumetric_v2` + registry | How measurement → money line | CPP / Pricing Registry | Commercial preview | Letters rules code-backed | 7I not started |
| Resource/Material Option | Inventory materials + FE option maps + contract options | Selectable materials/finishes | Split Company inventory / FE / contract | Intake, Aggregate | Should be company/catalog | Parallel option authorities |
| Company Setting | `company_commercial_settings`, markup policies | VAT, FX, markup policies | Company Settings | Dry-run, offer | Global company | |
| Product Setting | Template defaults / module defaults | Required modules, default depths | Template/module (partial) | PD/Intake | Template | Incomplete layer |
| Workspace Value | Intake V6 payload `finish_setup` etc. | Concrete job answers | Intake workspace | PD → Aggregate → CPP | Job-specific | |
| Snapshot Value | Quote/Order snapshots | Frozen accepted truth | Quotes/Orders | Execution | Immutable after accept | Must not live-mutate from PS |
| Execution Value | Plan tasks, actuals | Runtime production truth | Execution | Post-Job | Job-specific | Must not rewrite upstream product truth |

---

## 3. Product Family audit

**Creates family:** seed `CANONICAL_FAMILIES` + CRUD API `/api/v1/entities/product-families`.  
**First-class:** yes (DB rows).  
**Shared modules/settings/pricing:** **no** — grouping + default template pointer only.  
**Intake rendering:** family string on workspace; does not drive form contract.

| Family example | Status | Notes |
|----------------|--------|-------|
| Litere volumetrice (`litere_volumetrice`) | **ACTIVE** | Live root `TPL-VOLUMETRIC-LETTERS_v2` |
| Casete luminoase | **REFERENCE** | Family exists; no active Intake V6 root in availability probe |
| Textile/banner (`textile_banner` / banner under print) | **PARTIAL** | `TPL-BANNER-STANDARD` Build4; archived by active-scope |
| Colantări auto (`colantari_auto`) | **MISSING** product | Family only — no template seed |
| Print format mare | **PARTIAL** | Banner/print Build4 templates; not Intake V6 active root |
| Panouri ACP | **PARTIAL** | ACM boxed offerable as module/root; panel templates archived |
| Totems / lightboxes / vehicle zones | **MISSING** or REFERENCE | No modular Intake composition |

**Runtime probe (2026-07-17):** 14 families; availability list dominated by Letters/Logo/ACM/metal modular set.

---

## 4. Product Template audit

### What it owns today

| Responsibility | Owned? | Evidence |
|----------------|--------|----------|
| Allowed/required/optional components | Partial | `components_json` + module links |
| Modules | Partial | `product_template_module_links` + mini-module registry (code) |
| Product-level fields | Partial | Form contract bindings (Letters pilot) |
| Defaults | Partial | `default_values_json` on links; FE defaults |
| Dependencies | Partial | Mini-module `dependencies`; PD composition graph |
| Formulas | Indirect | `operations_json.formula_id` → other registries |
| Operations | Yes (JSON) | `operations_json` |
| Task templates | Partial | Dossier, not template JSON alone |
| Readiness | Partial | Usage mode + Intake readiness helpers |
| Commercial measurements | No (Aggregate service) | Letters measurement builder |
| Versioning | Code suffix | `_v2` in `template_code` |

### Answers

1. **Root of product?** Yes for offerable roots (`TPL-VOLUMETRIC-LETTERS_v2`). Same table also stores non-roots.  
2. **Composes Component Templates?** Intended yes; **runtime composes** BOM JSON + child Product Templates — not a Component Template entity.  
3. **Composes Mini-Modules?** Indirectly — registry keyed by template code (Letters only).  
4. **Directly define Intake fields?** Partially via modular form contract derived from mini-modules/backbone — not full UI.  
5. **Define pricing keys?** Indirectly via ops/materials/rules — not tariff ownership.  
6. **Define production operations?** Yes in `operations_json` (+ child templates).  
7. **Defaults vs allowed options?** Mixed; many options still FE.  
8. **Versioned?** Template code suffix; dossier integer version.  
9. **Share components/modules?** Child templates reusable via links (metal, ACM, volum aluminiu).  
10. **Override module defaults?** `default_values_json` / `input_mapping_json` on links — limited.

### Template matrix (runtime-relevant)

| Product template | Family | Components | Modules | Intake contract | Pricing outputs | Operations | Version |
|------------------|--------|------------|---------|-----------------|-----------------|------------|---------|
| `TPL-VOLUMETRIC-LETTERS_v2` | litere_volumetrice | Parent BOM + dossier comps | Links: volum Al, metal, ACM; mini-modules×8 | Modular form + pilot render_sections | Aggregate measurements → CPP | Parent+child ops JSON | `_v2` / dossier 3 |
| `TPL-VOLUMETRIC-LOGO_v1` | litere_volumetrice | Logo composition children | Candidate path | Preview form only | Guarded non-offerable | Seeded | `_v1` |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | structuri_metalice_premontaj\* | STRUCTURA | Standalone + Letters child | N/A as root Intake | Via parent/CPP | Own ops | `_v1` |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | panouri_acp_iluminate | ACM support | Linked optional | Trigger mounting | CPP path | Own ops | `_v1` |
| `TPL-BANNER-STANDARD` | print_large_format | Banner comps | None modular registry | Legacy/Build4 | Legacy | Banner ops | Build4 |
| Vehicle graphics | colantari_auto | — | — | — | — | — | **MISSING** |

\*family_id not in canonical family seed — denormalization drift.

---

## 5. Component Template audit

**Meaning today: MIXED / not first-class.**

| Question | Answer |
|----------|--------|
| Physical product part? | Yes for `components_json` / dossier `comp_*` |
| Reusable across templates? | Intended; proven only for linked child TPLs (metal/ACM/Al) |
| Owns materials/ops/formulas? | BOM rows and child templates do; aspirational FACE_v1 does not exist as DB |
| Owns Intake fields? | Form backbone maps fields → `component_template_code` (often non-DB) |
| Owns pricing measurements? | No — Aggregate/CPP |
| Child components? | Nested JSON possible |
| Optional/conditional? | Via module links + activation rules |

**Inconsistent uses of “component”:** physical part · UI section · module/child template · task group · material bundle · future `TPL-COMP-LETTER-*`.

---

## 6. Mini-Module audit

Registry is **code-only**, indexed only for `TPL-VOLUMETRIC-LETTERS_v2`.

| Module | Meaning | Templates | Inputs (sample) | Outputs | Ops | Components | Pricing effect | Execution effect |
|--------|---------|-----------|-----------------|---------|-----|------------|----------------|------------------|
| geometry_svg | SVG geometry gate | Letters v2 | vector, dims | PD dims | svg_geometry_analysis | — | readiness | frozen dims |
| debitare_fata | Face cut | Letters v2 | face fields | comp_face_litere | face cut | dossier face | CE/CPP materials | CNC tasks |
| modelare_cant | Return/cant | Letters v2 | return_depth/finish | volum Al child | return forming | side_wall | return lines | forming tasks |
| debitare_spate | Back | Letters v2 | backing | comp_spate | back cut | back | back lines | back CNC |
| sistem_led | Lighting | Letters v2 | lighting_system_type, PSU | comp_led | LED install | LED | LED lines | electrical tasks |
| finisaje | Finish + sablon | Letters v2 | finishes, mounting_template_* | finish/sablon | sablon CNC | finish | sablon lines | packaging |
| structura_suport | Support | Letters v2 | metal_support / ACM | metal/ACM child | premount | support | structure lines | linked child work |
| electrica_logo | Emblem electrical | Letters v2 | emblem_* | — | — | — | FUTURE | FUTURE |

**Reusable across families?** Names suggest yes; **`applies_to_template_codes` = Letters only** → false-generic.

---

## 7. Capability audit

| Sense | Exists? | Product System may declare? | Names React? |
|-------|---------|----------------------------|--------------|
| Catalog Standalone / Linked child / Both | FE `productSystemCanonicalCatalogModel.ts` + availability | Usage mode — OK | No |
| Mobile/runtime action capability | Backend flags | N/A | No |
| UI interaction capability (layered finishes editor, etc.) | **Not** a backend contract type | Target: declare capability **type** only | Current FE owns specialized React sections |

**Boundary check:** Product System form contract does **not** embed React component names. Frontend maps contract field types → generic renderer **or** specialized Letters sections.  
**Risk:** treating mini-modules or catalog “capability” as UI capability catalogs would recreate product catalogs in the wrong layer.

**Required target boundary (owner-aligned):**

```text
Product System may declare a capability type.
Frontend maps capability type to an approved renderer.
Product System must not name React components.
```

**Current:** partially respected for pilot field types; specialized Letters UI still product-named in FE.

---

## 8. Operation / task audit

| Operation domain | Owner | Notes |
|------------------|-------|-------|
| Product operation | `product_templates.operations_json` (+ children) | Formula ids, workcenters |
| Commercial line | CPP 7G + `commercial_rules_volumetric_v2` | Money |
| Internal cost step | EIC / internal_cost_rules | Not commercial authority |
| Machine capability | Workcenters / inventory rates | Pricing Registry view |
| Execution task | ExecutionPlan materialization | Consumes frozen/plan inputs |
| Planning minutes | Aggregate + planning_duration_contract | TE2E-028A/B — not price |

**Duplicate risk:** same conceptual op can appear in template JSON, CostEngine, commercial rules, and task catalogs with different codes.

---

## 9. Settings taxonomy (samples)

| Setting | Category | Current owner | Storage | Editable by | Consumer | Should move? |
|---------|----------|---------------|---------|-------------|----------|--------------|
| VAT % | Company | Company commercial settings | DB singleton | Admin Settings | Dry-run / offer | Stay company |
| Markup/discount | Workspace commercial | Intake finish_setup.commercial_inputs | Workspace | Operator | Dry-run | Stay workspace (override) |
| Material rates | Commercial / company | Pricing Registry → inventory/workcenter | DB materials/rates | Inventory/Pricing admin | CPP | Stay pricing/inventory |
| Face finish options | Product/options | **Split** contract options + FE maps | Code/FE | Devs | Intake | **Unify under PS/company option registry** |
| Return depth options | Product | API/contract + FE | Mixed | Devs | Intake | Unify |
| Lighting system type | Module/product | Contract pilot + FE hide | Contract + FE | Devs | Intake/PD | PS module setting |
| Default lighting_system_type=led_modules | Template/FE default | FE ReviewStep | Frontend | Devs | Hydration | Template/module default |
| mounting_template_enabled | Workspace | Operator | Workspace | Operator | PD/Aggregate | Stay workspace |
| Active template scope | Platform/product policy | seed_active_template_scope | Policy+DB active flags | Owner/seed | Availability | Owner gate |
| Quote snapshot totals | Snapshot | Quotes | Snapshot tables | Freeze path only | Execution | Never live-edit |

---

## 10. Defaults and overrides (observed)

**Proven precedence fragments (not a single global ladder):**

```text
Company VAT  →  forces dry-run VAT (workspace VAT not authority)
Active-scope seed  →  overrides template.active for offerability
Module link defaults  →  can supply child inputs when triggered
Workspace finish_setup  →  concrete operator values for PD
PD compile  →  activation truth (not FE visibility)
Aggregate  →  derived quantities / measurements
CPP  →  money from measurements + registry (workspace path fallback explicit)
Snapshots  →  freeze; ignore later PS mutation
```

**Not proven as a clean chain:** PLATFORM → COMPANY → FAMILY → TEMPLATE → COMPONENT/MODULE → WORKSPACE → DERIVED.  
Family layer does **not** currently supply defaults.

| Value | Default source | Override | Runtime precedence | Versioned | Risk |
|-------|----------------|----------|--------------------|-----------|------|
| vat_percent | Company | (ignored from workspace for authority) | Company wins | Company row | OK |
| lighting_system_type | FE default led_modules | Workspace | Workspace after hydrate | No | FE product default |
| Module optional metal | Link trigger | Workspace mounting fields | PD activation | Link row | Trigger mismatch risk |
| Commercial qty | Aggregate measurement | Workspace path fallback | Aggregate then fallback | No | Explicit COMPAT fallback |

---

## 11. Option ownership

| Domain | Canonical candidate | Duplicate source | Runtime reachable | Risk |
|--------|---------------------|------------------|-------------------|------|
| Finish/backing options | Modular form `options` (pilot) | `INTAKE_V6_BACKING_MODE_OPTIONS`, letter group FE | Yes both | Dual authority |
| Lighting options | Form contract select options | LightingSection local | Yes | Dual |
| Materials | Inventory materials | Template required_materials_json | Yes | Sync drift |
| Color (RAL/Oracal) | FE colorRegistry | Not auto Pricing | FE display | Must not price |

---

## 12. Module activation ownership

| Module | Allowed by | Activated by | Final authority | Frontend role |
|--------|------------|--------------|-----------------|---------------|
| modelare_cant | Letters template + required link | Link / always required | PD/Aggregate | Show return fields |
| structura_suport | optional link | metal_support / ACM triggers | PD composition | Mounting UI (still FE) |
| sistem_led | lighting_gate rule | lighting_system_type / illuminated | PD | Visibility ≠ activation |
| finisaje sablon | mounting_template_enabled | Workspace boolean | PD/Aggregate | Contract field pilot |
| geometry_svg | always_on | SVG present | PD readiness | Analyzer UI |

**Rule (target = current PD claim):** Frontend visibility ≠ module activation.  
**Current:** mostly true on backend; FE still gates large UI surfaces independently.

---

## 13. Intake contract ownership (pilot vs rest)

| Concern | Product semantics (should be PS) | UI interaction (FE OK) | Persistence (Intake) | Final validation |
|---------|----------------------------------|------------------------|----------------------|------------------|
| Sections / order | Pilot `render_sections` | Layout chrome | — | — |
| Field membership | Pilot field_keys | Specialized groups | — | — |
| Labels/types/options/required | Pilot bindings | Remaining FE maps | — | PD |
| Visibility | Structured rules pilot | Sold-scope FE | — | PD |
| Workspace path | Bindings allowlist | — | updateForm/finish-setup | PD |
| Capability type | Missing as type | Specialized React | — | — |
| Save logic | — | — | Intake APIs | — |

**Lighting / finishing / mounting as Intake-level concepts:** risk **CONFIRMED** — FE section names and helpers are Letters-shaped; pilot begins moving metadata to PS but specialized UI remains.

---

## 14. Multi-product model proof (conceptual)

### Volumetric letters (ACTIVE)

```text
Family: litere_volumetrice
Template: TPL-VOLUMETRIC-LETTERS_v2
Components: face, return(child), back, LED, finish (dossier/BOM)
Modules: geometry_svg, debitare_*, modelare_cant, sistem_led, finisaje, structura_suport
Capabilities (UI): analyzer viewer, layered finishes, lighting editor, mounting editor
```

### Banner (PARTIAL / archived active-scope)

```text
Family: print_large_format or textile_banner
Template: TPL-BANNER-STANDARD (Build4)
Components: substrate print, finishing (hem/eyelets)
Modules needed: dimensions, print, hemming, eyelets, delivery — NOT in mini-module registry
Must NOT reuse: sistem_led, modelare_cant, letter face
```

### Vehicle graphics (MISSING template)

```text
Family: colantari_auto (exists)
Template: none
Needed modules: vehicle identity, zones, vinyl, lamination, prep, install
Must NOT reuse: letter return, LED letter install as-is
```

**Conclusion:** Target composition model can represent all three **only if** mini-modules/capabilities are not Letters-hardcoded and Component Templates become real reusable units. **Current code cannot** without false-generic reuse.

---

## 15. Reuse boundaries

| Likely cross-family | Likely family-specific | Likely product-specific |
|---------------------|------------------------|-------------------------|
| File upload, dims, delivery, notes, material selector capability type | Lighting system, banner finishing, vehicle zones | Letter return, totem base, lightbox face |
| Company VAT, inventory materials | Shared volumetric child templates (Al, metal) within signage | Letters dossier IDs |

**False-generic modules:** `finisaje`, `sistem_led`, `geometry_svg` — generic names, Letters-only `applies_to`.

---

## 16. Duplicate model register

| Domain | Canonical candidate | Duplicate source | Runtime reachable | Risk |
|--------|---------------------|------------------|-------------------|------|
| Product templates | `product_templates` | Build4 + Letters seeds + inactive component-first | Yes | Scope seed archives many |
| Components | Parent BOM + dossier | Policy FACE_v1 codes without rows; TPL-COMP-* inactive | Partial | Ghost components |
| Modules | Mini-module registry + module_links | FE section = “module” mentally | Yes | Conflation |
| Options | Form contract options | FE option constants | Yes | Dual authority |
| Operations | Template ops JSON | CE / commercial rules / EIC | Yes | Code drift |
| Pricing keys | Pricing Registry + commercial rules | Workspace path fallback in CPP | Yes | Explicit fallback |
| Validation | PD | FE required + contract required | Yes | UX vs truth |
| Families | product_families | Template family_id denorm / intake legacy labels | Yes | Orphans |

---

## 17. Versioning

| Entity | Versioned today? | Mutable current? | Snapshots | Old job safety |
|--------|------------------|------------------|-----------|----------------|
| Family | No | Yes | No | Low impact |
| Product Template | Code suffix | Yes (active flag/JSON) | Code in snapshots | **Unsafe** if JSON mutates without new code |
| Component Template | N/A | — | — | — |
| Mini-Module | module_version string | Code deploy | Not frozen per job | Deploy can change meaning |
| Intake Contract | contract_version string | Code | Not in quote | OK for labels; risky for paths |
| ProductDefinition | preview version constants | Ephemeral compile | Embedded in flows | Recompute risk |
| ProductAggregate | resolve-time | Ephemeral | Measurements may re-derive | |
| Pricing Registry | Rates mutable | Yes | Quote freeze protects accepted | Pre-accept live |
| Operations/Tasks | Mixed | Yes | Plan freeze | Plan/Post-Job protected if frozen |

**Unsafe shared mutable references:** live `product_templates` JSON and mini-module code for open workspaces; accepted quotes/orders protected by snapshots.

---

## 18. Product System settings UI

| Surface | State |
|---------|-------|
| `/product-system` catalog | Read/edit templates (JSON) — **editable** products admin |
| Families API | CRUD exists; UI completeness varies |
| Mini-modules API | **Read-only** contract GET |
| Form contract GET | Read-only |
| Component-first UI | Read-only completeness / candidates |
| Formula/ops editors | Partial via template JSON fields — not a clean settings model |
| Pricing links | Pricing/Inventory pages — not PS composer |
| Intake contracts admin | **Missing** as owner UI |

---

## 19. Modules / Governance accuracy

`/modules` + `/governance` (Control Center) show spine:

```text
Product System → Intake → PD → Aggregate → CPP → Snapshots → Execution → Post-Job
```

**Accurate:** money at CPP; PD compiler; Aggregate technical; Intake capture; Letters pilot scoped.  
**Collapsed / missing:** Product Family, Component Template, Mini-Module, Capability as distinct nodes — folded into “Catalog produse”.  
**Overstatement risk:** “contract formular” sounds broader than Letters pilot — mitigated by limitation strings after renderer pilot.

**This audit does not update Control Center.**

---

## 20. Current architecture diagram (runtime truth)

```text
[product_families DB] ----grouping----> [product_templates DB]
        |                                    | components_json (BOM parts)
        |                                    | operations_json / materials_json
        |                                    v
        |                         [product_template_module_links]
        |                                    | child TPL rows (Al, metal, ACM)
        v                                    v
   Intake family string          [mini_module_registry CODE — Letters only]
                                             | dossier_component_id / child codes
                                             v
                              [modular form contract + backbone]
                                             |
                    +------------------------+------------------------+
                    v                                                 v
        [Intake V6 FE — specialized UI]                    [generic contract renderer pilot]
                    |                                                 |
                    +------------------ workspace finish_setup -------+
                                             v
                                   [ProductDefinition compile]
                                             v
                                   [ProductAggregate resolve]
                                      |                |
                          commercial_measurements   planning minutes
                                      v                v
                                 [CPP 7G money]   [ExecutionPlan]
                                      v                v
                              [Quote/Order Snapshot] [Execution Reality]
```

**Duplicates:** FE option maps ‖ contract options; FACE_v1 policy ‖ dossier face; CE ‖ CPP ‖ EIC catalogs; family seed ‖ template family_id drift.

---

## 21. Target ownership diagram (recommended)

```text
Product Family (grouping + shared family policies — optional)
  └── Product Template (root composer, versioned)
        ├── Component Templates (reusable physical/technical units)
        ├── Mini-Modules (reusable functional packages; not UI)
        ├── Intake Composition Contract (sections/fields/types/options/visibility)
        ├── Capability types (UI interaction kinds — no React names)
        ├── Operation Contracts
        └── Commercial Measurement Contracts (non-money)

Company Settings
  ├── materials / machines / option registries
  └── pricing registry links + VAT/FX

Workspace → concrete selected values
ProductDefinition → validated compiled configuration (activation authority)
ProductAggregate → resolved technical truth + measurements + minutes
Pricing Registry + CPP → money only
Execution → plan + actuals (no upstream rewrite)
```

---

## 22. Contradiction register

| ID | Contradiction | Runtime authority | Owner gate |
|----|---------------|-------------------|------------|
| C1 | Component Template docs vs no table | BOM + child TPL + dossier | Define Component Template entity or rename |
| C2 | Mini-module generic names vs Letters-only | Registry applies_to | Forbid cross-family reuse until multi-template registry |
| C3 | FE options vs contract options | Both reachable | Single option authority |
| C4 | FE visibility vs PD activation | PD for truth | Keep FE presentation-only |
| C5 | Family missing for child template family_ids | Denorm strings | Align family registry |
| C6 | Triple “active” definition | Policy + scope seed + runtime allow-list | One offerability matrix |
| C7 | Capability = catalog label vs UI ability | FE overloaded word | Split vocabulary |
| C8 | Template JSON mutable vs old open jobs | Live DB | Version pin or snapshot template refs |

---

## 23. Recommended canonical model

Adopt the target diagram in §21 with these **deviations forced by current code**:

1. Keep `product_templates` as persistence for both roots and linked modules **until** Component Template table exists — but **stop calling** linked children “Component Templates” in UI without qualification.  
2. Keep mini-modules code-backed for Letters until a multi-template registry exists — mark **NOT CROSS-FAMILY**.  
3. Capability types introduced as **string enums** in contracts before any React mapping table expansion.  
4. Do **not** put lighting/finishing/mounting into Intake infrastructure — only into product/module contracts.

---

## 24. Build options

### Option A — Canonical concept model first (RECOMMENDED)

- **Solves:** vocabulary + ownership gates before more renderer work  
- **Scope:** docs + Control Center truth + owner decisions; optional non-runtime type aliases  
- **Systems:** Product System docs, Modules/Governance labels  
- **Migration risk:** none if docs-only  
- **UI impact:** terminology only  
- **Runtime risk:** none  
- **Owner gates:** approve dictionary + STOP expansion  
- **Value:** prevents building correct code on wrong model  

### Option B — Product template composer contract

- **Solves:** explicit compose graph template→components→modules→intake→ops  
- **Scope:** contract schemas + read models  
- **Risk:** medium if mistaken for Component Template table  
- **UI:** Product System composer read-only  

### Option C — Settings ownership layer

- **Solves:** company vs template vs workspace option/default split  
- **Scope:** settings taxonomy implementation  
- **Risk:** schema pressure for option registries  
- **Owner gates:** schema GO if DB catalogs needed  

**Recommend: Option A only** until owner pack signed.

---

## 25. Owner decision pack — APPROVED 2026-07-17

| Decision | Approved value |
|----------|----------------|
| PRODUCT FAMILY | **FIRST-CLASS GROUPING** |
| PRODUCT TEMPLATE | **ROOT COMPOSER** |
| COMPONENT TEMPLATE | **PHYSICAL REUSABLE PART — CONCEPT NORMALIZATION REQUIRED** |
| MINI-MODULE | **OPERATIONAL PACKAGE WITH EXPLICIT SCOPE** |
| CAPABILITY | **UI INTERACTION TYPE** |
| MODULE ACTIVATION | **PRODUCT DEFINITION** |
| COMMERCIAL MEASUREMENT | **PRODUCT AGGREGATE** |
| MONEY | **CPP 7G** |
| MODULARITY MODEL | **REWORK** |
| AUDIT COMMIT | **YES** |
| IMPLEMENTATION | **GO — CONCEPT AND NAVIGATION NORMALIZATION ONLY** |

**Stabilization scope only:** Litere volumetrice · Logo · Panouri ACM (and their real components).  
**Do not invent/activate:** banner, vehicle graphics, new families, new products.

---

## 26. Paused product expansion (still enforce)

Still forbidden without separate owner GO:

- generic renderer expansion / more Letters fields  
- new templates / families  
- Pricing Registry 7I  
- Stock G3 / labor-money / task lifecycle  
- component_templates table / schema migration  
- Product System global form-generation claims  

Allowed next: concept dictionary, navigation truth, one Dossier, Inventory/Pricing links, Control Center vocabulary.

---

## 27. Evidence index (primary)

- `backend/models/product_families.py`, `product_templates.py`, `product_template_module_links.py`  
- `backend/seeds/seed_product_families.py`, `seed_tpl_volumetric_letters_v2.py`, `seed_build4_templates.py`, `seed_active_template_scope.py`  
- `backend/data/mini_module_registry_volumetric_v2.py`  
- `backend/services/intake_v6_modular_form_contract_service.py`, `product_definition_builder_service.py`, `letters_commercial_measurement_service.py`  
- `frontend/src/features/product-system/productSystemCanonicalCatalogModel.ts`  
- `frontend/src/lib/currentTruthControlCenter.ts`  
- Architecture direction (docs-only): `PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`  
- Runtime probes: families=14; mini-modules Letters=8; availability Letters/Logo/ACM/metal set  

---

## 28. Commit status

```text
AUDIT COMMIT AUTHORIZED — docs only (exact paths)
```

# Audit — Historical Product System UI / Blueprint reuse potential

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_AUDIT_HISTORICAL_PRODUCT_SYSTEM_BLUEPRINT_UI` |
| Mode | **AUDIT ONLY** — no app edits, no commit |
| HEAD | `f741006` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Git range | `c2bf9e1` / `1f9fda1` (clean import baseline) → HEAD (~566 commits on branch) |
| Runtime | FE `:3000` up; BE `:8001` **STALE** (unrelated to this audit) |

---

## Verdict

**BLUEPRINT_EXISTED_AS_DOSSIER_ADMIN_SURFACE_NOT_AS_LOST_CANVAS**

There was never a deleted React Flow / XYFlow visual “Product Blueprint builder” in this repository. What the owner likely remembers as a clearer Blueprint zone maps to:

1. **Blueprint Dossier Studio** (`/product-system/blueprint-dossier`) — still live, real CRUD.
2. **Product System IA shell** (commit `3be9c72`) with primary tabs Products / Components / Candidate Sets / **Dossiers** / Guards / Archived — later replaced by unified/canonical catalog (`0eb5088`, `8d98067`, `5c6b4e4`).
3. Docs-only “blueprint” contracts (`0416248`) — design, not UI.
4. Operator / Employee Mobile “production blueprint” — different domain.

**Single recommendation:** Option 2 — reuse Blueprint / IA visual and organization patterns inside current Product System UI over current contracts. Do not restore a parallel task engine.

---

## 1. Baseline & dirty-tree protection

| Check | Result |
|-------|--------|
| HEAD | `f741006` (matches latest reported) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Dirty tree | Yes — unrelated WIP left untouched |
| App edits this GO | **None** |
| Commits this GO | **None** |
| Methods | `git log`, `git show`, `git grep`, workspace Grep/Read only |

---

## 2. Search scope

Case-insensitive terms: Blueprint, Product Blueprint, ProductSystemBlueprint, product-system, Product Builder, Template Builder, Dossier, Process Graph, Task Graph, React Flow, XYFlow, Canvas, Formula, Workflow, Resource Options, Romanian: schiță / structură / configurație produs / finisaje / taskuri / procese / rețetă.

Surfaces: current frontend, git full history, docs/qa screenshots, worklogs, plans, APIs, models.

---

## 3. Historical UI inventory

| UI / Route | Commit / era | Status | Functional or mock | Real data | Authority | Reusable |
|------------|--------------|--------|--------------------|-----------|-----------|----------|
| `/product-system/products` | baseline → HEAD | Active | Functional | Templates API | Product System catalog/editor | REUSE_AS_IS |
| `/product-system/products/:code` | deep-link era | Active | Functional | Same | Same | REUSE_AS_IS |
| `/product-system/blueprint-dossier` | baseline (`c2bf9e1`) → HEAD | Active | **Functional CRUD** | `product_blueprint_dossiers` | Dossier documentation / contracts | REUSE_AS_IS (admin surface) |
| `/product-system/dossier-completion` | baseline → `451e90a` redirect | Redirect only | Was functional; now redirect | Was dossier readiness UI | Superseded by canonical dossier | DO_NOT_REUSE (second readiness UI) |
| IA shell tabs (Dossiers etc.) | `3be9c72` → removed `0eb5088` | Superseded in code | Functional UI of that era | Readonly contracts + catalog | Navigation IA | VISUAL_PATTERN_ONLY |
| Unified catalog | `0eb5088` | Superseded by canonical | Functional | Same | Catalog honesty | CONCEPT_ONLY / partial reuse |
| Canonical shell + planned sections | `5c6b4e4` | Active | Products functional; Components/Resources/Operations/Dependencies/Validation/Advanced = **planned stubs** | N/A for stubs | Shell labels “Planificat” | Planned sections = CONCEPT_ONLY |
| `/product-system/output-blocks-preview` | baseline→ | Active | Read-only preview | Output blocks | Preview | REUSE_WITH_ADAPTER |
| Docs letters template-set blueprint | `0416248` | Docs only | Mock / design | None | Design contract | CONCEPT_ONLY |
| Operator production blueprint | separate | Active | Functional | Order/tasks | Execution domain | DO_NOT_REUSE into PS admin |
| Employee Mobile order blueprint | separate | Active | Functional | Order | Mobile domain | DO_NOT_REUSE |
| React Flow canvas Blueprint | — | **Never existed** | — | — | — | DEAD (not in history) |

Root components:

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/BlueprintDossierStudio.tsx`
- `frontend/src/pages/DossierCompletionDashboard.tsx` (orphan file; route redirected)
- `frontend/src/features/product-system/*`
- `frontend/src/components/dossier/DossierSectionEditors.tsx`

---

## 4. Blueprint audit — 20 answers

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | Real route? | **Yes** | `App.tsx` → `/product-system/blueprint-dossier` → `BlueprintDossierStudio` |
| 2 | Tab? | **Mixed naming.** Studio is a route; IA shell had a **Dossiers** tab (`3be9c72`); Product System sometimes labeled “Blueprint Studio” in links | Screenshots `07_dossiers_tab.png`; studio header links |
| 3 | Design/mock only? | **No** for Studio. **Yes** for docs `0416248` | Studio save path; worklog “No frontend change” |
| 4 | Real data? | **Yes** | `frontend/src/api/blueprintDossier.ts` → `/api/v1/entities/product-blueprint-dossiers` |
| 5 | Saves? | **Yes** | `handleSave` → `blueprintDossierApi.update` |
| 6 | Entities? | Variants, layers, task_rules, time, costengine_mapping, quote_readiness, QC, risks, production notes, output/visual blocks, completion | `BlueprintDossierEntity` fields |
| 7 | Component graph? | **No canvas** | No ReactFlow in repo; structure in ProductSystem editor |
| 8 | Process graph? | **No** in Blueprint UI | Process DAG = backend/resolver / Aggregate later |
| 9 | Task graph? | **No** — documentation list only | `TaskRulesEditor`: “nu creează task-uri” |
| 10 | Finishes? | **Not first-class in dossier** | No finish_* section; finishes in ProductSystem / Intake / components |
| 11 | Material / RO? | Not dossier core; planned shell “Resources” stub | `productSystemShellConfig.ts` |
| 12 | Formulas? | Mapping audit only; not formula authority | `costengine_mapping_json` description |
| 13 | Variants? | **Yes** | `variants_json` + VariantsEditor |
| 14 | Validation/readiness? | Local + `getProductReadiness` | Studio loads readiness |
| 15 | Versioning? | **Yes** | `dossier_version`; approve increments |
| 16 | Active/inactive? | Active/archived template list tabs | Studio `listTab` |
| 17 | Drag-and-drop? | **No** | No DnD in studio |
| 18 | Ordering? | Fixed section groups; list add/remove | `DOSSIER_SECTION_GROUPS` |
| 19 | Duplicate authority? | **Yes if misused** — dossier ≠ Aggregate BOM / task runtime | Studio group authority banners; Aggregate “metadata only” warnings |
| 20 | Eliminated? | **Not eliminated.** Completion page demoted (`451e90a`); IA Dossiers tab removed (`0eb5088`); Studio remains | |

---

## 5. Comparison with canonical model

| Concept | Old / Blueprint UI | Current system | Compatible | Conflict |
|---------|-------------------|----------------|------------|----------|
| Product Template | ProductSystem editor | Product System | Yes | Low |
| Component Template | Structure + component-first readonly | Contracts + composition | Partial | Field ownership still mixed |
| Interface / Role | Sparse in dossier | Growing RO / lifecycle | Partial | Shell sections planned only |
| Resource Option | Not in dossier | Structural RO registry (new) | Via ProductSystem | Don’t put RO only in dossier |
| Formula | CostEngine mapping docs | CPP gated | Docs only OK | Don’t run CostEngine from dossier |
| Material | Layers narrative | Components / inventory keys | Weak in dossier | Parallel if treated as SoT |
| Finish | Not in dossier | Component + Intake | Current better for letters | Dossier cannot express ACP mixed faces |
| Operation | Template operational tab | Template + registries | Yes | Planned Operations stub empty |
| Process dependency | Text / later resolver | Modular process → Aggregate | Prefer current | Don’t revive dossier as DAG editor |
| Task rule | Dossier `task_rules_json` guidance | Aggregate / modular resolver → existing tasking | Guidance OK | **Dangerous if dossier = runtime** |
| Lifecycle | Studio status | Template lifecycle control | Prefer current | — |
| Version | `dossier_version` | Template + dossier | Yes | — |
| Variant | `variants_json` | Dossier + Intake options | Yes | Keep docs-only |
| Inactive isolation | Active/archived lists | Stronger activation scope today | Prefer current | — |

---

## 6. Finishes

| Question | Finding |
|----------|---------|
| Product-level? | Template quote options / ProductSystem workshops |
| Component-level? | Component-first readonly maps (`volumetric_surface_finish`, return cant finish) |
| Role / RO? | Emerging in structural RO — not Blueprint Dossier |
| Simple strings vs registry? | Mixed — Oracal/RAL paths still split across Intake + components |
| Reusable model? | **Partial** — component-first finish ownership maps are CONCEPT_ONLY / REUSE_WITH_ADAPTER; dossier has no finish editor |
| UI without authority? | Yes for some ProductSystem “shouldOwn” warnings |
| ACP stock / Oracal / RAL / cut face / plexi / multi-treatment? | **Not organized in Blueprint Dossier.** Partial ACP face type in ProductSystem SVG mock (`FATA_ACP_ROUTATA`); mixed-face ACP truth is **current gap**, not a lost Blueprint feature |

---

## 7. Tasks & operations classification

| Mechanism | Class |
|-----------|--------|
| Dossier `task_rules_json` editor | **configurator de reguli documentare** — not runtime |
| Aggregate compiled `task_rules` from modular resolver | **canonic** (letters path) |
| Existing mature tasking / Execution | **canonic operational** |
| Operator production blueprint | **separate domain** — DO_NOT_REUSE as PS admin |
| Planned Operations shell page | **mock / planned stub** |
| Imaginary Blueprint task scheduler | **dead / never existed** |

**Firm rule preserved:** do not reactivate a parallel task model. Desired path remains contracts → process DAG → Aggregate task_rules → existing tasking.

---

## 8. UX — old vs current (honest)

| Dimension | Clearer in IA shell / Dossier groups | Stronger in current UI |
|-----------|--------------------------------------|-------------------------|
| Hierarchy / overview | Multi-tab IA (`3be9c72`) + dossier section groups | Canonical honesty / fewer fake entry points |
| Density | Dossier groups readable | Catalog denser, sometimes flatter |
| Editability | Studio section editors | Template structure/operational/form-system tabs |
| Readiness | Split across completion dashboard + studio (confusing) | Canonical dossier route + lifecycle services |
| Scaling complex products | Tab separation helped mental model | Planned shell sections advertise future map but are empty |
| Nostalgia trap | IA felt “Blueprint-like” | Current lifecycle/contracts are more mature |

---

## 9. ACP conceptual use case vs old Blueprint

```text
Panou ACP casetat
├── Carcasa ACP
├── Cadru interior optional
├── Sistem de prindere
├── Zone fațadă A/B/C (mixed treatments)
```

| Need | Could old Blueprint Studio organize it? |
|------|----------------------------------------|
| Component | Only narratively (layers/sections) — not composition SoT |
| Role / RO | No |
| Material | Narrative layers only |
| Finish per face zone | **No** |
| Process / task rule | Docs task_rules only |
| Dependency | No graph |
| Active/inactive | Template archive only |
| Readiness | Dossier status, not ACP product truth |

**Result:** Old Blueprint would **not** organize ACP mixed-face product truth better than current Product System + Intake + structural RO path. Recover **organization patterns** (tabs/groups), not dossier-as-product-model.

---

## 10. Blueprint as surface, not new authority

Evaluated and **supported**:

```text
Blueprint / Dossier UI  = administration + visualization surface
Product System contracts = technical authority
ProductAggregate         = compilation
Existing tasking         = operational materialization
```

Studio already declares production group as guidance only. Safe reuse = keep that separation; improve discoverability and IA clarity.

---

## 11. Reusable components

| Component | Commit lineage | Role | Recommendation |
|-----------|----------------|------|----------------|
| `BlueprintDossierStudio` + groups | baseline→HEAD | Dossier admin | REUSE_AS_IS |
| `DossierSectionEditors` / TaskRulesEditor | baseline | Docs editors | REUSE_WITH_ADAPTER |
| Dossier validation / status UI | baseline | Lifecycle UX | REUSE_AS_IS |
| IA shell tab pattern | `3be9c72` | Navigation clarity | VISUAL_PATTERN_ONLY |
| Template studio tabs (structure/ops/form) | ProductSystem | Product edit | REUSE_AS_IS |
| `DossierCompletionDashboard` | orphaned | Second readiness | DO_NOT_REUSE |
| Operator/Employee blueprint panels | separate | Execution | DO_NOT_REUSE |
| React Flow canvas | n/a | — | DEAD |
| Docs `0416248` set | docs | Design | CONCEPT_ONLY |

---

## 12. API map

| Endpoint / artifact | Class |
|---------------------|--------|
| `/api/v1/entities/product-blueprint-dossiers` CRUD | **active** |
| `product_blueprint_dossier` table | **active** |
| `product_blueprint_dossier_service` | **active** |
| Dossier `task_rules` as production SoT | **legacy / dangerous if reactivated** |
| Operator production blueprint APIs | **active** (other domain) |
| React Flow / visual builder API | **never existed** |

---

## 13. Why the clearer UI “disappeared”

Evidence only:

1. IA multi-tab shell (`3be9c72`) replaced by unified catalog (`0eb5088`) then canonical shell — **organization flattened**.
2. Completion dashboard redirected to single dossier route (`451e90a`) — fewer entry points.
3. Blueprint Dossier Studio **still exists** but is less discoverable (overflow / deep link).
4. Naming overload: Blueprint Studio vs Blueprint Dossier vs docs blueprint vs operator blueprint.
5. **No** evidence of a deleted graph builder.

---

## 14. Screenshots inventory (high-signal)

| Path | Era | Shows |
|------|-----|-------|
| `docs/qa/product-system-ia-shell-2026-07-09/screenshots/07_dossiers_tab.png` | `3be9c72` | Dossiers tab |
| `docs/qa/product-system-ia-shell-2026-07-09/screenshots/01_top_summary_and_primary_tabs.png` | same | Full IA tabs |
| `docs/qa/product-system-unified-catalog-2026-07-09/screenshots/07_candidate_detail_dossier.png` | `0eb5088` | Dossier in unified detail |
| `docs/qa/product-system-catalog-page-chrome-slim-2026-07-09/screenshots/04_library_more_menu_blueprint.png` | chrome slim | Library → Blueprint Dossier |
| `docs/qa/figma-product-system-component-first-audit-2026-07-09/screenshots/04_dossier_tab.png` | component-first | Dossier tab |
| `docs/qa/product-system-active-path-isolation-v1/w6_t02_04_operator_blueprint_mounting.png` | later | Operator blueprint (not PS admin) |

Historical routes still runnable without code changes: `/product-system/products`, `/product-system/blueprint-dossier` (read-only browse OK).

---

## 15. Dead pieces check

| Item | Status |
|------|--------|
| Imaginary React Flow Blueprint | DEAD — never in git |
| Second dossier completion UI as parallel readiness | DEAD for routing |
| Dossier task_rules as scheduler | Unsafe if reactivated |
| Planned shell sections empty | Stub — don’t fake operational |
| Docs-only letters blueprint set | Concept only |

---

## 16. Recommendation

**Option 2 — REUSE BLUEPRINT VISUAL PATTERNS INSIDE CURRENT PRODUCT SYSTEM UI**

See `docs/plans/PRODUCT_SYSTEM_BLUEPRINT_REUSE_RECOMMENDATION.md`.

---

## 17. Acceptance

| Criterion | Met |
|-----------|-----|
| Git history searched | Yes |
| Blueprint located or absence proven | Located as Dossier Studio; canvas absence proven |
| Routes/components inventoried | Yes |
| Functional vs mock | Yes |
| Finishes / tasks clear | Yes |
| Duplicate authority clear | Yes |
| ACP use case evaluated | Yes |
| No app edits / no commit | Yes |
| Single recommendation | Option 2 |

**Cat sunt in directia stabilita: 92/100%** (audit complete; owner UI review next).

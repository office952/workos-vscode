# Wave 4 report — Product System / Modules / Governance

| Field | Value |
|-------|--------|
| Date | 2026-08-14 |
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM_V1` |
| Wave | `WAVE_4_PRODUCT_SYSTEM_MODULES_GOVERNANCE_AUDIT_V1` |
| Authorization | READ-ONLY AUDIT / RUNTIME / DOCS / SCREENSHOTS |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Baseline HEAD | `2af20f4ed0d797e33572fb17a18c39fea5d2d638` |
| Remote parity | LOCAL=REMOTE, AHEAD=0, BEHIND=0 |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Owner DB / Product Truth / PD / PA / pricing / quote / order / execution mutations | 0 |
| Frontend | `http://127.0.0.1:3000` (reused live stack) |
| Backend | `http://127.0.0.1:8000` (healthy) |
| Next task | **NOT_AUTHORIZED** |

## Verdict

**PASS — Wave 4 closed after targeted gap closure.**  
See `WAVE_4_GAP_CLOSURE_REPORT.md`. Initial audit remains `PASS_WITH_GAPS` evidence; it was **not** re-run.

Architectural answer (unchanged, now evidence-complete):

Product System = design-time language · ProductDefinition = compiler preview / no page · ProductAggregate = workspace-bound graph · Intake V6 + frozen Order = sold-work · Frozen graph + ExecutionPlan = execution · Atelier/operator/tablet = projections.

Product System / ProductDefinition / ProductAggregate are a **compiler spine**, not the commercial or shop-floor backbone.

- Wave 2 sold work is owned by **Intake V6 workspace + order snapshot**, not by `/product-system`.
- Wave 3 executed work is owned by **frozen order graph + ExecutionPlan**, then projected (and often hidden) by Atelier / operator / tablet.
- Product System owns **design-time language** (what *can* exist). ProductDefinition **previews** a compile. ProductAggregate **composes** a graph when a workspace is bound.

Complexity seen in Intake and Execution is therefore **both** local ownership (V6 job truth, unbounded operator list) **and** unclear upstream homes (no ProductDefinition page, FLUX Produse, dual governance catalogs, planned/unwired Product System shells).

No page FINAL. No Wave 5. No implementation. No commit. No push.

## Scope

| Item | Value |
|------|--------|
| Primary routes | `/product-system/products`, Letters v2, ACM boxed, planned `components`/`operations`, `/product-system/blueprint-dossier`, `/product-system/output-blocks-preview`, `/modules`, `/governance` |
| Classified audit/dev | blueprint-dossier, output-blocks-preview, planned sections |
| Not treated as operator pages | CatalogShell / TemplateLibraryView (unwired), composer IA mock (not drilled) |
| Excluded | create/activate/save, Product Truth mutation, Wave 5 |
| RT | initial 21/109 + gap-closure 27/87; scroll FAIL=0 |

## Orchestration

| Role | Writer | Status |
|------|--------|--------|
| D | `lane-d-product-system-gov/PAGE_CARDS.md` | PASS — page cards |
| F | `lane-f-ui-system/OBSERVATIONS.md` | PASS — observer only |
| G | `lane-g-legacy-dead/CLASSIFICATION.md` | PASS — observer only |
| H | `lane-h-nav-journeys/EDGES.md` | PASS — observer only |
| A | `lane-a-commercial-observer/OBSERVATIONS.md` | PASS — observer only, no cards |
| B | `lane-b-execution-observer/OBSERVATIONS.md` | PASS — observer only, no cards |
| RT | `runtime/rt-capture-log.json` + `runtime/rt-gap-closure-log.json` | PASS — 109 + 87 shots, 0 scroll fail, 0 mutations |
| ORCH | this file + gap-closure report | PASS |
| REV | `review/WAVE_4_CONSISTENCY_REVIEW.md` | **PASS** |

## Answer to the Owner question

**Do upstream product/system definitions explain the commercial and execution reality already observed?**

**Partially.** They explain *plan-level grain* for Letters (`TPL-VOLUMETRIC-LETTERS_v2` + child `TPL-VOLUM-ALUMINIU_v1` on execution 973024). They do **not** define what V6 sold, what the operator list shows, or what Atelier currently highlights.

| Layer | What it actually does |
|-------|------------------------|
| Product System | Catalog of templates / modules. Live roots: Letters v2, ACM boxed. Planned tabs and unwired CatalogShell over-model the UI. |
| ProductDefinition | Compiler **preview**. No persist. No dedicated page. `/modules` sends “verify” to `/intake-v6`. |
| ProductAggregate | Workspace compose can be a coherent graph + measurements + `task_contract`. Template-only `build()` is PASS_THROUGH of the catalog. |
| Intake V6 | Owns job/runtime product truth and preview money. |
| Order snapshot | Owns sold / frozen scope. |
| Execution UI | Does not project Product System grain; live Atelier card is a different order. |

## Classifications

| Axis | Class |
|------|--------|
| PRODUCT_SYSTEM_MODEL | **PARTIAL** (live spine real; planned/unwired shells OVERMODELED) |
| PRODUCT_DEFINITION_OWNERSHIP | **PARTIAL** |
| PRODUCT_AGGREGATE_OWNERSHIP | **PARTIAL** (`PARTIAL_AGGREGATE`) |
| MODULARITY_MODEL | **PARTIAL** |
| ACTIVE_SOLD_EXECUTION_SCOPE | **PARTIAL** |
| MODULES_PAGE_ACCURACY | **PARTIAL** |
| GOVERNANCE_PAGE_ACCURACY | **PARTIAL** |
| MODULES_GOVERNANCE_CONSISTENCY | **PARTIAL** |
| PRODUCT_SYSTEM_UI_HONESTY | **PARTIAL** / TECHNICAL |
| LOGO_LINKED_CHILD_STATE | **PARTIAL_LINKED_CHILD** (root BLOCKED) |
| ACM_ACP_MODEL_STATE | **PARTIAL** (boxed ACTIVE; casetat FUTURE; ACP ARCHIVED) |
| CROSS_WAVE_2_3_4_MODEL | **PARTIAL** |

## Runtime

| Metric | Value |
|--------|--------|
| Surfaces captured | 21 |
| Screenshots | 109 |
| Scroll container | `main.overflow-auto` |
| Nested | `workos-shell-nav max=624` |
| FULL_SCROLL_FAILURES | 0 |
| Role MATCH | YES (admin allowed; sales/manager modules/gov denied; operator products denied) |
| Light/dark | Admin primaries both themes. Sales/manager products light only. Planned/blueprint/ACM light only. |
| Mutations | 0 |

## STATE_NOT_REACHED

See `WAVE_4_STATE_NOT_REACHED_FINAL.md`. Workshops and planned 6/6 and sales/manager dark are **closed**. Remaining SNR are mutation/activation/owner-input fixtures only.

**STATE_NOT_REACHED_TOTAL = 5**, all with explicit blockers.

## Top findings

1. Product System is **design-time language**, not the sold-work editor. FLUX still inserts Produse between Cereri and Oferte (Wave 2 C5).
2. ProductDefinition has **no page**. Humans look in Product System; `/modules` points at Intake V6.
3. ProductAggregate explains **973024 task ids**; operator/Atelier do not show that grain.
4. V6 confirm can be blocked while an order is already frozen (**DEFINITION_DRIFT**).
5. `/governance` products tab is **stale** vs live `/product-system`.
6. Two documentation hierarchies (`DOCUMENTATION_HIERARCHY` vs `governanceData.truthHierarchy`).
7. Repo freeze is **omitted** from `/modules` and `/governance`.
8. Atelier / operator / tablet are **Execution projections** (not 12 missing systems). Dashboard/clients/HR are pages. `/modules` does not name the projections.
9. FE `activeTemplateScope` omits BE-offerable premount (**scope drift**).
10. TPL codes and “Product Compiler” dominate the Product System story (**technical leak**).

## Simplification candidates (audit only)

See `WAVE_4_SIMPLIFICATION_CANDIDATES.md`. None authorized now.

## Stop

`COMMIT = NO`. `PUSH = NO`. `WAVE_5 = NOT_AUTHORIZED`.  
`WAVE_4_CLOSED = YES`. Evidence stays local until Owner asks to commit.

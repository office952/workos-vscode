# S5 — Product System / Governance chrome truth (implementation)

| Field | Value |
|-------|--------|
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM_V1` |
| Task | `S5_PRODUCT_SYSTEM_AND_GOVERNANCE_CHROME_TRUTH_V1` |
| Phase | IMPLEMENTATION |
| Date | 2026-08-14 |
| Repository | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| HEAD before | `17e4b5359347f00265459d932ef5d8e571dbe693` |
| Unfreeze | NO (bounded display exception; `CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON`) |
| Push | NO |

## Verdict

```
VERDICT = PASS
S5_STATUS = PASS
HEAD_BEFORE = 17e4b5359347f00265459d932ef5d8e571dbe693
HEAD_AFTER = (local commit SHA after this report is committed)
PRODUCT_SYSTEM_ENTRY = WIRED
OLD_PRODUCT_SYSTEM_PRESENTATION = rail titled "Produse active"; Letters/ACM as undifferentiated peers; Logo deep-link "Template necunoscut"; next-step "Continuă spre ofertă"; connection card "Prețuri conexiune"
NEW_PRODUCT_SYSTEM_PRESENTATION = rail titled "Produse"; Letters "Rădăcină folosită azi"; ACM present + "Montaj ACM · parțial"; Logo "Candidat · rădăcină blocată"; next-step "Oferta se creează din Cereri"; card "Referință șablon" + 20 EUR/mp + "nu ofertă client"
LETTERS_RUNTIME_STATUS = ACTIVE (TPL-VOLUMETRIC-LETTERS_v2, unchanged)
LETTERS_PRESENTATION = Rădăcină folosită azi
ACM_RUNTIME_STATUS = PARTIAL / policy root-offerable (TPL-ACM-BOXED-MOUNTING-SUPPORT_v1, unchanged)
ACM_PRESENTATION = present on rail; Montaj ACM · parțial
ACM_DEACTIVATED = NO
ACM_REMOVED_FROM_RAIL = NO
ACM_GLOBAL_RENAME = NO
LOGO_RUNTIME_STATUS = BLOCKED / NOT OFFERABLE (unchanged)
LOGO_PRESENTATION = Candidat · rădăcină blocată (deep-link only; not in live rail)
LOGO_ACTIVATED = NO
LEGACY_RUNTIME_STATUS = ACTIVE
COMPONENT_FIRST_RUNTIME_STATUS = INACTIVE / CANDIDATE / NOT OFFERABLE
COMPONENT_FIRST_ACTIVATED = NO
LEGACY_RETIRED = NO
REFERENCE_PRICE_PRESENTATION = Referință șablon · 20 EUR/mp · nu ofertă client
REFERENCE_PRICE_NUMERIC_CHANGE = 0
PLANNED_SHELLS_CHANGED = NO
DOSSIER_MODEL = ONE_CANONICAL_DOSSIER (/product-system/blueprint-dossier)
DOSSIER_CHANGED = NO
DEV_MODE_STATUS = ABSENT
DEV_MODE_CHANGED = NO
MODULES_FREEZE_STATUS = VISIBLE
MODULES_NEW_PRESENTATION = compact "Referință înghețată" + CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON
GOVERNANCE_FREEZE_STATUS = VISIBLE
GOVERNANCE_NEW_PRESENTATION = same freeze + S1–S4 bounded-exception sentence
GOVERNANCE_PRODUCTS_TAB_STATUS = REFERINȚĂ / nomenclator / nu catalog activ
PRODUCT_SYSTEM_ENTRY_PERCEPTION = HONESTER
LETTERS_RUNTIME_STATUS_CHANGED = NO
PRODUCT_TRUTH_CHANGE = 0
PRICING_LOGIC_CHANGE = 0
ROUTES_CHANGED = 0
RBAC_CHANGED = NO
BACKEND_CHANGED = 0
DB_MUTATIONS = 0
LEVEL_1_SYSTEM_CHANGE = NO
CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON
S5_BOUNDED_EXCEPTION_USED = YES
GS_11 = IMPLEMENTED (chrome honesty; planned shells already honest, not deleted)
GS_12 = IMPLEMENTED
COMMIT_CREATED = YES (after this file is included)
PUSH = NO
PR = NO
MERGE = NO
DEPLOY = NO
S6 = NOT_AUTHORIZED
NEXT_TASK = NOT_AUTHORIZED
```

## Canonical truth (unchanged)

Product System does not choose a future in S5. It only states the present.

| Product | Runtime | Presentation |
|---------|---------|--------------|
| Letters `TPL-VOLUMETRIC-LETTERS_v2` | CURRENT RUNTIME AUTHORITY | Active / **Rădăcină folosită azi**. Not component-first. |
| ACM boxed `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | policy root-offerable; Harta PARTIAL | Stays on rail as **Alucobond casetat** + **Montaj ACM · parțial** |
| Logo `TPL-VOLUMETRIC-LOGO_v1` | root blocked; not live offerable | Deep-link **Candidat · rădăcină blocată**; not added to live rail |
| Component-first `TPL-COMP-*` | INACTIVE / CANDIDATE | Not promoted; not presented as authority |

## What changed (display only)

| Surface | Old | New |
|---------|-----|-----|
| V2 rail title | Produse active | **Produse** |
| Letters | peer, no status | **Rădăcină folosită azi** |
| ACM | peer, no status | stays on rail + **Montaj ACM · parțial** |
| Logo deep-link | Template necunoscut în listă | **Candidat · rădăcină blocată** + not-offerable copy |
| Next-step | Continuă spre ofertă | **Oferta se creează din Cereri**; not all templates are offer-ready. Routes unchanged. |
| Connection card | Prețuri conexiune / 20 EUR/mp | **Referință șablon** · same 20 EUR/mp · **nu ofertă client** |
| `/modules` | no repo freeze | compact **Referință înghețată** banner |
| `/governance` | no repo freeze | same banner + S1–S4 bounded-exception line |
| Governance products tab | REFERINȚĂ + “X produse” | nomenclator · **nu catalog activ** · rânduri |

No new status engine. Rail chips read existing `getProductModularityTruth` commercial vocabulary.

## Dirty tree classification

| Class | Paths |
|-------|--------|
| S5_PRODUCT | `ProductSystemV2Workspace.tsx`, `ProductSystemStructureReadonlyPanel.tsx`, `productSystemV2RailStatus.ts`, `commercialFlowUi.ts`, `truthPagesHonestyBaseline.ts`, `ModuleChain.tsx`, `Governance.tsx`, `WorkosReferenceFreezeBanner.tsx`, `workosReferenceFreezePresentation.ts` |
| S5_TEST | matching `*.test.ts(x)`, `frontend/scripts/ci-unit-tests.txt` |
| S5_EVIDENCE | `docs/qa/.../s5-research/`, `docs/qa/.../s5-runtime/` |
| S5_WORKLOG | unification worklog + `GLOBAL_SIMPLIFICATION_BACKLOG.md` status section |
| PREEXISTING_UNRELATED | `backend/_qa_backups/`, `_tmp_*`, other `docs/qa/*` leftovers — **not committed** |
| UNKNOWN | none |

## Tests

```
cd frontend
npx pnpm@8.10.0 exec vitest run
  src/features/product-system/productSystemV2RailStatus.test.ts
  src/features/product-system/productSystemV2Workspace.test.ts
  src/lib/commercialFlowUi.test.ts
  src/lib/workosReferenceFreezePresentation.test.ts
  src/pages/ModuleChain.test.tsx
  src/pages/Governance.test.tsx
  src/lib/rbac.test.ts
  src/lib/shellNavigation.test.ts
  src/lib/activeTemplateScope.test.ts
  src/features/product-system/lettersAcmCompositionSablonProcess.test.ts
  src/features/product-system/productSystemCanonicalCatalog.test.ts
  src/features/product-system/lettersAcmCompositionConnectionPrices.test.ts
  src/lib/productSystemModularityTruth.test.ts
  src/pages/Governance.presentTruth.test.tsx
```

| Field | Value |
|-------|--------|
| TEST_COMMANDS | targeted Vitest above |
| TEST_COUNT | 14 files / 126 tests |
| TEST_RESULT | PASS |

Proof coverage vs GO:

1. Rail does not classify PARTIAL/BLOCKED as uniformly fully active — title **Produse**; ACM/Logo distinct kinds.
2. Letters retains active/runtime truth.
3. ACM remains present; PARTIAL chip visible.
4. Logo blocked/non-offerable not hidden on deep-link.
5. Component-first remains inactive/candidate.
6. No template activation/publication.
7. Reference price card labeled șablon / nu ofertă client.
8. Numeric 20 EUR/mp / `formatLettersAcmSablonProcessRateRo` unchanged.
9. Planned shells unchanged.
10. One canonical Dossier.
11. `/modules` freeze visible.
12. `/governance` freeze + bounded exception visible.
13. Governance products tab remains reference/nomenclator.
14–16. Routes / RBAC / backend+DB+Product Truth unchanged.

## Runtime proof

One live stack (`:3000` + `:8000`). No parallel Playwright. Role: **admin** (manager/sales keep existing `view:products`; they do not see `/modules` or `/governance` — GS-12 is not a substitute for GS-11).

### Screenshots

| File | Mode | Surface |
|------|------|---------|
| [s5-impl-ps-letters-dark.png](s5-impl-ps-letters-dark.png) | dark | Product System Letters |
| [s5-impl-ps-letters-light.png](s5-impl-ps-letters-light.png) | light | Product System Letters |
| [s5-impl-ps-acm-light.png](s5-impl-ps-acm-light.png) | light | ACM + reference price |
| [s5-impl-ps-logo-light.png](s5-impl-ps-logo-light.png) | light | Logo blocked deep-link |
| [s5-impl-modules-light.png](s5-impl-modules-light.png) | light | `/modules` freeze |
| [s5-impl-modules-dark.png](s5-impl-modules-dark.png) | dark | `/modules` freeze |
| [s5-impl-governance-light.png](s5-impl-governance-light.png) | light | `/governance` freeze |
| [s5-impl-governance-dark.png](s5-impl-governance-dark.png) | dark | `/governance` freeze |
| [s5-impl-governance-products-light.png](s5-impl-governance-products-light.png) | light | products tab nomenclator |

LIGHT_MODE = YES (Product System, modules, governance).  
DARK_MODE = YES (Product System Letters, modules, governance).  
Truth does not rely on color alone (text chips + banner copy).

## Owner visual verification

1. **Product System**  
   URL = `http://127.0.0.1:3000/product-system/products`  
   Role = admin (manager/sales: same Produse chrome if they open it)  
   Letters expected = **Rădăcină folosită azi**  
   ACM expected = present, **Alucobond casetat**, **Montaj ACM · parțial**  
   Logo expected = `/product-system/products/TPL-VOLUMETRIC-LOGO_v1` → **Candidat · rădăcină blocată**  
   reference-price expected = **Referință șablon** · 20 EUR/mp · **nu ofertă client**

2. **Modules**  
   URL = `http://127.0.0.1:3000/modules`  
   Role = admin  
   expected freeze indicator = **Referință înghețată** + `CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON`  
   Meaning = current WorkOS is frozen reference; implementation changes only via authorized bounded waves.

3. **Governance**  
   URL = `http://127.0.0.1:3000/governance`  
   Role = admin  
   expected freeze indicator = same **Referință înghețată**  
   expected bounded-exception meaning = S1–S4 were display/nav exceptions, not an application unfreeze  
   products tab expected status = REFERINȚĂ / nomenclator / **nu catalog activ**

## Method / roadmap checkpoint

| Field | Value |
|-------|--------|
| Metoda de lucru si logica abordarii | Display-only honesty. Read existing modularity/freeze vocabulary. No winner between legacy and component-first. |
| Roadmap awareness | 9/10 |
| Where is S5 positioned in complete roadmap? | After S1–S4 bounded chrome exceptions; before any S6 catalog/IA work. GS-11 + GS-12 only. |
| Cât sunt în direcția stabilită | 100% of authorized S5 boundary |
| Dead Pieces Check | No new engines, routes, or DEV MODE. Planned shells left in place. |
| Overengineering Check | Page-local helper + existing chips + compact banner. No ProductTruthStatusEngine / FreezeRegistry. |
| Impact Harta sistemelor | NO CHANGE |
| Impact Guvernanta sistemului | DISPLAY UPDATE ONLY — freeze + bounded-exception copy; products tab still reference |
| Forbidden Scope respected | YES |
| Next recommended step according to roadmap | S6 = NOT_AUTHORIZED. Stop. Owner decides later. |

Forbidden scope confirmation: no seed, migration, DB write, Product System activation/deactivation, publication, Product Truth write, Pricing write, Cost Engine, Quote/Order, ProductDefinition, ProductAggregate, Execution, task generation, Intake V6, SVG/DWG, RBAC, route deletion, ACM removal, global ACM rename, component-first promotion, legacy retirement, Dossier merge, DEV MODE, broad redesign.

## Stop

Do not push. Do not start S6.

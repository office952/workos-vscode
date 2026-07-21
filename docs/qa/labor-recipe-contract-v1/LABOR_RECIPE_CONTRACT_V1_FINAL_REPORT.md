# LABOR_RECIPE_CONTRACT_V1 — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `212654a2` |
| Final HEAD | branch tip after labor commits (see §30) |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/labor-recipe-contract-v1/` |
| API | `GET /api/v1/product-system/templates/{code}/pricing` (`schema_version` **1.1.0**) |
| UI | Product System → **Prețuri template** → **Manoperă specifică template-ului** |

## 1. Verdict

| Axis | Result |
|------|--------|
| Central labor catalog | PASS — rates stay in typed registry / workcenter_rates |
| Recipe contract | PASS — typed `labor_recipes[]` additive read model |
| ACM | PASS — shell labor visible; treatments remain commercially blocked; 5/0 unchanged |
| VL | PASS_WITH_WARNINGS — 12 recipes, mostly registry-linked (formulas empty) |
| Volum Aluminiu | PASS_WITH_WARNINGS — API 2 recipes; UI tab hidden (component-first bucket) |
| Formula ownership | PASS — template ops / commercial refs; no rate duplication |
| Rate ownership | PASS — catalog join only |
| Readiness | PASS — technical vs commercial separated |
| CPP | PASS — preview unchanged vs Studio V1 dumps |
| EIC | PASS — provenance unchanged |
| UI | PASS_WITH_WARNINGS — clear on ACM/VL/Logo; Volum Aluminiu tab gap |
| Regression | PASS — recipe arrays identical length/status; no calc change |

## 2. Executive truth (RO)

Am formalizat modelul corect: **tarif central de manoperă în catalog** + **rețetă specifică pe template**. Studio arată operațiile, formulele (unde există), costul intern, tariful comercial și blocajele — fără tarife inventate și fără HR. ACM rămâne înghețat. VL arată rețetele legate de registry (formule încă incomplete). Volum Aluminiu are rețetă în API, dar tab-ul Prețuri nu apare pe bucket-ul component-first.

## 3. Repo / branch / HEAD / dirty tree

- Repo: `C:\w\psiso`
- Branch: `feature/product-system-active-path-isolation-v1`
- Kickoff: `212654a2`
- Dirty tree outside allowlist: protected / untouched
- No push / no PR

## 4. Accepted Studio state

Accepted `TEMPLATE_PRICING_STUDIO_V1` PASS_WITH_WARNINGS at `212654a2` before this build.

## 5. Runtime / API truth

See `RUNTIME_API_TRUTH.md`. Proof on **8020** because **8000** is a Windows ghost LISTENING set. FE screenshots used `BACKEND_PORT=8020`.

## 6–8. Plan / map / multi-agent

CP0 freeze + allowlist + shared map written before writes. Implementation followed ownership split; no parallel naming.

## 9. CP0 freeze

Stable IDs, catalog vs template ownership, read-only V1, no DB table — held.

## 10–12. Classification / ownership

Labor classes applied from typed catalog + status. Templates own ops/formulas; catalog owns rates. Machine forming excluded from labor recipes.

## 13–16. Identity / formulas / minimums / cost vs commercial

Identity includes op + catalog + formula token. Minimums surfaced when present on ops. Internal cost and commercial rate shown separately (`unavailable` when not mapped).

## 17–18. Readiness

Missing / mismatch rates → commercial blocked, technical may remain ready. Registry-linked VL rows without qty keys → technical_ready false (honest).

## 19–22. Templates

| Template | Labor recipes | Notes |
|----------|---------------|-------|
| ACM | 3 | 1 warning (rate-basis), 2 missing ASSEMBLY |
| VL | 12 | LED/wiring/finish/install visible; formulas mostly absent |
| Logo | 3 | commercial_line → labor/service catalog refs |
| Volum Aluminiu | 2 | bonding + painting from ops; rates missing under template filter |

## 23–24. CPP / EIC

Byte-compare of `cpp_preview` / `eic_preview` / `acm_acceptance` vs Studio V1 runtime: **identical**. No new commercial lines activated.

## 25–26. UI / screenshots

Section `Manoperă specifică template-ului`. Matrix in `SCREENSHOT_MATRIX.md` (01–15).

## 27. Tests

```text
backend/tests/test_template_labor_recipe.py
backend/tests/test_template_pricing_recipe.py
→ 13 passed
```

## 28. Runtime evidence

`docs/qa/labor-recipe-contract-v1/runtime/*_pricing.json`

## 29. Files changed (allowlist)

- `backend/services/template_labor_recipe.py` (new)
- `backend/services/template_pricing_recipe_service.py`
- `backend/schemas/template_pricing_recipe.py`
- `backend/tests/test_template_labor_recipe.py` (new)
- `frontend/src/api/templatePricingRecipe.ts`
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- `docs/qa/labor-recipe-contract-v1/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (append)

## 30. Commits

| SHA | Message |
|-----|---------|
| `23e54434` | docs(qa): freeze Labor Recipe Contract V1 |
| `09e0412e` | feat(product-system): add typed template labor recipe read model |
| `e9461d81` | feat(product-system-ui): expose labor recipes in Preturi template |
| `82aba35c` | docs(qa): finalize Labor Recipe Contract V1 evidence |
| `d95b7a29` | docs(qa): record Labor Recipe Contract V1 final HEAD |

## 31. Worklog

Section **LABOR RECIPE CONTRACT V1** appended to canonical realignment worklog.

## 32. Dirty-tree protection

Only allowlisted paths touched.

## 33. Remaining blockers / warnings

- Windows `:8000` ghost → proof on `:8020`
- VL labor mostly registry-linked without ops formulas
- Volum Aluminiu Prețuri tab hidden on component-first bucket
- ASSEMBLY shared by ACM fold/mount without owner-specific rates
- No HR (intentional)

## 34. Next recommended build

**LABOR_RECIPE_CONTRACT_V1_CLOSURE** — surface Prețuri template for Volum Aluminiu / component-first honesty path; attach ops formulas for VL labor codes where owner-confirmed; do **not** auto-run CNC or ACM rate wiring.

Do not execute automatically.

Alternatives (owner choose later): `CNC_MACHINE_SERVICE_MATRIX_V1` · `ACM_OWNER_RATE_WIRING`.

## 35. Dead pieces

No new dead tables. No invented rates. Capture scripts not kept in frontend.

## 36. Method

Read-model first over patterns already in Studio; join catalog; never write rates; prove CPP/EIC unchanged before UI claim.

## 37. Parerea sinceră ca agent

- Central-rate + template-recipe: **da, modelul corect**
- Recipes honestly template-specific: **partial** — ACM/Volum ops yes; VL mostly registry-linked
- Rates still centralized: **da**
- Calculation change: **nu**
- Missing rates scoped correctly: **da** (commercial only)
- HR unnecessary for V1: **da**
- UI in 10 seconds: **da pe ACM/VL**; Volum Aluminiu UI gap
- ACM frozen: **da**
- Fragile: port ghosts; VL formula emptiness; component-first pricing tab gate
- Next: closure for UI/formula honesty, not HR

## 38. Roadmap awareness

Inventory live · typed catalogs reusable · PS owns recipe visibility · ACM KEEP_DRAFT · dual-select HOLD · no Execution · no artwork parser · no Build 2 · mobile final-final.

## 39. Direction score

**78/100%**

| Slice | Score |
|-------|------:|
| ownership | 90 |
| recipe truth | 70 |
| formula visibility | 55 |
| rate visibility | 85 |
| readiness | 85 |
| UI | 75 |
| regression | 95 |
| ACM resumability | 40 |

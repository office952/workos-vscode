# LABOR_RECIPE_CONTRACT_V1_CLOSURE — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `1518b6ac` |
| Final HEAD | `b14d3e26` |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/labor-recipe-contract-v1-closure/` |
| schema_version | **1.1.1** (additive formula truth fields) |

## 1. Verdict

| Axis | Result |
|------|--------|
| Volum Aluminiu access | **PASS** — Prețuri template reachable |
| Component-first / legacy ownership | **PASS** — bucket unchanged; module note shown |
| VL recipe classification | **PASS** — all 12 have explicit `formula_status` |
| Formula truth | **PASS_WITH_WARNINGS** — 8 qty-key / 1 confirmed / 2 operation-only / 1 missing-owner |
| Central rates | **PASS** — not copied into templates |
| Readiness | **PASS** — T/C + formula status separated |
| CPP | **PASS** — unchanged vs Labor V1 dumps |
| EIC | **PASS** — unchanged |
| UI | **PASS** |
| ACM regression | **PASS** — 5/0, treatment=false |

## 2. Executive truth (RO)

Am închis cele două goluri din contract: **Volum Aluminiu** are acum tab Prețuri (fără să-l transformăm în produs root), iar cele **12 rețete VL** au status de formulă explicit — cantități confirmate unde există adevăr, fără productivitate inventată. Ambalarea și câteva operații rămân la owner.

## 3. Repo / HEAD / dirty tree

- Repo `C:\w\psiso`
- Branch `feature/product-system-active-path-isolation-v1`
- Kickoff `1518b6ac`
- Outside-allowlist dirty tree protected
- No push / no PR

## 4. Accepted Labor Recipe V1 state

Accepted PASS_WITH_WARNINGS at `1518b6ac` before closure.

## 5. Runtime port / API

Proof **`:8020`**. `:8000` ghost PIDs (DEAD); pricing on 8000 **404**. FE proxy verified `schema_version=1.1.1` via `:3000`.

## 6–9. Plan / map / agents / CP0

CP0 freeze + allowlist + VL evidence matrix written before writes. Explore agent evidence used for classification (no invented constants).

## 10–12. Volum Aluminiu

- Cause: `isProduct` false for `legacy-shared-modules` → no pricing tab.
- Fix: `showTemplatePricingStudio` eligibility for `TPL-VOLUM-ALUMINIU_v1` while keeping bucket.
- UI: same `TemplatePricingStudioPanel` + API.
- Labor: 2 recipes visible (bonding + painting); rates missing; qty from ops / Product Truth labels.

## 13–18. VL 12-row status (runtime 8020)

| Status | Count | Ops |
|--------|------:|-----|
| QUANTITY_KEY_CONFIRMED | 8 | bonding, face vinyl, lamination, painting, return RAL/vinyl, print, LED |
| FORMULA_CONFIRMED | 1 | montaj (commercial fixed) |
| MISSING_OWNER_FORMULA | 1 | PACKAGING |
| OPERATION_ONLY | 2 | PREPRESS, ELECTRICAL_WIRING |
| LEGACY_METADATA as final | 0 | seed names demoted via qty-key path + warning |

`led_assembly_time` **not** bound (throughput invent risk).

## 19–22. Provenance / ownership / readiness

Central catalog rates unchanged. Template owns consumption references. Technical ready when formula or qty key confirmed; commercial still rate-gated.

## 23–25. Regression

| Check | Result |
|-------|--------|
| VL cpp_preview | identical to Labor V1 dump |
| VL eic_preview | identical |
| ACM cpp / acm_acceptance | identical; 5/0; treatment=false |
| Migrations / new rates | none |

## 26. Screenshots

See `SCREENSHOT_MATRIX.md` (01–13).

## 27. Tests

```text
backend: test_template_labor_formula_truth + labor_recipe + pricing_recipe → 18 passed
frontend: templatePricingStudioEligibility.test.ts → 3 passed
```

## 28–32. Runtime / files / commits / worklog / dirty tree

Runtime JSON under `runtime/`. Worklog section appended. Allowlist-only.

## 33. Remaining owner inputs

See `OWNER_LABOR_PRODUCTIVITY_DECISION_PACK.md` (one consolidated pack).

## 34. Remaining warnings

- Port 8000 ghost environment
- VL packaging / electrical / prepress owner gaps
- Volum Aluminiu ops qty keys include gates (`return_depth_mm`) — not invented perimeter overwrite
- ACM fold/mount still OPERATION_ONLY + missing ASSEMBLY rates

## 35. Next recommended build

**OWNER_LABOR_PRODUCTIVITY_RATES_V1** — decide packaging + electrical + optional LED time; do not auto-execute.

Alternatives later: `CNC_MACHINE_SERVICE_MATRIX_V1` · `ACM_OWNER_RATE_WIRING`.

## 36–37. Dead pieces / method

No new tables. Classify first, wire only evidence-backed qty keys, expose route without ownership flip.

## 38. Parere sinceră

- Volum Aluminiu correctly represented? **Da** (API + UI)
- Component ownership preserved? **Da**
- VL formulas truly confirmed? **1** (montaj); **8** qty-key; **3** unresolved classes
- Invented productivity? **Nu**
- Blank formulas honest? **Da**
- CPP/EIC change? **Nu**
- UI 10s? **Da**
- ACM frozen? **Da**
- Another closure slice? **Nu pentru acces/clasificare; da pentru owner productivity**
- Next: owner productivity pack

## 39. Roadmap

Inventory live · catalogs central · PS owns recipes · ACM KEEP_DRAFT · dual-select HOLD · no Execution/artwork/Build2/mobile.

## 40. Direction score

**84/100%**

| Slice | Score |
|-------|------:|
| Volum Aluminiu access | 95 |
| VL formula truth | 75 |
| ownership | 90 |
| provenance | 85 |
| readiness | 85 |
| UI | 85 |
| CPP/EIC safety | 95 |
| ACM resumability | 40 |

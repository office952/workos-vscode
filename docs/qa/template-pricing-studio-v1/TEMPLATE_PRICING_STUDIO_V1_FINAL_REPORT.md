# TEMPLATE_PRICING_STUDIO_V1 — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `585115da` (Pricing Foundation accepted) |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/template-pricing-studio-v1/` |

## 1. Verdict

| Axis | Result |
|------|--------|
| Route / navigation | PASS — tab **Prețuri template** on `/product-system/products/:templateCode` |
| Recipe contract | PASS — derived read-only recipe items |
| Materials | PASS — Inventory / registry purchase cost |
| Machine operations | PASS — typed catalog machine_operation |
| Labor / services | PASS — typed catalog labor/service |
| Formulas / qty keys | PASS — CPP quantity_paths exposed |
| CPP | PASS_WITH_WARNINGS — structural catalog preview (no calc change) |
| EIC | PASS_WITH_WARNINGS — structural provenance notes |
| Readiness | PASS — technical vs commercial separated |
| UI | PASS — screenshots 01–07 |
| ACM acceptance | PASS — registry **5/0**; `treatment_commercial_lines_allowed=false` |
| Regression | PASS — no price/migration/seed changes |

## 2. Executive truth (RO)

Product System are acum un tab **Prețuri template** care arată din ce e format prețul unui șablon. Cataloagele rămân autoritatea tarifelor; Studio-ul doar compune rețeta, cantitățile și blocajele. ACM shell rămâne 5/0; tratamentele față rămân blocate comercial. Nu s-au inventat prețuri și nu s-a schimbat CPP/EIC.

## 3. Repo / HEAD

Kickoff `585115da`. Final HEAD: see commits after land. Dirty tree pre-existing protected via allowlist.

## 4–5. Pricing Foundation + Owner GO

Accepted Pricing Foundation V1. Owner GO: implement TEMPLATE_PRICING_STUDIO_V1 only.

## 6. Backend restart / API truth

| Check | Result |
|-------|--------|
| `typed_catalog` after clean restart | **50/50** populated (gate PASS) — see `RUNTIME_API_TRUTH.md` |
| Live Windows `:8000` | Ghost LISTENING PID blocked rebinds during session |
| Runtime proof port | **`127.0.0.1:8020`** (no-reload uvicorn) |
| FE proxy for screenshots | `BACKEND_PORT=8020` |

## 7–10. Plan / Compound / Agents / CP0

- CP0 freeze, allowlist, shared map under `docs/qa/template-pricing-studio-v1/`
- Route freeze: products detail tab (not `/templates/...` FE fork)
- Editability: read-only V1

## 11–12. Navigation + read model

- FE: `UnifiedCatalogDetailSection` += `pricing` → **Prețuri template**
- BE: `GET /api/v1/product-system/templates/{template_code}/pricing`
- Service composes `PricingRegistryService` + `RULES_BY_TEMPLATE` + ACM gate + EIC group notes
- Case-insensitive DB template lookup (identity uppercases `_V1`, DB keeps `_v1`)

## 13–20. Recipe views

| Kind | Source |
|------|--------|
| Materials | registry items `typed_catalog=material` — Cost achiziție |
| Machine ops | `machine_operation` + machine_family |
| Labor / services | typed labor/service |
| Commercial lines | CPP rule catalog (`commercial_line`) |
| Rate-basis warnings | `data_quality_flags` surfaced, not rewritten |

## 21–24. Readiness / CPP / EIC

- Technical vs commercial chips separate
- Stock untracked does not block commercial readiness notes
- CPP/EIC: structural preview only — **no calculation changes**

## 25. ACM acceptance

| Metric | Value |
|--------|-------|
| shell_registry_confirmed / missing | **5 / 0** |
| treatment_commercial_lines_allowed | **false** |
| recipe items (runtime) | 11 |

## 26. Other templates (runtime 8020)

| Template | Recipe items | Registry |
|----------|--------------|----------|
| VL v2 | 59 | 38 / 4 |
| Logo v1 | 7 | 0 / 0 (linked recipe visibility) |
| Volum Aluminiu | 1 | component_only honesty |

## 27. Screenshots

`docs/qa/template-pricing-studio-v1/screenshots/`

| File | URL / state |
|------|-------------|
| 01 | `/product-system/products` |
| 02 | ACM detail overview |
| 03 | ACM Prețuri template |
| 04 | ACM materials filter |
| 05 | ACM machine ops filter |
| 06 | VL Prețuri template |
| 07 | Volum Aluminiu Prețuri template |

## 28–29. Tests + runtime

- `backend/tests/test_template_pricing_recipe.py` — **5 passed**
- Runtime JSON: `docs/qa/template-pricing-studio-v1/runtime/`
- Typed registry still 50/50 typed_catalog

## 30–34. Files / commits / worklog / dirty tree

Allowlist-only. Worklog section appended. Outside dirty paths untouched. No push / no PR.

## 35. Remaining warnings

- Editing intentionally locked (read-only)
- CPP/EIC quantitative preview requires workspace payload (future)
- Windows `:8000` ghost listener required alternate proof port this session
- Logo / Volum Aluminiu are non-root — honesty warnings expected

## 36. Next recommended build

**LABOR_RECIPE_CONTRACT_V1** — formalize template-specific labor quantity/time without inventing a ServiceRate table; optionally then ACM_OWNER_RATE_WIRING.

## 37–39. Method / opinion

Studio is in the correct Product System location (detail tab). Operator can see price composition in ~10 seconds. Rates vs recipes separated. Inventory still owns materials. ACM is a useful acceptance case (5/0 + treatment blocked). No false authority created.

Fragile: Windows local port ghosts; case-normalization between identity scope and DB codes; CPP still needs payload for numeric subtotals.

## 40–41. Roadmap / score

Inventory live · typed catalogs reusable · PS owns recipe visibility · ACM draft · dual-select HOLD · no Execution/artwork/Build2/mobile.

Direction: **72/100** (route 90 · recipe 75 · catalog 85 · labor specificity 55 · CPP/EIC provenance 65 · UI 80 · commercial readiness 70 · ACM resumability 40).

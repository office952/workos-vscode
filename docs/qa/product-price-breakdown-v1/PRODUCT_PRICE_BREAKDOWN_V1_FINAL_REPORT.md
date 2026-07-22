# PRODUCT_PRICE_BREAKDOWN_V1 - Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `b8c6e8a8` (TEMPLATE_ACTIVATION_V1 accepted) |
| Final HEAD | 262d41ac |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/product-price-breakdown-v1/` |
| Proof port | `8020` (`:8000` ghost environment warning) |

## 1. Verdict (by axis)

| Axis | Result |
|------|--------|
| Materials | PASS_WITH_WARNINGS - purchase/inventory gaps visible |
| Market price truth | PASS - no AI-invented material prices |
| Quantities | PASS - fixture demo + Product Truth keys; VL qty resolved |
| Machine operations | PASS - projected from CPP/EIC |
| Labor | PASS - physical drivers via AI/CPP lines; time secondary |
| Services | PASS - packaging/service lines projected |
| AI defaults | PASS - visible, configurable via existing AI section |
| Totals | PASS - internal != commercial |
| CPP reconciliation | PASS - VL cpp_total_matches=true (1061 RON) |
| EIC provenance | PASS - VL eic_total_matches=true (923.2 RON) |
| UI | PASS - Desfasurator pret in Preturi template |
| Template acceptance | PASS_WITH_WARNINGS - see sections 25-28 |

## 2. Executive truth (RO)

Operatorul vede acum cum se construieste pretul pe configuratie demo: materiale (achizitie), utilaje, manopera, servicii, AI, ajustari, total intern vs comercial. CPP ramane autoritatea comerciala; EIC explica costul intern; desfasuratorul nu recalculeaza.

## 3. Repo / branch / HEAD

- Repo: `C:\w\psiso`
- Branch: `feature/product-system-active-path-isolation-v1`
- Kickoff: `b8c6e8a8`
- Dirty tree: large pre-existing; allowlist-only writes

## 4. Accepted lifecycle state (from TEMPLATE_ACTIVATION_V1)

VL PUBLISHED; ACM shell PUBLISHED (treatments blocked); Logo unpublished; Volum Aluminiu child; snapshots/CPP/EIC behavior unchanged by this build

## 5. Runtime truth

| Port | State |
|------|-------|
| `:8000` | Ghost LISTENING / stale 404 - environment |
| `:8020` | Canonical proof (uvicorn no-reload) |
| `:3000` | FE with BACKEND_PORT=8020 |

Runtime dumps: `runtime/SUMMARY.json`

| Template | Fixture | Lines | Comercial | Intern | Reconcile |
|----------|---------|-------|-----------|--------|-----------|
| VL | vl_letters_demo_v1 | 42 | 1061.00 | 923.20 | CPP+EIC OK |
| ACM | acm_shell_demo_v1 | 3 | null (blocked) | 5.00 | honest partial |
| Logo | logo_demo_v1 | 4 AI | null | null | honest (no root CPP) |
| Volum Aluminiu | volum_aluminiu_demo_v1 | 3 | 375.00 | 225.00 | child OK |

## 6-9. Plan / map / agents / CP0

CP0 freeze + allowlist in this folder. Shared line map in `schemas/product_price_breakdown.py`. Adapter only - no second calculator.

## 10-17. Contracts delivered

- API: `POST /api/v1/product-system/templates/{code}/price-breakdown`
- Groups: material / machine / labor / service / ai_decision / adjustment
- AI contribution note (no parallel total)
- Calibration hooks = capacity hints, excluded_from_total=true

## 18-19. Formula simplicity / no-time-primary

Operator formulas like `12.5 ml x 25 RON/ml`. Time only in secondary calibration hooks.

## 20-24. Totals / CPP / EIC

Internal and commercial totals separate. VL line sums reconcile with CPP/EIC authorities. Provenance arrays exposed.

## 25-28. Template acceptance

| Template | Verdict | Note |
|----------|---------|------|
| VL | PASS | Full demo breakdown |
| ACM | PASS_WITH_WARNINGS | treatments blocked chip; seeded pytest proves reconcile |
| Logo | PASS | Preview without pretending publication readiness |
| Volum Aluminiu | PASS | Separate-calc child slice; not root |

## 29-30. UI / screenshots

`SCREENSHOT_MATRIX.md` - 11 captures.

## 31. Tests

```text
pytest tests/test_product_price_breakdown_v1.py -> 6 passed
vitest PriceBreakdownSection.test.tsx -> 1 passed
```

## 32. Runtime/API evidence

`runtime/*.json` + `SUMMARY.json`

## 33. Files changed (allowlist)

Backend: schemas/services/router/fixtures/tests
Frontend: api + PriceBreakdownSection + Studio wire + vitest
Docs: docs/qa/product-price-breakdown-v1/** + canonical worklog append

## 34. Commits

```text
5288e652 docs(qa): freeze Product Price Breakdown V1 contract
b069ec84 feat(product-system): add authoritative price breakdown read model
35fc7324 feat(product-system-ui): add Desfasurator pret workspace
37628ac9 test(product-system): prove CPP EIC reconciliation for price breakdown
16e9db79 docs(qa): finalize Product Price Breakdown V1 evidence
cb3a5d1f docs(qa): pin Product Price Breakdown V1 final HEAD
dd1fbd19 docs(qa): restore Product Price Breakdown V1 report encoding
```

No push / no PR.

## 35. Worklog

Section PRODUCT PRICE BREAKDOWN V1 appended to canonical realignment worklog.

## 36. Dirty-tree protection

Outside-allowlist paths untouched.

## 37. Remaining warnings

- :8000 ghost
- ACM demo fixture commercial still blocked (honest)
- Material purchase gaps still visible
- Logo without CPP rules as root

## 38. Calibration opportunities (simple)

1. LED per-module rate (0.35 EUR) vs observed jobs
2. Packaging band MEDIUM + fragile addon
3. Electrical min + per-PSU
4. Fill missing material purchase costs in Inventory
5. Enrich ACM shell demo geometry for standalone CPP lines

## 39. Next recommended build (do not auto-execute)

MATERIAL_MARKET_PRICE_REGISTRY_V1 - close material purchase gaps with real supplier truth.

Alternates: AI_CALIBRATION_FEEDBACK_V1; ACM_CAPABILITY_PRICING_V1; PRODUCT_PRICE_BREAKDOWN_V1_CLOSURE

## 40. Dead pieces

None introduced. No duplicate calculator.

## 41. Metoda

Adapter read-model over CPP+EIC+recipe; demo fixtures; UI progressive disclosure.

## 42. Parerea sincera

- 10 seconds? Da - totals + reconcile chips first.
- Material market-based? Da unde exista; lipsurile sunt oneste.
- Labor simple? Da - driveri fizici / AI quantity.
- Overengineering? Nu - un endpoint adapter.
- Time secondary? Da.
- CPP reconcile? Da pe VL (+ pytest ACM seeded).
- AI easy to review? Da.
- ACM base separated? Da (treatments blocked).
- Calibrate first: material gaps + LED/packaging rates.

## 43. Roadmap awareness

Inventory live; Product System recipes; CPP calculates; EIC explains; AI configurable; breakdown = calibration surface; no Execution; no artwork parser; no Build 2; mobile out.

## 44. Direction score

82/100% - material 70; quantity 85; formula 85; AI 90; totals 90; CPP/EIC 88; UI 85; calibration readiness 75
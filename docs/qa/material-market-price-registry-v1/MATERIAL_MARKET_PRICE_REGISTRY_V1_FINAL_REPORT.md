# MATERIAL_MARKET_PRICE_REGISTRY_V1 - Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `a243dd69` |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/material-market-price-registry-v1/` |
| Proof port | `8020` |
| Migration | **none** |

## 1. Verdict

| Axis | Result |
|------|--------|
| Inventory preservation | PASS - no identity move |
| Supplier truth | PASS_WITH_WARNINGS - supplier_id sparse in DB (0 with_supplier in dump) |
| Purchase price | PASS - unit_cost as raw |
| Landed cost | PASS_WITH_WARNINGS - field reserved; not populated |
| Normalization | PASS - sheet->mp formula + identity mp |
| Freshness | PASS - AI_DECISION thresholds; not price truth |
| Fallback | PASS - none auto-created |
| Product System | PASS - breakdown material provenance |
| CPP/EIC | PASS - no second calculator; snapshots untouched |
| UI | PASS - Preturi materiale registry |

## 2. Executive truth (RO)

Registrul de preturi materiale citeste adevarul de achizitie din Inventory. Lipsa pretului ramane vizibila. AI nu inventeaza preturi. Normalizarea (ex. sheet->mp) este explicita. Desfasuratorul arata sursa, freshness si pretul normalizat pe liniile de material.

## 3. Repo / HEAD

- Kickoff: `a243dd69`
- Dirty tree: large pre-existing; allowlist-only

## 4. Accepted breakdown state

VL 1061/923.2 reconcile retained; adapter only enriches material provenance.

## 5. Runtime truth

| Metric | Value |
|--------|-------|
| total materials | 64 |
| priced | 31 |
| missing | 33 |
| AI fallback | 0 |
| ACM 3mm | 15 EUR/mp OWNER_CONFIRMED CURRENT |
| VL material lines with provenance | 16/20 |

## 9-12. CP0 / counts / sources / precedence

See CP0 freeze. Precedence frozen; classification from source_name/notes/review_status.

## 16. Unit normalization

Sheet 2440x1220 @ 89.30 EUR -> ~30 EUR/mp (unit test). Inventory ACM already stored as mp (identity).

## 21. Temporary AI fallback

Reserved in precedence; **not applied** in V1.

## 22-25. UI / cross-links / breakdown

`/inventory/pricing` -> Preturi materiale panel. Inventory + Product System links in detail. Breakdown shows material_source_type / supplier / freshness / formula.

## 26-28. CPP/EIC / snapshots

Unchanged calculation authority. No snapshot mutation.

## 29. Active-template gaps

Still missing purchase truth for several VL consumables (adeziv/cabluri/etc. in recipe) and other inventory rows. Critical list from runtime may include template-linked missing codes (e.g. MAT-LED-PSU-12V).

## 30. Tests

```text
pytest tests/test_material_market_price_registry_v1.py -> 7 passed
pytest (+ breakdown suite overlap) -> green
vitest MaterialMarketPriceRegistryPanel.test.tsx -> 1 passed
```

## 31-32. Evidence / screenshots

`runtime/` + `SCREENSHOT_MATRIX.md` (7 captures).

## 37-38. Remaining warnings / missing prices

33 materials without unit_cost. Collect real supplier/invoice prices for VL consumables and LED/PSU first.

## 39. Next recommended build (do not auto-execute)

**SUPPLIER_PRICE_IMPORT_V1** - structured import of supplier offers/invoices into existing Inventory fields (still no invented prices).

Alternates: AI_CALIBRATION_FEEDBACK_V1 · ACM_CAPABILITY_PRICING_V1 · MATERIAL_MARKET_PRICE_REGISTRY_V1_CLOSURE

## 42. Parerea sincera

- Trustworthy? **Da unde exista unit_cost + source**; lipsurile sunt oneste.
- Raw vs normalized? **Da**.
- Supplier provenance? **Partial** - few supplier_id links in current DB.
- Stale obvious? **Da** (chips + policy).
- AI impersonating market? **Nu**.
- Calibrate first: **adeziv/cabluri VL + PSU + attach suppliers**.

## 44. Direction score

**78/100%** - supplier 55 · normalization 85 · freshness 80 · UI 85 · Product System 80 · CPP/EIC 90 · coverage 70

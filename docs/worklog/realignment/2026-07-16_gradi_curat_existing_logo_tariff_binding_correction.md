# 2026-07-16 — Gradi-curat existing logo tariff binding correction

## Starting HEAD

`983585b` on `feature/product-system-active-path-isolation-v1`

## Exact binding root cause

Linked-logo CPP rules `logo_print` / `logo_laminate` / `logo_application` had:

- `documented_unit_price=None`
- `owner_decision_required=True`
- no `registry_pricing_code` mapping

CPP never looked up Pricing Registry / `workcenter_rates`. Fail-closed null prices were treated as “owner must invent new tariffs,” but owner-confirmed operation rates already existed under letters template.

Defect class: **rule-class mapping / lookup mismatch** (not missing owner prices).

## Canonical tariff records reused

| Logo line | Registry key | UI name | Value | Currency | Unit | Status |
|-----------|--------------|---------|-------|----------|------|--------|
| print | `LARGE_FORMAT_PRINT` | Serviciu print autocolant | 8.50 | EUR | mp | owner-confirmed / active |
| laminate | `LAMINATION` | Serviciu laminare print | 5.00 | EUR | mp | owner-confirmed / active |
| application | `FACE_VINYL_APPLICATION_LABOR` | Manoperă aplicare folie fețe litere | 5.00 | EUR | mp | owner-confirmed / active |

Explicitly **not** used: `SVC-LAMINATION-SERVICE` (Lipsă / buc stub).

No duplicate registry rows created. Mapping via `CommercialRuleDefinition.registry_pricing_code` only.

## Currency gate result

**Outcome A** — canonical conversion exists:

- Source: `company_commercial_settings.eur_to_ron_rate` via `get_eur_to_ron_rate(db)`
- Live value: **5.0** (same settings endpoint used by dry-run / order handoff)
- Not hardcoded in the commercial logo path
- Fail-closed if rate missing/invalid (`BLOCKED_BY_CANONICAL_CURRENCY_CONVERSION` warning + null unit price)

Normalized RON unit prices: print **42.5**, laminate **25.0**, application **25.0**.

## Quantity proof (workspace `11891d68-…`)

Per logo face area ≈ **0.40023 m2** (artwork finish / box; not letter face 1.2638 m2).

| Line | Qty | Unit price RON | Subtotal |
|------|-----|----------------|----------|
| logo_print::logo_instance_001/002 | 0.40023 | 42.5 | 17.0098 each |
| logo_laminate::… | 0.40023 | 25.0 | 10.0057 each |
| logo_application::… | 0.40023 | 25.0 | 10.0057 each |

Delta vs pre-binding line sum: **+74.0424 RON** (= 2 × 0.40023 × 92.5).

## Before / after CPP

| Metric | Before | After |
|--------|--------|-------|
| Print/lam/app unit prices | null | registry-bound RON |
| Proposal line sum | 2439.5202 | 2513.5626 |
| commercial_totals net/VAT/gross | null | null (montaj missing) |
| Blockers | MONTAJ + LOGO_PRINT/LAMINATE/APPLICATION + REVIEW | **MONTAJ** + REVIEW only |
| Letter body / logo body+LED | unchanged | unchanged |
| Internal MB | 725.16 EUR | 725.16 EUR |
| contains_missing_prices | false | false |

## Unchanged registry values

Pre/post `GET /api/v1/pricing/registry`: 50 items; LARGE_FORMAT_PRINT / LAMINATION / FACE_VINYL_APPLICATION_LABOR / SVC stub values and statuses identical. Browser UI still shows 8,50 / 5,00 / 5,00 EUR/mp.

## Site-install blocker

`MONTAJ_COMMERCIAL_RULE` — site installation selected; no owner-confirmed șantier tariff; configure at `/inventory/pricing`; Confirmare remains disabled.

## Tests

- `tests/test_commercial_price_proposal_logo_registry_binding.py` + linked-logo suite: **23 passed**
- Covers registry binding, stub rejection, currency gate, montaj fail-closed, letter non-regression, no duplicates

## Review findings

See session review: hourly false-positive on `workcenter_rates` substring fixed with word-boundary scan + source label `pricing_registry:operation:…`.

## Files changed

- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/services/linked_logo_commercial_price_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/schemas/commercial_price_proposal.py`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/tests/test_commercial_price_proposal_logo_registry_binding.py`
- docs/qa probes + this worklog + decision-log

## Remaining owner decision

**TRUE_OWNER_TARIFF_MISSING — SITE INSTALLATION** only.

- Proposed class: new commercial operation (no existing șantier row)
- Unit options supported today: fixed / `locatie` (CPP `montaj` basis)
- Do not invent numeric value

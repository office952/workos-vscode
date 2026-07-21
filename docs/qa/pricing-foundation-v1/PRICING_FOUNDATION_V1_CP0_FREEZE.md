# PRICING_FOUNDATION_V1 — CP0 Source and Classification Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Kickoff HEAD | `46c22c16` |
| Owner GO | Hybrid Option C — implement PRICING_FOUNDATION_V1 only |
| Mode | Implementation after freeze |

## Frozen ownership

| Surface | Route | Owns |
|---------|-------|------|
| Inventory | `/inventory` | material identity, category, stock, purchase cost, supplier, unit, status |
| Pricing catalogs | `/inventory/pricing` | typed views over reusable rates (no new physical registry table) |
| Product System Preturi Template-uri | future | **out of scope** |

## Frozen source tables

- `inventory_materials` — materials + purchase `unit_cost`
- `workcenter_rates` — machine / labor / service rates (single table; typed in application)
- `commercial_markup_policies` — markup (unchanged; empty OK)

## Frozen typed catalog categories

| `typed_catalog` | Meaning | Source |
|-----------------|---------|--------|
| `material` | Material purchase cost | `inventory_materials` |
| `machine_operation` | CNC / utilaj | `workcenter_rates` |
| `labor` | Manoperă | `workcenter_rates` |
| `service` | Serviciu / montaj / print | `workcenter_rates` |
| `unknown` | Needs classification | fallback |
| `markup_rule` | Adaos | markup policies |

Keep legacy `pricing_kind` (`material` / `operation_rate` / `markup_rule`) for readers.

## Frozen null-stock semantics

```text
stock_current = null  → Stoc neurmărit (untracked) — NOT zero, NOT Epuizat
stock_current = 0     → Epuizat (confirmed)
stock_current > 0     → În stoc / OK / Scăzut / Critic by min thresholds
```

Price missing ≠ stock exhausted.

## Frozen no-migration boundary

- Do not rewrite `workcenter_rates` values or bases
- Do not invent prices
- Do not unblock ACM / treatment commercial lines
- Do not implement Template Pricing Studio
- No Alembic / schema migration

## Rate-basis defect policy

Detect + warn when declared `rate_basis` does not match the populated column
(`rate_per_hour` vs `rate_per_linear_meter`; `per_square_meter` / `per_piece` have no dedicated column).
Do not auto-correct.

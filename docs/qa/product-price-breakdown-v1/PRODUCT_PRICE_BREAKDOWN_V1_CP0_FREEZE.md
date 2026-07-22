# PRODUCT_PRICE_BREAKDOWN_V1 — CP0 Contract Freeze

| Field | Value |
|-------|--------|
| Kickoff HEAD | `b8c6e8a8` |
| Prior | TEMPLATE_ACTIVATION_V1 PASS_WITH_WARNINGS |
| Proof port | `:8020` |
| Architecture | **Read-model adapter** — not a second calculator |

## Authority (frozen)

| System | Role |
|--------|------|
| CPP (`CommercialPriceProposalService`) | Commercial calculation authority |
| EIC (`EstimatedInternalCostService`) | Internal cost + provenance authority |
| Template Pricing Studio recipe | Structural composition + AI defaults |
| Price Breakdown | Explains / projects the above |

## Endpoint (frozen)

```text
POST /api/v1/product-system/templates/{code}/price-breakdown
body: { workspace_id?, quote_input?, currency?, fixture_id? }
```

Built-in fixture IDs for Studio without workspace:

- `vl_letters_demo_v1`
- `acm_shell_demo_v1`
- `logo_demo_v1` (may be partial)
- `volum_aluminiu_demo_v1` (child-scoped)

## Line groups (frozen)

`material` · `machine` · `labor` · `service` · `ai_decision` · `adjustment` · `commercial` · `internal`

## Totals (frozen)

- Internal: from EIC (`estimated_*_cost`, `estimated_total_internal_cost`)
- Commercial: from CPP (`subtotal_commercial`, `commercial_total`)
- Reconciliation flags: `cpp_total_matches`, `eic_total_matches`, `no_duplicate_lines`

## Material / labor / time

- Materials: inventory/purchase truth only — never invent market prices
- Labor: physical drivers; display operator language
- Time: capacity hints secondary only (`excluded_from_total`)

## UI placement

Product System → Prețuri template → section **Desfășurător preț** (after recipe / before or after structural CPP cards).

## Boundaries

No DB migration · no formula mutation · no publication changes · no artwork parser · no Execution · no push/PR

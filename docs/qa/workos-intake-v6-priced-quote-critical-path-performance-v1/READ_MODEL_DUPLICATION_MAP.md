# READ_MODEL_DUPLICATION_MAP

Step 2 after discrete commercial-affecting change (measured):

```text
PUT finish-setup
GET material-breakdown
GET pricing-input-preview
GET priced-quote-dry-run
GET quote-handoff-preview
GET logical-list-read-model
(+ occasional product-system-binding / ai-informational-assist — not production/task)
```

## Overlaps inside `priced-quote-dry-run` vs siblings

| Computation | Sibling endpoint | Classification | Notes |
|---|---|---|---|
| `build_v6_pricing_input_preview` | `pricing-input-preview` | **B SHAREABLE_WITHIN_REQUEST** / **A REQUIRED_DUPLICATION** across requests | Same workspace truth; separate HTTP requests cannot share without cache. Kept inside pricedQuote — canonical quote_input for CPP. |
| `get_material_breakdown_for_workspace` | `material-breakdown` | **D DIAGNOSTIC_ONLY** for official offer → **removed from default critical path** | Was recomputed inside pricedQuote solely for EIC/cost-plus traces. Step 2 UI letters cost comes from sibling GET. |
| CPP `build_preview` | (none for money) | **A REQUIRED** | Canonical official commercial authority. |
| EIC `build_preview` | material-breakdown / LiveCalculationSummary | **D DIAGNOSTIC_ONLY** for Ofertă → **removed from default critical path** | Opt-in for write/snapshot. |
| Diagnostic cost-plus + FX | — | **D DIAGNOSTIC_ONLY** → **removed from default critical path** | Must not block EUR official offer. |
| VAT settings read | settings | **A REQUIRED** | Official totals need VAT %. |
| Manual RON FX | settings | **A REQUIRED** when manual ≠ 0 | Policy unchanged. |
| Nested dry-run in `logical-list-read-model` | priced-quote-dry-run | **E LEGACY_REDUNDANT** / contention amplifier | Still calls `build_intake_v6_priced_quote_dry_run` again under fan-out. Out of OPTION B scope; residual latency source. |

## Decision

OPTION B: stop paying MB/EIC/cost-plus on the official GET critical path.  
Do **not** invent FE money. Do **not** add global cache.

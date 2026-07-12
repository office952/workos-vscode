# Intake V6 — Logo operation internal cost v1

**Task:** INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1  
**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT  
**Accepted HEAD before:** 49896b2  
**Branch:** main  
**Compound folder:** `.compound-engineering/intake-v6-logo-operation-internal-cost-v1/`

## Owner decisions

- **DEC-LOPS-ARCH-01:** Logo BOM ops only + thin EIC mapper; letters on `RULES_BY_TEMPLATE`.
- **DEC-LOPS-01:** Blocker-only mode — no numeric logo operation rates, no DEV_BRIDGE_LOGO_*.

## Gap closed

EIC ignored `bom.costable_operations`. Logo namespaced operations now map to `estimated_operation_lines` with quantity when canonical, explicit rate blockers otherwise.

## Architecture

```text
Letters: RULES_BY_TEMPLATE (unchanged)
Logo: bom.costable_operations → _is_linked_logo_bom_operation → EIC lines/blockers
```

## Blocker-only behavior

- Operation identity, segment ref, quantity preserved when available.
- `INTERNAL_OPERATION_RULE_MISSING` when no canonical internal rate.
- `subtotal=None` — never zero fallback.
- No workcenter hourly consumption.

## Tests

| Batch | Pass |
|---|---:|
| EIC logo + workspace + preview | 51 |
| Cost BOM + PA + gradi + binding + return/cant + pricing keys | 57 |
| selected_layer_refs (isolated) | 5 |

## Remaining debt

Canonical numeric internal operation rates for workspace-linked logo operations are not configured.

## Next safe step

**INTAKE_V6_LOGO_OPERATION_INTERNAL_RATE_CATALOG_V1** — owner-defined internal unit costs per logo `operation_code` in `internal_cost_rules_volumetric_v2` (or Step 7I registry). Do not proceed to CommercialPriceProposal until owner approves rates or explicitly waives operation costing.

## Direction score

**90/100** — structure mapped; numeric truth deferred by design.

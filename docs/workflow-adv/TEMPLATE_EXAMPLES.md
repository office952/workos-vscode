# Template Examples

## Purpose
Show the reference examples that anchor Workflow-ADV contracts. These examples illustrate ownership and readiness; they are not a catalog-duplication recipe or a promise that every template is complete.

## Ownership

| Example | Canonical ownership |
|---|---|
| VL root | Root composition, request scope, and aggregate Product System path |
| Volum Aluminiu child | Bounded technical truth, inputs, quantities, and referenced resources |
| ACM shell | Published constrained shell; treatments remain a declared limitation |
| Logo | Incomplete example; not a root-ready reference |
| PSU selector/variants | Inventory owns identity; Pricing owns concrete-variant purchase truth |

## Invariants

| Example | Canonical facts | Prohibited inference |
|---|---|---|
| VL root | `TPL-VOLUMETRIC-LETTERS_v2` is the complete reference root and uses `vl_letters_demo_v1` | A root duplicates child technical material/process ownership |
| Volum Aluminiu child | Child owns its technical inputs, quantities, material/process references, and separate-calc slice | Parent-owned cant/material duplication or treating child as an independent published root |
| ACM shell | `acm_shell_demo_v1` proves a bounded shell; treatments are blocked and CPP may be null | Claiming full ACM capability or commercial completion |
| Logo | `logo_demo_v1` may show an honest preview; it has no root CPP/EIC completion claim | Publishing Logo as a complete reference template |
| PSU selector | `MAT-LED-PSU-12V` is a `VARIANT_SELECTOR`, not a priced SKU | Adding generic price or stock as a purchasable material |
| PSU variants | `-60W`, `-100W`, `-160W`, `-200W` are concrete variants; VL fixture resolves `-100W` | Selecting a wattage without confirmed configuration |

- A parent composes; a child owns bounded technical truth. Neither may silently recreate the other’s cost inputs.
- Example availability is not a lifecycle substitute. The Readiness and Lifecycle contract decides whether the specific version/configuration may make a scoped claim.
- JIT catalog rules still apply: examples do not justify seeding unrelated materials, processes, labor, or services.

## Evidence

| Evidence | Example outcome |
|---|---|
| `docs/qa/product-price-breakdown-v1/` | VL: 42 lines, EIC `923.20`, CPP `1061.00`; Volum Aluminiu: separate child evidence; ACM/Logo limitations explicit |
| `docs/qa/product-system-reference-complete/` | VL root complete, Volum Aluminiu usable with gaps, Logo incomplete |
| `docs/qa/active-template-critical-material-fill-v1/` | VL selects `MAT-LED-PSU-12V-100W` at owner-confirmed evidence |
| Critical-fill commit `7bdd9f61` | PSU selector is cleared from false critical status |

## Limitations
- The examples are a reference suite, not a universal product taxonomy.
- ACM treatments, Logo root completion, visual add-child authoring, and generic Form Builder remain deferred or incomplete.
- The numeric fixture values are evidence for reconciliation, not portable default prices/rates.

## Do-not-transfer
- Do not transfer hard-coded VL pages or template-specific UI branches as the extensibility model.
- Do not transfer ACM shell publication as proof of treatment capability.
- Do not transfer Logo preview as production readiness.

## Related docs
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
- [Test Fixtures](TEST_FIXTURES.md)
- [Inventory and Material Contract](INVENTORY_AND_MATERIAL_CONTRACT.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)

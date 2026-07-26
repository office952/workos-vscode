# Child Template composition

## Purpose
Define root/child composition without duplicated technical or cost truth.

## Ownership
The root Product Template owns role composition and input mapping. Each child Product Template owns its bounded technical truth, resources, quantities, and formulas.

## Composition matrix
| Concern | Root | Child |
|---|---|---|
| Product role/placement | owns | receives assigned role |
| Child selection/link | owns | does not self-attach |
| Shared input mapping | maps confirmed input | consumes mapped input |
| Technical implementation | must not duplicate | owns |
| Resource references | references only for its scope | references only for its scope |
| Quantity/formula | must not recalculate child truth | owns its formula outputs |
| EIC lines | aggregates explainably | emits its scoped recipe lines |

The VL reference root `TPL-VOLUMETRIC-LETTERS_v2` composes `TPL-VOLUM-ALUMINIU_v1`. The child owns return/cant technical truth; the parent maps confirmed perimeter and depth inputs.

## Invariants
- Parent does not duplicate child truth, material selection, quantity, or formula.
- One technical fact has one source of truth and one formula owner.
- Child inputs come from confirmed PT, not unconfirmed Analyzer output.
- A child can be reused only through a Product Template link and declared role/usage mode.

## Evidence sources
- `GET .../reference-finish-line/contract`
- `POST .../templates/{code}/price-breakdown`
- `docs/qa/product-system-reference-complete/runtime/reference_complete.json`

## Limitations
The reference has no visual add-child UI; add-child remains API/seed authoring. Broader child catalogs beyond the VL pilot are future work.

## Do-not-transfer
Do not copy cant/return truth into the parent, create a ComponentTemplate clone, or let a parent-side UI calculator become a second owner.

## Related docs
- [Domain model](DOMAIN_MODEL.md)
- [Template authoring](PRODUCT_TEMPLATE_AUTHORING.md)
- [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
- [Quantity and Formula contract](QUANTITY_AND_FORMULA_CONTRACT.md)

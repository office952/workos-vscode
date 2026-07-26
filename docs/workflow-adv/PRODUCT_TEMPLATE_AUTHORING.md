# Product Template authoring

## Purpose
Specify safe authoring of canonical Product Templates and just-in-time catalog growth.

## Ownership
Workflow-ADV owns authoring. A Product Template owns technical scope, declared schema, composition links, and formulas; catalog owners retain resource identity, compatibility, and rates.

## Authoring Option 2
| Action | Current reference contract | Platform implication |
|---|---|---|
| Create/edit/publish template | supported contract | preserve versioned authoring |
| Update existing composition links | UI-capable | retain as normal operator/admin action |
| Add child link | API/seed only | visual factory deferred |
| Visual template factory | deferred | do not infer it from Lab UI |

## JIT catalog gate
| Gate | Required decision |
|---|---|
| 1. Declare need | Identify material, process, labor, service, consumable, or packaging requirement. |
| 2. Search canonical catalog | Reuse an existing compatible canonical resource where present. |
| 3. Fill only the gap | Create the missing canonical resource with identity/provenance/rate ownership. |
| 4. Reference it | Template stores a reference and quantity/formula relation, never local price authority. |
| 5. Validate | Confirm critical coverage, variant selection, formula ownership, and EIC output. |

## Invariants
- Do not pre-create speculative catalogs.
- Do not invent a local material, process rate, labor rate, or service price inside a template.
- `MAT-LED-PSU-12V` is a selector only. Resolve a concrete 60/100/160/200W variant before pricing.
- A new child is a Product Template with `usage_mode=child` or `dual-role`, not a new entity type.
- DEV MODE creates a new version; FREEZE ON versions are not mutated in place.

## Evidence sources
- `GET .../reference-finish-line/contract`
- `GET .../critical-materials`
- `GET /api/v1/pricing/material-market-prices`
- `docs/qa/product-system-reference-complete/runtime/reference_complete.json`

## Limitations
Visual add-child and a full template factory are deferred. Supplier Import is deferred; it cannot be substituted with invented catalog records.

## Do-not-transfer
Do not transfer API/seed-only add-child mechanics as a claim that a visual factory exists, or hardcoded template-code pages as the authoring model.

## Related docs
- [Domain model](DOMAIN_MODEL.md)
- [Child composition](CHILD_TEMPLATE_COMPOSITION.md)
- [Quantity and Formula contract](QUANTITY_AND_FORMULA_CONTRACT.md)
- [Overview](WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW.md)

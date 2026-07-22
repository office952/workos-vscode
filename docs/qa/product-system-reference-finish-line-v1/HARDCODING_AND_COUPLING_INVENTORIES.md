# Hardcoding and Coupling Inventories

Source of truth (runtime): `GET .../reference-finish-line/contract`

## Template-code branches

| Location | Classification | Handoff |
|----------|----------------|---------|
| form_system_contract_backbone_service template sets | valid product-specific adapter | ready |
| intake_v6 PILOT_TEMPLATE VL | technical debt | gap |
| Intake V6 specialized UI | valid product-specific adapter | gap (reference only) |
| ACM adapters | technical debt | do_not_transfer_as_universal |

## Field hardcoding

| Location | Classification | Handoff |
|----------|----------------|---------|
| VOLUMETRIC_FIELD_BINDINGS | vl_specific_schema | ready_as_template_schema |
| specialized letter_groups / montaj | vl_specific_ui | gap |
| CostEngine Step 7 undeclared names | technical debt | gap (do not broaden here) |

## Formula duplication

| Topic | Classification | Note |
|-------|----------------|------|
| CPP vs EIC | intentional dual read-model | EIC = lab stop |
| FE finish display | display only | no second calculator |
| Parent vs Volum Aluminiu cant | watch | child owns return truth |

## Cross-module coupling

| Topic | Classification |
|-------|----------------|
| Product System → Inventory | reference only |
| Pricing → template truth | read-model ok |
| Intake owning formulas | blocker if expanded |
| Analyzer inside WorkOS | boundary frozen (consume-only) |

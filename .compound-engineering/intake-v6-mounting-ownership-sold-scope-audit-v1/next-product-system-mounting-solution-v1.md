# Next bounded task — Product System mounting solution selection

**Prerequisite:** INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1 (mounting_scope commercial gate)  
**Owner GO required:** Yes — do not implement without explicit approval

## Problem

Metal premount bars and boxed ACM mounting support must not remain local Intake enums (`mounting_system`, `mounting_bar_profile`). Product System must own materials, operations, formulas, and execution truth.

## Templates today

| Template | Status | Safe for Intake reference? |
|---|---|---|
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | **Seeded, operational** linked optional module on letters | **Partial** — activates via `metal_support_required` bridge from legacy `mounting_system`; not yet a first-class Intake picker |
| `TPL-COMP-LETTER-MOUNTING_v1` | **Inert** component-first candidate (`activation_guard`, no executable BOM) | **No** — contract only |
| Boxed ACM mounting support template | **Missing** | **No** — `acm_panel` enum is capture-only on letters template |

## Required binding contract (proposal)

```text
finish_setup.mounting_solution_template_code  →  product_templates.template_code
finish_setup.mounting_solution_config         →  template-specific variant JSON (from dossier)
```

Intake V6 **Pregătire** section when `mounting_scope ∈ {preparation_only, preparation_and_site_installation}`:

1. Operator selects one allowed mounting solution from parent template module links / catalog.
2. Config fields come from selected template form contract — not duplicated in `finish_setup`.
3. Legacy `mounting_system` / `mounting_bar_profile` remain read-only migration display until workspace migrated.

## Deferred from scope foundation V1

- Editable `mounting_system` / `mounting_bar_profile` (prevented — read-only legacy display)
- New local booleans for bars vs ACM
- ACM boxed solution (no template)
- Activation of `TPL-COMP-LETTER-MOUNTING_v1`

## Suggested /ce-work title

`PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1`

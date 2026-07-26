# Intake V6 Layer Role Taxonomy Contract

## Scope

This contract defines the owner-facing layer role taxonomy for Intake V6 Step 1 / Step 2 / Step 3 in the volumetric letters + logo composition context.

## Owner Decision

For the current volumetric letters + logo context, the only owner-facing layer roles are:

- Vector Litere
- Vector Logo

No other role labels are allowed in the Step 1 role dropdown for this context.

## Context

The canonical test file is:

`C:\Users\offic\workos_app_vs\fisiere-teste-svg\gradi-curat.svg`

Expected analyzer composition:

- `TPL-VOLUMETRIC-LETTERS_v2`
  - layers 1-4 / text-letter layers
  - owner-facing role: Vector Litere
- `TPL-VOLUMETRIC-LOGO_v1`
  - logo-stanga
  - logo-dreapta
  - owner-facing role: Vector Logo

## Separation of Concepts

The system must keep these concepts separate:

1. Owner-facing layer role
   - Vector Litere
   - Vector Logo
2. Product System target template
   - `TPL-VOLUMETRIC-LETTERS_v2`
   - `TPL-VOLUMETRIC-LOGO_v1`
3. Internal analyzer / legacy role value
   - may still use internal values such as `printed_artwork` or legacy artwork terms
   - these must not leak as primary operator labels
4. Form System field group
   - must be derived from confirmed layer role + target template
5. Product Truth
   - must store confirmed layer role and target template separately

## Mapping

| Target template | Owner-facing role | Meaning |
|---|---|---|
| `TPL-VOLUMETRIC-LETTERS_v2` | Vector Litere | Letter/text vectors that feed the volumetric letters form/system |
| `TPL-VOLUMETRIC-LOGO_v1` | Vector Logo | Logo/symbol/non-letter vectors that feed the volumetric logo form/system |

## UI Contract

For context:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`

Step 1 dropdown must contain exactly:

- Vector Litere
- Vector Logo

Forbidden in this context:

- Vector Atipic
- Vector Atipic / logo
- Vinil aplicat
- Cant / volum
- Spate / backing
- Fundal / suport / bond / caseta
- Decupaj interior
- Gauri montaj
- Referinta / ghidaj
- Ignora strat
- De confirmat
- Recomandate / Alte roluri optgroups

## Analysis Panel Contract

For the volumetric letters + logo context, `Atentie analiza` must use the same owner-facing taxonomy as Step 1 layer decisions:

- Vector Litere
- Vector Logo

It must not expose legacy/internal/operator-confusing terms as primary labels:

- Vector Atipic
- Vector Atipic / logo
- artwork candidate
- stroke-only vector
- logo/artwork candidate

The panel is explanatory only. It must not define a separate role taxonomy from `Decizii straturi`.

## Form System Link

Form System must create the required fields from Product System / component contracts using:

- confirmed owner-facing role;
- target template;
- source/state of each field.

It must not rely on a global UI dropdown as source of truth.

## Product Truth Link

Product Truth must store:

- confirmed layer role:
  - Vector Litere
  - Vector Logo
- target template:
  - `TPL-VOLUMETRIC-LETTERS_v2`
  - `TPL-VOLUMETRIC-LOGO_v1`
- source/state:
  - analyzer suggested;
  - operator confirmed;
  - fallback/manual/etc. where applicable.

## Gradi-curat Expected Behavior

`gradi-curat.svg` must be calculated through cooperation between:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`

It must not be treated as:

- only Letters;
- only Logo;
- two independent offerable products.

It is one composed Intake V6 product truth.

## Non-goals

This contract does not:

- activate Logo as separate quote/order root;
- change pricing;
- change nesting/material consumption;
- change ProductDefinition;
- change Quote/Order;
- change Execution/TaskGraph/ProductAggregate;
- change analyzer composition.

## Acceptance Criteria

- UI real pe `gradi-curat.svg`;
- Layer 1-4: Vector Litere;
- Layer 5-6: Vector Logo;
- every dropdown contains exactly:
  - Vector Litere
  - Vector Logo;
- no global role list in this context;
- analyzer composition remains Letters + Logo;
- tests pass;
- no forbidden downstream changes.
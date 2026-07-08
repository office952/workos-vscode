# RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION_V1

Date: 2026-07-08
Project: WorkOS
Mode: docs-only / path canonicalization

## 1. Safety gate

Comenzi rulate:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git diff --check
```

Rezultat:

- accepted HEAD: `4c22e4f`
- staged files inainte de lucru: none
- diff format blockers: none
- untracked parked lanes: prezente, neatinse
- verdict: se poate continua

## 2. Decision

Decizia finala a acestui task:

```text
RETURN_CANT_CANONICAL_PATHS_READY_FOR_MAPPER_IMPLEMENTATION
```

Interpretare:

- runtime-ul nu este inca implementat pe path-urile tinta;
- dar schema path-urilor este acum suficient de precisa pentru un pas urmator de implementare a mapperului read-only.

## 3. Scope chosen

Varianta aleasa:

```text
docs-only canonicalization contract
```

Nu s-a adaugat cod.

## 4. Canonical schema covered

Schema definita contractual:

```text
components.return_cant
  depth_mm
  material_profile
  finish_type
  color_target.oracal_code
  color_target.ral_code
  color_target.paint_target
  layer_group_ids
  confirmation_state
  perimeter_source
  perimeter_dependency.face_confirmed_perimeter.*

components.face.confirmed_perimeter
  value
  unit
  source_state
  source_path
  layer_group_ids
  confirmation_state
```

## 5. Existing runtime evidence

Exista in runtime, dar necanonic sau incomplet:

- `components.return.depth_mm`
- `components.returnCant.depthMm`
- `finish_setup.return_finish_type`
- `finish_setup.return_oracal_code`
- `quote_geometry.letter_perimeter_m`
- `svg.selected_layer_refs[]`

Lipsesc complet ca path-uri canonice:

- `components.face.confirmed_perimeter.*`
- `components.return_cant.material_profile`
- `components.return_cant.finish_type`
- `components.return_cant.color_target.*`
- `components.return_cant.layer_group_ids`
- `components.return_cant.confirmation_state`
- `components.return_cant.perimeter_source`
- `components.return_cant.perimeter_dependency.face_confirmed_perimeter.*`

## 6. Hard rules confirmed

Confirmat:

- `quote_geometry.letter_perimeter_m` poate fi numai context sau fallback
- `return_cant.perimeter_dependency.face_confirmed_perimeter` este dependency explicita, nu derivare locala din root geometry
- `layer_group_ids` trebuie sa vina din operator-confirmed layer/group selection
- `confirmation_state = confirmed` este obligatoriu pentru preview ulterior
- ProductDefinition-derived poate fi numai consequence downstream

## 7. No-code confirmation

Confirmat:

- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB / seed / migration
- fara UI
- fara endpoint public nou

## 8. Validation

Validare rulata:

- safety gate initial
- citire docs relevante
- inspectie read-only in cod
- validare finala `git diff --check`
- confirmare docs-only diff

Nu au existat teste de rulat deoarece nu s-a atins cod.

## 9. Recommended next prompt

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1
```
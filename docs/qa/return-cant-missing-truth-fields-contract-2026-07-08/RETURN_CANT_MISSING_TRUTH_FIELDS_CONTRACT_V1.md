# RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT_V1

Date: 2026-07-08
Project: WorkOS
Mode: docs-only / contract definition

## 1. Safety gate

Comenzi rulate:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git diff --check
```

Rezultat:

- accepted HEAD: `122d3f8`
- staged files inainte de lucru: none
- tracked diffs inainte de lucru: none
- untracked parked lanes: prezente
- verdict: se poate continua docs-only

## 2. Scope

Acest task defineste contractul pentru field-urile lipsa ale `return_cant`.

Acest task nu:

- implementeaza preview-ul;
- calculeaza componenta;
- activeaza component root;
- activeaza component quote;
- creeaza UI nou;
- creeaza endpoint runtime;
- modifica Pricing / Quote / Order / Execution;
- modifica ProductAggregate / TaskGraph / ExecutionPlan;
- modifica DB / seed / migration.

## 3. Decision

Decizia finala a acestui task:

```text
RETURN_CANT_TRUTH_FIELDS_CONTRACT_READY
```

Contractul este gata pentru implementare ulterioara, dar runtime-ul nu este inca gata pentru preview.

## 4. Fields definite

Fields definite contractual:

- `return_cant.material_profile`
- `return_cant.perimeter_source`
- `return_cant.perimeter_dependency.face_confirmed_perimeter`
- `return_cant.color_target.oracal_code`
- `return_cant.color_target.ral_code`
- `return_cant.color_target.paint_target`
- `return_cant.layer_group_ids`
- `return_cant.confirmation_state`

## 5. Product Truth paths and source/state required

Rezumat:

- `components.return_cant.material_profile` -> required state `confirmed`
- `components.return_cant.perimeter_source` -> required state `confirmed`
- `components.return_cant.perimeter_dependency.face_confirmed_perimeter` -> required state `confirmed`
- `components.return_cant.color_target.oracal_code` -> `confirmed` cand finish-ul cere Oracal
- `components.return_cant.color_target.ral_code` -> `confirmed` cand finish-ul cere RAL
- `components.return_cant.color_target.paint_target` -> `confirmed` cand finish-ul cere paint
- `components.return_cant.layer_group_ids` -> `confirmed`
- `components.return_cant.confirmation_state` -> `confirmed`

## 6. Blockers ramasi

Runtime blockers ramasi:

- `RETURN_CANT_MATERIAL_MISSING`
- `RETURN_CANT_PERIMETER_MISSING`
- `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`
- `RETURN_CANT_COLOR_TARGET_MISSING`
- `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING`
- `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED`

## 7. Face/perimeter dependency

Dependency obligatorie:

```text
return_cant.perimeter_dependency = face.confirmed_perimeter
```

Regula:

- daca exista doar `quote_geometry.letter_perimeter_m`, verdictul ramane blocat;
- daca exista doar suggestion din SVG, verdictul ramane blocat;
- doar dependency explicita confirmed poate debloca preview-ul.

## 8. No-code confirmation

Confirmat:

- fara code changes;
- fara UI;
- fara endpoint;
- fara component root;
- fara component quote;
- fara Logo offerability;
- fara Pricing;
- fara Quote/Order;
- fara Execution;
- fara ProductAggregate;
- fara TaskGraph;
- fara ExecutionPlan;
- fara DB/seed/migration.

## 9. Recommended next prompt

Prompt recomandat:

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_SLICE_V1
```
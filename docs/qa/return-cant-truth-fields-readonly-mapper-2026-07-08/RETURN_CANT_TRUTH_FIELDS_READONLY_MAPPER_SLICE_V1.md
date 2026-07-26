# RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_SLICE_V1

Date: 2026-07-08
Project: WorkOS
Mode: docs-only / mapper contract

## 1. Safety gate

Comenzi rulate:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git diff --check
```

Rezultat:

- accepted HEAD: `64a2a44`
- staged files inainte de lucru: none
- diff format blockers: none
- untracked parked lanes: prezente, neatinse
- verdict: se poate continua

## 2. Scope chosen

Varianta aleasa:

```text
docs-only mapper contract
```

Nu s-a implementat cod read-only in acest task.

## 3. Why code was not added

Check-ul local decisiv:

- `ProductTruthGeometryInput` nu include `quote_geometry.letter_perimeter_m`;
- `ProductTruthDraft` retine `return_material_perimeter_ml`, nu fallback context-ul cerut de contract;
- nu exista inca path read-only explicit pentru `components.face.confirmed_perimeter`;
- naming-ul canonic `components.return_cant.*` nu este inca prezent in read model-ul intern curent.

Concluzie:

```text
Un helper de cod introdus acum ar risca sa ascunda lipsurile reale prin remapare implicita.
```

## 4. Decision

Rezultatul pentru acest slice:

```text
RETURN_CANT_MAPPER_BLOCKED
```

Interpretare:

- contractul mapperului este gata;
- implementarea ramane blocata pana la o suprafata de input care poate raporta onest dependency-ul de perimetru.

## 5. Mapper output contract confirmed

Contractul defineste:

- `component_scope`
- `root_template`
- `root_type`
- `quote_mode`
- `fields[]`
- `dependencies[]`
- `blockers[]`
- `overall_readiness`

## 6. Required canonical rows covered

Fields acoperite contractual:

- `return_cant.material_profile`
- `return_cant.perimeter_source`
- `return_cant.perimeter_dependency.face_confirmed_perimeter`
- `return_cant.color_target.oracal_code`
- `return_cant.color_target.ral_code`
- `return_cant.color_target.paint_target`
- `return_cant.layer_group_ids`
- `return_cant.confirmation_state`

Dependencies acoperite contractual:

- `components.face.confirmed_perimeter`
- confirmed layer group evidence catre `components.return_cant.layer_group_ids`

## 7. Readiness rule confirmed

`overall_readiness = blocked` daca lipseste sau nu este `confirmed` oricare dintre:

- `material_profile`
- `perimeter_source`
- `perimeter_dependency.face_confirmed_perimeter`
- `layer_group_ids`
- `confirmation_state = confirmed`

Color gating:

- Oracal cere `color_target.oracal_code`
- RAL cere `color_target.ral_code`
- paint cere `color_target.paint_target`

## 8. No-code confirmation

Confirmat:

- fara cod
- fara UI
- fara endpoint
- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB / seed / migration

## 9. Validation

Validare rulata pentru acest task:

- safety gate initial
- citire docs relevante
- inspectie read-only in cod
- validare finala `git diff --check`
- confirmare docs-only diff

Nu au existat teste de rulat deoarece nu s-a atins cod.

## 10. Recommended next prompt

```text
RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_IMPLEMENTATION_V1
```
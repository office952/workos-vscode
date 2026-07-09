# RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1

## Verdict

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY
```

## Scope checked

- docs-only canonical runtime container contract
- no runtime bridge implementation
- no Product Truth writes
- no UI changes
- no Pricing changes
- no adapter changes
- no builder or backbone code changes
- no DB migration
- no seed run

## Accepted HEAD

- `7ac67fe`

## Decision summary

Contractul canonic pentru `components.return_cant` este gata de fixat. Auditul a confirmat ca lipsa curenta este de shape final, ownership si compatibility policy, nu de informatie minima sau de imposibilitate de definire a containerului.

Deciziile-cheie ale contractului:

1. target final = `components.return_cant.version + components.return_cant.instances.<instance_key>`;
2. `instance_key` final este prefixed stabil:
   - `letter_group:<group_key>`
   - `artwork_layer:<layer_key>`
3. `layer_group_ids` ramane camp de instanta, nu camp in `source_ref`;
4. `material_profile` ramane structural si nu dubleaza chei Pricing;
5. `components.returnCant` si `components.return.*` raman legacy/transitional only.

## Canonical shape summary

Containerul final documentat este:

- `components.return_cant.version = "v1"`
- `components.return_cant.instances.<instance_key>.instance_key`
- `components.return_cant.instances.<instance_key>.source_kind`
- `components.return_cant.instances.<instance_key>.source_ref.group_key | layer_key`
- `components.return_cant.instances.<instance_key>.layer_group_ids[]`
- `components.return_cant.instances.<instance_key>.material_profile.width_mm`
- `components.return_cant.instances.<instance_key>.finish_variant.*`
- `components.return_cant.instances.<instance_key>.pricing_keys.*`
- `components.return_cant.instances.<instance_key>.geometry.*`
- `components.return_cant.instances.<instance_key>.confirmation_state`
- `components.return_cant.instances.<instance_key>.blockers[]`

## Readiness summary

Containerul poate exista in `draft` sau `blocked` chiar daca finish-ul este prezent. El nu devine `confirmed` doar din:

- Pasul 1 confirmat;
- row `confirmed`;
- `finish_setup.confirmed`;
- `quote_geometry.letter_perimeter_m`.

Lipsa confirmed perimeter, component confirmation, layer group mapping sau pricing refs obligatorii trebuie sa lase instanta in `blocked`.

## Next recommended slice

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```

De ce:

- contractul structural este acum clar;
- adapterul readonly este stratul cel mai aproape de target paths-urile finale;
- el inca pastreaza trei targete Pricing legacy si chei brute de sursa care trebuie normalizate inainte de bridge write.

## Validation

- read-only audit only
- no tests required
- no build required
- `git diff --check`
- docs-only diff expected

## Next recommended prompt

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```# RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1

## Verdict

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY
```

## Scope checked

- docs-only canonical runtime container contract
- no runtime bridge
- no Product Truth writes
- no UI changes
- no Pricing changes
- no adapter changes
- no DB migration
- no seed run
- no Quote / Order / Execution

## Accepted HEAD

- `7ac67fe`

## Decision summary

Contractul canonic pentru `components.return_cant` poate fi definit acum.

Slice-ul este `READY` deoarece shape-ul final, regulile de `instance_key`, politica de compatibilitate si regulile minime de readiness pot fi fixate fara a scrie runtime.

Ce ramane blocat nu este contractul, ci implementarea:

1. writer-ul runtime nu exista inca;
2. `components.face.confirmed_perimeter` nu are inca sursa runtime canonica;
3. `confirmation_state` nu are inca semantics implementate;
4. readonly adapterul foloseste inca targete legacy de pricing;
5. builderul si backbone-ul inca citesc / emit forme legacy.

## Canonical contract summary

- target final: `components.return_cant`
- schema version: `v1`
- storage shape: per-instance map la `components.return_cant.instances.<instance_key>`
- supported source kinds:
  - `letter_group`
  - `artwork_layer`
- canonical instance sections:
  - `source_ref`
  - `layer_group_ids`
  - `material_profile`
  - `finish_variant`
  - `pricing_keys`
  - `geometry`
  - `confirmation_state`
  - `blockers`

## Key contract decisions

1. `layer_group_ids` este field canonic top-level al instantei;
2. `material_profile.pricing_key` nu devine field separat, pentru a evita dublarea fata de `pricing_keys.material_profile_width`;
3. `geometry.evidence_perimeter_m` poate tine evidence; `geometry.confirmed_perimeter_m` cere sursa confirmata distincta;
4. `confirmation_state` accepta numai:
   - `missing`
   - `draft`
   - `blocked`
   - `confirmed`

## Instance key rules summary

- `letter_group:<group_key>` pentru letter groups
- `artwork_layer:<layer_key>` pentru artwork layers
- lipsa lui `group_key` sau `layer_key` blocheaza write-safe instance creation
- index numeric instabil este interzis

## Compatibility policy summary

- `components.returnCant` = legacy / transitional only
- `components.return` = legacy backbone old path only
- `components.return_cant` = single final target
- future bridge may read legacy, but must not write final state in legacy paths
- no dual-write permanent

## Readiness rules summary

Containerul poate exista in `blocked` daca lipsesc:

- `layer_group_ids`
- confirmed perimeter
- component confirmation
- color code necesar pentru vinyl sau RAL
- pricing key reference necesara pentru variant

Containerul nu devine `confirmed` doar pentru ca exista:

- Step 1 confirmation
- row confirmed
- `finish_setup.confirmed`
- analyzer perimeter
- `quote_geometry.letter_perimeter_m`

## Validation

- read-only audit only
- docs-only change set
- `git diff --check`
- no tests required
- no build required

## Next recommended prompt

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```
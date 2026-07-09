# RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1

## Verdict

```text
RETURN_CANT_BRIDGE_BLOCKERS_ALIGNMENT_READY
```

## Scope checked

- docs-only blocker alignment plan
- no UI changes
- no Pricing changes
- no adapter changes
- no Product Truth writes
- no runtime bridge implementation
- no endpoint public nou
- no DB migration
- no seed run

## Accepted HEAD

- `6a60cd3`

## Decision summary

Planul de aliniere este gata. Auditul nu a mai gasit ambiguitati critice despre:

1. unde sunt blockerele;
2. cine le detine;
3. care este ordinea corecta a slice-urilor;
4. care este primul slice ce trebuie executat.

Implementarea runtime bridge ramane blocata, dar planul de aliniere nu mai este blocat.

## Blocker alignment map summary

- containerul canonic `components.return_cant.instances.<instance_key>` lipseste si este blocker structural principal;
- `components.face.confirmed_perimeter` lipseste ca runtime source canonic;
- `return_cant.confirmation_state` lipseste complet ca semantica explicita;
- modelul legacy `components.returnCant` necesita contract de compatibilitate, nu promotie tacita;
- backbone paths `components.return.*` trebuie realiniate la contractul final;
- readonly adapterul trebuie sa renunte la pricing targetele legacy;
- `layer_group_ids` au evidence partial, dar nu mapping canonic;
- `finish_setup.confirmed` si Pasul 1 trebuie separate explicit de component confirmation.

## Ordered next slices

1. `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`
2. `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`
3. `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1`
4. `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1`
5. `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_V1`

## First recommended slice

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1
```

Why first:

- defineste targetul final fara de care toate celelalte reguli ar ramane suspendate pe forme legacy;
- permite compatibilitate explicita cu `components.returnCant` fara sa il promoveze ca shape final;
- fixeaza cadrul pentru layer mapping, confirmation contract si perimeter source contract.

## Validation

- read-only audit only
- `git diff --check`
- docs-only diff
- no tests required
- no build required

## Next recommended prompt

```text
RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1
```
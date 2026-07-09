# RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1

## Verdict

```text
RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_READY
```

## Scope

Docs-only / contract-only slice for `return_cant` component confirmation semantics.

Allowed:

- architecture contract docs;
- QA note;
- worklog.

Forbidden in this slice:

- no runtime writer
- no Product Truth writes
- no UI changes
- no Pricing changes
- no adapter changes
- no runtime DB changes
- no seed run
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB migration

## Safety gate

- HEAD confirmed: `2068699`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

## Audit summary

Current confirmation-like signals found in code:

1. Step 1 layer confirmation via `layer_role_setup.confirmation_status` and per-layer `confirmation_state`.
2. Finish setup confirmation via `finish_setup.confirmed`.
3. Row confirmation via `letter_group_finishes[].confirmed` and `artwork_finishes[].confirmed`.
4. Product composition confirmation via `product_composition_confirmed.confirmed`.
5. Internal draft quote confirmation via `finish_setup.internal_draft_quote_confirmed`.
6. Product Truth draft fields with state `confirmed`, `hydrated`, `fallback`, `blocked`, but no canonical runtime field yet for `components.return_cant.instances.<instance_key>.confirmation_state`.

Key finding:

```text
there is no existing owner-safe canonical component confirmation field for return_cant runtime instances
```

## Decision summary

Final runtime contract is ready and should use:

```text
components.return_cant.instances.<instance_key>.confirmation_state
```

Allowed values:

- `missing`
- `draft`
- `blocked`
- `confirmed`

Optional companion field:

```text
confirmation_source
```

Allowed final `confirmation_source` values:

- `operator_component_confirmation`
- `system_migration_verified`
- `imported_verified_truth`

Disallowed as final confirmation source:

- `step1_layer_confirmation`
- `finish_setup_confirmation`
- `row_confirmation`
- `analyzer_evidence`

## Required conditions for `confirmed`

`return_cant` may become `confirmed` only if all are true:

1. stable `instance_key`
2. valid `source_kind`
3. valid `source_ref`
4. valid `layer_group_ids` or equivalent final mapping
5. valid `material_profile.width_mm`
6. valid `finish_variant.type`
7. required pricing keys present for the chosen finish variant
8. valid `geometry.confirmed_perimeter_m`
9. explicit component confirmation action
10. allowed `confirmation_source`
11. no active blockers

## Cannot set confirmed

The following are explicitly insufficient on their own:

- Step 1 confirmed
- layer role selected
- `finish_setup.confirmed`
- row confirmed
- Oracal selected
- RAL selected
- stock color selected
- pricing keys present
- analyzer perimeter present
- `quote_geometry.letter_perimeter_m` present
- product composition confirmed
- internal draft quote confirmed

## Signal matrix summary

- Step 1 / layer role / row / finish setup / product composition = workflow or selection signals only
- Oracal / RAL / stock color = finish intent signals only
- pricing keys present = dependency completeness only
- analyzer perimeter / quote geometry = evidence only
- only explicit component confirmation can target `confirmed`, and only after canonical completeness + zero blockers

## Files created

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/qa/return-cant-component-confirmation-contract-2026-07-09/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_confirmation_contract_v1.md`

## Validation

- docs-only diff
- `git diff --check`
- no tests required
- no build required

## Next recommended prompt

```text
RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1
```
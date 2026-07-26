# RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1

## Verdict

```text
RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_READY
```

## Scope

Docs-only / contract-only slice for canonical source and mapping semantics of:

```text
components.return_cant.instances.<instance_key>
```

Focus:

- `instance_key`
- `source_kind`
- `source_ref`
- `group_key`
- `layer_key`
- `layer_group_ids`

Allowed:

- architecture contract doc;
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
- no Quote / Order / Execution
- no ProductAggregate / TaskGraph / ExecutionPlan
- no DB migration

## Safety gate

- HEAD confirmed: `72d7694`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

## Audit summary

Current mapping evidence found in code:

1. `deriveLetterGroupsFromAnalyzer()` creates `group_key` from confirmed layer role entries with `role = face`.
2. `deriveArtworkFinishesFromAnalyzer()` creates `layer_key` from confirmed layer role entries for artwork/logo layers.
3. `finish_setup.letter_group_finishes[]` persists `group_key` rows.
4. `finish_setup.artwork_finishes[]` persists `layer_key` rows.
5. `layer_role_setup.layers[]` persists `layer_key`, optional `layer_id`, `layer_name`, `auto_role`, `confirmed_role`, `confirmation_state`.
6. readonly adapter uses `source_row_key = group_key | layer_key` and warns `LAYER_GROUP_IDS_CAPTURED_AS_ROW_ID_EVIDENCE_ONLY` when mapping is still just row-id evidence.
7. readonly mapper keeps `selectedLayerRefs` and Step 1 layer confirmations as `context_only`, not canonical mapping truth.

Key finding:

```text
stable row keys already exist
the missing piece is the canonical promotion contract into runtime instance mapping
```

## Decision summary

Canonical rules should be:

1. For Vector Litere:

```text
source_kind = letter_group
instance_key = letter_group:<group_key>
source_ref.group_key = <group_key>
```

2. For Vector Logo:

```text
source_kind = artwork_layer
instance_key = artwork_layer:<layer_key>
source_ref.layer_key = <layer_key>
```

3. Forbidden as final identity:

- numeric index
- UI label
- unstable layer name
- invented fallback key

4. `source_label` is display/evidence only.
5. `source_role` is semantic role only.
6. `layer_group_ids` remains a canonical instance field, not a `source_ref` field.

## `layer_group_ids` decision

1. It represents real layer ids / layer keys backing the instance.
2. It may be derived from analyzer/layer-role/group mapping.
3. It is required for `confirmed`.
4. If missing or ambiguous, component confirmation must stay blocked.
5. A plain row-id echo is evidence only, not final mapping truth.

## Canonical blockers

- `RETURN_CANT_INSTANCE_KEY_MISSING`
- `RETURN_CANT_SOURCE_KIND_MISSING`
- `RETURN_CANT_SOURCE_REF_MISSING`
- `RETURN_CANT_GROUP_KEY_MISSING`
- `RETURN_CANT_LAYER_KEY_MISSING`
- `RETURN_CANT_LAYER_GROUP_IDS_MISSING`
- `RETURN_CANT_LAYER_MAPPING_AMBIGUOUS`
- `RETURN_CANT_LAYER_ROLE_UNSUPPORTED`
- `RETURN_CANT_LAYER_MAPPING_LEGACY_ONLY`

## Source matrix summary

- `group_key` and `layer_key` are the only current fields that can become the stable identity basis for canonical instances.
- role labels can define `source_kind`, but cannot define `instance_key`.
- labels and names are evidence/display only.
- analyzer/layer-role data can define real `layer_group_ids`, but only with controlled promotion rules.
- legacy `components.returnCant` cannot define stable per-instance mapping.

## Relationship with confirmation_state

1. Missing `instance_key` means `missing` or `blocked`.
2. Missing `source_kind` means `blocked`.
3. Missing `source_ref` means `blocked`.
4. Missing `layer_group_ids` means never `confirmed`.
5. Ambiguous mapping means `blocked`.
6. Only stable mapping + component confirmation + confirmed perimeter can allow `confirmed`.

## Next-slice decision

This mapping contract is ready and sufficient to move to bridge planning.

Recommended next prompt:

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1
```

## Files created

- `docs/architecture/product-system/RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT.md`
- `docs/qa/return-cant-layer-mapping-source-contract-2026-07-09/RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_layer_mapping_source_contract_v1.md`

## Validation

- docs-only diff
- `git diff --check`
- no tests required
- no build required
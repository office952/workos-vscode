# RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1

## Scope

Docs-only implementation plan pentru viitorul bridge runtime `return_cant`.

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
mode = implementation_plan_only
```

Fara:

- bridge implementation;
- Product Truth writes;
- UI changes;
- Pricing changes;
- runtime DB changes;
- seeds;
- Quote / Order / Execution changes;
- ProductAggregate / TaskGraph / ExecutionPlan changes.

## Safety Gate

Rezultat:

```text
HEAD = 3c6afb0
staged_files = none
git_diff_check = clean
```

Worktree-ul este murdar doar prin fisiere necorelate deja existente si a fost lasat neatins.

## Mandatory Anchors Read

Contracte:

1. `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
2. `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
3. `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT.md`
4. `RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT.md`

Code anchors:

1. `backend/services/intake_v6_workspace_service.py`
2. `backend/schemas/intake_v4.py`
3. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
4. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
5. `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
6. `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
7. `backend/tests/test_letter_group_finish_readiness.py`

## Findings

1. `save_finish_setup_for_intake_v6_workspace()` este punctul corect de write-hook deoarece acolo exista simultan `finish_setup` normalizat, `layer_role_setup`, `quote_geometry` si persistenta finala.
2. `upload_svg_to_intake_v6_workspace()` si `save_analysis_bundle_for_intake_v6_workspace()` sterg deja `finish_setup` cand SVG-ul este inlocuit, deci trebuie sa curete si viitorul slice runtime `return_cant`.
3. `save_layer_roles_for_intake_v6_workspace()` poate schimba mapping-ul si trebuie sa reruleze bridge-ul cand `finish_setup` exista.
4. `IntakeV4WorkspacePayload` nu declara inca un camp runtime Product Truth, iar `_parse_payload()` valideaza payload-ul prin Pydantic, deci output-ul bridge-ului ar fi fragil fara pasul de schema.
5. readonly adapterul si readonly mapperul confirma asteptarea pentru `components.return_cant`, dar nu sunt writers runtime.
6. `productTruthDraftBuilder.ts` ramane legacy preview shape (`components.returnCant`) si nu este locul corect pentru bridge.

## Planned Integration

Primary hook:

```text
backend/services/intake_v6_workspace_service.py
save_finish_setup_for_intake_v6_workspace()
```

Required sequence:

1. normalize finish setup;
2. persist normalized `finish_setup` in `payload_raw`;
3. refresh local derived state already owned by workspace service;
4. apply pure backend `return_cant` runtime bridge;
5. parse payload and persist.

Required cleanup or rerun hooks:

1. `upload_svg_to_intake_v6_workspace()`
2. `save_analysis_bundle_for_intake_v6_workspace()`
3. `save_layer_roles_for_intake_v6_workspace()`

## Bridge Inputs

1. `finish_setup.letter_group_finishes[]`
2. `finish_setup.artwork_finishes[]`
3. `finish_setup.return_depth_mm`, `return_finish_type`, `return_oracal_code`
4. `layer_role_setup.layers[]`
5. `quote_geometry.letter_perimeter_m`, `geometry_source`, `confirmed`
6. template code and workspace payload context

## Bridge Outputs

Relative la runtime Product Truth root:

```text
components.return_cant.version
components.return_cant.instances.<instance_key>
```

Per instanta:

1. `instance_key`
2. `source_kind`
3. `source_ref`
4. `layer_group_ids` only when real mapping is available
5. `material_profile`
6. `finish_variant`
7. `pricing_keys`
8. `geometry`
9. `confirmation_state`
10. `blockers`

## State Rules Locked By The Plan

1. stable key missing => no synthetic canonical instance
2. row-id echo alone => evidence only, not confirmed mapping
3. `quote_geometry.letter_perimeter_m` => evidence only
4. no auto-promotion to `confirmed`
5. legacy paths readable only as context, never as final write target

## Test Matrix

1. pure helper tests for letter groups, artwork rows, finish normalization, pricing key mapping, geometry evidence and blockers
2. workspace service tests for save, rerun and cleanup hooks
3. payload schema persistence test
4. read-only mapper/awareness recheck only if canonical runtime fixtures change
5. runtime smoke through workspace API payload inspection

## Verdict

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_READY
```

Reason:

1. integration point is local and concrete;
2. input sources are already present;
3. cleanup hooks are identifiable;
4. the remaining work is implementation discipline, not discovery.
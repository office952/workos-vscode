# INTAKE_V6_LINKED_LOGO_LAYER_BINDINGS_PERSISTENCE_V1 — Validation

**Phase:** VALIDATION COMPLETE

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_layer_binding_persistence.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_layer_binding_persistence.py tests/test_intake_v6_product_composition_recommendation.py tests/test_product_definition_gradi_composition.py tests/test_selected_layer_refs_runtime_capture.py -q
cd ..\frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx
```

## Results

| Suite | Pass | Fail |
|---|---:|---:|
| Layer binding persistence | 17 | 0 |
| Regression bundle (backend) | 28 | 0 |
| Composition panel (frontend) | 4 | 0 |

## Runtime evidence

- Isolated test workspaces used (UUID fixtures in pytest); historical workspace `22ef834d-f2d0-453b-a7a7-118928c98a39` not mutated
- Payload before: `layer_bindings: []`
- Payload after confirm: two rows `logo-stanga`, `logo-dreapta`, `binding_status: confirmed`, `target_template_code: TPL-VOLUMETRIC-LOGO_v1`
- Reload via `get_intake_v6_workspace` preserves bindings
- ProductDefinition preview exposes `binding_status: confirmed` and removes `LINKED_TEMPLATE_BINDING_MISSING`

## Forbidden-scope diff audit

```text
git diff -- backend
 backend/services/intake_v6_workspace_service.py
 backend/services/intake_v6_layer_binding_persistence_service.py (new)
 backend/tests/test_intake_v6_layer_binding_persistence.py (new)

git diff -- frontend
 (no application changes)
```

Confirmed:

- ProductAggregate application files: NOT modified
- Pricing / Quote / Order / Execution: NOT modified
- DB schema / migration: NOT modified
- General UI polish: NOT modified

## Known limitations

- ProductAggregate workspace-aware composition: NOT INCLUDED
- Historical workspaces not backfilled
- Segment removal auto-delete semantics deferred

## Boundary report

- Workspace binding persisted: YES (via tests)
- ProductDefinition consumes binding: YES
- ProductAggregate workspace composition: NOT INCLUDED

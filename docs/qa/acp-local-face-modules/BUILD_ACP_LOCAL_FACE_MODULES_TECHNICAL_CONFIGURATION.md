# BUILD — ACP Local Face Modules Technical Configuration

## Purpose

Component-owned local face modules on live ACP shell, with guarded Aggregate projection and minimal operator UI.

## Verdict

`ACP_LOCAL_MODULE_CONTRACTS_COMPLETE_UI_GUARDED`

## Commands

### Backend (targeted)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acp_local_face_modules_v1.py tests/test_acp_face_treatment_authority_v1.py tests/test_svg_component_binding_contract.py -q
```

Result: face-treatment + local-module + binding contract suites PASS (see agent report for counts).

### Frontend (targeted)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/svgComponentBindings.test.ts src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts
npx --yes pnpm@8.10.0 run build
```

Result: Vitest PASS; production build PASS.

### Full-repo

Not run (known debt / unrelated WIP noise). Targeted only.

## Boundary

- No CPP / tasking / Execution / schema / migration / seed
- LIGHT-ROUTED remains PARALLEL_LEGACY_COST_PATH
- Owner gates retained for plexi/LED/fit values

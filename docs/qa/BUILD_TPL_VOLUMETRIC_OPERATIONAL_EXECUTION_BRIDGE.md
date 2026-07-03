# BUILD — TPL-VOLUMETRIC Operational Execution Bridge

## Scop

Legătură coerentă între operațiile `TPL-VOLUMETRIC-LETTERS`, codurile canonice din execution plan (`process_type`) și Operational Registry, astfel încât OperatorView / ExecutionDetail afișează rezolvarea alias + pool eligibil real — fără hard-block și fără persistare angajați în ProductSystem.

## Context audit (operation code flow)

| Layer | Cod exemplu | Notă |
|-------|-------------|------|
| ProductSystem template ops | `vector_prep`, `face_cnc_cut`, `assembly_letters`, `painting`, … | 13 operații în template; PS codes |
| Order snapshot mapper | `assembly_letters` → `volumetric_letter_assembly` | Canonical task_type pentru gate |
| Execution plan `process_type` | `volumetric_letter_assembly`, `cnc_routing`, `ASSEMBLY`, … | Ce ajunge în `/operator` |
| Operational Registry | `assembly`, `cnc_cutting`, … + `product_system_aliases` | Sursa autorizări |
| OperatorView `operationCode` | = `process_type` din API | Pool via `eligible-employees` |

**Mismatch legacy:** UI local (`useOperatorEmployees`, `tabletLiveBridge`, `execution_reality_workforce`) căuta mapping direct pe `operation_code`, ignorând aliasuri PS → registry.

## Ce s-a schimbat

### Frontend
- `operationResolution.ts` — helper comun: normalize, resolve din listă, format label, parse pool API.
- `useOperatorEmployees` — eligibilitate dropdown folosește alias resolution.
- `tabletLiveBridge` — stație/registry folosește alias resolution.
- `OperationPoolPreviewPanel` — label unificat + warning soft pentru mapping lipsă.
- `OperationRegistryMappingBadge` — badge în ExecutionDetail task table.
- `ExecutionDetail` — badge registry mapped / alias resolved / missing mapping per task.
- `OperatorView.eligibility.test.tsx` — smoke component pentru bridge volumetric.

### Backend
- `execution_reality_workforce.resolve_task_workforce_context` — `resolve_operation_mapping` (alias-aware), returnează `resolved_operation_code` + `resolution`.

### Neatins
- CostEngine, pricing, payroll, schema/migrations, seed runtime, `dev.db`.
- ProductSystem template persistence (angajați nominali).
- Task lifecycle, auto-dispatch, hard authorization block.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_operational_resource_registry.py tests/test_operational_authorization_foundation.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/features/operational-registry/TemplateOperationMappingPanel.test.tsx src/features/operational-registry/OperationPoolPreviewPanel.test.tsx src/features/operational-registry/operationEligibility.test.ts src/features/operational-registry/operationResolution.test.ts src/pages/OperatorView.eligibility.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

## Smoke read-only

```powershell
$base = "http://127.0.0.1:8000/api/v1"
Invoke-RestMethod "$base/operational-registry/operation-mappings/volumetric_letter_assembly/resolve"
Invoke-RestMethod "$base/operational-registry/operation-mappings/volumetric_letter_assembly/eligible-employees"
```

UI: `/operator` — `volumetric_letter_assembly → assembly · 4 eligibili`; `/product-system` → Resurse operaționale OK.

## Boundaries

- Read-only registry consumption în execuție; edit mapping rămâne în ProductSystem panel / registry admin.
- `GET /resolve` rămâne 404 pentru unknown; `eligible-employees` răspunde soft (`not_found`, total=0).

## Gaps rămase

- Cosmetic: pool preview label în ProductSystem poate afișa registry code al ultimei operației selectate în listă.
- `workstationRouting.ts` demo routing paralel — nu sursă de truth pentru registry.
- Rapoarte operaționale — out of scope acest build.

## HEAD la build

Branch: `local/integration-pr4-plus-svg-path`

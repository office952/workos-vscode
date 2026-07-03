# BUILD: ProductSystem ↔ Operational Registry Alias Mapping (TPL-VOLUMETRIC-LETTERS)

## Purpose

Align `TPL-VOLUMETRIC-LETTERS` ProductSystem / execution operation codes with the operational workforce registry via `operation_resource_requirements.product_system_aliases`, so resolve API, eligible employee pool, ProductSystem **Resurse operaționale**, and OperatorView preview work without hardcoded runtime mappings.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Foundation commits: `a17e3c26`, `f89a866`, `9b6aff0`, `26bd2bd`
- Architecture: `docs/architecture/OPERATIONAL_RESOURCE_MAPPING_ARCHITECTURE.md`

## ProductSystem operation codes (13 — TPL-VOLUMETRIC-LETTERS)

From `backend/seeds/seed_build4_templates.py` / dossier:

| PS code | Label (typical) |
|---------|-----------------|
| `vector_prep` | Vector prep |
| `face_cnc_cut` | CNC față |
| `vinyl_application` | Colantare |
| `side_forming` | Cant litere |
| `return_face_bonding` | Lipire cant |
| `back_cut` | CNC backing |
| `led_install_letters` | LED |
| `electrical_letters` | Electric |
| `mounting_template_cnc_cut` | CNC template montaj |
| `painting` | Vopsire |
| `assembly_letters` | Asamblare |
| `qc_letters` | QC |
| `packaging_letters` | Packaging |

## Execution / Operator canonical codes (selected)

From `order_execution_snapshot_mapper.py`:

| Canonical (Operator task) | Source PS codes |
|---------------------------|-----------------|
| `file_preparation` | `vector_prep` |
| `cnc_routing` | `face_cnc_cut`, `back_cut`, `mounting_template_cnc_cut` |
| `edge_bending` | `side_forming` |
| `welding` | `return_face_bonding` |
| `vinyl_cutting` | `vinyl_application` |
| `led_assembly` | `led_install_letters` |
| `led_wiring` | `electrical_letters` |
| `volumetric_letter_assembly` | `assembly_letters`, `painting` |
| `quality_control` | `qc_letters` |
| `packaging` | `packaging_letters` |

## Registry mappings (14 after build)

| Registry `operation_code` | Key aliases |
|---------------------------|-------------|
| `prepress` | `vector_prep`, `file_preparation` |
| `print` | `print_large_format`, `face_print` |
| `print_roll` | `print_roll` |
| `laminare` | `laminating`, `lamination` |
| `cutter_plotter` | `cutter_plotter`, `oracal_cutting` |
| `cnc_cutting` | `face_cnc_cut`, `back_cut`, `cnc_routing` |
| `cant_modelare` | `side_forming`, `edge_bending` |
| `colantare` | `vinyl_application`, `vinyl_cutting` |
| `assembly` | `assembly_letters`, `painting`, **`volumetric_letter_assembly`** |
| `welding` | `return_face_bonding` |
| `montaj_led` | `led_install_letters`, `led_assembly`, `led_wiring` |
| `quality_control` | `qc_letters`, `quality_control` |
| `packaging` | `packaging_letters`, `packaging` |
| `field_installation` | `installation_onsite`, `mounting` |

All mappings: `authorization_mode = hybrid`, explicit authorized employees from seed roster where applicable.

## Files changed

- `backend/seeds/seed_operational_workforce_registry.py` — aliases, new mappings, employee auth IDs
- `backend/services/operational_catalog.py` — `SUGGESTED_OPERATION_ALIASES` (UI hints + canonical codes)
- `frontend/src/features/operational-registry/TemplateOperationMappingPanel.tsx` — loading stability, eligibility preview
- `backend/tests/test_operational_resource_registry.py`
- `backend/tests/test_operational_authorization_foundation.py`
- `frontend/src/features/operational-registry/TemplateOperationMappingPanel.test.tsx`
- `frontend/src/features/operational-registry/OperationPoolPreviewPanel.test.tsx`

## Seed behavior

- **Manual only** — not auto-run on dev boot.
- Idempotent on `operation_code`; re-run updates aliases and authorizations without duplicate rows.
- **Local DB must be re-seeded** after pulling this build for aliases to appear in dev.db.

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe -c "import asyncio; from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry; print(asyncio.run(seed_operational_workforce_registry()))"
```

Expected after seed: `operation_mappings_upserted = 14`.

## Tests

### Backend (targeted)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_operational_resource_registry.py tests/test_operational_authorization_foundation.py -q
```

### Frontend (targeted)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/features/operational-registry/TemplateOperationMappingPanel.test.tsx src/features/operational-registry/OperationPoolPreviewPanel.test.tsx src/lib/operatorEmployeeEligibility.test.ts
```

### Typecheck

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

## Runtime smoke (after manual reseed)

| Route | Expected |
|-------|----------|
| `/product-system` → TPL-VOLUMETRIC-LETTERS → Resurse operaționale | Aliases visible; panel not stuck on „Se încarcă…” |
| `/operator` → task `volumetric_letter_assembly` | Pool > 0 (Putaru / Vali / Costi / Andrei) |
| `/employees` | 8 active real / 5 inactive mock |
| `/utilaje` | 14 resources |
| `GET /api/v1/machines` | 200 |

## Gaps remaining

- CNC chamfer / bevel ops not in current TPL 13-op list — no registry row until template adds stage.
- `vinyl_cutting` canonical maps to `colantare` (application), not `cutter_plotter` — cutter plotter mapping exists for future vinyl cut-only tasks.
- Field installation not in the 13 template ops; mapping exists for order/montaj flows.
- Hard dispatch / automatic task assignment — out of scope.

## Boundaries (confirmed)

Not modified: CostEngine, pricing, quote_orchestrator, payroll, inventory, nesting, commercial PDF, schema/migrations, employee salaries, hard dispatch.

Not implemented: hard-block authorization, costing per employee, auto dispatch, auto seed, task auto-assignment.

## Next steps

1. Manual reseed local `dev.db`.
2. Runtime smoke `/operator` for `volumetric_letter_assembly`.
3. Commit: `feat(operations): map volumetric product operations to registry`

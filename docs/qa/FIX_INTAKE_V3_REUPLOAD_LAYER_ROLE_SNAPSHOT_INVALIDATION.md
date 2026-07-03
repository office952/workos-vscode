# FIX_INTAKE_V3_REUPLOAD_LAYER_ROLE_SNAPSHOT_INVALIDATION

## Problema

După upload SVG Corel (`litere-volumetrice.svg`), `path_geometry_summary` conținea layere noi (`fata_x0020_plexiglas`, `autocolant`), dar `layer_role_confirmation_snapshot` rămânea stale cu layer vechi (`layer-litere`) din upload anterior.

Operatorul vedea roluri vechi în UI/API deși geometry/lighting foloseau path geometry nou.

## Cauza

| Component | Comportament anterior |
|-----------|----------------------|
| `attach_svg_raw_analysis_to_workspace` | Actualiza `path_geometry_summary`, **nu** invalida layer roles |
| `get_layer_role_confirmation_for_workspace` | Returna snapshot persistat dacă exista, fără verificare vs path geometry |
| Persistență | `layer_role_confirmation_snapshot` în workspace payload JSON |

Nu exista comparare a layer key set-ului între path geometry și confirmation snapshot.

## Strategia de invalidare/rebuild

Loc: **`reconcile_layer_role_confirmation_after_path_geometry_update()`** în `intake_v3_layer_role_confirmation_service.py`, apelat din **`attach_svg_raw_analysis_to_workspace`** după generarea `path_geometry_summary`.

| Caz | Comportament |
|-----|--------------|
| Layer set **identic** | Rebuild draft din path geometry + **păstrează** roluri confirmate compatibile |
| Layer set **diferit** | Rebuild draft; roluri păstrate doar pentru chei intersectate; warning `layer_role_confirmation_reset_after_svg_reupload` |
| Fără snapshot anterior | Draft nou din path geometry |
| GET stale defense | `get_layer_role_confirmation_for_workspace` detectează mismatch și returnează draft rebuilt (`persisted=false`) |

După reconcile: **`build_and_attach_geometry_snapshot_for_workspace_payload`** regenerează geometry metrics snapshot.

## Frontend

- `layerRoleReuploadNotice.ts` — mesaj operator când snapshot a fost resetat
- `applyOperatorSvgUploadResult()` — afișează mesaj + `refreshLayerRoles()` (existent)

## Teste

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest `
  tests/test_intake_v3_reupload_layer_role_snapshot_invalidation.py `
  tests/test_intake_v3_path_geometry_svg_sanitization.py `
  tests/test_svg_sanitization.py `
  tests/test_intake_v3_lighting_plan.py `
  tests/test_intake_v3_operator_workspace_e2e_hardening.py -q

cd ..\frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV3/layerRoleReuploadNotice.test.ts `
  src/lib/intakeV3/pathGeometryUploadNotice.test.ts
```

**Rezultat:** backend 64 passed, frontend 5 passed

## Runtime smoke

Workspace: `e8d5b5b8-7f4d-4908-8445-e0bb8f32a3cf`

1. Upload `volumetric-multilayer.svg` → `layer-litere`
2. Confirm face
3. Re-upload `litere-volumetrice.svg`

| | Before | After |
|-|--------|-------|
| Confirm layers | `layer-litere` | **`fata_x0020_plexiglas`, `autocolant`** |
| Stale `layer-litere` | present | **absent** |
| `face_cutting_perimeter_ml` | — | **0.07737 m** |
| Module suggestion | — | **1** @ 100 mm pitch |

## Boundary confirmations

- No CostEngine / Inventory / StockMovement / ExecutionTask / ExecutionPlan / PO / SupplierOrder
- No Lighting / PSU / reserve formula changes
- No XML parser security changes
- No Atoms recomposition
- No DB manual edit / no migration
- Owner SVG not committed

## Ce rămâne

1. Browser visual smoke pe Operator SVG & Layers tab (file drop)
2. Commit controlat
3. Visual acceptance / Atoms 3-step

## Verdict

**PASS — re-upload rebuilds layer role confirmation from current SVG**

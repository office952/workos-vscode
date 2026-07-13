## Dossier write path — before/after

### Before (82a713e)

Backend enforcement existed via RBAC permissions:
- `dossier.create`: admin, manager
- `dossier.update`: admin, manager
- `dossier.delete`: admin, manager

Router dependencies:
- `backend/routers/product_blueprint_dossier.py`
  - create/update/delete routes depend on `require_permission("dossier.*")`.

However, dossier content is consumed by:
- ProductAggregate builder (`backend/services/product_aggregate_service.py`)
- ProductSystem readiness service (`backend/services/product_system_template_readiness_service.py`)

So even properly-permissioned dossier writes can influence active truth unless bounded.

### After (this slice)

- **No UI redesign** and **no RBAC changes** in this slice.
- We added explicit aggregate warnings:
  - `DOSSIER_CONSUMED` info warning when dossier was used
  - `TEMPLATE_IDENTITY` trace warning to prevent hidden identity drift when reading aggregate output

Remaining work (explicitly tracked as debt / next slice candidate):
- Make dossier consumption version-pinned or explicitly non-authoritative for operator-visible canonical templates.


# Dev Readiness — Active Route Analysis

**Task:** `PRODUCT_SYSTEM_DEV_READINESS_GATE_STALE_INTAKE_V3_FIX_V1`  
**Date:** 2026-07-13  
**Worktree:** `C:\w\psiso`  
**HEAD:** `9366a74` (+ uncommitted implementation)

## Router declaration (deprecated)

File: `backend/routers/intake_v3_workspaces.py`

```python
# DEPRECATED: V3 workspace endpoints superseded by V4. Router disabled from auto-discovery.
# V3 services are still imported by V4 as shared libraries — do not delete this file.
_deprecated_router = APIRouter(
    prefix="/api/v1/intake-v3",
    tags=["intake-v3-workspaces"],
    dependencies=[Depends(get_current_user)],
)
```

All route handlers attach to `@_deprecated_router`, not `router`.

## Exclusion from active discovery

File: `backend/main.py` — `include_routers_from_package()` only includes module attributes named:

- `router`
- `admin_router`

`intake_v3_workspaces.py` exports **no** `router` or `admin_router` — only `_deprecated_router`. Therefore the Intake V3 HTTP surface is **not registered** on the running FastAPI app.

## Stale paths — intentionally absent

| Path | In OpenAPI on live app | In `_deprecated_router` source |
|------|------------------------|--------------------------------|
| `/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments` | **NO** | YES (unregistered) |
| `/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation` | **NO** | YES (unregistered) |
| `/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan` | **NO** | YES (unregistered) |

**Runtime evidence (prior attempt):** Backend returned HTTP 200 on `/health` and `/openapi.json`; readiness failed solely because these three paths were required by `scripts/start-dev.ps1` but absent from OpenAPI.

## Active runtime dependency check

- Intake V4/V5/V6 supersede V3 workspace HTTP endpoints (per file comment).
- V3 **services** remain as shared libraries imported by V4+ — no requirement to restore V3 HTTP routes for general dev stack readiness.
- Product System V2 runtime proof does not depend on Intake V3 operator workspace routes.

## Conclusion

Removing the three stale paths from `Test-IntakeV3OperatorWorkspaceRoutesOk` / diagnostics required-path lists aligns dev readiness with **active** router registration. No backend change required.

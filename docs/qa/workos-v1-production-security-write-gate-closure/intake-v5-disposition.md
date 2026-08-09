# Intake V5 disposition

```text
INTAKE_V5 = DEPRECATED_NOT_MOUNTED
```

## Consumer proof

- Grep FE for `/api/v1/intake-v5` / `intake-v5`: **zero** production consumers.
- Backend tests: **zero** HTTP callers of intake-v5.
- Module kept for seeds/scripts; routes registered only on `_deprecated_router`.
- `main.include_routers_from_package` discovers only `router` / `admin_router`.

## Runtime

Live probe `GET http://127.0.0.1:8000/api/v1/intake-v5/config` → **404**.

## Defense in depth

If manually remounted, `_deprecated_router` dependencies include `get_current_user`.

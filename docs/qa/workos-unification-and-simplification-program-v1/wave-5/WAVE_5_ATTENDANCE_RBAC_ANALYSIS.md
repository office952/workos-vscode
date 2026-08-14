# Wave 5 — attendance RBAC

RBAC not changed. Reads only.

```text
FRONTEND_ROLE_ALLOWED = manager, admin (nav key attendance → view:hr)
BACKEND_ENDPOINT_AUTH = admin OR operator (require_attendance_operator)
READ_ENDPOINTS = GET /summary, GET /events, GET /effects, GET /effects/{id}
WRITE_ENDPOINTS = POST/PUT/DELETE /events, POST /effects/generate, POST /effects/{id}/apply
MANAGER_RUNTIME_RESULT = UI_OPENS; DEV_BYPASS_API=200_AS_ADMIN; MINTED_MANAGER_JWT=403_ON_READ
ATTENDANCE_RBAC_RELATION = MIXED
```

## Legs

| Actor | Frontend Pontaj | Backend read | Backend write |
|-------|-----------------|--------------|---------------|
| admin | YES | 200 | allowed (not clicked) |
| manager | YES (`view:hr`) | **403** `attendance_operator_required` | **403** (same gate) |
| operator | NO (no `view:hr`) | 200 | allowed (not clicked) |

All attendance endpoints share one gate. This is **not** READ_ALLOWED_WRITE_DENIED for manager.

## Runtime proof

`runtime/manager-attendance-probe.json` (GET only):

| Token | summary | events | effects |
|-------|---------|--------|---------|
| `__DEV_BYPASS_TOKEN__` (synthetic admin) | 200 | 422 missing dates | 200 |
| minted `role=manager` | **403** | **403** | **403** |
| minted `role=operator` | 200 | 422 missing dates | 200 |
| minted `role=admin` | 200 | 422 missing dates | 200 |

422 on `/events` is missing `start_date`/`end_date`, not auth.

Wave 5 manager Pontaj screenshots show data because DEV bypass is **admin** on the API. That is not manager-authorized backend access.

W5-C1 stays ACTIVE: FE overexposes manager; FE hides operator; BE is the inverse for those two roles.

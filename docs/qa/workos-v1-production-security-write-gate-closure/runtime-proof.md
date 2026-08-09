# Runtime proof

| Probe | Result |
|-------|--------|
| `GET :8000/api/v1/intake-v5/config` | **404** (not mounted) |
| `GET :3000/` | **200** (UI up) |
| Operator HR fields via API | pytest `operator_client` — salary/cost null |
| Admin HR fields via API | pytest `auth_client` — salary present |
| Anonymous fail-closed | pytest `prod_unauth_client` with `dev_auth_allowed=False` → 401 |

Browser network proof for field strip: backend TestClient responses (same JSON as browser network). Full multi-role browser login matrix LATER if Owner wants UI soak; engineering authority is backend.

**Note:** Dev stack uses `dev_auth_allowed` synthetic admin when no token — production deploy must set non-dev `APP_ENV` (existing BUILD 20 gate). Documented; not reinvented here.

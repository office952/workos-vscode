# BUILD: Employee Identity, Session & PWA Foundation

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `5389d08` — `feat(employee): add attendance console and self view` |
| **HEAD after** | _(filled post-commit)_ |
| **Status** | PASS |

## 1. Audit — auth / session summary

| Topic | Finding |
|-------|---------|
| Login | OIDC via `backend/routers/auth.py` → app JWT in HttpOnly `app_token` cookie (+ optional Bearer) |
| Session storage | Cookie `app_token`; frontend `AuthContext` + `lib/auth.ts` (`GET /api/v1/auth/me`) |
| Employee Mobile auth | Same path as desktop — no separate mobile login table or credentials |
| `current_user` | JWT decode → `UserResponse` via `get_current_user` |
| Employee identity | Server-side `employees.user_id = users.id` via `employee_mobile_identity.py` + `require_employee_self_user` |
| Manager/admin self | Allowed when user has employee link; review forbids self-approve (tested) |
| PWA before | No manifest, no install meta, only `favicon.svg` + `robots.txt` |
| Service worker | None (intentional for this build) |

## 2. Identity / session decision

Document: `docs/architecture/EMPLOYEE_IDENTITY_SESSION_AND_PWA_DECISION.md`

Rule: **Same credentials, different contexts.**

## 3. PWA files added/changed

| File | Change |
|------|--------|
| `frontend/public/manifest.webmanifest` | New — `start_url: /employee-app`, standalone, SVG icon |
| `frontend/public/icons/workos-icon.svg` | New — local icon |
| `frontend/index.html` | manifest link, theme-color, Apple web-app meta |

PNG maskable 192/512 deferred.

## 4. Frontend UX changes

| Area | Change |
|------|--------|
| `EmployeeMobileApp.tsx` | Shell disclaimer: same WorkOS account; install card on home; home intro clarifies self-only + same login |
| Error UX | Existing `employeeRequestErrors.ts` maps 401/403 (auth, employee link, self-review) — unchanged, verified by tests |

## 5. Backend guards verified (existing tests — no new backend code)

| Guard | Test evidence |
|-------|---------------|
| Self requests reject client `employee_id` | `test_client_sent_employee_id_rejected` |
| Self attendance rejects client `employee_id` | `test_self_attendance_rejects_client_employee_id` |
| User without employee link forbidden | mobile request tests + frontend 403 UX test |
| Manager/admin cannot self-approve | `test_self_review_forbidden` + frontend test |
| Attendance CRUD admin/operator only | `test_employee_attendance_events.py` |
| Effects console admin/operator only | `test_employee_request_attendance_effects.py` |

## 6. Routes affected

- `/employee-app` — install card + identity copy
- PWA `start_url` → `/employee-app`
- No new routes; no auth route changes

## 7. Tests run + results

```text
backend: pytest tests/test_employee_mobile_requests.py
         tests/test_employee_request_review.py
         tests/test_employee_attendance_events.py
         tests/test_employee_request_attendance_effects.py
         → 116 passed

frontend: vitest run src/pages/EmployeeMobileApp.test.tsx
         → 27 passed
```

No new backend tests added — coverage confirmed sufficient.

Frontend tests updated: install card + same-account disclaimer assertions.

## 8. Manual smoke

Not run in this build (no dev stack started). Manifest and meta are static files verifiable via DevTools Application tab when stack is up.

## 9. Limitations / deferred

- PNG maskable icons (192/512)
- Service worker / offline sync
- `beforeinstallprompt` install button
- Native Android/iOS app
- MFA, SSO, push notifications
- Multi-tenant identity

## 10. Confirmations

- [x] Same credentials for desktop and mobile
- [x] No separate mobile account
- [x] No separate mobile password
- [x] No client `employee_id` authority on self routes
- [x] Backend resolves employee identity
- [x] PWA `start_url` → `/employee-app`
- [x] Employee Mobile installability foundation present
- [x] No native app
- [x] No auth rewrite
- [x] No payroll/payment/cost changes
- [x] No DB/migration
- [x] Attendance CRUD remains admin/operator only
- [x] Approval remains status-only

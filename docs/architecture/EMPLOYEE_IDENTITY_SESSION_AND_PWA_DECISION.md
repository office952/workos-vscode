# Employee Identity, Session & PWA — Decision

## Status

| Item | Value |
|------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | frontend PWA metadata + Employee Mobile UX guards |
| **Backend impact** | identity/session verified by existing tests; no auth rewrite |
| **DB impact** | none |
| **Payroll impact** | none |

## Regula principală

```text
Same credentials, different contexts.
```

- Un singur user account și aceleași credențiale pentru desktop WorkOS și Employee Mobile.
- Nu există cont, parolă sau tabel de login separat pentru telefon.
- Employee Mobile este un **context UI + API self-only**, nu un sistem de autentificare paralel.
- Backendul rezolvă identitatea: `employees.user_id = users.id`.
- Clientul **nu** trimite `employee_id` ca autoritate pe rute self.

## Model conceptual

```text
users
  id          (OIDC sub / app user id)
  email
  role
  active

employees
  id
  user_id     → users.id
  name, status, role, department
```

Link MVP: **`employees.user_id = users.id`**

## Contexturi

| Context | Permis | Interzis |
|---------|--------|----------|
| `desktop_workos` | module ERP conform rol RBAC | self-only fără permisiune |
| `employee_self` | `/employee-mobile/*` self read/write requests, self attendance read | CRUD pontaj general, effects apply |
| `manager_review` | review cereri (fără self-approve) | apply pontaj, CRUD general |
| `attendance_operator` | CRUD pontaj + effects apply | payroll |
| `admin` | desktop + operator paths | — |

Același user poate avea **simultan** rol RBAC (ex. manager) **și** link employee pentru self context.

## Sesiune

- OIDC → JWT în cookie `app_token` (+ Bearer opțional).
- `get_current_user` decodează JWT → `UserResponse`.
- Dev: `VITE_ENABLE_DEV_AUTH` / `dev_auth_allowed()` — același mecanism pentru desktop și mobile.
- Employee self routes: `require_employee_self_user` → `resolve_employee_for_user`.

## Ce NU facem

Cont/parolă mobile separat, `employee_id` client, auth provider nou, app nativă, offline sync, push, MFA, SSO, multi-firmă complet, payroll.

## PWA MVP

- `manifest.webmanifest`: `start_url: /employee-app`, `display: standalone`.
- Meta mobile + Apple web app capable în `index.html`.
- Icon SVG local (`/icons/workos-icon.svg`).
- Fără service worker complex în acest build.
- Instalare: Add to Home Screen / browser install — același backend și sesiune.

## Securitate

- Backend guards = sursa de adevăr.
- Frontend routing ≠ securitate.
- Attendance CRUD: admin/operator only (unchanged).
- Approve request: status-only (unchanged).

## Deferred

App nativă, push, offline cache, MFA, SSO, magic links, QR login, device management, multi-tenant identity, manager team mobile dashboard, PNG maskable icons (512/192).

## Related

- `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md`
- `docs/architecture/EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_DECISION.md`

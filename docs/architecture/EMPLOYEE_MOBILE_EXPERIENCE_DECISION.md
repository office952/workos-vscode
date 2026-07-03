# Employee Mobile Experience — Decision

## Status

| Item | Value |
|------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | frontend Employee Mobile UX |
| **Backend impact** | none |
| **DB impact** | none |
| **Payroll impact** | none |

## Obiectiv produs

Employee Mobile devine spațiul operațional al angajatului:

```text
Home (dashboard)
Requests (self)
Attendance (self, read-only)
Review (manager/admin, when allowed)
```

## Reguli UX

- Home este dashboard cu cards acționabile, nu landing generic.
- Navigare mobilă persistentă (bottom nav) către Home, Cereri, Pontaj, Review.
- Același cont WorkOS explicat discret în header și card cont/instalare.
- Self-only clar; read-only fără butoane de editare pontaj.
- Review separat de cererile proprii; self-approve interzis (backend).
- Stări loading/empty/error unificate local (`EmployeeMobileStates`).
- PWA install informativ, fără buton fake.

## Ce construim

- Home dashboard cu rezumat cereri/pontaj (din API existent).
- Bottom navigation + header cu user hint.
- Componente state locale reutilizabile.
- Polish requests, attendance, review panels.
- Teste frontend țintite.

## Ce nu construim

Manager team attendance, payroll, push, offline sync, auth rewrite, native app, DB migration, backend permission changes, global design system rewrite.

## Acceptance criteria

- `/employee-app` coerent și util ca dashboard.
- Rute requests/attendance/review accesibile din nav.
- Same-account copy păstrat.
- Self attendance read-only.
- Review separat + 403 clar pentru non-manager.
- PWA install card informativ.
- Teste țintite PASS.

## Related

- `docs/architecture/EMPLOYEE_IDENTITY_SESSION_AND_PWA_DECISION.md`

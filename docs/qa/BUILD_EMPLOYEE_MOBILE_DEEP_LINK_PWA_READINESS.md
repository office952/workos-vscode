# BUILD: Employee Mobile Deep-Link Safety + PWA Readiness

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `494908e` — `feat(employee): clarify employee admin and mobile identity` |
| **HEAD after** | _(pending owner confirm)_ |
| **Status** | PASS (targeted tests + manual smoke) |

## 1. Scop build

1. **Deep-link safety** — `employee_mobile` nu vede UI manager/admin la URL direct (`/review`, `/team`).
2. **PWA readiness** — polish shell mobil, manifest, instalare browser fără push/offline/native.

## 2. Rute permise (UI guard)

| Rută | `employee_mobile` | `admin` / `manager` |
|------|-------------------|---------------------|
| `/employee-app` (home) | ✓ | ✓ |
| `/employee-app/requests` | ✓ | ✓ |
| `/employee-app/attendance` | ✓ | ✓ |
| `/employee-app/review` | **blocat UI** | ✓ |
| `/employee-app/team` | **blocat UI** | ✓ |

**Regulă:** UI guard = UX + deep-link safety. Backend guards = securitate reală (403 pe API).

## 3. Audit (read-only)

### Deep link — înainte

| Persona | `/review` | `/team` |
|---------|-----------|---------|
| `employee_mobile` | Shell Review + panel (confuz); API 403 | Shell Team (confuz) |
| `admin` | OK | OK |

Nav/dashboard ascundeau deja Review/Echipa mea pentru `employee_mobile`; deep link rămânea deschis.

### PWA — înainte

| Aspect | Stare |
|--------|--------|
| Manifest | `public/manifest.webmanifest` — `start_url: /employee-app`, `display: standalone` |
| Icon | `/icons/workos-icon.svg` |
| Service worker | **Nu** |
| Install UX | Card static manual (Share / meniu browser) |
| Safe area | Padding fix `pb-28`, fără `env(safe-area-inset-*)` |
| `background_color` manifest | `#ffffff` (mismatch față de shell `#070B14`) |

## 4. Implementare

### Fișiere modificate

| Fișier | Schimbare |
|--------|-----------|
| `frontend/src/lib/employeeMobileAccess.ts` | `canAccessEmployeeMobileRoute`, path helper, mesaje blocked |
| `frontend/src/lib/employeeMobileAccess.test.ts` | Teste route access |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileProtectedRoute.tsx` | **NOU** — wrapper guard |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileRouteBlocked.tsx` | **NOU** — ecran neutru + CTA acasă |
| `frontend/src/pages/EmployeeMobileApp.tsx` | Guard pe `review`/`team`; safe-area shell padding |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Teste deep link + install copy |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileShell.tsx` | Safe-area nav; install card îmbunătățit |
| `frontend/src/hooks/usePwaInstallPrompt.ts` | **NOU** — `beforeinstallprompt` fără SW nou |
| `frontend/public/manifest.webmanifest` | `background_color` aliniat shell |
| `frontend/index.html` | `viewport-fit=cover` |
| `docs/qa/BUILD_EMPLOYEE_MOBILE_DEEP_LINK_PWA_READINESS.md` | Acest document |

### Route guard

- Rute `review` și `team` învelite în `EmployeeMobileProtectedRoute`.
- Fără acces → `EmployeeMobileRouteBlocked` (mesaj RO + „Înapoi la acasă”).
- Fără apel API manager înainte de guard.

### PWA / shell

- Manifest `background_color` → `#070B14`.
- Viewport `viewport-fit=cover`; padding shell/nav cu `safe-area-inset`.
- Install card: status manual / ready / installed; buton instalare când browser emite `beforeinstallprompt`.
- Clarificare: fără push, fără offline în acest build.

### Neatinse

Backend, DB, seed-uri, auth, roluri, Axinte Remus, Calin Cimpean, ierarhii, direct reports, manager assignment, payroll, service worker complex, dependențe noi.

## 5. Deferred

| Item | Motiv |
|------|--------|
| Push notifications | Out of scope |
| Offline sync | Out of scope |
| Service worker avansat | Infrastructură inexistentă |
| Native app | Out of scope |
| Route capabilities DTO backend | UI guard suficient acum |
| Manifest separat doar Employee Mobile | Global manifest deja `start_url: /employee-app` |

## 6. Smoke verificat

### employee_mobile (`dev-employee-test-001`)

- `/employee-app`, `/requests`, `/attendance` — OK
- `/review`, `/team` — ecran blocked, fără UI manager
- Nav fără Review; dashboard fără Echipa mea

### admin (`dev-admin-user-00000000`)

- Review + Echipa mea vizibile și accesibile deep link
- Install/account UI OK

## 7. Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/employeeMobileAccess.test.ts `
  src/pages/EmployeeMobileApp.test.tsx
```

## 8. Boundary păstrat

- `employee_mobile`: fără Review/Echipa mea în nav/dashboard; deep link blocked UI
- `admin`/`manager`: Review + Echipa mea accesibile
- Backend guards neschimbate

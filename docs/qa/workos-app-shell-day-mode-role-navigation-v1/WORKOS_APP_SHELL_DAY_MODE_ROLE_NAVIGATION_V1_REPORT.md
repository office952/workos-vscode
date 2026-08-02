# WorkOS App Shell + Day Mode + Role Navigation V1 — Report

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Track | **U** (Wave 0) |
| Status | **PASS WITH WARNINGS** |
| Branch | `feat/app-shell-day-mode-role-nav-v1` |
| Worktree | `C:\w\workos_ui_wave0_v1` |
| Base HEAD | `2ea7de82` |
| Runtime identity | FE **`http://127.0.0.1:3020`** (worktree Vite) · API **`http://127.0.0.1:8000`** (existing; BE `:8020` not started) |
| Boundary | Frontend shell / RBAC nav / day tokens only — **no** `backend/**`, no MaterializedOpsGraph / OperatorView / ShopFloor / ExecutionDetail / Pricing logic / Employee Mobile / Intake V6 component rewrites |

---

## 1. Goal

Unify day-mode shell tokens, Romanian-first navigation (drop “(registry)”), and role-based visibility so each persona sees one clear ops home — without deleting routes or inventing a fake role switcher.

---

## 2. Code changes (allowlist)

| Path | Change |
|------|--------|
| `frontend/src/components/workos/AppShell.tsx` | **NEW** — extracted shell chrome; renders `<Outlet />` |
| `frontend/src/lib/shellNavigation.ts` | **NEW** — Romanian IA groups + route map |
| `frontend/src/lib/shellNavigation.test.ts` | **NEW** — projection tests |
| `frontend/src/lib/rbac.ts` | Extended `NavItem` / permissions; fail-closed `canViewNav`; Ops-Graph manager/admin; demos via DEV auth |
| `frontend/src/lib/rbac.test.ts` | Expanded role / nav assertions |
| `frontend/src/lib/personalNavigation.ts` | Romanian labels; drop “registry” |
| `frontend/src/lib/personalNavigation.test.ts` | Updated expectations |
| `frontend/src/App.tsx` | Router ownership kept; imports `AppShell`; business routes as children |
| `frontend/src/contexts/AuthContext.tsx` | `DEV_FALLBACK_USER.role = "admin"` (preserves DEV full nav when `/auth/me` unavailable) |
| `frontend/src/index.css` | Day-mode sidebar/topbar force-light |
| `frontend/scripts/ci-unit-tests.txt` | Allowlist `shellNavigation.test.ts`, `personalNavigation.test.ts` |

**Not touched:** `backend/**`, MaterializedOpsGraph, OperatorView, ShopFloor, ExecutionDetail, Pricing business logic, Employee Mobile pages, Intake V6 components. Routes not deleted.

---

## 3. Navigation IA (stable URLs)

| Group | Items (route) |
|-------|----------------|
| Lucrări | Cereri `/intake` · Produse `/product-system/products` · Oferte `/quotes` · Comenzi `/orders` |
| Producție | Planificare `/execution` · Ops-Graph `/execution/ops-graph` · Atelier `/tablet` · Control producție `/dashboard` · Shop Floor · Operator |
| Oameni | Angajați · Pontaj · Evidență HR |
| Resurse | Utilaje · Inventar · Prețuri `/inventory/pricing` |
| Relații | Clienți · Colaboratori · Documente |
| Management | Rapoarte · Plăți · Avansuri |
| Administrare | Harta · Guvernanță · Setări (admin) |
| DEV tooling | Demos + Intake V6 diag + Blueprint + Rapoarte operaționale — only when `VITE_ENABLE_DEV_AUTH` (non-prod) |

Full matrix: [`role-visibility-matrix.md`](./role-visibility-matrix.md).

---

## 4. Day-mode verdict

**PASS for shell chrome.**

Evidence:

- Screenshot `screenshots/shell/00-app-shell-day-mode.png` / `01-sidebar-day-mode.png`
- Capture probe: sidebar background `rgb(255, 255, 255)`, `data-day-shell="true"`, `html.light`
- CSS: `html.light .workos-app-sidebar { background-color: #ffffff; }` + lightened `--wo-*` day tokens

Page interiors still carry night-era slate/hex — see [`remaining-page-dark-islands.md`](./remaining-page-dark-islands.md) (**34** in-shell page modules + **3** standalone deferred).

---

## 5. Role matrix summary

| Role | Sees | Hides |
|------|------|-------|
| viewer | Control producție (+ DEV tooling if flag) | Everything else |
| operator | Atelier, Shop Floor, Operator, Control, Utilaje, Inventar | Lucrări, HR, money, Prețuri, Administrare |
| sales | Lucrări, Planificare, Inventar, Relații, Rapoarte | Shop ops peers, HR, money, Prețuri, Administrare, Ops-Graph |
| manager | Broad ops + HR + Plăți + Ops-Graph | Prețuri, Avansuri, Administrare |
| admin | Full IA including Prețuri / Avansuri / Administrare | — |

Screenshot proof: `screenshots/roles/{admin,manager,sales,operator,viewer}-shell.png` (roles mocked via `/api/v1/auth/me` intercept — **no UI role switcher**).

---

## 6. DEV auth preservation (before / after)

### Before (baseline behavior, preserved)

| Mechanism | Behavior |
|-----------|----------|
| `VITE_ENABLE_DEV_AUTH=true` | AuthContext may enter `dev_auth_enabled` + `DEV_FALLBACK_USER` when `/auth/me` fails/empty |
| `VITE_DEV_GUARD_BYPASS=true` or `sessionStorage WORKOS_DEV_GUARD_BYPASS=1` | `RuntimeProtectedOutlet` allows preview without real session |
| `VITE_DEV_GUARD_ALLOWLIST` | Path allow-list bypass |
| Bypass UI buttons | “Bypass temporar preview” / “Oprește bypass” still in `RuntimeProtectedOutlet` |
| `WORKOS_DEV_AUTH_USER_ID` (backend) | Impersonates user for `/auth/me`; FE never invents a switcher |
| Capture token | `__DEV_BYPASS_TOKEN__` in localStorage (same as U1) |

### After (Wave 0)

| Mechanism | Status |
|-----------|--------|
| All of the above | **Preserved** in `App.tsx` / `AuthContext` |
| `DEV_FALLBACK_USER` | Still present; **added** `role: "admin"` so shell nav is not fail-closed to viewer when `/auth/me` is unavailable |
| Unknown role | Still `resolveRole` → `viewer`; nav fail-closed |
| Unknown nav key | `canViewNav` → `false` |
| DEV tooling section | Shown only when `isDevEnvironment()` (`VITE_ENABLE_DEV_AUTH` + non-prod) |

### Commands used this GO

```powershell
# Worktree FE on 3020 (product changes) against existing API :8000
cd C:\w\workos_ui_wave0_v1\frontend
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
$env:VITE_ENABLE_DEV_AUTH='true'
$env:VITE_DEV_GUARD_BYPASS='true'
npx --yes pnpm@8.10.0 exec vite --port 3020 --host 127.0.0.1 --strictPort

# Targeted tests
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/rbac.test.ts `
  src/lib/shellNavigation.test.ts `
  src/lib/personalNavigation.test.ts `
  src/App.test.tsx

# Screenshots (Playwright via createRequire(frontend/package.json))
node docs/qa/workos-app-shell-day-mode-role-navigation-v1/_capture_shell.mjs
# U_BASE_URL default http://127.0.0.1:3020 · token __DEV_BYPASS_TOKEN__ · workos-theme light
```

**Note:** Existing `:3000` was **not** used for proof (likely other checkout). `:8020` BE was **not** started — FE `:3020` + API `:8000` identity is recorded here. LocalApiCompatibilityBanner reported API mismatch / unavailable components during capture (warning only).

---

## 7. Tests

| Suite | Result |
|-------|--------|
| `rbac.test.ts` | PASS (26) |
| `shellNavigation.test.ts` | PASS (14) |
| `personalNavigation.test.ts` | PASS (6) |
| `App.test.tsx` | PASS (8) |
| **Total** | **54 PASS** |

---

## 8. Screenshots

| Folder | Contents |
|--------|----------|
| `screenshots/shell/` | Day-mode shell + sidebar |
| `screenshots/roles/` | admin / manager / sales / operator / viewer |
| `screenshots/representative-pages/` | Control, Cereri, Oferte, Planificare, Atelier, Prețuri, Angajați, Setări |

---

## 9. Warnings / blockers

| Severity | Item |
|----------|------|
| WARNING | Capture against existing `:8000` showed LocalApiCompatibilityBanner (“Backend local indisponibil” / missing components). Shell/nav still rendered; KPI data empty. Prefer dedicated `:8020` next time if identity must match worktree BE. |
| WARNING | DEV tooling visible to all roles when `VITE_ENABLE_DEV_AUTH` is on (by design). Production builds keep it off. |
| WARNING | Page-level dark islands remain (**34** modules) — out of shell scope. |
| INFO | Shop Floor / Operator labels left in EN (route/product names); groups and primary labels Romanian-first. |
| BLOCKER | None for shell ACCEPT. |

---

## 10. Remaining dark islands count

| Bucket | Count |
|--------|------:|
| Shell | **0** |
| In-shell page modules (code hits) | **34** |
| Standalone deferred apps | **3** |

Details: [`remaining-page-dark-islands.md`](./remaining-page-dark-islands.md).

---

## 11. Next

1. Owner visual ACCEPT of day-mode shell + Romanian IA.
2. Optional Wave 0.1: hide DEV tooling behind admin-only even in DEV.
3. Wave 1: day-mode page interiors (Quotes / Orders / ShopFloor / Tablet).

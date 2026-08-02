# Agent C — Dashboard → Intake V6 Navigation Review

**Repo:** `C:\w\psiso` @ `6c3af83d`  
**Mode:** READ-ONLY product code (docs/screenshots evidence only)  
**Runtime:** FE `http://127.0.0.1:3000` (vite pid 28172) · BE `:8000` (uvicorn pid 30760)  
**Date:** 2026-08-02

## Verdict: **FAIL**

Dashboard does **not** provide a correct visible entry to Intake V6. The primary CTA lands on the legacy Cereri list; the shell-canonical Intake V6 route is blocked by the `demos` path guard and redirects to Dashboard.

---

## 1. Canonical Intake V6 route (from code)

| Route | Component | Notes |
|-------|-----------|--------|
| **`/intake-v6/operator`** | `IntakeV6OperatorWorkspaceApp` | Shell route; App comment: “V6 is the only active intake operator flow.” |
| **`/intake-v6/:workspaceId/operator`** | same | Workspace operator |
| `/intake-v6-app/operator` (+ `/:workspaceId/operator`) | `IntakeV6StandaloneRoot` | Outside AppShell; works at runtime; **no Dashboard/nav entry** |
| Helpers | `intakeV6OperatorRoutes.ts` | `INTAKE_V6_SHELL_BASE = "/intake-v6"` |

Legacy / list routes:

| Route | Behavior |
|-------|----------|
| `/intake` | `WorkIntake` list (Cereri) |
| `/intake/:id` | `IntakeLegacyRoute` → `Navigate` to `buildIntakeV6Path(id)` |

---

## 2. Dashboard entry details (code + UI)

**Page:** `frontend/src/pages/Dashboard.tsx`  
**Quick actions row** (“Acțiuni rapide:”):

| Control | Text | Icon | Position | Target |
|---------|------|------|----------|--------|
| Primary button | **Cerere Nouă** | `Plus` | First quick action (info/primary style) | `navigate("/intake")` — **not** V6 |
| Others | Oferte / Comenzi / Execuție / Atelier / Rapoarte | various | same row | `/quotes`, `/orders`, `/execution`, `/shop-floor`, `/reports` |

**Shell nav** (`shellNavigation.ts`):

| Item | Label | `to` | `navKey` | Visibility |
|------|-------|------|----------|------------|
| Lucrări | Cereri | `/intake` | `intake` | `view:intake` (sales/manager/admin) |
| DEV tooling | Intake V6 (diag) | `/intake-v6/operator` | `demos` | `VITE_ENABLE_DEV_AUTH===true` **and** `role===admin` only |

**RBAC / path guard (blocking):**

```ts
// shellNavigation.pathAllowedForRole
if (pathname.startsWith("/intake-v6") || pathname.startsWith("/demo/")) {
  return canViewNav(role, "demos"); // admin + DEV auth only
}
```

`ShellPathGuard` redirects disallowed paths to `getRoleHomePath(role)` (admin → `/dashboard`).

Roles with `view:intake` / `edit:intake`: **sales, manager, admin**.  
**operator** / **viewer**: no Cereri.  
**Intake V6 shell path** currently requires **demos**, not `view:intake`.

Running FE (`vite --host 127.0.0.1 --port 3000`) has **no** `VITE_ENABLE_DEV_AUTH` in process command line; `frontend/.env.local` has no `VITE_ENABLE_DEV_AUTH`. DEV tooling section **not** visible at runtime.

---

## 3. Browser steps and results

| # | Step | Result |
|---|------|--------|
| 1 | Open `/dashboard` | OK — Control producție; quick action **+ Cerere Nouă** visible |
| 2 | Screenshot before click | `agent-c-01-dashboard-before-click.png` |
| 3 | Click **Cerere Nouă** | URL → `http://127.0.0.1:3000/intake` (WorkIntake Cereri list) — **not** V6 |
| 4 | Screenshot after click | `agent-c-02-after-dashboard-cerere-noua-click.png` |
| 5 | Direct `/intake-v6/operator` | **Redirect → `/dashboard`** (shell guard) |
| 6 | Refresh / Back / Forward | History only between `/intake` and `/dashboard`; never stayed on V6 shell |
| 7 | Dashboard → Cerere Nouă again | Again `/intake` |
| 8 | Cereri → “Deschide Intake V6” | Navigates toward V6 then **guard redirects → `/dashboard`** |
| 9 | Legacy `/intake/IR-…` | Bridge to V6 then **guard redirects → `/dashboard`** |
| 10 | Standalone `/intake-v6-app/operator` | **Works** — Intake V6 operator UI (`…/intake-v6-app/{uuid}/operator`) |
| 11 | sales role probe (`workos-dev-role=sales`) | Still has Cerere Nouă → `/intake`; direct shell V6 still redirected away |

No 404 / blank page on Dashboard→Cereri. Failure mode is **wrong destination** + **shell V6 inaccessible**.

---

## 4. Screenshot paths

All under `docs/qa/workos-f7a-owner-review-v1/screenshots/`:

- `agent-c-01-dashboard-before-click.png`
- `agent-c-02-after-dashboard-cerere-noua-click.png`
- `agent-c-03-direct-intake-v6-operator.png` (shows redirect = Dashboard)
- `agent-c-04` … `agent-c-07` (refresh/back/forward/again)
- `agent-c-08-sales-dashboard.png` / `agent-c-09-sales-direct-intake-v6.png`
- `agent-c-10-standalone-intake-v6-app.png` (**only successful V6 surface**)
- `agent-c-11` … `agent-c-13` (shell retry / legacy bridge / Cereri open → Dashboard)

JSON: `agent-c-dashboard-intake-v6-nav-results.json`, `agent-c-followup-results.json`.

---

## 5. Console / network

Capture sessions: **no console errors** (beyond filtered React Router future warnings) and **no `/api/` 4xx/5xx** attributed to these navigations. Failures are client-side route guards / wrong CTA target.

---

## 6. Blocking findings

1. **Dashboard CTA is not Intake V6** — `Dashboard.tsx` `navigate("/intake")` opens legacy Cereri list.  
2. **Shell-canonical `/intake-v6/*` is gated as `demos`** — sales/manager (and admin without DEV auth flag) are redirected to role home; “Deschide Intake V6” and legacy bridge are ineffective in AppShell.  
3. **No visible Dashboard/shell production entry labeled Intake V6** — only optional DEV “Intake V6 (diag)”, absent on this runtime.  
4. **Standalone `/intake-v6-app/*` works** but is orphaned from Dashboard/Cereri IA.

### Files likely involved (for a **separate** UI build — no fix in this review)

- `frontend/src/pages/Dashboard.tsx` (Cerere Nouă target)
- `frontend/src/lib/shellNavigation.ts` (`pathAllowedForRole` demos gate; nav IA)
- `frontend/src/lib/rbac.ts` (`canViewNav` demos / `view:intake`)
- `frontend/src/components/workos/ShellPathGuard.tsx`
- `frontend/src/App.tsx` (route registration)
- `frontend/src/pages/WorkIntake.tsx` + `frontend/src/lib/volumetricIntakeRoute.ts` (list → V6 handoff)
- `frontend/src/pages/IntakeLegacyRoute.tsx`

### Proposed separate UI build scope (do not implement here)

1. Treat `/intake-v6/operator` as production intake path under `view:intake` (not `demos`).  
2. Retarget Dashboard **Cerere Nouă** (and align Cereri primary create) to Intake V6 bootstrap.  
3. Keep `/intake` as list hub if needed, but ensure “Deschide Intake V6” / legacy `:id` succeed inside AppShell.  
4. Demote or remove “Intake V6 (diag)” confusion once production entry exists.  
5. Decide shell vs `/intake-v6-app` story for operators.

### Reproduction

1. Open `http://127.0.0.1:3000/dashboard` (authenticated admin-capable session).  
2. Click **Acțiuni rapide → Cerere Nouă** → observe `/intake` Cereri list.  
3. Open `http://127.0.0.1:3000/intake-v6/operator` → observe redirect to `/dashboard`.  
4. Optional: open `/intake-v6-app/operator` → Intake V6 loads (proves app works; entry path broken).

---

**No product code changes. No commit. No push.**

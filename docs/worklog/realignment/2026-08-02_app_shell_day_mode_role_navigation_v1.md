# Worklog — App Shell + Day Mode + Role Navigation V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Track | U / Wave 0 |
| Branch | `feat/app-shell-day-mode-role-nav-v1` |
| Worktree | `C:\w\workos_ui_wave0_v1` |
| Base | `2ea7de82` (full route UI/UX baseline) |
| Status | Implemented — local commit pending ACCEPT |

## Intent

After the full-route UI/UX baseline, Owner needed a coherent day-mode Romanian shell before further page polish. Wave 0 extracts AppShell, regroups nav, wires RBAC projection, and removes the dark sidebar island.

## What changed

- Extracted `AppShell` from `App.tsx`; router ownership stays in `App.tsx` via nested routes + `<Outlet />`.
- Added `shellNavigation.ts` with Romanian groups (Lucrări / Producție / Oameni / Resurse / Relații / Management / Administrare / DEV tooling).
- Extended `rbac` nav map; unknown role/nav fail-closed; demos gated by `VITE_ENABLE_DEV_AUTH`.
- Dropped “(registry)” from nav labels; Pricing → Prețuri; Control Tower → Control producție.
- Day tokens + `html.light` sidebar force-white.
- `DEV_FALLBACK_USER` keeps DEV preview; set `role: admin` so nav is usable without `/auth/me`.

## Evidence

QA pack: `docs/qa/workos-app-shell-day-mode-role-navigation-v1/`

- Report, role matrix, remaining dark islands
- Screenshots under `screenshots/{shell,roles,representative-pages}/`
- Vitest: rbac + shellNavigation + personalNavigation + App.test (54 PASS)

## Boundaries respected

No backend, no OpsGraph/Operator/ShopFloor/ExecutionDetail/Pricing logic edits, no Employee Mobile / Intake V6 component rewrites, no route deletion, no fake role switcher.

## Open follow-ups

- Page-level day-mode debt (~34 modules)
- Optional: restrict DEV tooling to admin even when DEV auth is on
- Prefer FE `:3020` + BE `:8020` identity for future captures when API compatibility banner fires

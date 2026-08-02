# Design decision — Dashboard → Intake V6 canonical entry

**Date:** 2026-08-02  
**Agent:** C  
**Scope:** Frontend shell navigation + Dashboard CTA only (no backend).

## Chosen variant

**Dashboard primary CTA (`Cerere Nouă`) → `/intake-v6/operator` (shell bootstrap).**

That route is already registered on `IntakeV6OperatorWorkspaceApp`. When no workspace id is in the URL, `useIntakeV6Workspace` creates a workspace and replaces the location with `/intake-v6/{workspaceId}/operator`. No hardcoded workspace/order/demo user.

Helpers already encode this:

- `INTAKE_V6_SHELL_BASE = "/intake-v6"`
- `buildIntakeV6Path()` / `buildIntakeV6OperatorBootstrapPath()` → `/intake-v6/operator`

## Why not the alternatives

| Alternative | Rejected because |
|-------------|------------------|
| Keep `/intake` (legacy Cereri list) as CTA | Owner FAIL: lands on list hub, not the active operator flow. App treats V6 as the only active intake operator surface. |
| Standalone `/intake-v6-app/operator` | Works, but lives outside AppShell — orphaned from Dashboard/nav and role path guards. Canonical shell base is `/intake-v6`. |
| New workspace list / selector page | No existing production list-selector flow for V6 operator entry; inventing one expands scope and delays the bootstrap path that already exists. |
| Point shell nav **Cereri** at `/intake-v6/operator` | Cereri list remains useful as a hub for existing requests; primary *create* entry is Dashboard CTA + V6 bootstrap. List stays at `/intake`. |

## Access policy change

| Path | Before | After |
|------|--------|-------|
| `/intake-v6/*` | `demos` (admin + DEV auth only) → redirect to role home | `view:intake` (sales / manager / admin) |
| `/demo/*` | `demos` | unchanged (`demos`) |
| `/intake` list | `view:intake` | unchanged (list hub) |
| Unauthorized roles (operator / viewer) | blocked from intake | still blocked from `/intake-v6/*` |

## Nav IA note

- Remove **Intake V6 (diag)** from DEV tooling once production entry exists (Dashboard CTA + allowed shell path).
- Keep **Cereri** → `/intake` as the list hub (not the primary create entry).

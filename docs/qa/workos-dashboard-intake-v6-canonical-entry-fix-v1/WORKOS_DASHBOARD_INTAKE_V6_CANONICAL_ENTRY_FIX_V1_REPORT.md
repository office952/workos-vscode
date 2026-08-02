# WORKOS Dashboard → Intake V6 Canonical Entry Fix v1

## Verdict

```text
DASHBOARD → INTAKE V6 CANONICAL ENTRY FIX = PASS
POST MATERIALIZE = NOT EXECUTED
PUSH = NOT EXECUTED
```

## Design

See `design-decision.md`. Chosen path: Dashboard CTA → `/intake-v6/operator` bootstrap (creates workspace, replaces to `/intake-v6/{id}/operator`).

## Implementation

| Change | Detail |
|--------|--------|
| `Dashboard.tsx` | `Cerere Nouă` → `buildIntakeV6Path()` (= `/intake-v6/operator`) |
| `shellNavigation.ts` | `/intake-v6/*` allowed for `view:intake`; `/demo/*` remains demos |
| DEV nav | Removed **Intake V6 (diag)** |
| Cereri list | Remains `/intake` as hub (not primary create) |

## Browser proof (admin @ `:3000`)

| Step | Result |
|------|--------|
| Dashboard before click | CTA **Cerere Nouă** visible in Acțiuni rapide |
| Click | URL → `/intake-v6/operator` then replace → `/intake-v6/{uuid}/operator` |
| UI | Intake V6 operator workspace (Litere volumetrice / Straturi) |
| Direct `/intake-v6/operator` | Creates workspace; no redirect to `/dashboard` |
| Refresh on workspace URL | Stays on V6 operator |
| No Intake V6 (diag) in nav | Confirmed |

Screenshots: `screenshots/f7a1-c-01-*.png` … `f7a1-c-03-*.png`

## Tests

```text
vitest: Dashboard.quickActions + shellNavigation = 19 passed
tsc --noEmit = PASS
```

## UI/UX opinion

CTA works and lands in the real operator flow. Position (quick actions under KPI/gap noise) is acceptable but not heroic — operator still finds it as the primary blue button. **Cereri** list hub remains legacy `/intake`; that is intentional for existing requests, but a future polish could add a secondary “Deschide Intake V6” that stays shell-allowed. Day theme preserved; no parallel redesign.

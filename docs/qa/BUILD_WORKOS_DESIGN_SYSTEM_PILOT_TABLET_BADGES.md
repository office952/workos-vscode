# BUILD — WorkOS Design System Pilot 06: Tablet Badges

## Purpose

Adopt WorkOS design-system `SourceBadge` and `StatusBadge` in **Tablet / stații operaționale** UI only. Visual/semantic cleanup with **no** workflow, live bridge, task lifecycle, or backend changes.

## Scope

### In scope

- Replace local `TabletSourceBadge` inline spans with design-system `SourceBadge` (preserving RO labels and live-empty semantics)
- Replace task status inline spans on task cards + task detail header with `StatusBadge` domain `executionTask`
- Preserve tablet task RO labels via `TASK_STATUS_CONFIG` + `label` prop
- Targeted Vitest + read-only runtime smoke
- No token changes (`executionTask` domain already sufficient)

### Out of scope / boundaries

- No DB, seed, migrations, backend changes
- No CostEngine, Pricing, Quotes, Orders, Operator, Execution, Employee Payments, ProductSystem, Work Intake, Commercial Document
- No App shell / `index.css` / `tailwind.config` changes
- No tablet workflow, task actions, assignment, filters, live bridge, polling, or station routing changes
- No commit (manual commit-tree pending)

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/TabletMode.tsx` | `SourceBadge` + `StatusBadge` adoption; mapping helpers |
| `frontend/src/pages/TabletMode.live.test.tsx` | Update live badge text expectation (`Live DB`) |
| `frontend/src/pages/TabletMode.badges.test.tsx` | **New** design-system badge tests |

## Modules touched

- `TabletStationSelector`, `TabletStationQueue`, `TabletTaskDetail` (via shared components in `TabletMode.tsx`)
- `TaskCard` status badge only

**Untouched:** `useTabletStationData`, `tabletLiveBridge`, `EligibilityBadge`, operator availability dots, URGENT/mapping badges, help request UI, action buttons, layouts.

## Local badges removed/replaced

| Location | Before | After |
|----------|--------|-------|
| `TabletSourceBadge` | Inline spans (Live / Live DB (gol) / Eroare API / Demo fallback / Se încarcă) | Design-system `SourceBadge` via `resolveTabletSourceBadge()` |
| `TaskCard` | `TASK_STATUS_CONFIG` inline span | `StatusBadge domain="executionTask"` with RO `label` |
| `TabletTaskDetail` header | `TASK_STATUS_CONFIG` inline span | Same `StatusBadge` pattern |

**Left unchanged:** `EligibilityBadge`, attachment status chips, operator status dots, sync error span, help/urgent/mapping badges.

## Source semantics

Maps existing `useTabletStationData().source` + `operatorSource` — **no logic change**:

| Tablet `source` | `operatorSource` | `SourceBadge` | Label |
|-----------------|------------------|---------------|-------|
| `loading` | * | `loading` | Se încarcă |
| `live` | db/empty | `db` | Live DB (default) |
| `empty` | db/empty | `empty` | Live DB (gol) |
| `error` | error | `error` | Eroare API |
| `demo` | mock | `mock` | Demo fallback |
| `demo` | other | `demo` | Demo fallback |

Live empty ≠ mock/disconnected preserved (same rules as `da57fe7` / Operator fix).

## Task statuses covered

Display uses RO labels from `TASK_STATUS_CONFIG`. Badge `status` key uses `task.liveStatus` when present, else maps tablet status → `executionTask`:

| Tablet status | executionTask key | RO label (preserved) |
|---------------|-------------------|----------------------|
| in_coada | created | În coadă |
| pregatit | assigned | Pregătit |
| in_lucru | in_progress | În lucru |
| blocat | blocked | Blocat |
| finalizat | done | Finalizat |
| predat | completed | Predat |
| necesita_clarificare | blocked | Necesită clarificare |
| ajutor_cerut / ajutor_preluat | paused | Ajutor cerut / preluat |

Live operator statuses (`assigned`, `in_progress`, `blocked`, etc.) pass through via `liveStatus`.

## Token mappings added

**None** — existing `executionTask` domain covers mapped keys.

## Tests run + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/TabletMode.badges.test.tsx `
  src/pages/TabletMode.live.test.tsx `
  src/hooks/useTabletStationData.test.ts
```

**Result: PASS — 5 files, 59 tests**

Note: `tabletLiveBridge.test.ts` lives under `frontend/wip/operational-registry/` (not in main test path); not run.

## Runtime smoke (read-only)

| Route | Result |
|-------|--------|
| `/tablet` | PASS — loads; `SourceBadge data-source=db` text "Live DB"; station grid visible; no false mock banner on selector |
| `/tablet/montaj_autocolant` | PARTIAL — page loads; task card + demo operators visible in a11y snapshot; after settle CDP observed `data-source=empty` (Live DB gol) with empty status badges — possible live/demo state flip or first-load flash (deferred) |
| `/tablet/montaj_autocolant/TT-009` | PASS — demo task detail loads; checklist + disabled demo actions visible; layout intact |

No task actions executed. No DB writes.

## Visual before/after summary

- Source badge: unified pill shape/tone with design system; RO labels preserved (`Se încarcă`, `Eroare API`, `Demo fallback`)
- Task status: design-system badge on cards/detail; RO labels unchanged; touch card layout unchanged
- Tablet density: `size="sm"` + `text-[11px]` on badges; button/card sizes unchanged

## Deferred items

- Tablet deeper layout polish / dedicated density tokens
- First-load demo flash on station routes (observed intermittently on `/tablet/montaj_autocolant` — separate from badge build)
- Commercial Document visual output (Pilot 07 candidate)
- Global shell polish
- `EligibilityBadge` design-system adoption (operator eligibility, not task status)

## READY

**READY for manual commit-tree review** — targeted tests green, smoke read-only acceptable with noted partial route, boundaries respected, no commit performed.

# BUILD — Secondary Source Badge Pilot (Safe Cleanup)

## Status

**Implementation: NOT EXECUTED**

Blocked by prior **Label Parity Audit** — no `CLEAN NOW` items were confirmed. This build requires explicit label parity before replacing local badges.

## Purpose

Replace local source badges in secondary modules (`Colaboratori`, `Personal`, `ShopFloor`, `Utilaje`) with design-system `SourceBadge`, only where label parity is exact or owner-approved.

## Prerequisite audit

See label parity findings (conversation / prior audit). Summary:

| File | Blocker |
|------|---------|
| `Colaboratori.tsx` | `empty`/`error` → `"No Data"` ≠ DS `"Live DB (gol)"` / `"Source Error"` |
| `Personal.tsx` | same as Colaboratori |
| `ShopFloor.tsx` | `empty` → `"Empty"` ≠ DS `"Live DB (gol)"` |
| `Utilaje.tsx` | `empty`/`error` → `"No Data"`; local fn shadows `SourceBadge` |

## CLEAN NOW list (confirmed before edit)

```text
Clean now:
(none — audit found zero safe 1:1 replacements)
```

**STOP condition met:** empty CLEAN NOW list → no runtime edits in this build.

## Owner decisions required before retry

1. **Empty label:** canonical `"Live DB (gol)"` (recommended) vs per-module `label` override
2. **Error visibility:** adopt `"Source Error"` where locals currently show `"No Data"` for `error` state
3. **Loading:** hide (current) vs DS `"Loading"` spinner

## Recommended pilot order (after approval)

1. `ShopFloor.tsx` — error already aligned; only empty label decision
2. `Utilaje.tsx` — error + empty + rename local helper
3. `Colaboratori.tsx` / `Personal.tsx` — error + empty parity

## Scope (when implemented)

### In scope

- Replace local `DataSourceBadge` / shadow `SourceBadge` with DS `SourceBadge`
- Minimal badge adoption tests per page
- Preserve guards (`canCreateCollaborator`, `RegistryResourceEditor`, shop-floor alert source logic)

### Out of scope (boundaries)

- No DB / backend / API / business logic changes
- No CostEngine / Pricing / Quote-Order workflow
- No export / App shell / `index.css` / `tailwind.config`
- No status lifecycle / mock fallback / warning hiding
- No `StatusBadge` changes (collab status, role badges, connection pills stay local)

## Files changed (this build)

| File | Change |
|------|--------|
| `docs/qa/BUILD_WORKOS_SECONDARY_SOURCE_BADGE_PILOT.md` | **New** — blocked pilot record |

**Runtime:** none.

## Tests

Not run for implementation (no code changes). Prior design-system sanity: 44 passed (from consolidation audit).

## Runtime smoke

**N/A** — no pages touched.

## Deferred items

All four candidate files remain deferred until owner label decisions above.

## Next step

Re-run **Safe Cleanup** build after owner confirms empty/error/loading label strategy; start with `ShopFloor.tsx` only (single-file pilot).

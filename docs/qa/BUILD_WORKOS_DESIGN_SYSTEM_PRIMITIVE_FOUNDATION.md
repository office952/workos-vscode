# BUILD: WorkOS Design System — Primitive Foundation

**Date:** 2026-06-12  
**Status:** **PASS — uncommitted**  
**Branch:** `local/integration-pr4-plus-svg-path` @ `39ad338`  
**Prerequisite:** `39ad338 docs(design): add WorkOS visual identity charter`

---

## 1. Purpose

Ship the **minimal technical foundation** for the WorkOS design system:

- `tokens.ts` — surfaces, borders, text, accent, semantic tones, status/source maps, pure helpers
- `StatusBadge` — rectangular entity status badge
- `SourceBadge` — rounded data-source indicator
- Targeted Vitest coverage

**No rollout** to production pages in this build.

---

## 2. Scope

### Included

| Item | Path |
|------|------|
| Design tokens + helpers | `frontend/src/components/workos/design-system/tokens.ts` |
| StatusBadge | `frontend/src/components/workos/design-system/StatusBadge.tsx` |
| SourceBadge | `frontend/src/components/workos/design-system/SourceBadge.tsx` |
| Barrel export | `frontend/src/components/workos/design-system/index.ts` |
| Tests | `StatusBadge.test.tsx`, `SourceBadge.test.tsx` |
| This QA doc | `docs/qa/BUILD_WORKOS_DESIGN_SYSTEM_PRIMITIVE_FOUNDATION.md` |

### Explicitly excluded

| Area | Action |
|------|--------|
| Page rollout | **No** — Quotes, Orders, Operator, Tablet, Employee Payments, WorkIntake untouched |
| `index.css` | **No changes** |
| `tailwind.config` | **No changes** |
| App shell / global layout | **No changes** |
| Fonts | **Not imported** |
| Backend / DB | **No changes** |
| Seed / migrations | **Not run** |
| CostEngine / Pricing | **Not touched** |
| `docs/mockups/` | **Not touched** |
| Git commit | **Not performed** |

---

## 3. Token structure

### Hex reference (JS const)

- **Surfaces:** app, shell, surface, surfaceRaised, input, inset
- **Borders:** subtle, strong
- **Text:** primary, secondary, muted, dim
- **Accent:** primary, primaryHover, violet, cyan

### Semantic tones (Tailwind classes)

Each tone defines: `bg`, `text`, `border`, `dot`

| Tone | Typical use |
|------|-------------|
| slate | neutral / unknown / cancelled task |
| blue | sent, confirmed, assigned |
| cyan | viewed, delivered, adjusted |
| violet | priced, locked |
| emerald | accepted, paid, live, verified |
| amber | negotiating, mock, demo, paused |
| orange | partial payment, advance |
| red | rejected, blocked, error, invalidated |

### Pure helpers

| Helper | Behavior |
|--------|----------|
| `getStatusTone(domain, status)` | Unknown → `slate`; null → `slate`; no throw |
| `getSourceTone(source)` | Unknown → `slate`; no throw |
| `normalizeStatusLabel(domain, status)` | RO labels; unknown → title-case key |
| `normalizeSourceLabel(source)` | Fixed labels for db/empty/mock/… |
| `getToneClasses(tone)` | Returns Tailwind class set |

---

## 4. Status mappings included

| Domain | Keys (minimum) |
|--------|----------------|
| quote | draft, priced, sent, viewed, negotiating, accepted, rejected, expired, cancelled |
| order | created, confirmed, locked, in_execution, in_productie, completed, delivered, cancelled, anulat |
| executionTask | created, planned, assigned, in_progress, running, paused, blocked, done, completed, cancelled, anulat |
| payment | due, unpaid, pending, partial, advance, paid, cancelled, adjusted, missing_base |
| reality | reported, verified, valid, invalidated |
| source | db, empty, mock, demo, error, loading, mixed |

---

## 5. Components

### StatusBadge

- Rectangular `rounded-[6px]`, bordered, tinted background
- Props: `domain`, `status`, `label?`, `size`, `icon?`, `className`, `title?`
- Uses `cn` from `@/lib/utils`
- Default size: `sm`

### SourceBadge

- `rounded-full` (source indicator, not entity status)
- Lucide icons: Database, HardDrive, AlertTriangle, Loader2, GitBranch
- Special variants: `empty` (muted emerald), `mixed` (slate, non-live)

---

## 6. Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx
```

**Result:** **PASS** — 2 files, 16 tests, 0 failures (2026-06-12)

```
✓ StatusBadge.test.tsx  (8 tests)
✓ SourceBadge.test.tsx  (8 tests)
```

---

## 7. Boundary

This build **does not** authorize:

- Replacing local `DataSourceBadge` / `QuoteStatusBadge` in pages yet
- Adding `--wo-*` to global CSS
- Changing status lifecycle or business logic

---

## 8. Next recommended build

**Pilot adoption — owner decision required**

Options (Phase 3 entry):

1. **Employee Payments** — replace payment status chips + add SourceBadge when live wiring expands
2. **Work Intake V2** — readiness/status chips aligned to Operational Precision
3. **Quotes / Orders** — replace duplicated badge configs (higher regression surface)

Recommended sequence per charter:

1. Owner picks pilot module
2. Replace local badges in **one module only**
3. Targeted Vitest + existing module tests
4. Document in new `BUILD_*` QA file

Open decisions:

- First pilot module?
- Replace local `DataSourceBadge` before or after StatusBadge pilot?
- Start Work Intake vs Employee Payments?

---

## 9. PASS / FAIL

| Gate | Result |
|------|--------|
| tokens.ts + helpers | **PASS** |
| StatusBadge + SourceBadge | **PASS** |
| No page rollout | **PASS** |
| No CSS/tailwind/shell | **PASS** |
| No backend/DB | **PASS** |
| Targeted tests | **PASS** (16/16) |

---

*Build log — primitive foundation only. No production page behavior changed.*

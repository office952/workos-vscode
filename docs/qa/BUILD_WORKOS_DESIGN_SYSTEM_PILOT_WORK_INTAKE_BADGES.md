# BUILD: WorkOS Design System Pilot 01 — Work Intake Badges

**Date:** 2026-06-12  
**Status:** **PASS — uncommitted**  
**Branch:** `local/integration-pr4-plus-svg-path` @ `fbf41da`  
**Prerequisite:** `fbf41da feat(design-system): add WorkOS badge primitives`

---

## 1. Purpose

First **real-page pilot** of shared design-system primitives on Work Intake (`/intake`):

- Replace local `DataSourceBadge` → `SourceBadge`
- Replace local status badge → `StatusBadge` via `IntakeStatusBadge` wrapper
- Preserve layout, logic, flow, and status lifecycle

Visual-only pilot — no business logic refactor.

---

## 2. Scope

### Included

| Change | Detail |
|--------|--------|
| Work Intake page | `frontend/src/pages/WorkIntake.tsx` |
| Design-system tokens | Added `intake` domain to `tokens.ts` |
| StatusBadge tests | 3 new intake domain tests |
| Work Intake badge tests | New `WorkIntake.badges.test.tsx` (7 tests) |

### Explicitly excluded

| Area | Action |
|------|--------|
| WorkIntakeV2 | **Not touched** |
| Quotes / Orders / Operator / Tablet / EmployeePayments / ProductSystem | **Not touched** |
| `index.css` / `tailwind.config` | **No changes** |
| App shell / global layout | **No changes** |
| Backend / DB / seed / migrations | **No changes** |
| Status lifecycle / API calls | **No changes** |
| Work Intake → Quote flow | **Unchanged** |
| Git commit | **Not performed** |

---

## 3. Audit summary (pre-change)

| Question | Finding |
|----------|---------|
| Local `DataSourceBadge`? | Yes — inline in `WorkIntake.tsx` (db/mock/mixed/error/empty; loading → null) |
| Local `StatusBadge`? | Yes — inline component + `statusConfig` |
| Intake statuses used | `new`, `in_review`, `needs_info`, `ready_for_quote`, `blocked`, `cancelled` |
| Badge locations | Page header (source), list rows, detail panel; pipeline cards use `statusConfig` directly (unchanged) |
| Existing tests | `WorkIntake.routing.test.tsx`, `WorkIntake.draftQuote.test.tsx`, `WorkIntake.pagination.test.tsx` |

---

## 4. Local badges removed / replaced

| Removed | Replaced with |
|---------|---------------|
| `DataSourceBadge` (local function) | `<SourceBadge source={intakeSource} />` where `intakeSource = sourcesDetail.intakes ?? source` |
| `StatusBadge` (local function) | `IntakeStatusBadge` wrapper → `<StatusBadge domain="intake" … />` |

**Kept:** `statusConfig` + `PipelineCard` — pipeline KPI cards still use local config for icon/label (not entity list badges).

**Removed imports:** `Database`, `HardDrive` (only used by old source badge).

---

## 5. Design-system changes

### New `intake` domain in `tokens.ts`

| Status | Tone | Label RO |
|--------|------|----------|
| new | slate | Nou |
| in_review | blue | În Analiză |
| needs_info | amber | Lipsă Info |
| ready_for_quote | emerald | Gata pt. Ofertă |
| blocked | red | Blocat |
| cancelled | slate | Anulat |
| quoted / converted | violet | Ofertat / Convertit |

### Source badge behavior change (intentional)

| Source | Before (local) | After (SourceBadge) |
|--------|----------------|---------------------|
| empty | "No Data" (slate) | "Live DB (gol)" (emerald muted) — aligns with design-system charter |

---

## 6. Files changed

```
frontend/src/pages/WorkIntake.tsx
frontend/src/components/workos/design-system/tokens.ts
frontend/src/components/workos/design-system/StatusBadge.test.tsx
frontend/src/pages/WorkIntake.badges.test.tsx   (new)
docs/qa/BUILD_WORKOS_DESIGN_SYSTEM_PILOT_WORK_INTAKE_BADGES.md
```

---

## 7. Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/WorkIntake.badges.test.tsx `
  src/pages/WorkIntake.routing.test.tsx `
  src/pages/WorkIntake.draftQuote.test.tsx `
  src/pages/WorkIntake.pagination.test.tsx
```

**Result:** **PASS** — 6 files, 39 tests, 0 failures

| File | Tests |
|------|-------|
| StatusBadge.test.tsx | 11 |
| SourceBadge.test.tsx | 8 |
| WorkIntake.badges.test.tsx | 7 |
| WorkIntake.routing.test.tsx | 4 |
| WorkIntake.draftQuote.test.tsx | 3 |
| WorkIntake.pagination.test.tsx | 6 |

---

## 8. Runtime smoke

**Target:** `http://127.0.0.1:3000/intake`  
**Result:** **PASS** (2026-06-12, stack already running)

| Check | Result |
|-------|--------|
| Page loads | ✓ 4 intakes from live DB |
| SourceBadge | ✓ `Live DB`, `data-source="db"` |
| StatusBadge (list) | ✓ 4 badges `data-status-domain="intake"`; tones blue/emerald |
| Pipeline | ✓ counts visible (0/1/0/3/0) |
| List / detail | ✓ selected `WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` (ready_for_quote) |
| Detail actions | ✓ „Continuă în WorkIntake V2”, „Creează Ofertă Draft” present |
| Mock warning | ✓ absent on live source |
| Console | ✓ no errors observed during navigation |
| Quote flow | ✓ not exercised (no new intake/quote created) |

---

## 9. Visual impact (before / after notes)

**Before:**

- Local rounded-full source badge with custom emerald/amber/slate classes
- Local rectangular status badge with inline Tailwind per status
- Empty source labeled "No Data"

**After:**

- Shared `SourceBadge` (rounded-full, lucide icons, charter labels)
- Shared `StatusBadge` (rectangular 6px, semantic tones via `intake` domain)
- Icons preserved on status badges via `IntakeStatusBadge` wrapper
- Pipeline cards visually unchanged

---

## 10. Next recommended pilot

Based on Work Intake success:

1. **Employee Payments** — high Figma alignment, isolated payment status chips + future live source badge
2. **Quotes** — larger surface; replace `QuoteStatusBadge` + `DataSourceBadge` duplicates

Owner decisions still open:

- Replace local `DataSourceBadge` in Orders/Operator next, or continue StatusBadge pilots?
- Employee Payments vs Quotes as Pilot 02?

---

## 11. PASS / FAIL

| Gate | Result |
|------|--------|
| Work Intake only | **PASS** |
| No CSS/shell/backend | **PASS** |
| intake domain added + tested | **PASS** |
| Existing WorkIntake tests green | **PASS** |
| New badge tests | **PASS** |
| Runtime smoke | **PASS** |

---

*Pilot 01 — visual badge adoption only. No production logic changed.*

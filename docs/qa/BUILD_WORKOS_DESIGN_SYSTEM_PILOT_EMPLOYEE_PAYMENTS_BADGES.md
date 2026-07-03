# BUILD: WorkOS Design System Pilot 02 — Employee Payments Badges

**Date:** 2026-06-12  
**Status:** **PASS — uncommitted (runtime smoke not run)**  
**Branch:** `local/integration-pr4-plus-svg-path` @ `3053826`  
**Prerequisite:** `3053826 feat(work-intake): adopt design system badges`, `fbf41da feat(design-system): add WorkOS badge primitives`

---

## 1. Purpose

Apply shared design-system primitives to **Plăți angajați** (`/employee-payments`):

- `SourceBadge` for data source indicator
- `StatusBadge domain="payment"` for slot payment states
- Extend payment token mappings for Romanian slot statuses + employee-payments context

**No financial logic changes** — salary base, 15/30 schedule, confirm/cancel recording unchanged.

---

## 2. Scope

### Included

| Item | Path |
|------|------|
| Employee Payments page | `frontend/src/pages/EmployeePayments.tsx` |
| Payment token mappings | `frontend/src/components/workos/design-system/tokens.ts` |
| StatusBadge payment tests | `frontend/src/components/workos/design-system/StatusBadge.test.tsx` |
| Page badge tests | `frontend/src/pages/EmployeePayments.badges.test.tsx` (new) |
| Updated page tests | `frontend/src/pages/EmployeePayments.test.tsx` |
| This QA doc | `docs/qa/BUILD_WORKOS_DESIGN_SYSTEM_PILOT_EMPLOYEE_PAYMENTS_BADGES.md` |

### Explicitly excluded

| Area | Action |
|------|--------|
| Financial calculation | **Unchanged** |
| Salary source (`salary_amount` / profile) | **Unchanged** |
| 15/30 slot split | **Unchanged** |
| `createPayment` / confirm / cancel | **Unchanged** |
| Backend / DB / seed / migrations | **Not touched** |
| Other modules (Quotes, Orders, Operator, WorkIntake V2, etc.) | **Not touched** |
| `index.css` / `tailwind.config` / App shell | **Not touched** |
| Git commit | **Not performed** |

---

## 3. Audit findings (pre-change)

| Question | Finding |
|----------|---------|
| Local `DataSourceBadge`? | **No** — hardcoded shadcn `Badge` text `LIVE DB` in header |
| Local payment status badge? | **Yes** — `PaymentStatusBadge` using shadcn `Badge` + inline Tailwind |
| Statusuri afișate | `neplatit`, `partial`, `platit` (UI); API maps `unpaid`/`partial`/`paid`/`missing_base` |
| Badge locations | Header (source), list row, detail panel header; history uses plain text not badges |
| Existing tests | `EmployeePayments.test.tsx` (9 tests); `workforceRoutes.test.tsx` (employee-payments case — pre-existing mock/env issues) |
| Zones left unchanged | Summary cards, filters, form, breakdown math, history list, missing-base warning panel, save/cancel flow |

---

## 4. Badge replacements

| Before | After |
|--------|-------|
| `<Badge>LIVE DB</Badge>` (static) | `<SourceBadge source={situations.length === 0 ? "empty" : "db"} />` |
| `PaymentStatusBadge` (shadcn + inline classes) | Wrapper → `<StatusBadge domain="payment" … />` with `slotPaymentStatusKey()` |

**Preserved:** shadcn `Badge` for meta chips (`Manual`, `Fără stat de plată fiscal`, `Pontaj incomplet`).

**Source semantics:**

- Successful API load with employees → `db` → **Live DB**
- Successful API load, zero employees → `empty` → **Live DB (gol)**
- No mock/demo path added (page uses direct API only)

**Label preservation:** `slotStatusLabel()` still provides `Neplătit` / `Parțial` / `Plătit`.

**Tone change (visual only):** rows with `missingBase` use payment status key `missing_base` (red tone) while label remains `Neplătit` — clearer data-problem signal without changing status derivation logic.

---

## 5. Token mapping updates (`payment` domain)

| Status key | Tone | Notes |
|------------|------|-------|
| `paid` / `platit` | emerald | unchanged intent |
| `partial` | orange | matches prior Employee Payments orange |
| `unpaid` / `due` / `pending` / `neplatit` | amber | aligned with Employee Payments neplătit chip |
| `missing_base` | red | data problem — was amber in tokens, now red for clarity |
| `advance` | cyan | optional alias |
| `adjusted` | violet | optional alias |
| `cancelled` | slate | history / records |

Added Romanian aliases: `neplatit`, `platit`.

---

## 6. Payment statuses validated

| UI / API | StatusBadge key | Label shown |
|----------|-----------------|-------------|
| Slot neplătit | `unpaid` | Neplătit |
| Slot parțial | `partial` | Parțial |
| Slot plătit | `paid` | Plătit |
| Missing salary base (list row) | `missing_base` | Neplătit (label preserved) |

---

## 7. Salary / payment logic — explicitly unchanged

- Base: `employee_profile_salary` / `salary_amount` via `employeePaymentLiveMapper`
- Schedule: half-month slots 15/30 from profile salary
- Recording: `employeePaymentsApi.createPayment` + refetch
- No changes to `employeePaymentLiveMapper.ts`, API client, or backend

---

## 8. Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/EmployeePayments.test.tsx `
  src/pages/EmployeePayments.badges.test.tsx
```

**Result:** **PASS** — 4 files, 36 tests, 0 failures

| File | Tests |
|------|-------|
| StatusBadge.test.tsx | 14 |
| SourceBadge.test.tsx | 8 |
| EmployeePayments.test.tsx | 9 |
| EmployeePayments.badges.test.tsx | 5 |

**Not run (pre-existing / out of scope):**

- `workforceRoutes.test.tsx` employee-payments case — fails without API mock (`Failed to parse URL`); unrelated to badge change

---

## 9. Runtime smoke

**Route:** `/employee-payments`

**Result:** **NOT RUN** — frontend dev server unreachable at test time (`http://localhost:3000` connection refused).

When stack is running, verify:

1. Page loads
2. `SourceBadge` → Live DB
3. Payment status badges rectangular (design-system)
4. Andrei 8000 → 4000/slot, Chirila 7000 → 3500, Vali 5000 → 2500
5. Save payment form visible for valid employees
6. Missing base warning for employees without salary
7. No Mock/Demo source badge on live data

---

## 10. Visual before / after

**Before:**

- Static uppercase `LIVE DB` shadcn pill
- Payment status via shadcn `Badge` + inline amber/orange/emerald classes

**After:**

- Shared `SourceBadge` (rounded-full, lucide Database, charter label)
- Shared `StatusBadge` rectangular 6px, semantic payment tones
- Meta badges (`Manual`, fiscal disclaimer) unchanged

---

## 11. Boundaries

- No DB / backend / seed / migrations
- No CSS global / shell / other modules
- No financial logic or payment action behavior changes

---

## 12. Next recommended pilot

**Pilot 03 options (owner decision):**

1. **Quotes** — replace `QuoteStatusBadge` + local source badge
2. **Orders / Operator** — deduplicate `DataSourceBadge` + order/payment status badges

Open decisions:

- Pilot 03 module priority
- Replace Orders/Operator `SourceBadge` before or after Quotes status badges
- Keep payment labels local vs centralize in design-system (currently local override via `slotStatusLabel`)

---

## 13. PASS / FAIL

| Gate | Result |
|------|--------|
| Employee Payments only | **PASS** |
| SourceBadge + StatusBadge adopted | **PASS** |
| Financial logic unchanged | **PASS** |
| Targeted tests | **PASS** (36/36) |
| Runtime smoke | **NOT RUN** (stack down) |
| Commit | **N/A** |

**Overall build:** **PASS** (pending manual runtime smoke when stack available)

---

*Pilot 02 — visual badge adoption on Plăți angajați only.*

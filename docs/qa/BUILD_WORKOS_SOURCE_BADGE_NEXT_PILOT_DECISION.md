# BUILD — Design System Source Badge Validation + Next Pilot Decision

## Status

**Implementation: NOT EXECUTED** (audit + decision only)

ShopFloor pilot (`fd3b394`) validated. Next cleanup pilot identified but deferred to a dedicated follow-up build.

## Purpose

Validate ShopFloor `SourceBadge` adoption operatorially, audit remaining secondary modules, and choose at most one next pilot — without mass cleanup.

## Prerequisite

- Branch: `local/integration-pr4-plus-svg-path`
- HEAD: `fd3b394` — `feat(design-system): consolidate ShopFloor source badge`
- Prior pilot QA: `docs/qa/BUILD_WORKOS_SHOPFLOOR_SOURCE_BADGE_PILOT.md`

---

## TASK 1 — ShopFloor validation

### A. Code audit

| Check | Result |
|-------|--------|
| Local `DataSourceBadge` removed | ✅ |
| DS `SourceBadge` used | ✅ |
| Mapping presentation-only (`mapShopFloorSourceToBadge`) | ✅ |
| `mock` → `demo` | ✅ |
| `empty` / `error` / `loading` pass-through | ✅ |
| `runtimeAlerts` mock guard preserved | ✅ |
| Error + empty warning banners preserved | ✅ |
| Connection pills (Connected / Reconnecting) unchanged | ✅ |

### B. Runtime smoke (read-only)

Route: `http://127.0.0.1:3000/shop-floor`

| Check | Result |
|-------|--------|
| Page loads | ✅ |
| Source badge visible | ✅ `Live DB` (`data-source="db"`, emerald) |
| Empty label `Live DB (gol)` | ⚪ not observed live (fixture has machines); covered by unit tests |
| Warnings preserved | ✅ (none on live-db fixture — expected) |
| Console errors | ✅ none observed |
| Visual density | ✅ badge `text-[10px]` inline with title; does not dominate |
| Distinct from operational status | ✅ separate from Connected pill, blocked jobs pill, `JobStatusBadge` |

**Operator verdict:** ShopFloor pilot **ACCEPT** — clearer empty canonical label vs old `Empty`; no ambiguity introduced on live fixture.

### C. Tests

| Suite | Result |
|-------|--------|
| `StatusBadge.test.tsx` | 36 passed |
| `SourceBadge.test.tsx` | 8 passed |
| `ShopFloor.badges.test.tsx` | 5 passed |
| **Total** | **49 passed** |

`tsc -b --noEmit`: **FAIL** — 3 pre-existing errors (unrelated):

1. `QuoteCommercialActionPanel.badges.test.tsx` — missing `intakeId`
2. `EmployeePayments.tsx` — `RecordedPaymentEntry` undefined
3. `Pricing.badges.test.tsx` — incomplete `PricingRegistryResponse` mock

**Confirmed:** no errors in `ShopFloor.tsx`, `ShopFloor.badges.test.tsx`, or design-system files.

---

## TASK 2 — Candidate audit matrix

Canonical labels (owner):

```text
live      = Live DB
empty     = Live DB (gol)
error     = Source Error
loading   = Loading
mock/demo = Demo
```

### Colaboratori.tsx

```text
File: frontend/src/pages/Colaboratori.tsx
Local source states: db | mock | empty | error | loading (useColaboratoriData)
Current labels:
  db     → Live DB
  mock   → Mock Data
  empty  → No Data  ⚠
  error  → No Data  ⚠ (same as empty)
  loading → hidden
Business meaning:
  empty = API OK, suppliers list length 0, mock disabled
  error = API failure, mock disabled
Warnings affected:
  red error banner (error && source !== mock)
  amber create guard (!canCreateCollaborator)
sourcesDetail used: no
SourceBadge DS equivalent: pass-through + mock→demo (like ShopFloor)
Label parity: FAIL today (empty/error collapsed to No Data)
Risk: MEDIUM — canCreateCollaborator = db|empty; new empty label must stay aligned with create-enabled UX
Recommendation: DEFER — validate create-flow UX with Live DB (gol) before badge swap
```

### Personal.tsx

```text
File: frontend/src/pages/Personal.tsx
Local source states: db | mock | empty | error | loading (usePersonalData)
Current labels:
  db     → Live DB
  mock   → Mock Data
  empty  → No Data  ⚠
  error  → No Data  ⚠
  loading → hidden (full-page spinner replaces header)
Business meaning:
  empty = employees API OK, zero rows, mock disabled
  error = employees API failure, mock disabled
  mock  = demo HR roster (CostEngine employees API fallback)
Warnings affected: none dedicated (error in hook, no error banner in page)
sourcesDetail used: no
SourceBadge DS equivalent: pass-through + mock→demo
Label parity: FAIL today
Risk: MEDIUM-HIGH — HR demo vs live semantics; operator may confuse Demo roster with live HR truth
Recommendation: DEFER — needs owner sign-off on Demo label for HR module
```

### Utilaje.tsx

```text
File: frontend/src/pages/Utilaje.tsx
Local source states: db | mock | empty | error | loading (useMachinesData)
Current labels:
  db     → Live DB (emerald)
  mock   → Mock Data (amber)
  empty  → No Data (amber)  ⚠
  error  → No Data (amber)  ⚠ — should be red Source Error
  loading → hidden
Business meaning:
  empty = /api/v1/machines OK, zero rows, mock disabled
  error = API failure, mock disabled
  mock  = mock registry fallback
Warnings affected:
  static amber create-blocked banner (not source-gated)
  RegistryResourceEditor gated on source === "db"
sourcesDetail used: no
SourceBadge DS equivalent: pass-through + mock→demo; hook already distinguishes empty vs error
Label parity: FAIL in local badge only (hook semantics OK)
Risk: LOW-MEDIUM — shadow local fn named SourceBadge; badge-only swap; same API family as ShopFloor
Recommendation: CLEAN NOW for next dedicated pilot
```

### KEEP LOCAL (not source badges)

| Module | Component | Reason |
|--------|-----------|--------|
| Colaboratori | `CategoryBadge`, `StatusBadge` | Operational collab status |
| Personal | `RoleBadge`, `StatusDot` | HR role/status |
| Utilaje | `MntTypeBadge`, machine status dots | Maintenance / machine operational markers |

---

## TASK 3 — Next pilot decision

**Chosen module (one only):** `Utilaje.tsx`

**Why not implement in this build:** scope is audit + decision; ShopFloor validation must land before second pilot; no runtime edits without dedicated build boundary.

**Why Utilaje over Colaboratori / Personal:**

1. Lowest structural risk — hook states mirror ShopFloor (`useMachinesData` / machines API)
2. Closest pattern to completed ShopFloor pilot
3. Badge collapse is presentation-only fix (hook already sets `empty` vs `error`)
4. No `sourcesDetail` aggregate risk
5. No HR-specific demo semantics debate (unlike Personal)
6. Simpler workflow guards than Colaboratori create flow

### Mini-plan (next build — do not execute here)

**Mapping:**

| Hook `source` | DS `source` | Label |
|---------------|-------------|-------|
| `db` | `db` | Live DB |
| `empty` | `empty` | Live DB (gol) |
| `error` | `error` | Source Error |
| `loading` | `loading` | Loading |
| `mock` | `demo` | Demo |

**Files to modify:**

- `frontend/src/pages/Utilaje.tsx` — remove local `SourceBadge`; import DS; add `mapUtilajeSourceToBadge` (or reuse shared helper pattern from ShopFloor)
- `frontend/src/pages/Utilaje.badges.test.tsx` — **new** minimal badge tests

**Test plan:**

- DS sanity (`StatusBadge` + `SourceBadge`)
- `Utilaje.badges.test.tsx` — db, empty, error, mock fixtures
- `tsc -b --noEmit` — accept pre-existing debt if unchanged files clean

**Smoke plan (read-only):**

- `/utilaje` loads
- Live fixture → `Live DB`
- Warnings (create-blocked banner) still visible
- `RegistryResourceEditor` still appears only when `source === "db"` and machine selected
- No console errors

**Deferred:**

- `Colaboratori.tsx` — DEFER (create guard + empty label UX review)
- `Personal.tsx` — DEFER (HR demo/live operator semantics)

---

## Boundaries (this build)

- no backend
- no DB
- no API
- no business logic
- no App shell
- no CSS/tailwind
- no status lifecycle
- no runtime changes in this build

## Files changed (this build)

| File | Change |
|------|--------|
| `docs/qa/BUILD_WORKOS_SOURCE_BADGE_NEXT_PILOT_DECISION.md` | **New** — validation + decision record |

## Recommended commit message

```text
docs(design): document source badge next pilot decision
```

## Next step

Dedicated build: **Utilaje Source Badge Pilot** using mini-plan above. Do not batch Colaboratori/Personal.

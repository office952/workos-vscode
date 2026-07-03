# Internal Commercial Spine Demo

**Route:** `/demo/commercial-spine`  
**Audience:** Developers and operators (internal/onboarding only)  
**Template scope:** `TPL-VOLUMETRIC-LETTERS` only

## Purpose

Prove the stabilized volumetric commercial spine is real and traceable in the running app:

```
Quote readiness → Quote convert → Order detail → Execution detail → Execution plan 201
```

This is **not** a public sales demo. It does not claim all templates are production-ready.

## What it proves

- Live backend `quote_gate` is surfaced in Quotes UI (readiness panel)
- Primary fixture converts without acknowledgement when `requires_acknowledgement: false`
- WARN fixture requires inline acknowledgement before convert
- Quote-derived volumetric orders can generate execution plan **201** with tasks
- No `readiness_overlay` fixture hack — gate comes from backend policy

## What it does not prove

- Other product templates or families
- Public/customer-facing sales readiness
- Inventory, pricing formula correctness, or CostEngine internals
- Unsupported template activation

## Setup

### 1. Seed deterministic fixtures

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:APP_ENV='development'
cd backend
.\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py
```

Creates:

| Quote | Scenario |
|-------|----------|
| `QT-E2E-COMMERCIAL-001` | Ready — `requires_acknowledgement: false` |
| `QT-E2E-COMMERCIAL-WARN-001` | Warn — `requires_acknowledgement: true`, `operations_missing` pending |

### 2. Start backend + frontend

```powershell
# Backend :8000 (project standard)
cd backend
.\.venv\Scripts\uvicorn.exe main:app --reload --port 8000

# Frontend :3000 (Vite proxy to API)
cd frontend
npm run dev
```

### 3. Open demo

http://localhost:3000/demo/commercial-spine

The page probes fixture status from the **live backend API** (no local manifest file reads in the browser).

## Scenario walkthroughs

### A. Ready quote (`QT-E2E-COMMERCIAL-001`)

1. Demo card → **Open Quote**
2. Confirm volumetric readiness panel: **Ready** or **Ready with warnings**
3. `requires_acknowledgement: false`
4. **Transformă în Comandă** enabled (priced/accepted)
5. Convert → `/orders/:orderCode`
6. **Open Execution** → generate plan → expect **201**, tasks > 0

### B. Warning acknowledgement (`QT-E2E-COMMERCIAL-WARN-001`)

1. Demo card → **Open Quote**
2. Status: **Requires acknowledgement**
3. `(operations_missing)` in ack-pending section
4. Convert **disabled** until checkbox: *Confirm că am verificat avertizările comerciale…*
5. Check acknowledgement → convert enabled → convert
6. Order + execution plan same as scenario A

## Expected states (after seed)

| Field | Primary | WARN |
|-------|---------|------|
| `readiness_overlay` | `null` | `null` |
| `can_create_commercial_quote` | `true` | `true` |
| `requires_acknowledgement` | `false` | `true` |
| `acknowledgement_pending` | `[]` | `["operations_missing"]` |

## E2E tests

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npm run test:e2e:commercial          # all commercial specs (live → warn-ack → demo smoke)
npm run test:e2e:commercial-live
npm run test:e2e:commercial-warn-ack
npm run test:e2e:commercial-spine-demo
```

Re-seed if fixture quotes were already converted.

## Known caveats

- Demo route is **not** in production sidebar navigation
- Order/execution links appear only after conversion (no fake IDs)
- WARN quote must be re-seeded after warn-ack E2E converts it
- Demo page requires backend session/dev auth like other protected routes

## Related commits

- `43635cf` — stabilize volumetric commercial spine to execution
- `717b4d7` — expose volumetric quote readiness acknowledgement UX
- `821bd37` — internal commercial spine demo

## See also

- `docs/architecture/VOLUMETRIC_COMMERCIAL_SPINE_STATUS.md` — consolidated spine status

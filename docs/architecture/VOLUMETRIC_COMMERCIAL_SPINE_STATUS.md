# Volumetric Commercial Spine — Current Status

**Last updated:** 2026-06-07  
**Template scope:** `TPL-VOLUMETRIC-LETTERS` only  
**Status:** Stabilized for tested fixture paths (ready + warn-ack → execution plan **201**)

## 1. Status summary

| Path | Fixture quote | Result |
|------|---------------|--------|
| Primary ready | `QT-E2E-COMMERCIAL-001` | convert → order → execution plan **201** |
| Warning acknowledgement | `QT-E2E-COMMERCIAL-WARN-001` | ack → convert → order → execution plan **201** |
| `readiness_overlay` | both fixtures | `null` (live gate only) |

Internal demo route: `/demo/commercial-spine` (dev/onboarding, not in sidebar).

## 2. Scope boundaries

- **In scope:** TPL-VOLUMETRIC-LETTERS commercial quote gate, conversion guard, order snapshot, execution plan generation for fixture-backed paths.
- **Out of scope:** Other templates/families, public sales readiness, CostEngine formula changes, inventory mutation policy, status lifecycle changes, unsupported template activation.
- **Fixtures:** `seed_commercial_e2e_fixture.py` — dev/E2E only, not production seed data.

## 3. Runtime flow

```
Intake / fixture seed
  → Quote priced with persisted readiness_result + quote_gate (line_items wrapper)
  → Quotes UI: list chip (compact) + VolumetricCommercialReadinessPanel (detail)
  → Conversion guard:
       can_create_commercial_quote === false  → blocked
       requires_acknowledgement === true      → disabled until inline ack
  → createOrderFromQuote (ack payload when required)
  → Order detail (quote snapshot frozen on order)
  → Execution: generate plan → HTTP 201, tasks for positive-time ops
```

### Key `quote_gate` fields

| Field | Meaning |
|-------|---------|
| `can_create_commercial_quote` | Hard allow/deny for convert |
| `requires_acknowledgement` | Operator must ack warnings before convert |
| `classified.acknowledgement_pending` | Codes awaiting acknowledgement |
| `blockers` / `warnings` | Backend-classified commercial readiness items |

Acknowledgement is **operator-visible** in Quotes detail (checkbox + reason), not silent bypass.

## 4. Test commands

### Seed (required before live E2E)

```powershell
$env:APP_ENV='development'
# Set DATABASE_URL to your local dev.db — see docs/demo/COMMERCIAL_SPINE_DEMO.md
cd backend
.\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py
```

### Frontend E2E

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npm run test:e2e:commercial          # all three specs in order
npm run test:e2e:commercial-live       # primary ready path (mutates fixture)
npm run test:e2e:commercial-warn-ack   # warn-ack path (mutates WARN fixture)
npm run test:e2e:commercial-spine-demo  # read-only demo smoke
```

Re-seed after mutation specs if re-running convert flows.

### Unit tests (readiness chip + panel)

```powershell
cd frontend
npm run test -- --run src/components/workos/VolumetricQuoteReadinessChip.test.tsx src/pages/Quotes.list.readiness.test.tsx src/pages/Quotes.readiness.test.tsx src/lib/volumetricQuoteReady.test.ts
```

## 5. Known caveats

- **ProductReadinessService** may still set `ready_for_quote: false` on global `needs_review`; volumetric commercial gate applies a **narrow override** via `can_create_commercial_quote`.
- Formula-priced operations with `estimated_minutes: 0` produce no plan tasks; only positive-time ops appear in execution plan.
- **List readiness chip** is compact summary; full explanation lives in `VolumetricCommercialReadinessPanel` on quote detail.
- Fixture must be seeded before live-db E2E; specs probe real backend state and fail if fixtures are missing.
- WARN fixture is consumed by warn-ack E2E — re-seed before re-run.

## 6. Do-not-change boundaries

Do not regress without explicit build:

- CostEngine pricing formulas
- Backend readiness policy semantics (`evaluate_volumetric_quote_ready`, conversion guards)
- Execution snapshot validation
- Quote/order status lifecycle
- Inventory deduction behavior
- Unsupported template activation
- Mock mutation safety in non-db modes

## 7. Related commits

| Commit | Description |
|--------|-------------|
| `43635cf` | Stabilize volumetric commercial spine to execution |
| `717b4d7` | Expose volumetric quote readiness acknowledgement UX |
| `bedc25f` | Warn-ack Playwright E2E |
| `821bd37` | Internal commercial spine demo route |
| *(finalization)* | Combined E2E, list chips, status doc — see `BUILD_VOLUMETRIC_COMMERCIAL_SPINE_FINALIZATION_PACK.md` |

## 8. Related documentation

- `docs/demo/COMMERCIAL_SPINE_DEMO.md` — operator walkthrough
- `docs/qa/BUILD_VOLUMETRIC_COMMERCIAL_READINESS_GATE.md` — readiness gate policy
- `docs/qa/BUILD_COMMERCIAL_WARN_ACK_E2E.md` — warn-ack E2E
- `docs/qa/BUILD_INTERNAL_COMMERCIAL_SPINE_DEMO.md` — demo build QA

## FigJam reference

Architecture board (local dev stack): file key `SQ1OvAy2AKV71WJhCaKzJV` — optional sticky updates only; not source of truth for gate semantics.

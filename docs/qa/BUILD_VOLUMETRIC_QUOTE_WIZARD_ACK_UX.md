# BUILD-VOLUMETRIC-QUOTE-WIZARD-ACK-UX

**Date:** 2026-06-07  
**Build status:** **PASS**  
**Prior commit:** `43635cfee260ff467f89516475a5fd2a48ec8937` (volumetric commercial spine)  
**This build commit:** not committed (per user rule)

## Summary

Operator-facing UX now surfaces the backend volumetric `quote_gate` in QuoteWizard, VolumetricLettersQuoteFlow, and Quotes detail — including status taxonomy, blocker/warning classification, reason codes, and proactive acknowledgement before order conversion.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/volumetricQuoteReady.ts` | Status taxonomy, classify items, label map, `extractQuoteReadinessFromLineItems` |
| `frontend/src/components/workos/VolumetricCommercialReadinessPanel.tsx` | Shared readiness panel + ack checkbox |
| `frontend/src/lib/mockData.ts` | `Quote.volumetricReadiness` |
| `frontend/src/lib/dataStore.ts` | Parse readiness from `line_items` |
| `frontend/src/pages/Quotes.tsx` | Panel, convert guard, proactive ack payload |
| `frontend/src/components/workos/QuoteWizard.tsx` | Use shared panel in simulation preview |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | Always show gate panel (not only when blocked) |
| `frontend/src/lib/volumetricQuoteReady.test.ts` | Extended unit tests |
| `frontend/src/components/workos/VolumetricCommercialReadinessPanel.test.tsx` | Panel rendering tests |
| `frontend/src/pages/Quotes.readiness.test.tsx` | Convert + ack UX tests |
| `backend/scripts/seed_commercial_e2e_fixture.py` | WARN variant `QT-E2E-COMMERCIAL-WARN-001` |
| `docs/qa/BUILD_VOLUMETRIC_QUOTE_WIZARD_ACK_UX.md` | This doc |

## UI behavior added

### Readiness panel (TPL-VOLUMETRIC-LETTERS)

- **Status:** Ready / Ready with warnings / Requires acknowledgement / Blocked
- **Metrics:** `can_create_commercial_quote`, `requires_acknowledgement`, blocker count, `ack_pending` count
- **Groups:** Blocking issues · Warnings requiring acknowledgement · Informational warnings
- **Each item:** friendly label + raw reason code + status tag
- **Reason codes:** collapsible list when present

### Locations

| Surface | testId |
|---------|--------|
| Quotes detail | `quote-volumetric-readiness` |
| QuoteWizard simulation | `wizard-volumetric-readiness` |
| VolumetricLettersQuoteFlow rail | `volumetric-flow-readiness` |

### Acknowledgement (Quotes convert)

- Checkbox shown only when `requires_acknowledgement === true` and quote is `priced` or `accepted`
- Label: *Confirm că am verificat avertizările comerciale și continui cu conversia.*
- Convert disabled until checked; hard blockers keep convert disabled (no ack bypass)
- Proactive POST body: `acknowledge_readiness_warnings: true` + reason string
- Reactive modal (`ReadinessWarningAcknowledgementModal`) retained for API 422 fallback

## Readiness fields displayed

From persisted `readiness_result.quote_gate` / live simulation `readiness.quote_gate`:

- `can_create_commercial_quote`
- `requires_acknowledgement`
- `blockers`, `warnings`, `notes`, `reason_codes`
- `classified.*` including `acknowledgement_pending`

## Acknowledgement behavior

| Gate state | Convert button | Checkbox |
|------------|----------------|----------|
| `can_create=false` | Disabled | Hidden |
| `can_create=true`, `requires_ack=false` | Enabled | “No acknowledgement required” (compact) |
| `can_create=true`, `requires_ack=true` | Disabled until checked | Required |

Backend `orders.py` remains source of truth; UI does not invent readiness.

## WARN fixture

| Field | Value |
|-------|-------|
| Intake | `WI-E2E-COMMERCIAL-WARN-001` |
| Quote | `QT-E2E-COMMERCIAL-WARN-001` |
| Injection | `operations_missing` in `technical_readiness.warnings` |
| `can_create_commercial_quote` | `true` |
| `requires_acknowledgement` | `true` |
| Primary PASS fixture | Unchanged (`QT-E2E-COMMERCIAL-001`) |

Live E2E for warn-ack path: **deferred** — covered by frontend unit tests + seed manifest `warn_fixture` block. Optional Playwright spec can target `QT-E2E-COMMERCIAL-WARN-001` in a follow-up.

## Tests run

```powershell
cd frontend
npm run test -- --run src/lib/volumetricQuoteReady.test.ts src/components/workos/VolumetricCommercialReadinessPanel.test.tsx src/pages/Quotes.readiness.test.tsx
npm run lint
```

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:APP_ENV='development'
cd backend
.\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py
.\.venv\Scripts\python.exe -m unittest tests.test_volumetric_quote_ready_policy -v
```

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npm run test:e2e:commercial-live
```

| Suite | Result |
|-------|--------|
| `volumetricQuoteReady.test.ts` | 7/7 OK |
| `VolumetricCommercialReadinessPanel.test.tsx` | 4/4 OK |
| `Quotes.readiness.test.tsx` | 2/2 OK |
| `npm run lint` | PASS |
| `tests.test_volumetric_quote_ready_policy` | 12/12 OK |
| `seed_commercial_e2e_fixture.py` | PASS — primary `requires_acknowledgement: false`, warn `requires_acknowledgement: true` |
| `test:e2e:commercial-live` | 1/1 OK (5.4s) |

## Follow-up: BUILD-COMMERCIAL-WARN-ACK-E2E (2026-06-07)

**Status:** PASS — see `docs/qa/BUILD_COMMERCIAL_WARN_ACK_E2E.md`

- `commercial-chain-warn-ack.spec.ts` + `npm run test:e2e:commercial-warn-ack` cover `QT-E2E-COMMERCIAL-WARN-001`
- Primary `test:e2e:commercial-live` still passes after re-seed

## Remaining gaps

- FigJam sticky optional — not updated
- Quotes list cards do not show readiness badge (detail panel only — intentional minimal scope)
- No combined npm script for both commercial E2E specs

## No-regression checklist

- [x] Readiness summary visible for volumetric quote (detail + wizard)
- [x] Blockers distinct from warnings
- [x] Reason codes visible
- [x] `requires_acknowledgement` displayed
- [x] Ack required only for warning-only pending state
- [x] Hard blockers still block conversion
- [x] Existing commercial-live E2E fixture unchanged at primary quote
- [x] No CostEngine / readiness policy semantic changes
- [x] QA doc created

## Suggested next substantial build

Combined `test:e2e:commercial` script + list-card readiness chip for priced volumetric quotes in pipeline view.

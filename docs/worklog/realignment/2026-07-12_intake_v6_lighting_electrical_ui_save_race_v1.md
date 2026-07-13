# Intake V6 — lighting/electrical UI save race finalization

**Task:** INTAKE_V6_LIGHTING_ELECTRICAL_UI_SAVE_RACE_FINALIZATION_V1
**HEAD before:** 4ec40ca
**Date:** 2026-07-12

## ZoneTitle compile fix

`IntakeV6ReviewLetterGroupsSection.tsx` was missing the `function ZoneTitle({` header — JSX props were orphaned after `layerTestIdSuffix`, breaking Vite/TS compile. Minimal two-line fix only.

## Save race root cause

1. Overlapping PUTs: each checkbox click fired `persistIfNeeded` without serializing requests; slower responses could overwrite newer scope on the server.
2. Stale `soldModules` closure on rapid toggles before re-render.
3. `inFlightSerializedRef` deduped identical payloads only, not concurrent different intents.
4. `persisted` closure in save callback could skip or mis-order saves relative to hydrated payload.

## Fix

- Sequential persist queue (`persistChainRef`) — one PUT at a time, always flush latest intent.
- `soldModulesRef` for toggle reads.
- `acknowledgedSerializedRef` tracks last known server state; dirty/confirmed derived from it.
- Trailing intent coalesced after each successful save.
- `isOfferScopeValid()` extended to accept `LIGHTING` / `ELECTRICAL` so Review step unlocks after subset save (no reload workaround).

## Evidence

- UI-driven Playwright: `frontend/e2e/intake-v6-lighting-electrical-scope-v1.spec.ts`
- Screenshots: `docs/qa/intake-v6-lighting-electrical-scope-v1/screenshots/`
- Report: `docs/qa/intake-v6-lighting-electrical-scope-v1/evidence_report.json`

## Validation

- Vitest: `IntakeV6OfferScopePanel.test.tsx` (13), `intakeV6Readiness.test.ts` (6) — PASS
- Backend: `test_intake_v6_lighting_electrical_scope.py`, `test_intake_v6_offer_scope_persistence.py`, `test_intake_v6_live_calc_offer_scope.py` — 36 PASS
- Playwright UI evidence spec — PASS (ui_driven, 5 PUTs, totals match fixture)
- Frontend build — PASS

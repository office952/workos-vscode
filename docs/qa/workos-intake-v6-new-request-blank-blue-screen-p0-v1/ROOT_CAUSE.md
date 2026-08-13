# ROOT CAUSE — Intake V6 new-request blank blue screen P0

## Verdict

```text
ROOT_CAUSE = frontend render exception in IntakeV6PricingInputPanel
  when offerModel.eurToRonRate is null (company FX not yet hydrated)
  → TypeError: Cannot read properties of null (reading 'toLocaleString')
  → uncaught React render crash
  → AppShell remains (blue / wo-surface-app) with empty outlet
ROOT_CAUSE_COMMIT = pre-existing panel null access (not introduced by 55017ec3 D2)
D2_CAUSED_REGRESSION = NO
```

## Causal chain

1. Operator opens `/intake-v6/:id/operator` (new or configured workspace).
2. Review step mounts commercial sliders (`IntakeV6PricingInputPanel` variant `commercialSliders`).
3. `useCompanyCommercialSettings` may still return `eurToRonRate = null` on first paint.
4. `buildIntakeV6OfferModel` keeps `eurToRonRate: null` for EUR internal estimates (by design — no silent FX invent).
5. Panel rendered: `offerModel.eurToRonRate.toLocaleString(...)` without null guard.
6. React throws during render. Intake V6 route had **no ErrorBoundary** → entire outlet blank; sidebar/shell stays → Owner “blue screen, no Intake V6 content”.

## Why it looked D2-related

D2 (`55017ec3`) changes first-load PQ/LL timing and can make “Recalculez oferta…” linger, but:

- Even with LL never running, the shell must still render.
- Proven blank was a **render exception**, not LL deadlock.
- Parent `979d22d2` contains the same `toLocaleString` call; blank is timing/race, not exclusive to D2.

## Secondary bootstrap hardening (same GO)

Not the blank-screen root, but proven thrash / UX hazards fixed together:

| Issue | Effect | Fix |
|-------|--------|-----|
| `getAnalysisIdentityKey` included `updated_at` | Every autosave cancelled PQ before settle / cleared D2 signal | Drop `updated_at` from identity |
| D2 reset effect after PQ | Settle could be wiped relative to PQ wave ordering | Reset before PQ; clear settle at PQ start; publish on finally (incl. gen 0/0) |
| `fetchStartedRef` not cleared on cleanup | Cancelled workspace GET might never retry | Clear ref on effect cleanup; cache-first hydrate |
| `ANALYZER_START/READY` for server SVG rehydrate | Forced Straturi + unsavedAnalysis | `mode: "server_rehydrate"` preserves step |
| No ErrorBoundary on Intake V6 | Crash → total blank | Boundary with visible Romanian error |

## Classification (A–J)

| Code | Result |
|------|--------|
| A frontend render exception | **YES — primary** |
| B hydration failure | NO (secondary timing only) |
| C workspace GET failure | NO (HTTP 200) |
| D product/template binding | NO |
| E D2 first-load deadlock | NO (not blank cause); hardened anyway |
| F initial pricedQuote failure | NO |
| G logical-list state | NO |
| H routing/bootstrap | Partial (`fetchStartedRef` / cache flash) |
| I malformed payload | NO |
| J unrelated backend error | NO |

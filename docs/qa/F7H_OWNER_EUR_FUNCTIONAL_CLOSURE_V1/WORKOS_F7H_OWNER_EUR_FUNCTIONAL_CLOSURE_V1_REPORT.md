# WORKOS — F7H OWNER EUR FUNCTIONAL CLOSURE V1

**Verdict:** `FUNCTIONAL_PASS_WITH_UNPUBLISHED_RATE_GAPS`  
**Date:** 2026-08-03  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Base HEAD before commit:** `b82b47d85ccb74fbe29eb145c25aeda0cebb8fae`  
**Worktree:** `C:\w\psiso` → git-common-dir `C:\Users\offic\workos_app_vs\.git`

## Mini decision

Owner GO for E2E native EUR commercial policy for Litere volumetrice + Panou ACM. Final commercial price levels deferred; no invent / convert / rename; fail-closed for unpublished rates.

## Architecture readback

| System | Owns | Does not own |
| --- | --- | --- |
| Product Template | composition / contracts | commercial rates |
| ProductDefinition | activation / structure / readiness | commercial calc |
| ProductAggregate | expanded technical graph | final price |
| Pricing Registry / commercial catalog | configurable rules + rates | offer instance |
| CPP | runtime commercial proposal | internal cost |
| EIC | estimative internal cost | client price |
| Quote Snapshot V2 | frozen offer | live reprice |
| HR / Machines | internal / capacity | client tariff |
| Execution Plan | post-order task graph | offer calc |

## Historical tariff research (summary)

| Rule | Value | Currency | Unit | Classification | Action |
| --- | ---: | --- | --- | --- | --- |
| debitare_fata | 1.5 | EUR | ml | EUR_SOURCE_EXISTING (CNC_ROUTER workcenter — not dedicated commercial sell) | provisional commercial reuse |
| modelare_cant_aluminiu | 5.0 | EUR | ml | EUR_SOURCE_EXISTING (RETURN_PROFILE_MACHINE_FORMING only; bonding separate) | provisional commercial reuse |
| debitare_spate | — | EUR | m² | NOT_FOUND (CNC is EUR/ml, not EUR/m² sell) | unpublished fail-closed; m² preserved |
| sistem_led_module | — | EUR | buc | NOT_FOUND (0.5 purchase / 0.05 install ≠ sell) | unpublished |
| sursa_led | — | EUR | buc | NOT_FOUND (wattage purchase rows ≠ flat CPP sell) | unpublished |
| finisaje_cant_ral_labor | 1.0 | EUR | ml | OWNER_DOCUMENTED + EUR_SOURCE_EXISTING | native EUR |
| montaj | 200 | EUR | locație | OWNER_DOCUMENTED + EUR_SOURCE_EXISTING | native EUR |
| RAL minimum | 100 | RON | /culoare | LEGACY_RON / OWNER_DOCUMENTED | not converted; EUR floor unpublished |

Research follow-up: CNC/forming EUR are workcenter sources reused provisionally — not Owner-final commercial sell. No invented values. No RON→EUR conversion. No FX as offer truth for volumetric presentation.

## Implementation

- Scoped `presentation_currency=EUR` for volumetric + ACM templates.
- Registry EUR stays native under presentation EUR (no company FX rename).
- Universal currency guards + RAL EUR-only explicit top-up line.
- Legacy 100 RON floor retired from CPP math.
- Snapshot freezes full CPP preview (incl. presentation / rate_publication_status).
- Step 3 consumes backend breakdown; partial note when pending unpublished rates.
- Dry-run stamps `commercial_totals.currency` from CPP presentation.

## Tests

| Suite | Result |
| --- | --- |
| `tests/test_f7h_owner_eur_functional_closure.py` | 12 passed |
| CPP preview + site install + logo binding + F7F Step3 | 70 passed (group) |
| F7H ↔ F7F order A/B | DETERMINISTIC_PASS for these suites |
| CI four-file backend | 28 passed |
| FE Vitest Step3 / offer summary | 31 passed |
| Quote snapshot endpoint / FakeDb suites | pre-existing failures (404 router / FakeDb.execute) — not F7H currency regressions |

## Runtime proof (pre-restart / process)

- Process dry-run on `IV6-9C5D9538` (`5a5ce742-…`):  
  `presentation_currency=EUR`, Litere `277.0707 EUR`, ACM `190.7845 EUR`,  
  `complete_offer_total=467.8552 EUR`, `mix=false`, `partial=true`  
  (pending: ambalare, debitare_spate, sistem_led_module, sursa_led).
- Pre-restart UI was limited by stale `:8000` (health ok; `/api/v1/system/version` 404).
- Screenshots (Step 2 era): `screenshots/f7h-01-step2-eur-product-estimates.png`, `screenshots/f7h-02-step2-acm-eur-panel.png`.

## F7H-RUNTIME-CLOSURE-V1 (fresh canonical stack)

**Runtime verdict:** `PASS_WITH_UI_WARNING`  
**Rounding:** `EXPECTED_RAW_PRECISION_ROUNDING` (primary) with operator-visible `DISPLAY_RECONCILIATION_DEBT` of 0.01 EUR  
**Push readiness:** `READY_NOT_PUSHED`  
**Implementation HEAD lineage:** `7575e2c6` → honesty `6492cd15` (current verified runtime `git_commit`)

### Listener stop + restart

| Item | Evidence |
| --- | --- |
| Old :8000 | PID 27932 listen; reloader parent `C:\w\psiso\backend\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`; started 2026-08-03 00:06; health 200; `/api/v1/system/version` 404 |
| Authorization | Owner GO for stop of demonstrated WorkOS stale listener |
| Stop | `.\scripts\stop-dev.ps1` then residual spawn PID 23944 stopped after proven uvicorn tree |
| Start | `.\scripts\dev-detached.ps1` |
| Fresh BE | Listen PID 23500; reloader `C:\w\psiso\backend\.venv\…\python.exe -m uvicorn …`; `/health` 200; `/api/v1/system/version` `git_commit=6492cd15`; local-compatibility 200 `pilot_gate_open=false` |
| Fresh FE | Vite PID 31596 `C:\w\psiso\frontend\…\vite.js --host 127.0.0.1 --port 3000` |

### Fresh dry-run + rounding

See `evidence/runtime-dry-run-fresh-summary.json`.

| Value | Raw (backend) | Display (2 dp) |
| --- | ---: | ---: |
| Litere | 277.0707 | 277.07 |
| ACM | 190.7845 | 190.78 |
| Sum of displays | — | **467.85** |
| Grand total (backend sum of raws) | 467.8552 | **467.86** |

Formula: backend keeps ~4 dp line/product subtotals; `complete_offer_total` = sum of product raw EUR; UI `formatOfferMoney` formats backend total once — FE does **not** sum displayed subtotals. Classification: `EXPECTED_RAW_PRECISION_ROUNDING`. Operator who adds the two displayed subtotals sees −0.01 → documented as display reconciliation debt (not a FE fix-by-sum).

### Scenario A (real unpublished state)

- Label: **Total ofertă (parțial)** `467,86 EUR` — not “Total final”.
- Partial note lists unpublished codes; “Nu este preț comercial final”.
- TVA note separate (`tax_exclusive`, 21%).
- Handoff / “Creează oferta prețuită” / “Continuă către ofertă” disabled.
- Fresh dry-run / handoff: **`MISSING_RETURN_PAINT_COLOR` not present** (entry report claimed it; current blockers are unpublished rates + operator confirmation / handoff blockers). Acceptance still not falsely allowed.

### Scenario B (fail-closed)

Runtime DB write avoided. Controlled test `test_f7h_mixed_eur_ron_fail_closed` **PASS** (currency mix → total unavailable, no 0, no FX).

### Screenshots (runtime closure)

| Filename | URL | Workspace | Section | Expected | Actual | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `evidence/screenshots-runtime-closure/01-step3-full.png` | `/intake-v6/5a5ce742-…/operator` step 3 | IV6-9C5D9538 | full Step 3 | partial EUR total + blockers | 467,86 EUR partial; handoff blocked | PASS |
| `evidence/screenshots-runtime-closure/02-offer-totals.png` | same | same | Ofertă client | Litere/ACM/total | 277,07 / 190,78 / 467,86 | PASS |
| `evidence/screenshots-runtime-closure/03-handoff-blockers.png` | same | same | handoff strip | blocked | 1 blocant; Continuă disabled | PASS |

Owner route: open URL → click **3 Confirmare** → read Ofertă client + footer status.

### Fresh tests (this verification)

| Command | Result |
| --- | --- |
| `pytest tests/test_f7h_owner_eur_functional_closure.py` | 12 passed |
| `pytest tests/test_commercial_price_proposal_preview.py` | 32 passed |
| `pytest tests/test_f7f_owner_commercial_law_step3_total.py` | 9 passed (run separately; combined session fixture clash is pre-existing harness noise) |
| Vitest offer summary + FinalConfigurationSummary | 31 passed |

## Protected baselines (SQLite mode=ro)

| Fixture | Expected | Before | After restart |
| --- | --- | --- | --- |
| order 880811 total | 1847.5 | PASS | PASS |
| plan 22 planned_tasks | 5 | PASS | PASS |
| snapshot hash prefix | a59b6c44… | PASS | PASS |
| order 973019 total | 847.5 | PASS | PASS |
| plan 21 | intact | PASS | PASS |
| snapshot hash prefix | 2d412e6e… | PASS | PASS |
| pilot_gate_open | false | PASS | PASS |

Evidence: `evidence/protected-baselines.json`, `evidence/protected-baselines-after.json`.

## Gates

| Gate | Status |
| --- | --- |
| Native EUR path | PASS |
| No mixed currency math | PASS |
| RAL minimum | PASS (EUR-only / unpublished floor) |
| Snapshot immutability | PASS (tests) |
| Canonical backend :8000 | PASS (fresh) |
| Rounding reconciliation | PASS (expected raw) / UI WARNING (0.01 display sum) |
| Partial/unpublished truth | PASS |
| Acceptance readiness | PASS (not falsely open) |
| Final prices | DEFERRED — NON-BLOCKING |
| A-F3 | DEFERRED |
| A-F4 | CLOSED structural |
| Materialization | CLOSED |
| Scheduling | HOLD |
| Push | READY_NOT_PUSHED — not executed |

## Next

1. Owner decision for **push** of F7H commits (mechanism), separate from final tariff audit.  
2. Optional polish GO: display reconciliation note for 0.01 / duplicate EUR label on product rows (no FE sum fix).  
3. Dedicated final pricing pass for unpublished EUR rates + RAL EUR floor.

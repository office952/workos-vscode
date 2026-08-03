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

## Runtime proof

- Process dry-run on `IV6-9C5D9538` (`5a5ce742-…`):  
  `presentation_currency=EUR`, Litere `277.0707 EUR`, ACM `190.7845 EUR`,  
  `complete_offer_total=467.8552 EUR`, `mix=false`, `partial=true`  
  (pending: ambalare, debitare_spate, sistem_led_module, sursa_led).  
  Blockers include `MISSING_RETURN_PAINT_COLOR` (acceptance) + unpublished sell rates.
- UI: Step 2 shows EUR product estimates; FE reports backend contract mismatch on `:8000` (health ok, OpenAPI/version incomplete — ghost/stale listener). No port kill without Owner GO. Step 3 canonical total UI proof limited by that runtime identity issue.
- Screenshots: `screenshots/f7h-01-step2-eur-product-estimates.png`, `screenshots/f7h-02-step2-acm-eur-panel.png`.

## Protected baselines (SQLite mode=ro)

| Fixture | Expected | Actual |
| --- | --- | --- |
| order 880811 total | 1847.5 | 1847.5 PASS |
| plan 22 planned_tasks | 5 | 5 PASS |
| snapshot hash prefix | a59b6c44… | a59b6c44… PASS |
| order 973019 total | 847.5 | 847.5 PASS |
| plan 21 | intact | intact PASS |
| snapshot hash prefix | 2d412e6e… | 2d412e6e… PASS |

## Gates

| Gate | Status |
| --- | --- |
| Native EUR path | PASS |
| No mixed currency math | PASS |
| RAL minimum | PASS (EUR-only / unpublished floor) |
| Snapshot immutability | PASS (tests) |
| Final prices | DEFERRED — NON-BLOCKING |
| A-F3 | DEFERRED |
| A-F4 | CLOSED structural |
| Materialization | CLOSED |
| Scheduling | HOLD |
| Push | NOT EXECUTED |

## Next

1. Owner final pricing pass for unpublished EUR rates + RAL EUR floor.  
2. Fresh canonical backend restart (Owner GO) for Step 3 UI screenshot closure.  
3. Push only after Owner GO.

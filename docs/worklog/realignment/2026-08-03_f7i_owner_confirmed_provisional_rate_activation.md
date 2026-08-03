# F7I.1 — Owner-confirmed provisional commercial rate activation

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 |
| Mini decision | Activate four Owner-confirmed provisional EUR sell rates from F7I gaps |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `5a17da69` |
| Final HEAD | branch tip after F7I.1 commit (see `git rev-parse HEAD`) |
| Confirmation | Owner GO 2026-08-03 · provisional · EUR · VAT excluded |
| Verdict | `F7I_PROVISIONAL_RATE_ACTIVATION = COMPLETE` |

## Owner confirmation

```text
OWNER_RATE_CONFIRMATION = GRANTED
CONFIRMATION_DATE = 2026-08-03
RATE_NATURE = PROVISIONAL_COMMERCIAL
VAT = EXCLUDED
CURRENCY = EUR
```

| canonical_rule_code | Value | Unit |
| ------------------- | ----: | ---- |
| `debitare_spate` | 15.00 | EUR/m² |
| `sistem_led_module` | 1.50 | EUR/buc |
| `sursa_led` | 35.00 | EUR/buc |
| `ambalare` | 20.00 | EUR/set |

## Preflight

- Canonical git-common-dir: `C:\Users\offic\workos_app_vs\.git`
- Worktree: `C:\w\psiso`
- HEAD at start: `5a17da69` (tracked clean; untracked QA leftovers left local)
- Branch created: `feat/f7i-owner-rate-activation`

## Audit checkpoint

| Problemă | Adevăr la `5a17da69` | Schimbare | Fișiere | Risc |
| -------- | -------------------- | --------- | ------- | ---- |
| Four rates `ACTIVE_MISSING_RATE` / null | fail-closed F7I | Set constants + `ACTIVE_PROVISIONAL` consumable | `commercial_rules_volumetric_v2.py` | Low |
| Classify / template recipe | missing blockers | Owner provisional union + honesty labels | recipe service + FE label | Low |
| CPP unpublished | null unit price | Documented EUR + `owner_decision_required=False` | rules + CPP rate_status | Medium (test updates) |
| Snapshot | freeze path exists (F7H) | Embed provisional provenance | tests F7I.1 | Low |
| ACM treatment | blocked 5/0 | unchanged | — | None |
| DB | N/A | `STOP_DB_EXPANSION` — no migration | — | None |

## Architecture readback

Catalog owns values → template references → PD/PA context → CPP → Snapshot V2. EIC separate. No inventory/hourly/FX invent.

## Before / after

| Rule | Before | After |
| ---- | ------ | ----- |
| `debitare_spate` | missing / null | provisional 15 EUR/m² |
| `sistem_led_module` | missing / null | provisional 1.5 EUR/buc |
| `sursa_led` | missing / null | provisional 35 EUR/buc |
| `ambalare` | missing / null | provisional 20 EUR/set |

`OWNER_MISSING_COMMERCIAL_RATE_CODES` → empty. Logo siblings `logo_back_cnc` / `logo_led_modules` share the same Owner provisional constants.

## Provenance

```text
source = commercial_rules_volumetric_v2:owner_confirmed_provisional:f7i1_2026_08_03
publication = ACTIVE_PROVISIONAL / rate_publication_status=provisional
final_pricing_review_required = true
```

## Files changed

- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/services/template_pricing_recipe_service.py`
- `backend/services/commercial_price_proposal_service.py` (rate_status recognition)
- `backend/tests/test_f7i1_owner_confirmed_provisional_rate_activation.py` (new)
- `backend/tests/test_f7i_*.py`, F7H/CPP/logo binding updates
- `frontend/src/features/product-system/templatePricingCommercialReference.ts` (+ test)
- this worklog

## Tests

- Backend targeted: F7I.1 + F7I + F7H + CPP preview + logo binding + template recipe — **75 passed**
- Frontend: `templatePricingCommercialReference.test.ts` — green; lint — green
- `test_commercial_price_proposal_linked_logo.py` currency/subtotal assertions: classified **PRE_EXISTING / TEST_FIXTURE_DRIFT** vs F7H EUR presentation + legacy RON finish/sablon lines (not introduced by inventing rates; not weakened)

## Runtime

- Registry: 50 items
- Template pricing API: four codes `ACTIVE_PROVISIONAL` with exact values, no `COMMERCIAL_RATE_MISSING`
- CPP dry-run: four lines priced EUR provisional; status ready when geometry present

## UI proof

| Element | Result |
| ------- | ------ |
| URL | `http://127.0.0.1:3000/product-system/products/TPL-VOLUMETRIC-LETTERS_v2?ps_legacy=1` |
| Tab | Admin → Prețuri template |
| Visible | `Tarif provizoriu aprobat — Owner 2026-08-03` + values 15/1.5/35/20 · `Tarif provizoriu` · editable false |
| Catalog | `/inventory/pricing?template=TPL-VOLUMETRIC-LETTERS_v2` (owner surface) |
| Light/day | PASS (staging shell) |
| Dark | NOT_OFFICIALLY_SUPPORTED as separate gate (app default dark shell verified) |

## Snapshot / baselines

- Snapshot embeds provisional rates + provenance (F7I.1 test + F7H freeze mechanism)
- Protected orders RO unchanged: 880811 → 1847.5 / `a59b6c44`; 973019 → 847.5 / `2d412e6e`

## DB / forbidden scope

No reset/reseed/migration. Materialization CLOSED · Scheduling HOLD · no HR/utilaje/Employee Mobile/SVG.

## Dead Pieces Check

```text
Dead pieces discovered: none new
Dead pieces touched: none
Dead pieces removed: NONE
Why removal was or was not allowed: Step 12 not in scope
Step 12 impact: none
```

## Exact next step

```text
The four Owner-confirmed provisional commercial rates are active and traceable
through Catalog → Product Template references → ProductDefinition/ProductAggregate
context → CommercialPriceProposal → Quote Snapshot V2.
The previous Owner rate gaps are closed for the current provisional pricing phase.
The rates remain explicitly provisional and will be reviewed together with the
complete pricing system during the final pricing analysis.
No architectural redesign is required.
F7I remains structurally closed.
Materialization remains CLOSED.
Scheduling remains HOLD.
The next phase must not start automatically.
```

## Direction score

**93/100** — rates active, honest provisional disclosure, regression green on commercial spine; final pricing review still deferred; linked_logo RON fixture debt remains outside this GO.

## Method / opinion

Smallest coherent change: publish Owner values into the existing commercial catalog constants, map them to `ACTIVE_PROVISIONAL`, clear fail-closed missing set, update tests. Avoided DB expansion and redesign. Result matches Owner intent without pretending the rates are final.

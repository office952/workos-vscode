# WorkOS — V1 Reality Check (Light + Intake commercial + EUR/RON)

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_WORKOS_V1_REALITY_CHECK_LIGHT_INTAKE_COMMERCIAL_AUDIT`  
**Branch:** `feat/f7i-owner-rate-activation`  
**REALITY_CHECK_BASELINE_HEAD:** `1b5315fc`  
**Tracked worktree at start:** clean (untracked tmp/QA only — no checkpoint commit)  
**PRODUCT_CODE_CHANGES:** `0`

## Verdict

```text
WORKOS_V1_REALITY_CHECK = FAIL_REPAIR_REQUIRED
V1_EXIT_STATUS = HOLD_PENDING_REALITY_CHECK
LIGHT_THEME_V1 = REOPEN_REQUIRED
COMMERCIAL_OFFER_V1 = REOPEN_REQUIRED
UI_HONESTY_V1 = REOPEN_REQUIRED
INTAKE_V6_COMMERCIAL_TRUTH = FAIL
FINISH_PRICING = PARTIAL_CPP_OK_OFFER_BLOCKED_BY_CURRENCY_MIX
CURRENCY_UI_TRUTH = FAIL
GOLDEN_LETTERS_E2E = FAIL
NEXT_RECOMMENDED_BUILD = WORKOS_V1_COMMERCIAL_CURRENCY_TRUTH_CLOSURE
NEXT_TASK = NOT_AUTHORIZED
```

Do **not** ask Owner for `WORKOS_V1_PRODUCT_SET = LETTERS_ONLY` until repairs close.

---

## A. LIGHT_THEME_DEFECT_MATRIX (runtime)

| Route | Symptom | Severity | Root class | Screenshot |
|-------|---------|----------|------------|------------|
| `/intake` Light | Usable; sidebar dim labels low contrast | P1 | SEMANTIC_TOKEN / SHARED | `light/01-intake-list-light.png` |
| `/quotes` Light | Night chips / panels (`bg-[#121B2C]`, `bg-slate-900`) on Light canvas | P1 | PAGE_LOCAL | `light/02-quotes-list-light.png` |
| `/execution` Light | Mostly readable; dense diagnostic strip competes | P2 | PAGE_LOCAL / LEGACY | `light/03-execution-light.png` |
| `/intake-v6/...` Light | Config usable; residual slate text classes | P1–P2 | SHARED_COMPONENT + PAGE_LOCAL | `light/04-intake-v6-config-light.png` |
| Shell chrome | Light tokens work (`data-theme=light`, body `rgb(250,250,250)`) | — | GLOBAL_THEME_AUTHORITY OK | — |

**LIGHT_THEME_ROOT_CAUSE_MAP:** not missing ThemeProvider — **PAGE_LOCAL night hex/slate** + dual token footgun (`tokens.ts` dark hex vs `--wo-*`). Prefer systemic migration to `wo-*` / proper `dark:` pairs; not 30 one-off patches without shared primitive cleanup.

---

## B. SELECTED_TO_PRICED_MATRIX (CPP controlled golden)

Geometry baseline: face area 1.2 m², perimeter 12.5 m, return 60 mm.  
Evidence: `commercial/finish_numeric_deltas.json`, `commercial/complete_offer_currency_probe.json`.

| Component/option | Selected | CPP priced when EUR-pure | Included in complete_offer_total | Notes |
|------------------|----------:|-------------------------:|-----------------------------:|-------|
| Face none | Y | Y (no finish lines) | Only if no RON mix | |
| Face Oracal 641 | Y | Y (+11.4 EUR) | Y when paper sablon | material 6.5 + apply 3 /m² |
| Face Oracal 651 | Y | Y (+9.6) | Y when EUR-pure | |
| Face print_laminate | Y | Y (+15.6) | Y when EUR-pure | |
| Face Oracal 8500 @1260 | Y | Y (+19.8) | Y when EUR-pure | |
| Cant stock white_aluminum | Y | zero finish surcharge | N/A surcharge | profile/forming still EUR lines |
| Cant Oracal wrap | Y | Y (+6.0) | Y when EUR-pure | |
| Cant RAL paint | Y | Y (+43.75) | Y when EUR-pure | |
| Mounting template Forex | Y (default fixture) | RON line 15/m² | **NO — blocks total** | `COMMERCIAL_CURRENCY_MIX_UNRESOLVED` |
| Legacy flat `finisaje_colantare_vopsire` | with plexiglas_clear | RON 35/m² | **NO — blocks total** | should stay suppressed for EUR vinyl paths |

**Stock zero delta:** accepted only as finish surcharge = 0; return profile / forming / other sold lines still required — verified present in EUR bucket.

---

## C. FINISH_END_TO_END_TRACE

| Hop | Status |
|-----|--------|
| FINISH_SELECTION_CAPTURE | PASS (Intake shows Oracal 8500 on live workspace IV6) |
| FINISH_PRODUCT_TRUTH_PROPAGATION | PASS (contracts + bridge) |
| FINISH_AGGREGATE_PROPAGATION | PASS (measurements path) |
| FINISH_PRICING_RESOLUTION | PASS on CPP rules when EUR-pure |
| FINISH_BREAKDOWN_RENDER | PARTIAL (lines exist; operator may see incomplete offer) |
| FINISH_TOTAL_INCLUSION | **FAIL** when sellable RON lines present — `complete_offer_total=null` |
| FIRST_BROKEN_BOUNDARY | **CPP presentation currency composition** — RON rule lines vs `VOLUMETRIC_PRESENTATION_CURRENCY=EUR` |

Runtime Intake (`IV6` with Oracal 8500): hero **661,43 EUR** (`commercial/02-intake-live-oracal8500-eur.png`).  
Same magnitude on Quotes list labeled **RON** → currency UI fail (see D).

---

## D. CURRENCY_SURFACE_MATRIX

| Surface | Displayed value | Displayed currency | Backend/source | Expected | Class |
|---------|-----------------|--------------------|----------------|----------|-------|
| Intake V6 live hero (IV6 Oracal workspace) | 661,43 | EUR | official dry-run / offer rail | EUR sell | PASS this instance |
| Quotes list KPI / rows | 661,43 / aggregates | **RON (cu TVA)** | quote currency default/extraction | EUR for Letters V6 | **WRONG_LABEL** (likely WRONG_SOURCE if stamp missing) |
| `IntakeV6PricingInputPanel` | official totals | hardcoded `Intl` **RON** | ignores presentation currency | EUR | **WRONG_LABEL** code |
| CPP complete_offer with Forex sablon | null | — | mix EUR+RON | EUR complete or honest block | **BACKEND_CONTRACT** mix |
| Labor/material actuals | RON | RON | Policy A stamp at P&L | RON costs OK | PASS intentional |
| Profitability | EUR via stamp | EUR | `profitability_fx_v1` | EUR report | keep Policy A |

**Three concepts kept separate:** sell EUR · actual costs RON · P&L EUR via frozen FX.

---

## E. GOLDEN_LETTERS_E2E_MATRIX (component hops)

| Component | SEL | CFG | PT | AGG | PRICE_IN | PRICED | BRK | TOTAL | QUOTE | ORDER | EXEC | ACT |
|-----------|:---:|:---:|:--:|:---:|:--------:|:------:|:---:|:----:|:-----:|:-----:|:----:|:---:|
| Face | Y | Y | Y | Y | Y | Y* | Y* | FAIL* | FAIL* | n/a | n/a | n/a |
| Return/Cant | Y | Y | Y | Y | Y | Y* | Y* | FAIL* | FAIL* | n/a | n/a | n/a |
| Backing | Y | Y | Y | Y | Y | Y | Y | FAIL* | FAIL* | n/a | n/a | n/a |
| Lighting | Y | Y | Y | Y | Y | Y | Y | FAIL* | FAIL* | n/a | n/a | n/a |
| Electrical/Power | Y | Y | Y | Y | Y | Y | Y | FAIL* | FAIL* | n/a | n/a | n/a |
| Finish (Oracal/RAL/print) | Y | Y | Y | Y | Y | Y* | Y* | FAIL* | FAIL* | n/a | n/a | n/a |
| Mounting template Forex | Y | Y | Y | Y | Y | RON line | Y | **FAIL** | **FAIL** | n/a | n/a | n/a |

\*Line-level CPP OK in EUR-pure; **TOTAL/QUOTE fail** when mix or when UI mislabels currency.  
Full Quote→Order→Execution freeze walk not re-run on protected QA; classification uses CPP null complete_offer + Quotes RON labeling as sufficient blast evidence for commercial hop.

---

## F. ROOT_CAUSE_MATRIX

| ID | Symptom | Root cause | First break | Blast | Why tests missed | Owner | Fix | Regression test |
|----|---------|------------|-------------|-------|------------------|-------|-----|-----------------|
| RC1 | No complete EUR offer with Forex sablon | RON documented price on sellable `sablon_montaj_forex` under EUR presentation | `commercial_price_proposal_service` product breakdown / currency buckets | Dry-run null totals; Intake blocked/incomplete; Quote cannot honest-freeze EUR | Tests assert line rates / finish deltas; rarely assert `complete_offer_total` under default mounting forex | Commercial rules + CPP | Convert Forex sablon to Owner EUR (or remove from sold path / fail-closed sold module) | Assert complete_offer EUR with mounting forex enabled |
| RC2 | RON flat finish still in mix | Legacy `finisaje_colantare_vopsire` RON still emits for some face tokens (e.g. plexiglas_clear) | `commercial_rules_volumetric_v2` gate/suppress | Same mix as RC1 | Finish suites focus Oracal/none; plexiglas path under-tested vs presentation EUR | Commercial rules | Suppress/replace with EUR law or fail-closed | Mix fixture must yield null **or** pure EUR — never silent RON merge |
| RC3 | Quotes show RON for V6 EUR amounts | Default/extraction `RON` + list formatting | `quoteCurrency.ts` / Quotes page + missing currency stamp on DTO | Operator believes sell is RON | KPI tests mixed→em-dash; not EUR Letters row provenance | FE quote currency + BE stamp | Single sell-currency helper from snapshot/dry-run presentation | Vitest: V6 EUR quote never labels RON |
| RC4 | PricingInputPanel formats RON | Hardcoded `currency: "RON"` | `IntakeV6PricingInputPanel.tsx` | Review/confirm wrong unit | Panel tests may not assert currency code | FE Intake | Format from `commercial_totals.currency` / presentation | Component test EUR stamp |
| RC5 | Light unusable islands | Page-local `#121B2C` / slate-900 | Quotes (and peers) classNames | Operator Light trust | Theme tests shell-only / dark-biased | FE design system | `wo-*` migration + retire dark `tokens.ts` | Route Light screenshot gate P0/P1 |

**DUAL_CALC_DIVERGENCE:** EIC totals ≠ CPP (expected different systems). **material-breakdown is not offer authority.** Official money = CPP / priced-quote-dry-run.

**preview.status=ready with null subtotal** under mix is an honesty smell — operator-facing status must not look “ready” without a total.

---

## G. REPAIR_BUILD_PLAN (max 3)

### BUILD 1 — `WORKOS_V1_COMMERCIAL_CURRENCY_TRUTH_CLOSURE` (NEXT)

- **Root causes:** RC1–RC4  
- **Owner:** Commercial rules + Intake/Quote currency presentation  
- **Files (likely):** `commercial_rules_volumetric_v2.py`, `commercial_price_proposal_service.py`, `intake_v6_priced_quote_dry_run_service.py`, `IntakeV6PricingInputPanel.tsx`, `quoteCurrency.ts`, Quotes page  
- **User outcome:** selecting Letters finish + mounting yields one honest EUR complete total (or explicit incomplete); Intake + Quote + Order show EUR for sell; no RON label on EUR amounts  
- **Tests:** complete_offer under forex+Oracal; Quotes EUR label; PricingInputPanel currency from backend  
- **Runtime proof:** golden Intake → dry-run → Quote screenshot EUR

### BUILD 2 — `WORKOS_V1_LIGHT_THEME_SYSTEMIC_CLOSURE`

- **Root causes:** RC5  
- **Owner:** FE design system  
- **Outcome:** P0/P1 Light readable on Intake/Quotes/Orders/Execution/modules; Dark preserved  
- **Tests:** Light route smoke + no new dark hex in touched modules

### BUILD 3 — `WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF`

- Zero features; E2E numeric finish deltas + currency + Light spot; then resume exit verification

If BUILD 1 alone restores golden commercial truth, BUILD 2 can follow immediately; do not finalize V1 before BUILD 1.

---

## Domains

**REOPEN:** COMMERCIAL_OFFER, UI_HONESTY (currency + Light P1), EXIT HOLD  
**CLOSED remain:** Sessions, MachineRun runtime, Material actuals authority, Labor actuals, Policy A FX (do not redesign), Security write-gate

---

## Plain answers

| Question | Answer |
|----------|--------|
| Este Light theme pregătită? | **NO** |
| Intake V6 calculează toate opțiunile selectate? | **NO** (complete offer blocked by currency mix / UI currency lies) |
| Finisajul intră corect în preț? | **PARTIAL** — CPP lines yes when EUR-pure; complete offer often blocked |
| Prețurile EUR/RON sunt coerente în UI? | **NO** |
| Golden Letters E2E este coerent? | **NO** |
| Putem declara V1 finalizat azi? | **NO** |

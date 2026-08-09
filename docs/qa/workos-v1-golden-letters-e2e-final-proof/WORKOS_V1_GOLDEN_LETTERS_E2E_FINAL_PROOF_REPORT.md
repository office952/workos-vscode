# WORKOS V1 — Golden Letters E2E Final Proof

| Field | Value |
|-------|-------|
| Date | 2026-08-10 |
| Owner GO | `AUTHORIZE_WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF` |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `c5030f85` |
| Verdict | **PASS** |

---

## A. Verdict

```text
WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF = PASS
GOLDEN_LETTERS_PRODUCT_FLOW = PASS
GOLDEN_LETTERS_COMMERCIAL_FLOW = PASS
GOLDEN_LETTERS_EXECUTION_FLOW = PASS
GOLDEN_LETTERS_ACTUALS = PASS
GOLDEN_LETTERS_PROFITABILITY = PASS
SELECTED_TO_FINAL_TRUTH = PROVEN
CPP_INTAKE_PARITY = PROVEN
QUOTE_ORDER_PARITY = PROVEN
SOLD_TO_EXECUTION = PROVEN
LABOR_ACTUAL = PROVEN (minutes; labor money N_A_FOR_V1)
MATERIAL_ACTUAL = PROVEN
PROFITABILITY = PROVEN (Policy A partial known materials)
OPERATOR_TECHNICAL_MONEY_FALLBACKS = 0
HISTORICAL_QUOTES_OPERATOR_TRUTH = PASS
LIGHT_THEME_REGRESSION = NONE
DARK_THEME_REGRESSION = NONE (spot)
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
V1_EXIT_STATUS = READY_TO_RESUME
NEXT_RECOMMENDED_BUILD = WORKOS_V1_EXIT_VERIFICATION_RESUME
NEXT_TASK = NOT_AUTHORIZED
```

---

## B–D. Repo / GO / Fixture

- Historical golden workspace never mutated: `4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1`
- Disposable Golden fixture from `backend/tests/fixtures/intake_v6_golden_gradi/`
- Final accepted Golden IDs (last successful chain run):
  - workspace: `261f796c-b3e7-43ad-aae2-4d43852376e2` / `IV6-GOLD-FINAL-261F796C`
  - quote: `31` / `Q-V6-IV6-GOLD-FINAL-261F796C-1786318809`
  - order: `973024` / `ORD-IV6-V2-1786318810-31`
  - quote snapshot v2: `31`
  - execution plan: materialized with **18** `operational_tasks[]`

Evidence JSON: `golden_chain_run.json`, `restart_durability_read.json`.

---

## E. Selected configuration

| Field | Value |
|-------|-------|
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Face finish | `oracal_8500` (070 Black) |
| Return | white aluminum, 60 mm |
| Backing | `forex_10_no_bevel` |
| Lighting | LED modules, illuminated |
| Mounting template | **disabled** (no Forex sell template) |
| Commercial Adaos | **0%** (snapshot-authoritative V1 freeze applies VAT on 7G base only) |

---

## F. Selected → final matrix (summary)

| Component | Selected | Priced | Quote/Order | Execution | Actuals | Coherent |
|-----------|----------|--------|-------------|-----------|---------|----------|
| Face | yes | debitare_fata + Oracal | yes EUR | CUT_FACE (+ related) | session on CUT_FACE | YES |
| Return/Cant | yes | modelare_cant_aluminiu | yes | PREPARE/FORM_CANT | — | YES |
| Backing | yes | debitare_spate | yes | CUT_FOREX_BACK | — | YES |
| Lighting | yes | sistem_led_module | yes | INSTALL/WIRE/TEST LED | — | YES |
| Electrical/Power | yes | sursa_led | yes | LABEL/PACK PSU | — | YES |
| Finish | Oracal 8500 | finisaje_oracal_* | yes | face vinyl path | — | YES |
| Mounting template | none | n/a (disabled) | n/a | n/a | — | YES |
| Site montaj line | present in CPP | montaj | yes | workshop packaging/QC ops | — | YES |

Fixture SVG also yields linked logo commercial lines (gradi emblem instances). Not an ACM/Logo product-set expansion GO — consumed as existing volumetric linked segments.

---

## G–V. Chain proof (numeric)

| Hop | Result |
|-----|--------|
| Product Truth confirm | revision 1, freeze allowed |
| ProductDefinition | ok, revision aligned |
| ProductAggregate | ok |
| CPP dry-run | EUR **862.65** gross / **712.93** net / VAT **149.72** |
| Finish lines | `finisaje_oracal_8500_material`, `finisaje_aplicare_autocolant_fata` |
| Quote handoff | same totals EUR |
| Snapshot V2 | created |
| Pricing review | `quote_snapshot_v2` authority |
| Accept / Convert | order locked; accepted commercial EUR |
| ExecutionPlan | 18 operational tasks (DEC-009 temporarily registered then restored) |
| Assignment | employee 3 → CUT_FACE |
| Session | 40 minutes; END ≠ complete |
| Labor actual | 40 minutes in ExecutionReality |
| Material actual | issue qty 0.25 @ 8.5 → known cost **2.125** |
| MachineRun | NOT_APPLICABLE |
| Profitability | revenue EUR frozen; materials known; labor money N_A_FOR_V1; coverage PARTIAL |

Restart durability (new DB session): order locked, snapshot present, 18 ops tasks, 1 stock movement, profitability known cost 2.125 — PASS.

---

## Z / AA. Operator money + Quotes list

| Check | Result |
|-------|--------|
| `monedă indisponibilă` on `/quotes` | **0** (CDP + screenshot) |
| Historical missing currency | neutral `—` |
| Golden V6 notes currency EUR | list shows **862,65 EUR** after notes provenance extract |
| Screenshot | `screenshots/10-quotes-list-historical-money.png` |

Bounded regressions fixed in this GO:

1. Neutral money when currency missing (`quoteCurrency.ts`)
2. V6 notes currency provenance for list (`extractQuoteCurrencyFromNotes`)
3. Snapshot freeze vs post-7G Adaos compare (`intake_v6_quote_snapshot_v2_service.py`)
4. Pricing-review quote projection currency from notes (not hardcoded RON)

---

## AD. Tests

```text
frontend: vitest src/lib/quoteCurrency.test.ts → 16 passed
backend: pytest tests/test_intake_v6_snapshot_authoritative_pricing_review.py tests/test_dec009_materialize_gate.py → 28 passed
```

---

## AH. Roadmap

- `WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF = PASS`
- `V1_EXIT = READY_TO_RESUME`
- Next: `WORKOS_V1_EXIT_VERIFICATION_RESUME` (not authorized here)

---

## Plain answers

| Question | Answer |
|----------|--------|
| Intake configuration complete? | YES |
| Every selected sellable component reaches final truth? | YES |
| Finish affects official price correctly? | YES |
| Intake = Quote = Order commercial truth? | YES (EUR 862.65 / net 712.93) |
| Order produces coherent execution? | YES (18 ops tasks) |
| Actual labor/material reach Profitability? | YES (minutes + known material cost; labor money N/A V1) |
| Any technical monetary fallback visible to operator? | NO |
| Golden Letters E2E coherent? | YES |
| Can V1 Exit resume? | YES |

### What must NOT be reopened

Light Theme redesign · pricing redesign · new FX · Capacity · Phase E · PAUSE/RESUME · ACM/Logo expansion · Postgres · broad legacy cleanup

### Forbidden Scope Respected

YES (no push)

### Findings (not FAIL)

- Snapshot-authoritative freeze does **not** carry live Adaos; Golden PASS path uses Adaos 0%.
- DEC-009=B required temporary next-dry register for Golden materialize (restored to Wave3 target after).
- Profitability V1 excludes labor money by contract (`hr_labor_cost_missing` warning expected).

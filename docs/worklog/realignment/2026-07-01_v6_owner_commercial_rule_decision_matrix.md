# V6 OWNER COMMERCIAL RULE DECISION MATRIX

Date: 2026-07-01

## 1. Verdict

PASS

The real backend V6 dry-run was rerun for workspace `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3` / `IV6-BB8EE3F8` without quote mutation.

High-confidence conclusion:

- The current blocker is not frontend display, not snapshot composition, and not quote persistence mechanics.
- The current blocker is missing owner-approved commercial rule data for active V6 volumetric lines.
- The real workspace is commercially blocked by one hard basis ambiguity and four owner-decision lines.
- Every active client-facing commercial line in the current runtime trace still has `commercial_unit_price = null`.
- No official V6 priced quote write should be implemented until the owner decisions below are answered.

Final recommendation: `GO_OWNER_PACKET_FIRST / NO_FAKE_TOTALS`.

## 2. Runtime Source Used

Dry-run source:

- service: `build_intake_v6_priced_quote_dry_run(...)`
- commercial engine: `CommercialPriceProposalService.build_preview(...)`
- workspace id: `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`
- workspace code: `IV6-BB8EE3F8`
- quote safety: read-only, no quote writes, no snapshot writes, no order writes

Observed runtime result:

- `pricing_status = V6_PRICED_DRY_RUN_BLOCKED`
- `commercial_totals.subtotal_net = null`
- `commercial_totals.total_gross = null`
- `commercial_proposal_trace.status = blocked`
- `commercial_proposal_trace.quote_ready_for_commercial_review = false`

Active commercial modules in this real workspace:

- `debitare_fata`
- `modelare_cant`
- `debitare_spate`
- `sistem_led`
- `finisaje`

## 3. Exact Live Blockers

### Blocker list from real dry-run

| Code | Type | Severity | Why it blocks official V6 pricing now | Owner answer required | Implementation answer required |
|---|---|---|---|---|---|
| `COMMERCIAL_BASIS_UNKNOWN` | hard rule blocker | critical | Back cutting line has no approved commercial basis, so subtotal cannot exist | yes | yes |
| `DEBITARE_SPATE_BASIS_ML_VS_M2` | owner decision | critical | Back cutting must be sold either by perimeter or by area; current rule says `unknown` | yes | yes |
| `SABLON_FOREX_COMMERCIAL_PRICE` | owner decision | critical for this workspace | Forex mounting template is selected in the live workspace, but no approved commercial price exists | yes | yes |
| `AMBALARE_COMMERCIAL_RULE` | owner decision | optional line, but still blocks current dry-run readiness | Packaging rule is undefined | yes | yes |
| `MONTAJ_COMMERCIAL_RULE` | owner decision | optional line, but still blocks current dry-run readiness | Site installation rule is undefined | yes | yes |
| `V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY` | downstream readiness blocker | derived | Commercial engine status remains blocked | no | no |
| `V6_PRICED_DRY_RUN_ZERO_TOTAL` | downstream total blocker | derived | No positive subtotal can be computed while the above lines remain unresolved | no | no |

### Important clarification

The runtime trace confirms that `AMBALARE` and `MONTAJ` are modeled as optional/future commercial lines, but the current dry-run still treats unresolved owner decisions as blockers. That is acceptable for now because the purpose of this phase is owner clarity, not relaxed readiness.

## 4. Exact Live Commercial Line Map

All quantities below come from the real workspace dry-run, not from documentation only.

| Line | Module | Client-visible role | Current basis | Live quantity | Unit | Current unit price | Current subtotal | Why it is blocked now |
|---|---|---|---|---:|---|---:|---:|---|
| `debitare_fata` | `debitare_fata` | yes | `ml` | 20.9727 | `ml` | null | null | missing approved commercial unit price |
| `modelare_cant_aluminiu` | `modelare_cant` | yes | `ml` | 20.9727 | `ml` | null | null | missing approved commercial unit price |
| `debitare_spate` | `debitare_spate` | yes | `unknown` | 1.2638 | `unknown` | null | null | basis unresolved and unit price missing |
| `sistem_led_module` | `sistem_led` | yes | `piece` | 144 | `buc` | null | null | missing approved commercial unit price |
| `sursa_led` | `sistem_led` | yes | `piece` | 100 | `buc` | null | null | missing approved commercial rule and current quantity shape is unsafe |
| `finisaje_colantare_vopsire` | `finisaje` | yes | `m2` | 1.2638 | `m2` | null | null | missing approved commercial unit price |
| `sablon_montaj_forex` | `finisaje` | yes if offered separately | `m2` | 3.0523 | `m2` | null | null | owner has not approved Forex template price |
| `ambalare` | `finisaje` | maybe | `fixed` | null | `set` | null | null | owner has not defined if it is charged and how |
| `montaj` | `finisaje` | maybe | `fixed` | null | `locatie` | null | null | owner has not defined if it is charged and how |

## 5. Business Interpretation Of The Live Quantities

Romanian owner-language translation of the live runtime numbers:

- `Debitare față`: în acest caz real, baza tehnică disponibilă este `20.9727 ml` de contur total.
- `Modelare cant aluminiu`: în acest caz real, baza tehnică disponibilă este tot `20.9727 ml`.
- `Debitare spate`: sistemul are disponibilă `1.2638 m²` suprafață față/spate, dar nu are încă decizia dacă prețul comercial se vinde la `ml` sau la `m²`.
- `Module LED`: sistemul are `144 buc` module LED estimate pentru acest caz.
- `Sursă LED`: sistemul citește acum `100` din `selected_psu_watts`, deci regula actuală nu este încă sigură pentru comercial. Asta nu trebuie tratat ca `100 buc surse`; trebuie decizie clară de regulă comercială.
- `Finisaje`: sistemul are `1.2638 m²` pentru suprafața de față, iar trasarea de finisaj pe grupuri există în inputul de pricing, dar regula comercială actuală nu are încă preț documentat.
- `Șablon Forex`: în cazul real, șablonul este activ și are `3.0523 m²`, dar nu există încă preț comercial aprobat.

## 6. Owner Decision Matrix

Below is the owner-facing matrix in business language. The goal is to answer only what is necessary to make V6 commercially writable without reintroducing cost-plus, hourly logic, or frontend preview pricing.

| Decizie / Linie | Ce vede clientul | Variantă A | Variantă B | Variantă C | Recomandare implicită | Impact în sistem după GO |
|---|---|---|---|---|---|---|
| `DEBITARE_SPATE` | Debitare spate litere | Se vinde la `m²` pe suprafața spatelui | Se vinde la `ml` pe contur/perimetru | Se include în altă linie și nu apare separat | `A: m² separat` | setează bază comercială clară pentru linia spate și permite subtotal numeric |
| `DEBITARE_FATA` | Debitare față litere | linie separată `RON/ml` | inclusă în prețul feței complete | minim pe lucrare + `RON/ml` peste prag | `A: linie separată RON/ml` | cere unit price documentat și păstrează trasabilitate clară |
| `MODELARE_CANT` | Modelare cant aluminiu | linie separată `RON/ml` | inclusă în prețul corpului literei | minim pe lucrare + `RON/ml` peste prag | `A: linie separată RON/ml` | cere unit price documentat pe perimetru |
| `LED_MODULE` | Module LED | `RON/buc` pe număr de module | inclus în pachet iluminare | pachet minim până la un prag, apoi `RON/buc` | `A: RON/buc` | regula actuală suportă direct cantitatea `144 buc` |
| `SURSA_LED` | Sursă / alimentare LED | `RON/buc sursă`, cu cantitate reală de surse | preț fix pe clasă de putere | inclusă în pachet iluminare | `B: preț fix pe clasă de putere` | necesită clarificare de shape, altfel regula actuală poate multiplica greșit cu `100` |
| `FINISAJE` | Colantare / vopsire | `RON/m²` pe suprafața feței | preț separat pe grup de finisaj | minim pe lucrare + supliment pe grup/culoare | `C: minim pe lucrare + supliment pe grup/culoare` | cere decizie dacă linia rămâne una singură sau se sparge în sublinii |
| `SABLON_FOREX` | Șablon montaj Forex | linie separată `RON/m²` | preț fix pe lucrare | inclus gratuit dacă montajul este comandat | `A: linie separată RON/m²` | activează linie client-visible pentru cazurile cu Forex |
| `AMBALARE` | Ambalare | nu se taxează separat | preț fix pe comandă | preț pe set / pe colet / pe interval de dimensiune | `B: preț fix pe comandă` | decide dacă rămâne linie separată sau inclusă |
| `MONTAJ` | Montaj șantier | în afara acestui flux, ofertat manual | preț fix pe locație | ofertă compusă separat după vizită | `A: manual / în afara fluxului inițial` | permite V6 quote ready fără a inventa montaj automat |

## 7. Line Classification Matrix

| Line | Classification | Why |
|---|---|---|
| `debitare_fata` | client-visible commercial line | client can understand and accept face cutting as priced production work |
| `modelare_cant_aluminiu` | client-visible commercial line | direct volumetric body work, suitable for explicit pricing |
| `debitare_spate` | client-visible commercial line | explicit production step with unresolved selling basis |
| `sistem_led_module` | client-visible commercial line | direct illumination hardware quantity |
| `sursa_led` | included-in-parent commercial line or separate client-visible line | owner must decide whether PSU is bundled into LED package or exposed separately |
| `finisaje_colantare_vopsire` | client-visible commercial line | client-facing finish value, but may need minimum + supplements |
| `sablon_montaj_forex` | client-visible commercial line | if charged separately, it is understandable and measurable |
| `ambalare` | owner manual review | optional commercial policy line; do not auto-price until defined |
| `montaj` | owner manual review | out-of-scope for automatic initial V6 commercial total unless owner explicitly approves rule |

## 8. Minimal Owner Questions

These are the minimum questions needed to turn the current blocker state into implementable commercial rules.

### A. Debitare spate

1. Debitarea spatelui se vinde comercial la `m²` sau la `ml`?
2. Dacă se vinde la `m²`, care este prețul documentat `RON/m²`?
3. Dacă se vinde la `ml`, care este prețul documentat `RON/ml`?
4. Debitarea spatelui apare ca linie separată către client sau este inclusă în altă linie?

### B. Debitare față și modelare cant

1. Care este prețul documentat `RON/ml` pentru `Debitare față`?
2. Care este prețul documentat `RON/ml` pentru `Modelare cant aluminiu`?
3. Există prag minim pe lucrare pentru una dintre aceste două linii?

### C. LED

1. Care este prețul documentat pentru `Module LED`?
2. `Sursa LED` se vinde separat sau este inclusă în pachetul de iluminare?
3. Dacă se vinde separat, se vinde `RON/buc sursă` sau ca preț fix pe clasă de putere?
4. Dacă se vinde pe clasă de putere, care sunt clasele aprobate și prețurile lor?

### D. Finisaje

1. `Finisaje colantare / vopsire` se vând simplu la `RON/m²`, sau există minim pe lucrare?
2. Diferențele de grup/culoare se taxează separat sau sunt incluse?
3. Dacă se taxează separat, regula este pe grup, pe culoare, sau pe complexitate?

### E. Șablon montaj

1. `Șablon montaj Forex` se taxează separat?
2. Dacă da, care este prețul documentat: `RON/m²` sau preț fix pe lucrare?
3. Dacă montajul este comandat, șablonul rămâne taxat sau devine inclus?

### F. Ambalare și montaj

1. `Ambalare` apare ca linie separată, este inclusă, sau este manuală?
2. Dacă este separată, care este regula: preț fix pe comandă, pe colet, sau pe dimensiune?
3. `Montaj` trebuie exclus din automatizare și lăsat manual în faza 1, sau are deja o regulă comercială aprobată?

## 9. Recommended Default Policy

If the owner wants the smallest safe path to a real V6 priced quote without fake totals, the recommended default policy is:

1. `Debitare față` stays separate at `RON/ml`.
2. `Modelare cant aluminiu` stays separate at `RON/ml`.
3. `Debitare spate` becomes separate at `RON/m²`.
4. `Module LED` stays separate at `RON/buc`.
5. `Sursa LED` is not multiplied by watts; it becomes a fixed price by approved PSU class, or quantity `1 buc sursă` when the real PSU count is known.
6. `Finisaje` uses `minimum pe lucrare + supliment pe grup/culoare` rather than only raw `m²`.
7. `Șablon Forex` becomes separate at `RON/m²`.
8. `Ambalare` becomes optional fixed price per order.
9. `Montaj` remains manual / excluded from automatic V6 total in the first commercial-ready slice.

Why this is the best default:

- it resolves the only hard basis ambiguity (`DEBITARE_SPATE`) with the most natural technical quantity already present in the runtime trace;
- it avoids fake `100 buc` PSU multiplication from watt-class data;
- it keeps the first automatic quote focused on workshop-produced deliverables;
- it leaves site installation out of the first auto-total, which is safer than inventing a site rule.

## 10. Post-GO Rule Shapes

These are proposed rule shapes only. They are not implementation approval by themselves.

| Line | Proposed rule shape after owner GO | Notes |
|---|---|---|
| `debitare_fata` | `basis_type=ml`, `quantity=letter_perimeter_m`, `documented_unit_price=RON/ml` | no hourly logic |
| `modelare_cant_aluminiu` | `basis_type=ml`, `quantity=letter_perimeter_m`, `documented_unit_price=RON/ml` | no hourly logic |
| `debitare_spate` | preferred: `basis_type=m2`, `quantity=letter_face_area_m2`, `documented_unit_price=RON/m²` | fallback possible if owner chooses `ml` |
| `sistem_led_module` | `basis_type=piece`, `quantity=led_module_count`, `documented_unit_price=RON/buc` | direct fit for current live trace |
| `sursa_led` | preferred: new rule shape `fixed_by_psu_class` or `piece` with real PSU count | current `selected_psu_watts` should not behave as piece quantity |
| `finisaje_colantare_vopsire` | `minimum_job_price + supplements`, or `m2` plus grouped finish surcharge | owner must choose simplicity vs precision |
| `sablon_montaj_forex` | `basis_type=m2`, `quantity=mounting_template_area_m2`, `documented_unit_price=RON/m²` | supported by live workspace quantity |
| `ambalare` | `basis_type=fixed`, `quantity=None`, `documented_unit_price=RON/comandă` | optional line |
| `montaj` | phase-1 manual exclusion, later separate service rule | safest for first writable slice |

## 11. Minimal Implementation Slices After Owner GO

No implementation should start before the owner packet is answered. After GO, the smallest safe slices are:

### Slice 1. Catalog completion only

- update `backend/data/commercial_rules_volumetric_v2.py`
- replace null unit prices for approved lines
- replace `debitare_spate` basis from `unknown` to approved basis
- replace `sablon_montaj_forex` owner-pending placeholder with approved rule

### Slice 2. PSU rule shape hardening

- stop treating `selected_psu_watts` as implicit piece quantity if owner chooses fixed-by-class pricing
- introduce explicit commercial quantity/selector semantics for PSU pricing
- add focused runtime test proving no `100 buc` accidental multiplication

### Slice 3. Optional line gating

- decide whether `ambalare` and `montaj` unresolved lines should block readiness or stay excluded until selected
- add tests for both selected and unselected optional paths

### Slice 4. Dry-run readiness and write gate

- rerun `build_intake_v6_priced_quote_dry_run(...)`
- verify `commercial_proposal_trace.status = ready`
- verify positive subtotal and gross total
- only then allow official priced quote write path to persist totals

## 12. Explicit Non-Recommendations

Do not do any of the following to force a number:

- do not use `QuoteOrchestrator` cost-plus totals as V6 commercial truth;
- do not derive client prices from internal estimated cost totals;
- do not introduce hourly or minute-based pricing into V6 volumetric commercial lines;
- do not use frontend preview totals as persisted quote authority;
- do not multiply PSU commercial price by raw watt value unless the owner explicitly says that is the intended business rule.

## 13. Final Decision Packet Summary

What the owner must decide now:

- one hard basis decision: `debitare_spate = ml or m²`
- five price-policy decisions: `debitare_fata`, `modelare_cant`, `LED module`, `PSU`, `finisaje`
- one live-workspace active optional decision: `șablon Forex`
- two optional policy decisions: `ambalare`, `montaj`

What engineering can do immediately after owner GO:

- fill the catalog;
- harden PSU rule shape;
- rerun dry-run;
- only then enable quote total persistence.
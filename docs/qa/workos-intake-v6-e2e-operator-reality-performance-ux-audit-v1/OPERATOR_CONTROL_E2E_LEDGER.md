# OPERATOR_CONTROL_E2E_LEDGER

HEAD: `303add0f` · Runtime: `IV6-362B31FC` · Status legend: WORKS / WORKS_BUT_SLOW / NO_EFFECT_INTENTIONAL / NO_EFFECT_DEFECT / STALE / BLOCKED_CORRECTLY / DUPLICATE_AUTHORITY / DEAD_UI / UNCLEAR

Statuses based on live payload+dry-run+CPP OFAT without Owner DB writes. Exhaustive GRADI matrix used as secondary evidence.

## STEP 1 — Straturi

| CONTROL | UI LABEL | DOMAIN | SAVE | COMMERCIAL EXPECTED | OBSERVED | STATUS | LATENCY |
|---------|----------|--------|------|---------------------|----------|--------|---------|
| Layer role confirm | Rol geometrie / confirm | Layers | workspace layer persist | None (gate) | Works; layers confirmed | WORKS | n/a |
| SVG change | Schimbă SVG | Layers | upload | Rebuild composition | Available | WORKS | heavy reparse |
| Continue | Continuă la Configurare | Nav | step | — | Works | WORKS | — |

## STEP 2 — Finisaje (critical probes)

| CONTROL | UI LABEL | PERSISTED FIELD | COMMERCIAL EXPECTED | OBSERVED LIVE | CPP | STATUS | NOTES |
|---------|----------|-----------------|---------------------|---------------|-----|--------|-------|
| Face finish | Fără finisaj — plexiglas brut / Oracal… | `face_finish_type` | Money delta | UI 641; **no face Oracal lines in dry-run** | Gate wants `oracal_641`; adapter emits `vinyl` / `oracal_651` | **NO_EFFECT_DEFECT** | P0 money honesty |
| Face color | Oracal code/name | `face_oracal_*` | No rate tier | Display only | — | NO_EFFECT_INTENTIONAL | Looks commercial |
| Face roll width | mm | `face_vinyl_roll_width_mm` | 8500 tier | Not probed live | YES for 8500 | UNCLEAR live | GRADI: works |
| Cant finish stock | Alb/Negru/… | `return_finish_type=*_aluminum` | No surcharge | — | no finish lines | NO_EFFECT_INTENTIONAL | Misleading if operator expects paint price |
| Cant Oracal | Oracal 651 · depth | `oracal_wrapped` | YES | Lines present; money in total | cant Oracal mat+labor | WORKS_BUT_SLOW | Label mixes film + depth |
| Cant RAL | Vopsit RAL | `ral_paint` | YES | CPP OFAT +21 EUR | RAL mat+labor | WORKS_BUT_SLOW | Owner: slow/empty feel from refresh |
| Cant depth | 30/60/80/100 | `return_depth_mm` | YES on wrap/RAL; stock expect profile $ | Stock: NO_EFFECT | modelare ignores depth | NO_EFFECT_DEFECT (stock) | P1 QTY_OR_BACKING_DEPTH |
| Back Forex | cu/fără șanfren | `backing_mode` | YES (CNC bevel) | UI shows cu șanfren; CPP flat | debitare_spate no bevel | **NO_EFFECT_DEFECT** | P1 backing |
| Technical details accordion | Detalii tehnice… | — | None | Diagnostic | — | DIAGNOSTIC | Primary space leak |
| Diagnostic link | Deschide diagnostic tehnic | — | None | Opens heavy drawer | — | MOVE_TO_DIAGNOSTIC | Eager prod GETs |

## STEP 2 — Iluminare

| CONTROL | EXPECTED | OBSERVED (GRADI/audit) | STATUS |
|---------|----------|------------------------|--------|
| LED on/off | Money | OFF prices; ON baseline | WORKS (off) |
| LED module power / strip | Money | NO_EFFECT | NO_EFFECT_DEFECT |
| PSU watts 100/160/200 | Money | NO_EFFECT (1 PSU unit) | NO_EFFECT_INTENTIONAL / DEFECT vs owner expect |
| Light color | None | NO_EFFECT | NO_EFFECT_INTENTIONAL |

## STEP 2 — Panou / carcasă / Montaj / Compoziție / Ajustări

| CONTROL | STATUS | NOTES |
|---------|--------|-------|
| ACM geometry / L1 L2 / thickness | NO_EFFECT_DEFECT / UNCLEAR | P1 ACM_CONSTRUCTION cluster |
| ACM provisional pricing block | DUPLICATE_AUTHORITY | Provisional vs official Ofertă |
| Mounting template forex/paper | BLOCKED_CORRECTLY / UNCLEAR | Forex may block complete offer |
| Site install toggle | WORKS / UNCLEAR | montaj line |
| Composition confirm | WORKS | Separate write |
| Markup / discount / manual RON | WORKS_BUT_SLOW | Backend dry-run only; FX gate for manual≠0 |
| VAT % | BLOCKED_CORRECTLY readonly | Settings authority |

## STEP 3 — Confirmare

| CONTROL | STATUS | NOTES |
|---------|--------|-------|
| Consolidated status | WORKS | Blocked when handoff incomplete |
| Internal draft checkbox | WORKS | Persist confirmation |
| Ofertă Net/VAT/Gross | WORKS / UNCLEAR honesty | Shows totals even when handoff blocked (commercial composition may still be READY) |
| Create priced quote | BLOCKED_CORRECTLY | Disabled until confirm |

## Owner probes A–D (verdict)

| Probe | Verdict |
|-------|---------|
| A Face material copy “plexiglas brut” | Vocabulary conflation — material ≠ finish |
| B Face finish commercial effect | **DEFECT** — token drift drops face Oracal CPP lines |
| C Cant Oracal/RAL | Rules work; **slow refresh** from orchestration; empty feel from lag/stale |
| D Back bevel | **NO_EFFECT** — CPP does not consume bevel |

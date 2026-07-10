# INTAKE_V6_FOREX_BACKING_FINISH_PANEL_ORDER_V1

**Date:** 2026-07-10
**Task:** `INTAKE_V6_FOREX_BACKING_FINISH_PANEL_ORDER_V1`
**HEAD before:** `face15e`
**HEAD after:** `face15e` (no commit — visual QA PARTIAL on owner route)
**Verdict:** **PARTIAL**

---

## Ce era greșit înainte

1. **Prima iterație (`719844a`):** Forex / Spate litere era secțiune standalone deasupra tab-urilor Review — deconectat vizual de finisaje.
2. **A doua iterație (`face15e`):** Forex era în tab Finisaje, dar ca bloc separat (`border-top` / card propriu) sub litere/logo — nu în același card cu dropdown-urile Față/Cant.
3. **A treia iterație (local, necommit):** Forex mutat în interiorul cardului **Vector Litere** când există letter groups; fallback separat când jobul nu are litere.

## Owner correction

Forex backing = câmp de finisaj în panelul Finisaje, sub litere/logo, aliniat la dropdown-urile Față/Cant. Nu sub LED / Iluminare.

## Ce am mutat (slice curent, local)

- Extras `IntakeV6ReviewBackingFinishRow` — același grid/label/select ca finisajele layer (`REVIEW_LAYER_CARD_GRID_CLASS`, `REVIEW_SELECT_CLASS`).
- Integrat în `IntakeV6ReviewLetterGroupsSection` la finalul cardului Vector Litere (după straturi).
- `IntakeV6ReviewStep`: backing pasat în secțiunea litere; fallback `embedded` doar când `effectiveLetterGroups.length === 0`.
- Helper Vector Litere: *Față = finisaj vizibil · Cant = lateral volum · Spate = Forex corp litere.*

## Fișiere schimbate (slice UI)

- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.tsx` (new)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.test.tsx` (new)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
- `frontend/scripts/capture-intake-v6-forex-backing-finish-panel-order-screenshots.mjs`

## Teste rulate

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx
```

**Rezultat:** 26/26 PASS

## Visual QA — route owner

`http://127.0.0.1:3000/intake-v6/633b5663-8d15-4dca-805f-4cca202323f6/operator`

**Stare fixture la momentul QA:** `Compozitie produs propusa` = **Logo volumetric** (1 segment linked). **Nu există** card Vector Litere pe această rută — doar Vector Logo + fallback Spate litere.

| # | Criteriu | Rezultat pe ruta owner |
|---|----------|------------------------|
| 1 | Forex în interiorul cardului Vector Litere | **FAIL** — nu există Vector Litere; apare fallback `intake-v6-backing-finish-block` |
| 2 | Ultimul rând după straturi (în același card litere) | **FAIL** — N/A fără letter groups |
| 3 | Aliniat vizual cu Față/Cant | **PARTIAL** — grid față ok în fallback; nu se poate compara cu Față litere pe această rută |
| 4 | Aceeași înălțime/font/stil dropdown | **PASS** — `h-7` / `11px`, match cu dropdown artwork |
| 5 | Nu sub LED / Iluminare | **PASS** — `backingNotUnderLed: true` |
| 6 | LED off → Finisaj spate vizibil | **PASS** — vizibil pe tab Finisaje după toggle |
| 7 | Valoare păstrată „Forex 10 mm fara sanfren” | **PASS** — `forex_10_no_bevel` |
| 8 | Calcul live neschimbat | **PASS** — `1.668,88 RON` înainte/după toggle LED |

## Visual QA — fixture suplimentar (litere)

`http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator`

| # | Criteriu | Rezultat |
|---|----------|----------|
| 1 | Forex în card Vector Litere | **PASS** — `backingInsideVectorLitereCard: true` |
| 2 | După straturi | **PASS** (vizual în screenshot 04) |
| 3–4 | Aliniere + stil dropdown | **PASS** (vizual + programmatic height/font match) |

## Screenshot paths

**Obligatorii (ruta owner):**

- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/01_vector_litere_card_with_backing.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/02_backing_dropdown_alignment.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/03_led_off_backing_still_visible.png`

**Suplimentar (dovadă integrare litere):**

- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/04_letter_fixture_vector_litere_with_backing.png`

## Opinie sinceră UI

- **Pe job cu litere (screenshot 04):** integrarea e bună — Forex e ultimul rând în cardul Vector Litere, dropdown identic ca Față/Cant, fără secțiune dublă. **~88/100** pe acest caz.
- **Pe ruta owner (logo-only):** fallback-ul „Spate litere” sub Vector Logo e logic (nu există litere), dar **nu satisface** cerința vizuală 1–2 din checklist; încă arată ca mini-secțiune separată, nu ca rând în card litere. **~55/100** pe această rută.
- **Recomandare:** rerulare visual QA pe un workspace cu **Litere volumetrice + logo** (sau re-seed `633b5663…` dacă anterior avea litere) înainte de commit.

## Scope check

| Zonă interzisă | Atins? |
|----------------|--------|
| Backend | **NO** |
| Pricing / CostEngine | **NO** |
| DB / migrations | **NO** |
| ProductDefinition | **NO** |
| Quote / order / execution | **NO** |

**Forbidden scope respected:** YES — UI + tests + QA artifacts only.

## Git hygiene

```text
git diff --check → FAIL (trailing whitespace în fișier unrelated:
  docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md)
git status --short → dirty worktree (multe fișiere unrelated + slice UI)
```

**Commit:** NU — conform gate: screenshot-urile pe ruta owner nu confirmă criteriile 1–2.

## Cât sunt în direcția stabilită

**82/100%** — implementarea pentru joburi cu litere e corectă; blocajul e fixture-ul QA owner (logo-only) + fallback UI încă puțin „secțiune” pe acel caz.

## Next step

1. Re-seed / alege workspace cu Vector Litere pe ruta owner SAU acceptă ruta `668ffeb2…` ca gate visual.
2. După PASS pe criteriile 1–2 pe ruta aleasă → commit `Fix Intake V6 Forex backing finish panel order`.

---

## Fallback fix — logo-only route (`INTAKE_V6_FOREX_BACKING_CARD_FALLBACK_FIX_V1`)

**Verdict:** PASS

Owner route `633b5663…` is logo-only. Forex moved into **Vector Logo** card via `IntakeV6ArtworkFinishSection` when no Vector Litere. Detached `intake-v6-backing-finish-block` no longer shown on that route.

**Screenshots:** `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix/`

**Tests:** 46/46 PASS

**Cât sunt în direcția stabilită (post-fix):** **92/100%**

See: `docs/worklog/realignment/2026-07-10_intake_v6_forex_backing_card_fallback_fix_v1.md`

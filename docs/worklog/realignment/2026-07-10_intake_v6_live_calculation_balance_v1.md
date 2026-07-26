# Intake V6 — Live Calculation Visual Balance (V1)

**Date:** 2026-07-10  
**Status:** COMPLETE  
**Slice:** INTAKE_V6_LIVE_CALCULATION_BALANCE_V1  
**HEAD before:** `77c6543`  
**Scope:** Pas 2 live calculation panel — display/layout/labels only

---

## Initial UI audit

| Element | Observatie |
| --- | --- |
| Pozitie calcul live | Coloana dreapta desktop (`layout="rightPanel"`), bar sticky mobile deasupra grid-ului |
| Latime | ~360–460px coloana dreapta (grid ReviewStep) |
| Inaltime | Variabilă; totals + 5 linii preview + filtre + diagnostic inline |
| Sticky/non-sticky | Da — `lg:sticky lg:top-4` pe shell (`intake-v6-live-calculation-sticky-shell`) |
| Numar de carduri | 2+ (totals card + line list + diagnostic details) |
| Numar de valori mari | 2–3 (24px emerald gross, internal cost, net inline) |
| Numar de badge-uri | 5–6 filter chips + diagnostic badges |
| Culori dominante | Emerald gross, cyan filters/net, amber missing rates |
| Label principal | „Calcul live” |
| Label secundar | „Preț oficial cu TVA” / „Total cu TVA”, „Cost intern referință” |
| CTA-uri | Filter chips, technical toggle, Details sheet |
| Relatie cu blocker banner | Banner primar sus; calc competa vizual prin gross mare |
| Relatie cu formularul | Sticky dreapta — competiție la scroll |
| Relatie cu footer | Footer separat jos stânga |
| Relatie cu taburile | Calc global workspace, dar poziționat lângă tab activ |
| Risc interpretare pret final | **Ridicat** — „Preț oficial cu TVA”, 24px emerald |

**Problema principala:** **A (prea dominant)** + **E (pare preț final)**; secundar G, H.

---

## Component ownership

| Rol | Componentă |
| --- | --- |
| Afișare calcul | `IntakeV6LiveCalculationSummary.tsx` |
| Date | Props din `IntakeV6ReviewStep.tsx` (`breakdown`, `pricingPreview`, `pricedQuoteDryRun`, `logicalListReadModel`, `commercialInputs`) |
| Layout shell sticky | `IntakeV6ReviewStep.tsx` (neschimbat) |
| Labels | `IntakeV6LiveCalculationSummary.tsx` (constante exportate) |
| Teste | `IntakeV6LiveCalculationSummary.test.tsx` |
| CSS | Tailwind inline în componentă |

---

## Figma consultat

| Item | Value |
| --- | --- |
| File | WorkOS Intake V6 — UI Audit |
| Key | `911Q6oRKcEursrRoT4Qj0h` |
| Pages cerute | 00, 07, 09, 10 |
| Acces runtime MCP | Doar pagina `00 Audit Overview` listată; direcție aplicată din slice-uri anterioare + spec task (operator config first, preview secundar) |

---

## Implementare

### Labels before → after

| Before | After |
| --- | --- |
| Calcul live | **Calcul estimativ live** |
| Preț oficial cu TVA / Total cu TVA | **Valoare estimată cu TVA** |
| Net / Total net | **Estimare netă** |
| Cost intern referință | **Cost intern (referință)** |
| — | Hint: *Se actualizează după configurația curentă. Valoarea finală se confirmă ulterior.* |
| Calcul live — detalii | **Calcul estimativ live — detalii** |

### Layout before → after

| Before | After |
| --- | --- |
| Gross 24px emerald bold | Gross 18px semibold slate (o singură valoare dominantă) |
| Filter chip wall în rightPanel | Filtre doar în Details sheet |
| Diagnostic + technical toggle inline rightPanel | Mutat în Details sheet |
| Bar: 22px emerald + inline filters | Bar compact, fără filter chips inline |
| Panel border puternic | Border/background mai discret |

**Neschimbat:** logica `buildIntakeV6OfferModel`, surse date, sticky shell, `IntakeV6PricingInputPanel`, Pas 3, banner, diagnostic accordion, tab/footer semantics.

---

## Fișiere modificate

- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/scripts/capture-intake-v6-live-calculation-balance-v1-screenshots.mjs`
- `docs/qa/intake-v6-live-calculation-balance-v1/screenshots_index.md`
- `docs/qa/intake-v6-live-calculation-balance-v1/screenshots/*.png` (7 capturi)

---

## Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx `
  src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.test.ts `
  src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx `
  src/components/workos/intake-v6/IntakeV6ReviewTabNav.test.tsx `
  src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx `
  src/lib/intakeV6/intakeV6WorkspaceHeaderStatus.test.ts `
  src/components/workos/intake-v6/atoms/IntakeV6TechnicalDetailsAccordion.test.tsx
```

**Result:** 66/66 PASS (28 live calc + 38 regression)

---

## Screenshots

`docs/qa/intake-v6-live-calculation-balance-v1/screenshots/`

| # | Status |
| --- | --- |
| 01 before | **Indisponibil** — captură pre-implementare ratată |
| 02 balanced default | Capturat |
| 03 with blocker | Capturat |
| 04 subtotals (sheet) | Capturat |
| 05 incomplete | **Indisponibil** pe fixture; acoperit unit test |
| 06 diagnostic collapsed | Capturat |
| 07 iluminare regression | Capturat |
| 08 step1 regression | Capturat |
| 09 step3 unchanged | Capturat |

---

## Regresii verificate

- Blocker banner vizibil (03)
- Diagnostic colapsat (06)
- Iluminare fără pill ON (07)
- Pas 1 badge noise (08)
- Pas 3 neschimbat (09)
- Filter/diagnostic funcționează în sidebar + details sheet (teste existente)

---

## Forbidden scope

Respectat: fără backend, formule, pricing logic, ProductDefinition/Aggregate, Product Truth, Pas 3 logic, tab/footer/diagnostic semantics.

---

## Opinie sinceră

Panoul **era prea dominant** — gross emerald 24px + „Preț oficial” inducea ofertă finală. Noua ierarhie (titlu estimativ, hint discret, gross mai mic neutru, subtotaluri secundare) îl face consultabil fără să concureze cu formularul. **Nu mai pare preț final** în panoul live calc, dar `IntakeV6PricingInputPanel` de dedesubt încă folosește limbaj comercial — out of scope.

Sticky rămâne util pentru estimare la scroll; dominanța e redusă prin tipografie/culoare, nu prin eliminarea sticky.

Competiție banner: redusă; banner rămâne clar primar. Footer: separat, OK.

**Cel mai slab punct rămas:** panoul comercial sliders dedesubt + absența capturii „before” / stare incompletă runtime.

**Ce NU am schimbat:** PricingInputPanel, sticky removal, backend, Pas 3, mobile layout global.

---

## Next safe step

**INTAKE_V6_STEP3_CONSOLIDATED_STATUS_V1**

---

## Direction score

**88/100** — aliniat cu ierarhia stabilită; minus pentru PricingInputPanel adjacent și 2 screenshot-uri indisponibile.

---

## Commit

Mesaj: `Balance Intake V6 live calculation`

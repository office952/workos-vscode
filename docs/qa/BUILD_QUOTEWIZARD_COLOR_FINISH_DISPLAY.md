# BUILD — QuoteWizard Display for RAL / Oracal Color Fields

**Date:** 2026-06-08  
**Template:** `TPL-VOLUMETRIC-LETTERS`  
**Verdict:** PASS

---

## Scop

Afișare read-only a selecțiilor RAL / Oracal 651 / Oracal 8500 în QuoteWizard / flux comercial volumetric, fără pricing sau modificări handoff.

## Context

După buildurile WorkIntake V2 unified flow, Color Registry și Operator Polish:

- Intake capturează corect finisajele în `product_spec_json`
- Readiness și handoff păstrează câmpurile
- Quote preview din Readiness era compact dar duplicat logic
- QuoteWizard (`VolumetricLettersQuoteFlow`) nu afișa explicit finisajele înainte de simulare

## Câmpuri afișate

### Cant / return

- `return_finish_system` → standard / RAL / ORACAL
- Standard: `return_color` / `return_edge_color`
- RAL: `return_ral_code`, `return_ral_name`, `return_ral_preview_hex`
- Oracal: `return_oracal_series`, `return_oracal_code`, `return_oracal_name`, `return_oracal_preview_hex`
- Legacy fallback: `paint_ral_code`, `paint_ral_name` (doar când RAL activ, cu warning)

### Față / folie

- `face_vinyl_enabled` → Nu / Da
- Oracal 651 / 8500: `face_vinyl_series`, `face_vinyl_code`, `face_vinyl_name`, `face_vinyl_preview_hex`
- Legacy fallback: `face_vinyl_color_code`, `face_vinyl_color_name`, `face_finish_type`

## Helper display

**Fișier:** `frontend/src/lib/volumetricFinishDisplay.ts`

**Funcție:** `formatVolumetricFinishSummary(spec)` → `VolumetricFinishSummary`

- Read-only — nu modifică spec, nu normalizează, nu calculează preț
- Refolosit în `WorkIntakeV2ReadinessHandoffCard` quote preview (cant + față)

## UI QuoteWizard

**Component:** `frontend/src/components/workos/VolumetricFinishDisplayPanel.tsx`

**Integrare:** `VolumetricLettersQuoteFlow.tsx` — panel vizibil când `initialProductSpec` există (standalone + embedded)

**Secțiune:** `Finisaje și folii` (`data-testid="quote-finish-display"`)

- Cant / return cu swatch + notă preview aproximativ pentru RAL
- Față / folie cu badge `translucent` pentru 8500
- Warnings legacy (fără duplicate în label principal)

**Routing:** `QuoteWizard.tsx` delegă TPL-VOLUMETRIC-LETTERS la `VolumetricLettersQuoteFlow` — neschimbat.

## Compatibilitate legacy

| Prioritate | Return | Face vinyl |
|------------|--------|------------|
| 1 | `return_finish_system` | `face_vinyl_enabled` |
| 2 | RAL / ORACAL câmpuri canonice | `face_vinyl_series` + `face_vinyl_code` |
| 3 | `return_color` doar pentru standard | `face_vinyl_color_code` fallback |
| 4 | `paint_ral_*` fallback RAL | `face_finish_type` pentru serie |

**Reguli:**

- `return_color: white` nu maschează RAL când `return_finish_system === "RAL"`
- Nu se afișează simultan canonical + legacy ca linii separate
- Warning explicit când se folosește fallback legacy

## Handoff

**Neschimbat:**

```txt
applyFrontlitConstructionDefaults
→ normalizeIntakeProductSpecForSave
→ persistSpec(..., { skipRefresh: false })
→ onOpenQuoteWizard
→ buildQuoteWizardNavStateFromIntake
```

Readiness gates — neschimbate.

## Commercial document / export

`QuoteCommercialDocument.tsx` — **neatinse** (nu consumă încă summary formatat; build separat dacă e necesar backend).

## Teste

| Suite | Rezultat |
|-------|----------|
| `volumetricFinishDisplay.test.ts` | 9/9 PASS |
| `QuoteWizard.volumetricRouting.test.tsx` | +1 test Finisaje și folii PASS |
| `WorkIntakeV2Flow.test.tsx` | PASS (quote preview via același helper) |

**E2E deferred:** flux complet WorkIntake → QuoteWizard UI — costisitor fără CI fixture; acoperit prin unit + QuoteWizard routing test.

## Boundary

**Neatinse:** CostEngine, Pricing calculation, Inventory, backend major, WorkIntake V1, SmartBill, email/order, order confirmation, ACM/Bond, palette import.

## Riscuri rămase

- Export PDF/commercial document nu include încă secțiunea Finisaje
- `paint_ral_code` poate coexista în payload alături de `return_ral_code` (sync legacy) — display folosește canonical first
- E2E handoff → wizard nu rulat automat în CI

## Next candidates

1. **CI/E2E hardening** — smoke WorkIntake → QuoteWizard cu assert pe `quote-finish-display`
2. **Commercial document display** — dacă exportul consumă frontend summary
3. **Pricing linkage** — după display stabil în wizard și document

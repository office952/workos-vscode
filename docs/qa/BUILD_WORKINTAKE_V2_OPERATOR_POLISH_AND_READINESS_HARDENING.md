# BUILD — WorkIntake V2 Operator Polish + Readiness Hardening

**Date:** 2026-06-08  
**Route:** `/intake-v2/:id`  
**Template:** `TPL-VOLUMETRIC-LETTERS`  
**Verdict:** PASS

---

## Scop

Întărire readiness + polish operator pe WorkIntake V2 unified flow, înainte de ACM/Bond Geometry Engine, Pricing linkage sau QuoteWizard display.

## Context audit

Auditul *WorkOS Progress Review: Logic + UI/UX* a dat **PASS with risks** pe ambele axe. Riscuri principale adresate în acest build:

- `productionSaved` prea permisiv (fără `return_depth_mm`, fără cod folie față)
- Zone E duplicată (repair + checklist)
- Zone D densă
- Panouri imbricate (double border)
- Fișiere wizard deprecated

## Probleme rezolvate

| Problemă | Rezolvare |
|----------|-----------|
| Handoff fără adâncime cant | `isProductionStageSaved` cere `effectiveReturnDepthMm` valid |
| Colantare ON fără cod | `isFaceVinylSelectionComplete` — serie + `face_vinyl_code` |
| RAL/Oracal return incomplet | `isReturnFinishCompleteForV2` — cod + nume (+ serie Oracal) |
| CTA disabled generic | `getFirstWorkIntakeV2BlockerLabel` în header |
| Readiness duplicată | Checklist înlocuit cu `CompactStageSummary` collapsible |
| Zone D aglomerată | Secțiuni `<details>`: Cant, Față, LED, PSU, Avansat |
| Double borders | `v2StageShellClass(embedded)` pe stage-uri în carduri |
| Dead code | Șters fișiere neimportate (vezi cleanup) |

## Readiness changes

**`stageCompletion.ts`**

- `hasValidReturnDepthForProduction` — folosește `effectiveReturnDepthMm` + `ALLOWED_RETURN_DEPTH_MM`
- `isReturnFinishCompleteForV2` — standard / RAL (cod+nume) / ORACAL (serie+cod+nume)
- `isFaceVinylSelectionComplete` — când `face_vinyl_enabled`, cere `face_vinyl_series` + `face_vinyl_code`
- `isProductionStageSaved` — export public pentru teste

**`repairPanel.ts`**

- Blockers explicite: `return-depth`, `return-ral`, `return-oracal`, `face-vinyl-code`
- `getFirstWorkIntakeV2BlockerLabel` pentru header CTA

## UI changes

| Zonă | Schimbare |
|------|-----------|
| **Header** | `work-intake-v2-cta-blocker-reason` — primul blocker concret |
| **Zone D** | Secțiuni `work-intake-v2-section-return`, `-face-vinyl`, `-lighting-led`, `-psu` |
| **Zone E** | Repair list principal + `work-intake-v2-stage-summary` (progres collapsible) + quote preview |
| **Zone C** | Stage-uri `embedded` — fără border dublu în card |

## Cleanup efectuat

| Fișier | Status |
|--------|--------|
| `WorkIntakeV2StageNav.tsx` | Șters — zero importuri |
| `WorkIntakeV2RepairPanel.tsx` | Șters — logică în Readiness card |
| `V2QuoteStage.tsx` | Șters — înlocuit de QuotePreview + header CTA |
| `V2ContextStage.tsx` | Șters — înlocuit de JobDetails + header |
| `V2VerificationStage.tsx` | Șters — înlocuit de CompactStageSummary |
| `intakeProductSpec.HEAD.ts` | Șters — artefact merge |
| `intakeProductSpec.MIXED.ts` | Șters — artefact merge |

## Cleanup deferred

| Item | Motiv |
|------|-------|
| `onContinue` props pe stage-uri | Opțional dead path; risc minim, poate fi curățat ulterior |
| Playwright CI pipeline | Nu există `.github/workflows` — build separat CI/E2E hardening |
| E2E DB fixture `WI-E2E-COMMERCIAL-WARN-001` | Încă necesar pentru smoke; seed automat = build viitor |

## Teste rulate

```bash
cd frontend
npx vitest run src/lib/workIntakeV2/stageCompletion.test.ts
npx vitest run src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx
npx vitest run src/lib/workIntakeV2/
```

## Rezultate

| Suite | Rezultat |
|-------|----------|
| `stageCompletion.test.ts` | 6/6 PASS |
| `WorkIntakeV2Flow.test.tsx` | 24/24 PASS |
| `src/lib/workIntakeV2/*` | 33/33 PASS |

**E2E:** `work-intake-v2-volumetric.spec.ts` actualizat (return depth gate, face vinyl gate, stage-summary). Rulare locală necesită backend + `npm run dev` — neexecutat în acest build.

## Handoff confirmare

- `handleOpenQuoteWizardHandoff` neschimbat: `normalizeIntakeProductSpecForSave` → `persistSpec(skipRefresh: false)` → `onOpenQuoteWizard`
- Teste existente handoff PSU/geometry/color — PASS
- Gates noi blochează CTA până la date complete — nu pierd câmpuri la handoff

## Boundary

**Neatinse:** CostEngine, Pricing, Inventory, backend major, WorkIntake V1, SmartBill, email offer, order confirmation, ProductSystem unrelated, registry data, full palette import, ACM/Bond geometry.

## Riscuri rămase

- QuoteWizard nu afișează încă culorile noi în UI dedicat
- `return_color` legacy poate coexista cu RAL în payload (sync legacy) — display QuoteWizard = build viitor
- E2E fragil fără CI + fixture DB seed

## Next candidates

1. **QuoteWizard display for colors** — handoff are date, wizard nu le arată încă pe toate
2. **CI/E2E hardening** — Playwright în pipeline + fixture seed
3. **Deprecated file cleanup** — `onContinue` dead props (minor)
4. **ACM / Bond Cassette Geometry Engine** — după QuoteWizard display

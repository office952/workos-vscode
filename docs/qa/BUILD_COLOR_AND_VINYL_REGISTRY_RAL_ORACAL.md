# BUILD: Color & Vinyl Registry — RAL + Oracal 651 / 8500

**Date:** 2026-06-08  
**Status:** **PASS**  
**Template scope:** `TPL-VOLUMETRIC-LETTERS`  
**Route:** `/intake-v2/:id` — zone D (`WorkIntakeV2VolumetricRulesCard` / `V2ProductionStage`)

---

## 1. Purpose

Introduce a controlled **color and vinyl registry** for WorkIntake V2 operator selection:

- **RAL** — painted finishes (return/cant, structure; preview approximate)
- **Oracal 651** — colored cast vinyl (face, return wrap)
- **Oracal 8500** — translucent vinyl for illuminated faces

Goals:

- Visual selector with code + name + swatch preview
- Structured save into `product_spec_json`
- Preserve quote handoff pipeline
- **No automatic pricing** in this build

---

## 2. Context

Follows closed build **WorkIntake V2 Unified Operator Flow** (ERP-9/11/12).

Integration point: zone D — volumetric production rules inside unified WorkIntake V2.

Pricing registry / CostEngine / Inventory pricing are **out of scope** — separate future build.

---

## 3. Registry model

Location: `frontend/src/lib/colorRegistry/`

| File | Role |
|------|------|
| `colorRegistryTypes.ts` | `ColorRegistryItem`, usage scopes, finish systems |
| `ralColors.ts` | RAL subset (representative — full palette = separate import build) |
| `oracal651.ts` | Oracal 651 colored vinyl subset |
| `oracal8500.ts` | Oracal 8500 translucent subset (`translucent: true`) |
| `colorRegistry.ts` | Search, filter, lookup, label formatting |
| `colorRegistrySpec.ts` | Patch helpers + `isReturnFinishComplete` |

### `ColorRegistryItem` shape

```ts
{
  system: "RAL" | "ORACAL";
  brand?: "Oracal";
  series?: "651" | "8500";
  code: string;
  name: string;
  romanianName?: string;
  previewHex: string;
  usageScope: ["return" | "face_vinyl" | "illuminated_face" | ...];
  translucent?: boolean;
  active: boolean;
}
```

651 and 8500 are **never mixed** — UI labels `651 colored` vs `8500 translucent`.

---

## 4. UI behavior

Component: `frontend/src/components/workos/colorRegistry/ColorRegistrySelect.tsx`

- Search by code / name
- Color swatch preview
- System + series badges
- RAL approximate preview note
- Filter by `usageScope`, `system`, `series`
- Inactive items disabled

### Zone D — `V2ProductionStage`

**Finisaj cant / return** (`work-intake-v2-return-finish-section`):

| System | UI |
|--------|-----|
| Standard | Existing white/black stock select |
| RAL | `ColorRegistrySelect` + approx note |
| ORACAL | Oracal **651 only** for return wrap |

**Face vinyl** (when enabled):

- Radio: Oracal **651** vs **8500 translucent**
- `ColorRegistrySelect` filtered by series + usage scope
- 8500 scoped to `illuminated_face`

---

## 5. Fields in `product_spec_json`

### Return / cant

```txt
return_finish_system: "standard" | "RAL" | "ORACAL"
return_color / return_edge_color          (standard — preserved)
return_ral_code / return_ral_name / return_ral_preview_hex
return_oracal_series / return_oracal_code / return_oracal_name / return_oracal_preview_hex
paint_ral_code / paint_ral_name           (synced from RAL selection — legacy compat)
```

### Face vinyl

```txt
face_vinyl_enabled
face_vinyl_series: "651" | "8500"
face_vinyl_code / face_vinyl_name / face_vinyl_preview_hex
face_vinyl_finish
face_finish_type: oracal_651 | oracal_8500
face_vinyl_color_code / face_vinyl_color_name  (legacy quote compat)
```

Persisted via `normalizeVolumetricIntakeSpecForSave` in `intakeVolumetricSpec.ts`.

---

## 6. Handoff safety

Pipeline **unchanged**:

```txt
applyFrontlitConstructionDefaults
→ normalizeIntakeProductSpecForSave
→ persistSpec(..., { skipRefresh: false })
→ onOpenQuoteWizard
```

New color fields pass through normalize — verified in unit tests.

Readiness: `productionSaved` uses `isReturnFinishComplete()` — RAL/ORACAL/standard all valid; new fields **not mandatory** unless operator selects non-standard finish.

Quote preview (`WorkIntakeV2ReadinessHandoffCard`) shows formatted return finish + face vinyl codes.

---

## 7. Files changed

### Added

- `frontend/src/lib/colorRegistry/*` (types, data, registry, spec helpers, tests)
- `frontend/src/components/workos/colorRegistry/ColorRegistrySelect.tsx`
- `frontend/src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx`

### Modified

- `frontend/src/lib/intakeProductSpec.ts` — new optional fields
- `frontend/src/lib/intakeVolumetricSpec.ts` — normalize new fields
- `frontend/src/lib/workIntakeV2/stageCompletion.ts` — `isReturnFinishComplete`
- `frontend/src/components/workos/workIntakeV2/stages/V2ProductionStage.tsx` — registry UI
- `frontend/src/components/workos/workIntakeV2/cards/WorkIntakeV2ReadinessHandoffCard.tsx` — preview labels
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx` — color + handoff tests

### Not touched

- CostEngine, Pricing calculation, Inventory stock/pricing
- Backend major
- WorkIntake V1
- SmartBill, email offer, order confirmation
- Unrelated ProductSystem files

---

## 8. Tests run

```bash
cd frontend
npx vitest run \
  src/lib/colorRegistry/colorRegistry.test.ts \
  src/lib/colorRegistry/colorRegistrySpec.test.ts \
  src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx \
  src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx \
  src/lib/workIntakeV2/stageCompletion.ts \
  src/lib/workIntakeV2/workIntakeV2.test.ts
```

**Result:** `42/42 PASS` (5 files)

- Registry search/filter/translucent 8500
- Spec patch helpers (RAL, Oracal return, face 8500)
- Selector swatch + onChange + 651/8500 differentiation
- Production RAL selection in Flow
- Handoff preserves color + PSU + geometry fields

---

## 9. Boundary

No CostEngine · Pricing · Inventory · backend major · V1 · SmartBill · new templates · automatic pricing.

Registry is **frontend config only** — not Inventory-driven.

Initial palette is **representative subset** — full RAL/Oracal import requires validated source data (separate build).

---

## 10. Risks / follow-ups

| Item | Notes |
|------|-------|
| Partial palette | Extend `ralColors.ts` / `oracal*.ts` when validated PDF/CSV available |
| Pricing registry | Map registry codes → Pricing in separate build |
| `finish_selection` object | Documented direction — not implemented (explicit fields preferred) |
| E2E color smoke | Optional — add to `work-intake-v2-volumetric.spec.ts` when stable |
| QuoteWizard display | May need UI to show new fields beyond prefill (future) |

---

## 11. Status

**PASS** — registry, selector, zone D integration, persist, handoff preservation, tests, boundary respected.

---

## Next candidates

- Full RAL palette import (validated)
- Pricing registry linkage for Oracal/RAL codes
- Cable channel / structure RAL selectors
- E2E smoke for color selection flow

# ProductSystem — Shared Technical Modules

## Purpose

WorkOS ProductSystem templates (`TPL-VOLUMETRIC-LETTERS`, future lightboxes, CNC services, vinyl-only jobs) share physical production rules that must **not** be duplicated inside each template form or dossier.

This document indexes reusable modules and records owner direction for modules not yet fully extracted.

**Status:** `SHARED_VINYL_MATERIAL_CATALOG` foundation implemented (2026-06) — see [`SHARED_VINYL_MATERIAL_CATALOG.md`](SHARED_VINYL_MATERIAL_CATALOG.md). UI / Pricing Registry migration still pending.

---

## Module map (started + planned)

| Module | Doc / implementation | Status |
|--------|----------------------|--------|
| `CNC_OPERATION_MODEL` | [`SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE.md`](SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE.md), `shared_cnc_operation_model.py` | **Started** — preview rows + material process profiles |
| `LIGHTING_RULES` | [`LED_LIGHTING_DENSITY_RULES.md`](LED_LIGHTING_DENSITY_RULES.md), `shared_led_lighting_density_rules.py` | **Started** — perimeter + area density |
| `MATERIAL_PROCESS_PROFILES` | `shared_cnc_material_process_profiles.py` (CNC slice) | **Started** — CNC materials only |
| `CONSUMABLE_RULES` | adhesive/wiring in `intake_v4_consumables_*` | **Started** — Intake V4 slice |
| `EDGE / CANT RULES` | [`SHARED_EDGE_CANT_RULES.md`](SHARED_EDGE_CANT_RULES.md), `shared_edge_cant_rules.py` | **Foundation** — cant length, adhesive, Oracal 651 wrap, preview operation rows |
| **`SHARED_VINYL_MATERIAL_CATALOG`** | [`SHARED_VINYL_MATERIAL_CATALOG.md`](SHARED_VINYL_MATERIAL_CATALOG.md), `shared_vinyl_material_catalog.py` | **Foundation** — profiles 641/651/8500, owner prices, applications |
| **`VINYL_APPLICATION_RULES`** | same doc + `VinylApplication` enum | **Foundation** — allowed applications per series |

Related but separate:

- **Color / palette registry** — `frontend/src/lib/colorRegistry/` (RAL, Oracal 651, Oracal 8500 swatches). Not a price catalog.
- **Pricing Registry / CostEngine** — quote-time rates; **out of scope** for vinyl catalog doc until dedicated build.

---

## Why Oracal series must not live in every template

Owner decision:

> Seriile Oracal 641, 651, 8500 nu trebuie hardcodate în fiecare template/formular. Trebuie tratate ca un catalog comun de materiale vinil/autocolant și reguli de aplicare.

Same vinyl SKUs appear across:

- față litere volumetrice;
- cant / volum litere;
- casete luminoase;
- panouri;
- print / colantare;
- servicii doar colantare;
- lucrări cu materialul nostru vs materialul clientului.

Templates should request an **application** (`face_letters`, `return_cant_volum`, …) and resolve material from a shared catalog — not redefine series, prices, palette keys, stock keys, and warnings per template.

---

## `SHARED_VINYL_MATERIAL_CATALOG` (planned)

### `VinylMaterialProfile` (target model)

```txt
VinylMaterialProfile
  material_key              # stable id, e.g. oracal_651
  brand                     # Oracal
  series                    # 641 | 651 | 8500
  display_name              # operator label
  material_type             # standard_vinyl | premium_vinyl | translucent_vinyl | print_laminate
  stock_material_key        # inventory_materials.code when mapped
  pricing_material_rate_key # registry / alias key for quote pricing
  unit                      # m² | ml (roll)
  price_source              # registry | owner_confirmed_interim | missing
  palette_source            # colorRegistry series key or manual_only
  allowed_applications[]    # see VINYL_APPLICATION_RULES
  default_waste_factor
  roll_width_mm             # optional default roll
  outdoor_rating            # optional metadata
  notes
```

### Interim owner prices (central source — not UI literals)

Until Pricing Registry is complete for all vinyl SKUs, owner-confirmed purchase tiers:

| Series | EUR/m² (excl. TVA) | Current interim implementation |
|--------|-------------------|--------------------------------|
| Oracal 641 | **6.5** | `intake_v4_oracal_face_pricing_service.py` |
| Oracal 651 | **9.0** | same |
| Oracal 8500 | **20.0** | same |

**Direction:** move these into `SHARED_VINYL_MATERIAL_CATALOG` (or a thin `owner_confirmed_vinyl_prices` module) consumed by Intake V4 preview, material breakdown, and future templates — **not** scattered constants in UI components.

### Seed registry codes (compatibility)

Product 001 material registry v1.1 documents logical codes (not all wired to live pricing):

- `MAT_ORACAL_641`
- `MAT_ORACAL_651`
- `MAT_ORACAL_8500_TRANSLUCENT`

Intake V4 breakdown uses operational codes `MAT-ORACAL-{series}` for owner-priced face rows.

---

## `VINYL_APPLICATION_RULES` (planned)

Applications templates should reference instead of hardcoding series:

| Application key | Typical material | Notes |
|-----------------|------------------|-------|
| `face_letters` | 641 / 651 / 8500 per operator choice | area basis from quote geometry / nesting |
| `return_cant_volum` | Oracal 651 (default wrapped cant) | perimeter / lateral basis; 641 future if catalog expands |
| `lightbox_face` | 8500 translucent | illuminated face |
| `panel` | print + laminate or 651 | future templates |
| `vehicle` | generic vinyl service | future |
| `generic_vinyl_service` | operator-selected profile | CNC cutting service post-process |

Rules engine responsibilities (future):

- which applications allow which `material_type`;
- palette binding (`palette_source`);
- when to warn (e.g. 8500 priced as 651 — legacy CostEngine path);
- client-supplied vs internal stock (`consumes_stock_now` preview semantics).

### Current behavior to preserve

| Rule | Detail |
|------|--------|
| 641 vs 651 palette | Oracal **641** and **651** may share the **651 color registry palette** in UI (`oracalColorPaletteSeriesForFace`). |
| 641 vs 651 pricing | **641 must not be priced as 651** — separate EUR/m² (6.5 vs 9.0). |
| 8500 pricing | **8500 must not be priced as 651** — 20.0 EUR/m²; tests in `test_intake_v4_oracal_641_651_pricing.py`. |
| Cant / volum | `oracal_wrapped` → operator label **Oracal 651**; workbench vinyl application task. |
| 8500 use | Translucent / illuminated faces; separate registry (`oracal8500.ts`). |
| 641 colors | **Not in color registry** — manual code entry (`ORACAL_641_REGISTRY_HINT` in V2 letter group UI). |

---

## Template usage (target)

Templates declare **application slots**, not material series:

### `TPL-VOLUMETRIC-LETTERS`

- `face_finish` → vinyl application `face_letters` (641 / 651 / 8500 / print laminate).
- `return_finish` → `return_cant_volum` when `oracal_wrapped`.
- lighted emblem → translucent vinyl optional via `face_letters` + 8500 profile.

### `TPL-LIGHTBOX` (future)

- face → `lightbox_face` (8500 / translucent).
- panel → print + laminate.

### `TPL-CNC-CUTTING-SERVICE` (future)

- optional `generic_vinyl_service` after cutting.

Payload tokens like `oracal_651`, `oracal_641`, `oracal_8500` remain **compatibility aliases** mapping to `VinylMaterialProfile.material_key` during migration.

---

## Repo audit — Oracal / vinyl (2026-06)

Use this checklist when opening build **`SHARED_VINYL_MATERIAL_CATALOG`**.

### 1. Where are Oracal series hardcoded today?

| Layer | Location | What is hardcoded |
|-------|----------|-------------------|
| **Intake V4 face finish** | `frontend/src/lib/intakeV4/intakeV4FaceFinishOptions.ts` | tokens `oracal_641`, `oracal_651`, `oracal_8500`; palette series mapping |
| **Intake V4 UI** | `IntakeV4ReviewStep.tsx`, `IntakeV4LetterGroupFinishesSection.tsx` | `<option>` labels for 651 / 8500 |
| **Intake V4 return** | `intakeV4ReturnFinishOptions.ts`, `intake_v4_finish_truth_service.py` | `oracal_wrapped` → Oracal 651 label |
| **WorkIntake V2** | `letterGroupFinishUi.ts`, `V2ProductionStage`, spec editors | face/return Oracal enums, wrapped series 641/651 |
| **Legacy volumetric intake** | `volumetricQuoteInput.ts`, `volumetricFrontlitIntake.ts`, `intakeVolumetricSpec.ts` | `VOLUMETRIC_FACE_FINISH_OPTIONS`, `oracal_651` defaults |
| **Product 001 editor** | `Product001IntakeSpecEditor.tsx` | face finish select options |
| **Backend breakdown** | `intake_v4_material_breakdown_service.py` | `MATERIAL_REGISTRY_CODES["face_vinyl"]` → `MAT-ORACAL-651` default; dynamic `MAT-ORACAL-{series}` for owner rows |
| **Backend pricing interim** | `intake_v4_oracal_face_pricing_service.py` | series set `{641,651,8500}` |
| **CostEngine policy** | `volumetric_quote_input_policy.py` | `WARNING_ORACAL_8500_PRICED_AS_651` (legacy quote path) |
| **Seeds / registry** | `seed_product_001_material_registry_v1_1.py` | `MAT_ORACAL_*` documentation rows |
| **Task dry-run** | `intake_v4_task_generation_dry_run_service.py` | `MAT-ORACAL-651` on vinyl cut job |
| **Production narrative** | `volumetricLettersProduction.ts` | shop-floor timing text for 651/8500 |

### 2. Where are prices 6.5 / 9.0 / 20.0 hardcoded?

| Location | Values |
|----------|--------|
| **`backend/services/intake_v4_oracal_face_pricing_service.py`** | `INTAKE_V4_ORACAL_641_EUR_PER_M2 = 6.5`, `651 = 9.0`, `8500 = 20.0` |
| **`backend/tests/test_intake_v4_oracal_641_651_pricing.py`** | asserts against same constants |
| **Pricing Registry** | **Not** the source for these three tiers in Intake V4 preview (by design until catalog build) |
| **Inventory `/inventory/pricing`** | May supply `MAT-ORACAL-651` in tests; owner Oracal face rows use `price_source=intake_v4_owner_oracal_*` |

No 6.5 / 9 / 20 literals found in frontend TypeScript for Oracal (preview costs come from API).

### 3. Where are palettes defined?

| Asset | Scope |
|-------|--------|
| `frontend/src/lib/colorRegistry/oracal651.ts` | full Oracal 651 swatch list |
| `frontend/src/lib/colorRegistry/oracal8500.ts` | translucent 8500 swatches |
| `frontend/src/lib/colorRegistry/colorRegistry.ts` | merges RAL + 651 + 8500 |
| `frontend/src/lib/colorRegistry/colorRegistryTypes.ts` | `OracalSeries = "651" \| "8500"` only |
| `intakeV4FaceFinishOptions.ts` | **641 reuses 651 palette filter** |
| Import pipeline | `colorRegistry/import/` — CSV validation; 641 not in generated registry |

### 4. UI consumers

- Intake V4: `IntakeV4LetterGroupFinishesSection`, `IntakeV4ReviewStep`, confirm summary (`intakeV4ConfirmSummary.ts`)
- WorkIntake V2: letter group finish UI, production stage, quote stage summaries
- QuoteWizard finish display: `BUILD_QUOTEWIZARD_COLOR_FINISH_DISPLAY.md` scope
- Product001 / legacy spec editors
- Color picker components wired through `filterColorRegistry`

### 5. Backend service consumers

- `intake_v4_material_breakdown_service.py` — face vinyl rows, owner Oracal pricing
- `intake_v4_oracal_face_pricing_service.py` — series resolution + EUR/m²
- `intake_v4_finish_truth_service.py` — missing Oracal color blockers
- `intake_v4_finish_adapter.py` / production flags — `return_vinyl_application_required`
- `intake_v4_task_generation_dry_run_service.py` — vinyl cut / application tasks
- `intake_v4_production_handoff_preview_service.py` — handoff job hints
- `volumetric_quote_input_policy.py` — legacy 8500-as-651 warning
- `volumetric_material_rate_resolver.py` — **PSU only**, not Oracal vinyl

### 6. What should move into shared vinyl catalog?

| Move | Keep local (for now) |
|------|----------------------|
| Owner EUR/m² tiers (641/651/8500) | Per-template geometry basis (area vs perimeter) |
| `material_key` ↔ registry code ↔ inventory code mapping | Letter-group payload shape (`face_finish_type` tokens) |
| `allowed_applications` per profile | Template-specific finish truth gates |
| `palette_source` + manual-only flag (641) | ColorRegistry TS files (presentation); link via `palette_source` |
| `price_source` enum + missing-price warnings | CostEngine formula handlers |
| Print / laminate vinyl profiles (`MAT-VINYL-PRINT*`) | CNC operation rows |

Suggested implementation path:

1. `backend/services/shared_vinyl_material_catalog.py` (+ optional frontend mirror for labels).
2. Replace literals in `intake_v4_oracal_face_pricing_service.py` with catalog lookups.
3. UI option lists generated from catalog filtered by `allowed_applications`.
4. Later: Pricing Registry rows keyed by `pricing_material_rate_key`.

### 7. What must stay for compatibility?

- Payload tokens: `oracal_651`, `oracal_641`, `oracal_8500`, `oracal_wrapped`, `print_laminate`.
- `face_finish_type` / `return_finish_type` on `finish_setup` and letter groups.
- `MAT-ORACAL-{series}` breakdown row codes and `intake_v4_owner_oracal_*` price_source strings (audit trail).
- Color registry series **651** and **8500** files — add 641 palette only if owner imports catalogue.
- `WARNING_ORACAL_8500_PRICED_AS_651` until CostEngine path uses distinct 8500 rate everywhere.
- Quote handoff fields: `face_vinyl_series`, `return_oracal_*`, preview hex fields.

---

## Build boundaries (when implemented)

- **Do not** change Oracal EUR/m² without dedicated build + pytest (`test_intake_v4_oracal_641_651_pricing.py`).
- **Do not** mutate Pricing Registry or CostEngine global handlers in the catalog extraction build.
- **Do not** break Intake V4 material breakdown owner rows or confirm summary labels.
- Prefer read-only catalog + adapter layer first; migrate UI selects second.

---

## Recommended next build

**`BUILD_SHARED_VINYL_UI_AND_REGISTRY_MIGRATION`** (after foundation)

1. Frontend mirror for labels/options from catalog.
2. Refactor UI selects to filter by `allowed_applications` + template.
3. Pricing Registry rows keyed by `registry_code`.
4. Return cant vinyl area via catalog perimeter rules.

Foundation complete: `shared_vinyl_material_catalog.py` + Intake V4 pricing adapter (no EUR/m² change).

**After CNC dry-run alignment (2026-06):** technical modules remain open for dedicated builds — do not bundle into ProductSystem refactor:

- `CNC_OPERATION_MODEL` — operation_rows → dry-run alignment done; catalog mapping gaps still pending for some `operation_catalog_key` rows.
- `LIGHTING_RULES` — emblem area_lit foundation; further PSU catalog alignment separate.
- `SHARED_VINYL_MATERIAL_CATALOG` — UI migration still pending.
- **Future:** `EDGE/CANT_RULES`, `CONSUMABLE_RULES` (full shared module), `VINYL_APPLICATION_RULES` (UI + registry wiring).

---

## Code references (vinyl catalog)

- `backend/services/shared_vinyl_material_catalog.py`
- `backend/tests/test_shared_vinyl_material_catalog.py`
- `docs/architecture/SHARED_VINYL_MATERIAL_CATALOG.md`

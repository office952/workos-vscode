# Shared Vinyl Material Catalog — ORACAL 641 / 651 / 8500

## Purpose

Oracal vinyl series are **shared ProductSystem materials**, not per-template hardcodes. Templates declare an **application** (`face_letters_premium`, `return_cant_volum_wrapping`, `backlit_sign_face`, …) and resolve a `VinylMaterialProfile` from the catalog.

Implementation: `backend/services/shared_vinyl_material_catalog.py`

Related index: [`PRODUCTSYSTEM_SHARED_TECHNICAL_MODULES.md`](PRODUCTSYSTEM_SHARED_TECHNICAL_MODULES.md)

**Foundation build** — does not migrate all UI, Pricing Registry, or Color Registry.

---

## Why not hardcode in each template

| Context | Same vinyl SKUs |
|---------|-----------------|
| Litere volumetrice | față 641/651/8500, cant Oracal 651 |
| Casete luminoase | 8500 translucent face |
| Panouri | 641/651, print + laminate |
| Servicii colantare | generic vinyl service |
| CNC cutting service | optional post-cut vinyl (future) |

Each template should **not** redefine series, EUR/m², palette keys, registry codes, or warnings.

---

## Comparative table (owner + ORAFOL technical data)

| Series | Type | Thickness | Adhesive | App temp | Service life (outdoor CE) | Recommended use | Owner price |
|--------|------|-----------|----------|----------|---------------------------|-----------------|-------------|
| **641** | Economy Cal | **75 µm** | polyacrylate permanent | **> +10°C** | 3–4 years | short/medium markings, standard face | **6.5 EUR/m²** |
| **651** | Intermediate Cal | **70 µm** | solvent polyacrylate permanent | **> +8°C** | 3–5 years | outdoor markings, **cant/volum** | **9.0 EUR/m²** |
| **8500** | Translucent Cal | **80 µm** | solvent polyacrylate permanent | **> +8°C** | 5–7 years | **backlit / illuminated faces** | **20.0 EUR/m²** |

### Pricing rules (must preserve)

- **641 ≠ 651** — separate owner tier (6.5 vs 9.0).
- **651 ≠ 8500** — 8500 is **20.0 EUR/m²**, not 9.0.
- **641 UI palette** may reuse **651 color registry** swatches; pricing still uses 641 tier.
- **Cant / volum** `oracal_wrapped` → **651** application (`return_cant_volum_wrapping`).
- **Illuminated / backlit** → prefer **8500** profiles.

---

## `VinylMaterialProfile` fields

See dataclass in `shared_vinyl_material_catalog.py`:

- Identity: `material_key`, `brand`, `series`, `display_name`, `technical_name`
- Physics: `thickness_micron`, `adhesive_type`, `release_paper_gsm`, temperature range, `adhesive_power_n_per_25mm`
- Commercial: `price_eur_per_sqm`, `pricing_source`, `registry_code`, `breakdown_material_code`
- UX: `palette_source` → Color Registry binding (or manual gap for 641)
- Applications: `allowed_applications`, `recommended_templates`
- Datasheets: `technical_datasheet_filename`, `official_datasheet_url`, `official_product_page_url`

---

## Allowed applications

### ORACAL 641

- `face_letters_standard`
- `panel_standard`
- `generic_short_medium_marking`

### ORACAL 651

- `face_letters_premium`
- `return_cant_volum_wrapping`
- `panel_premium`
- `generic_outdoor_marking`

### ORACAL 8500

- `lightbox_face_translucent`
- `backlit_sign_face`
- `illuminated_acrylic_face`
- `illuminated_letter_face`

Helpers: `is_vinyl_application_allowed()`, `profiles_for_vinyl_application()`.

---

## Owner prices (interim central source)

Until Pricing Registry covers all vinyl SKUs:

```txt
ORACAL 641 = 6.5 EUR/m²  → intake_v4_owner_oracal_641
ORACAL 651 = 9.0 EUR/m²  → intake_v4_owner_oracal_651
ORACAL 8500 = 20.0 EUR/m² → intake_v4_owner_oracal_8500
```

Consumed by `intake_v4_oracal_face_pricing_service.py` via `resolve_owner_oracal_price_eur_per_sqm()` — **no value change** in this foundation build.

Owner Oracal fallback sources are protected from Pricing Registry overrides even when composed with module source prefixes (e.g. `shared_edge_cant_rules|intake_v4_owner_oracal_651` on edge/cant wrap rows).

---

## Technical datasheet sources

### Owner-uploaded PDFs (internal — not stored in git)

| Series | Filename |
|--------|----------|
| 641 | `fisa-tehnica-d-ORACAL641.pdf` |
| 651 | `fisa-tehnica-d-ORACAL651.pdf` |
| 8500 | `fisa-tehnica-d-ORACAL8500.pdf` |

### ORAFOL official (Europe)

| Series | Product page | Technical data sheet (PDF) |
|--------|--------------|----------------------------|
| **641** Economy Cal | https://www.orafol.com/en/europe/products/oracal-641-economy-cal | https://www.orafol.com/products/europe/en/technical-data-sheet/oracal-641-economy-cal-3550-technical-data-sheet-europe-en.pdf |
| **651** Intermediate Cal | https://www.orafol.com/en/europe/products/oracal-651-intermediate-cal | https://www.orafol.com/products/europe/en/technical-data-sheet/oracal-651-intermediate-cal-id3534-technical-data-sheet-europe-en.pdf |
| **8500** Translucent Cal | https://www.orafol.com/en/europe/products/oracal-8500-translucent-cal | https://www.orafol.com/products/europe/en/technical-data-sheet/oracal-8500-translucent-cal-3710-technical-data-sheet-europe-en.pdf |

`datasheet_sources` on each profile: `owner_uploaded_pdf` + `orafol_official`.

### Common application warnings (all series)

- Clean surfaces free of dust, grease, contaminants.
- Fresh paint/lacquer: minimum **3 weeks** cure before application.
- Test paint/lacquer compatibility.
- ORAFOL data is advisory; verify suitability per job.

---

## Color registry linkage

| Series | `palette_source` | Color Registry today |
|--------|------------------|----------------------|
| 641 | `shared_651_palette_manual_entry` | **No 641 catalogue** — UI filters `color_registry:651`; manual code (`ORACAL_641_REGISTRY_HINT` in V2) |
| 651 | `color_registry:651` | `frontend/src/lib/colorRegistry/oracal651.ts` |
| 8500 | `color_registry:8500` | `frontend/src/lib/colorRegistry/oracal8500.ts` (translucent) |

**Do not recreate palettes in this build** — catalog only documents binding.

---

## Intake V4 linkage (current)

| Concern | Path |
|---------|------|
| Face finish tokens | `oracal_641`, `oracal_651`, `oracal_8500` |
| Pricing adapter | `intake_v4_oracal_face_pricing_service.py` → catalog |
| Material breakdown rows | `MAT-ORACAL-{series}`, owner `price_source` |
| Return cant | `oracal_wrapped` → 651 label / workbench task (not yet catalog-driven UI) |

Intake V4 **prices and calculations unchanged** — adapter reads same EUR/m² from catalog.

---

## Future template linkage

### `TPL-LIGHTBOX` (planned)

- Face: `lightbox_face_translucent` → **8500** profile.
- Panel: print + laminate (separate vinyl profiles — future).

### `TPL-CNC-CUTTING-SERVICE` (planned)

- Optional `generic_outdoor_marking` / vinyl service after cut.
- Client-supplied material: operation rows without stock material row (mirror CNC service pattern).

### `TPL-VOLUMETRIC-LETTERS` (current)

- Face: `face_letters_standard` (641) or `face_letters_premium` (651) or illuminated → 8500.
- Return: `return_cant_volum_wrapping` → 651.

---

## Repo audit snapshot (foundation build)

1. **Series hardcoded** — Intake V4 face options, V2 `letterGroupFinishUi`, legacy volumetric intake, material breakdown default `MAT-ORACAL-651`.
2. **Prices 6.5 / 9 / 20** — now centralized in `shared_vinyl_material_catalog.py`; adapter in `intake_v4_oracal_face_pricing_service.py`.
3. **Palettes** — `colorRegistry/oracal651.ts`, `oracal8500.ts`; 641 shares 651 picker.
4. **Backend consumers** — material breakdown, finish truth, task dry-run, handoff preview.
5. **Frontend consumers** — Intake V4 letter groups, V2 production, Product001 editor.
6. **Extract to catalog** — done for metadata + prices + applications; UI migration pending.
7. **Compatibility** — keep payload tokens, `MAT-ORACAL-*` codes, `intake_v4_owner_oracal_*` price_source strings.

---

## Remaining work (out of scope for foundation)

- [ ] Generate UI face/return options from catalog filtered by template + application.
- [ ] Wire `stock_material_key` when inventory codes owner-confirmed.
- [ ] Pricing Registry rows per `registry_code` / `breakdown_material_code`.
- [ ] Return cant vinyl area pricing via catalog (perimeter basis).
- [ ] `TPL-LIGHTBOX` / CNC service template consumption.
- [ ] Frontend mirror module (`sharedVinylMaterialCatalog.ts`) for labels only.

---

## Tests

- `backend/tests/test_shared_vinyl_material_catalog.py`
- Regression: `backend/tests/test_intake_v4_oracal_641_651_pricing.py`

---

## Code references

- `backend/services/shared_vinyl_material_catalog.py`
- `backend/services/intake_v4_oracal_face_pricing_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `frontend/src/lib/colorRegistry/`
- `frontend/src/lib/intakeV4/intakeV4FaceFinishOptions.ts`
- `backend/seeds/seed_product_001_material_registry_v1_1.py`

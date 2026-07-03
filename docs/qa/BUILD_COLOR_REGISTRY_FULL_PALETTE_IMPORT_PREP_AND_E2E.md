# BUILD: Color Registry — Full Palette Import Prep + E2E Color Smoke

**Date:** 2026-06-08  
**Status:** **PASS**  
**Template scope:** `TPL-VOLUMETRIC-LETTERS`  
**Route:** `/intake-v2/:id` — zone D (`WorkIntakeV2VolumetricRulesCard` / `V2ProductionStage`)

---

## 1. Purpose

Prepare validated import infrastructure for full RAL / Oracal 651 / Oracal 8500 palettes, harden the live color/vinyl selection flow in WorkIntake V2, and add E2E smoke coverage — **without** inventing palette data, pricing, Inventory, or CostEngine changes.

Follows closed build **Color & Vinyl Registry — RAL + Oracal 651 / 8500** (representative subset in runtime registry).

---

## 2. Context

| Area | State |
|------|-------|
| Runtime registry | Representative subsets in `ralColors.ts`, `oracal651.ts`, `oracal8500.ts` (unchanged count) |
| UI selector | `ColorRegistrySelect` in zone D |
| Handoff | `product_spec_json` → QuoteWizard preview |
| Full palette | **Deferred** — no validated tabular source in repo |

---

## 3. Sources analyzed

| System | Reference | In repo? | Action |
|--------|-----------|----------|--------|
| RAL Classic | Industry fan decks / supplier PDFs | No machine-readable file | Import deferred |
| Oracal 651 | folii-adezive.ro — Oracal 651 Intermediate Cal | Not imported | Manual validation required before CSV |
| Oracal 8500 | folii-adezive.ro — Oracal 8500 Translucent Cal | Not imported | Manual validation required before CSV |
| Prior QA doc | `docs/qa/BUILD_COLOR_AND_VINYL_REGISTRY_RAL_ORACAL.md` | Yes | Subset-only baseline confirmed |
| Project seed scripts | `backend/scripts/seed_commercial_e2e_fixture.py` | Yes | No palette data — geometry/commercial only |

**Decision:** No bulk import. Mechanism + validator + documentation only; runtime subset preserved.

---

## 4. Import format

**Location:** `frontend/src/lib/colorRegistry/import/`

| File | Role |
|------|------|
| `color-registry-import.template.csv` | Header + 3 example rows (template only — not production data) |
| `README.md` | Workflow, sources, deferral notice |
| `validateColorRegistryImport.mjs` | Parse + validation rules (shared with Vitest) |

**CSV columns:**

```txt
system,brand,series,code,name,romanianName,previewHex,finish,usageScope,translucent,active,source,notes
```

**Example row semantics:**

- RAL: no `brand` / `series`; `usageScope` semicolon-separated; `previewHex` approximate
- Oracal 651: `brand=Oracal`, `series=651`, `translucent=false`
- Oracal 8500: `series=8500`, `translucent=true`, scopes include `illuminated_face`

**CLI (read-only — does not modify TS):**

```bash
cd frontend
npm run validate:color-registry
# or
node scripts/validate-color-registry-import.mjs path/to/validated/color-registry.csv
```

---

## 5. Validation rules

| Rule | Enforced |
|------|----------|
| `system` ∈ `RAL` \| `ORACAL` | Yes |
| Oracal → `brand=Oracal`, `series=651` \| `8500` | Yes |
| RAL → no `series` | Yes |
| 8500 → `translucent=true` | Yes |
| 651 → `translucent=false` | Yes |
| `code`, `name`, `source` required | Yes |
| `previewHex` valid `#RRGGBB` | Yes |
| `usageScope` tokens ∈ known set | Yes |
| Unique key `system + series + code` | Yes |
| Inactive rows flagged (not auto-imported) | Yes |

---

## 6. Bugfix (series switch)

**Issue:** `clearFaceVinylColorSelection()` included `face_vinyl_series: undefined` and was spread *after* series assignment in `selectFaceSeries`, resetting Oracal 8500 back to default 651.

**Fix:** Remove `face_vinyl_series` from clear helper; spread clear before series assignment; explicit series clear when disabling face wrap. Face vinyl series control changed from radio group to `<select>` for reliable E2E and operator UX.

---

## 7. E2E color smoke

**File:** `frontend/e2e/work-intake-v2-color-registry.spec.ts`

**Fixture:** `WI-E2E-COMMERCIAL-WARN-001` (seed: `backend/scripts/seed_commercial_e2e_fixture.py`)

**Flow validated:**

1. Open WorkIntake V2 unified flow — zone D visible
2. `return_finish_system = RAL` → search/select RAL 9010 → swatch + approximate note
3. Enable face wrap → select Oracal **8500** series → select code 010 → translucent label
4. Save production → readiness panel intact
5. Handoff preview shows return RAL + face Oracal 8500

**CTA note:** QuoteWizard CTA may remain disabled until full volumetric checklist (geometry, PSU) is complete — test asserts CTA visible and repair panel present; color fields must not break readiness UI.

**Run:**

```bash
# Backend :8000 + frontend :3000 (or preview :3001 after build)
cd frontend
PW_SKIP_WEB_SERVER=1 npx playwright test e2e/work-intake-v2-color-registry.spec.ts
```

---

## 8. Tests run

| Suite | Result |
|-------|--------|
| `validateColorRegistryImport.test.ts` | 9/9 PASS |
| `colorRegistry.test.ts` | 6/6 PASS |
| `colorRegistrySpec.test.ts` | 5/5 PASS |
| `ColorRegistrySelect.test.tsx` | (prior build) PASS |
| `WorkIntakeV2Flow.test.tsx` (+ face 8500 switch) | 20/20 PASS |
| CLI `npm run validate:color-registry` | PASS (3 template rows) |
| Playwright `work-intake-v2-color-registry.spec.ts` | 1/1 PASS |

---

## 9. Boundary (confirmed untouched)

| Area | Touched? |
|------|----------|
| CostEngine | No |
| Pricing calculation | No |
| Inventory stock/pricing | No |
| Backend major | No |
| WorkIntake V1 | No |
| SmartBill / email offer / order confirmation | No |
| New templates | No |
| Hardcoded prices | No |
| Invented palette codes/HEX | No |

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Full palette still manual | Documented workflow + validator; TODO in `import/README.md` |
| RAL HEX previews approximate | UI note retained; validator allows `notes` for provenance |
| E2E depends on DB fixture | Document seed script; fixture reset on clean DB |
| Import CSV not yet in repo | `validated/color-registry.csv` path reserved; gitignore when added |

---

## 11. Next candidates

1. Obtain validated Oracal 651/8500 CSV from folii-adezive.ro (manual cross-check)
2. Licensed RAL Classic tabular export → validate → import build
3. Optional codegen script: validated CSV → `ralColors.ts` / `oracal651.ts` / `oracal8500.ts`
4. Pricing registry linkage (separate build)
5. Inventory stock lookup for vinyl rolls (separate build)

---

## 12. Files created / modified

**Created**

- `frontend/src/lib/colorRegistry/import/README.md`
- `frontend/src/lib/colorRegistry/import/color-registry-import.template.csv`
- `frontend/src/lib/colorRegistry/import/validateColorRegistryImport.mjs`
- `frontend/scripts/validate-color-registry-import.mjs`
- `frontend/src/lib/colorRegistry/validateColorRegistryImport.test.ts`
- `frontend/e2e/work-intake-v2-color-registry.spec.ts`
- `docs/qa/BUILD_COLOR_REGISTRY_FULL_PALETTE_IMPORT_PREP_AND_E2E.md`

**Modified**

- `frontend/package.json` — `validate:color-registry` script
- `frontend/src/lib/colorRegistry/colorRegistrySpec.ts` — fix `clearFaceVinylColorSelection`
- `frontend/src/components/workos/workIntakeV2/stages/V2ProductionStage.tsx` — series `<select>`, specRef patch, clear order fix
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx` — face 8500 switch test

**Registry data files:** Not extended (subset unchanged).

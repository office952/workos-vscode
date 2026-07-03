# BUILD_INTAKE_V4_PRICING_PAGE_REGISTRY_ALIGNMENT_PACK

**Date:** 2026-06-22  
**Status:** PASS (scoped V4 pricing lookup aligned to `/inventory/pricing` BLK-18 bridge)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `77538e629467b879738ff8b83da363739e037c2a`  
**Commit:** none (awaiting user confirmation)

---

## Purpose

Close the Intake V4 pricing pillar: material breakdown unit prices must come from the same administrable source as `/inventory/pricing` (which already fed Intake V2 / QuoteWizard via BLK-18), not from a looser parallel lookup or owner hardcoded fallbacks.

---

## Working tree before (off-scope dirty — do NOT include in commit)

| Area | Examples |
|------|----------|
| Intake V3 operator workspace | `backend/services/intake_v3_*`, `frontend/src/components/workos/intake-v3/**`, `useIntakeV3OperatorWorkspace.ts`, … |
| Auth / V2 SVG | `AuthContext.tsx`, `V2SvgStage.tsx`, … |
| Untracked tmp / atoms / e2e | `tmp/`, `docs/audit/INTAKE_V4_ALIGNMENT_AUDIT.md`, `frontend/e2e/intake-v4-*.spec.ts`, … |

---

## Files audited (read-only)

| Path | Role |
|------|------|
| `frontend/src/App.tsx` | Route `/inventory/pricing` → `Pricing.tsx` |
| `frontend/src/pages/Pricing.tsx` | Pricing Registry UI hub |
| `frontend/src/lib/pricingRegistry.ts` | Edit validation / patch payloads |
| `frontend/src/api/pricingRegistry.ts` | `GET /api/v1/pricing/registry` |
| `frontend/src/api/inventoryMaterialsAdmin.ts` | Material PATCH |
| `frontend/src/api/workcenterRatesAdmin.ts` | Operation rate PATCH |
| `backend/routers/pricing_registry.py` | Registry aggregation endpoint |
| `backend/services/pricing_registry_service.py` | Template-driven registry view |
| `backend/services/inventory_materials_admin_service.py` | `load_material_pricing_dict`, `load_material_cost_dict` |
| `backend/services/quote_orchestrator.py` | `create_with_registry` — V2 quote path |
| `backend/services/intake_v3_material_quantity_breakdown_service.py` | `_lookup_registry_price` (loose gate + owner fallbacks) |
| `backend/services/intake_v4_material_breakdown_service.py` | V4 material rows + price apply |
| `backend/seeds/seed_volumetric_owner_confirmed_prices.py` | Owner-confirmed volumetric material prices |
| `backend/tests/test_pricing_registry.py` | Pricing registry + BLK-18 bridge tests |

---

## Files modified (in-scope for this build)

| File | Change |
|------|--------|
| `backend/services/intake_v4_material_breakdown_service.py` | Replace V3 `_lookup_registry_price` with `resolve_v4_registry_material_price` via `load_material_pricing_dict` |
| `backend/tests/test_intake_v4_material_breakdown.py` | Mock `load_material_pricing_dict`; assert no `owner_fallback` |
| `backend/tests/test_intake_v4_pricing_registry_alignment.py` | **New** — BLK-18 gate unit + seeded integration tests |
| `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` | Copy: prices from `/inventory/pricing`; missing → operator hint; not final QuoteWizard total |
| `docs/qa/BUILD_INTAKE_V4_PRICING_PAGE_REGISTRY_ALIGNMENT_PACK.md` | This document |

**Not touched:** CostEngine formulas, QuoteWizard commercial totals, V2/V3 dirty files, stock consumption, ACM/bond activation.

---

## A. `/inventory/pricing` audit

### 1. Frontend route

`frontend/src/App.tsx` — `<Route path="/inventory/pricing" element={<Pricing />} />`  
Legacy aliases redirect here (`/inventory/material-price-registry`, commercial markup, productsystem preview).

### 2. Components

- `frontend/src/pages/Pricing.tsx` — main hub
- `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx` — template-first layout
- `frontend/src/components/pricing/PricingEntryRow.tsx` — row rendering
- Helpers: `frontend/src/lib/pricingRegistry.ts`, `pricingRegistryUi.ts`

### 3. APIs called

| API | Purpose |
|-----|---------|
| `GET /api/v1/pricing/registry` | Read template-filtered pricing registry |
| `PATCH /api/v1/admin/inventory-materials/{code}` | Edit material unit cost + metadata |
| `GET /api/v1/admin/inventory-materials/{code}` | Refresh row after edit |
| `GET .../price-history` | Audit trail |
| `PATCH /api/v1/admin/workcenter-rates/{code}` | Edit operation rates |
| Commercial markup policies admin API | Markup policies section (read/edit) |
| `costEngineApi` | Dry-run / verification helpers in UI |

### 4. Backend entities

| Entity | Storage |
|--------|---------|
| Material unit costs | `inventory_materials` |
| Operation rates | `workcenter_rates` |
| Commercial markup | `commercial_markup_policies` |
| Template usage | `product_templates` (read via `PricingRegistryService`) |

Pricing Registry **does not duplicate** prices — it aggregates template-used codes and joins live registry rows.

### 5. Editable fields (materials)

Via Pricing page material edit form (`MaterialEditFormState`):

- `unit_cost`, `currency`, `vat_percent`, `valid_from`, `status`
- `source_review_status`, `source_notes`, `change_reason` (required on patch)

Workcenter rates: `rate_per_hour`, `rate_per_linear_meter`, `rate_basis`, `currency`, `status`, validity fields.

### 6. What the page administers

**Materials + operations + commercial markup policies** — all in one operator hub.  
Not inventory stock levels, suppliers, or purchase orders.

### 7. Terminology differences

| Term | Meaning |
|------|---------|
| **Inventory pricing page** | Operator UI at `/inventory/pricing`; edits `inventory_materials` / `workcenter_rates` |
| **Material Registry** | Colloquial name for `inventory_materials` rows (admin CRUD) |
| **Pricing Registry** | Read-only aggregation (`PricingRegistryService`) of template-used codes + live costs |
| **ProductSystem pricing** | Template formulas / `quote_input` — quantities and which codes apply, not unit cost storage |
| **CostEngine material rates** | Runtime `{code: unit_cost}` from `load_material_cost_dict` — **same inclusion gate** as pricing dict |

---

## B. Intake V2 audit

### 8. Where V2 consumed `/inventory/pricing` prices

WorkIntake V2 does **not** call the Pricing page directly. Flow:

1. Operator completes intake → QuoteWizard handoff
2. `QuoteOrchestrator.create_with_registry(db)` loads `load_material_pricing_dict` / `load_material_cost_dict` and `load_workcenter_rate_dict`
3. CostEngine applies ProductSystem template formulas (area, perimeter, hours, material qty)

Same backend tables the Pricing page edits.

### 9. Material codes (TPL-VOLUMETRIC-LETTERS)

From template + volumetric resolver: `MAT-ACP-FATA-LITERE`, `MAT-SPATE-PVC-LITERE`, `MAT-ORACAL-651`, `MAT-VINYL-PRINT*`, `MAT-PROFIL-LATERAL-LITERE-{30,60,80,100}MM`, `MAT-LED-MODULE`, `MAT-LED-PSU-12V-{60,100,160,200}W`, consumables, paint, mounting templates, etc.

### 10. Same backend entity as Pricing page?

**Yes** — `inventory_materials` (+ `workcenter_rates` for operations).

### 11. V2 formulas

**Yes** — area/perimeter-driven quantities in ProductSystem template; operation hours from workcenter rates. Nesting was **not** the V2 quote quantity source.

### 12. V2 source of truth for quoting

- **Unit costs / rates:** `inventory_materials` + `workcenter_rates` via BLK-18 bridge (active + complete metadata)
- **Quantities:** `quote_input` built from intake geometry (area/perimeter paths)

### 13. V2 deprecated for V4 copy

- Direct area/perimeter-only quantity paths where V4 has valid nest2 data (V4 prefers nesting for quote estimate)
- V3-style owner_confirmed_fallback prices in breakdown preview (V4 must not use)
- Stock consumption / sheet leftover logic (explicitly out of scope)

---

## C. Intake V4 audit

### 14. Where V4 looked up prices (before fix)

`intake_v4_material_breakdown_service._apply_registry_prices` imported V3 `_lookup_registry_price` — single-row scan: `active` + `unit_cost > 0` only.

### 15–16. Same source as `/inventory/pricing`?

| Aspect | Before fix | After fix |
|--------|------------|-----------|
| Table | `inventory_materials` | Same |
| Inclusion gate | Loose (no `vat_percent` / `valid_from` / currency required) | **`load_material_pricing_dict`** — identical to CostEngine / QuoteOrchestrator |
| Owner fallbacks | None in V4 (V3 has aluminum fallbacks) | Still none |
| `price_source` | `"pricing_registry"` even when CostEngine would exclude row | `"pricing_registry"` only when row is quote-ready; else `"missing"` |

**Verdict:** **Partially aligned → aligned** after this build.

### 17. Code compatibility

V4 `MATERIAL_REGISTRY_CODES` + depth/PSU variant maps use the **same codes** exposed in Pricing Registry for `TPL-VOLUMETRIC-LETTERS`.  
**Exception:** audit list mentions LED 0.72W / 1.44W — V4 uses single **`MAT-LED-MODULE`** (count from pitch/perimeter, not separate wattage SKUs).

### 18. Price entered in `/inventory/pricing` → V4 breakdown?

**Yes**, when row is `status=active` with `unit_cost > 0`, non-empty `currency`, `vat_percent` set, `valid_from` set — same as CostEngine.  
If operator sets cost but leaves `vat_percent` or `valid_from` empty, Pricing UI may still show the row with warnings; V4 correctly marks **`missing`**.

### 19. Risk: V4 `missing` while Pricing page shows price?

**Mitigated.** Previously yes (loose V3 scan vs strict bridge). Now V4 uses the same dict as registry `cost_engine_materials` join.

### 20. Risk: V4 shows price where CostEngine would refuse?

**Mitigated** for material unit costs — shared gate. CostEngine can still block quotes for **other** reasons (currency base mismatch, missing operations, template blockers) not reflected in material breakdown preview.

---

## D. Material codes — V4 vs Pricing page

Seeded reference: `seed_volumetric_owner_confirmed_prices.py` (dev after seed = **yes** for seeded env).  
Production/dev DB without seed depends on operator data — treat as environment-specific.

| code | name (canonical) | unit | source entity | editable in /inventory/pricing? | found in seeded dev? | used by V4? | missing risk | notes |
|------|------------------|------|---------------|--------------------------------|----------------------|-------------|--------------|-------|
| `MAT-ORACAL-651` | Oracal 651 face vinyl | mp | inventory_materials | yes | yes (seed) | yes (`face_vinyl`) | low if metadata complete | 5 EUR/mp seed |
| `MAT-ACP-FATA-LITERE` | Plexiglas față litere | mp | inventory_materials | yes | yes | yes (`plexiglas_face`) | low | alias ACP față |
| `MAT-SPATE-PVC-LITERE` | Forex spate litere | mp | inventory_materials | yes | yes | yes (`forex_backing`) | low | 16 EUR/mp seed |
| `MAT-PROFIL-LATERAL-LITERE-30MM` | Cant 30 mm | ml | inventory_materials | yes | yes | yes (depth map) | low | |
| `MAT-PROFIL-LATERAL-LITERE-60MM` | Cant 60 mm | ml | inventory_materials | yes | yes | yes | low | |
| `MAT-PROFIL-LATERAL-LITERE-80MM` | Cant 80 mm | ml | inventory_materials | yes | yes | yes | low | |
| `MAT-PROFIL-LATERAL-LITERE-100MM` | Cant 100 mm | ml | inventory_materials | yes | yes | yes | low | |
| `MAT-LED-MODULE` | LED module (generic) | buc | inventory_materials | yes | yes | yes (`led_modules`) | low | **Not** separate 0.72W/1.44W codes — single SKU |
| LED 0.72W / 1.44W | — | — | — | n/a | n/a | **mapped to `MAT-LED-MODULE`** | n/a | Wattage is engineering param, not pricing SKU |
| `MAT-LED-PSU-12V-60W` | PSU 60W | buc | inventory_materials | yes | yes | yes (PSU map) | low | |
| `MAT-LED-PSU-12V-100W` | PSU 100W | buc | inventory_materials | yes | yes | yes | low | |
| `MAT-LED-PSU-12V-160W` | PSU 160W | buc | inventory_materials | yes | yes | yes | low | |
| `MAT-LED-PSU-12V-200W` | PSU 200W | buc | inventory_materials | yes | yes | yes | low | |
| `MAT-VINYL-PRINT` | Print vinyl față | mp | inventory_materials | yes | yes | yes (`print_vinyl`) | low | |
| `MAT-VINYL-PRINT-LAMINATED` | Print + laminare | mp | inventory_materials | yes | yes | yes (`laminated_vinyl`) | low | |

---

## Quote material costing vs final commercial price

| Layer | Role |
|-------|------|
| **Intake V4 material breakdown** | Informative **material-only** estimate for operator review; nesting-preferred qty + registry unit costs; `stock_consumption=false` |
| **QuoteWizard / CostEngine** | Authoritative commercial quote — materials + operations + markup policies + blockers |
| **Inventory / stock** | Not a price source; no consumption wired in V4 |

Changing a price in `/inventory/pricing` updates V4 preview **and** future QuoteWizard runs (same bridge). V4 total ≠ QuoteWizard total (operations, markup, rounding).

---

## What was fixed in this build

1. **V4 price lookup** now calls `load_material_pricing_dict` (BLK-18) instead of V3 loose row scan.
2. **Tests** prove incomplete rows → `missing`; seeded volumetric codes → `pricing_registry`; no `owner_fallback`.
3. **UI copy** directs operator to `/inventory/pricing` for missing prices and clarifies non-final total.

---

## What was NOT fixed (and why)

| Gap | Reason |
|-----|--------|
| V3 `_lookup_registry_price` + owner fallbacks | Out of build boundary (V3 dirty) |
| Separate LED 0.72W / 1.44W pricing SKUs | Product decision — single `MAT-LED-MODULE` is template truth |
| Pricing page showing rows CostEngine excludes | UI already warns; strict gate is intentional (BLK-18) |
| Stock consumption / leftovers | Explicitly forbidden |
| CostEngine formula changes | Explicitly forbidden |

---

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_pricing_registry_alignment.py -q
```

**Result:** `16 passed`

Frontend: copy-only change — Vitest omitted (no logic change).

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| `/inventory/pricing` documented | ✅ |
| V2 → Pricing relationship clear | ✅ |
| V4 reads same BLK-18 source | ✅ (fixed) |
| Material codes mapped / gaps documented | ✅ |
| Missing prices point to `/inventory/pricing` | ✅ |
| No hardcoded fallback | ✅ |
| Preview ≠ final commercial total | ✅ |
| CostEngine not modified | ✅ |
| V2/V3 dirty not included | ✅ |
| Relevant tests pass | ✅ |

---

## FAIL criteria check

None triggered (no new Pricing page, no parallel registry, no hardcoded prices, no stock consumption, no CostEngine rewrite).

---

## Recommendation

**Recommend commit** (scoped files only):

```
fix(intake-v4): align material breakdown prices with inventory pricing BLK-18 bridge
```

Suggested staged paths:

- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_intake_v4_pricing_registry_alignment.py`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `docs/qa/BUILD_INTAKE_V4_PRICING_PAGE_REGISTRY_ALIGNMENT_PACK.md`

---

## Follow-ups

1. **V3 alignment** — consider migrating V3 breakdown off `_lookup_registry_price` / owner fallbacks (separate build).
2. **Pricing UI gate parity** — optional UX to hide or flag rows that fail BLK-18 completeness before operator expects V4 to price them.
3. **Live E2E** — optional smoke: edit price in `/inventory/pricing` → refresh V4 Review breakdown (requires dev stack).
4. **LED SKU policy** — document in template dossier that module wattage variants are not separate registry codes.

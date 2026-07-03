# BUILD_INTAKE_V4_MATERIAL_COSTING_FOR_QUOTE



**Date:** 2026-06-22  

**Status:** PASS (scoped quote material costing — nesting-preferred)  

**Branch:** `local/integration-pr4-plus-svg-path`  

**HEAD before:** `c6bf6a7db17719cb4eae442327ebe6e4fd658d10`  

**Commit:** `feat(intake-v4): add nesting-preferred quote material costing` (user-approved)




---



## Purpose



Material **cost estimate for quoting** in Intake V4 — not real stock consumption, sheet remnants, or inventory depletion.



Contract:



`analysis + template + finish + /inventory/pricing registry = quote material cost estimate`



**V4 target:** More realistic quote costing from **nesting-derived quantities** where SVG Analyzer provides valid child-part nesting. **Nesting is the preferred quote estimate basis when data is valid** — not the primary model for all materials (cant, LED, PSU, print remain geometry-driven).

**Fallback (not primary):** Area / perimeter + configurable waste (`area_with_waste_fallback`, `perimeter_with_waste`) applies only when nesting is missing or not sufficiently valid (e.g. unplaced parts). This preserves V2-compatible geometry rules as **fallback only**.

| Concept | Meaning |
|---------|---------|
| `quote material costing from nesting estimate` | Operator-facing material cost preview for quoting |
| `actual stock consumption` | **Out of scope** — no inventory depletion, remnants, or MRP in this build |

### Sheet nesting pro-rata (interim)

When both face and backing areas exist but nest2 sheet nesting returns a single `usedSheetAreaSqm` bucket, plexiglas and Forex quantities are **pro-rated** by geometry ratio. This is an **interim solution** — not role-accurate, **not real stock consumption**.

**Mandatory follow-up:** Split sheet nesting by **layer role from placements** (face vs backing child parts) to replace pro-rata with placement-derived `sheet_nesting_quote_estimate` per material line.




---



## Pricing source



| Layer | Role |

|-------|------|

| `/inventory/pricing` | Operator UI — edits `inventory_materials` + `workcenter_rates` |

| `load_material_cost_dict` | CostEngine bridge (Intake V2 QuoteWizard) |

| V4 `_lookup_registry_price` | Same `inventory_materials.unit_cost` (active) — no hardcoded OWNER_FALLBACK |



Follow-up for dev gaps: **Pricing Page / Registry Alignment**, not a new Pricing Foundation.



---



## Costing basis priority (policy v1)



### Preferred (nesting-derived)



| Material | Basis | `quantity_basis` | Waste on priced qty |

|----------|-------|------------------|---------------------|

| Oracal / colant tăiat | Roll nesting `usedRollAreaSqm` (child parts, layer/color) | `roll_nesting_quote_estimate` | No double buffer |

| Plexiglas față | Sheet nesting `usedSheetAreaSqm` (pro-rata față/spate when both) | `sheet_nesting_quote_estimate` | No double buffer |

| Forex spate | Sheet nesting (pro-rata) | `sheet_nesting_quote_estimate` | No double buffer |



### Fallback (V2-compatible geometry)



When nesting unavailable or invalid (`unplacedItemsCount > 0` → lower `confidence`):



| Material | Basis | `quantity_basis` | `confidence` |

|----------|-------|------------------|--------------|

| Plexiglas / Forex / Oracal | Geometry area + default waste (20%) | `area_with_waste_fallback` | `estimate_fallback_area` |

| Cant aluminiu | Perimeter × depth variant | `perimeter_with_waste` | `estimate_for_quote` |

| Print + laminare | Artwork / print area + waste | `print_area_with_waste`, `lamination_area_with_waste` | `estimate_for_quote` |

| LED | Perimeter / pitch | `led_modules_perimeter_pitch_estimate` | `estimate_for_quote` |

| PSU | Configuration variant | `psu_configuration_variant` | `estimate_for_quote` |



**Out of scope:** ACM/Bond casetare, stock depletion, remnants, CostEngine changes.



---



## UI basis labels



Material rows expose `quantity_basis` for operator audit:



- `roll_nesting_quote_estimate`

- `sheet_nesting_quote_estimate`

- `area_with_waste_fallback`

- `perimeter_with_waste`



`nesting_rows` remain a read-only comparison panel (rolls ml, sheets buc) — not a second pricing ledger.



---



## Files modified



| File | Change |

|------|--------|

| `backend/schemas/intake_v4.py` | Quote costing row/response contract fields |

| `backend/services/intake_v4_material_breakdown_service.py` | Nesting-preferred costing + explicit fallbacks |

| `backend/tests/test_intake_v4_material_breakdown.py` | Roll/sheet nesting + fallback tests |

| `frontend/src/lib/intakeV4/intakeV4Api.ts` | TS types for costing fields |

| `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` | Basis labels + nesting comparison copy |

| `docs/qa/BUILD_INTAKE_V4_MATERIAL_COSTING_FOR_QUOTE.md` | This doc |



---



## Tests run



```powershell

cd backend

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q

```



---



## PASS criteria



| Criterion | Status |

|-----------|--------|

| Oracal prefers roll nesting when jobs valid | ✅ |

| Plexiglas/Forex prefer sheet nesting when valid | ✅ (pro-rata when both areas) |

| Area/perimeter fallback when nesting missing | ✅ |

| No double waste on nesting rows | ✅ |

| Nesting ≠ stock consumption | ✅ |

| No hardcoded prices | ✅ |

| Same registry as `/inventory/pricing` | ✅ |

| No CostEngine / ACM / stock | ✅ |



---



## Next build recommendation

1. **Sheet nesting role split (mandatory)** — attribute sheet placements to face vs backing by layer role; remove pro-rata interim  
2. **Pricing Page / Registry Alignment** — seed `inventory_materials` for volumetric codes  
3. **Area vs nesting precision study** — compare fallback totals vs nesting totals per workspace  
4. **API handoff hash sync** — `create-draft-quote` stale guard



---



## Boundary



**In scope:** quote material cost contract, nesting-preferred enrichment, fallback labeling, UI, tests.



**Out of scope:** stock consumption, remnants, CostEngine, ACM bond, commits without user OK.



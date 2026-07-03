# BUILD: TPL-VOLUMETRIC-LETTERS Production Rules & Lighting System

**Build status:** PARTIAL PASS (intake/spec automation complete; CostEngine consumes existing LED/PSU fields only)

**Git:** Not committed (working tree was dirty at build start — mixed with SVG geometry hotfix work)

## Owner decisions implemented

| Rule | Status |
|------|--------|
| Visual chamfer mandatory | PASS — `visual_chamfer_included: true`, UI locked |
| Front illumination only | PASS — `illumination_family: "front_lit"`, no halo/backlit UI |
| Return white/black stock only | PASS — no brut/RAL on cant; paint section hidden |
| Face vinyl toggle | PASS — `face_vinyl_enabled` / „Fața se colantează?” |
| Lighting system module + strip | PASS |
| Warm/cold, no cost delta | PASS — metadata only |
| PSU ≥ consumption × 1.15 | PASS — auto-select + blocker if > 200 W |

## product_spec_json fields (canonical)

- `visual_chamfer_included`, `face_miter_chamfer`
- `illumination_family`, `illumination_type`
- `face_vinyl_enabled` (+ legacy `face_wrap_enabled`)
- `return_color` (+ legacy `return_edge_color`)
- `lighting_system_type`: `led_modules` \| `led_strip`
- `led_module_power_w`, `led_strip_density`, `led_strip_power_w_per_ml`
- `light_color`: `warm` \| `cold`
- `total_led_watts`, `required_psu_watts`, `selected_psu_watts`
- `psu_sizing_status`: `ok` \| `pending_geometry` \| `insufficient_capacity`
- `psu_sizing_warning`

## PSU sizing

```
required_psu_watts = total_led_watts × 1.15
selected = smallest in {60,100,160,200} where selected >= required
```

If none: `insufficient_capacity` + warning (no silent under-size).

## Readiness

`collectFrontlitIntakeMissing()` drives simulate/final missing lists in `volumetricIntakeFormPrep.ts`. No Oracal blockers when `face_vinyl_enabled = false`. No paint-tube requirement for standard return.

## QuoteWizard handoff

Prefills: `selected_psu_watts`, `total_led_watts`, `required_psu_watts`, existing geometry + face finish. CostEngine still derives `led_module_count` from perimeter; strip-specific costing not extended in this build.

## Tests run

- `volumetricFrontlitIntake.test.ts`
- `volumetricVectorFastAskMapping.test.ts`
- `volumetricIntakePathway.test.ts`
- `Product001IntakeSpecEditor.vectorFastAsk.test.tsx`
- Backend pytest: not run (`python` unavailable in shell)

## Remaining gaps

- QuoteWizard/CostEngine: LED strip wattage not a separate formula input yet (stored in spec only)
- `light_color` not passed to material registry (production metadata)
- Commercial E2E not re-run in this pass

## Boundaries preserved

- No CostEngine formula changes
- No new template activation
- No execution spine changes

---

## Hotfix follow-up (after Commit 2 `80415fd`)

Commit 2 landed production-rule **libs**, mapping, readiness, and tests, but **did not wire** the production UI into the committed `Product001IntakeSpecEditor.tsx` or `VectorIntakeFastAskPanel.tsx` (those controls existed only in local `.MIXED` separation artifacts).

This completion pass re-applied production UI from `.MIXED` reference via targeted edits (not committing `.MIXED` files):

| Area | Action |
|------|--------|
| `Product001IntakeSpecEditor.tsx` | Face vinyl toggle, locked visual chamfer, return white/black, lighting system (module/strip), LED power/density, warm/cold, PSU sizing display |
| `VectorIntakeFastAskPanel.tsx` | `vector-fast-ask-face-wrap`, `vector-fast-ask-face-colantare-type`, `vector-fast-ask-return-edge`, lighting fast-ask fields; SVG upload/drop/parse from Commit 1 preserved |
| `intakeProductSpec.ts` | Production fields on `IntakeProductSpec` |
| `intakeVolumetricSpec.ts` | Normalize/persist production fields on save |
| `backend/validators/intake_product_spec.py` | Allowlist + enum validation for production fields |

### Hotfix test results (2026-06-07)

| Check | Result |
|-------|--------|
| `npm run lint` | PASS |
| `npm run typecheck` (full repo) | FAIL — pre-existing errors unrelated to this hotfix (plus `.HEAD`/`.MIXED` backup files in `src/`); **no new errors** in hotfix source files |
| `Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | PASS (21/21) |
| Production rules suite (7 lib tests) | PASS (65 tests) |
| `VectorIntakeFastAskPanel.desktopSvgParse.test.tsx` + SVG parser tests | PASS (20 tests) |
| Backend pytest | Not run (`python` unavailable in shell) |

**Git:** Hotfix changes **not committed** (awaiting explicit request). HEAD remains `80415fd`.

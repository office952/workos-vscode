# 2026-07-16 Gradi Curat — revert no-backing attempt + restore owner truth

**Task:** `WORKOS-GRADI-CURAT-REVERT-NO-BACKING-AND-RESTORE-OWNER-TRUTH-V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD (verified):** `6e6ef5d33d540fccf61e54cd1f8bee8f508f5996`  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Runtime writes this task:** NONE

## Stopped implementation state

Owner clarified that `backing_mode` is **individual letter Forex/PVC rear closure**, not “common continuous panel”. The in-progress no-backing attempt (`backing_mode=none` = “Fără spate continuu”) was classified **CONFLATED_CONTRACT** / **MUST_REVERT** and stopped mid-flight (uncommitted WIP only).

## Scoped diff before revert (vs HEAD)

| File | Δ |
|------|---|
| `backend/services/intake_v4_backing_mode_service.py` | preserve `none`, continuous-panel labels, layer-derived resolve |
| `backend/services/intake_v4_material_breakdown_service.py` | `forex_backing_active` gate omit Forex on `none` |
| `backend/services/intake_v4_finish_truth_service.py` | `installation_template_only` mounting carve-out |
| `backend/tests/test_intake_v4_backing_mode.py` | none-omit + fixture edits |
| `backend/tests/test_intake_v6_canonical_readiness_spine.py` | template-only mounting tests |
| `frontend/src/lib/intakeV6/intakeV6BackingMode.ts` | expose `none` + effective resolve |
| `frontend/src/lib/intakeV6/intakeV4BackingMode.ts` | same |
| `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts` | `none` → no back material |
| `frontend/.../IntakeV6ReviewBackingSelect.tsx` | continuous-panel helper copy |
| `frontend/.../IntakeV6ReviewStep.tsx` | Iluminare global backing UI + cascade |
| related FE tests | none-option assertions |
| **untracked** `intakeV6BackingMode.noneContract.test.ts` | new |

Total scoped: ~265 insertions / 35 deletions across 12 tracked paths.

## Revert method

```text
git checkout HEAD -- <12 tracked paths>
Remove-Item frontend/src/lib/intakeV6/intakeV6BackingMode.noneContract.test.ts
```

No-backing attempt was **never committed**; revert = discard WIP to `6e6ef5d`.

## Files restored to HEAD

All 12 tracked paths listed above. Confirmed clean vs HEAD after checkout.

## Untracked removed

- `frontend/src/lib/intakeV6/intakeV6BackingMode.noneContract.test.ts`

## Residual check

No remaining attempt markers in restored sources:

- `Fără spate continuu`
- `resolveEffectiveIntakeV6BackingMode`
- `installation_template_only`
- `forex_backing_active`

## Tests

| Suite | Result | Notes |
|-------|--------|-------|
| FE ReviewBackingSelect + BackingAndEmblem + hydration/sync | **17/17 PASS** | `none` not exposed in options |
| BE `test_intake_v6_canonical_readiness_spine` | **10/10 PASS** | no template-only carve-out |
| BE `test_intake_v4_backing_mode` | **13 FAIL / 14 PASS** | Failures are `template_out_of_scope` for fixture `TPL-VOLUMETRIC-LETTERS` (pre-existing at HEAD vs active isolation). Not caused by residual no-backing logic. |
| Ad-hoc Forex path proof (`TPL-VOLUMETRIC-LETTERS_v2`) | **PASS** | `normalize(none)→forex_10_no_bevel`; material+CNC Forex present |

## Workspace persisted state (read-only)

| Field | Value |
|-------|-------|
| `finish_setup.backing_mode` | `forex_10_no_bevel` |
| per-layer `backing_mode` | null (all letter groups + logos) |
| `mounting_solution` | null |
| mounting gate | `MOUNTING_SOLUTION_MISSING` |
| `mounting_template_enabled` | true |
| `mounting_template_material_type` | forex *(template material, not letter back)* |
| `mounting_scope` | `preparation_and_site_installation` |
| `site_installation_included` | true |
| `illuminated` | true |
| `light_color` | `cool` |
| `face_finish_type` (global / groups) | `none` (plexiglas, no vinyl) |
| return | `white_aluminum` / 60 mm |
| logos | `print_laminate` |
| `readiness_status` | `runtime_capture_blocked` |
| `updated_at` | `2026-07-16T09:35:32.250206` |

Autosave from the aborted attempt did **not** leave `backing_mode=none` on this workspace. Global Forex individual back remains.

## Owner truth mapping

| Owner concept | Current contract field | Workspace value | Expected |
|---------------|------------------------|-----------------|----------|
| Individual letter back | `finish_setup.backing_mode` | `forex_10_no_bevel` | `forex_10_no_bevel` |
| Common continuous panel | *(no dedicated field)* | n/a | none — **modeling gap** |
| Installation template | `mounting_template_enabled` (+ area/material) | true / forex | template yes |
| Mounting support / ACM-bars | `mounting_solution` | **null** → blocker | template-only or explicit none-solution — **contract gap** |
| Installation included | `site_installation_included` | true | true |
| Illumination | `illuminated` + system | true / led_modules | FRONT_LIT equiv |
| Lighting color | `light_color` | `cool` | cool_white |

## Remaining blocker

`MOUNTING_SOLUTION_MISSING` with template enabled and empty `mounting_solution`. Do not re-add `installation_template_only` without a separate GO.

## Recommended next action

**MOUNTING_SOLUTION_CONTRACT_GAP**

Resume same workspace via UI only after a mounting contract decision: how “installation template only / no ACM-bars” is represented without abusing `backing_mode`.

## Runtime writes

NONE

## Roadmap score

7/10 — correct stop + clean discard of wrong semantic; mounting gap remains the real resume gate.

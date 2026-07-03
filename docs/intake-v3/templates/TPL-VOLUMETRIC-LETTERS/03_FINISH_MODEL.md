# TPL-VOLUMETRIC-LETTERS — Finish Model

**Contract:** `FinishAssignment`  
**Service:** `backend/services/intake_v3_finish_material_service.py`  
**Modes:** `all` | `group` | `letter_custom` (avansat, warning only)

---

## Implementat (`INTAKE_V3_FINISH_AND_MATERIAL_WORKFLOW`)

| Layer | Status |
|-------|--------|
| `validate_finish_assignment()` | ✅ blockers + warnings |
| `derive_operation_flags_from_finishes()` | ✅ |
| Face / return / backing sub-specs extinse | ✅ |
| Return wrapped vs painted ramuri distincte | ✅ |
| Face vinyl after return painting flag | ✅ |

---

## Face finish (față plexiglas)

| Variantă | Task colantare fețe |
|----------|---------------------|
| Față albă / necolantată | **nu** se generează |
| Față colantată / Oracal 8500 / folie | **da**, dacă specificat în comandă |

**Reguli:**

- `face_vinyl_roll_width_mm` **required** când face vinyl activ → `MISSING_FACE_VINYL_ROLL_WIDTH`.
- Colantare finală fețe **după asamblare**.
- Cant vopsit + față colantată → warning `FACE_VINYL_AFTER_RETURN_PAINTING`.

**Editable via field editor:** `enabled`, `finish_type`, `material`, `color_code`, `color_name`, `roll_width_mm`, `confirmed` (allowlist path aliases accepted).

**Per letter/group (local):** după confirmarea modelului, operatorul poate defini `letter_group_finish_assignments` și `letter_finish_assignments` via `PATCH .../finish-assignments`. Precedență: letter override → group → global. Holes (`C-HOLE-*`) nu sunt ținte valide.

**Variation summary (local):** `finish_variation_summary` în workspace preview agregă litere/materiale/operații per sursă — fără preț final.

---

## Return / cant finish

### A. Cant colantat (`oracal_wrapped` / `oracal_651`)

- `return_vinyl_application_required = true`
- **Înainte** de modelare cant
- `return_depth_mm` required → `MISSING_RETURN_DEPTH`

### B. Cant necolantat (`none` / `raw` / `prefinished`)

- Fără colantare cant, fără vopsire după asamblare

### C. Cant vopsit (`painted`)

- `return_painting_after_assembly_required = true`
- **Nu** înainte de modelare
- Culoare required → `MISSING_RETURN_PAINT_COLOR`
- Warning `RETURN_PAINT_REQUIRES_FACE_PROTECTION`

**Editable via field editor:** `finish_type`, `depth_mm`, `material`, `color_code`, `color_name`, `confirmed`. `finish_type=painted` dezactivează return vinyl chiar dacă material Oracal rămâne în payload.

---

## Readiness blockers (finish)

| Code | Condiție |
|------|----------|
| `MISSING_FACE_VINYL_ROLL_WIDTH` | face vinyl activ |
| `MISSING_RETURN_DEPTH` | return wrapped activ |
| `MISSING_RETURN_PAINT_COLOR` | return painted fără culoare |
| `MISSING_GROUP_FINISH_ASSIGNMENT` | group mode neconfirmat |
| `MISSING_FINISH_ASSIGNMENT` | finish neconfirmat (compat) |

---

## Legături

- MaterialIntent: [04_MATERIAL_INTENT_MODEL.md](./04_MATERIAL_INTENT_MODEL.md)
- Operation Catalog: [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md)

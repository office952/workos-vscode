# TPL-VOLUMETRIC-LETTERS — Vector and Letter Model

**Contracts:** `RawSvgAnalysis`, `RawSvgObject`, `ConfirmedProductionModel`, `LetterModel`, `CutContourModel`, `VectorModelValidationResult`

**Service:** `backend/services/intake_v3_vector_model_service.py`

---

## Separare obligatorie

| Layer | Proprietar | Conținut |
|-------|------------|----------|
| **RawSvgAnalysis** | Sistem | path_count, closed_contour_count, raw_objects, warnings, confidence |
| **ConfirmedProductionModel** | Operator | litere reale, contururi, goluri confirmate |

```text
Raw SVG:
  closed_contours = 27   (detectare automată)

Confirmed:
  real_letters    = 18   (operator)
  cut_contours    = 27   (include goluri)
  inner_holes     = 9    (nu sunt litere)
```

---

## Implementat în `INTAKE_V3_VECTOR_AND_LETTER_MODEL`

| Layer | Status |
|-------|--------|
| `RawSvgObject` — obiect detectat brut cu `raw_role_guess` | ✅ contract |
| `summarize_raw_svg_analysis()` | ✅ serviciu pur |
| `build_confirmed_production_model()` | ✅ serviciu pur |
| `validate_confirmed_production_model()` | ✅ blockers + warnings |
| Integrare readiness — vector blockers + raw mismatch warning | ✅ |
| TS types + helpers (`isConfirmedProductionModelReady`, `summarizeLetterContourCounts`) | ✅ |
| Test HUB 18/27/9 | ✅ `test_intake_v3_vector_and_letter_model.py` |

---

## Reguli

1. **Golurile nu sunt litere separate** — sunt `inner_hole` în `CutContourModel`, legate de `parent_letter_id`.
2. **Contururile CNC includ golurile** — 18 outer + 9 inner = 27 cut paths (exemplu HUB).
3. **`letter_count` nu se deduce automat** din `closed_contour_count`.
4. Readiness: `UNCONFIRMED_LETTER_MODEL` până la `confirmation_status=confirmed`.
5. **Raw vs confirmed mismatch = warning**, nu blocker, dacă modelul confirmat este coerent.
6. Blockers vector: `CUT_CONTOUR_COUNT_MISMATCH`, `INNER_HOLE_WITHOUT_PARENT_LETTER`, `LETTER_WITHOUT_OUTER_CONTOUR`, etc.

---

## HUB 18/27/9 — caz test obligatoriu

| Metric | Raw | Confirmed |
|--------|-----|-----------|
| closed_contour_count | 27 | — |
| letter_count | — | 18 |
| cut_contour_count | — | 27 |
| inner_hole_count | — | 9 |

Fixture: `build_hub_media_production_fixture()` în teste — **nu hardcodat în runtime**.

---

## Ce rămâne concept (nu în acest build)

| Item | Status |
|------|--------|
| Parser SVG complet | ❌ |
| Editor vizual / Assisted Interpretation UI | ❌ |
| Nesting real (goluri grupate cu litera-mamă) | ❌ build separat |
| CNC file generator | ❌ |
| DB persistence model confirmat | ❌ |

---

## Sursă pentru downstream

`ConfirmedProductionModel` confirmat este sursa pentru:

- finisaje (`FinishAssignment` pe grup/literă);
- `MaterialIntent` estimări;
- `PricingInput` adapter (build viitor);
- `ProductionHandoff` task seed (build viitor).

Raw analysis **nu** alimentează direct pricing sau producție.

---

## Pregătire fișiere — separare de grafică

| Operație | Skill | Output |
|----------|-------|--------|
| Verificare grafică / vectorizare | `graphic_design`, `vector_preflight` | SVG validat, layer map |
| Pregătire CNC față/spate | `cnc_file_preparation` | fișiere debitare |
| Pregătire traseu cant | `return_forming_file_preparation` | fișier modelare cant |

Aceeași persoană **poate** face CNC prep și traseu cant dacă are skill-uri — template-ul nu le fuzionează într-o singură operație.

---

## Legături

- Operation: `graphic_vector_preflight`, `confirmed_production_model` în [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md)
- Readiness: [../../../04_READINESS_AND_BLOCKERS_MODEL.md](../../../04_READINESS_AND_BLOCKERS_MODEL.md)
- QA: [../../../qa/BUILD_INTAKE_V3_VECTOR_AND_LETTER_MODEL.md](../../../qa/BUILD_INTAKE_V3_VECTOR_AND_LETTER_MODEL.md)

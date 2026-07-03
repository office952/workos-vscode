# TPL-VOLUMETRIC-LETTERS — Material Intent Model

**Contract:** `MaterialIntent`  
**Service:** `derive_material_intent()` în `intake_v3_finish_material_service.py`

---

## Principiu

```text
MaterialIntent = intenție pentru ofertare și pregătire producție.
Nu consumă stoc. Nu creează StockMovement.
```

`inventory_mutation_allowed` = **false** (hard-validat).

---

## Implementat

| Derivare | Status |
|----------|--------|
| Roll face vinyl (`source_finish=face`) | ✅ |
| Roll return vinyl (`source_finish=return`) | ✅ |
| Sheet Plexiglas (`source_component=face`) | ✅ |
| Sheet Forex backing (`source_component=backing`) | ✅ |
| LED module intent | ✅ `owner_input_required` |
| PSU intent (pack vs mount) | ✅ |
| Accessories (autoforante, stretch, protecție față) | ✅ |
| Warning `MATERIAL_ESTIMATE_ONLY` | ✅ nu blochează quote |
| Finish assignment variations note in preview | ✅ summary only — granular per-group pricing deferred |
| `finish_variation_summary` material/operation notes | ✅ local — no m²/ml per variation |

Estimări exacte mp/ml → `requires_geometry` până la nesting/build viitor.

**Field editor:** patch pe finisaje regenerează `derive_material_intent()` în preview — roll/sheet/accessory intents se actualizează; `inventory_mutation_allowed` rămâne false.

---

## Roll materials

| Câmp | Exemplu |
|------|---------|
| `source_finish` | `face` \| `return` |
| `roll_width_mm` | 1260 |
| `estimate_status` | `requires_geometry` |

---

## Sheet materials

| Câmp | Exemplu |
|------|---------|
| `source_component` | `face` \| `backing` |
| `remaining_label` | **Rest placă estimat** |
| `estimate_status` | `requires_geometry` |

---

## Power supplies (fără suport comun)

```text
packaging_required = true
mounted_on_shared_support = false
source_rule = no_shared_support_psu_at_packaging
```

Cu suport comun: `mounted_on_shared_support = true` (pending owner model).

---

## AccessoryIntent

Consumabile mici: `strict_inventory_tracking = false`.

Return painted → accessory `face_protection`.

---

## Ce rămâne

- Pricing adapter (build viitor)
- Nesting real pentru mp/ml exact
- Inventory write — **out of scope**

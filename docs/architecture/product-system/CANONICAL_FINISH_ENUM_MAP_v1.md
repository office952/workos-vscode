# Canonical Finish Enum Map v1

**Version:** 1.0.0  
**Status:** Readonly architecture contract — not runtime wiring  
**Scope:** Product System finish semantics by `surface_target` + `technical_variant`

---

## 1. Purpose

WorkOS finish semantics are **surface-separated**, not global:

- **cant** — finish applied to return/side/cant (perimeter-based)
- **face** — visible face surface treatment (Vector Litere)
- **artwork** — logo/printed artwork surface treatment (Vector Logo)

The correct lookup key is **`surface_target` + `technical_variant`**, not a single finish enum shared across components.

Product System must:

- **Not** duplicate Intake V6 color catalogs (Oracal/RAL lists live in `frontend/src/lib/colorRegistry/`)
- **Not** copy EUR/mp or EUR/ml values from Pricing Registry (key references only where applicable)
- **Not** implement generic `product.components.finish.oracal_code` / `ral_code` / `stock_color` paths

Readonly TS contract: `frontend/src/features/product-system/canonicalFinishEnumMap.ts`

---

## 2. Owner decisions source

Authoritative owner sign-off:

- [`docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md`](../../worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md)

Decisions A–E accepted (2026-07-09, Alex / P-Media).

Prior audits:

- `FINISH_vs_RETURN_CANT_BOUNDARY_DECISION_AUDIT_PLAN_V1`
- `CANONICAL_FINISH_ENUM_UNIFICATION_MAP_V1`

---

## 3. Surface targets

| Surface | Intake domain | Layer role (typical) |
|---------|---------------|----------------------|
| `cant` | `return_finish_type`, RETURN-CANT fields | return / cant per letter group |
| `face` | `face_finish_type` on letter groups | Vector Litere (`face`) |
| `artwork` | `execution_type` on artwork rows | Vector Logo (`printed_artwork`) |

---

## 4. Technical variants

| Variant | Meaning |
|---------|---------|
| `stock_color` | Operational stock color label (no extra finish rate on cant) |
| `vinyl_application` | Oracal / vinyl wrap or cut |
| `paint_application` | RAL paint |
| `print_laminate` | Print + laminare |
| `print_only` | Print without laminate |
| `commercial_minimum` | Owner commercial policy (not a registry rate) |
| `none_or_material_default` | Raw substrate / no application finish |

User-facing families (reusable across surfaces): `Culoare Stock`, `Folie autocolantă`, `Vopsit RAL` — see `REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY.md`.

---

## 5. Owner component rules

### RETURN-CANT

- Owns: `cant_stock_color`, `cant_oracal_wrap`, `cant_ral_paint`, `cant_ral_minimum_policy`
- Truth: `product.components.return_cant.*`
- Catalog: Intake V6 Color Registry (readonly cross-ref)
- Pricing: `/inventory/pricing` key refs only

### FINISH

- Owns: face vinyl, face print/laminate, artwork vinyl/print/laminate
- Truth: `product.components.finish.face.*`, `product.components.finish.artwork.instances[]`
- **Must not** own cant stock/Oracal/RAL or cant pricing keys

### FACE

- Owns: substrate, material, thickness, cut path, area/perimeter refs
- Does **not** own vinyl application (FINISH) unless owner revises decision A

---

## 6. Canonical map table

| canonical_id | surface_target | technical_variant | intake_tokens | PS label | owner_component | truth_path_prefix | catalog_source | pricing_source | material_keys | labor_keys | quantity_basis | commercial_policy_source | forbidden_owners | activation_status |
|--------------|----------------|-------------------|---------------|----------|-----------------|-------------------|----------------|----------------|---------------|------------|----------------|--------------------------|------------------|-------------------|
| cant_stock_color | cant | stock_color | white_aluminum, black_aluminum, gold_aluminum, mirror_silver, standard_aluminum | Culoare Stock | RETURN-CANT | product.components.return_cant.finish | stock_color_catalog_tbd | /inventory/pricing | MAT-PROFIL-LATERAL-LITERE-{30,60,80,100}MM | — | ml_perimeter | — | FINISH, FACE | owner_confirmed |
| cant_oracal_wrap | cant | vinyl_application | oracal_wrapped, oracal_651, vinyl | Oracal | RETURN-CANT | product.components.return_cant.finish.vinyl | intake_v6_color_registry | /inventory/pricing | MAT-ORACAL-641, MAT-ORACAL-651 | RETURN_CANT_VINYL_APPLICATION_LABOR | ml_perimeter_x_width | — | FINISH, FACE | owner_confirmed |
| cant_ral_paint | cant | paint_application | ral_paint, painted, paint | Vopsit RAL | RETURN-CANT | product.components.return_cant.finish.paint | intake_v6_color_registry | /inventory/pricing | MAT-VOPSEA-RAL-CANT-{30,60,80,100}MM | RETURN_CANT_RAL_PAINT_LABOR | ml_perimeter | — | FINISH, FACE | owner_confirmed |
| cant_ral_minimum_policy | cant | commercial_minimum | — | 100 lei pe culoare RAL | RETURN-CANT | product.components.return_cant.commercial_policy.ral_minimum | — | — | — | — | owner_policy | cpp_owner_policy | FINISH | owner_confirmed |
| face_none_or_material_default | face | none_or_material_default | none | — | FACE | product.components.finish.face | — | — | — | — | none | — | RETURN-CANT | blocked |
| face_oracal_641 | face | vinyl_application | oracal_641 | Folie autocolantă — 641 | FINISH | product.components.finish.face.vinyl | intake_v6_color_registry | /inventory/pricing | MAT-ORACAL-641 | FACE_VINYL_APPLICATION_LABOR | mp_face_area | — | RETURN-CANT | blocked |
| face_oracal_651 | face | vinyl_application | oracal_651 | Folie autocolantă — 651 | FINISH | product.components.finish.face.vinyl | intake_v6_color_registry | /inventory/pricing | MAT-ORACAL-651 | FACE_VINYL_APPLICATION_LABOR | mp_face_area | — | RETURN-CANT | blocked |
| face_oracal_8500 | face | vinyl_application | oracal_8500 | Folie autocolantă — 8500 | FINISH | product.components.finish.face.vinyl | intake_v6_color_registry | /inventory/pricing | MAT-ORACAL-8500 | FACE_VINYL_APPLICATION_LABOR | mp_face_area | — | RETURN-CANT | blocked |
| face_print_laminate | face | print_laminate | print_laminate | Print + laminare | FINISH | product.components.finish.face.print_lamination | — | /inventory/pricing | pending | pending | mp_face_area | — | RETURN-CANT | blocked |
| artwork_print_laminate | artwork | print_laminate | execution_type=print_laminate | Print + laminare (logo) | FINISH | product.components.finish.artwork.instances[].print_lamination | — | /inventory/pricing | pending | pending | mp_artwork_area | — | RETURN-CANT | blocked |
| artwork_print_only | artwork | print_only | execution_type=print_only | Print (logo) | FINISH | product.components.finish.artwork.instances[].print | — | /inventory/pricing | pending | pending | mp_artwork_area | — | RETURN-CANT | blocked |
| artwork_cut_vinyl | artwork | vinyl_application | execution_type=cut_vinyl | Colant tăiat | FINISH | product.components.finish.artwork.instances[].vinyl | intake_v6_color_registry | /inventory/pricing | pending | pending | mp_artwork_area | — | RETURN-CANT | blocked |
| artwork_translucent_vinyl | artwork | vinyl_application | execution_type=translucent_vinyl | Colant translucid | FINISH | product.components.finish.artwork.instances[].vinyl | intake_v6_color_registry | /inventory/pricing | MAT-ORACAL-8500 | pending | mp_artwork_area | — | RETURN-CANT | blocked |
| artwork_none_raw_plexi | artwork | none_or_material_default | execution_type=none_raw_plexi | Plexiglas brut | FINISH | product.components.finish.artwork.instances[].variant | — | — | — | — | none | — | RETURN-CANT | blocked |

Machine-readable source of truth: `CANONICAL_FINISH_ENUM_MAP` in `canonicalFinishEnumMap.ts`.

---

## 7. Retired conceptual paths

| Retired path | Reason | Replacement |
|--------------|--------|-------------|
| product.components.finish.oracal_code | Generic; duplicates cant Oracal | finish.face.vinyl.* · finish.artwork.instances[].vinyl.* · return_cant.finish.vinyl.* |
| product.components.finish.ral_code | Generic; duplicates cant RAL | return_cant.finish.paint.ral_code · finish.face.paint.* (future) |
| product.components.finish.stock_color | Generic; duplicates cant stock | return_cant.finish.stock_color_label · finish.face.variant |
| product.components.finish.type | Ambiguous without surface | return_cant.finish.variant · finish.face.variant · finish.artwork.instances[].variant |

Legacy code may still reference retired paths until alignment slice — **do not implement new features on them**.

---

## 8. Forbidden mappings

- FINISH **must not** own cant Oracal / RAL / stock selections or cant pricing keys
- RETURN-CANT **must not** own face print/laminate or artwork finish
- Product System **must not** duplicate Oracal/RAL catalogs
- Product System **must not** embed EUR/mp or EUR/ml registry values
- Pricing Registry **must not** store 100 lei RAL minimum
- Generic FINISH fields listed above are **deprecated conceptual paths**

---

## 9. Quantity basis rules

| Context | Quantity basis |
|---------|----------------|
| Cant stock / profile | `ml_perimeter` — profile material by depth; no extra finish rate |
| Cant Oracal | `ml_perimeter_x_width` — material mp from perimeter × cant width |
| Cant RAL paint | `ml_perimeter` |
| Face vinyl | `mp_face_area` |
| Face print/laminate | `mp_face_area` |
| Artwork finish | `mp_artwork_area` |
| RAL minimum | `owner_policy` — CPP / Product System, not registry |

---

## 10. Activation gates

| Gate | Status |
|------|--------|
| Readonly contract (this doc + TS map) | **Allowed** |
| Runtime Intake → ProductDefinition bridge | **Blocked** |
| Product Truth live write | **Blocked** |
| Pricing activation | **Blocked** |
| FINISH workshop | **Blocked** until FACE boundary workshop |
| FACE workshop | **Next allowed slice** |
| Work Intake exposure (component-first) | **Blocked** |

---

## Related files

- Owner decisions: `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md`
- TS contract: `frontend/src/features/product-system/canonicalFinishEnumMap.ts`
- Tests: `frontend/src/features/product-system/canonicalFinishEnumMap.test.ts`
- Worklog: `docs/worklog/realignment/2026-07-09_canonical_finish_enum_map_readonly_contract_v1.md`

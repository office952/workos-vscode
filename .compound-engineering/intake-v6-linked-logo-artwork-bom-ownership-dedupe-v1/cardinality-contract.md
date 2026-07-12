# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Cardinality Contract

**Version:** 1.1 (all-finish artwork ownership)  
**Accepted HEAD:** 0df2c79

---

## 1. Per-segment target (print + laminate + application active)

| Concept | Rows / segment | Canonical component | Provenance |
|---|---:|---|---|
| `print_media` | **1** | `comp_logo_finish` | `linked_module` |
| `laminate_media` | **1** | `comp_logo_finish` | `linked_module` |
| `logo_face_print` | **1** | `comp_logo_finish` | `linked_module` |
| `logo_face_laminate` | **1** | `comp_logo_finish` | `linked_module` |
| `logo_finish_application` | **1** | `comp_logo_finish` | `linked_module` |
| `logo_face_material` | **1** | `comp_logo_face` | `linked_module` |
| `logo_face_cnc_cut` | **1** | `comp_logo_face` | `linked_module` |

**Forbidden costable per segment:**

- Any artwork concept on `comp_logo_face::{segment}`
- Any artwork concept on `linked_segment::{segment}`
- Any `status=mapping_only` / `provenance=dossier` artwork row in Cost BOM

---

## 2. Two-segment workspace

| Segment | Artwork materials | Artwork operations |
|---|---:|---:|
| `logo-stanga` | 2 | 3 |
| `logo-dreapta` | 2 | 3 |
| **Total** | **4** | **6** |

**No cross-segment dedupe.**

---

## 3. Stable identity key

```text
cost_row_id = concept_kind | concept_code | segment_key | canonical_component | provenance_class
```

Examples:

- `material|print_media|logo-stanga|comp_logo_finish|linked_module_costable`
- `operation|logo_face_print|logo-dreapta|comp_logo_finish|linked_module_costable`

**Not** array index. **Not** material_code-only dedupe.

---

## 4. Partial states

| State | Artwork cardinality / segment |
|---|---|
| Finish unconfirmed / partial | **0** (existing `LINKED_SEGMENT_FINISH_PARTIAL`) |
| No binding | **0** |
| Application inactive (future gate) | 2 materials + 2 ops (no application) |

---

## 5. Before / after probe

| Metric | Before | After |
|---|---:|---:|
| `print_media` / segment | 3 | **1** |
| `laminate_media` / segment | 3 | **1** |
| `logo_face_print` / segment | 2 | **1** |
| `logo_face_laminate` / segment | 2 | **1** |
| `logo_finish_application` / segment | 2 | **1** |

**Probe:** `.compound-engineering/intake-v6-artwork-internal-rate-duplication-audit-v1/_bom_inventory_probe.py`  
**Fixture:** `tests.eic_workspace_logo_fixtures.confirmed_bindings_payload()`

---

## 6. Quantity invariants (unchanged)

- Segment artwork area via `_artwork_finish_area_for_segment` — **do not modify**
- Shared area across material + operation rows = **different cost concepts**, not duplication
- Letter geometry — **not** used for logo artwork rows

---

## 7. Rates remain disabled

35 RON/m² candidates stay unconfigured until parent rate catalog `/ce-work` after dedupe re-audit passes.

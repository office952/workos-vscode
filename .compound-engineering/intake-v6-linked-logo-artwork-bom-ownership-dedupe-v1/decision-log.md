# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Decision Log

**Phase:** PLAN COMPLETE — all 7 ownership decisions **CLOSED**  
**Accepted HEAD:** 0df2c79

---

## DEC-DEDUPE-OWNER-PRINT-MATERIAL — CLOSED

| Field | Value |
|---|---|
| **Canonical owner** | `comp_logo_finish::{segment}` / `TPL-VOLUMETRIC-LOGO-FINISH_v1` |
| Evidence | Finish component label *Print / laminare / finisaj*; pilot `logo_finish` gates artwork path; owner intent; finish child already declares `print_media` |
| Reject | Face child duplicate; dossier `mapping_only` |
| Blocks /ce-work | NO |

---

## DEC-DEDUPE-OWNER-LAMINATE-MATERIAL — CLOSED

| Field | Value |
|---|---|
| **Canonical owner** | `comp_logo_finish::{segment}` / `TPL-VOLUMETRIC-LOGO-FINISH_v1` |
| Evidence | Same as print material |
| Reject | Face child duplicate; dossier `mapping_only` |
| Blocks /ce-work | NO |

---

## DEC-DEDUPE-OWNER-PRINT-OP — CLOSED

| Field | Value |
|---|---|
| **Canonical owner** | `comp_logo_finish::{segment}` / `TPL-VOLUMETRIC-LOGO-FINISH_v1` |
| Evidence | Owner preferred direction; finish module semantic owner for print processing; operation code `logo_face_print` retained (name ≠ component owner) |
| Seed gap today | Op declared on **face** child — must **move** to finish child in bounded /ce-work (`seed_tpl_volumetric_logo_v1.py`) |
| Reject | Face child costable row; dossier `mapping_only`; `linked_segment::` |
| Blocks /ce-work | NO (seed realign is in-scope for bounded build) |

---

## DEC-DEDUPE-OWNER-LAMINATE-OP — CLOSED

| Field | Value |
|---|---|
| **Canonical owner** | `comp_logo_finish::{segment}` / `TPL-VOLUMETRIC-LOGO-FINISH_v1` |
| Evidence | Same as print op |
| Seed gap today | Op on face child — **move** to finish child in /ce-work |
| Blocks /ce-work | NO |

---

## DEC-DEDUPE-OWNER-APPLICATION-OP — CLOSED

| Field | Value |
|---|---|
| **Canonical owner** | `comp_logo_finish::{segment}` / `TPL-VOLUMETRIC-LOGO-FINISH_v1` |
| Evidence | Seed already places `logo_finish_application` on finish; workcenter `FACE_VINYL_APPLICATION_LABOR`; task `logo_print_finish` |
| Reject | dossier `mapping_only`; `linked_segment::` |
| Blocks /ce-work | NO |

---

## DEC-DEDUPE-MAPPING-ONLY — CLOSED

| Field | Value |
|---|---|
| **Allowed role** | Metadata, provenance registry, compatibility — **never costable consumption** when linked child canonical row exists |
| Rule | `if linked_module canonical row for (concept_code, segment_key): exclude mapping_only from costable projection` |
| Fallback | Do **not** promote `mapping_only` to cost truth without explicit contract |
| Producer | `product_aggregate_service.build` dossier loops (lines 172–191) |
| Blocks /ce-work | NO |

---

## DEC-DEDUPE-LAYER — CLOSED

| Field | Value |
|---|---|
| **Primary** | **Option A** — `seed_tpl_volumetric_logo_v1.py` CHILD_SPECS realign (move print/lam ops + remove face media duplicates) |
| **Secondary** | **Option B** — `product_aggregate_workspace_composition_service.py` ownership filter |
| **Tertiary** | **Option C** — `aggregate_cost_bom_adapter.py` guard (`mapping_only` + non-canonical skip) |
| **Rejected** | Option D (EIC-only); generic code dedupe |
| Blocks /ce-work | NO |

---

## Face module retained scope (non-artwork)

| Concept | Owner |
|---|---|
| `logo_face_material` | `comp_logo_face::{segment}` |
| `logo_face_cnc_cut` | `comp_logo_face::{segment}` |

Artwork concepts **must not** remain costable on `comp_logo_face::{segment}` after fix.

# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Ownership Matrix

**Accepted HEAD:** 0df2c79  
**All 7 DEC decisions:** CLOSED (finish-owned artwork model)

---

## 1. Module ownership analysis

| Concept | Candidate owner | Semantic fit | Component truth | Duplicate risk | **Recommendation** |
|---|---|---:|---:|---:|---|
| `print_media` | finish module | 5 | finish child declares | HIGH if face kept | **finish** |
| `print_media` | face module | 2 | face duplicate | HIGH | **reject** |
| `print_media` | mapping_only | 1 | dossier registry | HIGH | **reject (costable)** |
| `laminate_media` | finish module | 5 | finish child declares | HIGH if face kept | **finish** |
| `logo_face_print` | finish module | 5 | owner + pilot contract | HIGH if face kept | **finish** (seed move) |
| `logo_face_print` | face module | 3 | seed today only | HIGH | **reject after realign** |
| `logo_face_laminate` | finish module | 5 | owner + pilot | HIGH | **finish** (seed move) |
| `logo_finish_application` | finish module | 5 | seed today | LOW | **finish** |
| Face substrate | face module | 5 | `logo_face_material` | LOW | **face** |
| Face CNC | face module | 5 | `logo_face_cnc_cut` | LOW | **face** |

---

## 2. Producer inventory (mandatory rows)

| Concept | Producer | Module/template | component_ref | provenance | Costable today? | **After fix** |
|---|---|---|---|---|---:|---|
| `print_media` | face `_component_from_spec` | LOGO-FACE | `comp_logo_face::{seg}` | linked_module | YES | **NO** |
| `print_media` | finish `_component_from_spec` | LOGO-FINISH | `comp_logo_finish::{seg}` | linked_module | YES | **YES** |
| `print_media` | dossier loop | parent | `linked_segment::{seg}` | dossier/mapping_only | YES | **NO** |
| `laminate_media` | face child | LOGO-FACE | `comp_logo_face::{seg}` | linked_module | YES | **NO** |
| `laminate_media` | finish child | LOGO-FINISH | `comp_logo_finish::{seg}` | linked_module | YES | **YES** |
| `laminate_media` | dossier loop | parent | `linked_segment::{seg}` | dossier | YES | **NO** |
| `logo_face_print` | face child (today) → finish (target) | LOGO-FACE → LOGO-FINISH | face::{seg} → finish::{seg} | linked_module | YES | **YES on finish only** |
| `logo_face_print` | dossier loop | parent | `linked_segment::{seg}` | dossier | YES | **NO** |
| `logo_face_laminate` | face → finish | same | same | linked_module | YES | **YES on finish only** |
| `logo_face_laminate` | dossier loop | parent | `linked_segment::{seg}` | dossier | YES | **NO** |
| `logo_finish_application` | finish child | LOGO-FINISH | `comp_logo_finish::{seg}` | linked_module | YES | **YES** |
| `logo_finish_application` | dossier loop | parent | `linked_segment::{seg}` | dossier | YES | **NO** |

---

## 3. Canonical ownership table (selected)

| Concept | Canonical owner | Suppress always |
|---|---|---|
| `print_media` | `comp_logo_finish::{segment}` | face, mapping_only, `linked_segment::` |
| `laminate_media` | `comp_logo_finish::{segment}` | face, mapping_only, `linked_segment::` |
| `logo_face_print` | `comp_logo_finish::{segment}` | face (after seed move), mapping_only, `linked_segment::` |
| `logo_face_laminate` | `comp_logo_finish::{segment}` | face (after seed move), mapping_only, `linked_segment::` |
| `logo_finish_application` | `comp_logo_finish::{segment}` | mapping_only, `linked_segment::` |
| `logo_face_material` | `comp_logo_face::{segment}` | — |
| `logo_face_cnc_cut` | `comp_logo_face::{segment}` | — |

---

## 4. mapping_only semantics

| Use | Consumer | Required after fix | Risk |
|---|---|---|---|
| Dossier key registry | Aggregate API, cost_contract | Keep in aggregate informational | LOW |
| Costable BOM row | `aggregate_cost_bom_adapter` | **Exclude** | HIGH if unchanged |
| Fallback when no child | Not proven for logo workspace | Must not auto-promote | MED |

**Preferred safe rule (CLOSED):** canonical linked child exists → `mapping_only` non-costable.

---

## 5. Seed realign required (Option A evidence)

Finish child `operations_json` today contains **only** `logo_finish_application`.  
To close print/lam op owners on finish without re-homing at runtime:

- Remove from face child: `print_media`, `laminate_media`, `logo_face_print`, `logo_face_laminate`
- Add to finish child: `logo_face_print`, `logo_face_laminate` (sequences 1–2; application sequence 3)

Face child retains: `logo_face_material`, `logo_face_cnc_cut` only.

This is **template definition realign**, not DB schema redesign.

# ACP Internal Frame — Owner Rules Pack

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_STRUCTURAL_RESOURCE_OPTIONS_REGISTRY_V1_AND_ACP_INTERNAL_FRAME_E2E` |
| Status | **PARTIAL OWNER_CONFIRMED** — materials + frame formula + crossbar spacing confirmed; **profiles DEFERRED** |
| HEAD baseline | `10253ff5c52fec36c069bb6857de7401ebfc3949` |

**Legend:** `PROPOSED` · `OWNER_CONFIRMED` · `DEFERRED` · `GUARDED` · `NOT_APPLICABLE`

---

## Owner-confirmed product truth (2026-07-18)

| Rule | Status | Value |
|------|--------|-------|
| Oțel permis | **OWNER_CONFIRMED** | Da — `MAT-STRUCT-STEEL` / label „Oțel” |
| Aluminiu permis | **OWNER_CONFIRMED** | Da — `MAT-STRUCT-ALUMINIUM` / label „Aluminiu” |
| Internal spelling | **OWNER_CONFIRMED** | `ALUMINIUM`; legacy `aluminum` = read alias only |
| Frame dimension formula | **OWNER_CONFIRMED** | See §1.2 |
| Fit allowance (luft total) | **OWNER_CONFIRMED** | Fixed **2 mm total** (not per side) |
| Clearance min/max | **NOT_APPLICABLE** | No range; not editable clearance interval |
| Old `frame_clearance_mm` / hidden 5 mm | **GUARDED** legacy | Replaced semantically by `total_fit_allowance_mm=2`; do not treat 5 mm as authority |
| Formula vs fold count | **OWNER_CONFIRMED** | Identical for single and double fold |
| Steel max crossbar spacing | **OWNER_CONFIRMED** | **1000 mm** |
| Aluminium max crossbar spacing | **OWNER_CONFIRMED** | **750 mm** |
| Crossbar UX | **OWNER_CONFIRMED** | System suggests; operator confirms; override needs reason |
| Structural certified calc | **NOT_APPLICABLE** | WorkOS never claims certified structural calc |
| Global XOR frame vs premount | **OWNER_CONFIRMED** reject | Independent; XOR is mounting-support choice only |
| Initial ACP profile sizes | **DEFERRED** | None confirmed — Registry profiles list empty for ACP until GO |

### 1.2 Frame formula (OWNER_CONFIRMED)

```text
frame_outer_width_mm  = panel_outer_width_mm  - 2 * panel_material_thickness_mm - 2
frame_outer_height_mm = panel_outer_height_mm - 2 * panel_material_thickness_mm - 2
```

Example ACP 3 mm, panel 2000×700 → frame **1992×692** (single fold = double fold).

`total_fit_allowance_mm = 2` is the fixed mounting margin (luft total).  
It is **not** a configurable clearance min/max and **not** the old hidden 5 mm default.

### 1.3 Crossbars (OWNER_CONFIRMED)

| Material | Max spacing between stiffeners |
|----------|-------------------------------|
| Steel (`MAT-STRUCT-STEEL`) | 1000 mm |
| Aluminium (`MAT-STRUCT-ALUMINIUM`) | 750 mm |

V1: suggestion + operator confirmation + override with provenance.

### 1.4 Profiles

**No profile section is OWNER_CONFIRMED for ACP.**  
Do not approve `20×20×1.5`, `30×30×1.5`, or premount/lightbox SKUs as ACP defaults.

Registry V1 may ship with **empty** `accepted_profile_codes` / empty active profile catalog for ACP → Step 2 cannot reach complete confirmation until profiles are confirmed.

---

## Materials (catalog)

| Code | Label | Status |
|------|-------|--------|
| `MAT-STRUCT-STEEL` | Oțel | **OWNER_CONFIRMED** (technical active) |
| `MAT-STRUCT-ALUMINIUM` | Aluminiu | **OWNER_CONFIRMED** (technical active) |

---

## Naming (profiles — when later confirmed)

| Topic | Status | Value |
|-------|--------|-------|
| Format | **OWNER_CONFIRMED** (convention) | `PROFILE-SHS-{W}X{H}X{T}` / `PROFILE-RHS-…` |
| Material in code | **OWNER_CONFIRMED** | No — compatibility separate |
| Initial ACP set | **DEFERRED** | Empty |

---

## Compatibility / Product System

| Topic | Status |
|-------|--------|
| ACP accepted materials | **OWNER_CONFIRMED** STEEL + ALUMINIUM |
| ACP accepted profiles | **DEFERRED** empty |
| Premount auto-accept | **OWNER_CONFIRMED** reject |
| Pricing in technical registry | **OWNER_CONFIRMED** reject |

---

## Forbidden assumptions

- Hidden 5 mm clearance authority
- Clearance min/max UI
- Fold-dependent frame size
- Invented profile defaults
- Premount/lightbox as ACP profile authority
- `OPT-ACP-FRAME-MAT-*`
- Global XOR internal frame ↔ premount

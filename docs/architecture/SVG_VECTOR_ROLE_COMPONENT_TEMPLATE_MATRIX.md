# Matrix — SVG vector roles ↔ Component / Product Templates

Updated 2026-07-17 — Product System SVG binding contract is authority.

## Canonical geometry roles (Product System)

| Geometry role | Owner label | Notes |
|---------------|-------------|-------|
| `LETTER_VECTOR_SET` | Vector litere | Not a Product Template |
| `LOGO_VECTOR_SET` | Vector logo | Not a Product Template |
| `SUPPORT_CONTOUR` | Contur suport | Not material; not “Vector ACP” |
| `DECORATIVE_VECTOR` | Element decorativ | |
| `IGNORE` | Ignoră | |

## Runtime compatibility (Product System contract)

| Geometry role | Component Template | Product Template | Selection mode | Cardinality | Status |
|---------------|--------------------|------------------|----------------|-------------|--------|
| `LETTER_VECTOR_SET` | `TPL-VOLUMETRIC-FACE_v1` (process `FACE`) | `TPL-VOLUMETRIC-LETTERS_v2` | `LAYER_OR_GROUP` | `MULTI` | Active required |
| `LOGO_VECTOR_SET` | `TPL-VOLUMETRIC-LOGO_v1` | Letters optional / logo candidate | `LAYER_OR_GROUP` | `MULTI` | Guarded candidate |
| `SUPPORT_CONTOUR` | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Letters optional | `CLOSED_CONTOUR` | `MAX_ONE` | Available, inactive by default |
| — (no SVG) | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | Letters optional | `NONE` | — | Available, SVG not required |
| `DECORATIVE_VECTOR` | none | — | element/group | — | Not bound V1 |
| `IGNORE` | none | none | any | — | — |

## Legacy Intake Step 1 options (`LEGACY_INTAKE_SVG_ROLE_ADAPTER`)

| Optiune actuală | Cod | Maps toward (legacy) | Status |
|-----------------|-----|----------------------|--------|
| Vector Litere | `face` | Letters product recommendation | Legacy adapter — replace later |
| Vector Logo | `printed_artwork` | Logo candidate recommendation | Legacy adapter |

Do **not** extend this array with ACP / Vector ACP.

## Closed-contour roles (parallel Intake UI — unify later)

| Optiune | Cod | Should map to PS | Status |
|---------|-----|------------------|--------|
| Panou Alucobond casetat | `ALUCOBOND_CASED_PANEL` | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` + `SUPPORT_CONTOUR` | Parallel until Intake unification |
| Fundal plat / decorativ / ignore | … | inactive casing | Isolation OK |

## Stale

| Code | Status |
|------|--------|
| `TPL-BOND-CASETAT` | Legacy deprecated string-only — **not** new selection authority |

Contract: `docs/architecture/PRODUCT_SYSTEM_SVG_COMPONENT_BINDING_CONTRACT.md`

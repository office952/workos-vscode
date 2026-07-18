# ACP Face Treatment Authority Contract

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Version | `acp_face_treatment/v1` |
| GO | `GO_FIX_ACP_MIXED_FACE_AUTHORITY_AND_PERSISTENCE_FOUNDATION` |
| Live shell | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

## Authority chain

```text
SVG Analyzer → geometry measure
Operator → confirm role + component + treatment
Product System → available treatments + compatibility
FinishSetup → persist confirmed config
ProductDefinition → concrete instances
ProductAggregate / CPP / tasking → later
```

Dossier is **not** authority. `TPL-ACP-LIGHT-ROUTED` is **PARALLEL_LEGACY_COST_PATH** — not Intake V6 composition authority.

## Concept separation

| Concept | Meaning | Examples |
|---------|---------|----------|
| `geometry_role` | Geometry intent | `CUTOUT_TEXT`, `ACRYLIC_INSERT`, `SUPPORT_CONTOUR` |
| Component ownership | Which template owns geometry | Letters face vs ACM shell |
| `face_treatment_code` | Construction of face zone | `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` |
| Finish | Surface appearance | Oracal, RAL, stock |
| Material | Resource | ACM sheet, plexi |

Do **not** merge into one enum. No global `face_mode` XOR.

## Registry codes (V1 identity only)

- `FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT` — external letter/logo component
- `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` — shell-local; requires later module
- `FACE-TREATMENT-ACRYLIC-INSERT` — shell-local; requires later module
- `FACE-TREATMENT-PLAIN-DECORATIVE` — shell-local decorative

Code authority: `backend/data/product_system/acp_face_treatment_registry_v1.py`

## Shell capabilities

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` declares:

- `boxed_acp_shell`
- `local_face_treatments`

`SUPPORT_CONTOUR` remains `MAX_ONE`. Face-treatment bindings are `MULTI` on the same component template.

## Out of scope (V1)

Plexiglas/LED/PSU editors, BOM, CPP, tasking, Execution, Dossier redesign.

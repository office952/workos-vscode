# ACP Local Face Modules — Owner Gates

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_ACP_BASE_AND_LOCAL_FACE_MODULES_TECHNICAL_CONFIGURATION` |
| Mode | Contracts implemented · values remain gated |

Do **not** invent values. Implement structure; keep gates explicit.

## Gate inventory (post-implementation)

| Gate | Status | Source | Implemented | Guard |
|------|--------|--------|-------------|-------|
| Live ACP shell template | EXISTING_CANONICAL | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Yes | — |
| Face-treatment registry | EXISTING_CANONICAL | `acp_face_treatment_registry_v1` | Yes | — |
| Local module registry | OWNER_CONFIRMED (structure) | `acp_local_face_modules_v1` | Yes | — |
| Plexiglas backing thickness | OWNER_GATE_REQUIRED | Missing optical RO | Structure only | `OWNER_GATE_REQUIRED` |
| Plexiglas optical type | OWNER_GATE_REQUIRED | Missing optical RO | Structure only | `OWNER_GATE_REQUIRED` |
| Backing adhesion / overlap | OWNER_GATE_REQUIRED | No V6 catalog | Structure only | `OWNER_GATE_REQUIRED` / `MANUAL_CONFIRMATION_REQUIRED` |
| Insert thickness 10 mm | OWNER_CONFIRMED_VARIANT | Owner + legacy reference | Seeded as variant | `OWNER_REVIEW_REQUIRED`; not sole thickness |
| Insert clearance / protrusion / retention | OWNER_GATE_REQUIRED | No catalog | Structure only | `OWNER_GATE_REQUIRED` |
| LED density / layout | OWNER_GATE_REQUIRED | Missing electrical RO | Structure only | `OWNER_GATE_REQUIRED` |
| PSU sizing (ACP cavity) | OWNER_GATE_REQUIRED | Missing electrical RO | Structure only | `OWNER_GATE_REQUIRED` |
| Wiring / electrical test | OWNER_GATE_REQUIRED | — | Structure only | `OWNER_GATE_REQUIRED` |
| Service corner | EXISTING_CANONICAL | shell `service_corner` | Reused on electrical config | — |
| Applied mounting / cable passage | OWNER_GATE_REQUIRED | Interface identity only | Interface fields | `OWNER_GATE_REQUIRED` |
| LIGHT-ROUTED values | LEGACY_REFERENCE | Cost path | Not imported | `PARALLEL_LEGACY_COST_PATH` |

## Rule

Module existence does not imply readiness COMPLETE.  
Inactive modules produce zero warnings / materials / Aggregate leakage.

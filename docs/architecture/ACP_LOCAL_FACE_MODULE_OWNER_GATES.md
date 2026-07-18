# ACP Local Face Modules — Owner Gates

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_ACP_MIXED_FACE_FOUNDATION_RUNTIME_REVIEW_AND_LOCAL_MODULE_PREP` |
| Mode | Pre-build gates only — no implementation |

Do **not** invent values. Classify before coding modules.

## Gate inventory

| Topic | Item | Classification | Notes |
|-------|------|----------------|-------|
| Plexiglas backing | Allowed thicknesses | **OWNER_GATE_REQUIRED** | LIGHT-ROUTED seed mentions opal **3mm** diffuser — not V6 authority |
| Plexiglas backing | Material type (opal/clear) | **OWNER_GATE_REQUIRED** | Seed label “opal 3mm” is CostEngine reference only |
| Plexiglas backing | Mounting / adhesion method | **OWNER_GATE_REQUIRED** | Not in V6 FinishSetup |
| Plexiglas backing | Min overlap / edge rule | **OWNER_GATE_REQUIRED** | Or MANUAL_CONFIRMATION_REQUIRED |
| Plexiglas backing | LED treatment behind diffuser | **OWNER_GATE_REQUIRED** | Letters lighting ≠ ACP cavity |
| Acrylic insert | Thickness fixed 10 mm vs options | **DISCOVERABLE_FROM_REPO** (legacy seed) / **OWNER_GATE_REQUIRED** for V6 | LIGHT-ROUTED `RELIEF_PLEXI_10MM`; not confirmed for composable zones |
| Acrylic insert | Exterior protrusion | **OWNER_GATE_REQUIRED** | |
| Acrylic insert | Cutout tolerance / fit | **OWNER_GATE_REQUIRED** | |
| Acrylic insert | Retention method | **OWNER_GATE_REQUIRED** | |
| Acrylic insert | Backing + illumination mode | **OWNER_GATE_REQUIRED** | |
| Electric | LED module types | **OWNER_GATE_REQUIRED** for ACP face | Letters LED path is separate (**EXISTING_CANONICAL** for letters) |
| Electric | Density / layout rule | **OWNER_GATE_REQUIRED** | |
| Electric | PSU sizing for ACP cavity | **OWNER_GATE_REQUIRED** | Support service corner exists (**EXISTING_CANONICAL** for corner choice only) |
| Electric | Wiring / service access | Partial **EXISTING_CANONICAL** | `power_supply_service_corner` on shell |
| Electric | Electrical test step | **OWNER_GATE_REQUIRED** | |
| Applied letters on ACP | Mounting relation to shell | **OWNER_GATE_REQUIRED** | Interface identity exists; relation semantics not |
| Shell | ACM boxed live template | **EXISTING_CANONICAL** | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Authority | Face-treatment registry v1 | **EXISTING_CANONICAL** | Identity only |
| Legacy | LIGHT-ROUTED formulas | **DISCOVERABLE_FROM_REPO** | Not Intake V6 authority — do not auto-import |

## Rule

No local-module implementation GO until owner answers **OWNER_GATE_REQUIRED** rows (or explicitly accepts MANUAL_CONFIRMATION_REQUIRED defaults).

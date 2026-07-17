# Runtime validation — Intake V6 component-aware SVG assignment

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `GO_INTAKE_V6_COMPONENT_AWARE_SVG_ASSIGNMENT_AND_FINISHSETUP_DURABILITY` |
| HEAD before | `62dc7a7` |
| Verdict | `INTAKE_V6_COMPONENT_AWARE_SVG_ASSIGNMENT_COMPLETE_WITH_GUARDS` |

## FinishSetup durability

| Check | Result |
|-------|--------|
| `IntakeV4FinishSetup.svg_support_selection` | Field present — no longer dropped |
| `IntakeV4FinishSetup.svg_component_bindings` | Field present — unified SoT |
| Schema probe (model_validate + dump) | PASS |
| Sync SUPPORT_CONTOUR → `svg_support_selection` | PASS |
| Stale `TPL-BOND-CASETAT` blocked | PASS |

## Product System options

| Item | Result |
|------|--------|
| Endpoint | `GET /api/v1/product-system/template-availability` |
| Field | `svg_bindable_components` |
| Letters | `TPL-VOLUMETRIC-FACE_v1` / `LETTER_VECTOR_SET` |
| Logo | `TPL-VOLUMETRIC-LOGO_v1` / guarded |
| ACP | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / `SUPPORT_CONTOUR` / `CLOSED_CONTOUR` / max 1 |

## Dual-flow unification

| Before | After |
|--------|-------|
| Layer roles + separate Alucobond panel as parallel SoT | Assignment panel consumes PS bindables; ACP config nested under Contur suport; bindings + selection persist together |
| Hardcoded FE = authority | Marked `LEGACY_INTAKE_SVG_ROLE_ADAPTER` (layer bridge only) |

## ProductDefinition

| Field | Status |
|-------|--------|
| `svg_component_instances` | Emitted from bindings |
| `support_type=alucobond_cased` | From confirmed SUPPORT / selection |
| Typed precedence | bindings → selection → legacy |

## Guards

- Full seeded workspace click-path screenshots not captured (no seed/write GO)
- Layer role table still uses legacy two-option bridge for analysis-bundle gate
- Logo remains candidate/guarded

## Fixture

External ACP SVG unchanged (SHA `afce1e6f…`); closed-contour detection still valid.

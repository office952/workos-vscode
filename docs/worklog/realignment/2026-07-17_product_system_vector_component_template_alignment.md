# Worklog — Product System vector-component template alignment

| Field | Value |
|-------|-------|
| Task | `PRODUCT_SYSTEM_VECTOR_COMPONENT_TEMPLATE_ALIGNMENT` |
| Owner GO | `GO_PRODUCT_SYSTEM_VECTOR_COMPONENT_TEMPLATE_ALIGNMENT` |
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `bc68c1b` |
| Audit docs commit | `5fffc94` |
| Feature commit | `514896e` |
| Worklog commit | `c46a3e5` |
| Start | `PRODUCT_SYSTEM_VECTOR_COMPONENT_ALIGNMENT_IN_PROGRESS` |
| Final | `PRODUCT_SYSTEM_VECTOR_COMPONENT_ALIGNMENT_COMPLETE_WITH_GUARDS` |

## Stages

1. Consolidated audit docs (commit `5fffc94`).
2. Code-owned SVG binding contract + projector.
3. Availability read model `svg_bindable_components`.
4. Contained `TPL-BOND-CASETAT` → live ACM for new support recommendations.
5. Minimal Product System composition UI projection.
6. Tests: binding contract + composition redirect + availability SVG field.

## Runtime proof (letters)

`TPL-VOLUMETRIC-LETTERS_v2` exposes:

- Face → `LETTER_VECTOR_SET` / layer-or-group / multi / required
- Logo → `LOGO_VECTOR_SET` / guarded candidate / inactive default
- ACM → `SUPPORT_CONTOUR` / closed contour / max one / optional / inactive default
- Metal → SVG binding disabled
- No `TPL-BOND-CASETAT` in bindable list

## Boundaries held

- Intake Step 1 UI unchanged
- FinishSetup unchanged
- No schema/migration/seed
- No CPP / tasking / DXF

## Guards

- FE Product System detail shows bindable list only when API returns it (optional field)
- Broader availability tests still have pre-existing metal offerable noise (unrelated)
- FinishSetup `svg_support_selection` gap remains for next GO

## Next safe step

**Option 1 — GO INTAKE V6 COMPONENT-AWARE SVG ASSIGNMENT + DUAL-FLOW UNIFICATION**  
(or FinishSetup persistence fix as immediate sibling if owner prefers PD durability first)

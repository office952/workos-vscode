# 02 - Canonical Docs Index

## Status

- Date: 2026-07-04
- Purpose: compact source index for implementation continuation

## Authority Rules

- Current canonical docs define desired direction.
- Current runtime/code proves what exists factually now.
- Legacy docs provide context/evidence only.
- Py/seeds/registries are runtime risk surfaces, not architecture authority.
- If canonical docs conflict with old docs, canonical docs win.
- If runtime conflicts with canonical docs, mark conflict and ask owner.
- Conflict = STOP + owner review.

## Core Canonical Product/System Docs

| Document | Role |
|---|---|
| `WORKOS_SYSTEMS_ALIGNMENT_MAP.md` | Top-level system roles, E2E flow, source-of-truth boundaries. |
| `PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md` | Product Template vs Component Template vs Strategy/Profile boundary. |
| `PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md` | Future component-root/calculation readiness states; no current component quote. |
| `PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md` | Form System concrete model: roots, fields, sources, value states, truth mapping. |
| `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md` | Stable Intake V6 UI surface IDs and reconstruction ownership map from final multi-SVG audit. |
| `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md` | Real material consumption, sheet/roll nesting, selected roll width, split/panelization and material quote-readiness boundary. |
| `FORM_SYSTEM_FIELD_CONTRACT_MAP.md` | Field-level map from Intake V6 UI surfaces to Form System fields, Product Truth paths, source/state, readiness and downstream boundaries. |
| `PRODUCT_TRUTH_CONFIRMATION_POLICY.md` | Rules for promoting suggested/hydrated/fallback/partial/material/split fields into confirmed Product Truth and readiness gates. |
| `COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md` | Commercial preview vs Quote boundary for live calculation, material preview, markup/discount, Pricing Registry source states and CTAs. |
| `PRODUCT_SYSTEM_COMPONENT_PRODUCTION_OPERATIONS_CONTRACT.md` | Component-owned operation/task contract; no materialization now. |
| `VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md` | Volumetric E2E order and roadmap with downstream/later gates. |
| `INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md` | Intake V6 Product Truth boundary and source separation. |
| `VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md` | Reusable components for volumetric letters Intake V6. |
| `VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md` | Quote/order/execution readiness levels and blockers. |
| `VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md` | UI state vocabulary: suggested, confirmed, fallback/hydrated, blocked, warning. |

## Authority / Risk Docs

| Document | Role |
|---|---|
| `WORKOS_CANONICAL_DOCUMENTATION_AUTHORITY_POLICY.md` | Defines doc/code/runtime authority hierarchy and conflict rules. |
| `WORKOS_PY_SEED_REGISTRY_RUNTIME_RISK_POLICY.md` | Defines how py/seeds/registries/fixtures/tests can reactivate old models. |
| `WORKOS_PY_SEED_REGISTRY_RUNTIME_RISK_AUDIT.md` | Audit of runtime risks R1-R5 and medium follow-ups. |
| `WORKOS_RUNTIME_RISK_REMEDIATION_PLAN.md` | Owner-gated remediation order and first safe slices. |
| `WORKOS_LEFT_MENU_E2E_ROLE_MAP_AUDIT.md` | Full left menu role map including Executie, Pricing, employees, machines, collaborators. |

## QA / Runtime Baselines

| Document | Role |
|---|---|
| `INTAKE_V6_ORDER_INTEGRATION_AUDIT.md` | Read-only audit of Intake V6 -> Offer/Quote -> Order integration and guards. |
| `INTAKE_V6_CONFIRMATION_HANDOFF_COMPLETION_AUDIT.md` | Confirmare and quote/offer handoff baseline; no order/execution/stock in Confirmare. |
| `INTAKE_V6_CURRENT_UI_BASELINE.md` | Current UI shell and preservation rules: Straturi / Review / Confirmare. |

## Flow / Pricing Docs

| Document | Role |
|---|---|
| `07_OFFER_QUOTE_ORDER_FLOW.md` | Quote Snapshot V2, accept, convert-to-order, no execution plan at convert. |
| `13_ORDER_LIFECYCLE_FLOW.md` | Order lifecycle into ExecutionPlan V2 later; materialization owner-gated. |
| `WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` | Commercial price vs internal cost vs actuals separation; no client hourly pricing. |

## R1/R2 Completion Worklogs

| Document | Role |
|---|---|
| `2026-07-04_r1_r2_logo_seed_scope_guard.md` | First R1/R2 guard slice; initially PARTIAL due alias mismatch. |
| `2026-07-04_r2_active_template_scope_alias_guard.md` | PASS: closes Letters legacy alias -> Letters v2 scope mismatch. |

## Conflict Handling

When in doubt:

1. Check the current canonical docs.
2. Check current runtime/code as factual evidence.
3. Search for legacy/runtime-risk sources.
4. If conflict remains, stop and ask owner.
5. Do not implement from old docs or seed behavior alone.

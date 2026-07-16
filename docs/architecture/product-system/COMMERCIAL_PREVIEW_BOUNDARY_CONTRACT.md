# Commercial Preview Boundary Contract

## 1. Purpose

This document defines how Intake V6 may display live calculation, material preview, operation preview, consumable preview, markup, discount, totals, commercial status, commercial CTAs, and quote draft handoff.

Commercial Preview is not Quote. Calcul live is not final price. Material estimate is not material consumption ready. Pricing Registry exists separately and is the authority for pricing records and pricing configuration; Intake V6 UI must not invent parallel commercial rules.

This contract connects:

- `PRODUCT_TRUTH_CONFIRMATION_POLICY.md`;
- `FORM_SYSTEM_FIELD_CONTRACT_MAP.md`;
- `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`;
- `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md`;
- Pricing Registry / Inventory Pricing boundary.

This contract does not modify Pricing, Pricing Registry, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB schema, seed, migration, UI, or backend runtime behavior.

## 2. Scope

In scope:

- Calcul live;
- material breakdown;
- operation preview;
- consumable preview;
- markup;
- discount;
- total net/gross preview;
- quote-ready state;
- blocked/guarded state;
- logo-only not-offerable;
- material consumption readiness;
- split/panelization readiness;
- Pricing Registry boundary.

Out of scope:

- pricing formulas;
- pricing data changes;
- Pricing Registry implementation;
- Quote creation;
- Order creation;
- Execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB schema;
- seed/migration;
- nesting engine.

## 3. Pricing Registry Boundary

Pricing Registry / Inventory Pricing is the source for pricing records and pricing configuration.

Known route:

```text
http://127.0.0.1:3000/inventory/pricing
```

Read-only runtime check on 2026-07-04 confirmed the page exists and displays `Pricing Registry`, template coverage, materials, services/operations, owner-confirmed prices, and review/missing states. No pricing values were edited.

Rules:

1. Intake V6 Commercial Preview must not invent material/service prices.
2. Intake V6 Commercial Preview must not create a parallel pricing registry.
3. Intake V6 may consume pricing outputs/read models only through approved services/contracts.
4. Pricing page can exist independently and must remain the place where pricing records are managed.
5. This contract does not change pricing values or formulas.
6. If a price is missing, stale, unknown, or fallback-only, Intake V6 preview must be guarded.
7. Pricing source must be visible in commercial state: `pricing_registry`, `fallback_price`, `missing_price`, `manual_override`, `not_applicable`.

| Pricing source state | Can show preview? | Can be quote-ready? | Required guard |
| --- | --- | --- | --- |
| `pricing_registry` | Yes | Yes if Product Truth and material readiness also pass | show registry source and coverage state |
| `fallback_price` | Yes | No by default | label fallback and require owner review/override |
| `missing_price` | Yes, diagnostic only | No | missing price guard, link/operator direction to Pricing Registry |
| `manual_override` | Yes | Only if owner override policy allows it | explicit override audit and downstream visibility |
| `not_applicable` | Yes if item is non-commercial | Not applicable | state why price is not required |

## 4. Commercial State Vocabulary

| State | Meaning | UI allowed? | Quote draft allowed? | Order allowed? |
| --- | --- | --- | --- | --- |
| `commercial_hidden` | Commercial surface should not be shown | No, except diagnostic | No | No |
| `commercial_blocked` | Commercial path blocked by readiness or offerability | Guarded message only | No | No |
| `preview_partial` | Some inputs are partial, suggested, hydrated, fallback, or unconfirmed | Yes, with partial label | No | No |
| `preview_internal` | Internal estimate or reference preview | Yes, with internal label | No unless all gates pass and state changes | No |
| `preview_guarded` | Preview is shown with explicit blocker/guard reason | Yes | No | No |
| `preview_ready_for_quote_draft` | Preview values are ready to be considered for quote draft handoff | Yes | Maybe, if Confirmare gates pass | No from Intake V6 |
| `quote_ready` | Product Truth, material consumption, pricing and handoff gates pass | Yes | Yes | No from Intake V6 |
| `not_offerable` | Product/template not commercial root offerable | Guarded analysis only | No | No |
| `stale_pricing` | Pricing source exists but is stale relative to required policy | Yes, guarded | No | No |
| `missing_pricing` | Required price is missing | Yes, diagnostic | No | No |
| `owner_override_required` | Cannot proceed without explicit owner override | Yes, diagnostic | No | No |
| `owner_override_confirmed` | Owner accepted scoped exception | Yes | Only if policy allows and all other gates pass | No from Intake V6 |

Rules:

- `preview_partial` is not quote-ready.
- `preview_internal` is not quote-ready unless gates pass and the state becomes `preview_ready_for_quote_draft` or `quote_ready`.
- `preview_guarded` must show reason.
- `quote_ready` requires all gates.
- `not_offerable` blocks quote/order/execution.
- `stale_pricing` and `missing_pricing` block quote-ready.

## 5. Commercial Readiness Inputs

Commercial readiness requires:

1. Product Truth ready.
2. Material consumption ready.
3. Required material prices available from Pricing Registry.
4. Required service/operation prices available from Pricing Registry.
5. Split/panelization decisions confirmed if needed.
6. `logo_only_not_offerable=false`.
7. No row-level partials hidden by global readiness.
8. No fallback/area-only/nesting-preview values used as final.
9. Owner override explicit if any blocker is bypassed.

| Input | Required for preview? | Required for quote-ready? | Blocks what? |
| --- | --- | --- | --- |
| `product_truth_ready` | No | Yes | quote draft, commercial ready |
| `material_consumption_ready` | No | Yes for material-bearing products | commercial ready, quote draft |
| `pricing_registry_ready` | No | Yes for priced lines | quote-ready totals |
| `split_confirmed` | No | Yes when split required | material ready, commercial ready |
| `logo_only_not_offerable` | Yes as guard | Must be false | quote/order/execution |
| `row_level_partials_clear` | No | Yes | Product Truth and commercial ready |
| `owner_override_confirmed` | No | Only for scoped exception | may unblock scoped blocker only |

## 6. Calcul Live Boundary

Calcul live can be shown only with correct label based on state.

Rules:

- If Product Truth is partial, label as `Preview partial`, not final offer.
- If material consumption is area-only, label as `Estimare materiale`, not final consumption.
- If nesting is preview-only, label as `Nesting preview`, not final material consumption.
- If pricing is missing/stale, block quote-ready and show pricing guard.
- If logo-only, hide or block commercial surface with not-offerable reason.
- Calcul live must not create impression of final quote unless `quote_ready=true`.

Required UI copy concepts:

- `Preview intern`;
- `Preview partial`;
- `Materiale neconfirmate`;
- `Consum material neconfirmat`;
- `Preturi lipsa sau neverificate`;
- `Neofertabil comercial`;
- `Gata pentru draft oferta` only when gates pass.

## 7. Material Breakdown Boundary

This section uses `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`.

Rules:

- Geometry area can be shown as a technical value.
- Geometry area cannot be final material consumption.
- Rigid sheet consumption requires nesting result or owner override.
- Roll consumption requires selected roll width x roll length used.
- Narrow graphic still consumes selected roll width.
- Split proposed/unconfirmed blocks quote-ready.
- Each material line can show preview but must identify quantity source, quantity state, price source, price state, and quote-ready flag.

| Quantity state | Price state | Can show line? | Can affect quote-ready total? | Guard |
| --- | --- | --- | --- | --- |
| `estimate_area_only` | `pricing_registry` | Yes | No | area-only quantity guard |
| `nesting_preview` | `pricing_registry` | Yes | No | nesting preview guard |
| `computed_unconfirmed` | `pricing_registry` | Yes | No | confirmation required |
| `confirmed` | `pricing_registry` | Yes | Yes if all gates pass | source visible |
| `confirmed` | `missing_price` | Yes | No | missing price guard |
| `confirmed` | `fallback_price` | Yes | No by default | fallback price guard / owner override |
| `confirmed` | `manual_override` | Yes | Only if override confirmed | override audit guard |

## 8. Markup / Discount Boundary

Rules:

- Markup/discount can be visible only when commercial preview is allowed.
- Markup/discount cannot turn partial Product Truth into quote-ready.
- Markup/discount cannot bypass material consumption readiness.
- Markup/discount cannot bypass missing or stale pricing.
- For logo-only not-offerable, markup/discount must be hidden or disabled.
- Any owner override must be explicit and audited.

| Commercial state | Markup allowed? | Discount allowed? | Notes |
| --- | --- | --- | --- |
| `commercial_hidden` | No | No | no commercial surface |
| `commercial_blocked` | No | No | show blocker reason |
| `preview_partial` | Yes, as preview inputs | Yes, as preview inputs | cannot unlock quote-ready |
| `preview_internal` | Yes, as internal preview | Yes, as internal preview | no final offer implication |
| `preview_guarded` | Conditional | Conditional | guard must stay visible |
| `preview_ready_for_quote_draft` | Yes | Yes | still requires Confirmare gates |
| `quote_ready` | Yes | Yes | can feed quote draft if handoff gates pass |
| `not_offerable` | No | No | logo-only/root not offerable |
| `missing_pricing` | Yes only as diagnostic | Yes only as diagnostic | missing price blocks quote-ready |

## 9. Logo-only Commercial Boundary

Rules:

- `TPL-VOLUMETRIC-LOGO_v1` as logo-only candidate remains candidate/read-only.
- Logo-only can reach Review/Confirmare as safe analysis.
- Logo-only cannot show final offer surface.
- Logo-only cannot enable quote draft/order/execution.
- Logo-only may show technical/material analysis only as not-offerable guarded preview.
- Pricing Registry availability does not make logo-only offerable.

## 10. Confirmare Commercial Gate

Fields:

- `iv6.s3.gates.product_truth_ready`
- `iv6.s3.gates.material_consumption_ready`
- `iv6.s3.gates.commercial_ready`
- `iv6.s3.gates.logo_only_not_offerable`
- `iv6.s3.handoff.quote_draft_allowed`
- `iv6.s3.boundary.no_order`
- `iv6.s3.boundary.no_execution`

Rules:

- Confirmare can be reachable as safe review.
- `commercial_ready=false` if Product Truth is partial.
- `commercial_ready=false` if material consumption is partial.
- `commercial_ready=false` if pricing is missing or stale.
- `quote_draft_allowed` requires `commercial_ready=true`.
- `logo_only_not_offerable=true` blocks `quote_draft_allowed`.
- `no_order` and `no_execution` remain true from Intake V6.

## 11. Commercial Readiness Matrix

| Product Truth | Material Consumption | Pricing Registry | Split | Logo-only | Commercial state | Quote draft allowed |
| --- | --- | --- | --- | --- | --- | --- |
| partial | any | any | any | false | `preview_partial` | no |
| ready | partial | ready | not required | false | `preview_guarded` | no |
| ready | ready | missing | confirmed/not required | false | `missing_pricing` | no |
| ready | ready | stale | confirmed/not required | false | `stale_pricing` | no |
| ready | ready | ready | proposed | false | `preview_guarded` | no |
| ready | ready | ready | confirmed/not required | false | `quote_ready` | yes, if Confirmare gates pass |
| any | any | any | any | true | `not_offerable` | no |
| ready | owner override confirmed | owner override confirmed | owner override confirmed | false | `owner_override_confirmed` | yes only if override policy allows and handoff gates pass |

## 12. Owner Override Boundary

Rules:

- Owner override can allow guarded quote draft only where allowed by Product Truth Confirmation Policy.
- Owner override cannot make logo-only root offerable unless separate owner GO changes product commercial policy.
- Owner override cannot create order/execution from Intake V6.
- Owner override must record override id, field/gate id, reason, old state, new state, owner user id, timestamp, downstream visibility, and expiry/recheck condition.

Required owner override fields:

- `override_id`;
- `field_id` / `gate_id`;
- `reason`;
- `old_state`;
- `new_state`;
- `owner_user_id`;
- `timestamp`;
- `downstream_visible`;
- `expires_or_requires_recheck`.

## 13. Relationship To Quote / Order / Execution

Rules:

- Intake V6 Commercial Preview is not Quote.
- Quote Draft is a separate downstream handoff.
- Order is not created from Intake V6.
- Execution is not created from Intake V6.
- Commercial preview output must be snapshot-safe before quote handoff.
- Quote/Order/Execution changes are forbidden by this contract.

## 14. Current Status And Gaps

- Product Truth Confirmation Policy exists but is docs-only.
- Form System Field Contract Map exists but is docs-only.
- Material Consumption Contract exists but is docs-only.
- Pricing Registry page exists at `/inventory/pricing`; boundary to Intake V6 needs runtime audit later.
- Commercial readiness is not yet runtime-enforced by this contract.
- Calcul live may still be stronger visually than its readiness state.
- Intake V6 commercial preview currently consumes/reflects pricing and material preview surfaces, but this contract does not change those implementations.

## 15. Required Next Slice

Recommended next slice:

```text
COMMERCIAL_PREVIEW_RUNTIME_AUDIT_V1
```

Reason:

Before changing UI/backend, audit current runtime behavior against this contract:

- Intake V6 commercial surfaces;
- Pricing Registry availability;
- readiness states;
- logo-only guard;
- material/nesting partial guards;
- Confirmare CTAs.

Do not implement runtime changes in this task.
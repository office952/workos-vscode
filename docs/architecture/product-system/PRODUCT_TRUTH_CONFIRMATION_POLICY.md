# Product Truth Confirmation Policy

## 1. Purpose

This document defines how Intake V6 / Form System fields become confirmed Product Truth and how partial fields block commercial and downstream readiness.

Product Truth is not the same thing as an SVG Analyzer suggestion. Product Truth is not the same thing as a UI preview. Product Truth is not the same thing as a hydrated, fallback, or area-only estimate. Product Truth is the confirmed runtime truth that can support commercial readiness, ProductDefinition consumption, and downstream handoff boundaries.

This policy connects:

- `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md`;
- `FORM_SYSTEM_FIELD_CONTRACT_MAP.md`;
- `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`;
- `INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`.

Commercial readiness display and CTA boundaries are specified by:

- `COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`.

This policy does not implement UI, Form System runtime generation, backend changes, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB schema, seed, or migration behavior.

## 2. Scope

In scope:

- Pas 1 layer roles;
- Vector Litere;
- Vector Atipic / logo;
- logo-only candidate;
- lighting;
- mounting;
- material consumption;
- nesting;
- roll width;
- split/panelization;
- commercial preview;
- Confirmare gates;
- owner override.

Out of scope:

- UI implementation;
- backend implementation;
- Pricing formula changes;
- quote/order creation;
- execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB migration;
- seed data;
- nesting engine implementation.

## 3. Confirmation Vocabulary

| State | Meaning | Can be Product Truth? | Can allow preview? | Can allow quote draft? |
| --- | --- | --- | --- | --- |
| `suggested` | Proposed by analyzer, registry mapping, or contract hint | No | Yes, with suggested label | No |
| `hydrated` | Reused from payload/prior state | No, unless operator confirms or explicit confirmation policy accepts it | Yes, with hydrated label | No by default |
| `fallback` | Default value chosen by UI/service | No | Yes, with fallback label | No by default |
| `partial` | Enough to display/preview but not complete truth | No | Yes, with partial label | No |
| `confirmed` | Explicitly operator-confirmed or accepted by a documented confirmation rule | Yes | Yes | Yes if all other gates pass |
| `blocked` | Cannot progress until resolved | No | Limited diagnostic preview only | No |
| `candidate_read_only` | Visible candidate, not active as root truth | No as commercial root | Yes | No as root |
| `not_offerable` | Explicitly blocked from commercial root behavior | No | Safe review only | No |
| `estimate_area_only` | Geometry/area estimate without real consumption | No | Yes, preview only | No |
| `nesting_preview` | Visual/comparative nesting output | No by itself | Yes, preview only | No |
| `computed` | Computed by an approved source | Maybe, only with owner/source/path/validation and confirmation | Yes | Only after confirmation/readiness |
| `split_proposed` | Split/panelization suggested but not accepted | No | Yes, diagnostic only | No |
| `split_confirmed` | Split accepted by operator and panels fit format | Yes for split truth | Yes | Yes if material readiness passes |
| `split_rejected` | Operator rejected split | No | Diagnostic only | No if no alternate format exists |
| `override_required` | Cannot continue without explicit owner override | No | Diagnostic only | No |
| `owner_override_confirmed` | Owner accepted an exception with audit trail | Yes, only for the scoped exception | Yes | Yes only if downstream-visible and allowed by this policy |

Rules:

- `suggested` is never Product Truth confirmed.
- `hydrated` is not Product Truth confirmed without operator confirmation or an explicit documented confirmation rule.
- `fallback` is not Product Truth confirmed.
- `estimate_area_only` is preview only.
- `nesting_preview` is preview only.
- `computed` can become Product Truth only if source, owner, Product Truth path, validation and confirmation are present.
- `split_proposed` is not quote-ready.
- `split_confirmed` may become quote-ready if material consumption is ready.
- `not_offerable` blocks quote/order/execution.
- `owner_override_confirmed` can bypass some blockers only if explicitly audited and downstream-visible.

## 4. Confirmation Levels

| Level | Required inputs | Who confirms | Output | Can block |
| --- | --- | --- | --- | --- |
| Field-level confirmation | field id, value, source, state, owner, validation | operator or documented policy | field ready/partial/blocked | row, section, commercial, downstream |
| Row-level confirmation | all required fields in row | operator or row policy | row readiness | section, Product Truth |
| Section-level confirmation | all required rows/components, accepted exceptions | operator or section policy | section readiness | Product Truth, commercial |
| Product Truth snapshot confirmation | all required sections and paths | Product Truth policy + operator boundary | product truth ready | commercial and downstream |
| Commercial readiness confirmation | Product Truth ready, material consumption ready, commercial coverage | backend readiness + operator handoff | commercial ready | quote draft |
| Downstream handoff readiness | commercial ready and no forbidden status | backend policy + explicit operator confirmation | draft/quote handoff allowed | quote/order/execution |

Rules:

- Field-level partial must propagate upward.
- Row-level partial must not be hidden by section/global readiness.
- Section-level ready requires all required rows ready or explicit accepted exception.
- Commercial ready requires Product Truth ready + material consumption ready.
- Downstream ready requires commercial ready + no forbidden status.

## 5. Pas 1 / Layer Role Confirmation Policy

Fields:

- `iv6.s1.layer.auto_role`
- `iv6.s1.layer.confirmed_role`
- `iv6.s1.layer.confirmation_state`
- `iv6.s1.template.candidate_code`
- `iv6.s1.template.root_offerable`
- `iv6.s1.gate.roles_complete`

Rules:

- SVG Analyzer may suggest a role.
- `auto_role` is `suggested`, not Product Truth.
- Operator must confirm relevant roles or explicitly ignore irrelevant layers.
- `confirmed_role` with `confirmation_state=confirmed` becomes Product Truth input.
- Role-complete gate can allow Review, but it does not mean quote-ready.
- Template candidate is not commercial root unless `root_offerable=true` by owner-approved Product System policy.
- `root_offerable=false` blocks commercial root handoff.
- Logo candidate can continue Review/Confirmare safe, but remains not offerable.

## 6. Vector Litere Confirmation Policy

Fields:

- `iv6.s2.letter_group.face.material`
- `iv6.s2.letter_group.face.color_code`
- `iv6.s2.letter_group.face.source`
- `iv6.s2.letter_group.face.state`
- `iv6.s2.letter_group.cant.material`
- `iv6.s2.letter_group.cant.depth_mm`
- `iv6.s2.letter_group.cant.source`
- `iv6.s2.letter_group.cant.state`
- `iv6.s2.letter_group.readiness_status`

Rules:

- Nearest Oracal color from analyzer is `suggested` / `partial` until operator-confirmed.
- Face material must be operator-confirmed or explicitly confirmed by a documented default policy.
- Cant material/depth hydrated from prior state is `partial` until confirmed.
- Row readiness `partial` blocks Product Truth row ready.
- All required letter rows must be ready for Vector Litere section ready.
- Commercial preview may show a partial estimate, but quote readiness must be guarded.
- Stale row/source mismatch blocks row readiness until resolved.

## 7. Vector Atipic / Logo Candidate Confirmation Policy

Fields:

- `iv6.s2.artwork.role`
- `iv6.s2.logo_candidate.template_code`
- `iv6.s2.logo_candidate.root_offerable`
- `iv6.s2.logo_candidate.read_only`
- `iv6.s2.logo_candidate.not_offerable_reason`
- `iv6.s2.linked_segment.binding_state`
- `iv6.s2.linked_segment.readiness_status`

Rules:

- `TPL-VOLUMETRIC-LOGO_v1` is candidate/read-only unless owner GO changes commercial policy.
- Linked logo binding state `suggested` is `partial`.
- Confirmed artwork role is not the same as confirmed linked template binding.
- Logo-only candidate can pass Review/Confirmare as safe analysis.
- Logo-only candidate cannot become quote/order/execution ready.
- Linked child Logo inside Letters can contribute to Product Truth only when binding is confirmed and required fields are ready.

## 8. Lighting and Mounting Confirmation Policy

Fields:

- `iv6.s2.lighting.mode`
- `iv6.s2.lighting.led_strategy`
- `iv6.s2.lighting.source`
- `iv6.s2.lighting.state`
- `iv6.s2.mounting.type`
- `iv6.s2.mounting.support`
- `iv6.s2.mounting.source`
- `iv6.s2.mounting.state`

Rules:

- Hydrated/default/manual values are `partial` until confirmed.
- Lighting mode affects material, electrical, task, and downstream readiness.
- Mounting affects downstream execution preparation and may affect quote readiness depending on active template requirements.
- Missing required lighting/mounting data must warn or block depending on template requirements.
- Support/mounting fallback must remain visible as fallback until accepted by operator or policy.

## 9. Material Consumption Confirmation Policy

This section uses `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`.

Rigid sheet fields:

- `iv6.s2.material.rigid.material_code`
- `iv6.s2.material.rigid.sheet_width_mm`
- `iv6.s2.material.rigid.sheet_height_mm`
- `iv6.s2.material.rigid.sheet_count`
- `iv6.s2.material.rigid.geometry_area_mm2`
- `iv6.s2.material.rigid.nested_consumption_area_mm2`
- `iv6.s2.material.rigid.waste_area_mm2`
- `iv6.s2.material.rigid.efficiency_percent`
- `iv6.s2.material.rigid.nesting_status`
- `iv6.s2.material.rigid.material_consumption_ready`

Roll fields:

- `iv6.s2.material.roll.material_code`
- `iv6.s2.material.roll.selected_width_mm`
- `iv6.s2.material.roll.usable_width_mm`
- `iv6.s2.material.roll.left_margin_mm`
- `iv6.s2.material.roll.right_margin_mm`
- `iv6.s2.material.roll.length_used_mm`
- `iv6.s2.material.roll.width_consumption_area_mm2`
- `iv6.s2.material.roll.geometry_area_mm2`
- `iv6.s2.material.roll.waste_area_mm2`
- `iv6.s2.material.roll.efficiency_percent`
- `iv6.s2.material.roll.nesting_status`
- `iv6.s2.material.roll.material_consumption_ready`

Rules:

- Area-only estimate is never material consumption confirmed.
- Visual nesting preview is not material consumption confirmed.
- Rigid sheet material needs sheet format and nesting result or explicit owner override.
- Roll material needs selected roll width and roll length used.
- Roll consumption uses selected roll width x length used.
- Usable width is fit validation only.
- Narrow graphic still consumes selected roll width.
- No gang nesting is assumed.
- `material_consumption_ready=false` blocks commercial quote-ready.

## 10. Split / Panelization Confirmation Policy

Fields:

- `iv6.s2.material.split.oversized_for_material_format`
- `iv6.s2.material.split.required`
- `iv6.s2.material.split.status`
- `iv6.s2.material.split.plan_id`
- `iv6.s2.material.split.panel_count`
- `iv6.s2.material.split.operator_confirmed`
- `iv6.s2.material.split.customer_approval_required`

Rules:

- Split is only allowed/required when graphic/part does not fit selected format.
- `split_proposed` is not quote-ready.
- `split_confirmed` may allow material consumption ready if all panels fit and other material fields are ready.
- `split_rejected` blocks readiness if no alternate material format exists.
- Split must be visible in Product Truth.
- Split cannot be hidden inside Pricing.
- `customer_approval_required` must propagate as warning/blocker based on policy.

## 11. Commercial Preview Confirmation Policy

Fields:

- `iv6.s2.commercial.preview_total`
- `iv6.s2.commercial.material_estimate_state`
- `iv6.s2.commercial.material_consumption_ready`
- `iv6.s2.commercial.markup_percent`
- `iv6.s2.commercial.discount_percent`
- `iv6.s2.commercial.quote_ready`
- `iv6.s2.commercial.guard_reason`

Rules:

- Preview can exist for operator awareness.
- Preview must be labeled partial when Product Truth is partial.
- `quote_ready` requires Product Truth ready, material consumption ready, no logo-only not-offerable state, no split proposed/unconfirmed, and no area-only required material quantity.
- Markup/discount cannot turn partial Product Truth into quote-ready.
- Commercial surface for logo-only remains blocked/not offerable.

## 12. Pas 3 / Confirmare Gate Policy

Fields:

- `iv6.s3.summary.template_code`
- `iv6.s3.gates.product_truth_ready`
- `iv6.s3.gates.material_consumption_ready`
- `iv6.s3.gates.commercial_ready`
- `iv6.s3.gates.logo_only_not_offerable`
- `iv6.s3.handoff.quote_draft_allowed`
- `iv6.s3.boundary.no_order`
- `iv6.s3.boundary.no_execution`

Rules:

- Confirmare can be reached for safe review, but handoff may remain blocked.
- Global ready must not hide row-level partial readiness.
- `product_truth_ready=false` blocks `quote_draft_allowed`.
- `material_consumption_ready=false` blocks `commercial_ready`.
- `logo_only_not_offerable=true` blocks `quote_draft_allowed`.
- Intake V6 cannot create Order or Execution directly.
- `no_order` and `no_execution` remain true.

## 13. Owner Override Policy

Owner override is an explicit, audited exception to normal readiness. It is not a default path and cannot silently promote preview/fallback values.

Allowed use:

- material format exception;
- area-only temporary quote estimate;
- split rejected but alternate commercial decision accepted;
- missing non-critical field accepted by owner.

Not allowed:

- bypass logo-only not-offerable into Order/Execution;
- bypass `no_order` or `no_execution` boundaries;
- silently promote fallback/preview to confirmed;
- hide row-level partial states.

Owner override fields:

- `override_id`;
- `field_id`;
- `reason`;
- `owner_user_id`;
- `timestamp`;
- `old_state`;
- `new_state`;
- `downstream_visible`;
- `expires_or_requires_recheck`.

Rules:

- override must be explicit;
- override must be audited;
- override must be downstream-visible;
- override cannot be default behavior.

## 14. Readiness Aggregation Matrix

| Input state | Field ready | Row ready | Section ready | Product Truth ready | Commercial ready | Quote draft allowed |
| --- | --- | --- | --- | --- | --- | --- |
| `suggested` | no | no | no | no | no | no |
| `hydrated` | no by default | no by default | no by default | no | no | no |
| `fallback` | no by default | no by default | no by default | no | no | no |
| `confirmed` | yes | yes if all required fields ready | yes if all rows ready | yes if all sections ready | yes if material and commercial gates pass | yes if handoff gates pass |
| `estimate_area_only` | no | no | no | no | no | no |
| `nesting_preview` | no | no | no | no | no | no |
| `computed` unconfirmed | no | no | no | no | no | no |
| `split_proposed` | no | no | no | no | no | no |
| `split_confirmed` | yes for split field | yes if all material fields ready | yes if material section ready | yes if all sections ready | yes if commercial gates pass | yes if handoff gates pass |
| `not_offerable` | no for commercial root | no for commercial row | no for commercial section | no as quoteable root | no | no |
| `owner_override_confirmed` | yes for scoped exception | yes if override covers row blockers | yes if override covers section blockers | yes only with downstream-visible audit | yes only when allowed by policy | yes only when handoff gates pass |

## 15. Multi-SVG Policy Matrix

| File | Product Truth policy | Commercial policy | Downstream policy |
| --- | --- | --- | --- |
| `gradi-curat.svg` | Gradi semantic pseudo groups are allowed for this fixture family; letter rows and linked logo segments still need row/segment readiness confirmation | Letters preview may show, but Product Truth/material readiness must govern quote readiness | Draft/quote gated; no order/execution from Intake V6 |
| `litere-vol-1-layer.svg` | Generic fill row is a valid letter candidate; must not inherit gradi semantic labels | Preview may show as Letters, but generic fill Product Truth needs confirmation | Draft/quote gated; no order/execution from Intake V6 |
| `litere-vol-2-layere.svg` | Two generic fill rows are valid letter candidates; must not inherit gradi semantic labels | Preview may show as Letters, but generic fill Product Truth needs confirmation | Draft/quote gated; no order/execution from Intake V6 |
| `logo.svg` | Logo-only candidate/read-only; no Vector Litere Product Truth | Commercial quote readiness blocked by `logo_only_candidate_not_offerable` | Draft/quote/order/execution blocked |

Rules:

- Gradi special semantics are allowed only for the known file family.
- Litere1/litere2 generic fill rows must not inherit gradi semantics.
- Logo-only remains safe review/not offerable.
- Commercial preview for Letters still requires Product Truth/material readiness.

## 16. Current Status and Gaps

Already systemic:

- layer role confirmation;
- `logo_only_candidate_not_offerable` readiness;
- letter group readiness endpoint;
- linked template segment readiness endpoint;
- Form System Field Contract exists as docs;
- Form System Backbone read-only diagnostic exists;
- no-order/no-execution boundary exists.

Partial:

- row-level readiness is not fully surfaced in main UI;
- linked logo binding remains suggested;
- material/nesting fields are docs-only;
- commercial readiness enforcement is still later;
- Confirmare does not fully aggregate row/material readiness.

UI-only / hydrated / fallback:

- Review tab state;
- lighting/mounting/support defaults;
- material preview/nesting preview;
- commercial inputs before final Product Truth.

Missing:

- runtime enforcement of this confirmation policy;
- runtime Product Truth snapshot;
- material consumption readiness service;
- owner override persistence/audit object;
- Commercial Preview Boundary implementation.

## 17. Required Next Slice

Recommended next slice:

```text
COMMERCIAL_PREVIEW_BOUNDARY_V1
```

Reason:

After confirmation policy, commercial preview must be aligned with confirmed Product Truth and material consumption readiness.

Do not start direct Pricing implementation yet. Do not implement Commercial Boundary in this task.
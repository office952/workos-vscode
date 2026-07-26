# Montaj Domain Ownership

**Evidence date:** 2026-07-19  
**Visual candidate:** `5336734`  
**Primary runtime workspace:** `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` (`IV6-EA145E74`)

## What “Montaj” means in Intake V6

Montaj is **not one domain**. The Page 2 tab currently packages at least three authorities under one label:

1. **Physical product support / shell** — Fundal și carcasă, ACM/ACP panel, SVG support selection, segmented background, per-panel 220V.
2. **Commercial mounting offer** — `mounting_scope`, site installation, mounting template (Forex/paper), installation_template solution.
3. **Product-system mounting aids** — metal premount structure, ACM boxed mounting template as `mounting_solution`, fixing system.

UI copy on Montaj (runtime probe): *„Fundal și carcasă primul · montaj comercial doar dacă e în ofertă”* — correctly states the split, but the tab still mixes both.

---

## Category map (Part B)

| Element | Category | Owner proof |
|---------|----------|-------------|
| Fundal și carcasă cluster | **1 Physical product support** (+ **6 Segmented**) | UI label „Componentă de produs — independentă de scope-ul comercial”; PD `svg_support_selection` / ACM config |
| ACM/ACP dimensions, folds, thickness, return, rear lip, V-groove | **1 Physical product support** | `mounting_solution.configuration.*` + SVG geometry |
| Internal frame | **2 Product assembly** | nested `internal_frame` under ACM config; PD projection |
| `mounting_scope` | **3 Commercial preparation** / **4 Site installation** | `mountingScope.ts`; PD `commercial_mounting_scope`; CPP `_sablon_enabled` / site install |
| `site_installation_included` | **4 Site installation** | only when scope = preparation_and_site_installation |
| `mounting_template_*` | **7 Template / mounting aid** (commercial) | gated by prep-active scope in CPP |
| Metal premount solution | **2 Product assembly** / **7 Template aid** | `TPL-METAL-PREMOUNT-STRUCTURE_v1` |
| ACM boxed `mounting_solution` | **1 Physical product support** (also sells as support product) | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`; decoupled from scope in `c0a3404` |
| `mains_cable_length_m` | **5 Electrical connection** (product/process) | process resolver input; material consumable |
| `power_supply_service_corner` | **5 Electrical** / **8 Service** | process resolver requires for alucobond_cased; multi-source |
| `mounting_fixing_system` | **2 Product assembly** / site fixing | separate from commercial scope in PD |
| Segmented panels/joints/bindings | **6 Segmented background** | `acm_segmented_background_service`; PD only when CONFIRMED |
| Per-panel 220V | **5 Electrical** nested in **6** | `acm_segmented_electrical_service`; unpriced |
| Applied component interface | **1 Physical** interface-only | docs `ACP_APPLIED_COMPONENT_INTERFACE.md`; no price/tasks |
| Advanced fixing / legacy mounting display | **9 Technical diagnostic** + legacy | Advanced cluster; legacy `mounting_system` |
| Accesorii montaj 5% line | **3 Commercial** consumable estimate (not a Montaj field) | always-on material breakdown formula |
| Left-nav „Product System” | **10 Unknown / nav chrome** | not Montaj field; pollutes probe for Product System language |

---

## Owner answers (Part C condensed)

| # | Question | Answer |
|---|----------|--------|
| 1 | What is Montaj? | Mixed tab: product shell + commercial mounting + aids |
| 2 | Physical product decisions | SVG support, ACM dims/folds/frame, segmented assembly, applied interface |
| 3 | Commercial-only | `mounting_scope`, site install flag, mounting template area/material when prep active |
| 4 | Execution, not Intake | Real task materialization, shop-floor mounting tasks — Intake only previews |
| 5 | Fundal și carcasă = Montaj? | **Product structure**, housed under Montaj tab for UX |
| 6 | ACM support | **Product composition / support component**, not commercial mounting scope |
| 7 | `mounting_scope` commercial only? | **Yes** (canonical V1) |
| 8 | `mounting_solution` | **Both**: product_system_template (physical) OR installation_template (commercial template fields) |
| 9 | Mains cable length | Typed FinishSetup → process/material; required when illumination/process path needs it |
| 10 | Service corner | Multi-source: typed FinishSetup, ACM config, svg_support_selection; process resolver blocks alucobond without it |
| 11 | Mounting template | Commercial prep when scope prep-active |
| 12 | Support structure | Metal premount / ACM solution / svg_support — product |
| 13 | Segmented background | Product shell; PD/Aggregate only CONFIRMED; unpriced |
| 14 | Per-panel electrical | Nested segmented; unpriced; authoritative when segmented CONFIRMED |
| 15 | Required for pricing | Scope+template for sablon lines; site for `montaj` line; ACM has own commercial path; Accesorii 5% always when manufacturing subtotal > 0 |
| 16 | Required for production | Confirmed support geometry, process corner/cable as resolver requires, segmented CONFIRMED if used |
| 17 | Conditional fields | Template/site/cable/corner/electrical depend on scope/ACM/segmented/illumination |
| 18 | Appear when irrelevant? | Template enabled with `mounting_scope=none` on ACM runtime workspace — **yes, contradiction** |
| 19 | Inferred vs confirmed | SVG dims inferred then confirmed; scope hydrate may infer preparation_only from template signals if scope empty; here scope explicitly `none` while template true |
| 20 | Silent defaults | Metal/ACM config defaults in `mountingSolution.ts`; site_installation_included defaults true when scope is site |

---

## Critical ownership verdict

**Physical product and commercial mounting are partially separated in code/docs, but not cleanly in operator first paint or in graph activation.**

Proof: PD composition `blockers: ["MOUNTING_SCOPE_INACTIVE"]` while `frozen_mounting_solution` still holds ACM template and UI shows full Fundal/carcasă editor.

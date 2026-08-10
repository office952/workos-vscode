# OPERATOR_INPUT_LEDGER — Intake V6 (UI-authoritative)

**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1`  
**Primary write:** `PUT /api/v1/intake-v6/workspaces/{id}/finish-setup`  
**Probe authority:** `POST /api/v1/product-system/commercial-price-preview/TPL-VOLUMETRIC-LETTERS_v2` (EUR)  
**Sources:** Intake V6 Review UI (`IntakeV6ReviewStep`, lighting/finish/ACM panels), `intake_v4.py` schema, F7D field ledger cross-check.

Legend: **commercial expectation** = YES/NO/UNKNOWN from active Letters EUR commercial contracts (not invented rates).  
`BACKEND_ONLY` = schema token not exposed in current Intake V6 UI — excluded from operator matrix unless noted.

| surface/step | control label | control type | visible? | enabled? | operator-selectable values | frontend state path | request payload path | backend schema path | normalized commercial path | CPP consumer | commercial expectation | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Finisaje | Finisaj față | select | Y | Y | `none`,`oracal_641`,`oracal_651`,`oracal_8500`,`print_laminate` | `letter_group_finishes[i].face_finish_type` | same | `IntakeV4FinishSetup` / group face | finish face rules | `finisaje_*` face/vinyl/print lines | YES (except `none`→NO finish surcharge) | |
| Finisaje | Rolă (mm) | select | when oracal/print | Y | Oracal `1000`,`1260`; Print `1050`,`1320`,`1500` | `face_vinyl_roll_width_mm` | same | same | vinyl width rate branches | YES (8500 width tiers) | prerequisite for 8500 |
| Finisaje | Culoare față | color | when oracal | Y | Oracal registry codes | `face_oracal_code` | same | same | usually no tier | NO (color not rate-tiered) | |
| Finisaje | Finisaj cant | select | Y | Y | UI `white/black/gold/silver/ral_paint/oracal_wrapped` → `*_aluminum` / `ral_paint` / `oracal_wrapped` | `return_finish_type` | same | `ReturnFinishTypeToken` | return finish rules | YES for RAL/wrap; NO stock zero surcharge | |
| Finisaje | Adâncime cant | select | Y | Y | `30`,`60`,`80`,`100` | `return_depth_mm` | same | same | qty paths perimeter/depth | YES | |
| Finisaje | Culoare cant Oracal/RAL | color | when wrap/RAL | Y | registry | `return_oracal_code` | same | same | usually no tier | NO | |
| Finisaje | Finisaj spate | select | Y | Y | `forex_10_no_bevel`,`forex_10_with_bevel` | `backing_mode` | same | + schema `none` BACKEND_ONLY | backing rules | YES | `none` not in UI |
| Iluminare | LED activ | checkbox | Y | often readonly-on | true/false | `illuminated` | same | same | lighting gate | YES when toggled | template default illuminated |
| Iluminare | Tip iluminare | select | when LED | Y | `led_modules`,`led_strip` | `lighting_system_type` | same | same | LED module/strip lines | YES | |
| Iluminare | Culoare lumină | select | when LED | Y | `warm`,`neutral`,`cool` | `light_color` | same | same | no rate branch known | NO | |
| Iluminare | Putere modul | select | modules | Y | `0.75`,`1`,`1.44` | `led_module_power_w` | same | same | module count/PSU | YES | |
| Iluminare | Sursă LED | select | when LED | Y | `60`,`100`,`160`,`200` | `selected_psu_watts` | same | same | PSU material line | YES | |
| Montaj comercial | Scope | select | Y | Y | `none`,`preparation_only`,`preparation_and_site_installation` | `mounting_scope` | same | + legacy aliases BACKEND_ONLY | mounting gates | YES when prep/site sold | |
| Montaj comercial | Șablon montaj | checkbox | when prep | Y | bool | `mounting_template_enabled` | same | same | `sablon_montaj_*` | YES | forex historically RON → mix risk |
| Montaj comercial | Material șablon | select | when tmpl | Y | `forex`,`paper` | `mounting_template_material_type` | same | same | material gate | YES | |
| Montaj comercial | Arie șablon | number | when tmpl | Y | m² | `mounting_template_area_m2` | same | same | qty | YES | |
| Montaj comercial | Montaj locație | checkbox | site scope | Y | bool | `site_installation_included` | same | same | site install lines | YES | |
| Montaj comercial | Sistem montaj | readonly | Y | N | display only | `mounting_system` | may persist | same | structural | NO (not operator money control here) | NOT operator-selectable for OFAT |
| Panou ACM | Tip placă | select | ACM | Y | `standard`,`colorat`,`oglinda_gold`,`oglinda_antracit` | `acm_panel_instance.sheet_material.variant` | nested finish-setup | ACM instance | acm face material | YES when ACM sold | |
| Panou ACM | Mediu | select | ACM | Y | `interior`,`exterior` | `.environment` | nested | ACM | YES when sold | |
| Panou ACM | Folie after frame | select | ACM | Y | `none`/`after_frame` | `shell_finish.apply_after_frame` | nested | ACM shell | YES when sold | |
| Panou ACM | Pliuri | select | ACM | Y | `1`,`2` | `configuration.fold_count` | nested | ACM qty | YES when sold | |
| Panou ACM | Grosime / L1 / L2 | number | ACM | Y | mm | `acm_thickness_mm`,`l1_mm`,`l2_mm` | nested | ACM qty | YES when sold | |
| Panou ACM | Cadru interior | checkbox | ACM | often readonly | bool | `internal_frame_enabled` | nested | ACM | UNKNOWN | |
| Ajustări | Adaos % | number | Y | Y | 0–400 | `commercialInputs.markupPercent` | `commercial_inputs.markup_percent` | commercial inputs | total composition | YES | |
| Ajustări | Discount % | number | Y | Y | 0–100 | `discountPercent` | `discount_percent` | same | YES | |
| Ajustări | TVA % | number | Y | **disabled** | company setting | `vatPercent` | `vat_percent` | settings | NOT operator-selectable | |
| Ajustări | Ajustare manuală (RON) | number | Y | Y | RON | `manualAdjustmentRon` | `manual_adjustment_ron` | same | **UNKNOWN / currency audit** | Letters presentation EUR |

## BACKEND_ONLY / NOT_OPERATOR_SELECTABLE (excluded from matrix)

| Token / field | Reason |
|---|---|
| `printed_vinyl`, `printed_laminated_vinyl`, `plexiglas_clear` | Face schema; not in V6 letter UI list |
| `standard_aluminum`, `none`, `same_as_face` (return) | Not distinct UI options |
| `backing_mode=none` | Schema only |
| `emblem_lighting_mode=needs_decision` | Schema only |
| Legacy mounting_scope aliases | Hydrated → V1 tokens |
| DXF multi-segment, cutout_logo/text sold-root | Not exercised (NOT_EXERCISED.md) |

## Broken-boundary watch

| Symptom | Boundary to prove in matrix |
|---|---|
| UI value never in finish-setup PUT | `UI_BINDING` / `PAYLOAD` |
| Stored but not in quote_input normalize | `NORMALIZATION` |
| Line priced, complete_offer null | `TOTAL_COMPOSITION` / `CURRENCY_COMPOSITION` |
| Forex sablon on EUR Letters | `CURRENCY_COMPOSITION` |
| Manual RON on EUR offer | `CURRENCY_COMPOSITION` (special audit) |

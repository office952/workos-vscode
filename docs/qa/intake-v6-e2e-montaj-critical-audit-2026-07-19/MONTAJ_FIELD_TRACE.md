# Montaj Field-by-Field Trace

Workspace evidence: `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` · API slice `runtime/acm_finish_setup_slice.json`  
Persistence container: `intake_v6_workspaces.payload_json.finish_setup` only (no dedicated columns).

| Field | UI source | State source | Persist | Compiler/PD | Pricing | Readiness/blocker | Downstream | Dead? | Dup? | Misleading? |
|-------|-----------|--------------|---------|-------------|---------|-------------------|------------|-------|-----|--------------|
| `mounting_scope` | Montaj comercial accordion (`IntakeV6ReviewStep`) | `finish_setup.mounting_scope` | PUT finish-setup | PD `commercial_mounting_scope` | Gates sablon + site `montaj` line | `MOUNTING_SCOPE_MISSING` if unconfirmed; graph `MOUNTING_SCOPE_INACTIVE` when none | Offer commercial | No | Legacy scopes mapped | Label „Montaj” mixes product |
| `mounting_solution` | Fundal solution selector + ACM/metal forms | `finish_setup.mounting_solution` | yes | frozen in PD; Aggregate conflict if scope inactive | ACM commercial path when applicable; installation_template → template fields | `MOUNTING_SOLUTION_MISSING` if prep active | PD/Aggregate | No | vs legacy `mounting_system` | „șablon montaj” empty option vs product ACM |
| `mounting_template_enabled` | Commercial prep fields | finish_setup | yes | task preview signal | CPP `_sablon_enabled` needs prep-active | incomplete if installation_template | Forex CNC conditional tasks | No | — | **Enabled=true while scope=none on ACM WS** |
| `mounting_template_area_m2` | same | finish_setup | yes | — | sablon qty | required if template enabled under prep | tasks readiness | No | — | Auto 0.7004 present with scope none |
| `mounting_template_material_type` | Forex/paper | finish_setup | yes | — | sablon_forex/hartie | required under prep | tasks | No | — | same |
| `mains_cable_length_m` | Advanced / electrical region | finish_setup | yes | process adapter | wire consumable | invalid length blocks process | Aggregate process notes | No | — | Hidden when irrelevant (good) |
| `site_installation_included` | under site scope | finish_setup | yes | — | forces `montaj` commercial line | — | offer | No | — | defaults true when site scope |
| `power_supply_service_corner` / service_corner | Advanced + SVG/ACM | multi: typed + config + svg_support | yes | PD `service_corner` | process | Aggregate `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` | production | No | **Yes multi-source** | UI says not here when segmented “confirmed” |
| `support_type` | mostly derived | finish_setup / PD derived `alucobond_cased` | yes/derived | PD | legacy paths | `SUPPORT_TYPE_MISSING` legacy | — | Legacy | vs svg_support | Operator rarely sets directly |
| `support_material` / profile / bar_count | Metal premount config | `mounting_solution.configuration` | yes | PD config | metal module | — | — | No | legacy bar profile | — |
| ACP width/height/thickness/return/rear lip/folds/V-groove | Fundal ACP form | `mounting_solution.configuration` | yes | PD + quote input ACM | ACM commercial rules | geometry | Aggregate | No | SVG authoritative dims | Editable vs SVG source tension |
| Segmented status/panels/joints/bindings | `IntakeV6SegmentedBackgroundPanel` | `finish_setup.segmented_background` | yes (+ legacy nest under solution) | PD only CONFIRMED | **explicitly not priced** | FE/BE validation blockers | informational tasks only | No | dual read path | **UI text “confirmat” vs API PROPOSED** |
| Electrical connection / per-panel 220V | `IntakeV6SegmentedElectricalPanel` | nested under segmented | yes | PD only CONFIRMED | not priced / no PSU sizing | unresolved → warning/blocker | Aggregate | No | vs single service corner | Authority switches with segmented confirm |
| Applied component interface | ACP local face modules panel | bindings / segmented element_bindings | yes | PD interface | no | — | no tasks | No | — | Operator may over-read as ownership |
| `mounting_fixing_system` | Advanced | finish_setup | yes | PD fixing projection | separate | — | Aggregate | No | — | Technical |
| Legacy `mounting_system` / `mounting_bar_profile` | read-only Advanced | finish_setup | stripped on new saves when solution exists | PD/pricing fallback | legacy | does **not** satisfy solution gate | — | Compatibility | Yes | Looks alive |
| Accesorii montaj (not a field) | Pricing rail banner | computed `mounting_accessories_percent` | N/A | logical list formula | 5% manufacturing | missing-rate UI when cost incomplete | consumable estimate | No | named “montaj” | Appears even when commercial Montaj scope=none |

## Plugin evidence

- Browser/Playwright: Montaj tab selected (`10_montaj_tab_selected_1440.png`); banner „Tarife lipsă — Accesorii montaj / conectori”.
- Git: see `GIT_HISTORY_AND_OWNERSHIP_TRACE.md`.
- Figma: not used as ownership authority.

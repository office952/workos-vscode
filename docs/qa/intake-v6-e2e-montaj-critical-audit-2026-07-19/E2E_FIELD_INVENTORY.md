# E2E Field Inventory — Page 2 + Confirmare

Authority: live code + ACM runtime `IV6-EA145E74` on FE `:3000` / BE `:8003`.  
Not every Finisaje/Iluminare row is expanded here; Montaj is complete; other tabs listed at control-group level for chain context.

| ID | Surface | Field/control | UI component | State key | Truth owner | Persisted where | Pricing effect | PD/Aggregate effect | Confirmare effect | Execution effect | Visibility condition | Duplicate? | Verdict |
|----|---------|---------------|--------------|-----------|-------------|-----------------|----------------|---------------------|-------------------|------------------|----------------------|------------|---------|
| F01 | Finisaje | Letter group finish rows | ReviewStep / letter cards | `letter_group_finishes[]` | FinishSetup | finish_setup | finish lines | components.finish | blockers if incomplete | CNC prep | always for letters | — | OK owner |
| F02 | Finisaje | Cant depth/finish | Edge cant cards | letter/return fields | FinishSetup | finish_setup | cant lines | yes | local + footer | yes | letter present | — | OK |
| F03 | Finisaje | Artwork/vector confirm | artwork cards | `artwork_*` | FinishSetup | finish_setup | print/laminate | artwork components | warning/blocker | graphics ops | artwork present | — | OK |
| L01 | Iluminare | LED on/type/power/PSU | LightingSection | `illuminated`, LED/PSU fields | FinishSetup | finish_setup | LED/PSU lines | lighting modules | yes | illumination plan gate | illuminated | was dup'd historically | Single owner after V1 |
| M01 | Montaj | Montaj comercial scope | ReviewStep accordion | `mounting_scope` | Commercial mounting | finish_setup | sablon/site gates | `commercial_mounting_scope` | scope confirm gate | offer only | always (collapsed default) | legacy scopes | **Split unclear in UI** |
| M02 | Montaj | Site installation included | ReviewStep | `site_installation_included` | Commercial | finish_setup | `montaj` line | scope bundle | — | offer | site scope only | — | OK |
| M03 | Montaj | Șablon montaj enable/area/material | ReviewStep | `mounting_template_*` | Commercial template | finish_setup | sablon_forex/hartie | task signal | solution incomplete | Forex CNC conditional | prep-active **should** | enabled w/ scope none | **CONTRADICTION** |
| M04 | Montaj | Fundal / solution selector | ReviewStep Fundal | `mounting_solution` | Product support | finish_setup | ACM/metal paths | frozen solution + graph | solution gate if prep | preview ops | support composition | vs svg_support | Product under Montaj tab |
| M05 | Montaj | ACP dimensions/folds/frame | ReviewStep ACP form | solution.configuration.* | Product ACM | finish_setup | ACM commercial | PD support values | process corner etc. | materials/ops | ACM solution | SVG dims | OK product |
| M06 | Montaj | SVG support selection (implicit) | Step1 → Montaj | `svg_support_selection` | Product binding | finish_setup | via ACM | PD when confirmed | — | — | SUPPORT_CONTOUR confirmed | binding dup | OK |
| M07 | Montaj | Segmented proposal/confirm | SegmentedBackgroundPanel | `segmented_background` | Product shell | finish_setup | **none** | CONFIRMED only | warning if PROPOSED | informational | multi-panel detect | nest under solution | **UI vs API status mismatch** |
| M08 | Montaj | Per-panel 220V | SegmentedElectricalPanel | nested electrical | Electrical/product | finish_setup | **none** | CONFIRMED only | warning unresolved | informational | segmented active | vs service_corner | Authority switch |
| M09 | Montaj | Applied / local face modules | AcpLocalFaceModulesPanel | bindings | Interface | finish_setup | none | interface PD | — | none | ACM | — | OK no price |
| M10 | Montaj | Service corner / screw / fixing | Advanced | corner/screw/fixing | Product/process | finish_setup | process | PD/Aggregate | Aggregate error if missing | process | advanced / ACM | multi-source corner | **High risk** |
| M11 | Montaj | Cable length | Advanced / lighting-adjacent | `mains_cable_length_m` | Process/material | finish_setup | wire | process bridge | invalid blocks | consumable | illuminated paths | — | OK |
| M12 | Pricing rail | Tarife lipsă Accesorii | LiveCalculationSummary | computed accessories % | Material breakdown | not a field | 5% job cost | logical list | soft warning UI | none | manufacturing>0 | named montaj | **Not Montaj-field-owned** |
| C01 | Confirmare | Readiness checklist | ConfirmStep | readiness + finish | mixed | — | gate write | — | primary gate | — | page 3 | duplicates Page2 | Residual dup |
| C02 | Confirmare | Continue CTA | footer/confirm | readiness | — | — | — | — | disabled reasons | — | — | — | Naming honesty required |

## Chain summary

SVG/layers → composition → Finisaje → Iluminare → **Montaj (mixed)** → Confirmare → PD (scope can block graph) → Aggregate (corner/graph conflicts) → pricing (Accesorii independent) → task preview (catalog ops; Forex conditional) → execution readiness (not materialized here).

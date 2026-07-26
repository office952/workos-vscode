# Desktop UI Element Inventory

**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602`  
**Runtime:** FE `:3000` · BE `:8003` · workspace sample `29472e22-5fe1-4e8d-af66-f9ab75d5fe32`  
**Sources:** live desktop + code under `frontend/src/components/workos/intake-v6/`

Type codes: Decision · Result · Blocker · Warning · Positive confirmation · Informational · Technical diagnostic · Navigation · Commercial · Decorative · Unknown

Disposition: Keep · Contextual · Disclosure · Merge · Hide · Remove

| ID | Surface | Visible text/control | Component/source | Type | Truth owner | Operator purpose | Current visual owner | Current placement | Importance | Stress | Duplicate? | Keep/move/merge/hide/remove | Reason |
|----|---------|----------------------|------------------|------|-------------|------------------|----------------------|-------------------|------------|--------|------------|-----------------------------|--------|
| G01 | Shell | Left app nav | App shell | Navigation | WorkOS IA | Leave Intake | Outside Intake | Left fixed | Low in-task | Low | No | Keep | App chrome |
| G02 | Shell | “Stare sistem: necesită verificare” | App header | Warning / Unknown | System health | Unclear in Intake | Global header | Top-right | Unclear | High | Yes vs Intake | Contextual / demote | `FALSE_URGENCY` for Intake |
| G03 | Intake | Breadcrumb IV6 · template · step | `IntakeV6Header` | Navigation | Workspace | Orientation | Header | Top | Medium | Low | No | Keep | Identity |
| G04 | Intake | Stepper Straturi/Configurare/Confirmare | Header progress | Navigation | Progress model | Jump/see step | Header | Top | High | Low | No | Keep | Workflow |
| G05 | All | Footer “Următorul pas” | `IntakeV6OperatorWorkspaceFooter` | Navigation | Guidance model | What now | Sticky footer | Bottom | Critical | Medium | Duped by banner | Keep as sole spine | Canonical |
| G06 | All | Footer issue inventory | Footer expand | Technical / Warning | Status counts | Inventory | Footer | Bottom | Medium | Medium | Dup banner | Keep drawer-only detail | Avoid mid-page clone |
| G07 | All | Înapoi / Continuă CTAs | Footer | Navigation | Step gates | Proceed | Footer | Bottom | High | Low | Competes Confirmă | Keep | Gate CTAs |
| P1-01 | Straturi | SVG preview / Confirmă fișier | `IntakeV6LayersFileConfirmPanel` | Decision | Artwork file | Confirm file | Preview card | Main col | High | Low | No | Keep | Physical truth |
| P1-02 | Straturi | Fișier recunoscut chip | FileConfirm | Positive confirmation | Upload | Success | Preview | Near file | Low | Low | No | Keep quiet | Success not alert |
| P1-03 | Straturi | Rol geometrie selects | `IntakeV6LayersRoleTable` | Decision | Layer roles | Assign roles | Layer cards | Main | Critical | Amber if pending | No | Keep | Core Page1 |
| P1-04 | Straturi | Contur suport hint | Role table | Warning / Decision | Support binding | Guide support role | Near cards | Main | High when ACM | Medium | No | Keep local | Wiring truth |
| P1-05 | Straturi | Confirmă toate sugestiile | `IntakeV6LayersOperatorPanel` | Decision | Role confirmations | Batch confirm | Sticky rail | Right | High | Low | No | Keep | Efficiency |
| P1-06 | Straturi | Produs composition panel | `IntakeV6ProductCompositionPanel` | Decision | Composition | Confirm product | Card | Main | Critical | Amber badge | Footer next | Keep CTA L1 | Gate |
| P1-07 | Straturi | Detalii tehnice / template codes | Composition details | Technical diagnostic | Templates | Debug | Disclosure | Nested | Low | Low | No | Disclosure | L6 |
| P1-08 | Straturi | Offer scope panel | `IntakeV6OfferScopePanel` | Informational / Decision | Offer modules | Scope edit | Card | Main | Medium | Low | Review scope | Contextual | Avoid double cards |
| P1-09 | Straturi | Metrici tehnice accordion | SvgAnalyzer step | Technical diagnostic | Geometry metrics | Rare | Collapsed | Main | Low | Low | No | Disclosure | L6 |
| P1-10 | Straturi | SupportContourGeometryCard | Component unused | Unknown | Support geometry | — | **Not rendered** | — | — | — | Orphan code | Remove or wire later | `ORPHANED_UI_ELEMENT` |
| P1-11 | Straturi | Handoff “use footer” summary | LayersOperatorPanel | Informational | Navigation | Point to footer | Rail | Right | Low | Low | Footer | Merge into footer | `DETACHED_HELPER` |
| P2-01 | Config | Produs title + identity | Composition panel | Informational / Decision | Composition | Know product | Top card | Full width | Critical | Low | No | Keep compact | L1 |
| P2-02 | Config | Badge Necesită confirmare | Composition | Warning | Confirmation flag | Act | Badge | Top-right card | High | Medium | Footer/banner | Keep | Not rose slab |
| P2-03 | Config | Confirmă compoziția CTA | Composition | Decision | Confirmation | Confirm | Card L1 | Top | Critical | Low | Footer text | Keep | Required |
| P2-04 | Config | Component mini-cards | Composition open | Informational | Items | See parts | Nested cards | Inside Produs | Medium | Low | Summary line | Merge/compact | `NESTING_NOISE` |
| P2-05 | Config | Detalii tehnice compoziție | Composition | Technical diagnostic | Warnings/PD | Rare | Accordion | Nested | Low | Low | No | Disclosure | L6 |
| P2-06 | Config | Scope ofertă strip | `IntakeV6OfferScopeReviewSummary` | Informational | Offer scope | Know inclusions | Strip | Left col | Low–Med | Low | Page1 scope | Keep quiet | L5 |
| P2-07 | Config | Scope Detalii excluded | Scope disclosure | Informational | Exclusions | See exclusions | Button | Strip | Low | Low | No | Disclosure | OK |
| P2-08 | Config | Blocker banner full | `IntakeV6ReviewOperatorBlockerBanner` | Blocker / Warning | Status service | Attention | Sticky mid | Left | High truth / too loud UI | **Very high** | Footer/drawer | Move→compact chip | Stress engine |
| P2-09 | Config | Banner footer hint | Blocker banner | Informational | Guidance | Navigate | Mid banner | Detached | Low | Medium | Footer | Hide/remove | `DETACHED_HELPER` |
| P2-10 | Config | Diagnostic link | Blocker banner | Technical diagnostic | Diagnostics | Deep dive | Mid | Link | Low | Low | Drawer | Disclosure | L6 |
| P2-11 | Config | Tabs Finisaje/Iluminare/Montaj | `IntakeV6ReviewTabNav` | Navigation | Review tabs | Switch domain | Tablist | Left | High | Low | No | Keep | Structure |
| P2-12 | Config | Tab pending Finisaje badge | TabNav | Warning | Pending finishes | See debt | Tab | On Finisaje | Medium | Amber | Banner | Keep small | OK |
| P2-13 | Config | Pricing Rezultat comercial | `IntakeV6LiveCalculationSummary` | Commercial / Result | Pricing preview | See money | Right rail | Sticky | High commercial / secondary UI | Medium | Banner msgs | Keep secondary | L3 |
| P2-14 | Config | Pricing confirm composition msg | LiveCalc | Warning | Composition gate | Act elsewhere | Rail | Detached | Medium | Medium | Produs | Move near Produs | `DETACHED_HELPER` |
| P2-15 | Config | Cost intern total | LiveCalc | Result | Cost engine | Reference | Rail | Visible | High | Low | No | Keep | Always visible |
| P2-16 | Config | Tarife lipsă chip | LiveCalc | Warning | Rate registry | Fix rates | Rail | Visible | Medium | Medium | Details | Keep compact | Legitimate |
| P2-17 | Config | Detalii linii sheet | LiveCalc Sheet | Commercial / Technical | Line items | Inspect | Drawer | On demand | Medium | Low | No | Keep | OK |
| P2-18 | Config | Ajustări comerciale | ReviewStep accordion | Commercial | Markup/VAT | Adjust | Right under rail | Collapsed | Medium | Low | No | Disclosure | L3 optional |
| P2-19 | Config | Autosave status | `IntakeV6ReviewSaveFooter` | Positive / Warning | Persistence | Trust save | Near panels | Bottom-leftish | Medium | Amber if pending | No | Keep; success tone | Avoid `FALSE_URGENCY` |
| F01 | Finisaje | “Finisaje pe layer…” helper | ReviewStep / letter section | Informational | UX copy | Orient | Under tabs | Floating | Low | Low | Tab hints | Merge into tab/section | `DETACHED_HELPER` |
| F02 | Finisaje | Litere volumetrice header | `IntakeV6ReviewLetterGroupsSection` | Informational | Letters component | Group owner | Card | Main | High | Low | Produs | Keep | L2 owner |
| F03 | Finisaje | Anatomie Față·Cant·Spate helper | Letter section | Informational | Anatomy model | Explain zones | Card | Near groups | Medium | Low | No | Keep near groups | OK |
| F04 | Finisaje | Letter group cards | Letter groups | Decision | FinishSetup | Configure finishes | Cards | Main | Critical | Amber incomplete | No | Keep | Core |
| F05 | Finisaje | Față finish/select/roll/color | Face zone | Decision | Face finish | Choose face | Zone | Expanded | Critical | Low | No | Keep | Primary |
| F06 | Finisaje | Cant finish/depth/color | Cant zone | Decision | Cant | Choose return | Zone | Expanded | Critical | Blocker if missing | Banner | Keep + local blocker | Primary |
| F07 | Finisaje | Spate Forex | Backing zone | Decision | Backing | Choose back | Zone | Expanded | High | Low | No | Keep | Primary |
| F08 | Finisaje | Copiază cant la toate | Cant tools | Decision aid | Batch | Speed | Near groups | Main | Medium | Low | No | Keep | Aid |
| F09 | Finisaje | Vector Logo cards | `IntakeV6ArtworkFinishSection` | Decision | Logo finishes | Configure logos | Nested cards | Main | High when logos | Amber | Letters | Keep | Conditional |
| F10 | Finisaje | Finish ownership technical | Ownership note | Technical diagnostic | Domain ownership | Rare | Accordion | Bottom | Low | Low | No | Disclosure | L6 |
| I01 | Iluminare | Contract “Tip iluminare” | Contract renderer | Decision | lighting_system_type | Choose system | Bare fields | **Above** specialized | High but duplicated | Low | I03 | Merge | `UNEXPLAINED_DECISION` |
| I02 | Iluminare | Contract “PSU selectat (W)” | Contract renderer | Decision | selected_psu_watts | Choose PSU | Bare fields | Above | High dup | Low | I07 | Merge | Dual owner |
| I03 | Iluminare | Engineering adapter helper | Contract section copy | Technical diagnostic | Dev | None | Floating | Top | None | Low | — | Hide | Orphan |
| I04 | Iluminare | Section “Iluminare și surse” | `IntakeV6ReviewLightingSection` | Informational | Lighting UX | Frame | Card | Main | Medium | Low | Contract title | Merge titles | Nesting |
| I05 | Iluminare | LED activ toggle | Lighting section | Decision | illuminated | Enable LED | Card | Top of section | Critical | Low | No | Keep | Primary |
| I06 | Iluminare | Culoare / Putere / Emblemă | Lighting fields | Decision | FinishSetup | Configure light | Card | Main | Critical | Low | No | Keep | Primary |
| I07 | Iluminare | Sursă LED (putere) | Electrical subsection | Decision | PSU | Choose supply | Card | Main | High | Low | I02 | Merge with I02 | One PSU control |
| I08 | Iluminare | Rezultate calculate | Lighting results | Result | LED calc | See quantities | Band | Below decisions | High | Amber if PSU issue | Rail | Keep L3 | Separate OK |
| I09 | Iluminare | Detalii calcul LED | Accordion | Technical diagnostic | Calc detail | Rare | Collapsed | Below | Low | Low | No | Disclosure | L6 |
| I10 | Iluminare | Empty lower viewport | Layout | Decorative / waste | — | — | Main | Below fold | — | — | — | Recompose | Unused space |
| M01 | Montaj | Ordine de lucru strip | ReviewStep | Informational | UX | Orient | Card | Top panel | Low | Low | Shell desc | Shorten/merge | Noise |
| M02 | Montaj | Contract șablon fields | Contract / ReviewStep | Decision | Mounting template | Enable area | Top floating | Above shell | Medium | Low | Commercial cluster | Contextual | Orphaned feel |
| M03 | Montaj | Responsibility helper string | Contract copy | Technical diagnostic | Form system | None | Floating | Top | None | Low | — | Hide | Orphan |
| M04 | Montaj | SectionShell “Montaj” | ReviewSectionShell | Decorative frame | — | Group | Frame | Around all | Low | Low | Accordion titles | Reduce frame | Nesting |
| M05 | Montaj | Montaj comercial accordion | TechnicalDetailsAccordion | Decision group | Commercial mounting | Scope services | Nested | Inside shell | Medium | Low | M02 | Keep conditional | OK |
| M06 | Montaj | Scope comercial montaj | select | Decision | mounting_scope | Include prep/site | Inside accordion | Top | High | Low | No | Keep | Primary commercial |
| M07 | Montaj | Pregătire nested card | Prep section | Decision / Informational | Prep services | Configure prep | Nested card | Inside | Medium | Low when inactive | Empty noise | Collapse if inactive | Nesting |
| M08 | Montaj | Șablon montaj checkbox | input | Decision | mounting_template_enabled | Toggle template | Prep | — | Medium | Low | Contract field | One control only | Merge |
| M09 | Montaj | Arie șablon m² | input | Decision | area | Size template | Prep | — | Medium | Low | Contract | Merge | Conditional |
| M10 | Montaj | Material șablon | select | Decision | material | Choose material | Prep | — | Medium | Low | No | Keep when active | Conditional |
| M11 | Montaj | Lungime cablu | select | Decision | mains_cable_length_m | Cable service | Grid | When solution | Medium | Low | No | Contextual | Not always |
| M12 | Montaj | Cable helper 2.5–25 | helper | Informational | Policy | Explain steps | Under select | Local | Low | Low | No | Keep under control | OK |
| M13 | Montaj | Colt service inactive note | note | Informational | ACP rule | Explain absence | Beside cable | Often wrong context | Low | Low | Advanced corner | Contextual only ACP | `DETACHED_HELPER` |
| M14 | Montaj | Montaj la locație empty card | site section | Informational | Scope | Show locked | Nested empty | Large | Low | Low | — | Hide when inactive | Empty space |
| M15 | Montaj | Site included checkbox | checkbox | Decision | site_installation_included | Include site | When active | — | High when active | Low | No | Keep | Conditional |
| M16 | Montaj | Fundal și carcasă shell | MontajClusterShell | Decision group | Support product | Configure ACP | Primary cluster | Main | Critical ACM | Chip Propunere | No | Keep as primary | Product-first |
| M17 | Montaj | Product System link | Link | Technical diagnostic | Template registry | Admin jump | Header | Visible L1 | Low | Low | IDs | Disclosure | Leak |
| M18 | Montaj | Soluție / Panou ACP select | select | Decision | mounting solution | Choose support | Solution panel | Main | Critical | Low | Composition support | Keep | Core |
| M19 | Montaj | Dimensiuni SVG + hash | readout | Technical diagnostic / Result | SVG geometry | Verify size | Cyan nested | Deep | Medium result / low ID | Low | No | Split: keep mm, hide hash | Leak |
| M20 | Montaj | ACM geometry fields grid | inputs | Decision | ACP config | Define panel | Nested grid | Deep | Critical | Low | No | Keep; reduce frames | Core |
| M21 | Montaj | Segmented background panel | SegmentedBackgroundPanel | Decision / Warning | Segment truth | Confirm panels | Inside Fundal | — | High when proposed | Amber/rose | Banner | Keep local | Domain frozen |
| M22 | Montaj | Segmented electrical | SegmentedElectricalPanel | Decision | 220V | Per-panel power | Inside Fundal | — | High multi-panel | Amber | No | Keep | Domain frozen |
| M23 | Montaj | Avansat accordion | Advanced cluster | Technical / Decision | Legacy/advanced | Rare | Collapsed | Bottom | Low | Low | No | Disclosure default | L6 |
| M24 | Montaj | Service corner select (advanced) | select | Decision | power_supply_service_corner | Corner | Advanced | Hidden | Medium ACP | Low | M13 | Keep advanced/ACP | Conditional |
| M25 | Montaj | Body screw finish | select | Decision | service_screw_finish | Finish | Advanced | — | Low | Low | No | Advanced | L6 |
| M26 | Montaj | Volum aluminum module | select | Decision | module template | Optional | Advanced | — | Low | Low | Product System | Advanced | L6 |
| C01 | Confirmare | Page title | ConfirmStep | Navigation | Step | Orient | Top | Visible | Medium | Low | No | Keep | — |
| C02 | Confirmare | Rezumat accordion default closed | `IntakeV6FinalConfigurationSummary` | Unknown misuse | Whole page | Hide content | Collapsed | Primary | Critical content hidden | False calm | — | Open first-paint | Structural defect |
| C03 | Confirmare | Status tile | Final summary | Blocker / Result | Status | See readiness | Inside accordion | Hidden first | Critical | Neutral styling | Footer | Always visible | Must L1 |
| C04 | Confirmare | Dashboard tiles | ConfirmDashboard | Informational / Result | Recap | Review | Inside | Hidden | Medium | Low | Page2 | Keep after open | L3 |
| C05 | Confirmare | Checklist + draft CTA | ConfirmHandoffPanel | Decision | Handoff | Create draft | Inside | Hidden | Critical | Amber errors | Footer | First paint | Page purpose |
| C06 | Confirmare | Priced quote CTA | Handoff/pricing | Commercial | Quote | Create offer | Inside | Hidden | High when ready | Low | Rail | Keep | L3 |
| C07 | Confirmare | Technical readiness blocks | Summary | Technical diagnostic | Modular graph | Rare | Disclosure | Nested | Low | Low | No | Disclosure | L6 |
| C08 | Confirmare | Blocker props unused in handoff | Code | Blocker | allFatalBlockers | Should show | **Not rendered** | — | — | — | Status only | Fix in impl later | Truth gap risk |

## Summary counts (this inventory)

- Decision controls: dominant on Page1 roles, Finisaje anatomy, Iluminare LED/PSU, Montaj ACP/scope  
- Duplicate / detached / orphan marks: ≥15 explicit  
- Technical leaks on L1: Product System badge, hashes, responsibility strings, adapter helper  
- Positive confirmations at risk of alert chrome: autosave, system header  

Full 15-question answers for each class are aggregated in the reset report sections 8–12; this table is the operational index.

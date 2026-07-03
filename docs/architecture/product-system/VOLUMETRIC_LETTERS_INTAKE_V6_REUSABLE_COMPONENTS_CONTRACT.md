# Volumetric Letters Intake V6 Reusable Components Contract

**Version:** 1.0.0  
**Status:** Docs-only operational contract  
**Scope:** Intake V6 volumetric letters reusable component composition  
**Primary question:** What reusable components compose Intake V6 for volumetric letters, and what truth does each component produce?

---

## 1. Purpose

Intake V6 must act as a composer of reusable components, not as a rigid form duplicated for every volumetric letters variant.

The main problem is not only missing fields. The real problem is the lack of a clear map of reusable components that compose Intake V6 for volumetric letters and the truth produced by each component.

This document defines the operational contract for those reusable components.

---

## 2. Mandatory Boundary

### SVG Analyzer

- suggests geometry and layer roles;
- does not make commercial decisions;
- does not invent final tasks;
- does not replace the form.

### Form System

- activates conditional modules;
- asks for missing inputs;
- collects operator confirmations;
- produces Product Truth.

### ProductDefinition

- consumes Product Truth;
- activates or deactivates product modules;
- emits blockers and warnings;
- does not calculate price.

### CommercialPriceProposal

- consumes only the truth needed for quote readiness;
- does not become the place where commercial logic is guessed in real time.

### CostEngine

- remains internal;
- consumes materials, operations, minutes, and capacity logic;
- does not become commercial truth.

### Pricing Registry

- resolves missing prices or pricing configuration;
- does not repair missing Form System truth;
- does not decide support, finish target, selected_layer, or layer role.

---

## 3. Interpretation of required_before_*

- `required_before_quote`: without the minimum output of the component, the product cannot enter quote composition coherently.
- `required_before_order`: without the required confirmations, the product cannot be frozen correctly for order truth.
- `required_before_execution`: without full truth, execution cannot start without operational risk.

---

## 4. Operational Contract

### 4.1 `base_product`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `base_product` | Base Product | Establishes the canonical product identity and intake context for the volumetric letters request. | Always on when template family is volumetric letters. | Suggested overall width, height, count, grouped geometry summary, source file presence. | product family, product variant, quantity, nominal dimensions if SVG is incomplete, illuminated yes/no, intended commercial scope, customer-facing variant name if needed. | Confirm that detected family and variant match the requested product; confirm quantity and major dimensional interpretation. | canonical product identity, family, runtime template candidate, quantity, dimensional baseline, commercial intent flags. | Activates downstream candidate modules and enables volumetric letters ProductDefinition path. | Required to determine if the request is quotable at all. | Provides baseline dimensions and quantity for internal costing only after truth is accepted. | Missing product family; ambiguous product category; unresolved quantity; no valid geometry baseline. | Quantity derived from SVG but not confirmed; dimensions inconsistent with operator reading. | `YES` | `YES` | `YES` |

### 4.2 `svg_layer_roles`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `svg_layer_roles` | SVG / Layer Roles | Produces the interpreted SVG structure and role suggestions used to pre-activate conditional modules. | Active when SVG exists or when geometry import is attempted. | layer list, grouped contours, face/back candidates, stroke/fill patterns, print hints, lighting hints, support hints, selected_layer candidates. | selected layer when multiple candidates exist, manual role override, ignore/include flags for noisy layers. | Confirm ambiguous layer role mapping; confirm that suggested face/back/print interpretation is acceptable. | canonical layer-role map, geometry confidence notes, role suggestions, unresolved SVG ambiguities. | Activates or suppresses candidate modules such as face, finish, lighting, rear_support, mounting. | Helps readiness by narrowing commercial questions, but never decides them. | Supplies geometry interpretation for internal process estimation. | No usable SVG when SVG is mandatory for this intake path; selected layer unresolved in a multi-layer file. | Low-confidence role detection; multiple valid face candidates; print/finish inferred but not confirmed. | `YES`, when SVG-driven intake path is used | `YES` | `YES` |

### 4.3 `face`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `face` | Face Module | Defines the frontal visible component of the volumetric letters product. | Activated by volumetric letters base path and confirmed face role from SVG or manual override. | face contours, face area estimates, grouped letters, candidate printable face surface. | face material family, face execution mode, transparent/opal intent, face branding treatment, face thickness if not derived elsewhere. | Confirm that detected face role is correct; confirm special exceptions such as non-standard face treatment. | face component truth: active face, material family, execution mode, finish dependency hints, area baseline. | Activates face-related ProductDefinition nodes and may activate finish or print-related subpaths. | Required whenever face treatment affects price, appearance, or offer scope. | Supplies internal area/material/process load after commercial truth is fixed. | Face role missing; face material unresolved; face execution path missing. | Face geometry present but material path unclear; print hint exists without confirmation. | `YES` | `YES` | `YES` |

### 4.4 `back`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `back` | Back Module | Defines the rear closure component and its structural role. | Activated for volumetric letters that require a back element. | back contour candidate if detectable, geometry compatibility hints, enclosure closure hints. | back material, back mode, closure strategy, bevel/simplified back flags if relevant. | Confirm back strategy when SVG cannot decide enclosure interpretation. | back component truth: back present/absent, material, closure mode, structural dependency notes. | Activates back-related ProductDefinition nodes and can enable support or lighting compatibility rules. | Relevant when back material or build mode affects quote scope. | Drives internal material and operation detail for rear closure. | Back required but unresolved; incompatible back mode with selected product type. | Back can be inferred but not confirmed; rear strategy conflicts with lighting assumptions. | `YES` | `YES` | `YES` |

### 4.5 `return_cant`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `return_cant` | Return / Cant Module | Defines side wall depth, material, and treatment for volumetric construction. | Activated when volumetric depth/cant exists or the product family mandates a return. | depth hints from geometry, edge/perimeter hints, candidate cant grouping. | return depth, return material, cant treatment, edge coating or wrap choice, special cant notes. | Confirm non-standard cant build, wrap exceptions, or atypical depth strategy. | return/cant truth: presence, depth, material family, treatment mode. | Activates return-related ProductDefinition nodes and related finish/material rules. | Required whenever return depth or cant treatment affects price. | Used for internal perimeter, material usage, and process load. | Return required but no depth confirmed; cant material missing. | SVG suggests depth but operator has not confirmed manufacturable interpretation. | `YES` | `YES` | `YES` |

### 4.6 `lighting_electrical`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `lighting_electrical` | Lighting / Electrical Module | Defines whether the product is illuminated and the electrical path needed. | Activated when illuminated intent is selected or SVG suggests lighting roles. | illumination hints, channel hints, LED accommodation hints, access limitations. | illuminated yes/no, lighting system type, power strategy, cable/access assumptions, PSU or driver class if commercially relevant. | Confirm if suggested illumination is real; confirm exceptional electrical constraints. | lighting truth: illuminated state, electrical mode, required electrical dependencies, unresolved electrical risks. | Activates lighting/electrical ProductDefinition modules and dependent QC paths. | Required when lighting changes quote scope or commercial promise. | Drives internal LED materials, electrical operations, and capacity assumptions. | Illumination required but no electrical mode chosen; conflicting electrical constraints. | SVG suggests lighting but operator rejects it; illumination confirmed without access strategy. | `YES` when illuminated product is quoted | `YES` | `YES` |

### 4.7 `finish`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `finish` | Finish Module | Defines surface treatment and appearance outputs such as print, laminate, vinyl, or paint-related choices. | Activated when face/return/back treatments are needed or SVG suggests graphic treatment. | printable layer hints, color grouping hints, vinyl/laminate suggestions, finish target candidates. | finish target, print yes/no, laminate yes/no, vinyl application yes/no, paint family, protected surface requirements. | Confirm that suggested finish path is commercially intended; confirm exceptions per surface. | finish truth: treatment choices per target surface, graphic treatment decisions, unresolved finish dependencies. | Activates finish-related ProductDefinition modules and deactivates incompatible alternatives. | Required whenever finish affects the offer, visual promise, or material path. | Drives internal print/paint/vinyl process details and material loads. | Finish required but target unresolved; conflicting finish modes on same target. | SVG suggests finish but no commercial confirmation; multiple finish options remain valid. | `YES` | `YES` | `YES` |

### 4.8 `rear_support`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `rear_support` | Rear Support Module | Defines rear structural support or premount needs beyond the base back component. | Activated by mounting strategy, geometry risk, or explicit support requirement. | support candidate hints, geometry span risk hints, stability suggestions. | support required yes/no, support type, premount strategy, bar/frame family, support notes. | Confirm if support is truly required and what structural approach is acceptable. | rear support truth: support required state, support type, structural dependency flags. | Activates support-related ProductDefinition modules and structural add-ons. | Relevant only when support changes quote scope materially. | Drives internal support materials, structure operations, and capacity load. | Support required but unresolved; support type incompatible with mounting choice. | Geometry hints possible support need, but no operator confirmation yet. | `YES` when support affects offer | `YES` | `YES` |

### 4.9 `mounting`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `mounting` | Mounting Module | Defines how the product is intended to be installed and what mounting dependencies exist. | Activated for any product that must declare installation intent before quote/order truth. | installation orientation hints at most; no decisive commercial decision from SVG. | mounting system, standoff/direct/wall strategy, template-based installation yes/no, site constraints if commercially relevant. | Confirm actual mounting intent and non-standard installation limitations. | mounting truth: mounting mode, installation dependency flags, support implications. | Activates mounting-related ProductDefinition modules and may activate rear support. | Required whenever mounting changes the offer or support requirement. | Supplies internal installation operations and resource assumptions. | Mounting mode unresolved; incompatible mounting/support combination. | SVG suggests one orientation but commercial mounting intent differs. | `YES` | `YES` | `YES` |

### 4.10 `commercial_offer_readiness`

| component_key | display_name | purpose | activation_trigger | SVG inputs | Form System fields | operator confirmations | Product Truth output | ProductDefinition activation/deactivation | CommercialPriceProposal relevance | CostEngine internal-only relevance | blockers | warnings | required_before_quote | required_before_order | required_before_execution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `commercial_offer_readiness` | Commercial Offer Readiness | Consolidates the minimum truth needed to allow a coherent quote without pretending execution truth already exists. | Activated after all commercially relevant reusable components report their minimum outputs. | confidence summary only; no commercial decision from SVG. | readiness confirmations, unresolved assumption acknowledgment, quote-safe fallback choices where allowed. | Confirm unresolved-but-acceptable assumptions and explicit hold points before quote. | quote readiness truth: quoteable yes/no, unresolved assumptions, blocker summary, warning summary. | Activates or blocks quote-ready ProductDefinition states; never decides execution task materialization. | Direct consumer for quote readiness gating. | Only receives derived internal notes if they do not alter commercial truth. | Missing mandatory commercial module outputs; unresolved blockers from face/finish/mounting/lighting/support. | Quote allowed with assumptions that must be visible downstream; pending order-level confirmations. | `YES` | `YES` | `NO`, because execution needs fuller downstream truth |

---

## 5. Why This Contract Exists

This contract prevents duplicated forms such as:

- volumetric letters without support;
- volumetric letters with support;
- volumetric letters with print laminate;
- volumetric letters with vinyl on cant.

Instead, Intake V6 should use:

- one `base_product` module;
- reusable conditional modules;
- activation driven by SVG Analyzer suggestions, Form System questions, and operator confirmations.

---

## 6. Operational Conclusion

Intake V6 must be a composer of reusable components, not a rigid form.

The main problem is not only missing fields, but the lack of a clear map of reusable components that compose Intake V6 for volumetric letters and the truth produced by each one.

---

## 7. Example Scenario — gradi-curat.svg

This section documents a mandatory read-only audit of a real SVG already present in a live Intake V6 workspace. No code, backend, frontend, DB, schema, seed, quote, order, or execution state was changed while collecting this evidence.

### 7.1 File availability

- Desktop file verified as present: `C:\Users\offic\Desktop\gradi-curat.svg`.
- Live UI route used for read-only inspection: `/intake-v6/IR-MR18L96M/operator`.
- Live workspace reused to avoid record creation side effects: `IV6-BB8EE3F8`.
- Live workspace id: `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`.
- Live template: `TPL-VOLUMETRIC-LETTERS_v2`.
- Persisted SVG source in workspace: `gradi-curat.svg`.
- Persisted source hash: `593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1`.

### 7.2 SVG Analyzer findings

- File parsed successfully after safe doctype sanitization.
- Geometry baseline already persisted in workspace payload:
	- width: `5086.99 mm`
	- height: `600.03 mm`
	- letter count: `19`
	- face area: `1.2638 m2`
	- artwork area: `0.8005 m2`
	- outer letter perimeter: `20.9727 ml`
	- total return material perimeter: `29.9098 ml`
	- CNC face cutting perimeter: `25.0188 ml`
	- inner holes count: `9`
	- artwork pieces: `2`
	- volumetric pieces: `21`
- Analyzer color evidence found the real palette used by the file:
	- `#00a0e3`
	- `#e31e24`
	- `#009846`
	- `#ef7f1a`
	- `#2b2a29`
- Analyzer warnings prove the SVG is useful but not sufficient for commercial truth:
	- `FILLED_AREA_NOT_AVAILABLE`
	- `PERIMETER_CONFIDENCE_MEDIUM`
	- `PSEUDO_LAYER_SOLID_FILL`
	- `STROKE_ONLY_VECTOR_LAYER`
- Operational reading:
	- SVG can provide strong geometry and grouping evidence.
	- SVG cannot decide final commercial finish, mounting, or quote-readiness alone.

### 7.3 Layer/group detection

The current analyzer/runtime split the file into six operational groups:

| layer_key | detected name | kind | suggested role | confidence | evidence |
|---|---|---|---|---|---|
| `pseudo:maria` | pseudo maria (blue) | pseudo | `face` | `high` | solid fill `#00a0e3` |
| `pseudo:soare` | pseudo soare (red) | pseudo | `face` | `high` | solid fill `#e31e24` |
| `pseudo:ana` | pseudo ana (green) | pseudo | `face` | `high` | solid fill `#009846` |
| `pseudo:gradinita` | pseudo gradinita (orange) | pseudo | `face` | `high` | solid fill `#ef7f1a` |
| `logo-stanga` | logo stanga | pseudo | `printed_artwork` | `high` | stroke-only vector `#2b2a29` |
| `logo-dreapta` | logo dreapta | pseudo | `printed_artwork` | `high` | stroke-only vector `#2b2a29` |

Operational interpretation:

- four groups behave like letter faces;
- two groups behave like printed emblem/logo artwork;
- analyzer grouping is credible enough to pre-activate modules;
- analyzer grouping is not enough to claim operator-confirmed manufacturing truth.

### 7.4 Suggested vs confirmed roles

- All six groups currently have suggestions.
- All six groups are still pending operator confirmation.
- `layer_role_setup.confirmation_status = missing`.
- `Confirmă toate sugestiile 6` is visible in the current UI.
- `additional_template_binding_confirmation_required` is present as a runtime warning.

What this means operationally:

- the system has enough evidence to suggest downstream modules;
- the system does not yet have enough truth to persist a quote-safe analysis boundary refresh;
- pricing/material/nesting previews remain correctly blocked until role confirmation is complete.

### 7.5 Component activation map

Real module activation from the modular contract preview:

| reusable component | current state from live workspace | why |
|---|---|---|
| `base_product` | active | volumetric letters template and intake context already resolved |
| `svg_layer_roles` | active but incomplete | SVG exists, but role confirmation is still missing |
| `face` | active | four face groups were detected and finish payload exists |
| `back` | active | `backing_mode = forex_10_no_bevel` is already present |
| `return_cant` | active | `return_depth_mm = 60` and `return_finish_type` already exist |
| `lighting_electrical` | active | `illuminated = true`, `lighting_system_type = led_modules` |
| `finish` | active | face/artwork finish payload already exists |
| `rear_support` | inactive | `structura_suport` remains optional inactive |
| `mounting` | active | `mounting_system = direct_wall`, `mounting_template_enabled = true` |
| `commercial_offer_readiness` | blocked | quote handoff preview says `handoff_allowed = false` |

### 7.6 Required Form System questions

Questions that are required by the current product truth contract for this exact file:

| component | what can come from SVG | what cannot come from SVG and must be asked or confirmed |
|---|---|---|
| `base_product` | width, height, letter count, grouped geometry | intended product variant, commercial scope, quantity confirmation when needed |
| `svg_layer_roles` | candidate face groups and artwork groups | final accepted role per group, include/exclude decisions, manual overrides |
| `face` | face group geometry and per-color grouping | face material family confirmation, execution mode per group, exceptions |
| `back` | back presence hints from current template path only | back strategy confirmation, back material override, bevel exception |
| `return_cant` | return perimeter and manufacturable depth candidate only by existing payload | final return depth, final return finish path, special wrap/paint exceptions |
| `lighting_electrical` | illuminated likelihood from current path only | actual illumination intent, power strategy acceptance, electrical exceptions |
| `finish` | source colors, artwork grouping, print hints | chosen finish per group, vinyl series, print/laminate decision, transparency intent confirmation |
| `rear_support` | no decisive truth from SVG | whether support is required at all |
| `mounting` | almost nothing decisive | direct wall vs support path, mounting template material/use |
| `commercial_offer_readiness` | blocker evidence only | explicit resolution or accepted hold state |

Minimum question inventory that should be visible before quote for this file:

- confirm each of the six suggested layer roles;
- confirm whether the two logos remain `printed_artwork` and are not volumetric letter faces;
- confirm face material for the four face groups;
- confirm face finish mode per face group;
- confirm whether print laminate on logos is correct;
- confirm return depth `60 mm` or override it;
- confirm return finish family for each letter group and for artwork return edges;
- confirm backing mode `forex_10_no_bevel`;
- confirm mounting mode `direct_wall` and whether support is not required;
- confirm mounting template usage and material;
- confirm lighting path `led_modules` and PSU acceptance;
- confirm unresolved warnings before quote remains blocked or becomes quote-safe.

### 7.7 Required operator confirmations

Mandatory operator confirmations for `gradi-curat.svg`:

- all six layer role suggestions;
- that the two logos are intentional artwork and not misclassified faces;
- that persisted face finish assumptions are intended, not just fallback carryover;
- that `mounting_system = direct_wall` is operationally correct;
- that optional metal support is truly not needed;
- that current LED allocation is acceptable for the real product;
- that quote-readiness cannot be forced while blockers remain.

### 7.8 Product Truth expected output

Expected Product Truth once this scenario is complete:

- canonical product identity: volumetric letters intake bound to `TPL-VOLUMETRIC-LETTERS_v2`;
- confirmed layer-role map for six groups;
- confirmed face groups with per-group finish choices;
- confirmed artwork groups with final execution type;
- confirmed return depth and return finish choices;
- confirmed backing mode;
- confirmed lighting system and power path;
- confirmed mounting path and support requirement state;
- explicit quote-readiness verdict with remaining warnings separated from blockers.

The important rule is that Product Truth must contain confirmed manufacturing/commercial choices, not only analyzer suggestions or UI fallbacks.

### 7.9 Pricing / formula trace

#### Component-by-component trace

| component | Product Truth needed by commercial layer | pricing inputs / formulas | Pricing Registry dependencies | CostEngine internal-only |
|---|---|---|---|---|
| `base_product` | width, height, count, family | enables template path only | none directly | baseline dimensions for internal normalization |
| `svg_layer_roles` | confirmed role map | readiness gate only, non-priced | none | geometry segmentation notes |
| `face` | `letter_face_area_m2`, `face_finish_type` | face material `mp` + `FACE_VINYL_APPLICATION_LABOR` when vinyl exists + `CNC_ROUTER` by cutting perimeter | `MAT-ACP-FATA-LITERE`, face vinyl material code, `CNC_ROUTER`, `FACE_VINYL_APPLICATION_LABOR` | exact nesting/waste and machine load remain internal |
| `back` | `backing_mode`, `letter_face_area_m2` | back material `mp` + back cut perimeter path | `MAT-SPATE-PVC-LITERE`, `CNC_ROUTER` | back prep nuances remain internal |
| `return_cant` | `return_depth_mm`, `return_finish_type`, return perimeter | return profile `ml` + machine forming `ml` + face bonding `ml` + optional paint `ml` | `MAT-PROFIL-LATERAL-LITERE-60MM`, `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING`, `PAINTING`, `MAT-VOPSEA-RAL`, `MAT-ADEZIV-CANT-LITERE` | bend losses, machine efficiency, yield remain internal |
| `lighting_electrical` | `lighting_system_type`, `led_module_count`, PSU selection | LED modules `buc` + PSU units + wiring/assembly rates | `MAT-LED-MODULE`, PSU material codes, `LED_ASSEMBLY`, `ELECTRICAL_WIRING` | watt reserve logic and electrical safety margins remain internal |
| `finish` | per-group finish decisions, artwork execution type | Oracal `mp`, print `mp`, laminate `mp`, application labor `mp`, optional painting `ml` | `MAT-ORACAL-641`, `MAT-ORACAL-651`, `MAT-ORACAL-8500`, `MAT-VINYL-PRINT-LAMINATED`, `SVC-LAMINATION-SERVICE`, `LARGE_FORMAT_PRINT`, `LAMINATION`, `FACE_VINYL_APPLICATION_LABOR`, `MAT-VOPSEA-RAL` | color match heuristics and internal scrap remain internal |
| `rear_support` | support required yes/no | only if activated | premount bar material/rates | fabrication detail remains internal |
| `mounting` | mounting system, template enabled, template area | mounting template area drives template material; support link may activate separate materials | `MAT-SABLON-MONTAJ`, `MAT-SABLON-HARTIE`, possibly support bar codes | install execution planning remains internal |
| `commercial_offer_readiness` | blocker-free minimum truth | no price formula; it gates access to priced previews | none | no internal costing ownership |

#### Fata / Plexiglas

- Status: `VALIDATED_IN_CODE` for the existence of the material/rate path.
- Live geometry anchor: `letter_face_area_m2 = 1.2638`.
- Live registry anchor: `MAT-ACP-FATA-LITERE = 16 EUR/mp`.
- Live contract anchor: `debitare_fata` downstream uses `letter_face_area_m2`, `face_cnc_cut`, `vinyl_application`.
- Operational formula trace:
	- base face material depends on `letter_face_area_m2`;
	- face CNC depends on cutting perimeter, not on commercial guesswork;
	- vinyl/application is conditional on confirmed face finish type.
- What is validated:
	- face material has an owner-confirmed price in registry;
	- face cutting rate exists in registry;
	- the contract explicitly binds face truth to priced downstream inputs.
- What is still partial:
	- exact commercial payload formula assembly is blocked in this workspace because layer confirmations are incomplete.
- Status: `PARTIAL` for end-to-end live priced preview because the system correctly returns `analysis_boundary_blocked` before the preview is allowed.

#### Finisaj / Oracal / Print laminat

- Status: `VALIDATED_IN_CODE` for available finish modes and registry-backed material/rate paths.
- Current face finish options in code:
	- `none`
	- `oracal_651`
	- `oracal_641`
	- `oracal_8500`
	- `print_laminate`
- Current live workspace fallback/carryover state:
	- global `face_finish_type = oracal_651`
	- logos use `execution_type = print_laminate`
	- all group/artwork finish confirmations remain `false`
- Live registry anchors:
	- `MAT-ORACAL-641 = 6.5 EUR/mp`
	- `MAT-ORACAL-651 = 9 EUR/mp`
	- `MAT-ORACAL-8500 = 20 EUR/mp`
	- `MAT-VINYL-PRINT-LAMINATED = 10 EUR/mp`
	- `SVC-LAMINATION-SERVICE = 5 EUR/mp`
	- `LARGE_FORMAT_PRINT = 8.5 EUR/mp`
	- `LAMINATION = 5 EUR/mp`
	- `FACE_VINYL_APPLICATION_LABOR = 5 EUR/mp`
- What is validated:
	- finish modes exist in code;
	- finish materials and operation rates exist in the registry;
	- the live workspace already stores per-group and per-artwork finish payloads.
- What is only `PARTIAL`:
	- current workspace cannot prove final priced totals because operator confirmations are missing;
	- current UI still carries values that may be defaults rather than accepted truth.
- What is `NEEDS_VERIFICATION`:
	- whether the persisted per-group Oracal colors are genuine operator decisions or hydration defaults;
	- whether the two logos should remain translucent `print_laminate` in final product truth.
- What is `DOCUMENTED_NOT_IMPLEMENTED` in a strict semantic sense:
	- a hard guarantee that every persisted finish value shown before confirmation is visually labeled as fallback/assumption rather than accepted truth.

### 7.10 Missing questions before quote

Questions still missing or not yet fully enforced before quote on this exact file:

- per-group explicit confirmation that each face color group should use the persisted Oracal series/value;
- explicit confirmation that the logo groups should remain artwork and not switch to another module path;
- explicit confirmation that the artwork execution type is commercially intended, not only analyzer-derived;
- explicit explanation for why `mounting_system = direct_wall` implies no support in this case;
- explicit confirmation for the unresolved trigger mismatch around support activation;
- explicit distinction in UI between fallback finish values and confirmed finish truth.

### 7.11 What must NOT go to Pricing Registry

The following are not Pricing Registry responsibilities for this scenario:

- deciding whether `logo-stanga` or `logo-dreapta` are artwork vs face;
- deciding whether `direct_wall` is the correct mounting system;
- deciding if metal support is required;
- deciding if `oracal_651` is accepted for all face groups;
- deciding if the two logos should be `print_laminate`;
- repairing incomplete layer role confirmation;
- compensating for missing operator acceptance by allowing quote materialization anyway.

Pricing Registry should only provide priced materials/rates once the relevant Product Truth fields are already coherent.

### 7.12 What remains CostEngine internal-only

The following may inform cost but must not be promoted as commercial truth fields:

- nesting strategy and waste optimization;
- exact machine efficiency and scrap assumptions;
- electrical reserve margins and internal PSU safety calculations beyond surfaced commercial truth;
- internal labor normalization and capacity math;
- internal breakdown of operations that does not change the client-facing offer scope.

### 7.13 Current UI behavior

Observed live behavior for this scenario:

- the workspace opens successfully from an existing intake request without creating a new intake;
- the SVG is already persisted and visible in the workspace;
- the `Straturi` step shows six pending suggested roles and a `Confirmă toate sugestiile 6` action;
- the workspace already holds a populated `finish_setup` payload even though role confirmations are incomplete;
- quote handoff preview is available in read-only mode and correctly reports blocking reasons;
- pricing input preview, material breakdown, and nesting preview return `422` with `analysis_boundary_blocked` and blocker `layer_roles_incomplete`.

Operational implication:

- the system already separates read-only diagnostics from quote-enabling previews;
- the UI currently exposes persisted finish/setup assumptions before the layer-role truth is complete.

### 7.14 Gaps found

Real gaps found during the audit:

- quote-readiness is blocked for the right reason, but the UI still displays rich finish state that can be mistaken for confirmed truth;
- role suggestions are high confidence, but there is still no mandatory confirmation boundary per group before downstream semantics are trusted;
- support activation still has a canonical trigger mismatch warning between `metal_support_required` and `mounting_system`;
- artwork-related confirmation semantics remain weaker than they should be for quote-safe truth;
- current payload can preserve defaults/fallbacks without making their non-confirmed nature explicit enough.

### 7.15 Recommended next safe slice

The next safe slice for this exact scenario is still docs-first and boundary-focused:

- define explicit UI semantics for `suggested`, `hydrated fallback`, and `operator-confirmed` values in Review;
- define the mandatory confirmation contract for face groups and artwork groups before quote previews unlock;
- define the canonical support trigger mapping so `mounting_system` and `metal_support_required` cannot drift;
- keep pricing/material preview blocked until the above truth boundary is satisfied.

This remains a docs-only safe slice. It does not require backend, frontend, DB, schema, seed, task, quote, order, or execution materialization in this audit step.

---

## Operational Component Matrix — gradi-curat.svg

The matrix below closes the reusable-component contract against the real `gradi-curat.svg` case. It answers the operational question that matters for Intake V6:

What must each component force the form to collect so the system can produce correct Product Truth and a quote-safe commercial boundary?

| Componenta | Ce vede SVG | Ce NU poate decide SVG | Ce trebuie sa impuna formularul Intake V6 | Ce trebuie sa confirme operatorul | Product Truth output care trebuie salvat | Pricing / formula source | Ce ramane CostEngine / Operational internal-only | Blocker quote | Blocker order | Blocker execution | Status actual in gradi-curat.svg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Fata / Plexiglas | 4 grupuri candidate `face`; 19 litere; `1.2638 m2`; `5086.99 x 600.03 mm`; culori `#00a0e3`, `#e31e24`, `#009846`, `#ef7f1a`; perimetre si bounding boxes per grup. | material exact; opal/transparent/colorat; grosime; daca toate grupurile sunt produs real; sanfren; finisaj final; relatie finala cu iluminarea. | `selected_face_layer` sau `face_layer_ref`; `operator_confirmed_face_role`; `face_material`; `face_thickness_mm`; `face_bevel_enabled`; `face_finish_type`; `finish_target`; `print_required`; `lamination_required`; `vinyl_required`; `face_is_illuminated`; `geometry_override_required`. | ca cele 4 grupuri sunt fete reale; materialul si grosimea corecta; daca exista sanfren; daca finisajul este pe fata; daca geometria SVG poate fi acceptata comercial. | `face.active`; `face.layer_refs`; `face.material`; `face.thickness_mm`; `face.area_sqm`; `face.geometry_source`; `face.operator_confirmed`; `face.finish_type`; `face.finish_target`; `face.requires_cnc_cut`; `face.bevel_enabled`; `face.blockers`; `face.warnings`. | material fata din Pricing Registry; reguli comerciale pe `mp`; CNC ca regula comerciala pe perimetru sau needs verification; finisaj fata din Pricing Registry plus CommercialPriceProposal; fara pricing pe minute. | nesting; waste; sarcina CNC; timpi interni; eficienta utilaj. | lipsa layer face confirmat; lipsa material/grosime; lipsa finish target; lipsa relatie cu iluminarea. | fata neconfirmata; grosime/material neinghetate. | fata neconfirmata; geometrie neacceptata; lipsa adevar complet de executie. | partial: grupurile si geometria exista, dar rolul si materialul nu sunt confirmate. |
| Spate / Forex | exista `backing_present = true`; `backing_material = FOREX_10MM`; aceeasi baza geometrica a fetei pentru debitare spate. | daca Forex 10 mm este alegerea finala comerciala; alternativa de material; daca exista sanfren pe spate; exceptii constructive. | `backing_mode`; `back_material`; `back_thickness_mm`; `back_bevel_enabled`; `back_layer_ref` daca apare nevoie; `geometry_override_required`. | ca spatele exista; ca `forex_10_no_bevel` este corect; ca nu exista exceptii constructive. | `back.active`; `back.material`; `back.thickness_mm`; `back.mode`; `back.bevel_enabled`; `back.area_sqm`; `back.operator_confirmed`; `back.blockers`; `back.warnings`. | material spate din Pricing Registry; debitare din regula comerciala pe geometrie/perimetru; fara pricing pe timp. | layout intern, pierderi, timpi CNC interni. | lipsa mod spate confirmat; lipsa material spate. | lipsa mod spate inghetat. | lipsa adevar final pentru panou spate. | partial: payload-ul are `forex_10_no_bevel`, dar semantica de confirmare nu este inchisa. |
| Cant / Return | `return_material_perimeter_ml = 29.9098`; `return_depth_mm = 60` in payload; 2 artwork returns detectate; perimetre per grup. | profil exact final; daca 60 mm este acceptat; finisajul cantului; daca cantul artwork urmeaza alta regula; daca autocolantul tine de T06 sau T19E. | `return_depth_mm`; `return_material`; `return_finish_type`; `return_finish_target`; `return_wrap_required`; `return_paint_required`; `return_vinyl_before_forming`; `return_vinyl_after_forming`; `return_layer_refs`; `geometry_override_required`. | adancimea finala; tipul de profil; daca artwork return intra in acelasi tratament; daca autocolantul e inainte de modelare sau dupa corp format. | `return.active`; `return.depth_mm`; `return.material`; `return.finish_type`; `return.finish_stage`; `return.perimeter_ml`; `return.operator_confirmed`; `return.blockers`; `return.warnings`. | profil si finisaj din Pricing Registry; reguli comerciale pe `ml`; T06/T19E trebuie separate in contract, nu calculate din minute. | modelare interna, curbe dificile, scrap, timpi de formare. | lipsa adancime/finisaj/stadiu T06 vs T19E. | lipsa cant final inghetat. | lipsa tratament final cant. | partial: geometria si 60 mm exista, dar confirmarea de semantica finish-stage lipseste. |
| Finisaj / Oracal / Print laminat | culori reale pe 4 grupe; 2 grupe `printed_artwork`; workspace are `oracal_651` global si `print_laminate` pe logos. | daca finishul este fata sau cant; daca Oracal este 641/651/8500; daca logos raman print laminate; daca exista vopsire; daca un grup este decor-only; daca operatia e T06 sau T19E. | `face_finish_type`; `finish_target`; `selected_finish_layer`; `print_required`; `lamination_required`; `vinyl_required`; `paint_required`; `artwork_execution_type`; `return_finish_stage`; `operator_confirmed_finish_role`. | daca valorile hidratate sunt acceptate; target-ul exact; T06 vs T19E; daca logos raman `print_laminate`; daca exista vopsire pe cant. | `finish.active`; `finish.entries[]`; `finish.target`; `finish.type`; `finish.stage`; `finish.layer_refs`; `finish.operator_confirmed`; `finish.blockers`; `finish.warnings`. | materiale si servicii din Pricing Registry; reguli comerciale pe `mp`, `ml`, `buc`; CommercialPriceProposal foloseste doar adevarul confirmat; fara formule hourly. | timpi de aplicare, complexitate reala atelier, rebuturi, protectii interne. | lipsa finish target; lipsa T06/T19E; lipsa confirmare artwork vs product finish. | lipsa finish inghetat per componenta. | lipsa instructiuni finale de finisaj. | partial: optiunile si preturile exista, dar confirmarile si semantica T06/T19E lipsesc explicit. |
| Electrica / LED | `illuminated = true`; `lighting_system_type = led_modules`; `led_module_count = 144`; `selected_psu_watts = 100`; configuratie PSU `[160]`; `estimated_led_watts = 108`. | daca intentia comerciala reala este iluminat; configuratia electrica finala; exceptii traseu cablu; daca artwork-ul are aceeasi logica de iluminare. | `face_is_illuminated`; `lighting_system_type`; `led_configuration_mode`; `led_module_count_override`; `psu_selection_mode`; `electrical_access_notes`; `artwork_lighting_mode`. | ca produsul este luminat; ca numarul/configuratia LED este acceptata; ca sursa si traseul sunt comercial corecte. | `lighting.active`; `lighting.illuminated`; `lighting.system_type`; `lighting.module_count`; `lighting.psu_config`; `lighting.operator_confirmed`; `lighting.blockers`; `lighting.warnings`. | module LED si surse din Pricing Registry; configuratie comerciala pe bucati/config; nu pe minute electrica. | watt reserve, cablaj intern, timp montaj LED, safety margins. | lipsa intentie iluminare confirmata; lipsa configuratie PSU. | lipsa configuratie electrica inghetata. | lipsa electrica finala pentru productie. | partial: payload-ul exista, dar operator confirmation lipseste. |
| Suport spate / Bare | SVG nu decide suport; contractul live tine `structura_suport` inactiv; doar geometria poate sugera risc de span. | daca produsul are suport; tip suport; material bara; lungime comerciala finala; legatura cu montajul. | `support_required`; `support_type`; `support_bar_material`; `support_bar_profile`; `support_bar_length_rule`; `support_reason`; `mounting_dependency`. | daca suportul chiar nu este necesar; daca exista bara/premontaj; tipul de suport acceptat. | `support.active`; `support.required`; `support.type`; `support.material`; `support.profile`; `support.operator_confirmed`; `support.blockers`; `support.warnings`. | daca activ, bara/material/pachet din Pricing Registry; in prezent blocat la nivel semantic de trigger mismatch. | calcule structurale, sudura, incarcare atelier, timpi metal. | lipsa deciziei daca exista suport. | lipsa tip suport/material. | lipsa definitie suport executabil. | inactive with warning: optional component plus `TRIGGER_FIELD_MISMATCH` risk. |
| Montaj | SVG nu vede montaj comercial; payload-ul are `mounting_system = direct_wall`; `mounting_template_enabled = true`; `mounting_template_area_m2 = 3.0523`; `mounting_template_material_type = forex`. | daca `direct_wall` este corect; daca e nevoie de suport; material sablon; constrangeri site; pachet montaj comercial. | `mounting_system`; `mounting_template_enabled`; `mounting_template_material_type`; `mounting_template_area_override`; `site_constraint_notes`; `mounting_package_mode`; `support_dependency`. | ca `direct_wall` este real; ca sablonul este necesar; daca lipsesc constrangeri de sit. | `mounting.active`; `mounting.system`; `mounting.template_enabled`; `mounting.template_material`; `mounting.template_area_sqm`; `mounting.operator_confirmed`; `mounting.blockers`; `mounting.warnings`. | sablon/material/pachet montaj din Pricing Registry sau regula comerciala documentata; fara minute montaj in pret client. | planning montaj, timp echipa, logistics, execution routing. | lipsa mounting system; lipsa relatie cu suportul. | lipsa montaj inghetat comercial. | lipsa instructiuni de montaj executabile. | partial: payload bogat exista, dar suportul si confirmarea montajului nu sunt inchise. |
| SVG / Layere | 6 grupuri; 4 `face`; 2 `printed_artwork`; warnings `PSEUDO_LAYER_SOLID_FILL` si `STROKE_ONLY_VECTOR_LAYER`; `confirmation_status = missing`. | care sugestii devin adevar; ce layere sunt ignorate; ce este product vs artwork only; override-uri manuale. | `selected_layer`; `operator_confirmed_face_role`; `operator_confirmed_artwork_role`; `include_in_quote`; `geometry_override_required`; `manual_role_override_reason`. | toate cele 6 sugestii; daca logos raman artwork only; daca exista override de geometrie/rol. | `svg.layer_roles[]`; `svg.confirmation_status`; `svg.accepted_geometry`; `svg.operator_confirmed`; `svg.blockers`; `svg.warnings`. | non-priced readiness gate; nicio sursa de pret. | segmentare, analize, confidence intern. | `layer_roles_incomplete`; `operator_confirmation_missing`; `unclassified_vector_artwork_requires_decision`. | aceleasi blocari, plus imposibilitate de a ingheta order truth. | executia nu poate porni fara roluri confirmate. | blocked: acesta este blockerul real curent. |
| Readiness oferta | quote handoff preview disponibil; `handoff_allowed = false`; previews comerciale blocate corect; Pricing Registry pregatit. | nu poate decide daca lipsa e de pret sau de adevar; nu poate substitui confirmarile lipsa. | `quote_readiness_ack`; `assumption_policy`; `unresolved_warning_resolution`; `operator_confirmation_complete`. | ca produsul poate sau nu poate merge la oferta; ca warning-urile ramase sunt acceptabile sau nu. | `quote_readiness.status`; `quote_readiness.blockers`; `quote_readiness.warnings`; `quote_readiness.operator_confirmed`. | Product Truth + Pricing Registry + CommercialPriceProposal boundary; nu din CostEngine. | orice detaliu intern ramas dupa frontiera comerciala. | orice lipsa minima de Product Truth; in cazul real `layer_roles_incomplete`. | lipsa confirmarilor obligatorii. | lipsa truth complet de executie. | blocked: Pricing Registry este pregatit; blockerul real este Product Truth incomplet. |

## Pricing / Formula Trace by Component — gradi-curat.svg

### Fata / Plexiglas

#### Ce vede SVG pentru Fata / Plexiglas

- analyzerul a sugerat 4 grupuri candidate pentru fata:
	- `pseudo:maria`
	- `pseudo:soare`
	- `pseudo:ana`
	- `pseudo:gradinita`
- toate cele 4 au sugestie `face` cu incredere `high`;
- geometria disponibila pentru ofertare preliminara este reala si deja persistata:
	- arie totala fata: `1.2638 mp`;
	- dimensiuni globale: `5086.99 x 600.03 mm`;
	- numar litere: `19`;
	- perimetru litere exterior: `20.9727 ml`;
	- perimetru total de taiere fata: `25.0188 ml`;
- culorile indicative disponibile in SVG sunt:
	- `#00a0e3`
	- `#e31e24`
	- `#009846`
	- `#ef7f1a`
- exista bounding box si perimetru per grup pseudo-face;
- SVG poate sugera ca aceste grupuri sunt fete de litere, dar nu poate decide singur adevarul comercial sau constructiv.

#### Ce NU poate decide SVG

- materialul exact al fetei;
- plexiglas opal / transparent / colorat;
- grosimea reala;
- daca fata este luminoasa sau neluminoasa ca alegere comerciala finala;
- daca se face sanfren;
- daca se aplica Oracal / print laminat / folie / vopsire;
- daca toate grupurile sunt produs real sau unele sunt doar decor/artwork;
- daca layerul este confirmat comercial pentru ofertare.

#### Ce trebuie sa impuna formularul

Formularul Intake V6 trebuie sa ceara explicit pentru aceasta componenta:

- `face_material`;
- `face_thickness_mm`;
- `selected_face_layer` sau `face_layer_ref`;
- `operator_confirmed_face_role`;
- `face_bevel_enabled`, daca este aplicabil;
- `face_finish_type`;
- `finish_target`;
- `print_required`;
- `lamination_required`;
- `vinyl_required`, daca este cazul;
- `face_is_illuminated` sau legatura obligatorie cu `lighting_electrical`;
- `geometry_override_required`, daca operatorul nu are incredere in geometria SVG.

#### Variante care trebuie acceptate

- plexiglas opal;
- plexiglas transparent;
- plexiglas colorat;
- alta varianta configurabila, daca exista in registry;
- grosime 3 mm;
- grosime 5 mm;
- alta grosime configurabila;
- fara finisaj;
- Oracal 641;
- Oracal 651;
- Oracal 8500;
- print laminat;
- vopsire, daca este aplicabil.

#### Product Truth output

Exemplu de output canonical dorit:

- `face.active = true`;
- `face.layer_refs = [...]`;
- `face.material = ...`;
- `face.thickness_mm = ...`;
- `face.area_sqm = 1.2638` sau valoare confirmata;
- `face.geometry_source = svg_analyzer`;
- `face.operator_confirmed = true/false`;
- `face.finish_type = ...`;
- `face.finish_target = face`;
- `face.requires_cnc_cut = true`;
- `face.bevel_enabled = true/false`;
- `face.blockers = [...]`;
- `face.warnings = [...]`.

#### Pricing / formula trace pentru Fata / Plexiglas

- Inputuri de formular necesare pentru oferta:
	- `face_material`;
	- `face_thickness_mm`;
	- `selected_face_layer` sau `face.layer_refs`;
	- `face_finish_type`;
	- `finish_target`;
	- `face_is_illuminated` cand schimba componenta de oferta.
- Inputuri care vin din SVG / geometrie:
	- `face.area_sqm`;
	- `face.cutting_perimeter_ml`;
	- `letter_count`;
	- culoare indicativa per grup.
- Pret plexiglas / mp: vine din Pricing Registry.
	- Pentru traseul live inspectat: `PRICING_REGISTRY_SOURCE = MAT-ACP-FATA-LITERE`.
- Debitare CNC:
	- apartine frontierei comerciale doar daca exista o regula comerciala explicita bazata pe perimetru sau pachet;
	- in suprafetele inspectate nu este validata o formula hourly pentru client;
	- orice minute CNC raman `INTERNAL_COST_ONLY`;
	- starea pentru formula comerciala completa in cazul live este `PARTIAL`, fiindca preview-ul este blocat de `layer_roles_incomplete`.
- Finisaj fata:
	- materialele Oracal/print/laminare vin din Pricing Registry;
	- alegerea efectiva apartine Product Truth si este `COMMERCIAL_PRICE_RELEVANT` doar dupa confirmare;
	- executia interna, rebuturile si timpii de aplicare raman `INTERNAL_COST_ONLY`.
- Clasificare:
	- `PRICING_REGISTRY_SOURCE`: material fata, materiale finisaj, eventual servicii comerciale pe `mp` sau `ml`;
	- `COMMERCIAL_PRICE_RELEVANT`: material fata, finish confirmed, eventuala regula comerciala de debitare, complexitate/politica comerciala daca exista documentata;
	- `INTERNAL_COST_ONLY`: minute CNC, nesting detaliat, scrap, eficienta operator/utilaj;
	- `NEEDS_VERIFICATION`: regula comerciala exacta pentru debitarea fetei in cazul in care nu este doar inclusa in alt bundle comercial.
- Ce NU trebuie pus in formular:
	- minute CNC;
	- timpi operator;
	- routing intern.
- Ce NU trebuie pus in CommercialPriceProposal:
	- cost/minut CNC;
	- cost/ora operator.
- Ce lipseste pentru oferta finala:
	- confirmarea rolului face;
	- material/grosime finale;
	- finish target si finish type confirmate.
- Blocker daca lipseste:
	- `layer_roles_incomplete` sau lipsa adevarului minim pentru fata blocheaza quote.

### Spate / Forex

- Inputuri de formular necesare: `backing_mode`, `back_material`, `back_thickness_mm`, `back_bevel_enabled`.
- Inputuri din SVG / geometrie: aria si perimetrul de taiere asociat spatelui derivat din geometria literelor.
- Preturi necesare: material spate si eventuala regula comerciala de debitare.
- Surse: Pricing Registry pentru material; CommercialPriceProposal doar dupa Product Truth confirmat.
- Regula actuala: `VALIDATED_IN_CODE` pentru existenta `backing_mode = forex_10_no_bevel`; `PARTIAL` pentru formula comerciala live, fiindca preview-ul este blocat inainte de quote path.
- Formula apartine: component contract + Product Truth boundary; nu CostEngine hourly.
- Nu trebuie in formular: timpi CNC, nesting intern.
- Nu trebuie in CommercialPriceProposal: cost/ora de debitare.
- Internal-only: waste, nesting, capacitate CNC.
- Lipsa pentru oferta: confirmarea ca `forex_10_no_bevel` este adevar final.
- Blocker: lipsa mod/material spate confirmat.

### Cant / Return

- Inputuri de formular necesare: `return_depth_mm`, `return_material`, `return_finish_type`, `return_finish_stage`, `return_layer_refs`.
- Inputuri din SVG / geometrie: `29.9098 ml` return total, perimetre per grup, relationarea cu artwork returns.
- Preturi necesare: profil cant pe `ml`, finisaj cant pe `ml`, eventual material de vopsire/autocolant.
- Surse: Pricing Registry pentru profil, vopsire, adeziv; CommercialPriceProposal pentru folosirea lor in regula comerciala.
- Regula actuala: `VALIDATED_IN_CODE` pentru existenta profil/rate registry; `DOCUMENTED_NOT_IMPLEMENTED` pentru semanticile explicite T06/T19E in suprafetele inspectate; `PARTIAL` pentru preview live blocat.
- Formula apartine: component contract + CommercialPriceProposal boundary; nu minute modelare.
- Nu trebuie in formular: minute modelare cant, eficienta utilaj.
- Nu trebuie in CommercialPriceProposal: cost/ora de modelare.
- Internal-only: formare curbe dificile, timpi reali, rebuturi.
- Lipsa pentru oferta: adancime finala, finish type, stage T06 vs T19E.
- Blocker: lipsa semantica finish-stage si confirmare operator.

### Finisaj / Oracal / Print laminat

#### Variante si semantica obligatorie

| Varianta | Ce trebuie ales in formular | Ce layer/target trebuie selectat | Se aplica pe fata? | Se aplica pe cant? | T06 sau T19E | Ce pret trebuie sa existe in Pricing Registry? | Ce regula comerciala il foloseste? | Ce ramane CostEngine / Operational internal-only? | Ce blocheaza oferta daca lipseste? |
|---|---|---|---|---|---|---|---|---|---|
| fara finisaj | `face_finish_type = none`; `finish_target` | target explicit `face` sau `return` | da, ca stare de "brut" | poate insemna fara tratament cant | nici T06, nici T19E | nu cere pret de folie; doar materialul de baza ramane activ | regula comerciala foloseste componenta fara overlay de finisaj | manopera interna daca exista tratament minim de atelier | lipsa target-ului sau conflict cu alte finishuri active |
| Oracal 641 | `face_finish_type = oracal_641` sau `return_finish_type` dupa target | trebuie selectat layer-ul/grupul si target-ul exact | da | doar daca se confirma ca finisaj de cant | T06 doar daca este autocolant pe cant inainte de modelare; T19E daca e aplicare dupa corp format | `MAT-ORACAL-641`; eventual manopera comerciala de aplicare daca este definita | CommercialPriceProposal foloseste material `mp` sau `ml` dupa target si regula component-contract | timpi aplicare, rebut, rework | lipsa target-ului; lipsa distinctiei T06 vs T19E; lipsa rolului confirmat |
| Oracal 651 | `face_finish_type = oracal_651` sau `return_finish_type` | target `face` sau `return`; layer/grup explicit | da | da, daca este confirmat | T06 sau T19E dupa stadiul de aplicare; trebuie decizie explicita | `MAT-ORACAL-651`; eventual manopera comerciala definita | regula comerciala foloseste materialul confirmat si target-ul confirmat | timpi, rework, curburi dificile | lipsa target/stage sau lipsa confirmare operator |
| Oracal 8500 | `face_finish_type = oracal_8500` | target explicit, de regula `face` cand translucidul conteaza | da | posibil, daca contractul il permite si operatorul confirma | T06/T19E doar daca se aplica pe cant; altfel nu | `MAT-ORACAL-8500`; eventual aplicare comerciala | regula comerciala foloseste seria translucid confirmata | selectia de culoare exacta, pierderi si aplicare reala | lipsa target-ului sau lipsa confirmare face iluminata |
| print laminat | `artwork_execution_type = print_laminate`; `print_required = true`; `lamination_required = true` | `logo-stanga`, `logo-dreapta` sau alt target confirmat | da, daca se aplica pe fata | numai daca se confirma explicit pe cant, altfel nu presupune | T19E pentru aplicare dupa corp format; nu T06 implicit | `MAT-VINYL-PRINT-LAMINATED`, `LARGE_FORMAT_PRINT`, `LAMINATION`, `SVC-LAMINATION-SERVICE` unde se aplica | regula comerciala foloseste print + laminare ca output comercial, nu minute print shop | timpi print, setup intern, rebut, profil de culoare | lipsa target artwork confirmat; lipsa deciziei daca grupul este artwork-only |
| vopsire | `paint_required = true`; `finish_target`; `paint_family` sau echivalent | target `return` sau alt target confirmat | posibil, daca produsul o cere | da, frecvent pe cant/return | nu T06 si nu T19E prin definitie de folie; este alta familie de finisaj | `MAT-VOPSEA-RAL` si/sau regula comerciala de vopsire | CommercialPriceProposal foloseste material/pachet/rata comerciala documentata pe target-ul corect | timpi de pregatire, uscare, cabine, rework | lipsa target-ului sau lipsa familiei de vopsire |
| alt material configurabil din registry | selectie explicita de material si target | target si grup selectat obligatoriu | depinde de material | depinde de material | depinde de stadiul real de aplicare | cod material/serviciu existent in Pricing Registry | regula comerciala poate exista doar daca materialul este mapat la componenta | validare tehnica interna si compatibilitate atelier | lipsa maparii intre material, target si componenta |

#### Distinctia T06 vs T19E

- `T06` = autocolant pe cant inainte de modelare.
- `T19E` = aplicare folie/colant dupa corp format.
- Acestea nu sunt acelasi lucru.
- In suprafetele inspectate nu exista o eticheta runtime explicita T06/T19E; pentru acest contract statusul este `DOCUMENTED_NOT_IMPLEMENTED` si trebuie inchis in formularul modular viitor.

#### Pricing / formula trace pentru Finisaj / Oracal / Print laminat

- Inputuri de formular necesare pentru oferta:
	- `face_finish_type`;
	- `return_finish_type`;
	- `finish_target`;
	- `selected_finish_layer`;
	- `print_required`;
	- `lamination_required`;
	- `vinyl_required`;
	- `return_finish_stage` pentru T06/T19E.
- Inputuri care vin din SVG / geometrie:
	- grupuri colorate de fata;
	- grupuri `printed_artwork`;
	- aria artwork `0.8005 m2`;
	- aria fata `1.2638 m2`;
	- perimetre relevante pentru cant.
- Preturi necesare:
	- `MAT-ORACAL-641`;
	- `MAT-ORACAL-651`;
	- `MAT-ORACAL-8500`;
	- `MAT-VINYL-PRINT-LAMINATED`;
	- `SVC-LAMINATION-SERVICE`;
	- `LARGE_FORMAT_PRINT`;
	- `LAMINATION`;
	- `MAT-VOPSEA-RAL` cand se aplica;
	- orice material configurabil suplimentar numai daca este mapat in registry.
- De unde vin preturile:
	- Pricing Registry pentru materiale si servicii comerciale;
	- CommercialPriceProposal pentru folosirea combinatiei confirmate in oferta;
	- CostEngine doar pentru cost intern si analiza operationala;
	- documentatia pentru distinctia T06/T19E pana cand este modelata explicit in UI.
- Ce regula exista acum:
	- optiunile de finish si codurile de registry sunt `VALIDATED_IN_CODE`;
	- relatia dintre payload-ul actual si confirmarea operatorului este `PARTIAL`;
	- distinctia T06/T19E este `DOCUMENTED_NOT_IMPLEMENTED` in suprafetele inspectate;
	- nu este validata o formula comerciala hourly in calea citita.
- Formula apartine:
	- component contract;
	- ProductSystem/Dossier pentru maparea componentelor;
	- CommercialPriceProposal pentru combinarea preturilor comerciale deja existente;
	- Pricing Registry pentru codurile de pret;
	- CostEngine internal-only pentru timp/reality.
- Ce NU trebuie pus in formular:
	- minute aplicare folie;
	- minute laminare;
	- minute vopsire.
- Ce NU trebuie pus in CommercialPriceProposal:
	- cost/ora print shop;
	- cost/minut aplicare folie;
	- timp atelier ca formula directa de client.
- Ce ramane doar CostEngine intern:
	- setup print;
	- routing intern;
	- rebut, rework, internal scrap;
	- workload real.
- Ce lipseste pentru oferta finala:
	- confirmarea layer/target;
	- confirmarea ca logos raman artwork-only;
	- confirmarea T06 vs T19E unde cantul are folie.
- Ce blocker apare daca lipseste:
	- lipsa target-ului sau a semnaticii de finish blocheaza quote deoarece Product Truth ramane ambiguu.

### Electrica / LED

- Inputuri de formular necesare: `face_is_illuminated`, `lighting_system_type`, configuratie LED, selectie surse, exceptii artwork.
- Inputuri din SVG / geometrie: perimetru litere si grupare produs/artwork; nu intentia comerciala finala.
- Preturi necesare: module LED, surse, eventual pachet comercial electric.
- Surse: Pricing Registry pentru module si PSU; CommercialPriceProposal pentru regula comerciala pe configuratie.
- Regula actuala: `VALIDATED_IN_CODE` pentru prezenta campurilor si codurilor live; `PARTIAL` pentru quote path blocat inainte de confirmare operator.
- Formula apartine: component contract + CommercialPriceProposal; nu timp electrica.
- Nu trebuie in formular: minute electrica, setup intern.
- Nu trebuie in CommercialPriceProposal: cost pe ora electrician.
- Internal-only: cablaj, watt reserve detaliat, safety margins, timpi montaj intern.
- Lipsa pentru oferta: confirmarea iluminarii si configuratiei PSU.
- Blocker: lipsa truth electric confirmat.

### Suport spate / Bare

- Inputuri de formular necesare: `support_required`, `support_type`, `support_bar_material`, `support_bar_profile`, `support_bar_length_rule`.
- Inputuri din SVG / geometrie: doar context geometric, nu decizie suport.
- Preturi necesare: bara/material suport si pachet comercial asociat, doar daca suportul devine activ.
- Surse: Pricing Registry daca suportul este activat; in prezent exista warning de mapare trigger.
- Regula actuala: `NEEDS_VERIFICATION` pe activare din cauza `TRIGGER_FIELD_MISMATCH`; niciun pret nu trebuie cerut ca substitut pentru decizia lipsa.
- Formula apartine: component contract + ProductDefinition trigger mapping.
- Nu trebuie in formular: timpi lacatuserie, sudura, productivitate.
- Nu trebuie in CommercialPriceProposal: cost/ora metal fab.
- Internal-only: structura, sudura, routing, capacitate metal.
- Lipsa pentru oferta: decizia daca suportul exista.
- Blocker: lipsa deciziei de suport si mismatch-ul de trigger.

### Montaj

- Inputuri de formular necesare: `mounting_system`, `mounting_template_enabled`, `mounting_template_material_type`, `site_constraint_notes`, `support_dependency`.
- Inputuri din SVG / geometrie: arie sablonului derivata, nicidecum intentia comerciala de montaj.
- Preturi necesare: material sablon, eventual pachet comercial montaj sau regula documentata.
- Surse: Pricing Registry pentru sablon; CommercialPriceProposal pentru folosirea comerciala a pachetului; nu minute montaj.
- Regula actuala: `VALIDATED_IN_CODE` pentru payload-ul live de montaj; `PARTIAL` pentru confirmarea operatorului si suport relation.
- Formula apartine: component contract + CommercialPriceProposal policy.
- Nu trebuie in formular: timp echipa montaj, pontaj, load intern.
- Nu trebuie in CommercialPriceProposal: cost/ora montaj.
- Internal-only: logistics, travel, team planning, execution routing.
- Lipsa pentru oferta: confirmarea `direct_wall`, suport, sablon material.
- Blocker: lipsa sistem montaj confirmat.

### SVG / Layere

- Inputuri de formular necesare: confirmarea celor 6 roluri, include/exclude, override-uri.
- Inputuri din SVG / geometrie: cele 6 grupe, warnings si confidence.
- Preturi necesare: niciunul; este non-priced readiness gate.
- Surse: documentatie + Product Truth boundary; nu Pricing Registry.
- Regula actuala: `VALIDATED_IN_CODE` pentru gating-ul de readiness; `layer_roles_incomplete` blocheaza corect.
- Formula apartine: component contract / Product Truth boundary.
- Nu trebuie in formular: preturi pentru a compensa lipsa rolului.
- Nu trebuie in CommercialPriceProposal: orice presupunere de layer role.
- Internal-only: confidence scoring si analize.
- Lipsa pentru oferta: roluri confirmate si artwork decision.
- Blocker: `layer_roles_incomplete`, `operator_confirmation_missing`, `unclassified_vector_artwork_requires_decision`.

### Readiness oferta

- Inputuri de formular necesare: confirmari finale, rezolvare warnings, acceptare explicitata a presupunerilor permise.
- Inputuri din SVG / geometrie: doar indicatori de incompletitudine si geometrie persistata.
- Preturi necesare: toate preturile componentelor deja confirmate, nu mai mult.
- Surse: Pricing Registry pregatit; CommercialPriceProposal consuma doar truth valid.
- Regula actuala: `VALIDATED_IN_CODE` pentru blocarea preview-urilor comerciale cand truth-ul minim lipseste.
- Formula apartine: quote-readiness boundary, nu CostEngine.
- Nu trebuie in formular: minute interne.
- Nu trebuie in CommercialPriceProposal: repararea semantica a truth-ului lipsa.
- Internal-only: orice detaliu cost intern dupa frontiera comerciala.
- Lipsa pentru oferta: truth minim complet.
- Blocker: in cazul real `layer_roles_incomplete`.

## Current Intake V6 Form Truth vs Future Modular Form

### Ce adevar exista acum

- SVG geometry exista si este deja persistata in workspace;
- layer role suggestions exista pentru toate cele 6 grupuri;
- `gradi-curat.svg` este deja in workspace;
- `layer_roles_incomplete` blocheaza handoff-ul;
- `finish_setup` payload exista si este bogat;
- Pricing Registry este pregatit pentru `TPL-VOLUMETRIC-LETTERS_v2`;
- preview-urile `pricing-input-preview`, `material-breakdown` si `nesting-preview` sunt blocate corect pana la layer truth complet.

### Ce este risc acum

- UI poate arata finish/setup bogat inainte ca layer-role truth sa fie confirmat;
- operatorul poate crede ca produsul este mai confirmat decat este;
- lipsurile de layer/finish/support nu trebuie trimise la Pricing Registry;
- lipsa Product Truth nu trebuie mascata ca lipsa de pret;
- distinctia T06/T19E nu este inca modelata explicit in suprafetele inspectate.

### Ce trebuie sa faca viitorul formular modular

- sa activeze componente conditionale;
- sa puna intrebari impuse de componenta;
- sa distinga `suggested` vs `confirmed`;
- sa salveze Product Truth canonical;
- sa blocheze quote daca lipseste truth minim;
- sa blocheze order daca lipsesc confirmarile;
- sa blocheze execution daca lipseste truth complet;
- sa evite formulare duplicate;
- sa nu trateze Pricing Registry ca substitut pentru intrebari de formular.

## What must NOT go to Pricing Registry

Nu trebuie trimise la Pricing Registry:

- lipsa `selected_face_layer`;
- lipsa `operator_confirmed_face_role`;
- lipsa `finish_target`;
- lipsa `selected_layer`;
- lipsa `support_type`;
- lipsa `mounting_system`;
- lipsa deciziei daca produsul are suport;
- lipsa deciziei daca layerul este artwork-only;
- lipsa deciziei daca finisajul tine de T06 sau T19E;
- lipsa deciziei daca fata este real product sau decor.

Acestea sunt probleme de Form System / Operator confirmation / Product Truth, nu probleme de pret.

Pricing Registry trebuie sa rezolve:

- preturi materiale;
- preturi servicii;
- operation rates interne;
- markup policies;
- coverage de pricing.

## What remains CostEngine / Operational internal-only

Aceste informatii pot exista doar pentru analiza interna, capacitate, estimare productie, incarcare atelier si post-job reality:

- minute CNC estimate;
- minute aplicare folie estimate;
- minute modelare cant estimate;
- minute electrica estimate;
- minute montaj estimate;
- setup time intern;
- operator effort intern;
- capacity planning;
- workcenter load;
- internal cost decomposition;
- workcenter efficiency;
- material waste intern;
- routing intern;
- ExecutionReality post-job.

REGULA FERMA:

- aceste valori NU calculeaza pretul comercial la ora;
- aceste valori NU se expun ca pricing client;
- aceste valori NU trebuie folosite ca formula directa de oferta;
- CostEngine ramane intern;
- CommercialPriceProposal ramane comercial.

## 8. Recommended Next Safe Slice

The next safe slice remains:

- finalize the modular form boundary that forces explicit layer-role, face-finish, and T06/T19E confirmations before quote previews unlock.

# Volumetric Letters Intake V6 Modular Form UI State Contract

**Version:** 1.0.0  
**Status:** Docs-only operational contract  
**Scope:** Intake V6 modular form UI state contract for volumetric letters  
**Primary question:** Cum trebuie sa vada operatorul in Intake V6 starea fiecarei componente reutilizabile, astfel incat sa inteleaga clar ce este sugerat, ce este confirmat, ce este fallback, ce blocheaza oferta si ce este doar warning?

---

## 1. Purpose

Acest document defineste contractul UI-state pentru formularul modular viitor din Intake V6.

Nu defineste redesign vizual si nu cere implementare. Defineste doar regulile functionale prin care UI-ul trebuie sa arate adevarul si lipsa de adevar.

Regula de baza este:

- UI-ul trebuie sa arate diferit ce este sugerat, ce este confirmat si ce este fallback;
- UI-ul trebuie sa arate explicit ce blocheaza quote, order sau execution;
- UI-ul nu trebuie sa mascheze lipsa Product Truth ca problema de Pricing Registry;
- UI-ul nu trebuie sa confunde CostEngine internal-only cu pricing comercial.

Acest contract este ancorat in cazul real `gradi-curat.svg`, unde geometria si pricing coverage exista, dar oferta trebuie sa ramana blocata la `layer_roles_incomplete`.

---

## Existing Intake V6 UI Inventory

### 1. Step SVG Analyzer / Straturi

- ce exista acum:
  - upload sau schimbare SVG;
  - preview SVG;
  - metrici geometrice;
  - tabel sau carduri pentru layere si grupuri detectate;
  - operator panel pentru confirmari;
- ce este bun si trebuie pastrat:
  - separarea clara a pasului de analiza fata de Review;
  - vizibilitatea geometriei si a grupurilor detectate;
  - posibilitatea de confirmare rapida a sugestiilor;
- ce este hardcodat:
  - wiring-ul direct dintre analyzer si anumite controale V6 native;
- ce este fallback sau hydrated:
  - eventuale valori persistate local in workspace;
- ce este operator-confirmed:
  - rolurile confirmate explicit pe grupuri;
- ce este Product Truth real:
  - layer role truth si geometria acceptata;
- ce este doar preview:
  - highlight-uri, warnings tehnice si sugestii analyzer;
- ce risca sa fie confundat cu oferta finala:
  - sugestiile analyzer daca nu sunt etichetate clar ca `SUGGESTED`.

### 2. Layer/group confirmation

- ce exista acum:
  - confirmare roluri pe grupuri detectate;
  - confirm-all suggestions;
  - artwork-only decision panel;
- ce este bun si trebuie pastrat:
  - punctul clar unde operatorul aproba sau respinge semantica SVG;
- ce este hardcodat:
  - relatia directa dintre unele roluri si wiring-ul V6 actual;
- ce este fallback sau hydrated:
  - confirmari persistate anterior, daca exista in workspace;
- ce este operator-confirmed:
  - role acceptance sau ignore;
- ce este Product Truth real:
  - clasificarea finala face/artwork/ignored/unknown resolved;
- ce este doar preview:
  - confidence, warnings, pseudo-group diagnostics;
- ce risca sa fie confundat cu oferta finala:
  - faptul ca rolurile sugerate par deja acceptate daca UI-ul nu le marcheaza drept neconfirmate.

### 3. Review / Pasul 2

- ce exista acum:
  - sectiuni pentru setup, finish, lighting, mounting, previews si traceability;
- ce este bun si trebuie pastrat:
  - centralizarea deciziilor comerciale si tehnice intr-un singur pas de review;
  - componentizarea deja existenta pe sectiuni;
- ce este hardcodat:
  - unele optiuni si defaults sunt definite direct in adaptoarele V6 actuale;
- ce este fallback sau hydrated:
  - valori din payload, defaults de contract, valori deduse;
- ce este operator-confirmed:
  - doar campurile explicit schimbate sau acceptate prin workflow;
- ce este Product Truth real:
  - campurile confirmate si salvate coerent pentru componentele active;
- ce este doar preview:
  - panouri de breakdown, task dry run, preview comercial si intern;
- ce risca sa fie confundat cu oferta finala:
  - valorile hidratate care arata mature vizual, dar nu sunt inca validate.

### 4. Finish controls

- ce exista acum:
  - finish fata, culori Oracal, latime rola, print, laminare, artwork finishes;
- ce este bun si trebuie pastrat:
  - optiunile reale deja prezente pentru fata si artwork;
- ce este hardcodat:
  - seturile de optiuni si unele defaults in adaptoarele curente;
- ce este fallback sau hydrated:
  - finish payload preumplut din workspace sau contract;
- ce este operator-confirmed:
  - doar optiunile selectate explicit si validate;
- ce este Product Truth real:
  - finish target, finish type, stage si per-group settings confirmate;
- ce este doar preview:
  - estimari de materiale/operatii rezultate din setup;
- ce risca sa fie confundat cu oferta finala:
  - finish payload hidratat care pare deja inghetat.

### 5. Return/cant controls

- ce exista acum:
  - adancime cant, finish cant, culori cant, RAL, volum;
- ce este bun si trebuie pastrat:
  - separarea logica a cantului fata de fata si artwork;
- ce este hardcodat:
  - unele mape de culori si optiuni native V6;
- ce este fallback sau hydrated:
  - adancimea si finish-ul propuse din payload;
- ce este operator-confirmed:
  - cand operatorul accepta adancimea, culoarea si stage-ul;
- ce este Product Truth real:
  - return depth, finish type, finish stage, material family;
- ce este doar preview:
  - calcule derivate de ml si impact comercial intern;
- ce risca sa fie confundat cu oferta finala:
  - lipsa distinctiei T06 versus T19E.

### 6. Lighting controls

- ce exista acum:
  - illuminated toggle, LED config, PSU, light settings;
- ce este bun si trebuie pastrat:
  - faptul ca lighting este sectiune separata si coerenta;
- ce este hardcodat:
  - anumite defaults pentru module, PSU si wattage;
- ce este fallback sau hydrated:
  - configuratia iluminarii derivata din payload;
- ce este operator-confirmed:
  - configuratia asumata explicit;
- ce este Product Truth real:
  - lighting mode, counts, PSU config si exceptii relevante;
- ce este doar preview:
  - calcule estimate si allocation status;
- ce risca sa fie confundat cu oferta finala:
  - counts derivate care par definitive fara confirmare.

### 7. Mounting controls

- ce exista acum:
  - mounting system, mounting template, material template, profile;
- ce este bun si trebuie pastrat:
  - sectiunea separata de montaj si legatura cu sablonul;
- ce este hardcodat:
  - unele optiuni si defaults de mounting;
- ce este fallback sau hydrated:
  - direct_wall si template area deja persistate;
- ce este operator-confirmed:
  - alegerea finala a sistemului de montaj;
- ce este Product Truth real:
  - mounting system, template usage, support dependency;
- ce este doar preview:
  - impactul derivat in breakdown-uri;
- ce risca sa fie confundat cu oferta finala:
  - valori preumplute care nu sunt inca validate.

### 8. Commercial/internal preview

- ce exista acum:
  - pricing input preview, material breakdown, task/task generation dry run, quote/commercial panels;
- ce este bun si trebuie pastrat:
  - separarea clara intre setup si preview-uri read-only;
- ce este hardcodat:
  - wiring-ul direct spre endpoint-uri si panouri actuale;
- ce este fallback sau hydrated:
  - date de preview preluate din payload sau endpoints cand exista readiness;
- ce este operator-confirmed:
  - nimic in sine; preview-ul nu este confirmare;
- ce este Product Truth real:
  - doar ce vine din componentele confirmate, nu preview-ul insusi;
- ce este doar preview:
  - tot panoul din dreapta si calculele sale;
- ce risca sa fie confundat cu oferta finala:
  - preview-ul comercial intern daca nu este etichetat clar `not final offer`.

### 9. Confirmare

- ce exista acum:
  - pas final de verificare si handoff gating;
- ce este bun si trebuie pastrat:
  - punctul de oprire inainte de quote/order boundary;
- ce este hardcodat:
  - unele motive si gating-uri V6 native;
- ce este fallback sau hydrated:
  - sumarul campurilor deja salvate;
- ce este operator-confirmed:
  - confirmarea finala permisa de boundary;
- ce este Product Truth real:
  - doar valorile deja validate pe componente;
- ce este doar preview:
  - orice sumar informativ care nu schimba adevarul;
- ce risca sa fie confundat cu oferta finala:
  - handoff preview daca Product Truth minim nu este complet.

---

## Intake V6 Modular Form UI State Vocabulary

### 1. `NOT_ACTIVE`

- componenta nu se aplica pentru produsul curent;
- cardul poate fi ascuns sau aratat ca inactiv, dar nu trebuie tratat ca lipsa.

### 2. `SUGGESTED`

- valoare propusa de SVG Analyzer sau de sistem;
- nu este confirmare operator;
- nu are voie sa deblocheze oferta singura.

### 3. `NEEDS_OPERATOR_CONFIRMATION`

- sistemul are o sugestie, dar operatorul trebuie sa confirme;
- exemplu: face layer sugerat, printed artwork sugerat.

### 4. `NEEDS_FORM_INPUT`

- lipseste informatie pe care SVG-ul nu o poate decide;
- exemplu: material fata, grosime, finish target, suport, montaj.

### 5. `FALLBACK_OR_HYDRATED`

- valoare venita din fallback, template, draft sau hidratare;
- trebuie afisata diferit de `OPERATOR_CONFIRMED`;
- nu trebuie confundata cu adevar confirmat.

### 6. `OPERATOR_CONFIRMED`

- operatorul a confirmat explicit;
- poate contribui la Product Truth.

### 7. `BLOCKED`

- componenta blocheaza quote, order sau execution;
- trebuie sa arate clar ce lipseste si ce actiune trebuie facuta.

### 8. `WARNING`

- componenta are risc, informatie estimata sau debt de contract;
- nu blocheaza nivelul curent.

### 9. `READY_FOR_QUOTE`

- Product Truth minim este complet pentru oferta.

### 10. `READY_FOR_ORDER`

- adevarul comercial este complet pentru snapshot de comanda.

### 11. `READY_FOR_EXECUTION`

- adevarul tehnic este complet pentru executie viitoare;
- nu inseamna materialization acum.

State rules:

- `SUGGESTED` nu este egal cu `OPERATOR_CONFIRMED`;
- `FALLBACK_OR_HYDRATED` nu este egal cu `OPERATOR_CONFIRMED`;
- `BLOCKED` trebuie sa fie actionabil;
- `WARNING` nu are voie sa ascunda un blocker;
- `READY_*` se aplica doar dupa rezolvarea blockerelor relevante.

---

## Per-layer / Per-group Modularity Contract

Regula de baza: setarile trebuie sa poata fi aplicate per layer sau per detected group, nu doar global.

| Setting | Applies globally? | Applies per layer/group? | Source now | Future modular source | Product Truth output | Blocks quote if missing? | Notes for gradi-curat.svg |
|---|---|---|---|---|---|---|---|
| role confirmation | no | yes | analyzer step + confirmation table | SVG/layer component contract | `svg.layer_roles[]` | yes | 6 grupuri trebuie confirmate |
| selected template / target template | yes | conditional | workspace/template binding | ProductSystem plus Form System | `product_binding.template_target` | yes when unresolved | template global, dar targetul poate depinde de grup |
| face material | conditional global defaults | yes | review payload / defaults | face component contract | `face.material` per group or family | yes | cele 4 grupuri face pot cere tratari diferite |
| face thickness | conditional global defaults | yes | review payload / defaults | face component contract | `face.thickness_mm` | yes | poate ramane comun, dar trebuie sa suporte override per group |
| face finish type | no | yes | review section | finish component contract | `finish.face.type` | yes | trebuie sa suporte per group |
| Oracal type | no | yes | face finish options | finish component contract | `finish.face.oracal_series` | yes when finish active | 641/651/8500 per group |
| Oracal color | no | yes | letter group finishes | finish component contract | `finish.face.oracal_color_code` | yes when Oracal active | culorile diferite pe grup sunt relevante |
| roll width | possible default global | yes | hydrated finish payload | finish component contract | `finish.face.roll_width_mm` | no by itself unless required by rule | exista deja in payload |
| print required | no | yes | artwork finish logic | finish/artwork component contract | `finish.print_required` | yes when artwork path active | relevant pentru logos |
| lamination required | no | yes | artwork finish logic | finish/artwork component contract | `finish.lamination_required` | yes when print active and rule requires it | relevant pentru logos |
| finish target | no | yes | partially implicit now | finish component contract | `finish.target` | yes | fata vs cant vs artwork |
| finish apply stage | no | yes | not explicit enough now | finish component contract | `finish.stage` | yes when cant finish active | T06 vs T19E |
| return/cant depth | maybe default global | yes | return cant bridge | return component contract | `return.depth_mm` | yes | 60 mm exista, dar trebuie confirmat |
| return/cant color | no | yes | return finish UI | return component contract | `return.color` | yes when finish active | poate diferi per group |
| return/cant finish | no | yes | return finish UI | return component contract | `return.finish_type` | yes | alb/negru/auriu/argintiu/RAL/Oracal |
| RAL color | no | yes | return finish UI | finish or return component contract | `return.ral_code` | yes when RAL active | conditional |
| lighting mode | can start global | yes for exceptions | lighting section | lighting component contract | `lighting.mode` | yes when illuminated | global by default, exceptions possible |
| LED configuration | can start global | yes for exceptions | lighting section | lighting component contract | `lighting.configuration` | yes when illuminated | logo vs litere pot diverge |
| support/mounting | mostly global | conditional per group later only if justified | mounting section | mounting and support component contracts | `mounting.*`, `support.*` | yes when active | in cazul curent ramane global |
| artwork-only / ignored decision | no | yes | analyzer step | SVG/layer component contract | `svg.artwork_only`, `svg.ignored` | yes | logos trebuie clarificate |

---

## Existing Options -> Reusable Components Mapping

| Existing UI option/control | Current location | Reusable component | Should be component-owned? | Should come from Form System? | Should come from ProductSystem/Dossier? | Should come from Pricing Registry? | Product Truth field | CommercialPriceProposal relevance | CostEngine internal-only relevance |
|---|---|---|---|---|---|---|---|---|---|
| Oracal 641 | Review finish controls | Finisaj / Oracal | yes | yes | allowed options can be constrained by dossier | price only | `finish.face.oracal_series=641` | yes | no |
| Oracal 651 | Review finish controls | Finisaj / Oracal | yes | yes | allowed options can be constrained by dossier | price only | `finish.face.oracal_series=651` | yes | no |
| Oracal 8500 | Review finish controls | Finisaj / Oracal | yes | yes | allowed options can be constrained by dossier | price only | `finish.face.oracal_series=8500` | yes | no |
| print laminat | Review artwork finish controls | Finisaj / Printed artwork | yes | yes | activation can come from component path | price only | `finish.artwork.execution=print_laminate` | yes | no |
| vopsit RAL | Return finish controls | Cant / Return or Finish | yes | yes | allowed by dossier/compatibility | price only | `return.finish_type=ral_paint` | yes | no |
| culoare Oracal | Letter group finish controls | Finisaj / Oracal | yes | yes | palette constraints may come from dossier | no, except registry-backed price family | `finish.face.oracal_color_code` | yes | no |
| latime rola | Letter group finish controls | Finisaj / Oracal | yes | yes when required | defaults may come from dossier | no | `finish.face.roll_width_mm` | conditional | yes for optimization only |
| cant/volum | Return cant section | Cant / Return | yes | yes | geometry and ops guidance from dossier | conditional on priced component | `return.active` and `return.material_family` | yes | yes |
| adancime cant | Return cant section | Cant / Return | yes | yes | allowed values can be dossier-driven | no | `return.depth_mm` | yes | yes |
| culoare cant | Return cant section | Cant / Return | yes | yes | allowed values can be dossier-driven | no | `return.color` | yes | no |
| RAL cant | Return cant section | Cant / Return | yes | yes | conditional by finish family | price only for paint material/rule | `return.ral_code` | yes | no |
| iluminare | Lighting section | Electrica / LED | yes | yes | defaults/activation from dossier | no | `lighting.illuminated` | yes | no |
| LED-uri | Lighting section | Electrica / LED | yes | yes | suggested counts may be derived | price only for modules | `lighting.module_count` | yes | yes |
| surse | Lighting section | Electrica / LED | yes | yes | suggested config may be derived | price only for PSU | `lighting.psu_config` | yes | yes |
| cabluri | Lighting section or future electrical section | Electrica / LED | yes | yes | compatibility from dossier | price only if commercialized | `lighting.cable_config` | conditional | yes |
| CNC fata plexiglas | Preview panels | Fata / Plexiglas | yes as derived commercial input | not direct form field | ops mapping from dossier | maybe priced operation, but not truth source | `face.requires_cnc_cut` | yes if commercial rule exists | yes |
| CNC spate Forex | Preview panels | Spate / Forex | yes as derived commercial input | not direct form field | ops mapping from dossier | maybe priced operation, but not truth source | `back.requires_cnc_cut` | yes if commercial rule exists | yes |
| sanfren | Backing or face controls | Fata / Plexiglas or Spate / Forex | yes | yes | compatibility from dossier | no | `face.bevel_enabled` or `back.bevel_enabled` | conditional | yes |
| lipire cant/volum | Preview panels and derived ops | Cant / Return | yes as derived op | not direct unless operator choice affects branch | ops mapping from dossier | maybe priced op, but not truth source | `return.requires_face_bonding` | yes if commercial rule exists | yes |
| montaj | Mounting section | Montaj | yes | yes | defaults/rules from dossier | price only for package/materials | `mounting.system` | yes | yes |

---

## Pseudo-group vs Native Layer Display Contract

For `gradi-curat.svg`:

- exista un layer nativ SVG/Corel: `Layer_x0020_1`;
- `maria`, `soare`, `ana`, `gradinita`, `logo stanga`, `logo dreapta` sunt grupuri detectate sau pseudo-groups, nu layere native Corel separate.

UI-ul trebuie sa afiseze operator-friendly:

- `Grup detectat: maria`
- `Grup detectat: soare`
- `Grup detectat: ana`
- `Grup detectat: gradinita`
- `Grup detectat: logo stanga`
- `Grup detectat: logo dreapta`

Si pentru fiecare:

- `Layer sursa: Layer_x0020_1`
- `Rol sugerat: face` sau `printed artwork`
- `Rol confirmat: ...`
- `Template target: ...`

Display rules:

- UI-ul nu trebuie sa puna `pseudo` in titlul principal vazut de operator;
- identitatea interna poate ramane stabila pentru sistem;
- display-ul trebuie sa fie clar pentru operator si sa evite impresia falsa ca fiecare grup este layer nativ separat;
- sursa nativa si grupul detectat trebuie sa fie ambele vizibile cand ajuta decizia operatorului.

---

## Component UI State Matrix

| Componenta | Possible UI states | Suggested source | Confirmation required? | Form input required? | Fallback/hydrated risk | Blocker display | Warning display | Ready display | Operator action | Product Truth output affected | Current gradi-curat.svg state |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SVG / Layere | `SUGGESTED`, `NEEDS_OPERATOR_CONFIRMATION`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE` | SVG Analyzer layer role suggestions | yes | only for overrides or include/exclude decisions | low; main risk is treating suggestions as confirmed | show missing role confirmations and unresolved artwork-only decisions | show analyzer confidence warnings | show all relevant layer roles confirmed | confirm all relevant roles | `svg.layer_roles`, `svg.confirmation_status`, `svg.accepted_geometry` | `BLOCKED` |
| Fata / Plexiglas | `SUGGESTED`, `NEEDS_OPERATOR_CONFIRMATION`, `NEEDS_FORM_INPUT`, `FALLBACK_OR_HYDRATED`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE`, `READY_FOR_ORDER`, `READY_FOR_EXECUTION` | face groups and geometry from SVG | yes | yes | high; finish/material values can be hydrated and misread as confirmed | show missing face layer, material, thickness, finish target | show geometry confidence or fallback warning | show face truth complete for current level | confirm face groups, material, thickness, finish | `face.*` | `NEEDS_OPERATOR_CONFIRMATION` plus `NEEDS_FORM_INPUT` |
| Spate / Forex | `FALLBACK_OR_HYDRATED`, `NEEDS_OPERATOR_CONFIRMATION`, `NEEDS_FORM_INPUT`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE` | template/runtime path, not SVG-decided | yes | yes | medium; `forex_10_no_bevel` can be shown as if frozen | show missing back material or unresolved back mode | show alias/bevel semantic debt | show back mode confirmed | confirm backing mode and exceptions | `back.*` | `FALLBACK_OR_HYDRATED` / partial |
| Cant / Return | `SUGGESTED`, `NEEDS_FORM_INPUT`, `NEEDS_OPERATOR_CONFIRMATION`, `FALLBACK_OR_HYDRATED`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE` | geometry/perimeter from SVG and runtime | yes | yes | high; depth and finish can be prefilled without true acceptance | show missing depth, finish type, T06/T19E decision | show perimeter confidence | show return truth complete | confirm depth, finish and stage | `return.*` | `FALLBACK_OR_HYDRATED` / partial |
| Finisaj / Oracal / Print laminat | `SUGGESTED`, `NEEDS_OPERATOR_CONFIRMATION`, `NEEDS_FORM_INPUT`, `FALLBACK_OR_HYDRATED`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE`, `READY_FOR_ORDER`, `READY_FOR_EXECUTION` | colors, artwork hints, hydrated payload | yes | yes | very high; hydrated finish values can be mistaken for accepted truth | show missing finish target, finish type, artwork confirmation, T06/T19E decision | show fallback values and non-blocking color warnings | show finish truth complete | confirm target, type and artwork path | `finish.*`, `artwork.*` | `FALLBACK_OR_HYDRATED` and `BLOCKED` by truth gaps |
| Electrica / LED | `FALLBACK_OR_HYDRATED`, `NEEDS_OPERATOR_CONFIRMATION`, `NEEDS_FORM_INPUT`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE`, `READY_FOR_ORDER`, `READY_FOR_EXECUTION` | runtime payload and derived geometry | yes | yes when illuminated | medium; derived counts/config can look final | show missing lighting mode or PSU acceptance | show watt reserve or derived estimate warnings | show lighting truth complete | confirm lighting mode and configuration | `lighting.*` | `FALLBACK_OR_HYDRATED` / partial |
| Suport spate / Bare | `NOT_ACTIVE`, `NEEDS_FORM_INPUT`, `NEEDS_OPERATOR_CONFIRMATION`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE` | no decisive SVG source | yes if active or suspected | yes if active or suspected | medium; inactive optional component can hide mismatch debt | show support type missing when branch is active | show trigger mismatch or optional inactive debt | show support branch explicitly inactive or confirmed | confirm absent or select support type | `support.*` | `NOT_ACTIVE` with warning debt |
| Montaj | `FALLBACK_OR_HYDRATED`, `NEEDS_FORM_INPUT`, `NEEDS_OPERATOR_CONFIRMATION`, `BLOCKED`, `WARNING`, `OPERATOR_CONFIRMED`, `READY_FOR_QUOTE`, `READY_FOR_ORDER`, `READY_FOR_EXECUTION` | runtime payload, not SVG | yes | yes | high; direct_wall and template settings can appear final too early | show missing mounting system or support dependency | show site constraint warnings | show mounting truth complete | confirm mounting system and template semantics | `mounting.*` | `FALLBACK_OR_HYDRATED` / partial |
| Readiness oferta | `BLOCKED`, `WARNING`, `READY_FOR_QUOTE`, `READY_FOR_ORDER`, `READY_FOR_EXECUTION` | derived from all component truth plus pricing coverage | yes, at summary level | indirectly, through missing component fields | low; risk is mislabeling truth blockers as pricing blockers | show exact blocker list and owning component | show residual warnings only | show exact readiness level reached | resolve blockers in owning component | `quote_readiness.*` | `BLOCKED` |

---

## UI Blocker Display Rules

| Blocker code | Componenta | Where shown in UI | Message to operator | Required action | Blocks quote preview? | Blocks handoff? | Blocks order? | Blocks execution? | Must NOT be shown as Pricing Registry issue |
|---|---|---|---|---|---|---|---|---|---|
| `LAYER_ROLES_INCOMPLETE` | SVG / Layere | layer role table, review summary, readiness card | Confirma rolurile tuturor grupurilor relevante inainte de oferta. | confirm all unresolved roles | yes | yes | yes | yes | yes |
| `FACE_LAYER_NOT_CONFIRMED` | Fata / Plexiglas | face component card, review summary | Grupurile candidate pentru fata nu sunt confirmate. | confirm which groups are real face layers | yes | yes | yes | yes | yes |
| `PRINTED_ARTWORK_NOT_CONFIRMED` | Finisaj / Printed artwork | finish/artwork card, review summary | Grupurile artwork nu sunt confirmate ca artwork-only. | confirm artwork path | yes | yes | yes | yes | yes |
| `UNKNOWN_LAYER_REQUIRES_DECISION` | SVG / Layere | layer role table and blocker panel | Exista layere necunoscute care necesita decizie. | classify or ignore explicitly | yes | yes | yes | yes | yes |
| `ARTWORK_ONLY_REQUIRES_DECISION` | SVG / Layere / Finisaj | artwork card and blocker panel | Decide daca layerul este doar artwork sau parte din produs. | choose artwork-only vs product | yes | yes | yes | yes | yes |
| `SELECTED_FACE_LAYER_MISSING` | Fata / Plexiglas | face card | Selecteaza layerul sau grupurile care definesc fata comerciala. | select face layer refs | yes | yes | yes | yes | yes |
| `FACE_MATERIAL_MISSING` | Fata / Plexiglas | face card and missing fields list | Lipseste materialul fetei. | choose face material | yes | yes | yes | yes | yes |
| `FACE_THICKNESS_MISSING` | Fata / Plexiglas | face card and missing fields list | Lipseste grosimea fetei. | choose face thickness | yes | yes | yes | yes | yes |
| `FACE_FINISH_TARGET_MISSING` | Fata / Plexiglas / Finisaj | finish card and missing fields list | Nu este clar unde se aplica finisajul. | choose finish target | yes | yes | yes | yes | yes |
| `FINISH_TYPE_MISSING` | Finisaj / Oracal / Print laminat | finish card | Lipseste tipul de finisaj pentru componenta activa. | choose finish type | yes | yes | yes | yes | yes |
| `T06_VS_T19E_NOT_DECIDED` | Finisaj / Cant | finish card, cant card | Decide daca folia tine de T06 sau T19E. | choose finish stage explicitly | yes when active | yes | yes | yes | yes |
| `SUPPORT_TYPE_MISSING` | Suport spate / Bare | support card, review summary when support is active | Lipseste tipul de suport. | choose support type or confirm no support | yes when active | yes | yes | yes | yes |
| `MOUNTING_SYSTEM_MISSING` | Montaj | mounting card | Lipseste sistemul de montaj. | choose mounting system | yes | yes | yes | yes | yes |
| `LIGHTING_MODE_MISSING` | Electrica / LED | lighting card | Lipseste modul de iluminare pentru produsul iluminat. | choose lighting mode | yes when illuminated | yes | yes | yes | yes |
| `BACK_MATERIAL_MISSING` | Spate / Forex | back card | Lipseste materialul de spate. | choose back material | yes | yes | yes | yes | yes |
| `RETURN_CANT_HEIGHT_MISSING` | Cant / Return | return card | Lipseste inaltimea sau adancimea de cant. | choose return height | yes | yes | yes | yes | yes |
| `PRICING_REGISTRY_COVERAGE_MISSING` | Readiness oferta / Pricing boundary | readiness summary and pricing coverage section | Product Truth este complet, dar lipseste coverage de pricing pentru componenta activa. | fix pricing coverage | yes | yes | no | no | no |
| `INTERNAL_COST_ONLY_DATA_MISSING` | CostEngine internal-only | internal diagnostics only, not commercial blocker panel | Lipsesc date interne pentru analiza operationala, dar oferta poate continua daca truth-ul comercial este complet. | optional internal follow-up | no | no | no | conditional | no |

Display rules:

- blockerul trebuie afisat pe cardul componentei si in sumarul de readiness;
- mesajul trebuie sa spuna ce lipseste, nu doar codul;
- mesajul trebuie sa trimita operatorul la componenta corecta, nu la Pricing Registry, daca problema este Product Truth;
- `PRICING_REGISTRY_COVERAGE_MISSING` este singurul din aceasta lista care poate fi prezentat explicit ca issue de pricing coverage;
- `INTERNAL_COST_ONLY_DATA_MISSING` nu trebuie tratat ca motiv de blocare comerciala daca truth-ul comercial este complet.

---

## Suggested vs Confirmed Visual Contract

### 1. Suggested by SVG Analyzer

- inseamna: sistemul propune o interpretare bazata pe SVG;
- eticheta: `SVG suggested`;
- nu trebuie sa deblocheze: quote, order sau execution singur;
- poate contribui la Product Truth: doar ca input preliminar;
- actiunea operatorului: confirma, override sau ignora explicit.

### 2. Confirmed by operator

- inseamna: operatorul a acceptat explicit valoarea sau clasificarea;
- eticheta: `Operator confirmed`;
- nu trebuie sa deblocheze: niveluri superioare daca alte campuri obligatorii lipsesc;
- poate contribui la Product Truth: da, direct;
- actiunea operatorului: none, except review if changed later.

### 3. Fallback / hydrated from template

- inseamna: valoare incarcata din template, draft sau hidratare runtime;
- eticheta: `Fallback / hydrated`;
- nu trebuie sa deblocheze: quote, order sau execution ca si cum ar fi confirmata;
- poate contribui la Product Truth: doar dupa confirmare explicita sau validare formala prin alte reguli;
- actiunea operatorului: confirm or replace.

### 4. Missing required input

- inseamna: SVG-ul nu poate decide si formularul nu are inca valoare valida;
- eticheta: `Input required`;
- nu trebuie sa deblocheze: nivelul curent de readiness;
- poate contribui la Product Truth: numai dupa completare;
- actiunea operatorului: complete field.

### 5. Warning

- inseamna: exista risc, estimare sau debt, dar nu blocker la nivelul curent;
- eticheta: `Warning`;
- nu trebuie sa deblocheze: nimic singur;
- poate contribui la Product Truth: doar informational;
- actiunea operatorului: review if warning changes understanding.

### 6. Blocker

- inseamna: lipseste adevar minim sau coverage minim pentru nivelul curent;
- eticheta: `Blocked`;
- nu trebuie sa deblocheze: nimic pana nu este rezolvat;
- poate contribui la Product Truth: indirect, prin rezolvarea lui;
- actiunea operatorului: complete or confirm required truth.

### 7. Ready

- inseamna: componenta sau sumarul a atins nivelul cerut pentru quote, order sau execution;
- eticheta: `Ready for quote`, `Ready for order`, `Ready for execution`;
- nu trebuie sa deblocheze: nivele superioare care inca lipsesc;
- poate contribui la Product Truth: da, deja validat la nivelul respectiv;
- actiunea operatorului: proceed or review.

Mandatory rules:

- `SUGGESTED` nu este acelasi lucru cu `CONFIRMED`.
- `FALLBACK_OR_HYDRATED` nu este acelasi lucru cu `CONFIRMED`.

---

## Suggested / Confirmed / Fallback Contract over Existing UI

### suggested by SVG Analyzer

- etichetare: `SVG suggested`;
- poate contribui la Product Truth doar ca propunere;
- nu are voie sa deblocheze oferta;
- operatorul trebuie sa confirme, sa modifice sau sa ignore.

### fallback or hydrated from template

- etichetare: `Fallback / hydrated`;
- poate contribui la Product Truth doar dupa confirmare explicita sau dupa o regula formala clara;
- nu are voie sa deblocheze oferta de una singura;
- operatorul trebuie sa confirme sau sa inlocuiasca valoarea.

### manually selected

- etichetare: `Manual input`;
- contribuie la Product Truth cand este salvat coerent in componenta;
- nu deblocheaza oferta daca alte blockere raman;
- operatorul trebuie sa verifice relatia cu celelalte componente.

### operator confirmed

- etichetare: `Operator confirmed`;
- contribuie direct la Product Truth;
- poate participa la readiness doar impreuna cu restul adevarului minim necesar;
- operatorul poate reveni si modifica doar cu intentie explicita.

### missing required input

- etichetare: `Input required`;
- nu contribuie la Product Truth;
- nu are voie sa deblocheze oferta;
- operatorul trebuie sa completeze campul lipsa.

### warning

- etichetare: `Warning`;
- poate semnala estimari, debt sau confidence issues;
- nu blocheaza nivelul curent;
- operatorul trebuie sa revizuiasca doar daca warning-ul schimba intelegerea.

### blocker

- etichetare: `Blocked`;
- inseamna lipsa truth-ului minim sau a coverage-ului minim de pricing;
- trebuie sa spuna exact ce actiune este necesara;
- nu trebuie prezentat generic ca problema de pret cand este de Product Truth.

Mandatory rules:

- `SUGGESTED` nu este `CONFIRMED`;
- `FALLBACK_OR_HYDRATED` nu este `CONFIRMED`;
- preview comercial intern nu este oferta finala;
- Product Truth incomplet nu trebuie mascat ca lipsa de pret.

---

## Intake V6 Review Screen Contract

In Review, operatorul trebuie sa vada clar:

1. Product Truth summary
- sumar pe componente active, nu doar un payload tehnic.

2. Component readiness cards
- cate un card pentru fiecare componenta activa sau relevanta.

3. Layer role confirmation state
- cate grupuri sunt sugerate, cate confirmate si cate raman blocker.

4. Missing required form inputs
- lista explicita de campuri lipsa per componenta.

5. Finish/setup state
- distinctie intre valori sugerate, hidratate si confirmate.

6. Support/mounting state
- ce este inactiv, ce este optional si ce este blocker.

7. Commercial readiness state
- `ready` versus `not ready`, cu blocker list clara.

8. Quote preview locked/unlocked reason
- motiv explicit pentru lock sau unlock, nu un status vag.

9. What is suggested vs confirmed
- etichete si separare vizibila.

10. What remains warning-only
- warnings separate de blockers.

11. What must not be sent to Pricing Registry
- un reminder functional ca anumite lipsuri sunt de Product Truth, nu de pricing.

For `gradi-curat.svg`, Review trebuie sa arate clar:

- analyzerul are geometrie;
- analyzerul are suggestions;
- layer roles nu sunt complet confirmate;
- oferta ramane blocata;
- Pricing Registry nu este problema;
- operatorul trebuie sa confirme rolurile layerelor si deciziile de componenta.

---

## Existing Preview Boundary

Preview-ul din dreapta sau calculatorul intern poate arata:

- consum plexiglas;
- consum Forex;
- Oracal;
- vopsea RAL;
- cant / volum ml;
- LED-uri;
- surse;
- cabluri;
- adezivi;
- CNC fata plexiglas;
- CNC spate Forex;
- sanfren;
- print;
- laminare;
- lipire cant / volum;
- alte operatii.

Dar:

- NU este oferta finala;
- NU trebuie sa calculeze pret comercial la ora;
- NU trebuie sa inlocuiasca CommercialPriceProposal;
- NU trebuie sa deblocheze quote daca Product Truth este incomplet;
- NU trebuie sa trimita la Pricing Registry probleme care sunt de layer, finish sau support truth.

Boundary rule:

- preview-ul poate explica impactul setup-ului curent;
- preview-ul nu are voie sa legitimeze un produs neconfirmat semantic;
- preview-ul intern si comercial trebuie etichetat clar ca preview.

---

## Modular Component Card Contract

Fiecare component card trebuie sa aiba minim:

- Component name
- State badge
- Source badge:
  - `SVG suggested`
  - `Operator confirmed`
  - `Fallback / hydrated`
  - `Manual input`
- Required fields status
- Blockers
- Warnings
- Operator next action
- Product Truth output preview
- Quote readiness impact
- Order readiness impact
- Execution readiness impact

Functional rules:

- cardul trebuie sa arate cine a furnizat valoarea, nu doar valoarea;
- cardul trebuie sa arate daca valoarea este actionabila sau doar informationala;
- cardul trebuie sa arate urmatoarea actiune minima ceruta operatorului;
- cardul nu cere UI polish, doar contract functional clar.

---

## Applied Case — gradi-curat.svg

- file: `gradi-curat.svg`
- route: `/intake-v6/IR-MR18L96M/operator`
- workspace: `IV6-BB8EE3F8`
- template: `TPL-VOLUMETRIC-LETTERS_v2`
- readiness: `layer_roles_incomplete`

### 1. Ce state trebuie sa aiba SVG / Layere?

- `SUGGESTED` pentru cele 6 grupuri;
- `NEEDS_OPERATOR_CONFIRMATION` pentru cele 4 face groups si 2 printed artwork groups;
- `BLOCKED` la nivel de componenta pana cand confirmarile sunt complete.

### 2. Ce state trebuie sa aiba Fata / Plexiglas?

- `SUGGESTED` pentru grupurile candidate si geometrie;
- `NEEDS_OPERATOR_CONFIRMATION` pentru rolurile de fata;
- `NEEDS_FORM_INPUT` pentru material, grosime si finish target;
- `FALLBACK_OR_HYDRATED` daca runtime-ul afiseaza deja valori preumplute;
- nu poate deveni `READY_FOR_QUOTE` inca.

### 3. Ce state trebuie sa aiba Finisaj / Printed artwork?

- `SUGGESTED` pentru artwork path;
- `NEEDS_OPERATOR_CONFIRMATION` pentru logos ca printed artwork;
- `FALLBACK_OR_HYDRATED` pentru finish payload deja prezent;
- `BLOCKED` daca target-ul, tipul sau semantica T06/T19E lipsesc.

### 4. Ce state trebuie sa aiba Readiness oferta?

- `BLOCKED`;
- nu trebuie sa afiseze `Pricing coverage missing` ca problema principala;
- trebuie sa arate blocker-ele de Product Truth.

### 5. Ce preview-uri trebuie blocate?

- quote handoff preview;
- pricing input preview;
- material breakdown preview;
- nesting preview.

### 6. Ce mesaj trebuie sa vada operatorul?

- geometria si sugestiile sunt disponibile;
- layer roles nu sunt complet confirmate;
- oferta nu poate continua pana la confirmarea layer roles si completarea adevarului pe componente;
- Pricing Registry este pregatit si nu este blockerul principal.

### 7. Ce actiune minima trebuie facuta ca sa treaca spre quote readiness?

- confirmarea tuturor layer roles relevante;
- clarificarea artwork-only versus product;
- completarea campurilor lipsa de component truth pentru componentele comerciale active.

### 8. Ce nu trebuie prezentat ca problema de Pricing Registry?

- face layer neconfirmat;
- printed artwork neconfirmat;
- finish target lipsa;
- T06 versus T19E nedecis;
- support sau mounting nedecise.

Mandatory conclusion:

`gradi-curat.svg` trebuie sa ramana blocat pentru oferta pana cand layer roles si component truth sunt confirmate.

---

## No Hourly Commercial Pricing UI Rule

- UI-ul nu trebuie sa expuna minutele ca pret comercial.
- UI-ul nu trebuie sa sugereze pret pe ora.
- UI-ul nu trebuie sa transforme CostEngine internal-only in pricing client.
- Timpul poate aparea doar ca internal, capacity sau ops signal, daca exista un context intern.
- CommercialPriceProposal ramane comercial, nu hourly.

Daca UI-ul afiseaza sau sugereaza pricing pe timp, marcheaza `ARCHITECTURE_RISK`.

---

## Future Modular Form UI Requirements

- formularul activeaza componente conditionale;
- fiecare componenta cere propriile inputuri;
- acelasi component se refoloseste pentru variante diferite;
- nu se creeaza formular separat pentru fiecare produs;
- UI-ul separa `suggested`, `confirmed`, `fallback`, `blocked`, `warning`;
- Review arata Product Truth summary;
- quote preview ramane blocat pana cand Product Truth minim este complet;
- Pricing Registry nu mascheaza lipsa de adevar;
- CostEngine internal-only nu devine pricing client.

Additional requirements:

- UI-ul trebuie sa arate explicit sursa valorii;
- UI-ul trebuie sa arate explicit urmatoarea actiune minima ceruta;
- UI-ul trebuie sa afiseze blocker-ele pe componenta si in sumarul de readiness;
- UI-ul trebuie sa poata marca o componenta ca `NOT_ACTIVE` fara a o confunda cu lipsa de date.

---

## What remains NOT implemented

- nu s-a implementat modular form;
- nu s-a schimbat UI;
- nu s-au mutat optiunile in contract runtime;
- nu s-a schimbat SVG Analyzer;
- nu s-a schimbat Pricing Registry;
- nu s-a schimbat CommercialPriceProposal;
- nu s-a schimbat CostEngine;
- nu s-a schimbat ProductAggregate;
- nu s-a schimbat ExecutionPlan.

---

## 9. Operational Conclusion

UI-ul formularului modular viitor trebuie sa fie un contract de adevar, nu doar un sumar de campuri.

In cazul `gradi-curat.svg`:

- sugestiile exista;
- geometria exista;
- pricing coverage exista;
- dar UI-ul trebuie sa arate fara ambiguitate ca oferta ramane blocata pana la confirmarea layer roles si completarea component truth.

Acesta este contractul corect pentru starea vizibila a formularului modular viitor.

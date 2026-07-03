# Volumetric Letters Intake V6 Modular Form Readiness Boundary

**Version:** 1.0.0  
**Status:** Docs-only operational contract  
**Scope:** Intake V6 modular form readiness boundary for volumetric letters  
**Primary question:** Cand are voie Intake V6 sa deblocheze oferta si preview-urile comerciale si cand trebuie sa ramana blocat pentru ca Product Truth este incomplet?

---

## 1. Purpose

Acest document defineste boundary-ul operational de readiness pentru formularul modular viitor din Intake V6.

Regula centrala este simpla:

- geometria buna nu este suficienta;
- sugestiile bune de layere nu sunt suficiente;
- preturile disponibile in Pricing Registry nu sunt suficiente;
- oferta se poate debloca doar cand Product Truth minim necesar este complet.

Acest contract este ancorat in cazul real `gradi-curat.svg`, unde sistemul are geometrie, sugestii bune si pricing coverage, dar ramane corect blocat la `layer_roles_incomplete`.

---

## 2. Interpretation of required_before_*

- `required_before_quote`: adevarul minim necesar pentru quote preview, quote handoff preview si orice preview comercial care foloseste Product Truth.
- `required_before_order`: adevarul comercial inghetat necesar pentru snapshot de comanda, fara ambiguitati care ar putea schimba oferta sau configuratia comandata.
- `required_before_execution`: adevarul tehnic complet necesar executiei. Nu inseamna materialization in acest slice; defineste doar contractul de readiness pentru viitor.

---

## Intake V6 Readiness Levels

### 1. `SVG_ANALYZED`

- SVG incarcat sau deja prezent in workspace;
- geometrie disponibila;
- layer/group suggestions disponibile;
- warnings de analizor disponibile;
- nu inseamna ca oferta poate continua.

What it means:

- exista o baza geometrica si semantica preliminara;
- sistemul poate afisa diagnostice si sugestii;
- sistemul nu are voie sa trateze aceste date drept Product Truth complet.

### 2. `LAYER_ROLES_SUGGESTED`

- analyzerul a sugerat roluri pentru layere sau grupuri;
- operatorul inca nu a confirmat;
- pot exista `unknown`, `printed_artwork`, `face`, `ignored` sau alte stari candidate;
- nu deblocheaza oferta.

What it means:

- sistemul poate pre-activa intrebarile de formular relevante;
- sistemul nu are voie sa calculeze preview comercial final doar din sugestii.

### 3. `LAYER_ROLES_CONFIRMED`

- operatorul a confirmat ce este `face`, `back`, `artwork`, `ignored` sau `unknown` rezolvat;
- toate `unknown`-urile relevante sunt rezolvate;
- `artwork-only` vs product-layer este clarificat unde conteaza;
- poate debloca urmatorul nivel doar daca restul componentelor sunt complete.

What it means:

- sistemul are semantica acceptata pentru geometria relevanta comercial;
- layer role truth devine parte din Product Truth;
- quote preview ramane totusi blocat daca lipsesc componente precum fata, cant, finisaj, montaj sau electrica.

### 4. `COMPONENT_TRUTH_COMPLETE_FOR_QUOTE`

- Product Truth minim pentru oferta este complet;
- toate componentele relevante pentru cazul concret au datele minime necesare;
- blockerele de Product Truth sunt rezolvate;
- Pricing Registry coverage exista pentru componentele active;
- quote preview poate fi calculat sau afisat.

What it does not mean:

- nu inseamna comanda inghetata;
- nu inseamna executie pregatita;
- nu inseamna materialization.

### 5. `COMPONENT_TRUTH_COMPLETE_FOR_ORDER`

- confirmarile necesare pentru snapshot de comanda sunt complete;
- nu exista lipsuri critice care ar schimba oferta sau configuratia comandata;
- valorile comerciale si configurarile relevante sunt inghetate semantic.

What it means:

- comanda poate fi reprezentata coerent;
- ambiguitatile comerciale nu mai sunt acceptabile;
- warnings pot ramane doar daca nu schimba semantica comerciala sau snapshot-ul de order.

### 6. `COMPONENT_TRUTH_COMPLETE_FOR_EXECUTION`

- adevarul tehnic necesar executiei este complet;
- layer refs, materiale, finisaje, suport, montaj, electrica si compatibilitati tehnice sunt clarificate;
- nu inseamna materialization acum;
- defineste doar contractul readiness pentru viitor.

What it means:

- execution truth nu mai lasa loc pentru inventarea datelor downstream;
- ExecutionPlan si materialization viitoare nu trebuie sa repare lipsuri de Intake V6.

---

## Blocker / Warning Taxonomy

| Code | Severity | Blocks quote? | Blocks order? | Blocks execution? | Component affected | Why it blocks | What operator must do | Must NOT go to Pricing Registry? | Status in gradi-curat.svg |
|---|---|---|---|---|---|---|---|---|---|
| `LAYER_ROLES_INCOMPLETE` | BLOCKER | yes | yes | yes | SVG / Layere | semantica layerelor este incompleta; sistemul nu stie ce devine produs vs artwork | confirme toate rolurile relevante | yes | active |
| `FACE_LAYER_NOT_CONFIRMED` | BLOCKER | yes | yes | yes | Fata / Plexiglas | fata comerciala nu este confirmata | confirme care grupuri sunt fata reala | yes | implied by current state |
| `PRINTED_ARTWORK_NOT_CONFIRMED` | BLOCKER | yes | yes | yes | Finisaj / Artwork | logos sau artwork-ul pot schimba traseul de finisaj si pricing | confirme ca grupurile sunt artwork si nu produs | yes | active by implication |
| `UNKNOWN_LAYER_REQUIRES_DECISION` | BLOCKER | yes | yes | yes | SVG / Layere | orice unknown relevant lasa Product Truth ambiguu | reclasifice sau ignore explicit | yes | not currently explicit, but covered by readiness gate |
| `ARTWORK_ONLY_REQUIRES_DECISION` | BLOCKER | yes | yes | yes | SVG / Layere / Finisaj | sistemul trebuie sa stie daca layerul este artwork-only | confirme artwork-only vs product | yes | active in spirit via artwork decision blockers |
| `SELECTED_FACE_LAYER_MISSING` | BLOCKER | yes | yes | yes | Fata / Plexiglas | oferta nu poate folosi aria si perimetrul corect fara tinta clara | selecteze layerul sau grupurile de fata | yes | missing today |
| `FACE_MATERIAL_MISSING` | BLOCKER | yes | yes | yes | Fata / Plexiglas | lipseste materialul comercial al fetei | aleaga materialul fetei | yes | missing today |
| `FACE_THICKNESS_MISSING` | BLOCKER | yes | yes | yes | Fata / Plexiglas | lipseste grosimea, care schimba produsul si executia | aleaga grosimea corecta | yes | missing today |
| `FACE_FINISH_TARGET_MISSING` | BLOCKER | yes | yes | yes | Fata / Plexiglas / Finisaj | nu este clar daca finisajul este pe fata, pe cant sau pe artwork | aleaga target-ul de finisaj | yes | missing today |
| `FINISH_TYPE_MISSING` | BLOCKER | yes | yes | yes | Finisaj / Oracal / Print laminat | materialul si regula comerciala de finisaj nu pot fi determinate | aleaga tipul de finisaj | yes | partial today |
| `T06_VS_T19E_NOT_DECIDED` | BLOCKER | yes when cant finish is active | yes | yes | Finisaj / Cant | autocolant pe cant inainte de modelare nu este acelasi lucru cu aplicare folie dupa corp format | decida T06 versus T19E explicit | yes | missing today |
| `SUPPORT_TYPE_MISSING` | BLOCKER | yes when support is active or suspected | yes | yes | Suport spate / Bare | suportul este ramura separata de produs | confirme tipul de suport sau absenta lui | yes | warning debt today |
| `MOUNTING_SYSTEM_MISSING` | BLOCKER | yes | yes | yes | Montaj | suportul, sablonul si unele ramuri comerciale depind de montaj | aleaga sistemul de montaj | yes | not missing today, but remains a boundary field |
| `LIGHTING_MODE_MISSING` | BLOCKER | yes when illuminated | yes | yes | Electrica / LED | produsul iluminat nu poate fi ofertat corect fara mod de iluminare | confirme modul de iluminare | yes | payload exists, confirmation still partial |
| `BACK_MATERIAL_MISSING` | BLOCKER | yes | yes | yes | Spate / Forex | lipseste componenta de spate comercial si tehnic | confirme materialul si modul de spate | yes | not missing in payload, confirmation partial |
| `RETURN_CANT_HEIGHT_MISSING` | BLOCKER | yes | yes | yes | Cant / Return | adancimea cantului schimba profilul si traseul comercial | confirme inaltimea sau override-ul | yes | not missing in payload, confirmation partial |
| `PRICING_REGISTRY_COVERAGE_MISSING` | BLOCKER | yes | no | no | Pricing boundary | exista Product Truth, dar lipsesc preturi comerciale sau coverage | corecteze coverage-ul de pricing, nu Product Truth | no | not active |
| `INTERNAL_COST_ONLY_DATA_MISSING` | WARNING | no | no | conditional | CostEngine internal-only | lipsa timpilor sau a datelor interne nu trebuie sa opreasca oferta daca Product Truth si pricing-ul comercial sunt complete | nu blocheaza oferta; completeaza doar daca procesul intern are nevoie | no | not relevant as blocker |

Taxonomy rules:

- lipsa Product Truth este blocker pentru quote, order sau execution in functie de componenta;
- lipsa de pret sau coverage in Pricing Registry este blocker comercial separat si nu trebuie folosita ca acoperire pentru truth lipsa;
- lipsa datelor internal-only pentru CostEngine nu devine blocker de quote cat timp frontiera comerciala este completa.

---

## Component Readiness Boundary

| Componenta | Required before quote | Required before order | Required before execution | Blocks quote if missing | Blocks order if missing | Blocks execution if missing | Warning only | Pricing Registry dependency | CostEngine internal-only dependency | Current gradi-curat.svg status |
|---|---|---|---|---|---|---|---|---|---|---|
| SVG / Layere | SVG analizat; roluri relevante confirmate; unknown rezolvate; artwork-only clarificat | aceleasi confirmari inghetate | layer refs si semantica tehnica completa | `LAYER_ROLES_INCOMPLETE`, `UNKNOWN_LAYER_REQUIRES_DECISION`, `ARTWORK_ONLY_REQUIRES_DECISION` | da | da | warnings de confidence pot ramane daca rolul final este clar | none | none | blocked |
| Fata / Plexiglas | face layer confirmat; material fata; grosime; geometrie acceptata; finish target daca exista finisaj | material, grosime, finish si rolurile nu mai sunt ambigue | layer refs, material, grosime, sanfren, compatibilitati tehnice | `FACE_LAYER_NOT_CONFIRMED`, `SELECTED_FACE_LAYER_MISSING`, `FACE_MATERIAL_MISSING`, `FACE_THICKNESS_MISSING`, `FACE_FINISH_TARGET_MISSING` | da | da | culoare indicativa din SVG poate ramane warning pana la confirmare | material fata si eventual finisaj | nesting, waste, timpi CNC | partial |
| Spate / Forex | backing mode; back material; geometrie acceptata | back mode si material inghetate | spate complet tehnic, inclusiv bevel daca exista | `BACK_MATERIAL_MISSING` | da | da | warning de alias semantic pana la unificare | material spate | waste, CNC intern | partial |
| Cant / Return | return depth; material/profil; finish type; target; T06/T19E daca exista folie pe cant | aceleasi confirmari inghetate | detalii tehnice complete de cant | `RETURN_CANT_HEIGHT_MISSING`, `FINISH_TYPE_MISSING`, `T06_VS_T19E_NOT_DECIDED` | da | da | warning de confidence pe perimetru daca operatorul accepta geometria | profil cant, finisaj cant | modelare interna, timpi, scrap | partial |
| Finisaj / Oracal / Print laminat | finish type; finish target; layer target; print/lamination booleans; artwork confirmat | combinatia comerciala finala inghetata | instructiuni tehnice de aplicare complete | `FINISH_TYPE_MISSING`, `FACE_FINISH_TARGET_MISSING`, `PRINTED_ARTWORK_NOT_CONFIRMED`, `T06_VS_T19E_NOT_DECIDED` | da | da | warnings de culoare sau fallback hidratat pot ramane pana la confirmare, dar nu dupa order | finisaje si servicii comerciale | timpi aplicare, rework, scrap | partial |
| Electrica / LED | iluminare confirmata; lighting mode; configuratie LED minima; PSU/commercial config acceptata | configuratia comerciala si electrica inghetata | adevar tehnic electric complet | `LIGHTING_MODE_MISSING` | da | da | warning de watt reserve poate ramane daca nu schimba oferta | LED, PSU, eventual consumabile comerciale | cablaj, safety margins, timpi electrica | partial |
| Suport spate / Bare | doar daca suportul este activ sau suspectat: support required, support type, material/profile | suportul si relatia cu montajul inghetate | detalii tehnice suport complete | `SUPPORT_TYPE_MISSING` | da | da | warning daca suportul este optional dar inactiv explicit | bara/material/pachet suport daca suportul devine activ | structura, sudura, routing, capacitate | inactive with warning debt |
| Montaj | mounting system; template enabled/material daca este relevant; relatia cu suportul | sistem montaj inghetat comercial | constrangeri tehnice si install truth complete | `MOUNTING_SYSTEM_MISSING` | da | da | warnings de site constraints pot ramane pre-order doar daca nu schimba oferta | sablon si eventual pachet montaj | planning montaj, logistics, time | partial |
| Readiness oferta | toate componentele comerciale active complete; coverage pricing prezent; blockere truth rezolvate | confirmarile comerciale complete si inghetate | nu este componenta de executie, dar gate-ul de readiness trebuie sa fie fara ambiguitati | orice blocker de Product Truth sau `PRICING_REGISTRY_COVERAGE_MISSING` | da | n/a direct | warnings pot ramane doar daca nu schimba produsul sau oferta | depends on active components | none direct | blocked |

Boundary rules:

- `required_before_quote` defineste minimul sub care quote preview nu are voie sa se deblocheze;
- `required_before_order` elimina ambiguitatile comerciale si snapshot drift;
- `required_before_execution` elimina ambiguitatile tehnice care ar forta inventare downstream.

---

## Quote Preview Unlock Rules

### 1. Commercial readiness badge

- poate fi afisat in orice stare doar daca semnalizeaza clar `ready` versus `not ready`;
- Product Truth minim necesar pentru `ready`:
  - `LAYER_ROLES_CONFIRMED`;
  - componentele comerciale active au campurile minime completate;
  - coverage de pricing exista pentru componentele active;
- blockere care il opresc de la `ready`:
  - `LAYER_ROLES_INCOMPLETE`;
  - orice blocker de componenta activa;
  - `PRICING_REGISTRY_COVERAGE_MISSING`;
- warnings care pot ramane:
  - warnings de confidence din analyzer;
  - warnings de internal-only data missing;
  - warnings care nu schimba produsul sau formula comerciala;
- ce nu trebuie verificat inca:
  - timpi interni;
  - capacity planning;
  - ExecutionReality;
- ce nu trebuie calculat inca:
  - cost intern complet;
  - minute atelier;
- ce nu trebuie trimis la Pricing Registry:
  - probleme de layer role, target sau support decision.

### 2. Quote handoff preview

- Product Truth minim necesar:
  - `COMPONENT_TRUTH_COMPLETE_FOR_QUOTE`;
  - toate blockerele de Product Truth relevante sunt rezolvate;
- blockere care il opresc:
  - `LAYER_ROLES_INCOMPLETE`;
  - `PRINTED_ARTWORK_NOT_CONFIRMED`;
  - `SELECTED_FACE_LAYER_MISSING`;
  - `FACE_MATERIAL_MISSING`;
  - `FACE_THICKNESS_MISSING`;
  - `FINISH_TYPE_MISSING`;
  - `MOUNTING_SYSTEM_MISSING` cand componenta este activa;
  - `PRICING_REGISTRY_COVERAGE_MISSING` daca Product Truth este deja complet;
- warnings care pot ramane:
  - confidence warnings din SVG;
  - warning de support trigger mismatch ca debt de contract, atata timp cat semantica efectiva este inchisa;
- ce nu trebuie verificat inca:
  - truth tehnic complet pentru executie;
- ce nu trebuie calculat inca:
  - ExecutionPlan;
  - cost minute-based intern;
- ce nu trebuie trimis la Pricing Registry:
  - selected_face_layer lipsa;
  - artwork-only nedecis;
  - T06 versus T19E nedecis.

### 3. Pricing input preview

- Product Truth minim necesar:
  - acelasi minim ca pentru quote handoff preview;
  - toate inputurile comerciale relevante pentru componentele active trebuie sa fie determinate;
- blockere care il opresc:
  - orice blocker de Product Truth activ;
  - `PRICING_REGISTRY_COVERAGE_MISSING`;
- warnings care pot ramane:
  - only non-product-changing warnings;
- ce nu trebuie verificat inca:
  - date internal-only de capacitate;
- ce nu trebuie calculat inca:
  - estimated internal cost complet;
- ce nu trebuie trimis la Pricing Registry:
  - lipsuri de target, layer sau suport.

### 4. Material breakdown preview

- Product Truth minim necesar:
  - `COMPONENT_TRUTH_COMPLETE_FOR_QUOTE`;
  - toate material-role decisions comerciale sunt explicite;
- blockere care il opresc:
  - `LAYER_ROLES_INCOMPLETE`;
  - `FACE_MATERIAL_MISSING`;
  - `BACK_MATERIAL_MISSING`;
  - `FINISH_TYPE_MISSING`;
  - `T06_VS_T19E_NOT_DECIDED` cand cant finish este activ;
  - `PRICING_REGISTRY_COVERAGE_MISSING`;
- warnings care pot ramane:
  - warnings de confidence pe geometrii acceptate;
- ce nu trebuie verificat inca:
  - optimizare finala de waste;
- ce nu trebuie calculat inca:
  - decompozitie completa de cost intern;
- ce nu trebuie trimis la Pricing Registry:
  - selected_layer sau support decision lipsa.

### 5. Nesting preview

- Product Truth minim necesar:
  - geometriile relevante acceptate;
  - componentele de material active confirmate suficient pentru nesting preview util;
- blockere care il opresc:
  - `LAYER_ROLES_INCOMPLETE`;
  - `SELECTED_FACE_LAYER_MISSING`;
  - `FACE_MATERIAL_MISSING` cand nesting-ul depinde de materialul selectat;
  - `BACK_MATERIAL_MISSING` pentru nesting de spate;
- warnings care pot ramane:
  - warnings de perimeter confidence dupa acceptarea operatorului;
- ce nu trebuie verificat inca:
  - total cost intern;
- ce nu trebuie calculat inca:
  - quote comercial final doar din nesting;
- ce nu trebuie trimis la Pricing Registry:
  - orice ambiguitate de layer role sau target.

Mandatory rule:

- daca `layer_roles_incomplete`, atunci quote handoff, pricing input, material breakdown si nesting trebuie sa ramana blocate sau marcate clar `not ready`.

---

## Applied Scenario — gradi-curat.svg

- file: `gradi-curat.svg`
- route: `/intake-v6/IR-MR18L96M/operator`
- workspace: `IV6-BB8EE3F8`
- template: `TPL-VOLUMETRIC-LETTERS_v2`
- readiness: `layer_roles_incomplete`

### 1. Ce este deja suficient pentru `SVG_ANALYZED`?

- SVG-ul exista si este deja in workspace;
- geometria exista si este persistata;
- exista 6 grupuri detectate;
- exista 4 grupuri sugerate ca `face`;
- exista 2 grupuri sugerate ca `printed_artwork`;
- dimensiunile globale sunt disponibile;
- aria fetei si perimetrul de return sunt disponibile;
- warnings si confidence sunt disponibile.

Verdict:

- `gradi-curat.svg` este clar in starea `SVG_ANALYZED`.

### 2. Ce lipseste pentru `LAYER_ROLES_CONFIRMED`?

- confirmarea operatorului pentru toate cele 6 grupuri;
- inchiderea explicita a grupurilor artwork-only;
- eliminarea starii `confirmation_status = missing`;
- rezolvarea semantica a blockerului `unclassified_vector_artwork_requires_decision`.

### 3. Ce lipseste pentru `COMPONENT_TRUTH_COMPLETE_FOR_QUOTE`?

- layer role truth complet confirmat;
- selected face layer sau face layer refs explicite;
- material fata confirmat;
- grosime fata confirmata;
- finish target clarificat;
- finish type clarificat per suprafata activa;
- semantica T06 versus T19E daca finish-ul pe cant este activ;
- confirmarea ca logos raman artwork si nu produs;
- inchiderea semantica montaj vs suport unde este relevant.

### 4. Ce preview-uri trebuie sa ramana blocate?

- quote handoff preview trebuie sa ramana `not ready`;
- pricing input preview trebuie sa ramana blocat;
- material breakdown preview trebuie sa ramana blocat;
- nesting preview trebuie sa ramana blocat;
- commercial readiness badge nu trebuie sa arate `ready`.

### 5. Ce informatii NU trebuie trimise la Pricing Registry?

- selected face layer lipsa;
- operator confirmed face role lipsa;
- finish target lipsa;
- artwork-only nedecis;
- T06 versus T19E nedecis;
- suport nedecis;
- montaj nedecis.

### 6. Ce ar trebui sa vada operatorul in UI ca blocker?

- `LAYER_ROLES_INCOMPLETE`;
- `FACE_LAYER_NOT_CONFIRMED`;
- `PRINTED_ARTWORK_NOT_CONFIRMED`;
- orice lipsa de material/target/finish pentru componentele comerciale active;
- un mesaj explicit ca quote preview este blocat de Product Truth incomplet, nu de lipsa de pret.

### 7. Ce poate ramane warning?

- warnings de confidence din analyzer dupa acceptarea operatorului;
- `PERIMETER_CONFIDENCE_MEDIUM` dupa confirmare manuala;
- debt de contract pentru trigger mismatch suport, daca semantica efectiva a fost totusi inchisa corect in formular;
- lipsa unor date internal-only pentru CostEngine.

Concluzie explicita:

`gradi-curat.svg` nu este blocat de lipsa preturilor, ci de Product Truth incomplet.

---

## Pricing Boundary Confirmation

Pricing Registry poate bloca oferta doar cand lipsesc:

- preturi materiale;
- preturi servicii;
- rate sau configuratii comerciale;
- coverage pentru template;
- markup policies.

Pricing Registry NU trebuie sa primeasca si NU trebuie sa rezolve:

- `selected_face_layer` lipsa;
- `operator_confirmed_face_role` lipsa;
- `finish_target` lipsa;
- `selected_layer` lipsa;
- suport nedecis;
- `mounting_system` lipsa;
- `artwork-only` nedecis;
- `T06` vs `T19E` nedecis;
- fata real product vs decor nedecis.

Acestea sunt probleme de:

- Form System;
- Operator confirmation;
- Product Truth;
- component readiness.

Boundary rule:

- Pricing Registry rezolva lipsuri de pricing;
- formularul modular rezolva lipsuri de adevar;
- operatorul confirma adevarul;
- sistemul nu are voie sa confunde aceste frontiere.

---

## No Hourly Commercial Pricing Rule

Pretul comercial NU se calculeaza la ora sau minut.

Timpul poate exista doar pentru:

- CostEngine intern;
- estimare productie;
- capacitate;
- incarcare workcenter;
- analiza eficienta;
- ExecutionReality post-job;
- comparatie estimat versus real.

Nu valida formule comerciale hourly.

Daca exista in docs sau cod risc de pret comercial pe timp, marcheaza-l `ARCHITECTURE_RISK`.

Pentru acest slice read-only:

- nu a fost validata nicio formula comerciala hourly in suprafetele inspectate;
- nu s-a gasit motiv sa se converteasca datele de timp in pret client;
- minutele si timpii mentionati in ecosistem raman internal-only.

CommercialPriceProposal trebuie sa ramana pe reguli comerciale precum:

- material / mp;
- cant / ml;
- LED / bucata sau configuratie;
- surse / bucata;
- suport / ml sau pachet;
- montaj / pachet sau regula comerciala;
- finisaj / mp, ml sau bucata;
- complexitate;
- adaos comercial;
- minim de comanda;
- politici comerciale.

---

## Future Modular Form Contract Requirements

- fiecare componenta impune intrebarile ei;
- formularul nu este duplicat per produs;
- aceeasi componenta se refoloseste in variante diferite;
- `suggested role` este diferit vizual si logic de `confirmed role`;
- `fallback` sau `hydrated value` este diferit de `operator-confirmed value`;
- quote preview ramane blocat pana la Product Truth minim;
- order ramane blocat pana la confirmarile comerciale;
- execution ramane blocata pana la adevarul tehnic;
- Pricing Registry nu este folosit pentru a masca lipsa de adevar;
- CostEngine internal-only nu devine pret comercial.

Future-form rules:

- activarea componentelor conditionale trebuie sa fie derivata din Product Truth, nu din pricing fallback;
- blockerele trebuie sa fie afisate pe componenta si pe nivelul de readiness afectat;
- warnings nu trebuie sa ascunda blockerele;
- formularul trebuie sa stie clar ce este `required_before_quote`, `required_before_order` si `required_before_execution` pentru fiecare componenta activa.

---

## 9. Operational Conclusion

Intake V6 are voie sa deblocheze oferta numai cand Product Truth minim pentru quote este complet.

In cazul real `gradi-curat.svg`:

- geometria exista;
- sugestiile de layere exista;
- Pricing Registry este pregatit;
- dar sistemul trebuie sa ramana blocat pentru oferta deoarece `layer_roles_incomplete` inseamna Product Truth incomplet.

Acesta este boundary-ul corect pentru formularul modular viitor.
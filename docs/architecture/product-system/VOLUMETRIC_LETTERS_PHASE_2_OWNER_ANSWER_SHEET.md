# Volumetric Letters Phase 2 Owner Answer Sheet

**Date:** 2026-07-01  
**Status:** OWNER_ANSWER_REQUIRED  
**Scope:** Short owner-facing answer sheet, extracted from `VOLUMETRIC_LETTERS_PHASE_2_OWNER_DECISION_PACKET.md`  
**Roadmap phase:** Phase 2 - Modular Form component questions

---

## Purpose

Complete this sheet before Phase 2 runtime/UI implementation.

No new rules are introduced here. This is a short, fillable version of the owner decision packet.

---

## PH2-OD-01

**Area:** Global vs per group defaults

**Intrebarea pentru owner:** Which values may be global defaults, which must be per layer/group, and when can a group override the default?

**Recomandarea tehnica:** Allow global defaults only as starting values; require per-group confirmation for role, finish, Oracal color, artwork, cant exceptions, and any field that changes material/offer. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Global-only for simple jobs; per-group-only for all fields; hybrid default plus override.

**Impact daca alegem gresit:** Wrong materials, colors, printed artwork, or cant settings can be quoted and ordered incorrectly.

**Blocheaza quote/order/execution?** Quote: yes for role/finish/material fields. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing Intake V6 already has per-layer roles plus per-group face/cant/artwork controls and global fallbacks, but owner must validate when fallback values become quote-safe Product Truth and which fields must always be per-group.

**Raspuns owner:** Folosim model hybrid.

Formularul/template-ul poate oferi defaulturi globale/prefill pentru job, dar operatorul trebuie sa poata confirma sau modifica per layer/group orice valoare care afecteaza materialul, finisajul, culoarea, cantul, artwork-ul, iluminarea, suportul, montajul sau pretul.

Defaulturile globale nu devin Product Truth final pana cand sunt confirmate de operator.

Unde toate grupurile au aceeasi configuratie, se poate confirma global.

Unde un grup difera, override-ul per group este obligatoriu.

Quote blocker: da pentru valorile care afecteaza oferta. Order blocker: da. Execution blocker: da.

---

## PH2-OD-02

**Area:** Face / Plexiglas

**Intrebarea pentru owner:** Is default face material plexiglas opal, is default thickness 3 mm, when is 5 mm required, and must face material/thickness be confirmed before quote?

**Recomandarea tehnica:** Default proposal: plexiglas opal 3 mm as quote default, 5 mm only for owner-defined size/rigidity/use cases; require confirmation before quote. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Use 3 mm as fallback warning only; require material/thickness every time; add 5 mm based on width/height threshold; allow product variant to choose.

**Impact daca alegem gresit:** ProductDefinition or pricing would guess material/thickness; quote and execution may not match the product.

**Blocheaza quote/order/execution?** Quote: yes. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing form captures face finish, Oracal/print/no-finish choices, and face area, but does not expose explicit face material or plexiglas thickness policy.

**Raspuns owner:** Pentru moment, default operational ramane plexiglas opal 3 mm. Este clasicul folosit pentru litere volumetrice luminoase front-lit.

3 mm poate fi folosit ca prefill/default in formular, dar trebuie sa ramana vizibil si confirmabil de operator.

5 mm ramane exceptie ulterioara, selectabila sau conditionata de reguli viitoare de dimensiune/rigiditate.

Quote blocker: da. Order blocker: da. Execution blocker: da.

---

## PH2-OD-03

**Area:** Back / Forex

**Intrebarea pentru owner:** Is Forex 10 mm the default backing, should back bevel/sanfren be default yes or no, and when does backing become mandatory?

**Recomandarea tehnica:** Default proposal: Forex 10 mm, no sanfren, with explicit operator confirmation; sanfren only when owner/operator selects it or product rule requires it. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** No backing by default; Forex 10 mm with sanfren by default; backing decided by product variant; backing required only when illuminated.

**Impact daca alegem gresit:** Back material or bevel can be silently encoded in a select value and not treated as Product Truth.

**Blocheaza quote/order/execution?** Quote: yes. Order: yes. Execution: yes.

**Existing form status:** FOUND_IN_EXISTING_FORM

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing form already exposes Forex 10 mm backing with/without sanfren through `backing_mode`; owner mainly validates default, mandatory conditions, and blocker level.

**Raspuns owner:** Default operational pentru spate este Forex 10 mm.

By default este fara sanfren.

Sanfrenul trebuie sa poata fi selectat in formular daca se doreste sau daca produsul cere.

Forex 10 mm poate fi prefill/default, dar trebuie sa fie vizibil si confirmabil de operator.

Quote blocker: da. Order blocker: da. Execution blocker: da.

---

## PH2-OD-04

**Area:** Return / Cant

**Intrebarea pentru owner:** What is default cant depth, default cant color, allowed finish family, and when must cant be confirmed?

**Recomandarea tehnica:** Default proposal: template default 60 mm as starting value; require confirmation for quote; color/finish per group when not identical. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** 80 mm default; depth based on letter size; global cant only; per-group cant always; default white/black/aluminum/RAL/Oracal by product variant.

**Impact daca alegem gresit:** Wrong return depth or finish changes both price and manufacturing path.

**Blocheaza quote/order/execution?** Quote: yes. Order: yes. Execution: yes.

**Existing form status:** FOUND_IN_EXISTING_FORM

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing Review cards already expose cant depth, finish family, RAL/Oracal color, and Alb/Negru/Auriu/Argintiu options; owner validates defaults and required confirmation rules.

**Raspuns owner:** Se folosesc campurile existente din formular pentru return/cant.

Defaultul poate veni din template/formular, dar trebuie sa fie vizibil si confirmabil.

Adancimea cantului, culoarea cantului, RAL, Oracal/vopsit/alb/negru/aluminiu trebuie sa poata fi selectate.

Pentru litere volumetrice standard, cantul poate porni din defaultul template-ului, dar operatorul trebuie sa poata modifica valoarea.

Daca finisajul/cantul difera pe grupuri, sistemul trebuie sa permita configurare per layer/group.

Quote blocker: da, cand produsul are cant/return activ. Order blocker: da. Execution blocker: da.

---

## PH2-OD-05

**Area:** Finish / Oracal / Print / Laminare

**Intrebarea pentru owner:** Which finish types are allowed before quote: no finish, Oracal 641/651/8500, print laminated, painting; must Oracal color, roll width, print required, and lamination required be explicit?

**Recomandarea tehnica:** Default proposal: finish type and target required before quote; Oracal color required when Oracal is selected; print_required and lamination_required explicit for artwork/print; roll width warning/conditional unless owner marks it commercial. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Roll width required for quote; roll width internal-only; print always implies lamination; print and lamination separate; allow no finish as explicit confirmed choice.

**Impact daca alegem gresit:** Quote may promise wrong material/service or miss print/lamination cost.

**Blocheaza quote/order/execution?** Quote: yes for finish type/target/color/print policy; conditional for roll width. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing form already includes Oracal 641/651/8500, Oracal color, roll width, and Print + laminare, but print_required, lamination_required, finish target, and T06/T19E are not explicit enough for Product Truth.

**Raspuns owner:** Se folosesc optiunile existente in formular pentru Oracal si finisaje:

- Oracal 641;
- Oracal 651;
- Oracal 8500;
- culoare Oracal;
- latime rola;
- print;
- laminare;
- finish target fata/cant/artwork.

Acestea sunt suficiente pentru oferta daca sunt selectate si confirmate de operator.

Print_required si lamination_required trebuie pastrate ca decizii separate; printul nu presupune automat laminare.

Quote blocker: da, daca finisajul/printul/laminarea afecteaza pretul. Order blocker: da. Execution blocker: da.

---

## PH2-OD-06

**Area:** Artwork / Printed artwork

**Intrebarea pentru owner:** Is `printed_artwork` automatically print, can it be artwork-only, can it be ignored, how is target decided, and what should `logo stanga` / `logo dreapta` be in `gradi-curat.svg`?

**Recomandarea tehnica:** Default proposal: `printed_artwork` is a suggestion, not automatic final print; `logo stanga` and `logo dreapta` should default to printed artwork suggestions requiring operator confirmation. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Always print; require target selection; allow artwork-only; allow ignored only by explicit operator confirmation; map to face/cant target when applied to product.

**Impact daca alegem gresit:** Artwork can be priced, produced, or ignored incorrectly.

**Blocheaza quote/order/execution?** Quote: yes. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing role table and artwork cards already support printed_artwork/logo/ignore, artwork confirmation, and transparency; owner validates policy for automatic print, artwork-only, ignored layers, and target semantics.

**Raspuns owner:** `printed_artwork` este sugestie, nu print final automat.

Pentru `logo stanga` / `logo dreapta` din `gradi-curat.svg`, sistemul poate sugera `printed_artwork`, dar operatorul trebuie sa confirme decizia:

- printat/aplicat;
- artwork-only;
- ignored.

Artwork-ul nu trebuie produs, ofertat sau ignorat fara confirmare operator.

Quote blocker: da. Order blocker: da. Execution blocker: da.

---

## PH2-OD-07

**Area:** Finish target

**Intrebarea pentru owner:** Can target be face, cant, artwork, all, or another target, how is it expressed in UI, and when does missing target block quote?

**Recomandarea tehnica:** Default proposal: require explicit target before quote for any active finish; UI should express target in component cards using owner-friendly labels: Fata, Cant, Artwork, Spate, All when policy allows. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Target embedded in each card; single target selector per finish row; no `all`; allow `all` only as shortcut expanding to explicit targets.

**Impact daca alegem gresit:** Pricing Registry or ProductDefinition may be asked to repair missing semantics.

**Blocheaza quote/order/execution?** Quote: yes. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing UI implies target through Face/Cant/Artwork zones, but no explicit canonical `finish_target` field or `all` policy was found.

**Raspuns owner:** Finish target trebuie sa fie explicit si vizibil in UI.

Operatorul trebuie sa vada pe fiecare layer/grup ce finisaj este selectat pentru fata si ce finisaj este selectat pentru cant.

Exemplu: layerul `maria` poate avea finisaj pe fata si finisaj diferit pe cant.

Formularul trebuie sa pastreze logica per layer/group acolo unde finisajul difera.

Quote blocker: da, daca finisajul afecteaza pretul. Order blocker: da. Execution blocker: da.

---

## PH2-OD-08

**Area:** T06 vs T19E

**Intrebarea pentru owner:** Should UI ask T06 as autocolant pe cant inainte de modelare and T19E as folie dupa corp format, when is this decided, and what does it block?

**Recomandarea tehnica:** Default proposal: ask only when foil/print interacts with cant/body; require before quote if it changes commercial scope, otherwise before order at latest; use plain labels plus code. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Always ask when Oracal on cant; derive from finish target; ask later at order; hide codes and show process labels only.

**Impact daca alegem gresit:** Wrong process branch can alter materials, sequence, quote, and execution plan later.

**Blocheaza quote/order/execution?** Quote: yes when active/commercial. Order: yes. Execution: yes.

**Existing form status:** MISSING

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** No clear owner-facing T06/T19E form control was found; this remains a real owner process decision.

**Raspuns owner:** T06/T19E nu trebuie tratat acum ca intrebare comerciala principala in oferta.

Diferenta trebuie sa apara in sistemul de taskuri / execution flow.

Regula de executie: taskul de aplicare folie nu trebuie sa se activeze pana cand procesul anterior corect nu este terminat.

Pentru T19E:

- aplicarea foliei se face dupa ce corpul este format/asamblat;
- taskul de aplicare folie trebuie blocat pana cand operatorul confirma pe telefon terminarea ansamblarii/corpului.

Pentru T06:

- aplicarea foliei/autocolantului pe cant se face inainte de modelare, daca procesul cere asta.

In Phase 2, formularul pastreaza doar informatia de finisaj/target. Activarea taskurilor T06/T19E este pentru Task Graph / ExecutionPlan later, nu pentru acum.

Quote blocker: doar daca procesul schimba pretul comercial. Order blocker: da, daca metoda trebuie inghetata. Execution blocker: da.

---

## PH2-OD-09

**Area:** Lighting / LED

**Intrebarea pentru owner:** What is default lighting mode, LED density/config default, PSU default, PSU placement policy, and which cable fields are quote vs execution?

**Recomandarea tehnica:** Default proposal: illuminated product defaults to LED modules with neutral light only as starting value; confirm lighting mode and PSU class before quote; cable lengths/types and PSU placement before order/execution unless owner includes them in quote. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Non-illuminated default; LED strip default; front-lit/back-lit variants; cables required before quote; PSU placement required before quote.

**Impact daca alegem gresit:** Quote may omit electrical scope or execution may invent cabling/PSU placement.

**Blocheaza quote/order/execution?** Quote: yes for lighting mode and commercial PSU scope; conditional for cables. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing form already has illuminated toggle, LED modules/strip, light color, wattage, emblem mode, derived watts, and PSU class; cable fields and PSU placement policy are missing.

**Raspuns owner:** In oferta se include automat:

- 1 m cablu 2 x 0.75 pentru litere;
- 5 m cablu 2 x 1.5 pentru alimentare finala 220V.

Acestea sunt defaulturi comerciale incluse in oferta.

Cabluri suplimentare, trasee speciale, pozitie sursa, cerinte de santier sau montaj special se clarifica ulterior, in order/execution, sau in oferta daca clientul cere montaj/conditii speciale.

Quote blocker: nu pentru defaulturile incluse; da daca exista cerinte electrice speciale sau montaj inclus. Order blocker: da. Execution blocker: da.

---

## PH2-OD-10

**Area:** Support / Bare

**Intrebarea pentru owner:** Is rear support default yes/no, when use aluminum bars/structure/no support, when does support affect offer, and when execution?

**Recomandarea tehnica:** Default proposal: default support_required=false for direct_wall, but require explicit confirmation when geometry, mounting, or owner policy suspects support; support affects quote when commercial material/labor is included. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Always ask support; derive fully from mounting; support required for large dimensions; aluminum bars default; steel/structure default; external support prep.

**Impact daca alegem gresit:** Support may be omitted from offer or invented during execution.

**Blocheaza quote/order/execution?** Quote: conditional. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing mounting controls include steel/aluminum bars and bar profile, but support is not a first-class Product Truth object with required/type/material/position/internal prep fields.

**Raspuns owner:** Suportul/barele sunt optionale si trebuie intrebate in formular daca nu se detecteaza clar in layerele SVG.

Daca SVG-ul contine layer/grup care indica suport/bare, formularul trebuie sa il afiseze ca detectat/sugerat si sa ceara confirmare.

Daca nu se detecteaza, operatorul trebuie sa poata selecta manual:

- fara suport;
- cu bare aluminiu;
- cu alta structura/suport.

Quote blocker: conditional, daca suportul afecteaza materialul/manopera/pretul. Order blocker: da. Execution blocker: da.

---

## PH2-OD-11

**Area:** Mounting

**Intrebarea pentru owner:** What is default mounting system, is installation included or external, how is mounting surface/area handled, is template/sablon required, and what blocks quote?

**Recomandarea tehnica:** Default proposal: direct_wall as starting default only; require operator confirmation before quote; template/sablon enabled only when owner policy says it is part of offer; installation included/external must be explicit. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Always include template; template optional; montaj external by default; montaj included by default; require site surface before quote; site details only before order.

**Impact daca alegem gresit:** Offer may include/exclude mounting or support incorrectly.

**Blocheaza quote/order/execution?** Quote: yes for mounting system and included/external scope. Order: yes. Execution: yes.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing form already captures mounting system, template enabled/area/material, and bar profile; owner must decide installation included/external and site/surface blocker policy.

**Raspuns owner:** Montajul trebuie sa fie explicit in oferta:

- fara montaj;
- montaj inclus;
- montaj extern;
- de decis.

Quote blocker: da, pentru montaj inclus/extern. Order blocker: da. Execution blocker: da.

---

## PH2-OD-12

**Area:** Pricing / Cost boundary

**Intrebarea pentru owner:** Which questions must never go to Pricing Registry, what remains CostEngine internal-only, and how do we avoid hour/minute pricing?

**Recomandarea tehnica:** Default proposal: Pricing Registry only answers coverage/prices after Product Truth; CostEngine keeps minutes, rates, capacity, waste, and actuals internal; commercial pricing uses unit/product rules. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Allow owner acknowledgement when internal cost incomplete; stricter block when commercial rule missing; separate CommercialPriceProposal from EstimatedInternalCost.

**Impact daca alegem gresit:** Product Truth blockers may be mislabeled as pricing issues, or internal time may become client price.

**Blocheaza quote/order/execution?** Quote: yes only for missing commercial price coverage after truth exists. Order: no direct, except snapshot readiness. Execution: no direct, except internal planning readiness.

**Existing form status:** FOUND_IN_EXISTING_FORM

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing architecture/docs and Review direction already keep Pricing Registry after Product Truth and CostEngine internal-only; owner validates this boundary rather than inventing form answers.

**Raspuns owner:** Pricing Registry nu decide Product Truth.

Pricing Registry primeste Product Truth complet si verifica/acopera preturi/reguli comerciale.

Nu trimitem la Pricing Registry intrebari precum role, finish_target, support, mounting, T06/T19E, artwork decision, print_required, lamination_required sau configuratie tehnica neconfirmata.

CommercialPriceProposal foloseste Product Truth confirmat si reguli comerciale.

CostEngine ramane internal-only pentru timpi, minute, capacitate, utilaje, manopera interna, waste, randament si ExecutionReality.

Pretul comercial nu se calculeaza la ora/minut.

Quote blocker: da doar cand Product Truth este complet, dar lipseste regula/coverage comerciala. Order blocker: nu direct, exceptand snapshot readiness. Execution blocker: nu direct, exceptand planning/internal readiness.

---

## PH2-OD-13

**Area:** Quote / Order / Execution classification

**Intrebarea pentru owner:** For each decision, is it required for quote, required for order, required for execution, optional, or warning only?

**Recomandarea tehnica:** Default proposal: quote requires commercial Product Truth; order requires frozen commercial decisions and non-ambiguous configs; execution requires full technical details; internal-only data is warning unless owner says otherwise. OWNER_DECISION_REQUIRED.

**Optiuni posibile:** Make more fields quote blockers; defer more fields to order; classify cables/site constraints as execution only; use owner acknowledgement warnings.

**Impact daca alegem gresit:** Quote can unlock too early or stay blocked by internal-only data.

**Blocheaza quote/order/execution?** Quote: yes for commercial truth. Order: yes for frozen order truth. Execution: yes for technical execution truth.

**Existing form status:** PARTIAL

**Owner action needed:** OWNER_APPROVED_RULE_APPLIED

**Reason:** Existing readiness docs and UI blockers provide direction, but the final per-field quote/order/execution taxonomy is not fully encoded and needs owner approval.

**Raspuns owner:** Folosim regula:

Quote blocker = orice afecteaza pretul, configuratia comerciala sau ce promitem clientului.

Order blocker = orice trebuie inghetat inainte de comanda ca sa nu se schimbe produsul vandut.

Execution blocker = orice trebuie stiut ca sa producem, asamblam, aplicam folie, cablam, pregatim surse sau montam corect.

Internal-only = timp, minute, capacitate, pontaj, utilaje, cost intern, randament, statistica si realitate productie.

Regula ferma: pretul comercial nu se calculeaza la ora/minut. Orele/minutele raman pentru CostEngine intern, capacitate si ExecutionReality.

---

## Owner Decision Reduction Summary

### A. Owner-approved in this patch

- PH2-OD-01 Global vs per group defaults: hybrid model approved; global defaults/prefill require operator confirmation and per-group overrides when groups differ.
- PH2-OD-02 Face / Plexiglas: plexiglas opal 3 mm remains operational default; 5 mm remains later exception; visible operator confirmation required.
- PH2-OD-03 Back / Forex: Forex 10 mm without sanfren is default; sanfren remains selectable; visible operator confirmation required.
- PH2-OD-04 Return / Cant: existing return/cant fields are approved; defaults may come from template/form but must remain visible, confirmable, and per-group overrideable.
- PH2-OD-05 Finish / Oracal / Print / Laminare: existing Oracal/print/lamination/target controls are sufficient for offer when selected and confirmed; print and lamination remain separate decisions.
- PH2-OD-06 Artwork / Printed artwork: printed_artwork is suggestion only; logo stanga/logo dreapta require operator confirmation as print/applied, artwork-only, or ignored.
- PH2-OD-07 Finish target: target must be explicit and visible per layer/group, especially when face and cant finishes differ.
- PH2-OD-08 T06 / T19E: not a primary commercial offer question now; execution/task activation belongs later to Task Graph / ExecutionPlan.
- PH2-OD-09 Lighting / LED / Cabluri / Surse: default included cables are 1 m 2 x 0.75 for letters and 5 m 2 x 1.5 for final 220V feed; special electrical/site needs are clarified later or in offer when requested.
- PH2-OD-10 Support / Bare: support/bars are optional; detect/suggest from SVG when possible and allow manual selection when not detected.
- PH2-OD-11 Mounting: offer must explicitly classify mounting as no mounting, included, external, or to decide.
- PH2-OD-12 Pricing / Cost boundary: Pricing Registry does not decide Product Truth; CommercialPriceProposal uses confirmed truth; CostEngine remains internal-only.
- PH2-OD-13 Quote / Order / Execution classification: quote/order/execution/internal-only rules are owner-approved; commercial price is not hour/minute based.

### B. Existing form policy still awaiting owner answer

- None. All PH2-OD-01 through PH2-OD-13 owner answers are now captured in this sheet.

### C. Implementation follow-up implied by owner answers

- PH2-OD-01 Global vs per group defaults: support global confirmation only when all groups share the same configuration; require per-group override when any group differs.
- PH2-OD-02 Face / Plexiglas: make plexiglas opal 3 mm visible/confirmable and keep 5 mm as later exception.
- PH2-OD-04 Return / Cant: keep return/cant fields visible and confirmable; allow per-layer/group configuration for differing cant/finish.
- PH2-OD-05 Finish / Oracal / Print / Laminare: preserve separate print_required and lamination_required decisions; print does not imply lamination.
- PH2-OD-06 Artwork / Printed artwork: require operator confirmation before producing, offering, or ignoring artwork.
- PH2-OD-07 Finish target: make face/cant/artwork target explicit per layer/group.
- PH2-OD-08 T06 / T19E: defer task activation details to Task Graph / ExecutionPlan later; Phase 2 keeps finish/target info only.
- PH2-OD-09 Lighting / LED: include default commercial cables; clarify special electrical/site requirements later or in offer when requested.
- PH2-OD-10 Support / Bare: ask/select support when SVG detection does not clearly answer.
- PH2-OD-11 Mounting: make mounting offer scope explicit.
- PH2-OD-12 Pricing / Cost boundary: keep Product Truth questions out of Pricing Registry and keep CostEngine internal-only.
- PH2-OD-13 Quote / Order / Execution classification: apply owner-approved blocker/internal-only rules.

### D. Still open / not owner-approved in this patch

- None.

---

## Roadmap Checkpoint

- Roadmap phase: Phase 2 - Modular Form component questions
- Roadmap status of this task: NEXT / owner answers patch
- Roadmap implementation progress: 8/100%
- Roadmap alignment score: 99/100%
- Cat sunt in directia stabilita: 98/100%
- Owner GO required next: YES

---

## Scope Confirmation

This answer sheet does not implement or authorize:

- frontend changes;
- backend changes;
- payload changes;
- analyzer changes;
- pricing changes;
- ProductTruth runtime changes;
- ProductDefinition changes;
- ProductSystem runtime changes;
- ProductAggregate changes;
- ExecutionPlan changes;
- DB/schema/seeds changes;
- quote/order/execution creation;
- materialization;
- Employee Mobile.

# Decision — Litere volumetrice × ACM casetat: template-uri curate + contract + Composer

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Status** | `ACCEPTED` — PS Litere/ACM closed · contract ACCEPT · Finish/Composer/CPP v1 shipped; **ACM = offerable root** (Q2) |
| **Owner intent** | ACM rămâne **root ofertabil** (panou / vinyl / decorativ / litere); Litere pe ACM = composition, nu demote ACM |
| **Root** | `C:\w\psiso` |
| **Branch context** | `feature/product-system-active-path-isolation-v1` |
| **Related UI evidence** | Product System V2 workspace: Structură produs aliniată cu editorul clasic (Litere); ACM separat în rail |
| **Forbidden until explicit GO** | DB/API/pricing/PD/Aggregate/Execution behavior changes; Composer UI; mutations to frozen operational truth |

---

## 1. Purpose

Lock the **product direction** agreed in session:

1. Each Product Template shows **only its own structure** (no foreign variants mixed in).
2. **Litere volumetrice** and **ACM casetat** stay separate templates.
3. The link between them is a **compatibility / assembly contract**, not a merged catalog blob.
4. A future **Composer** lets the operator pick template A → see compatible templates → attach ACM → form a **composite** product.
5. The physical assembly sequence (șablon de poziționare → montaj) is the **semantic content** of that contract.
6. **Unity (2026-07-23 AMEND):** montaj pe ACM = același spine ca pe bare / alte suprafețe (memoriu T12–T18); contractul ACM e **surface delta** (șablon vinyl + 20 EUR/mp, electric în carcasă, pack o dată) — nu un al doilea model de montaj. Cabluri rămân PH2-OD-09.
7. **Connection prices (2026-07-23):** foaie PS `structure/conexiune-litere-acm-preturi`. Șablon **20 EUR/mp OWNER_LOCKED**; restul (8 / 35 / 6 / 8 / 12 / 10+min15) **OWNER_VERIFIED_COHERENT** — owner: „par coerente momentan”.

This document is for **study and advice**, not for coding yet.

---

## 2. Decision summary (one paragraph)

**Litere** and **ACM casetat** are clean, separate Product Templates. Compatibility is declared by contract. The operator (later) composes them in a Composer. The contract’s meaning is the real workshop sequence: finished ACM (structure + vinyl if needed) receives a **positioning template (șablon)**; letter **Forex backs with LEDs and jumper cables** are fixed onto ACM using the șablon as guide; then the **plexiglass body + return/cant** is fixed onto those backs; finally **electrical ties and transformer** complete the product.

---

## 3. Locked rules

### 3.1 Template purity

| Product Template | Shows | Does **not** show as nucleus |
|------------------|-------|------------------------------|
| `TPL-VOLUMETRIC-LETTERS_v2` (Litere volumetrice) | Letter structure only (vizual față, volum aluminiu, capac spate, sistem LED; Finisaj produs ascuns — finisaje pe Față/Volum) | ACM variants, foreign mount catalogs, shared-contract duplicates as “extra modules” |
| ACM casetat (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` or successor offerable root) | ACM structure / what ACM needs | Letter face/cant/LED as if they were ACM parts |

**Rule:** No “15 supports dumped into Letters nucleus.” Optional mounts are either (a) out of Letters nucleus, or (b) attached later via Composer + contract.

### 3.2 Contract (not merge)

Between Letters and ACM there is a **contract**, not a fused template.

The contract answers:

- May Letters attach to this ACM? (compatibility)
- In what **order** must assembly happen? (dependency)
- What is the **interface piece**? → **Șablon de poziționare**
- Who owns which materials/truth? (ACM vinyl vs letter LED vs interface șablon)

### 3.3 Composer (future — direction only)

Operator flow (not built yet):

1. Choose **first** Product Template (e.g. Litere).
2. System lists **compatible** templates (e.g. ACM casetat).
3. Operator selects ACM casetat.
4. Result = **composite**: Letters + ACM under the contract.

**Composer ≠ Pricing ≠ Intake ≠ Execution.**  
Composer defines *what product assembly is*. Offer/cost/execution consume a composed truth later.

### 3.4 Commercial boundary (unchanged)

- Product System does **not** invent client offer price.
- A commercial offer may later price a **composite** (one freeze / one commercial root hierarchy), not “blindly glue two unrelated template prices.”
- Multi-line customer quotes (two independent roots on one paper) remain a **commercial document** concern, separate from this Composer contract.

---

## 4. Assembly contract — owner narrative (canonical meaning)

Source: owner description, 2026-07-23. This is the **intended semantic** of the Letters↔ACM contract.

### 4.1 Preconditions

- **ACM casetat** is finished through mounting accessories (ACM principal tasks 1–9), with **applied vinyl/autocolant when applicable**. On composition: **no ACM pack yet**.
- **Letters** parts exist as their own structure (face, return/cant, Forex back, LED, finishes) — prepared as letter modules, not mixed into ACM template UI. Body attaches **after** Forex is on bond.

### 4.2 Sequence (ordered) — OWNER_CONFIRMED 2026-07-23 evening

1. **Finalize Alucobond casetat** (tasks 1–9) — **without packaging**.
2. **Șablon process on bond** (guiding interface). Commercial: **one** process at **20 EUR/mp** bundling material + cutter/plotter + transfer + apply.  
   Qty = **outbox of volumetric letters as one integral layer** — not sum of per-letter boxes.
3. **Forex backs** (LEDs + jumper cables already on them) fastened onto ACM with autoforante, using the șablon.
4. **Electrical work inside the ACM cassette** + transformer/PSU tie-in.
5. **Supply cable 5 m @ 220V**.
6. **Light test**.
7. **Plexiglass body + return/cant** fastened onto Forex already on ACM — fine screws painted to cant/volume colour.
8. **Pack composite assembly** (single pack at end).

Canonical draft: `docs/architecture/product-system/LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.md`.  
Teaching SoT: `frontend/src/features/product-system/lettersAcmCompositionTaskOrder.ts`.

### 4.3 Implied ownership split

| Piece / concern | Owning side (direction) |
|-----------------|-------------------------|
| ACM structure, cassette, vinyl on ACM | ACM template |
| Letter face (plexiglass visual), return/cant, Forex back, LED modules on letter | Letters template |
| Positioning șablon (Litere-owned process @ 20 EUR/mp on letters-layer outbox) + ordered assembly | **Contract / Composer interface** |
| Electric inside ACM + PSU + 5 m cable + light test + body attach + final pack | Assembly sequence (contract → later Execution / Intake materialization) |

### 4.4 What the contract is *not*

- Not “ACM is just another row in Letters Module produs grid.”
- Not “two offer prices added without structure.”
- Not silent AI confirmation of Product Truth.
- Not Execution authority living inside Product System UI chrome.

---

## 5. Mental model (for advisors)

```text
[Product Template: Litere]     [Product Template: ACM casetat]
        |                                 |
        |         COMPATIBILITY CONTRACT  |
        |    (șablon poziționare + order) |
        +---------------┬-----------------+
                        |
                        v
              [COMPOSITE ASSEMBLY]
              Litere mounted on ACM
                        |
          (later) Offer / Cost / Execution channels
```

**Spine stays Product System-owned:**  
Product Template → Module produs / Structură → Product Compiler → Pregătire.  
Ofertă / Cost / Execution remain **other systems** (links / later consumption).

---

## 6. Alignment with current UI state (as of this decision)

Already accepted in product conversation (implementation may lag; this is direction):

- Letters V2 **Structură produs** reads as numbered stages: Vizual față → Volum aluminiu → Capac spate → Sistem LED (**Finisaj produs** ascuns; finisaje pe Față/Volum — `LETTERS_PS_UI_CLOSED`).
- Shared-contract diagnostics and laboratory editor are **secondary**, not the operator story.
- ACM appears as its **own** template story, not as duplicate English modules inside Letters.
- Optional supports currently visible under Letters are **transitional**; long-term, ACM attachment is via **contract + Composer**, not nucleus pollution.

---

## 7. Non-goals (this decision)

| Non-goal | Why |
|----------|-----|
| Implement Composer UI now | Owner wants study first |
| Rewrite CostEngine / Pricing / PD / Aggregate | Out of boundary |
| Merge Letters + ACM into one Product Template | Violates purity rule |
| Put Oferta as a Product System spine step | Ownership violation |
| Auto-confirm Product Truth from Analyzer/AI | Governance rule |

---

## 8. Open questions for owner + AI advisor

Record answers before build GO:

1. Is the **șablon de poziționare** a first-class Module produs / component under Letters, under ACM, or a **contract-only** artifact?  
   **ANSWERED (2026-07-23):** Litere-owned **contract interface** (not ACM nucleus card). On ACM composition: transparent vinyl + transfer; commercial = **one process 20 EUR/mp** on **letters-layer outbox (integral)**, not per-piece. Teaching: `lettersAcmCompositionSablonProcess.ts`. Task id remains conceptually `sablon_montaj` / composition process — Intake wiring GO separate.
2. Is ACM already an **offerable root**, or only a linked support until Composer exists?  
   **ANSWERED (2026-07-23):** **Yes — ACM (Alucobond casetat) is an offerable Product Template root** in its own right. Not only a Letters support. Owner uses: panou simplu + autocolant; alte modele de litere pe el; sau pur decorativ / panel-only (`applied_content=none`). Letters-on-ACM remains a **composition** via contract/Composer; it does not demote ACM to a non-root accessory.
3. Does one Intake/workspace freeze **one composite**, or can a quote still hold multiple composites as commercial lines?  
   **ANSWERED (2026-07-23):** **Multiple products may appear on a commercial offer as separate lines / separate roots** — each offered separately. A freeze / Product Truth workspace stays **one product (or one composite) at a time**; do **not** merge unrelated products into one freeze. Multi-panel ACM segmented assembly ≠ multiple commercial products (still one ACM product physically). Owner: „pot avea mai multe produse dar ofertate separat”.
3b. **Commercial / invoice name for Letters-on-ACM composite** — **ANSWERED (2026-07-23):**  
   The composition (Alucobond casetat + litere aplicate) is a **final product** closed on the invoice as **one line name**, not two template names glued.  
   **Denumire owner:** `Litere volumetrice premontate pe suport de Alucobond` + **cotă** (cm sau mm — aceeași unitate pe document).  
   Intern: tot composition Litere↔ACM (contract + prețuri conexiune); pe factură/ofertă clientul vede denumirea de mai sus, nu „2 template-uri”.
4. Where do **transformer / PSU** truth fields live when the assembly is Letters+ACM vs Letters alone (direct wall)?  
   **Partial (sequence):** on ACM composition, electric + PSU + 5 m cable + light test happen **inside/after Forex on bond**, **before** body attach (§4.2). Field ownership schema still open.
5. What is the minimal **compatibility matrix** v1 (Letters ↔ ACM only, or also premount / other mounts)?  
   **ANSWERED for v1:** Letters ↔ Alucobond casetat only (`LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.md`).

---

## 9. Execution order (owner ACCEPTED — 2026-07-23; amended evening)

**ACM PS UI settled** (`ACM_PS_UI_CLOSED` 2026-07-23). **Contract v1 ACCEPTED** (`LETTERS_ACM_COMPATIBILITY_CONTRACT_V1_ACCEPTED` 2026-07-23).

1. ~~Doc freeze ACCEPTED~~ — done.
2. ~~**UI Litere volumetrice**~~ — **`LETTERS_PS_UI_CLOSED`** (owner ACCEPT 2026-07-23):  
   - Structură produs = doar litere (fără ACM/premount în nucleu).  
   - Patru carduri detaliu: Vizual față · Volum aluminiu · Capac spate · Sistem LED (formule, CNC 2/3|5, LED litere, ordine taskuri principale).  
   - **Amendament ACCEPT:** pasul **Finisaj produs** rămâne **ascuns** pe hartă; finisajele trăiesc pe componente — **Față** (Oracal/print) și **Volum** (cant stock/Oracal/RAL). Nu card Finisaj separat; nu „sub pasul Finisaj” ca rând nucleu.  
   - Out of scope pentru această închidere: emblemă, montaj, procesor dinamic finisaj→taskuri (Intake V6), Aggregate/PD pe carduri, Composer.  
   - Evidence: `docs/worklog/realignment/2026-07-23_letters_ps_structure_ui_closed.md`.
3. ~~**UI ACM casetat (display v2)**~~ — **`ACM_PS_UI_CLOSED`** (owner ACCEPT 2026-07-23):  
   - Nucleu **2** carduri: **Corp casetat** · **Structură metalică**; titlu **Alucobond casetat**.  
   - Owner la ACCEPT: finisaje **obligatoriu în Intake**; CNC seed ops **nu** prioritar — contează **grafica CNC** (ArtCAM Cut outside + V-groove along line); qty Decupare pe material desfășurat = da; SKU profil cadru = **DEFERRED confirmat**; contract path = ACCEPT.  
   - Evidence: `2026-07-23_acm_ps_structure_ui_closed.md` + `2026-07-23_acm_ps_structure_corp_frame_ui_v2.md`.
3b. ~~**Finish Contract / finisaje ACM în Intake**~~ — **v1 shipped** (AcmPanel `shell_finish`; face≠volume; 651/print+lam; strategie folie; confirm). Evidence: `build__acm_shell_finish_contract_intake_v1.md`. CostEngine still gap.
4. ~~**Contract schema**~~ — **`LETTERS_ACM_COMPATIBILITY_CONTRACT_V1_ACCEPTED`**.
5. ~~**Composer IA mock**~~ — **v1 shipped** (`structure/composer-litere-acm`). Evidence: `build__letters_acm_composer_ia_mock_v1.md`.
6. ~~Intake/CPP GO for șablon **20 EUR/mp** + connection lines~~ — **v1 shipped** (`letters_acm_conn_*` in CPP; legacy sablon suppressed under composition). Evidence: `build__letters_acm_composition_commercial_cpp_v1.md`. CostEngine BOM path still historic.
7. Broader implementation GO with narrow build boundary (EIC mirror / outbox Intake field UI).

---

## 10. Meta-lesson (keep)

**UI is owner reality.** If the owner cannot see the model on screen, the agent cannot guess it in chat. Product System (and sibling operator surfaces) must make structure and boundaries self-evident; explanations are secondary. Captured as Cursor rule: `.cursor/rules/ui-is-owner-reality.mdc`.

---

## 11. Cum am ajuns aici — firul discuției (2026-07-23)

Această secțiune există ca **advisorul / ownerul să înțeleagă contextul**, nu doar decizia finală. Nu e jurnal de commit; e traseul de gândire.

### 11.1 De unde am pornit

Contextul mai larg al zilei / sesiunii:

- Product System trecea printr-un **rebuild de workspace (V2)** după ce ownerul respinsese UI „vopsit pe vechi” (blank ≠ temă dark).
- Primarul trebuia să fie: **Product Template → Module produs → Product Compiler → Pregătire**, cu Ofertă / Cost / Execution pe canale separate.
- Catalogul vechi rămânea izolat (`?ps_legacy=1`), nu ca poveste principală.
- Ownerul a cerut claritate: **să înțeleagă ecranul**, nu să asculte explicații de agent.

### 11.2 Problema #1 — headerul era un morman

**Simptom (owner):** pe Product System nou apăreau de mai multe ori aceleași titluri / același lanț de pași („Product System”, „Workspace”, „Workspace produs”, spine repetat).

**Cauză găsită:** trei layere de chrome lipite:
1. shell (`ProductSystemLayout`) — titlu + subtitle + tab Workspace  
2. pagina (`ProductSystem`) — toolbar tip catalog (Workspace + Live DB + reload/info/⋯)  
3. V2 workspace — încă un titlu + același subtitle + spine  

**Învățământ:** ce „pare header nou” poate fi **rest din rundele trecute**. UI-ul trebuie curățat ca o singură poveste, nu stivuit.

**Acțiune în sesiune:** colaps header — un titlu, spine o dată, utilitare fără al doilea titlu.

### 11.3 Problema #2 — aglomerația de module la Litere

**Simptom (owner):** la selectarea Litere volumetrice, ~13 carduri; jumătate RO („Față literă”…), jumătate EN („Volumetric face”…) — părea că litera are zeci de piese.

**Cauză găsită:** UI-ul lipea în același grid:
- `composition_modules` = rețeta produsului  
- `shared_component_contracts` = strat de audit pe **aceleași** module  

Plus suporturi opționale (premount, ACM) ca egale cu nucleul.

**Întrebarea ownerului (esențială):**  
*Dacă mai apar 10 suporturi / Halou cu 15 combinații — ce facem? Unde e locul?*

**Răspuns de model (înainte de Composer):**
- nucleu produs ≠ opțiuni ≠ contracte diagnostic  
- variante de produs = template-uri / profiluri separate, nu 15 carduri în același detal  

**Acțiune în sesiune:** partiționare afișare (nucleu / opțiuni / contracte în Admin). Apoi ownerul a spus adevărul dur: **dacă doar agentul explică și el nu vede, direcția o ține cine?**

### 11.4 Problema #3 — „nu pare să avem viitor” + gruparea în ofertă

**Simptom (owner):** dacă nu putem „grupa 2 Product Template-uri într-o ofertă de preț”, pare blocaj de produs.

**Clarificare de model:**
- Product System = **o rețetă / un root** pe ecranul de produs  
- Oferta = **document comercial** care poate avea mai multe linii  
- Viitorul nu e „lipim Litere+ACM în Product System ca un Frankenstein”  
- Viitorul e: **compui întâi** (Composer + contract), apoi ofertezi **compozitul**; sau linii comerciale separate pentru root-uri independente  

Ownerul a simțit pe bună dreptate golul: lipsea **mecanismul de unire**, nu doar regula „nu lipi orbește”.

### 11.5 Escapa în laboratorul vechi — și nostalgia clarității

**Simptom:** din V2, prin **Admin → Editor șablon**, ownerul a ajuns în editorul clasic (Validare, Product Compiler audit, blockers FACE/BACK/CANT).

**Clarificare:** ușa laterală către laborator, nu drumul principal V2.

**Apoi ownerul a arătat UI-ul vechi „Structură produs”** (1–5: Vizual față → Volum aluminiu → Capac spate → Sistem LED → Finisaj) și a spus: *uite ce frumos aveam, înțelegeam ceva*.

**Pivot:** nu mai „explicăm” structura — **reafișăm** limba vizuală pe care ownerul o citise deja (chips + timeline + aceleași labels din `components_json`).

**Meta-lecție explicită a ownerului:**  
*Cum îmi explici tu, eu nu înțeleg; dacă văd și tot nu înțeleg pentru că doar tu știi — direcția cine o ține?*  
→ UI-ul trebuie să țină direcția vizibilă pentru owner.

### 11.6 Ideea Composer + contract (owner)

Din tensiunea „template-uri separate” vs „vreau Litere cu ACM împreună”, ownerul a propus:

1. Aleg primul template (Litere).  
2. Văd template-urile **compatibile**.  
3. Aleg ACM casetat.  
4. Am **compozit** Litere + ACM.  

Agentul a validat: asta e direcție — **Composer de compatibilitate**, nu merge oarbă în ofertă.

**Rafinare owner (puritate):**
- în Litere afișăm **doar ce e al literei**  
- în ACM afișăm **doar ce e al ACM**  
- între ele facem un **contract**  

### 11.7 Conținutul contractului — realitatea de atelier (owner)

Ownerul a descris montajul real (detaliat la §4), pe scurt (rafiat seara):

1. ACM casetat gata (+ autocolant dacă e cazul) — **fără pack**  
2. **Proces șablon** pe ACM = ghidaj; comercial **20 EUR/mp** pe **outbox layer litere (integral)**  
3. Spate Forex + LED + cabluri, prinse pe ACM după șablon  
4. Electrică în carcasa bond + traf + cablu 5 m + test lumină  
5. Corp plexi + cant/volum pe Forex (autoforante fine vopsite)  
6. Pack ansamblu  

Asta a devenit **semantica contractului** (nu doar un flag `compatible: true`).

### 11.8 Documentare înainte de build

Ownerul a cerut explicit: **documentează direcția** ca s-o studieze cu AI advisorul său — **fără implementare Composer/contract încă**.

În același pas: lecția UI → regulă Cursor `.cursor/rules/ui-is-owner-reality.mdc` + §10 din acest fișier.

### 11.9 Hartă scurtă: simptom → decizie

| # | Ce s-a văzut / simțit | Ce am învățat | Ce a rămas ca direcție |
|---|------------------------|---------------|-------------------------|
| 1 | Header triplat | Chrome vechi stivuit | Un singur header / o singură spine |
| 2 | 13 module la Litere | Composition ≠ shared contracts ≠ suporturi | Template pur; diagnostic secundar |
| 3 | „Nu grupăm 2 template-uri în ofertă” | Oferta ≠ Product System merge | Composer + contract → apoi comercial |
| 4 | Editor vechi / Structură frumoasă | Owner citesc UI-ul vechi | Aliniază V2 la Structură produs |
| 5 | „Doar tu știi” | Explicația ≠ realitate | UI first-class (`ui-is-owner-reality`) |
| 6 | Composer + șablon montaj | Unire onestă Litere×ACM | Acest decision doc |

### 11.10 Ce s-a schimbat în cod în sesiune (context, nu obiectul deciziei)

Pentru advisor: în paralel cu discuția s-au făcut curățiri UI pe V2 (header, partiționare, aliniere Structură produs read-only). **Composerul și schema de contract NU sunt implementate** — doar direcția din acest document.

### 11.11 Artefacte legate

| Artefact | Rol |
|----------|-----|
| Acest fișier | Decizie + fir discuție |
| `.cursor/rules/ui-is-owner-reality.mdc` | Regulă agent: UI = realitatea ownerului |
| Product System V2 + `ProductSystemStructureReadonlyPanel` | Stare UI curentă (structură litere lizibilă) |
| Chat session (Cursor agent transcript) | Detaliu conversațional; **acest doc e sursa de studiu** |

---

## 12. Acceptance of this document

| Check | Expected |
|-------|----------|
| Direction readable without chat history | Yes (§2–§5) |
| Journey / why we got here documented | Yes (§11) |
| Letters / ACM purity stated | Yes |
| Contract = șablon + ordered assembly | Yes |
| Contract v1 owner ACCEPT | Yes — `LETTERS_ACM_COMPATIBILITY_CONTRACT_V1_ACCEPTED` |
| Composer described as future, not built | Yes — mock now unblocked |
| Commercial / Execution boundaries stated | Yes |
| UI meta-lesson captured | Yes (§10 + rule file) |
| CostEngine wiring deferred | Yes — separate GO |

**Owner study action (historical):** direction ACCEPTED earlier; contract v1 ACCEPTED 2026-07-23.

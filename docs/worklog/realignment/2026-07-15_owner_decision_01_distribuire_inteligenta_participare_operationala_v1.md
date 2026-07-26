# OWNER-DECISION-01 — Decizii owner: distribuire inteligentă și participare operațională V1

**Task:** OWNER-DECISION-01 — `DECIZII_OWNER_DISTRIBUIRE_INTELIGENTA_SI_PARTICIPARE_OPERATIONALA_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `746ab23`  
**Audit bază:** PROD-INT-02 (`746ab23`)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Cod changed:** NO

## Reguli gate

- Recomandările arhitecturale **nu** sunt decizii confirmate până la semnătură owner explicită.
- Termen canonic operație: **Operatie de productie** (nu task/sarcină/job).
- **MOBILE-INT-02** rămâne **BLOCAT** până la `OWNER_DECISIONS_CONFIRMED_READY_FOR_ARCHITECTURE`.
- **Implementare autorizată:** **NO** (0 decizii CONFIRMAT).

---

## Verdict gate

**`OWNER_DECISIONS_PARTIAL_REMAIN_BLOCKED`**

Toate cele 24 de puncte de decizie sunt documentate cu variante și recomandare, dar **0 CONFIRMAT** — așteaptă răspuns owner pe fiecare punct sau pe pachet aprobat.

---

## Contract de ieșire (stare curentă)

| Decizie | Varianta recomandată (NECONFIRMATĂ) | Status | Impact dacă se adoptă | Implementare autorizată |
|---------|-------------------------------------|--------|------------------------|-------------------------|
| D1 Moduri de lucru | Toate 5 moduri canonice | AMANAT | Model colaborativ definibil | NO |
| D2 Mod implicit | A + avertizare configurare | AMANAT | MOBILE-T06 rămâne valid default | NO |
| D3 Niveluri competență | 5 niveluri | AMANAT | Extindere model angajat | NO |
| D4 Validare competențe | Manager propune + RT validează risc | AMANAT | Workflow aprobare | NO |
| D5 Atribuții | Competență obligatorie; atribuție = prioritate | AMANAT | Separare distribuție | NO |
| D6 Autorizări | Criteriu eliminatoriu | AMANAT | Gate siguranță | NO |
| D7 Matrice operație–competență | Pe tip/sablon operație | AMANAT | Sursă adevăr clară | NO |
| D8 Eligibilitate | Filtru binar complet | AMANAT | Motor distribuție | NO |
| D9 Disponibilitate | 5 stări (nu binar liber/ocupat) | AMANAT | Program/absențe | NO |
| D10 Încărcare | Minute + procent schimb | AMANAT | Echilibrare | NO |
| D11 Operații simultane | Max 1 sesiune productivă | AMANAT | Protecție focus | NO |
| D12 Capacitate utilaje | Eligibil/disponibil/recomandat separat | AMANAT | Scheduling utilaj | NO |
| D13 Ordine optimizare | Lista 11 criterii (propusă) | AMANAT | Scor ponderat | NO |
| D14 Productivitate istorică | Factor secundar, date suficiente | AMANAT | Scor soft | NO |
| D15 Calitate istorică | Da, verificări confirmate | AMANAT | Scor soft | NO |
| D16 Cost intern | Factor foarte slab, invizibil angajat | AMANAT | Optimizare internă | NO |
| D17 Alocare automată | Cazuri sigure strict definite | AMANAT | Auto vs confirmare | NO |
| D18 Realocare | Sistem recomandă; manager confirmă | AMANAT | Fără mutări auto | NO |
| D19 Protecție sesiuni | Reguli + praguri configurabile | AMANAT | Anti-oscilație | NO |
| D20 Cerere de ajutor | Flux solicitare → ofertă → confirmare | AMANAT | Colaborare | NO |
| D21 Colaborativ + contribuții | Sesiuni/contributioni separate | AMANAT | Nu `assigned_employee_id` singur | NO |
| D22 Vizibilitate explicații | Rol diferențiat angajat/manager | AMANAT | UX + audit | NO |
| D23 Închidere operație | Sesiune ≠ operație | AMANAT | MOBILE-T05 remodelare colaborativ | NO |
| D24 MOBILE-T04/T05/T06 | Valid individual; remodelare alte moduri | AMANAT | MOBILE-INT-02 tot BLOCAT | NO |

---

## Deciziile 1–24 (detaliu)

### D1 — Modurile de lucru

**Problemă:** Fără mod canon, distribuția tratează greșit colaborarea, loturile și echipele.

| Mod (RO) | Definiție propusă | Min | Max executanți | Sesiuni simultane | Responsabil | Pornire | Închidere |
|----------|-------------------|-----|----------------|-------------------|-------------|---------|-----------|
| Executie individuala | Un executant principal | 1 | 1 | 1 principal | Executant | Preluare/pornire individuală | Complete = operație |
| Executie colaborativa | Mai mulți pe aceeași operație | 2 | N configurat | N (roluri distincte) | Responsabil operație | Fiecare sesiune proprie | Responsabil închide operația |
| Executie pe loturi | Sub-unități (ex. 100 litere) | 1 | N pe lot | Per lot | Per lot sau comun | Preluare lot | Lot + agregare progres |
| Executie in echipa | Echipă minimă fixă (ex. montaj) | Echipă min | Echipă max | Per membru | Coordonator echipă | Confirmare echipă | Coordonator |
| Operator principal cu ajutor | 1 principal + ajutori | 1 | 1+N ajutor | Principal + ajutor(i) | Operator principal | Principal pornește | Principal închide; ajutor închide sesiune |

**Variante:** (1) Toate 5 — **Recomandat** | (2) Doar individual + colaborativ | (3) Doar individual până la PROD-ARCH-02  
**Consecințe (1):** Contract mare, MOBILE/T06 nu acoperă toate — **necesită PROD-ARCH-01**.  
**Status:** **AMANAT**

---

### D2 — Modul implicit

**Variante:** A. Individual implicit | B. Blocat fără config | C. Dedus din șablon  
**Recomandare:** A + avertizare dacă șablonul marchează colaborativ/echipă — operația **nu** pornește auto în mod greșit.  
**Consecințe:** MOBILE-T06 rămâne comportament default; risc configurare uitată.  
**Status:** **AMANAT**

---

### D3 — Nivelurile de competență

**Propunere:** Incepator, Asistat, Autonom, Avansat, Instructor.  
**Variante:** (1) Toate 5 | (2) 3 niveluri simplificate | (3) Amânare  
**Recomandare:** (1) — cu istoric modificări, expirare opțională pe autorizări risc, dovadă practică pentru Avansat+.  
**Status:** **AMANAT**

---

### D4 — Validarea competențelor

**Variante:** Manager singur | RT singur | Manager+RT pe domeniu | Admin override excepțional  
**Recomandare:** Manager propune; RT validează CNC/laser/sudură/înălțime/electric/vehicul; admin corecție excepțională auditată.  
**Status:** **AMANAT**

---

### D5 — Atribuție principală și secundară

**Recomandare:** Competență obligatorie; atribuție principală ↑ prioritate; secundară permite alocare; rezervă/urgent; **atribuția nu înlocuiește competența**.  
**Variante:** (1) Recomandare | (2) Doar competență | (3) Atribuție eliminatorie  
**Status:** **AMANAT**

---

### D6 — Autorizări

**Audit obligatoriu:** CNC router, laser, modelator tablă, sudare, lucru la înălțime, instalații electrice, conducere vehicul, manipulare echipamente speciale.  
**Recomandare:** Autorizare = **eliminare**, nu scor.  
**Status:** **AMANAT**

---

### D7 — Matrice operație–competență

**Variante:** Pe produs | Pe angajat | Pe tip/sablon operație  
**Recomandare:** Cerințe pe **tip/sablon operație**; angajat deține competențe/autorizări; produs compune operații.  
**Status:** **AMANAT**

---

### D8 — Eligibilitate

**Criterii eliminatorii propuse:** dependențe, competență, nivel minim, autorizare, rol, activ, program, neabsent, locație, utilaj operabil, restricții, capacitate personală, mod lucru compatibil.  
**Rezultat:** Eligibil / Neeligibil + motive.  
**Status:** **AMANAT**

---

### D9 — Disponibilitate

**Recomandare:** Disponibil acum | Disponibil ulterior | Disponibil pentru ajutor | Ocupat | Indisponibil — include program, absență, sesiune, deplasare, schimb context.  
**Status:** **AMANAT** — **NECESITA DATE** pentru integrare pontaj/absențe dacă nu există sursă unică.

---

### D10 — Încărcarea

**Variante:** Număr operații | Minute | Procent schimb | Combinat  
**Recomandare:** **Minute estimate + procent schimb**; număr operații auxiliar.  
**Status:** **AMANAT**

---

### D11 — Operații simultane

**Recomandare:** Max **1 sesiune productivă activă**; excepții: asistență pasivă, colaborativ configurat.  
**Status:** **AMANAT**

---

### D12 — Capacitatea utilajului

**Recomandare:** Separă utilaj eligibil / disponibil / recomandat; model rezervări, mentenanță, defect, posturi, lucrări simultane — **independent** de capacitatea oamenilor.  
**Status:** **AMANAT** — **NECESITA DATE** inventar utilaje real + rezervări curente.

---

### D13 — Ordinea criteriilor de optimizare

**Propunere (neconfirmată):** 1 siguranță/autorizare → 2 dependențe → 3 termen/risc → 4 operații critice flux → 5 continuitate → 6 utilaj → 7 competență/nivel → 8 minim schimb context → 9 echilibrare → 10 productivitate/calitate → 11 cost intern.  
**Owner trebuie să confirme sau reordoneze.**  
**Status:** **AMANAT**

---

### D14 — Productivitate istorică

**Recomandare:** Factor **secundar** doar cu volum date suficient; niciodată eliminatoriu.  
**Riscuri:** date puține, penalizare lucrări grele.  
**Status:** **AMANAT** — **NECESITA DATE** (prag minim observații).

---

### D15 — Calitate istorică

**Recomandare:** Da, doar verificări comparabile confirmate; fără impresii manager în scor automat.  
**Status:** **AMANAT** — **NECESITA DATE** (sursă verificări QC).

---

### D16 — Cost intern

**Recomandare:** Factor **foarte slab**; sub siguranță/termen/calitate/competență; **invizibil angajatului**.  
**Status:** **AMANAT**

---

### D17 — Alocare automată

**Cazuri sigure propuse:** execuție individuală, risc redus, dependențe OK, un eligibil evident sau diferență mare scor, fără realocare/utilaj critic/conflict/sesiune afectată, date complete. Altfel: **Propunere cu confirmare**.  
**Status:** **AMANAT**

---

### D18 — Realocare

**Recomandare:** Sistem **recomandă**; manager **confirmă**; responsabil solicită; angajat **cere**, nu se mută singur.  
**Status:** **AMANAT**

---

### D19 — Protecția sesiunilor active

**Reguli propuse:** fără mutare aproape finalizat; fără mutare principal fără înlocuitor; păstrează echipă minimă; utilaj critic cu operator; cost schimbare; perioadă stabilitate — **praguri în configurare ulterioară**.  
**Status:** **AMANAT**

---

### D20 — Cerere de ajutor

**Termen canonic:** **Cerere de ajutor**.  
**Flux propus:** solicitare → eligibili → coleg se oferă → confirmare responsabil/manager (obligatorie la utilaj critic/termen/realocare) → sesiune ajutor separată → închidere separată.  
**Status:** **AMANAT**

---

### D21 — Operații colaborative și contribuții

**Confirmare necesară:** mai mulți executanți; sesiuni individuale; contribuții; progres agregat; responsabil separat; un executant **nu** închide singur întreaga operație colaborativă.  
**Progres:** cantitate, loturi, suprafață, lungime, etape, checklist, finalizat/nefinalizat — **mod per tip operație**.  
**Status:** **AMANAT**

---

### D22 — Vizibilitatea explicațiilor

**Angajat:** motiv recomandare, eligibilitate, dependențe, utilaj, echipă, ajutor, prioritate — **fără** scor colegi, cost, clasamente.  
**Manager:** eligibili, excluderi, scor, încărcare, risc, alternative, impact realocare.  
**Status:** **AMANAT**

---

### D23 — Închiderea operației (separat)

| Acțiune | Executant | Responsabil | Manager | Sistem |
|---------|-----------|-------------|---------|--------|
| Încheiere sesiune | Da (a sa) | — | — | Validare |
| Finalizare contribuție | Da | Validare | — | Agregare |
| Închidere lot | Per responsabil lot | Da | Da | Agregare |
| Închidere operație | Nu (colaborativ) | Da | Da | Gate dependențe |

**Recomandare:** Colaborativ — executant închide sesiunea/contribuția; responsabil/manager închide operația.  
**Status:** **AMANAT**

---

### D24 — Reclasificare MOBILE-T04 / T05 / T06

| Task | Clasificare propusă | Acțiuni viitoare (neautorizate acum) |
|------|---------------------|--------------------------------------|
| **MOBILE-T04** | `VALID_INDIVIDUAL` | Ma alatur operatiei, Preiau lotul, Pornesc ca operator principal, Ma alatur ca ajutor, Confirm participarea in echipa |
| **MOBILE-T05** | `VALID_INDIVIDUAL` — Complete = închidere totală | Inchei sesiunea, Raportez contributia |
| **MOBILE-T06** | `VALID_INDIVIDUAL` — nu motor universal | Alocare colaborativă separată de `assigned_employee_id` singur |

**Status:** **AMANAT** (reclasificare formală)

---

## Scenarii — rezultat sub recomandări (NECONFIRMAT)

| Scenariu | Rezultat așteptat dacă se adoptă pachetul recomandat |
|----------|------------------------------------------------------|
| **A — 100 litere** | Mod colaborativ/loturi; 3 eligibili; 2 mese; ajutor via Cerere de ajutor; realocare la sudare = **recomandare manager**, nu auto; progres pe loturi |
| **B — Sudare urgentă** | Motor compară progres modelare vs urgență sudare; recomandă realocare doar dacă trece D19; altfel respinge cu explicație |
| **C — CNC** | Scor între 2 eligibili: continuitate comandă + nivel + încărcare; explicație pentru manager |
| **D — Montaj** | Mod echipă; minim 3 roluri; vehicul ca utilaj; fără pornire până echipă completă confirmată |
| **E — 2 urgente** | Conflict capacitate explicit; **Propunere cu confirmare** obligatorie; manager alege — sistem nu inventează oameni |

---

## Blocaje rămase

1. **0 decizii CONFIRMAT** de owner în această sesiune.  
2. **MOBILE-INT-02** BLOCAT.  
3. **Implementare** interzisă până la `OWNER_DECISIONS_CONFIRMED_READY_FOR_ARCHITECTURE`.  
4. **NECESITA DATE:** pontaj/absențe (D9), inventar utilaje runtime (D12), prag productivitate/calitate (D14–D15).

---

## Următorul task permis

**Blocat** — după confirmare owner completă:  
`PROD-ARCH-01_CANONICAL_WORKFORCE_ROUTING_AND_COLLABORATIVE_EXECUTION_CONTRACT`

---

## Opinie sinceră

Gate-ul este gata pentru review owner: recomandările sunt coerente cu PROD-INT-02 și cu MOBILE-T06 ca subsistem individual. Fără confirmare explicită, orice implementare ar confunda „propus” cu „decis”. Prioritate owner: D1 (moduri), D21 (colaborativ), D23 (închidere), D24 (mobile) — restul derivă.

**Roadmap:** Waves 1–7 + mobile T01–T06 închise pe individual; următorul front este **contract arhitectural**, nu cod.

---

## Sumar status decizii

| Status | Count |
|--------|-------|
| CONFIRMAT | 0 |
| RESPINS | 0 |
| AMANAT | 20 |
| NECESITA DATE | 4 (D9 parțial, D12, D14, D15) |
| **Total puncte** | **24** |

# Adevăr tehnic — produse mixte ACM/ACP + litere volumetrice

| Câmp | Valoare |
|------|---------|
| Status | **CANONIC** — documentație de proces și ownership |
| Dată | 2026-07-19 |
| GO docs | `GO_MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP_AUDIT` |
| Baseline | `4c682c8` |
| Mod | Docs-only; nu schimbă runtime |

**Rol:** un singur adevar de atelier / Product System pentru panouri casetate mixte.  
**Nu înlocuiește** procesatorul grafic, CNC-ul sau atelierul.

---

## 0. Unde se citește ce

| Subiect | Document / authority |
|---------|----------------------|
| Terminologie ACM/ACP/Bond | `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md` |
| Cadru interior (formulă + traverse) | `ACP_INTERNAL_FRAME_OWNER_RULES.md` + acest doc §5 |
| Face treatments / module locale | `ACP_FACE_TREATMENT_AUTHORITY_CONTRACT.md`, module ACP_* |
| Litere volumetrice (corp) | `LITERE_VOLUMETRICE_LUMINOASE_CANONICAL_PRODUCT_DOSSIER.md` |
| LIGHT-ROUTED | `PARALLEL_LEGACY_COST_PATH` — nu SoT Intake V6 |
| PD → Aggregate → Execution | `03_PRODUCT_DEFINITION_COMPILER.md`, `05_PRODUCT_AGGREGATE_FLOW.md`, `08_EXECUTION_PLAN_FLOW.md`, `10_EXECUTION_PLAN_TASK_GRAPH.md` |

---

## 1. Descriere produs

Panou casetat din **ACM sau ACP** pe care pot coexista:

- carcasă pliată + cadru metalic interior;
- zone decupate iluminate (plexiglas pe spate);
- inserturi plexiglas ~10 mm în goluri;
- litere/logo volumetrice aplicate pe față;
- șablon de poziționare;
- cablare, sursă, acces service.

Product Template **doar compune**. Adevărul rămâne pe componente și pe interfețe.

---

## 2. ACM vs ACP (terminologie)

| Regulă | Detaliu |
|--------|---------|
| Familie material | ACM ≡ ACP ≡ Alucobond ≡ Dibond (alias-uri de magazin) |
| Cod live shell | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Label operator | „Panou Alucobond/ACP casetat” |
| LIGHT-ROUTED | `TPL-ACP-LIGHT-ROUTED` = **legacy Cost**, nu composition V6 |
| Capcană | `MAT-ACP-FATA-LITERE` = **plexi față litere**, nu panou compozit |
| Bond | Conversational / alias; nu ID nou de template |

În reguli tehnice scrie explicit: **ACM**, **ACP**, sau **ACM/ACP** numai când regula este comună.

---

## 3. Ce vede clientul vs ce rămâne intern

### Client

Exemplu: `1000 × 1000 × 100 mm` =

- lățime exterioară;
- înălțime exterioară;
- adâncime exterioară totală (volum).

Clientul **nu** primește calculele interne (straturi, luft cadru, traverse, joc insert).

### Intern (atelier / Product System)

Dimensiuni CNC, listă debitare cadru, carcasă locală, jocuri, electrica, șablon — pe fișe interne / taskuri.

---

## 4. Carcasă ACM/ACP — ordine CNC

Ordine confirmată:

1. Frezare V pe **partea opusă** feței active (pregătește plierea).
2. Decupaj grafic în **fața activă**.
3. Debitare contur exterior.
4. Pliere / formare.

Note:

- Unghiul frezei **nu** definește automat unghiul final al pliului.
- Doar CNC-ul este modelat pentru frezarea V.
- Cadrul metalic stabilizează geometria finală.

**Stare în repo (audit):** seed ACM are `cut → v_groove → fold`, fără regula „V pe fața opusă / decupaj înainte de contur”. Acest ordin este **OWNER_CONFIRMED în documentație**; materializarea în task_rules = gap.

---

## 5. Fixarea panoului pe cadru

- Fixare pe contur.
- Șuruburi autoforante cu cap înecat; capul la nivelul feței.
- **Nu** inventa pas rigid sau dimensiune șurub fără GO.

### Finisaj față

| Situație | Ordine |
|----------|--------|
| Față **fără** Oracal | Capetele se vopsesc la culoarea finală. |
| Față **cu** Oracal 651 | 1) fixare pe cadru → 2) șuruburi îngropate → 3) colantare **după** fixare → 4) folia acoperă capetele → 5) **nu** se mai vopsesc șuruburile. |

Catalog: Oracal 651 existent. Nu crea alt catalog.

**Stare în repo:** secvența Oracal-după-șuruburi pe panou ACM/ACP era **MISSING** în docs anterioare; aici este canonică.

---

## 6. Cadru metalic interior

### Ce se salvează (atelier — nu geometrie CNC)

- dimensiune exterioară cadru;
- material;
- profil / secțiune *(cod profil: vezi gate)*;
- orientare;
- elemente lungi / scurte;
- traverse;
- listă de debitare.

### Formulă dimensiune cadru (OWNER_CONFIRMED existent)

```text
frame = panel_outer − 2 × grosime_panou − 2 mm (luft total)
```

Exemplu documentat anterior: panou 2000×700×3 → cadru **1992×692**.

### Topologie listă debitare (OWNER_CONFIRMED acest GO)

- Elementele cele mai lungi rămân la cota completă a cadrului.
- Elementele scurte intră între ele; din scurte se scade **lățimea profilului la ambele capete**.
- Traversele: după același principiu (intră între elementele pe care le rigidizează).

Exemplu didactic (profil 20×20, cadru 838×638):

- 2 × 838 mm (lungi);
- 2 × 598 mm (scurte: 638 − 2×20);
- traverse între lungi: 598 mm.

### Propunere traverse

| Material | Spațiere propusă |
|----------|------------------|
| Oțel | ~1000 mm |
| Aluminiu | ~750 mm |

Sistemul propune; operatorul confirmă.

### Gate profil

`ACP_INTERNAL_FRAME_OWNER_RULES.md`: setul inițial de **coduri profil** pentru cadru interior ACP rămâne **DEFERRED**.  
Exemplul 20×20 de mai sus explică **topologia debitării**, nu aprobă SKU-ul ca default runtime până la GO profiluri.

Aggregate: cantități/listă debitare rămân **GUARDED** până există profil confirmat + consumer.

---

## 7. Carcasă locală de iluminare (zonă decupată)

### Construcție

| Element | Material |
|---------|----------|
| Bază / fereastră | Plexiglas **3 mm** |
| Pereți | Forex **10 mm** |
| Capac demontabil | Forex **3 mm** |

### Asamblare

1. Pereții Forex se lipesc între ei.
2. Rama Forex se lipește de plexiglas.
3. Capacul **nu** se lipește — se prinde cu șuruburi, rămâne demontabil.
4. LED-urile pot fi pe capac; capacul poate avea gravată poziția LED.

### Dimensiune bază

- Bounding box comun al personalizării.
- Țintă: **+30 mm pe fiecare latură**.
- Limite reale: pereții casetei ACM/ACP, profilul cadrului, spațiul liber.
- Conturul poate fi asimetric.

Exemplu: grafică 400×400 → plexiglas țintă 460×460.

### Forex 10 — topologie pereti (4 laturi)

- 2 × cotă completă;
- 2 × cotă minus 20 mm (când grosimea peretelui este 10 mm pe două capete).

### Stare în repo

| Sursă | Verdict |
|-------|---------|
| Intake V4 `inner_hole` package (plexi3 + Forex10 + Forex3) | **EXISTS** (analyzer helper) |
| Modul ACP `ROUTED-BACKLIT` | **PARTIAL** — intent + gate-uri; fără BOM carcasă |
| Documentație atelier unificată | Acest document |

---

## 8. Volum (adâncime exterioară) și iluminare

Volum = adâncime exterioară totală a casetei.

### Marje (intervale fără suprapunere)

| Volum (mm) | Marjă (mm) |
|------------|------------|
| ≥ 90 și ≤ 100 | 5 |
| ≥ 80 și &lt; 90 | 4 |
| ≥ 70 și &lt; 80 | 3 |
| ≥ 50 și &lt; 70 | 2 |
| ≥ 30 și &lt; 50 | (regim compact — vezi mai jos) |
| &lt; 30 | Nerecomandat — owner review |

### Regim standard

- Minim recomandat **60 mm**.
- Module LED pe capac.
- Iluminare din spate spre plexiglas.

### Regim compact (30–60 mm)

- Bandă LED / iluminare perimetrală.
- LED pe pereți laterali.
- **Altă** configurație optică — nu doar carcasă micșorată.

### Ownership electric

Preferat: `SHELL_COMMON_WITH_ZONE_INTENTS`  
(zonele declară intent; shell-ul compune LED/PSU/cablare/service — fără PSU duplicat pe zonă).

Literele volumetrice iluminate își păstrează traseul electric **propriu** (nu se amestecă cu cavity-ul ACP).

---

## 9. Plexiglas 10 mm (insert în decupaj)

### Diferență față de decupaj iluminat

| | Decupaj iluminat (routed) | Insert 10 mm |
|--|---------------------------|--------------|
| Rol | Gol + plexi pe **spate** | Element gros **în** gol |
| Grosime tipică | Gate (ex. diffuser 3 mm pe legacy) | Variantă frecventă **10 mm** — nu unica admisă |

### Construcție confirmată

1. Placă plexiglas lipită pe partea **opusă** feței active (susținere + transmisie lumină; transparentă sau opală — nu obligație globală).
2. Elementul 10 mm intră în decupaj.
3. Lipire de placa suport cu **cianoacrilat**.

### CNC vs laser

- ACM/ACP: freză **minimum 3 mm** → colțuri interioare cu rază.
- Plexiglas 10 mm: poate fi tăiat la **laser**.
- Sistemul **nu** modifică automat grafica.

### Recomandări scurte (procesator grafic confirmă)

- Verifică razele lăsate de freză.
- Verifică detaliile mici și spațiile înguste.
- Verifică dacă piesele intră ușor.
- Lasă joc pentru montaj și lipire.
- Evită goluri luminoase.
- Verifică potrivirea fișierului CNC cu fișierul laser.

**Stare în repo:** modul insert EXISTĂ ca identity + gate-uri; backing + ciano + toleranțe = documentate aici, **nu** ca defaults inventate în Aggregate.

---

## 10. Litere volumetrice (nu se copiază în shell)

Adevărul corpului literei rămâne la `TPL-VOLUMETRIC-LETTERS_v2` / dossier litere.

### Secvență corp (rezumat)

1. Cantul se lipește pe conturul feței (plexi 3 mm).
2. Corpul rămâne separat.
3. Spatele = Forex 10 mm; electrica pe Forex.
4. Spatele se montează pe casetă; treceri, legături, test.
5. Corpul se montează ulterior pe spate; fixare cu șuruburi vopsite.

### Montaj pe casetă (ordine)

1. Aplică șablonul.  
2. Poziționează spatele Forex 10 mm.  
3. Gaurește Forex + ACM/ACP pentru cabluri.  
4. Trage cablurile în carcasă.  
5. Legături + montaj sursă + verificare.  
6. Montează corpul.  
7. Fixare finală.

Detalii corp / LED / finisaje: dossier litere — **nu** duplica aici.

---

## 11. Șablonul de montaj

### Ce este

- Autocolant transparent, cu folie de transfer.
- Litere / forme pline + ghidaje + schiță cu cote + fișier de tăiere.

### Forme pline vs ghidaje

| Element | Comportament |
|---------|--------------|
| Forme pline | Rămân lipite pe ACM/ACP; acoperite de spatele Forex; **nu** se îndepărtează. |
| Ghidaje liniare / crop-uri | Temporare; ajută poziționarea; se îndepărtează după aliniere. |

### Alegerea ghidajelor

- Ghidaje liniare: pot economisi material când grafica e departe de margini; cer măsurători.
- Crop-uri: pot grăbi poziționarea; trebuie conectate geometric; pot consuma mult material.
- Aproape de margini: diferența de consum e mică — procesatorul alege.
- **Sistemul nu impune automat.**

### Task (un singur ownership)

Șablonul generează **un** task ownership-correct pe componenta **Litere** (`sablon_montaj` / INSTALLATION_TEMPLATE).

**Interzis:** task șablon din ACM/ACP **plus** task șablon din litere.

### Ce cere taskul

- schiță șablon;
- cote;
- orientare;
- tip ghidaje;
- fișier tăiere;
- confirmarea literelor / formelor pline.

### Stare în repo (audit)

| Aspect | Verdict |
|--------|---------|
| Mini-modul `sablon_montaj` pe litere | EXISTS |
| Paper vs Forex CNC | EXISTS (cu drift memoriu paper vs default Forex) |
| Vocabular pline / ghidaj / crop ca produs șablon | **MISSING** înainte — definit aici |
| Task șablon pe ACM seed | Absent (bine) |
| Risc sentinel comercial fără activare modul | Documentat în audit litere — de urmărit |

---

## 12. Ownership (fermități)

### Litere volumetrice

Față, cant, spate, LED, cablaj corp, montaj corp–spate, **șablon**, reguli proprii de montaj.

### ACM/ACP (shell)

Față suport, carcasă, cadru, finisaj panou, spațiu interior, prindere pe cadru, acces cabluri / service.

### Interfață ACM/ACP ↔ Litere

Zonă montaj, poziționare, cote, relație cu șablonul, treceri cabluri, acces în carcasă, constrângeri structurale.  
Cod tratament: `FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT` (`external_component`).

### Carcasă locală iluminare / insert

Plexi 3 + Forex 10 + capac 3; sau insert 10 mm + placă suport — pe **module locale** shell (`ownership_mode = acp_shell_local`).

### Product Template

Compune. Nu mută adevărul component-owned în mega-template.

---

## 13. Task flow (sistemul existent)

```text
Component Templates + Interface Contracts
  → ProductDefinition
  → ProductAggregate (task_contract.task_rules)
  → frozen snapshot
  → ExecutionPlan
  → taskuri operaționale existente
```

Nu creăm: model task nou, scheduler, coadă, pagină, catalog paralel.

Module inactive → **zero** materiale, procese, warnings, efecte CPP/task.

---

## 14. Ce nu automatizăm

- Procesare grafică / corectare rază / joc insert.
- Unghi pliu din unghi freză.
- Alegerea ghidaje vs crop.
- Calcul structural certificat.
- Cantități plexi/LED fără dimensiuni și registry optice.
- Import reguli din `TPL-ACP-LIGHT-ROUTED`.

---

## 15. Matrice audit — existent vs gap

| Topic | În repo | În acest doc |
|-------|---------|--------------|
| Shell live ACM boxed | EXISTS | Confirmat |
| LIGHT-ROUTED legacy | EXISTS (paralel) | Delimitat |
| Face treatments composabile | EXISTS (identity) | Confirmat |
| Module locale gated | EXISTS | Confirmat |
| Cadru formulă + spacing | EXISTS | Confirmat + topologie debitare |
| Profil cadru SKU | DEFERRED | Exemplu didactic 20×20 |
| Ordine CNC V-opus/decupaj | Gap task_rules | OWNER_CONFIRMED docs |
| Oracal după șuruburi | Gap | OWNER_CONFIRMED docs |
| Carcasă locală stack | PARTIAL (inner_hole) | OWNER_CONFIRMED docs |
| Regimuri volum iluminare | PARTIAL | OWNER_CONFIRMED docs |
| Insert 10 + ciano + backing | PARTIAL gates | OWNER_CONFIRMED docs |
| Șablon pline/ghidaj/crop | Gap vocabular | OWNER_CONFIRMED docs |
| Un singur task șablon | Intent litere | Regulă fermă |

---

## 16. Owner decisions rămase (implementare ulterioară)

1. Confirmare set profiluri cadru interior ACM/ACP (închide DEFERRED).  
2. Materializare ordine CNC în `task_rules` ACM.  
3. Registry RO optic/electric (închide gate-uri module).  
4. Reconciliere șablon paper vs Forex default comercial.  
5. DAG montaj litere pe panou + insert + routed (composition).  
6. GO separat dacă LIGHT-ROUTED trebuie migrat (nu acum).

---

## 17. Exemple scurte atelier

**Client:** panou 1000×1000×80 mm → volum 80 → marjă 4 mm (intern).

**Cadru:** după formulă din panou; listă: lungi complete, scurte −2×lățime profil.

**Zonă logo insert 10 mm + litere sus:** tratamente coexistente; litere = componentă separată; insert = modul local shell; un șablon = ownership litere.

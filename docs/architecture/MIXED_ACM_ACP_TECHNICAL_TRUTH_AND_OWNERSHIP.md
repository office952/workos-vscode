# Adevăr tehnic — produse mixte ACM/ACP + litere volumetrice

| Câmp | Valoare |
|------|---------|
| Status | **CANONIC** — proces, finish, fundal segmentat, electric, ownership |
| Dată | 2026-07-19 |
| GO | Audit consolidare completă (docs-only) |
| Baseline audit | `849c776` |
| Mod | Docs-only; **nu** schimbă runtime |

**Rol:** un singur adevăr pentru panouri casetate mixte, finisaje, fundaluri segmentate, litere, inserturi, șablon și electric.  
**Nu înlocuiește** procesatorul grafic, CNC-ul, atelierul, electricianul sau montatorul.

---

## 0. Unde se citește ce

| Subiect | Authority |
|---------|-----------|
| Terminologie ACM/ACP/Bond | `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md` |
| Cadru interior (formulă) | `ACP_INTERNAL_FRAME_OWNER_RULES.md` + §6 |
| Face treatments / module | `ACP_FACE_TREATMENT_*`, `ACP_*_LOCAL_MODULE.md` |
| Corp litere / LED / Forex | `LITERE_VOLUMETRICE_LUMINOASE_CANONICAL_PRODUCT_DOSSIER.md` + graph |
| Finish Oracal / print | `SHARED_VINYL_MATERIAL_CATALOG.md`, `CANONICAL_FINISH_ENUM_MAP_v1.md` |
| LIGHT-ROUTED | `PARALLEL_LEGACY_COST_PATH` — nu SoT V6 |
| PD → Aggregate → Execution | `03_…`, `05_…`, `08_…`, `10_…` |

---

## 1. Scop produs

Pot coexista pe același ansamblu:

- panouri **ACM** și/sau **ACP** casetate;
- cadru metalic; finisaj față / volum (Oracal 651 sau print+laminare);
- fundal din **mai multe panouri**;
- litere volumetrice aplicate; litere/forme decupate; insert plexiglas ~10 mm;
- carcasă locală de iluminare; șablon; cablare; surse; 220V; montaj atelier + teren.

Product Template **doar compune**.

---

## 2. Terminologie ACM / ACP / Bond

| Regulă | Detaliu |
|--------|---------|
| Familie material | ACM ≡ ACP ≡ Alucobond ≡ Dibond (alias magazin) |
| Cod live shell | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Label | „Panou Alucobond/ACP casetat” |
| LIGHT-ROUTED | Legacy Cost — nu composition V6 |
| Capcană | `MAT-ACP-FATA-LITERE` = **plexi față literă**, nu panou |
| Bond | Conversational; nu ID template nou |
| Reguli | Scrie **ACM**, **ACP**, sau **ACM/ACP** numai când e comun |

Aliniere cerută (verificare, nu implementare aici): formular → PD → PS → materiale → pricing → taskuri → fișă atelier → client → Execution.

---

## 3. Ce vede clientul

`1000 × 1000 × 100 mm` = lățime × înălțime × **adâncime exterioară totală**.  
Fără calcule interne (straturi, luft, traverse, jocuri).

---

## 4. Carcasă casetată — CNC

1. Frezare V pe **partea opusă** feței active.  
2. Decupaj grafic în fața activă.  
3. Debitare contur exterior.  
4. Pliere / formare.

Note: unghi freză ≠ unghi pliu automat; V mai permisiv posibil în practică (risc fisură față); doar CNC în Product System; unealta manuală **nu** intră în DAG.

**Repo:** seed ACM `cut → v_groove → fold` — fără regula V-opus; gap task_rules.

---

## 5. Fixare pe cadru + finisaj față

- Contur; autoforante cap înecat; fără pas/dimensiune inventate.

| Față | Ordine |
|------|--------|
| Fără colant | Capete vopsite la culoare |
| Cu colant | Fixare → șuruburi îngropate → **colant după** → folia acoperă → **nu** se vopsesc capetele |

---

## 6. Cadru metalic (atelier, nu CNC)

Salvat: dimensiune exterioară, material, profil/secțiune *(SKU DEFERRED)*, orientare, lungi/scurte, traverse, listă debitare.

**Formulă cadru (existent):** `frame = panel − 2×grosime − 2 mm`. Exemplu: 2000×700×3 → 1992×692.

**Topologie debitare:** lungi = cotă completă; scurte = cotă − 2×lățime profil; traverse la fel.

Exemplu didactic profil 20×20, cadru 838×638: `2×838` + `2×598` + traverse 598.  
**Nu** hardcoda 20×20×1,5 ca default runtime (profiluri DEFERRED).

Traverse propuse: oțel ~1000 mm; aluminiu ~750 mm; operator confirmă.

---

## 7. Finisaj față ≠ finisaj volum

Zone distincte. Pe fiecare: culoare placă | Oracal 651 | print + laminare.

Exemple valide: față Oracal + volum placă; față print+lam + volum Oracal; ambele la fel; ambele diferite.

**Repo:** `face_finish_type` ≠ `return_finish_type` (EXISTS pe litere/intake). Pe shell ACM — documentat aici; binding runtime Finish Contract = gap.

### Oracal 651

Catalog existent: `MAT-ORACAL-651` / serie `ORACAL_651` / culori `651-xxx`. **Nu** crea alt catalog.

### Print + laminare (exterior)

1. Print → 2. Laminare → 3. Aplicare.  
Ops existente pe artwork/față litere: `print_vinyl`, laminare, `face_vinyl_application_final`.

---

## 8. Lățime folie și strategii de colantare

Lățimea utilă = din **catalog** (nu inventată).

Oracal (existent): role nominale 1000/1260 mm → util ~960/1220.  
Print+lam UI: 1050/1320/1500 (retrageri laterale) — distinct de nesting Oracal.

### Ordine preferință

1. **Față + primul pliu** dintr-o bucată (dacă latimea permite). Primul pliu = latura care redă volumul carcasei.  
2. Față dintr-o bucată; **volum separat** (sus/jos/stânga/dreapta).  
3. Față din mai multe bucăți; îmbinări vizibile; **suprapunere mică**; poziție discretă; **client informat**.

### De salvat (Finish Contract)

material · latime utilă · orientare · față+primul pliu da/nu · față o bucată da/nu · volum separat da/nu · nr bucăți · poziție îmbinări · suprapunere · schiță · client informat.

### Mesaj client (calm)

> Pentru această dimensiune, colantarea feței necesită mai multe bucăți de folie. Îmbinările vor avea o suprapunere discretă, necesară pentru stabilitate în timp, și vor fi poziționate cât mai puțin vizibil.

---

## 9. Carcasă locală de iluminare

| Element | Material |
|---------|----------|
| Fereastră | Plexiglas 3 mm |
| Pereți | Forex 10 mm |
| Capac demontabil | Forex 3 mm |

Asamblare: pereți lipiți; ramă lipită de plexi; capac pe șuruburi (demontabil); LED pe capac posibil.

Dimensiune: bbox personalizare + **30 mm / latură**; limită = pereți casetă + cadru + spațiu; contur poate fi asimetric.  
Exemple: 400×400 → țintă 460×460; Forex 10: 2×cotă completă + 2×(cotă−20).

**Repo:** V4 `inner_hole` PARTIAL; modul routed gated.

### Volum & iluminare

Volum = adâncime exterioară. Marje (fără overlap):  
90–100 → 5 · 80–&lt;90 → 4 · 70–&lt;80 → 3 · 50–&lt;70 → 2.

- Standard ≥60 mm: LED pe capac, iluminare spre plexi.  
- Compact 30–60: bandă/perimetral, LED pe pereți — **altă** optică.  
- &lt;30: nerecomandat, owner review.

Electric shell: `SHELL_COMMON_WITH_ZONE_INTENTS`. Litere = traseu electric **propriu**.

---

## 10. Plexiglas 10 mm (insert)

≠ routed (plexi pe spate). Insert = element în gol; 10 mm = variantă frecventă, nu unica.

1. Placă suport pe spatele feței (transparent/opal — nu obligație globală).  
2. Insert în decupaj.  
3. Lipire cianoacrilat.

CNC freză ≥3 mm (raze); laser pe insert; sistemul **nu** modifică grafica.

Recomandări procesator: raze · detalii · spații înguste · intrare ușoară · joc · fără goluri luminoase · CNC↔laser.

---

## 11. Fundaluri segmentate (mai mari decât placa)

Produsul vizual = **un ansamblu**; fizic = mai multe panouri unite la montaj.

Sistemul **nu** împarte automat. Poate propune confirmare:

> Am găsit mai multe fundaluri apropiate care par să formeze un singur ansamblu. Confirmă dacă este un fundal ACM/ACP realizat din mai multe panouri.

### După confirmare se salvează

id ansamblu · nr panouri · ordine · poziție · dim. panou · dim. ansamblu · orientare · rost · continuitate grafică · schiță · elemente pe panou · elemente peste îmbinare · 220V · trasee · surse · dependențe montaj.

Panourile **nu** devin produse independente dacă formează același fundal.

### Compoziție distribuită (normală)

Litere pe panouri diferite = **OK**, nu panică.

> Grafica este distribuită pe mai multe panouri. Confirmă ordinea panourilor și continuitatea ansamblului.

**Nu:** „Eroare: grafica traversează mai multe fundaluri.”

### Per element se salvează

tip constructiv · panou principal · panou secundar · intersectează îmbinarea · regulă · strategie montaj · legătură electrică · dependențe.

Tipuri: literă volumetrică aplicată · aplicat simplu · literă/formă decupată · insert 10 mm.

### Literă volumetrică **peste** îmbinare — EXECUTABIL

Montaj în **două etape**:

1. Identifică panoul cu cea mai mare parte a spatelui Forex.  
2. Fixează partea principală pe panoul principal.  
3. Porțiunea peste îmbinare rămâne **temporar nesprijinită** până la alinierea panourilor.  
4. Completează prinderea pe panoul secundar la montaj.

**Nu** spune „rămâne în aer”.  
**Nu** blocker. **Nu** defect.

> Această literă trece peste îmbinare. Fixează partea principală în atelier și completează prinderea după alinierea panourilor.

### Decupaj / insert 10 mm peste îmbinare — BLOCKER

Literă/formă **decupată** sau insert 10 mm care necesită gol continuu **nu** pot traversa îmbinarea.

> O literă sau un decupaj trece peste îmbinarea dintre panouri. Mută îmbinarea sau modifică grafica.

| Situație | Verdict |
|----------|---------|
| Compoziție pe mai multe panouri | Normal |
| Literă aplicată peste îmbinare | Executabil, 2 etape |
| Decupaj / insert 10 peste îmbinare | Imposibil — blocker |

**Runtime contract:** un `SUPPORT_CONTOUR` rămâne envelope (`MAX_ONE`); panourile fizice nested în `finish_setup.segmented_background` (`acm_segmented_background_v1`). Nu se flipuiește MULTI pe SUPPORT.

---

## 12. Litere volumetrice — ordine reconciliată (din dossier + graph)

Adevărul corpului rămâne la `TPL-VOLUMETRIC-LETTERS_v2`.

### Confirmat

- Cant pe plexi 3 mm → corp separat.  
- Spate Forex 10 mm.  
- **LED-urile se montează pe Forex înainte de prinderea spatelui pe fundal** (ordine owner T09→T13; workshop: LED înainte de închiderea corpului).  
- Cablaj local pe Forex → traseu prin spate → `LOCAL_ELECTRICAL_READY`.  
- Corp pe Forex cu șuruburi vopsite, **după** test aprindere (graph: TEST_LED_ON → ATTACH_BODY → TEST_UNIFORMITY).

### Schemă atelier (cu suport / casetă)

```text
CUT_FOREX → LED pe Forex → cablaj local → ROUTE
FABRICATE_PANEL/CADRU ∥ …
ATTACH_BACKS pe casetă/bare
  → (canal dacă bare) → CONNECT
  → PSU (+ mains) → TEST_LED_ON
  → ATTACH_BODY → TEST_UNIFORMITY → QC
```

Alucobond: fără canal cablu; PSU lângă `service_corner`.  
Fără suport: PSU în colet; fără premount.

### Atelier vs teren

| Atelier | Teren / livrare |
|---------|-----------------|
| Debitare, LED pe Forex, cablaj local, premount spate, PSU pe ansamblu (dacă suport), teste, corp, pack | Livrare / montaj pe șantier; legături care depind de alinierea panourilor; re-test după montaj |

### Drift documentat (nu ascuns)

Graph permite ATTACH paralel cu LED până la canal; lista owner cere LED înainte de T13 — **preferăm ordinul owner + dossier §3.5** (LED pe Forex înainte de legături pe suport). Memoriu: un T17 vs două teste graph — ambele teste rămân în docs graph.

---

## 13. Șablon (un singur owner = Litere)

### Montaj pe casetă ACM/ACP (OWNER_CONFIRMED — închis)

Pentru litere volumetrice montate pe panou ACM/ACP:

- material: **autocolant transparent** (nu hârtie ca default în acest context);
- aplicare: **folie de transfer**;
- formele literelor: **pline**;
- formele pline **rămân** pe față sub spatele Forex 10 mm;
- ghidajele liniare și crop-urile sunt **temporare** și se îndepărtează după poziționare.

`paper vs Forex default` **nu** mai este o decizie deschisă pentru montajul pe ACM/ACP.  
Alte variante de șablon din documentația literelor pot rămâne pentru **alte contexte de montaj** (fără casetă ACM/ACP) — nu se șterg global.

### Reguli operaționale

- Alegere ghidaj vs crop: procesatorul; sistemul **nu** impune.  
- Task unic: `sablon_montaj` pe litere — **nu** și pe shell.

Task cere: schiță · cote · orientare · tip ghidaj · fișier tăiere · confirmare forme pline.

---

## 14. Management 220V și cabluri

Nu e suficient `alimentare 220V: da`.

### Per panou

- poziție 220V (colturi / centru / personalizat pe schiță);  
- ieșire cablu; sursă/traf asociat; grup litere;  
- traseu recomandat; direcție cabluri pregatite în atelier;  
- rezervă cablu; legături între panouri;  
- legături făcute în atelier vs rămase la montaj.

Exemple mesaje:

> Pregătește cablurile panoului 1 spre colțul dreapta sus.

### Ansamblu

Documentează: ce se pregătește în atelier · ce rămâne cu rezervă · unde e legătura finală · care panou deține sursa · care primește 220V · litere peste panouri · legături dependente de aliniere · test atelier · test după montaj.

**Repo:** `service_corner` / `power_supply_service_corner` EXISTS pe shell; poziție 220V **per panou segmentat** = MISSING runtime — docs aici.  
Litere: PSU pe ansamblu / colet; cablu alimentare default documentat în phase-2 answers (~5 m 2×1.5) — comercial, nu înlocuiește poziția pe panou.

**Nu** duplica taskuri electrice: shell = context 220V + acces; litere = LED/cablaj local + PSU litere; interfață = treceri.

---

## 15. Ownership

| Owner | Deține |
|-------|--------|
| **Shell ACM/ACP** | Panouri, carcasă, cadru, ordine panouri, dim., finisaj panou, prindere, continuitate ansamblu, acces interior, context 220V, service |
| **Litere** | Față, cant, Forex, LED, cablaj local, corp, corp–spate, **șablon**, secvență proprie |
| **Interfață** | Zonă montaj, panou principal/secundar, îmbinare, montaj 2 etape, treceri cablu, schiță, dependențe aliniere |
| **Finish Contract** | Zonă, tip folie, cod, latime, orientare, față/primul pliu/volum, bucăți, îmbinări, mesaj client |
| **Carcasă locală** | Plexi 3, Forex 10, capac 3, dim., iluminare, service |
| **Product Template** | Doar compune |

---

## 16. Task flow

```text
Component + Interface + Finish Contracts
  → ProductDefinition
  → ProductAggregate (task_contract.task_rules)
  → frozen snapshot
  → ExecutionPlan
  → taskuri existente
```

Dependențe reale; fără catalog paralel. Inactive → zero output.  
Ordinea completă litere: din dossier/graph (§12), nu inventată aici.

---

## 17. Mesaje atelier / client (limbaj)

Atelier: scurte, acțiune. Client: calm, transparent, fără dramatizare.

Exemple bune: vezi §8, §11, §14.

Evită: „configurație invalidă din cauza intersecției geometrice multi-panel”.

---

## 18. Exemple SVG (Desktop teste — nu în repo)

Cale: `%USERPROFILE%\Desktop\fisiere-teste-svg\`

| Fișier | Ce arată | Sistemul poate propune | Nu bloca |
|--------|----------|------------------------|----------|
| `litere-cu-fundal-acm-segmentat.svg` | 2×1000 mm ACM; litere pe câte un panou | Confirmare ansamblu segmentat | Dual-rect ca eroare |
| `…-litera-peste-imbinare.svg` | Literă aplicată peste seamă | Ansamblu + montaj 2 etape | Reject intake |
| `situatie-3.svg` | Peste îmbinare + overhang | Avertizări montaj/acoperire | Containment obligatoriu |

Deducție: geometrie + confirmare operator. Nu SoT unic.

---

## 19. Ce nu automatizăm

Procesare grafică · unghi pliu din freză · alegere ghidaj/crop · împărțire automată fundal · rotunjire insert · cantități fără registry · LIGHT-ROUTED ca SoT · unealtă manuală V.

---

## 20. Matrice existent vs gap

| Topic | Repo | Docs |
|-------|------|------|
| Shell ACM live | EXISTS | OK |
| face≠return finish (litere) | EXISTS | OK |
| Oracal 651 catalog | EXISTS | OK |
| Print+lam ops | EXISTS (artwork) | OK |
| Față+primul pliu strategie | MISSING | OWNER_CONFIRMED |
| Ansamblu multi-panou | CONTRACT `acm_segmented_background_v1` (envelope MAX_ONE + panels) | OWNER_CONFIRMED |
| Literă peste îmbinare | CONTRACT (2-stage + primary/secondary) | EXECUTABIL |
| Decupaj peste îmbinare | CONTRACT blocker | BLOCKER |
| 220V per panou | PARTIAL (service_corner) | OWNER_CONFIRMED |
| LED pe Forex înainte de attach | Graph soft / owner list | OWNER_CONFIRMED docs |
| Șablon pe ACM/ACP | OWNER_CONFIRMED vinyl transparent | Ferm (§13) |

---

## 21. Owner decisions rămase (implementare)

1. Profiluri cadru SKU (închide DEFERRED).  
2. Consum SVG Analyzer → propunere segmentare (UI confirmare) — contractul există; wiring UI separat.  
3. Finish Contract pe shell (față/volum/pliu/îmbinări).  
4. Materializare CNC + Oracal-după-fixare în task_rules.  
5. 220V position enum per panou.  
6. Reconciliere graph ATTACH vs LED (dep tare).  
7. GO LIGHT-ROUTED migrate — separat.  

**Închis:** șablon pe ACM/ACP = autocolant transparent + transfer; forme pline permanente; ghidaje/crop temporare (§13).  
**Închis ca model contract:** ansamblu = un `SUPPORT_CONTOUR` envelope + `assembly_panels[]` nested (nu MULTI SUPPORT global).

---

## 22. Legacy / reference / archive

| Item | Status |
|------|--------|
| `TPL-ACP-LIGHT-ROUTED` | PARALLEL_LEGACY_COST_PATH |
| `TPL-BOND-CASETAT` | Dead / blocked |
| Intake-v3 shared-support pending | Reference — workshop 2026-07-17 wins |
| Diffuser `splitDiffuserSegments` | Nu = fundal ACM segmentat |

# WorkOS — Pachet de decizii terminologice pentru owner (OD-TERM-01…11)

> **Explicații pentru owner** · **Doar documentație** · **Nu este implementare** · **Nu schimbă meniul acum**  
> Data: 2026-07-16 · Surse: registrul UI, fundația de finalizare pagini, meniul actual, Figma MASTER  
> Companion: `docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md`

---

## Cum să folosești acest document

Fiecare decizie întreabă: **ce text văd oamenii** și **ce rămâne în engleză doar pentru tehnicieni**.

Nu schimbă rutele, datele sau calculele — doar limba etichetelor, când va veni un build de UI.

**Blocarea build-ului B2 (index documentație):**  
B2 poate începe **înainte** să răspunzi la toți termenii, dacă B2 **nu** modifică meniul, **nu** publică etichete operator definitive și **nu** introduce traduceri hardcodate ca adevăr UI.  
Verdict recomandat: **`B2_CAN_START_BEFORE_ALL_TERMS`**.

---

## A. Decizii vizibile pentru operator (meniu / pagini)

### OD-TERM-01 — Numele paginii de catalog produse

**Unde va vedea utilizatorul schimbarea**  
Meniu stânga → Resurse · titlu pagină catalog produse.

**Cum arată astăzi**  
În meniu: `Product System`.  
În documente/Figma: Product System, uneori „sistem produs”.  
Variante greșite de evitat: „Sistem Produse” (nu e aprobat).

**Varianta recomandată**  
`Sistem produs`

**Ce rămâne în engleză**  
Numele tehnic secundar: `Product System` (sub titlu sau în documentație tehnică).  
Codurile șabloanelor rămân tip `TPL-…`.

**De ce**  
Operatorul lucrează în română; „Product System” sună ca jargon. „Sistem produs” e clar și scurt.

**Avantaj**  
Meniu coerent cu Oferte / Comenzi / Inventar.

**Risc**  
Obișnuința cu engleza; prima săptămână poate părea „alt nume”.

**Ce rămâne neschimbat functional**  
Doar text. Nu se schimbă ruta, datele, șabloanele.

**Exemplu vizual**  
`Sistem produs`  
subtitlu opțional: `Product System`

**Recomandare finală**  
Sistem produs (+ alias tehnic Product System).

**Răspuns simplu**  
`OD-TERM-01 = Aprob "Sistem produs", cu "Product System" doar ca nume tehnic secundar. Nu folosim "Sistem Produse".`

**Blochează:** `NON_BLOCKING_NOW` (blochează doar polish-ul UI Product System, nu B2).

---

### OD-TERM-02 — Numele zonei de preluare lucrări

**Unde**  
Meniu → Comercial · lista de cereri / intake.

**Astăzi**  
Meniu: `Work Intake`.  
În fluxul operatorului există și Intake V6 (pas cu pas).  
Figma Configurare folosește deja mult română pe pași.

**Recomandat**  
`Preluare lucrare`

**EN**  
Alias tehnic: `Work Intake`. Versiunea `Intake V6` poate rămâne pe ecrane tehnice.

**De ce**  
„Work Intake” e engleză într-un meniu altfel în română (Oferte, Comenzi).

**Avantaj**  
Operatorul înțelege imediat „de unde intră lucrarea”.

**Risc**  
Cine e obișnuit cu „Work Intake” trebuie să se uite o dată la noul nume.

**Funcțional**  
Doar etichetă. Ruta și datele rămân.

**Exemplu**  
`Preluare lucrare`  
subtitlu: `Work Intake`

**Răspuns simplu**  
`OD-TERM-02 = Aprob "Preluare lucrare" în meniu; "Work Intake" rămâne alias tehnic.`

**Blochează:** `NON_BLOCKING_NOW` (UI Intake ulterior).

---

### OD-TERM-03 — Control Tower și Shop Floor

**Unde**  
Meniu → Operațiuni.

**Astăzi**  
`Control Tower` · `Shop Floor` · (lângă) `Operator` · `Atelier Tablet`.

**Recomandat**  
**Păstrăm engleza** ca nume de „brand” al zonei de operațiuni:  
`Control Tower` · `Shop Floor`

**EN**  
Acestea *sunt* etichetele vizibile (intenționat).

**De ce**  
Sunt deja învățate ca nume de locuri de muncă; traducerea forțată (ex. „Turn de control”) nu ajută neapărat.

**Avantaj**  
Continuitate; mai puțin zgomot pe operațiuni.

**Risc**  
Meniu rămâne parțial mixt RO/EN — acceptat doar pentru aceste branduri.

**Funcțional**  
Neschimbat.

**Exemplu**  
`Control Tower` / `Shop Floor` (fără traducere obligatorie).

**Răspuns simplu**  
`OD-TERM-03 = Aprob păstrarea "Control Tower" și "Shop Floor" în engleză ca nume de brand.`

**Blochează:** `NON_BLOCKING_NOW`.

---

### OD-TERM-04 — Pagina de prețuri / tarife

**Unde**  
Meniu → Resurse, lângă Inventar.

**Astăzi**  
Meniu: `Pricing`.  
Documente: Pricing, tarife, registru prețuri.

**Recomandat**  
`Tarife`

**EN**  
Alias: `Pricing` (pagină tehnică / documentație).

**De ce**  
„Pricing” e engleză; „Tarife” spune clar că e registru de tarife, nu oferta comercială finală.

**Avantaj**  
Mai puțină confuzie cu „prețul ofertei”.

**Risc**  
Unii vor căuta încă „Pricing”.

**Funcțional**  
Doar etichetă. Nu schimbă modul de calcul.

**Exemplu**  
`Tarife`  
subtitlu: `Pricing`

**Răspuns simplu**  
`OD-TERM-04 = Aprob "Tarife" în meniu; "Pricing" rămâne alias tehnic.`

**Blochează:** `NON_BLOCKING_NOW`.

---

### OD-TERM-07 — Cum numim „fișa / spațiul” unei lucrări în Intake

**Unde**  
Texte din Intake (titluri, mesaje), nu neapărat un item de meniu.

**Astăzi**  
În engleză apare des `Workspace`.  
În română se poate spune spațiu de lucru / lucrare.

**Recomandat**  
`Spațiu de lucru`

**EN**  
`Workspace` ca nume tehnic; ID-urile (șiruri de litere/cifre) rămân neschimbate.

**De ce**  
Operatorul nu trebuie să învețe „workspace”.

**Avantaj**  
Limbaj de birou clar.

**Risc**  
Textele lungi dacă se repetă des — se poate scurta local la „Spațiu” doar dacă e clar din context.

**Funcțional**  
Doar text.

**Exemplu**  
`Spațiu de lucru` · (tehnic) `Workspace`

**Răspuns simplu**  
`OD-TERM-07 = Aprob "Spațiu de lucru" pentru operator; "Workspace" rămâne tehnic.`

**Blochează:** `NON_BLOCKING_NOW` (relevant la polish Intake / Wave 2 UI).

---

### OD-TERM-08 — Pagina actuală „Module Chain”

**Unde**  
Meniu → Sistem · pagina de hartă a legăturilor între sisteme.

**Astăzi**  
Meniu: `Module Chain`.  
Direcția Wave 0: pagina devine harta sistemelor (proiecție, nu editor).

**Recomandat**  
`Harta sistemelor`

**EN**  
Alias secundar: `Module Chain` (sub titlu).

**De ce**  
„Module Chain” nu spune ce face pagina. „Harta sistemelor” spune: vezi cum sunt legate sistemele.

**Avantaj**  
Clar pentru owner și operator tehnic.

**Risc**  
Cei care ziceau „Module Chain” trebuie să se obișnuiască.

**Funcțional**  
Doar etichetă / titlu. Nu schimbă datele. (Conținutul paginii se curăță în build-uri ulterioare, separat.)

**Exemplu**  
`Harta sistemelor`  
subtitlu: `Module Chain`

**Răspuns simplu**  
`OD-TERM-08 = Aprob "Harta sistemelor", cu "Module Chain" doar ca alias tehnic secundar.`

**Blochează:** `BLOCKS_TRUTH_PAGE_UI_ONLY` (etichete pe `/modules` la B4). **Nu blochează B2.**

---

### OD-TERM-09 — Pagina actuală „Governance”

**Unde**  
Meniu → Sistem · pagina de reguli / responsabilități.

**Astăzi**  
Meniu: `Governance`.  
Titlu intern: System Governance.

**Recomandat**  
`Guvernanța sistemului`

**EN**  
Alias: `System Governance` / `Governance`.

**De ce**  
Aliniat cu „Harta sistemelor”; limba operațională e română.

**Avantaj**  
Se înțelege că e despre reguli și proprietate, nu un panou de setări oarecare.

**Risc**  
Cuvântul „guvernanță” e puțin formal — acceptabil pe pagina de sistem.

**Funcțional**  
Doar etichetă.

**Exemplu**  
`Guvernanța sistemului`  
subtitlu: `System Governance`

**Răspuns simplu**  
`OD-TERM-09 = Aprob "Guvernanța sistemului", cu "System Governance" ca alias tehnic.`

**Blochează:** `BLOCKS_TRUTH_PAGE_UI_ONLY` (B5). **Nu blochează B2.**

---

## B. Decizii pentru zone tehnice / admin (nu meniul principal)

### OD-TERM-05 — Cum numim „definiția produsului” pe ecran

**Unde**  
Panouri tehnice în Intake / previzualizări (nu un item de meniu separat azi).

**Astăzi**  
ProductDefinition, PD, uneori engleză brută.

**Recomandat**  
Pentru operator: `Definiție produs`  
În zone debug: `PD` e acceptat.

**EN**  
`ProductDefinition` / `PD` în loguri și panouri tehnice.

**De ce**  
Operatorul vede română; tehnicienii păstrează acronimul.

**Avantaj / risc**  
Claritate vs. nevoie de legendă „PD = Definiție produs” o dată.

**Funcțional**  
Doar etichetă.

**Răspuns simplu**  
`OD-TERM-05 = Aprob "Definiție produs" pentru operator; "PD" doar în debug.`

**Blochează:** `NON_BLOCKING_NOW` (Wave 3 UI).

---

### OD-TERM-06 — Cum numim lista tehnică de componente / bom

**Unde**  
Panouri tehnice Aggregate / BOM (nu meniu principal).

**Astăzi**  
Aggregate, BOM, uneori confuzie cu „fișă de lucru”.

**Recomandat**  
`Agregat tehnic`

**EN**  
`ProductAggregate` / BOM în tehnic.

**Interzis ca etichetă operator**  
„Fișă de lucru” (induce confuzie cu alt tip de document).

**De ce**  
Spune că e rezultat tehnic, nu ofertă și nu fișă HR.

**Funcțional**  
Doar etichetă.

**Răspuns simplu**  
`OD-TERM-06 = Aprob "Agregat tehnic"; nu folosim "Fișă de lucru".`

**Blochează:** `NON_BLOCKING_NOW` (Wave 3 UI).

---

### OD-TERM-11 — Română pe ecranul operatorului, engleză în debug

**Unde**  
Toate paginile: zona normală vs. panouri „debug” / tehnice.

**Astăzi**  
Amestec pe multe ecrane.

**Recomandat**  
- Operator / meniu / butoane / statusuri: **română**  
- Panouri debug, câmpuri API, ID-uri: **engleză tehnică permisă**

**De ce**  
Operatorul nu trebuie să citească nume de câmpuri din bază; tehnicianul da.

**Avantaj**  
Limba clară unde contează; fără a forța traducerea ID-urilor.

**Risc**  
Dacă un panou „debug” e lăsat vizibil greșit, operatorul vede engleză — de evitat prin UI.

**Funcțional**  
Politică de afișare, nu schimbă date.

**Răspuns simplu**  
`OD-TERM-11 = Aprob: ecrane operator în română; zone debug pot rămâne engleză tehnică.`

**Blochează:** `NON_BLOCKING_NOW`.

---

## C. Decizii pentru traducerea viitoare (nu acum)

### OD-TERM-10 — Ce se întâmplă când lipsește o traducere

**Unde**  
Abia când vom introduce sistemul de traduceri (i18n).  
**i18n** = mecanism care ține textele pe limbi separate, fără a rescrie logica aplicației.

**Astăzi**  
Nu există framework de traduceri; textele sunt scrise direct în pagini.

**Recomandat**  
1. Limba principală: **română**  
2. Dacă lipsește o traducere: folosim textul din registrul românesc  
3. Dacă și acela lipsește: afișăm eticheta tehnică engleză (nu inventăm alt text)

„Limba de rezervă” (fallback) = ce se arată când lipsește traducerea.

**De ce**  
Evităm ecrane goale sau engleză aleatoare.

**Avantaj**  
Comportament predictibil când vom traduce treptat.

**Risc**  
Uneori rămâne un cuvânt tehnic EN vizibil — mai bun decât text greșit.

**Funcțional**  
Nu schimbă nimic acum. Nu blochează B2.

**Răspuns simplu**  
`OD-TERM-10 = Aprob: română principală; dacă lipsește traducerea → text din registru → ultimă rezervă engleză tehnică.`

**Blochează:** `BLOCKS_I18N_LATER` (doar la GO i18n). **Nu blochează B2.**

---

## Tabel rezumat

| ID | Unde apare | Varianta recomandată | Ce rămâne EN | Ce blochează | Răspuns simplu |
|----|------------|----------------------|--------------|--------------|----------------|
| OD-TERM-01 | Meniu Resurse | Sistem produs | Product System | NON_BLOCKING_NOW | Aprob Sistem produs |
| OD-TERM-02 | Meniu Comercial | Preluare lucrare | Work Intake | NON_BLOCKING_NOW | Aprob Preluare lucrare |
| OD-TERM-03 | Meniu Operațiuni | Control Tower / Shop Floor (EN) | — (sunt brand) | NON_BLOCKING_NOW | Păstrăm EN brand |
| OD-TERM-04 | Meniu Resurse | Tarife | Pricing | NON_BLOCKING_NOW | Aprob Tarife |
| OD-TERM-05 | Panouri tehnice | Definiție produs | PD / ProductDefinition | NON_BLOCKING_NOW | Aprob Definiție produs |
| OD-TERM-06 | Panouri tehnice | Agregat tehnic | ProductAggregate / BOM | NON_BLOCKING_NOW | Aprob Agregat tehnic |
| OD-TERM-07 | Texte Intake | Spațiu de lucru | Workspace | NON_BLOCKING_NOW | Aprob Spațiu de lucru |
| OD-TERM-08 | Meniu Sistem | Harta sistemelor | Module Chain | BLOCKS_TRUTH_PAGE_UI_ONLY | Aprob Harta sistemelor |
| OD-TERM-09 | Meniu Sistem | Guvernanța sistemului | System Governance | BLOCKS_TRUTH_PAGE_UI_ONLY | Aprob Guvernanța sistemului |
| OD-TERM-10 | Viitor i18n | RO → rezervă EN tehnic | — | BLOCKS_I18N_LATER | Aprob rezervă RO→EN |
| OD-TERM-11 | Toate paginile | Operator RO / debug EN | ID, API, debug | NON_BLOCKING_NOW | Aprob split RO/debug |

---

## Recomandările agentului (câte un rând)

1. OD-TERM-01 — Sistem produs  
2. OD-TERM-02 — Preluare lucrare  
3. OD-TERM-03 — păstrează Control Tower / Shop Floor  
4. OD-TERM-04 — Tarife  
5. OD-TERM-05 — Definiție produs (PD doar debug)  
6. OD-TERM-06 — Agregat tehnic  
7. OD-TERM-07 — Spațiu de lucru  
8. OD-TERM-08 — Harta sistemelor (+ Module Chain secundar)  
9. OD-TERM-09 — Guvernanța sistemului (+ System Governance secundar)  
10. OD-TERM-10 — română întâi, rezervă engleză tehnică  
11. OD-TERM-11 — operator română, debug engleză tehnică  

---

## Ce blochează B2 / ce poate aștepta

| Poate începe B2 acum? | Da |
|-----------------------|-----|
| Condiție | B2 = index documentație read-only, **fără** meniu nou, **fără** etichete operator definitive, **fără** traduceri UI hardcodate ca adevăr |
| Decizii obligatorii înainte de B2 | **Niciuna** din OD-TERM-01…11 |
| Utile înainte de UI pe Harta / Guvernanță | OD-TERM-08, OD-TERM-09 (la B4/B5) |
| Utile la i18n | OD-TERM-10, OD-TERM-11 |
| Utile la polish meniu | OD-TERM-01…04, 07 |

**Verdict B2:** `B2_CAN_START_BEFORE_ALL_TERMS`

Dovezi: plan Wave 0 — B2 = „Documentation Index and Read Model”; fundația B3 — politicile de limbă se aplică la finalizarea paginilor UI, nu la indexul read-only de documente.

---

## Bloc copy/paste pentru owner

```text
OD-TERM-01 = Aprob "Sistem produs" (alias tehnic: Product System)
OD-TERM-02 = Aprob "Preluare lucrare" (alias tehnic: Work Intake)
OD-TERM-03 = Aprob păstrarea "Control Tower" și "Shop Floor" în engleză
OD-TERM-04 = Aprob "Tarife" (alias tehnic: Pricing)
OD-TERM-05 = Aprob "Definiție produs" (PD doar în debug)
OD-TERM-06 = Aprob "Agregat tehnic" (fără "Fișă de lucru")
OD-TERM-07 = Aprob "Spațiu de lucru" (alias tehnic: Workspace)
OD-TERM-08 = Aprob "Harta sistemelor" (alias tehnic: Module Chain)
OD-TERM-09 = Aprob "Guvernanța sistemului" (alias tehnic: System Governance)
OD-TERM-10 = Aprob română principală; dacă lipsește traducerea → registru RO → rezervă EN tehnică
OD-TERM-11 = Aprob ecrane operator în română; debug poate rămâne EN tehnic

Verdict B2 = B2_CAN_START_BEFORE_ALL_TERMS
```

(Poți schimba orice linie cu „Resping / Vreau alt text: …”.)

---

## Next safe step

Owner răspunde doar la deciziile pe care vrea să le închidă acum (sau confirmă pachetul).  
Apoi: **GO separat pentru W0-B2** — fără a aștepta obligatoriu toți termenii, dacă B2 rămâne fără UI de etichete.

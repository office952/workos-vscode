# INTAKE_V6_REAL_SVG_RUNTIME_AUDIT

**Status:** Audit runtime only — **fără modificări de cod**, **fără mock-uri**, **fără alterarea SVG**  
**Data:** 2026-07-20  
**Viewport:** 1440×900 (același ca auditul UI system)  
**Runtime:** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8001`  
**Owner gate:** STOP — așteaptă decizie; **nu** trece în implementare

---

## 0. Scop și metodă

Auditul UI anterior pe Intake V6 a fost incomplet fără upload real. Acest document completează inventarul cu **două sesiuni curate**, câte un fișier SVG:

| Caz | Fișier local (nemodificat) | Workspace |
|-----|----------------------------|-----------|
| 1 | `C:\Users\offic\Desktop\fisiere-teste-svg\litere-cu-fundal-acm-segmentat.svg` (5136 B) | `IV6-87B98425` / `319c706e-…` |
| 2 | `C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg` (27173 B) | `IV6-3A52D29C` / `ebfed730-…` |

**Flow real folosit:** create workspace API → open `/intake-v6/{id}/operator` → `setInputFiles` pe `intake-v6-svg-input` → analiză client (`analyzeSvgFileForIntakeV6Client`) → confirm roluri → Configurare → refresh → reopen.

**Dovezi:** `docs/audits/_evidence/2026-07-20_intake-v6-real-svg-runtime/`  
Script: `capture-real-svg-runtime.mjs` · logs: `case*/runtime-log.json` · API slim: `case*-analysis-slim.json`

---

## 1. Structura SVG reală (adevăr fișier, nu UI)

### Cazul 1 — `litere-cu-fundal-acm-segmentat.svg`

| Grup Corel (ID) | Conținut | Semnificație operațională așteptată |
|-----------------|----------|-------------------------------------|
| `gravare-cnc-135gr` | **2× `<rect>`** gri `#C5C6C6` (stânga/dreapta) | Fundal ACM **segmentat** (2 panouri) |
| `decupare-cnc-outside` | 1× `<path>` roșu `#E31E24` „Litere Vol” | Litere / contur decupare |

### Cazul 2 — `gradi-curat.svg`

Grupuri/nume detectate în UI: `maria`, `soare`, `ana`, `gradinita` + `logo_instance_001/002`. Litere colorate pe două rânduri (GRADINITA / ANA MARIA SOARE) + 2 instanțe logo.

---

## 2. Verdict pe fișier (obligatoriu)

### Cazul 1 — litere-cu-fundal-acm-segmentat.svg

| Dimensiune | Verdict |
|------------|---------|
| upload | **PASS** |
| procesare SVG | **PARTIAL** |
| preview | **PASS** |
| detectie layere | **PARTIAL** |
| mapare componente | **PARTIAL** |
| claritate pentru operator | **62/100** |
| corectitudine operatională | **48/100** |
| persistenta | **PARTIAL** |
| cat suntem in directia stabilita | **55/100** |

### Cazul 2 — gradi-curat.svg

| Dimensiune | Verdict |
|------------|---------|
| upload | **PASS** |
| procesare SVG | **PARTIAL** |
| preview | **PASS** |
| detectie layere | **PARTIAL** |
| mapare componente | **FAIL** |
| claritate pentru operator | **58/100** |
| corectitudine operatională | **42/100** |
| persistenta | **PARTIAL** |
| cat suntem in directia stabilita | **50/100** |

---

## 3. Observații pe flow (ambele cazuri)

### Upload

| Check | Caz 1 | Caz 2 |
|-------|-------|-------|
| Selectabil / accept `.svg` | da (`intake-v6-svg-input`) | da |
| Încărcare | da, ~1.3s / ~0.15s | da |
| Nume afișat | `litere-cu-fundal-acm-segmentat.svg` | `gradi-curat.svg` |
| Tip SVG recunoscut | „Fișier recunoscut” | „Fișier recunoscut” |
| Feedback loading | **nu capturat** (prea rapid) | **da** — `Analizez…` (`03-upload-processing`) |
| Erori explicate | N/A (succes) | N/A |
| Asociere după salvare/refresh | analiză pe API **da**; chip pe pas Straturi după reopen **nu verificabil** (pasul nu se redeschide) | idem |

### Procesare (API + UI)

| Check | Caz 1 | Caz 2 |
|-------|-------|-------|
| Geometrie citită | da — perimeter/subpaths | da |
| Dimensiuni | **2000 × 350 mm** (high) | **5087 × 600 mm** (high) |
| viewBox | `0 0 132.47524 23.19281` | `0 0 519.77114 61.30898` |
| Elemente / contururi | 14 contururi închise, 0 deschise | 36 contururi închise |
| Grupuri / layere UI | **2** pseudo-fill (culoare), **nu** ID-urile Corel | **6** (4 grupuri litere + 2 logo) |
| Segmente ACM | **2 rects în fișier → 1 strat gri** | N/A (dar UI inventează „segmente legate”) |
| Avertizări analiză | `PERIMETER_CONFIDENCE_MEDIUM` | `FILLED_AREA_NOT_AVAILABLE` + perimeter medium |
| Erori analiză | 0 | 0 |
| Detectat vs propunere | UI marchează „Propunere” pe roluri | idem; totuși auto-rol `high` pe logo→`support_panel` induce în eroare |

### Preview

| Check | Ambele |
|-------|--------|
| Preview există | da (thumbnail + „Deschide preview”) |
| Complet / orientare / aspect | da — litere lizibile, panouri orizontale, fără tăiere evidentă @1440 |
| Fundal / goluri | Caz 1: fundal gri + litere outline vizibile; Caz 2: litere colorate pe fundal alb |
| Inspectabilitate | dialog „Preview SVG & straturi” + highlight pe hover/select |
| Domină formularul? | thumbnail rezonabil; dialog inspect ocupă majoritatea viewport-ului (acceptabil pe cerere) |

### Persistenta

| Layer | Observat |
|-------|----------|
| API `svg_analysis_json` după refresh | **PASS** (ambele) |
| `layer_role_setup.confirmation_status=complete` | **PASS** |
| `finish_setup.segmented_background` | **null** ambele (nici propunere segmentată) |
| UI Configurare după refresh | **PASS** — produs/componente rămân |
| Revenire la pasul Straturi (preview + chip) | **FAIL / blocat UX** — stepper rămâne pe Configurare; `chip=null`, `layers=0` la reopen pe Straturi |
| Save explicit | fără buton „Salvează”; auto-persist + banner „Analiză nesalvată…” pe Caz 2 înainte de confirm |

---

## 4. Product Definition — ce produce fiecare fișier

### Cazul 1

| Domeniu | Observat | Evaluare |
|---------|----------|----------|
| Produs | „Litere volumetrice + Panou Alucobond casetat” | Panou OK ca intenție; **fără** adevăr segmentat |
| Componente litere | Element 1 — roșu | OK (un grup litere) |
| Fundal ACM | Contur suport pe gri; Montaj menționează fundal/segmentare generice | **Segmentele 2× rect nu apar ca 2 componente/calcule** |
| Vector Logo | **Vector Logo 1 — „Necesită confirmare”** | **Fals pozitiv** — fișierul nu are logo vector separat |
| Layere UI | 2 (gri / roșu), nu `gravare-cnc-135gr` / `decupare-cnc-outside` | Pierde semnalele din ID-uri |
| Dimensiuni produs | 2000×350 mm | Coerent cu SVG width/height cm |
| Materiale / ops | defaults Față/Cant/Spate; cost intern ~387,84 EUR | Defaults, nu adevăr confirmat |
| Blocante Configurare | (1) compoziție neconfirmată (2) handoff ofertă blocat | Așteptate până la Confirmă; sursa e clară în drawer |
| `segmented_background` | null | **Lacună operațională majoră** pentru acest fixture |

### Cazul 2

| Domeniu | Observat | Evaluare |
|---------|----------|----------|
| Produs | tot „Litere + Panou Alucobond casetat” | **Greșit** pentru gradi-curat (fără fundal ACM) |
| Litere | Element 1–4 (maria/soare/ana/gradinita) | Bună separare pe grupuri color |
| Logo | Logo 1/2 auto-rol **`support_panel` (high)** → Panou Alucobond + UI „segmente legate”; plus **Vector Logo 1/2** „Necesită confirmare” | **Mapare dublă / greșită** — logo ≠ contur suport |
| Clasificare schimbabilă | da — dropdown rol (Vector Litere / Logo / Contur suport / …) | Operator **poate** corecta, dar auto-high + Confirmă toate încurajează acceptarea greșită |
| Componente inutile | Panou Alucobond + Vector Logo pe lângă 4 elemente litere | da |
| Componente pierdute | nu evident pentru litere | — |
| Blocante false | Panou/composition din mapare greșită logo→support | da (impact comercial ~651 EUR) |
| Blocante necesare | confirmare finisaj Vector Logo / compoziție | parțial acoperite, dar pe o structură greșită |

---

## 5. Inventar probleme (clasificate)

### P1 — Segmente ACM pierdute (Caz 1)

| Câmp | Valoare |
|-----|---------|
| Fișier | litere-cu-fundal-acm-segmentat.svg |
| Pas | Procesare → mapare componente → Montaj |
| Observat | 2× rect în `gravare-cnc-135gr` colapsate într-un singur strat `pseudo:fill-c5c6c6`; `segmented_background=null` |
| Așteptat | 2 segmente fundal configurabile/calculabile separat + relație litere↔suport |
| Impact | Ofertă/execuție ACM segmentat imposibilă din adevărul detectat |
| Severitate | **Critical** |
| Owner probabil | SVG Analyzer / ACM segmented background / Product Truth |
| Tip | procesare SVG + Product Truth |
| Origine | **WorkOS existent** (nu demo 21st) |

### P2 — Logo → Contur suport (Caz 2)

| Câmp | Valoare |
|-----|---------|
| Fișier | gradi-curat.svg |
| Pas | Propunere roluri → Confirmă toate → Configurare |
| Observat | `logo_instance_001/002` auto `support_panel` high → produs + Panou Alucobond + „segmente legate” |
| Așteptat | Vector Logo (sau ignore) — **nu** panou ACM |
| Impact | Compoziție greșită, cost intern umflat, operator indus în eroare |
| Severitate | **Critical** |
| Owner probabil | Layer role heuristics / svgAnalyzer |
| Tip | procesare SVG + Product Truth |
| Origine | WorkOS existent |

### P3 — Vector Logo fantomă (Caz 1)

| Câmp | Valoare |
|-----|---------|
| Fișier | litere-cu-fundal-acm-segmentat.svg |
| Pas | Configurare / Finisaje |
| Observat | „Vector Logo 1 — Necesită confirmare” deși SVG are doar fundal + litere |
| Așteptat | Fără slot Vector Logo sau slot explicit „absent” |
| Impact | Blocant/confirmare inutilă; confuzie ownership |
| Severitate | **High** |
| Owner probabil | Product composition / finish modular contract |
| Tip | Product Truth + UI |
| Origine | WorkOS existent |

### P4 — ID-uri layere Corel ignorate (Caz 1)

| Câmp | Valoare |
|-----|---------|
| Fișier | litere-cu-fundal-acm-segmentat.svg |
| Pas | Detectie layere |
| Observat | Pseudo fill pe culoare; UI „Element gri/roșu” |
| Așteptat | Păstrare/afișare `gravare-cnc-135gr` / `decupare-cnc-outside` ca semnal operațional |
| Impact | Operator nu vede intenția CNC din denumiri |
| Severitate | **Medium** |
| Owner probabil | svgAnalyzer / layer display |
| Tip | procesare SVG + UX |
| Origine | WorkOS existent |

### P5 — Feedback upload inconsistent / control vizibil

| Câmp | Valoare |
|-----|---------|
| Fișiere | ambele |
| Pas | Upload |
| Observat | Butonul `intake-v6-svg-select-button` nu e „visible” ca label separat (input hidden pe label); busy doar pe Caz 2 |
| Așteptat | Feedback clar select→analiză pentru orice fișier |
| Impact | Minor pe fișiere mici; risc pe fișiere lente |
| Severitate | **Low** |
| Owner probabil | Intake V6 UI |
| Tip | UI/UX |
| Origine | WorkOS existent |

### P6 — Observații analiză „în subsol” / duplicate status

| Câmp | Valoare |
|-----|---------|
| Fișiere | ambele |
| Pas | Straturi |
| Observat | „N observații analiză — Vezi în subsol”; footer cu blocante/avertizări; banner global „Stare sistem” |
| Așteptat | Un singur rail de adevăr (detectat vs propunere vs blocker) |
| Impact | Operator pierde contextul; deschide prea multe zone |
| Severitate | **Medium** |
| Owner probabil | Intake V6 operator UX |
| Tip | UX |
| Origine | WorkOS existent |

### P7 — Nu se poate redeschide Straturi după confirmare

| Câmp | Valoare |
|-----|---------|
| Fișiere | ambele |
| Pas | Refresh / reopen → corectare |
| Observat | Stepper Straturi bifat; click nu readuce preview/chip/layer cards |
| Așteptat | Reinspectare și corectare roluri fără recreate workspace |
| Impact | Corectarea propunerii după avans e grea |
| Severitate | **High** |
| Owner probabil | Intake V6 workspace steps / hydration |
| Tip | UX + persistence/integrare |
| Origine | WorkOS existent |

### P8 — „Confirmă toate sugestiile” pe heuristici greșite

| Câmp | Valoare |
|-----|---------|
| Fișier | gradi-curat.svg (și risc general) |
| Pas | Straturi |
| Observat | Un click confirmă 6 roluri incl. logo→support |
| Așteptat | Confirm bulk doar pe roluri cu încredere + diferențiere clară „propunere riscantă” |
| Impact | Amplifică P2 |
| Severitate | **High** |
| Owner probabil | Intake V6 layers UX + role confidence gating |
| Tip | UX + Product Truth |
| Origine | WorkOS existent |

### P9 — Console 422/404 în timpul flow-ului

| Câmp | Valoare |
|-----|---------|
| Fișiere | ambele |
| Pas | Integrare runtime |
| Observat | `422 Unprocessable Entity`, `404 Not Found` în console (fără mesaj operator dedicat) |
| Așteptat | Erori mapate în UI sau absente pe happy path |
| Impact | Necunoscut pe calcule secundare; erodează încrederea la debug |
| Severitate | **Medium** |
| Owner probabil | Intake V6 API clients / optional endpoints |
| Tip | integrare |
| Origine | WorkOS existent |

### P10 — Text EN în UI RO („Full-product composition…”)

| Câmp | Valoare |
|-----|---------|
| Fișiere | ambele (body sample Configurare) |
| Pas | Configurare |
| Observat | String tehnic EN în surface operator |
| Așteptat | Vocabular RO din registry |
| Impact | Claritate |
| Severitate | **Low** |
| Owner probabil | Intake V6 copy |
| Tip | UI |
| Origine | WorkOS existent |

---

## 6. UX operator — puncte de fricțiune

1. **Nu înțelege** de ce gradi-curat devine „Panou Alucobond casetat” / „segmente legate”.  
2. **Nu știe** dacă „Propunere” + confidence high e sigură — Confirmă toate e prea agresiv.  
3. **Pierde contextul** între observații subsol / footer blocante / drawer „2 probleme” / banner sistem.  
4. **Prea multe secțiuni** după Straturi (Finisaje / Iluminare / Montaj + commercial rail) înainte ca geometria să fie re-verificabilă.  
5. **Duplicate:** status Straturi incomplete vs panou operator vs footer.  
6. **Coduri tehnice:** `pseudo:fill-*`, EN composition string; detaliile tehnice sunt în accordion (OK) dar ID-urile utile Corel lipsesc.  
7. **Nu poate corecta ușor** după avans (P7).  
8. **Sursa blocker:** drawer „2 probleme” e relativ clar (compoziție + handoff) — **bun**; blockerii din mapare greșită apar ca nevoie de confirmare Vector Logo, nu ca „rol greșit pe strat”.

---

## 7. Scoruri agregate (inventar general)

| Metrică | Valoare |
|---------|---------|
| Completitudine audit Intake V6 (acum cu SVG real) | **ridicată** pe upload/preview/layers; **medie** pe ACM segmentat end-to-end |
| Risc operațional pe fixture ACM segmentat | **ridicat** (P1) |
| Risk operațional pe gradi-curat | **ridicat** (P2/P8) |
| Legătură cu direcția dark WorkOS | neschimbată — problemele sunt **adevăr produs / analyzer**, nu skin demo 21st |

---

## 8. Dovezi obligatorii (capturi)

### Caz 1 — `case1-acm-segmentat/`

`01-before-upload` · `02-layers-before-upload` · `04-after-process` · `05-preview` · `05b-preview-inspect` · `06-layers-detected` · `07–09` roluri · `10-after-advance` · `11-review-config` · `11b-montaj` · `11b-finisaje` · `12-saved` · `13-after-refresh` · `14-final-fullpage` · `15/16/17` reopen

### Caz 2 — `case2-gradi-curat/`

Același set + `03-upload-processing` (busy state capturat)

---

## 9. Ce NU s-a făcut (boundary respectat)

- Nu s-a modificat codul  
- Nu s-au modificat SVG-urile  
- Nu s-au introdus mock-uri / seed / migration  
- Nu s-a „reparat” Product Truth  
- Nu s-a implementat fix — **STOP pentru owner**

---

## 10. Decizii owner (propuse)

| ID | Întrebare |
|----|-----------|
| S1 | Prioritizezi fix P1 (ACM 2 rects → segmente) înainte de polish UI? |
| S2 | Logo instances: default `printed_artwork` / Vector Logo, **niciodată** `support_panel` fără confirmare explicită? |
| S3 | Slot Vector Logo: doar dacă există strat cu rol logo — elimină fantomele? |
| S4 | Straturi read-only/editabile după Configurare — obligatoriu? |
| S5 | „Confirmă toate” gated pe confidence + tip rol riscant? |

**STOP — așteaptă decizia owner (S1–S5).**

---

## Addendum — Root-cause (2026-07-20)

Owner a confirmat STOP pe UI / 21st. RCA complet:

→ [`2026-07-20_INTAKE_V6_SVG_TRUTH_AND_REINSPECTION_ROOT_CAUSE_AUDIT.md`](./2026-07-20_INTAKE_V6_SVG_TRUTH_AND_REINSPECTION_ROOT_CAUSE_AUDIT.md)  
→ Worklog: `_evidence/2026-07-20_intake-v6-svg-truth-rca/WORKLOG.md`

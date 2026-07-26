# ProductSystem Template Onboarding Playbook

**Versiune:** 2026-06-06 (finalizat; lifecycle gate 2026-07-17)  
**Scop:** Ghid intern oficial pentru adăugarea unui template ProductSystem end-to-end în WorkOS.  
**Audiență:** Cursor, agenți, developeri, owner.  
**Referință matură:** `TPL-VOLUMETRIC-LETTERS` (Product 001) — primul template activ validat pe lanțul complet.

> **Lifecycle gate (V1):** înainte de implementare/activare, rulează `template-lifecycle inspect <TEMPLATE_CODE>` (vezi `docs/architecture/WORKOS_TEMPLATE_LIFECYCLE_CONTROL_SYSTEM.md`). Product System rămâne authority; lifecycle e proiecție derivată.

> **Regulă de aur:** Un template **nu este funcțional** doar pentru că apare în ProductSystem. Trebuie aliniat în întreg lanțul: **ProductSystem → Pricing Registry → CostEngine → QuoteWizard → Work Intake → Blueprint Dossier → Readiness → Production task rules → Tests → Smoke → Documentation**.

> **Exemplu vs proces universal:** Secțiunile cu `TPL-VOLUMETRIC-LETTERS` sunt **ilustrative**. Regulile de produs (CNC passes, bare premontaj, ACM separat etc.) **nu** se aplică automat altor template-uri.

**Commits referință (volumetric, `master`):**

| Hash | Subiect |
|------|---------|
| `d4264fa` | QC internal-only / costing basis cleanup |
| `a7022a8` | unit-based volumetric operations |
| `544805d` | paint as whole tube material |
| `6f83e6b` | `paint_tube_count` in QuoteWizard |
| `cc7c2dc` | optional back bevel input |
| `2a3c321` | capture finish/mounting options |
| `a535b59` | finish/mounting pricing |
| `46c8260` | derive mounting bar length from assembly width |
| `fe0be10` | seed volumetric letters blueprint dossier |
| `e8761d1` | docs mounting bar length/profile pricing |

---

## 1. Purpose

Acest document este **playbook-ul oficial** pentru onboarding-ul unui template ProductSystem nou în WorkOS.

Folosește-l ca:

- checklist pentru Cursor/agents la fiecare template nou;
- ghid pentru developeri la implementare;
- criteriu PASS/FAIL înainte de activare quote/pricing;
- referință la ce trebuie documentat, testat și validat.

**Nu înlocuiește** deciziile owner despre produs, prețuri sau metodă de producție.

---

## 2. TPL-VOLUMETRIC-LETTERS as process reference, not universal product template

TPL-VOLUMETRIC-LETTERS (Product 001) este **referință de proces** pentru onboarding și validare în WorkOS — **nu** un model universal de produs. Folosește lanțul, checklist-urile și disciplina validate pe acest template; **nu** copia regulile de produs volumetrice în alte template-uri fără confirmare explicită owner.

### Reusable across future templates (process discipline)

| Area | Ce se reutilizează |
|------|-------------------|
| Onboarding lifecycle | Secțiunile 3–29 ale acestui playbook — ordinea pașilor, PASS/FAIL, smoke fără quote/order |
| Owner decision intake | Secțiunea 6 — întrebări produs/preț/producție înainte de cod |
| Active / archived scope | Un singur scope activ owner-validat; archived out of quote flows |
| Pricing Registry before CostEngine | Materiale + workcenter rates în registry; CostEngine citește registry |
| No hardcoded prices | Fără unit_cost inventat în formule sau handlers |
| No invented geometry | Prefill safe din intake; metrici geometrice doar manual sau extrase valid |
| Quote input contract | Document audit per template (quote_input keys, required/optional/conditional) |
| Work Intake mapping | Mapare business choices → quote_input; fără SVG→mp automat |
| Blueprint Dossier | pproved dossier + costengine_mapping_json + version |
| 	ask_rules_json | Ordine și condiții producție — **conținut specific fiecărui template** |
| output_blocks_json | Blocuri quote/producție — **structură proces, conținut per template** |
| Readiness policy | Clasificare blockers vs warnings — **lista blockerilor e per template** |
| Simulate vs quote-ready | simulate_ready ≠ can_create_commercial_quote; gate separat documentat |
| Final quote gate | Guard la POST /entities/quotes/price — **policy per template** |
| Tests and smoke | Unittest + vitest + API smoke + browser smoke; counts quotes/orders neschimbate |
| Backup / export | ZIP + DB înainte de build-uri majore; fără commit exports/ |

### Not reusable automatically (product-specific — TPL-VOLUMETRIC-LETTERS only)

| Area | De ce nu se copiază |
|------|---------------------|
| CNC / perimeter formulas | perimeter_pass_linear_meter, back bevel passes, pitch LED — specifice litere 3D |
| Paint tube logic | paint_tube_count, tuburi întregi MAT-VOPSEA-RAL + serviciu PAINTING |
| Oracal / RAL rules | ace_vinyl_color_code, paint_ral_code, roll width — finisaj față volumetric |
| Mounting bars rules | steel_bars / luminum_bars, profil 30x30x1.5, lungime din width_mm |
| Vector / SVG requirements | Vector Studio, layer mapping la 	emplate_code, manual review |
| Operation list | ace_cnc_cut, side_forming, ector_prep etc. — alt produs = alte operații |
| Material list | MAT-ACP-FATA-LITERE, MAT-SPATE-PVC-LITERE etc. |
| Production task order | Ordinea din dossier volumetric (față → lateral → spate → LED → finisaj) |
| Quote-ready blockers | letters_vector_file_required, ACM separate template, Oracal metadata — policy volumetric |
| QuoteWizard field layout | Câmpuri Product 001 / VOLUMETRIC_QUOTE_INPUT_FIELDS |
| CostEngine operation defs | Componente și formule din components_json volumetric |
| Product001 labels | Work Intake / Vector Studio copy — alt produs = alt UI |
| Volumetric assumptions | Profil 30/60/80/100 mm, Forex 10 mm spate, modul LED 75+25 mm |

### Rule: template-specific dossier before pricing or quote logic

Pentru **fiecare** template nou (sau reactivare majoră):

1. Creează sau actualizează **dossierul specific template-ului** (audit architecture dedicat).
2. Definește **înainte** de implementare pricing/quote:
   - scop produs (ce se vinde / ce nu);
   - materiale (cod, unitate, formulă);
   - operații (workcenter, basis, gates);
   - câmpuri quote_input (required, optional, conditional, default);
   - pricing basis (mp, ml, buc, tub, oră etc.);
   - secvență taskuri producție;
   - readiness gates (blockers vs warnings);
   - cerințe vector/fișier (dacă există);
   - output_blocks_json pentru quote și producție;
   - plan teste + smoke (payload referință, total așteptat dacă există).

**FAIL:** implementare CostEngine / QuoteWizard / quote gate copiat din volumetric fără dossier și confirmare owner.

### Cursor / agents

- Pornește **întotdeauna** din acest playbook (proces universal).
- **Adaptează** fiecare regulă product-specific la noul 	emplate_code.
- **Nu copia** valori, formule, blockers, câmpuri QuoteWizard sau task order din TPL-VOLUMETRIC-LETTERS decât dacă owner confirmă explicit că se aplică noului produs.
- Tratează TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md și TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md ca **documentație de produs**, nu ca șablon universal de input contract.

---

## 3. Definition of a functional template

Un template este **funcțional pe lanț** doar când are toate elementele de mai jos (nu doar card în ProductSystem):

| # | Element | Obligatoriu |
|---|---------|-------------|
| 1 | Identitate ProductSystem (`template_code`, family, status) | Da |
| 2 | `components_json` — structură produs | Da |
| 3 | Materiale — cod, unitate, formulă cantitate | Da |
| 4 | Operații — workcenter, basis, flags | Da |
| 5 | Contract `quote_input` documentat | Da |
| 6 | Intrări Pricing Registry (materiale + rate) | Da sau gap intenționat cu warning |
| 7 | Formule CostEngine + handlers | Da |
| 8 | Câmpuri QuoteWizard aliniate contractului | Da |
| 9 | Mapare Work Intake → `quote_input` (safe prefill) | Da |
| 10 | Blueprint Dossier (`approved` sau draft documentat) | Da |
| 11 | `task_rules_json` — ordine și condiții producție | **Da** |
| 12 | `output_blocks_json` — output quote/producție | **Da** |
| 13 | `costengine_mapping_json` — mapare structurală | Da |
| 14 | Politică readiness (warnings vs blockers) | Da |
| 15 | Teste backend + frontend | Da |
| 16 | Smoke API + browser (fără quote/order) | Da |
| 17 | Documentație architecture audit | Da |

**FAIL:** template vizibil în ProductSystem fără oricare din rândurile 5–16.

---

## 4. Template lifecycle states

| Stare | Semnificație | Quote/pricing live? |
|-------|--------------|---------------------|
| **experimental / draft** | În construcție; gaps acceptate în dev | Nu |
| **archived / inactive** | Retras; păstrat pentru audit | Nu |
| **active (browse)** | Vizibil în ProductSystem library | Poate (simulate) |
| **active for quote/pricing** | În `active_template_scope` owner-validat | Da, dacă și readiness OK |
| **simulate-ready** | `simulate-cost` PASS fără cost blockers pe payload referință | Simulate da; quote final poate nu |
| **dossier-documented** | Dossier `approved` + `task_rules` + `output_blocks` + mapping | Warnings dossier cleared |
| **quote-ready** | `ready_for_quote=true` (toate gate-urile policy) | Da — creare quote permisă |
| **production-ready** | Task rules validate + output blocks + fișiere producție | Execuție după quote acceptat |

### Exemplu curent: `TPL-VOLUMETRIC-LETTERS`

| Stare | Valoare |
|-------|---------|
| Active scope | Singur template activ (policy curentă) |
| simulate-ready | Da — baseline **844.41 EUR**, zero cost blockers |
| dossier-documented | Da — seed `fe0be10`, status `approved` |
| quote-ready | **Nu** — `ready_for_quote=false` (vector/file gate `letters_vector_file_required`) |
| production-ready | Parțial — task rules există; vector gate rămâne |

**Distincție critică:** `simulate-ready` ≠ `quote-ready`. Dossier complet nu ocolește vector/file policy.

---

## 5. Template identity rules

| Regulă | Detaliu |
|--------|---------|
| **template_code** | Identitate canonică stabilă — ex: `TPL-VOLUMETRIC-LETTERS` |
| **Nume UI** | Marketing/operator — diferit de cod |
| **family / category** | Grupare ProductSystem — ex: `litere_volumetrice` |
| **active vs archived** | Controlat prin scope + status template |
| **Fără duplicate ambigue** | Un cod = un produs; nu reutiliza codul unui template arhivat |
| **Fără hard delete** | Archive în loc de ștergere |
| **Archived out of flows** | Template arhivat **nu** apare în QuoteWizard, simulate activ, Pricing live |

**SVG layers:** mapping la `template_code` **exact** — nu la nume afișat.

---

## 6. Owner decision intake

Înainte de cod/seed, colectează și documentează:

### Produs
- [ ] Scop produs (ce se vinde / ce nu)
- [ ] Metodă reală de producție (nu presupuneri agent)
- [ ] Dimensiuni și măsurători necesare
- [ ] Variante și opțiuni business

### Materiale și operații
- [ ] Lista materiale (cod, unitate, bază preț)
- [ ] Lista operații (workcenter, basis, quote-priced da/nu)
- [ ] Activități **internal-only** (QC, planificare, calibrare)
- [ ] Activități **quote-priced** (CNC, montaj, finisaj…)

### Opțiuni și fișiere
- [ ] Finisaje, montaj, premontaj
- [ ] Fișiere obligatorii (vector, SVG, RAL, culori)
- [ ] Ce **nu** e prețuit încă → warning policy

### Prețuri
- [ ] Prețuri owner-confirmed (**fără TVA** în `unit_cost`)
- [ ] Conversie manuală documentată (nu live FX implicit)
- [ ] Monedă bază (Settings — de obicei EUR)

### Producție
- [ ] **Ordinea task-urilor** de execuție (nu doar lista operațiilor de cost)
- [ ] Dependențe între task-uri
- [ ] Task-uri condiționale pe `quote_input`
- [ ] Gate-uri readiness (simulate vs quote final)

---

## 7. Component model

- **Componentele** = structură produs în `components_json`.
- Grupează **materiale** și **operații** pe zone logice de producție.
- Reflectă realitatea atelierului, nu doar contabilitatea.
- Ordinea componentelor ajută UI/înțelegere — **nu înlocuiește** ordinea task-urilor de execuție.

> **CostEngine operation ≠ Production task.** O componentă poate conține mai multe operații de cost; un task de producție poate agrega sau condiționa mai multe operații.

**Exemplu volumetric (ilustrativ):**

| component_id | Rol |
|--------------|-----|
| `comp_face_litere` | Față plexiglas |
| `comp_lateral_litere` | Cant profil |
| `comp_spate_litere` | Capac spate Forex |
| `comp_led_litere` | Sistem LED |
| `comp_finisaj_litere` | Vopsire, șablon, ambalare |
| `comp_premount_bars` | Bare premontaj |

---

## 8. Material model

Pentru **fiecare** material:

| Câmp | Regulă |
|------|--------|
| `material_code` | Canonic — ex: `MAT-VOPSEA-RAL` |
| Unitate | mp, ml, buc, tub, set |
| `formula_id` | Cantitate în CostEngine — **nu preț** |
| `unit_cost` | Doar în Pricing Registry / Inventory — **fără TVA** |
| `currency` | Aliniat Settings |
| `source_review_status` | `accepted_override` / `needs_review` |
| `source_notes` | Conversie manuală, waste, furnizor |
| Gate condițional | Ex: `face_finish_type`, `mounting_bar_profile_in` |

**Reguli:**

- **Nu hardcoda preț material în CostEngine.**
- Stoc/procurement (Inventory) ≠ preț quote (Registry) — nu inversa.
- Materiale whole-unit: ex. tuburi vopsea `ceil(paint_tube_count)`.
- Preț **profil-specific** ≠ preț material-generic pentru toate variantele.

---

## 9. Operation / service model

Pentru **fiecare** operație:

| Câmp | Regulă |
|------|--------|
| `code` | Ex: `face_cnc_cut`, `qc_letters` |
| `workcenter` | Ex: `CNC_ROUTER`, `QC_INSPECTION` |
| `quote_priced` | `true` / `false` |
| `internal_only` | Fără cost quote, fără blocker rate lipsă |
| `rate_basis` | `per_piece`, `per_linear_meter`, `per_square_meter` |
| `formula_id` | Cantitate — nu preț |
| Pass logic | În `formula_params` dacă multi-pass |

**Reguli:**

- **Evită hourly ca default** — doar cu decizie owner explicită.
- **Nu duplica generic ASSEMBLY** dacă pașii sunt deja prețuiți explicit.
- Operație fără acțiune comercială distinctă → `internal_only` sau de-scope.

**Exemple volumetrice:**

| Operație | WC | Basis | Quote-priced |
|----------|-----|-------|--------------|
| `vector_prep` | PREPRESS | per letter | Da |
| `face_cnc_cut` | CNC_ROUTER | per ml/pass | Da |
| `painting` | PAINTING | per ml | Da |
| `qc_letters` | QC_INSPECTION | — | **Nu** (`internal_only`) |
| `assembly_letters` | ASSEMBLY | — | **Nu** (de-scoped) |

---

## 10. Internal-only vs quote-priced

| Tip | Cost quote | Rate obligatoriu | Blochează pricing? | Task producție |
|-----|-----------|------------------|--------------------|----------------|
| Quote-priced | Da | Da (Registry) | Da dacă lipsește | Da, cu referință operație |
| Internal-only | Nu | Nu | **Nu** | Da (QC, checklist) |
| Captured-only | Nu | Nu | Nu — warning | Poate (instrucțiuni) |
| De-scoped | Nu | Nu | Nu | Nu sau intern |

**Exemple volumetric:**

- `qc_letters` — internal-only; durata poate fi calibrare, nu preț client.
- `mounting_labor_not_priced` — material bare prețuit; manoperă montaj încă neconfirmată → **warning**, nu blocker.

**Regulă:** QC intern **nu** trebuie să producă `WORKCENTER_RATE_MISSING` la simulate.

---

## 11. Unit basis rules

| Basis | Utilizare | Exemplu volumetric |
|-------|-----------|-------------------|
| mp | Suprafață | Oracal, ambalare, șablon Forex |
| ml | Perimetru, profil, bare, vopsire serviciu | CNC per pass, painting |
| buc / piece | Litere, module, PSU | PREPRESS, electrical |
| tub | Consumabil întreg | `MAT-VOPSEA-RAL` |
| set | Consumabile montaj | MAT-CONSUMABILE-MONTAJ |
| per pass linear meter | CNC multi-pass | face 2 passes, back 3/5 |
| derived | Din alt input | `led_module_count` din perimetru |
| override | Input explicit | `mounting_bar_length_m` |

**Reguli:**

- `ceil` pentru unități indivizibile (tuburi).
- Override bate derivarea (ex: lungime bare manuală).
- Input lipsă → `NEEDS_QUOTE_INPUT` sau warning — **fără zero silențios**.

---

## 12. Pricing Registry setup

- [ ] Toate prețurile/rate-urile în **Pricing Registry** / `inventory_materials` / `workcenter_rates`
- [ ] CostEngine calculează **cantitatea**, nu rata comercială
- [ ] Monedă bază din **Settings**
- [ ] **TVA exclus** din `unit_cost` și rate-uri
- [ ] Conversie manuală în `source_notes` — nu live FX decât modul explicit
- [ ] `accepted_override` vs `needs_review` — policy readiness clară
- [ ] Variante/profiluri — preț separat sau warning (nu fallback silențios)

**Anti-pattern:** `steel 30x30x1.5 = 2 EUR/ml` aplicat automat la `40x40x2`.

---

## 13. CostEngine setup

- [ ] `formula_handlers.py` — fiecare `formula_id` din template înregistrat
- [ ] Gates `quote_input` pe linii condiționale (`mounting_template_enabled`, `face_finish_type`, etc.)
- [ ] Missing input → `NEEDS_QUOTE_INPUT` (blocker) sau warning policy
- [ ] **Zero prețuri hardcodate** în `cost_engine_service.py`
- [ ] Breakdown metadata unde e util (ex: `derived_total_length_m`, `override_used`)
- [ ] Operații `internal_only` skip fără blocker
- [ ] Teste: line totals, missing input, no silent zero, currency mismatch

**Servicii relevante:** `cost_engine_service.py`, `formula_handlers.py`, `volumetric_quote_input_policy.py` (pattern per template).

---

## 14. Quote input contract

Fiecare câmp din `quote_input` trebuie documentat:

| Aspect | Obligatoriu |
|--------|-------------|
| Cheie canonică | Da |
| Required / optional / conditional | Da |
| Default | Da (sau explicit „fără default”) |
| Validare | Da |
| Efect costing | Da |
| Efect readiness | Dacă aplicabil |
| Efect task rules | Dacă condițional |

**Categorii:**

- Geometrie (`width_mm`, `letter_perimeter_m`, …)
- Opțiuni (`back_bevel_enabled`, `face_finish_type`, `mounting_system`, …)
- Metadata producție (`paint_ral_code`, culori vinyl — poate fi captură fără preț)
- Override (`mounting_bar_length_m`)

**Policy warnings:** opțiuni capturate dar neprețuite → cod warning explicit, nu 0 EUR.

**Exemple volumetric:** vezi `TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md`.

---

## 15. QuoteWizard alignment

- [ ] Câmpuri pentru toate inputurile required și condiționale
- [ ] Label + helper text înțeles de operator
- [ ] Validare condițională (ex: aria șablon doar dacă checkbox activ)
- [ ] Payload builder trimite chei exacte din contract
- [ ] `width_mm` din Step 2 propagat la simulate
- [ ] Opțiuni neprețuite → warnings vizibile
- [ ] **Simulate preliminar nu creează quote/order**
- [ ] Fără default ascuns care adaugă cost neașteptat

**Exemplu:** `mounting_bar_length_m` = override opțional; label *Lungime totală bare premontaj override*; helper auto `width × 2 bare`.

---

## 16. Work Intake alignment

- Capturează alegeri business **devreme** în `product_spec_json`.
- **Nu inventa geometrie** din text liber dacă produsul necesită vector/SVG/măsurători.
- Prefill QuoteWizard doar pentru mapări **safe** și documentate.
- Geometria poate veni ulterior din SVG analiză sau introducere manuală în wizard.

**Mapări volumetrice (exemplu):**

| Intake | quote_input |
|--------|-------------|
| `backing_chamfer` | `back_bevel_enabled` |
| `face_finish=oracal_651` | `face_finish_type=oracal_651` |
| `mounting_type=direct_wall` | `mounting_system=direct_wall` |
| `metal_structure` | `steel_bars` |
| `acm_casetted_panel` | `acm_panel` (warning template separat) |

---

## 17. Blueprint Dossier alignment

Dossier = documentație **template-level** (nu snapshot quote).

**Trebuie să includă:**

| Artefact | Conținut |
|----------|----------|
| `costengine_mapping_json` | Input-uri required/optional, primitive derivate, mapping structural |
| `output_blocks_json` | Blocuri quote/producție, audience, variabile |
| `task_rules_json` | **Ordine task-uri, condiții, dependențe** |
| Variante permise | Opțiuni owner-valid vs experimentale |
| Reguli producție | CNC passes, finisaj, montaj |
| Note readiness | Ce gate rămâne activ după seed |

**Reguli:**

- Seed **idempotent** — ex: `seed_tpl_volumetric_letters_dossier.py`
- **Nu bypass** readiness real (vector/file) prin dossier
- **Nu prețuri comerciale** în dossier — doar structură/reguli
- Dossier `approved` ≠ `quote-ready` automat

**Exemplu volumetric (`fe0be10`):**

- Warnings cleared: `blueprint_dossier_missing`, `costengine_mapping_missing_no_dossier`, `output_blocks_missing`, `task_rules_missing`
- Rămâne: `letters_vector_file_required` → `ready_for_quote=false`

---

## 18. Readiness policy

Evaluare canonică: `ProductReadinessService.evaluate(template_id)`.

| Concept | Semnificație |
|---------|--------------|
| **Cost blockers** | Împiedică calcul valid (NEEDS_QUOTE_INPUT, currency mismatch, rate lipsă pe linie quote-priced) |
| **Readiness warnings** | Dossier, vector, opțiune neprețuită, profil fără preț |
| **ready_for_quote** | Boolean policy — toate gate-urile pentru creare quote |
| **Simulate preliminar** | Poate rula cu warnings dacă nu există cost blockers |

**Nu confunda:**

- Dossier lipsă ≠ vector lipsă (coduri warning diferite)
- Warning profil fără preț ≠ blocker input lipsă
- `simulate-ready` cu warnings ≠ `quote-ready`

**Nu ocoli readiness** pentru UI verde artificial.

---

## 19. Production task rules and task order

> **Obligatoriu.** Un template **nu este complet** fără `task_rules_json` cu ordine, condiții și dependențe.

### CostEngine operation ≠ Production task

| Concept | Rol |
|---------|-----|
| **CostEngine operation** | Linie de cost/preț (cantitate × rate) |
| **Production task** | Pas executabil în atelier / checklist operator |
| Relație | Unele operații priced generează unul sau mai multe task-uri; unele task-uri sunt internal-only fără cost |

**De ce contează ordinea:**

- Operatorul execută în secvență fizică (CNC înainte de lipire, vopsire înainte de ambalare).
- Opțiunile condiționale (`back_bevel_enabled`, `face_finish_type`, `mounting_system`) trebuie să **activeze task-uri**, nu doar linii de cost.
- QC intern poate fi ultimul pas înainte de ambalare/expediere.

### Checklist obligatoriu `task_rules_json`

Pentru fiecare task:

- [ ] `task_id` / `task_name` / cod stabil
- [ ] Titlu operator (RO, clar)
- [ ] Descriere
- [ ] `order` / `sequence`
- [ ] `component` / stage
- [ ] `condition` / `trigger_condition`
- [ ] `depends_on` (dacă aplicabil)
- [ ] `quote_input` trigger (ex: `back_bevel_enabled=true`)
- [ ] `internal_only` yes/no
- [ ] `priced_operation` reference (dacă există)
- [ ] Output/artifact așteptat
- [ ] Note operator

### Exemplu ordine producție — `TPL-VOLUMETRIC-LETTERS` (ilustrativ, nu universal)

Ordinea de mai jos este **exemplu operator** pentru litere volumetrice. Template-uri noi **definesc propria secvență**.

| # | Task (operator) | Condiție | CostEngine ref (dacă există) |
|---|-----------------|----------|------------------------------|
| 1 | Verificare fișier/vector | always | readiness gate |
| 2 | Prepress / pregătire grafică | always | `vector_prep` |
| 3 | Debitare CNC față plexiglas | always | `face_cnc_cut` (pass 1) |
| 4 | Șanfren față plexiglas | always | `face_cnc_cut` (pass 2) |
| 5 | Debitare spate Forex | always | `back_cut` (3 passes default) |
| 6 | Șanfren spate | `back_bevel_enabled=true` | `back_cut` (+2 passes) |
| 7 | Formare cant aluminiu | always | `side_forming` |
| 8 | Lipire cant pe fața literelor | always | `return_face_bonding` |
| 9 | Vopsire / finisare RAL | always | `painting` + `MAT-VOPSEA-RAL` |
| 10 | Aplicare autocolant | `face_finish_type != none` | `vinyl_application` + vinyl mat |
| 11 | Montaj LED | always | `led_install_letters` |
| 12 | Cablare electrică | always | `electrical_letters` |
| 13 | Pregătire șablon montaj | `mounting_template_enabled=true` | `mounting_template_cnc_cut` + sablon |
| 14 | Pregătire bare premontaj | `mounting_system=steel_bars\|aluminum_bars` | premount material lines |
| 15 | QC intern | always | `qc_letters` (internal-only) |
| 16 | Ambalare | always | `packaging_letters` |

**Validare:** task order verificat prin teste dossier, smoke browser/API, sau review owner.

**Seed referință:** `backend/seeds/seed_tpl_volumetric_letters_dossier.py` → `_task_rules()`.

---

## 20. Output blocks

`output_blocks_json` definește ce apare în:

| Audience | Conținut tipic |
|----------|----------------|
| Customer-facing | Rezumat ofertă, dimensiuni, opțiuni selectate |
| Production | Fișă producție, materiale, culori RAL/Oracal |
| Internal | Readiness messages, note QC |
| Warnings | Opțiuni neprețuite, template separat necesar |

**Reguli:**

- Variabile din `quote_input` — nu inventa valori
- Ce rămâne intern (QC, calibrare) nu apare ca linie client
- `approval_status` pe blocuri — draft vs approved
- Teste: `test_output_blocks_render_preview.py` pattern

---

## 21. SVG / vector / layer mapping

- [ ] Layere SVG mapate la `template_code` exact
- [ ] Layere nemapate → mesaj clar, nu metrici inventate
- [ ] Vector file poate fi gate readiness (`letters_vector_file_required`)
- [ ] Simulate preliminar poate rula fără vector; quote final poate fi blocat
- [ ] SVG analiză **nu înlocuiește** automat tot contractul (ex: perimetru litere poate rămâne manual)

---

## 22. Dossier and task seed strategy

1. [ ] Creează seed idempotent dedicat template — ex: `seed_tpl_<code>_dossier.py`
2. [ ] Runner script în `backend/scripts/` (opțional dar recomandat)
3. [ ] Upsert pe `template_id` — **fără duplicate**
4. [ ] Include: mapping, output blocks, task rules, variante
5. [ ] **Nu modifica** alte template-uri
6. [ ] **Nu muta** pricing/CostEngine în seed dossier
7. [ ] Teste idempotency — ex: `test_tpl_volumetric_letters_dossier.py`

```bash
# Exemplu volumetric
cd backend
.venv/Scripts/python.exe scripts/seed_tpl_volumetric_letters_dossier.py
```

---

## 23. Testing checklist

### Backend
- [ ] Formula handlers — toate `formula_id`
- [ ] CostEngine line totals pe payload referință
- [ ] Missing input → NEEDS_QUOTE_INPUT
- [ ] No silent zero
- [ ] Pricing registry / owner-confirmed prices
- [ ] Currency mismatch
- [ ] Active template scope
- [ ] Dossier readiness (mapping, output blocks, task rules)
- [ ] Internal-only ops — no blocker
- [ ] Conditional options (back bevel, finish, mounting)
- [ ] Quote input policy warnings

### Frontend
- [ ] QuoteWizard field specs + validation
- [ ] Payload builder
- [ ] Work Intake prefill mapping
- [ ] ProductSystem UI (dacă atins)

### Quality gates
- [ ] Niciun preț hardcodat în CostEngine
- [ ] Niciun test acceptă zero fără `skipped`/error explicit

---

## 24. API / browser smoke checklist

- [ ] Pricing Registry se încarcă fără crash
- [ ] ProductSystem — template activ vizibil
- [ ] QuoteWizard — câmpuri contract vizibile
- [ ] `POST /api/v1/product-system/simulate-cost` — `persisted=false`
- [ ] **Nu se creează quote/order** (verifică count înaină/după)
- [ ] Blueprint Dossier se deschide
- [ ] Readiness state explicabil (`ready_for_quote`, warnings)
- [ ] Baseline total pe payload referință
- [ ] Deltas pe opțiuni cheie documentate
- [ ] Task/readiness visibility în UI dacă aplicabil

**Payload referință volumetric:**

```
width_mm=4800, letter_face_area_m2=2.88, letter_perimeter_m=18,
letter_count=9, mounting_template_enabled=true, direct_wall
→ total 844.41 EUR
```

**Deltas validate:** steel bars +19.20; aluminum +33.60; template off → 800.13.

---

## 25. Backup / export practice

**Înainte de modificări majore** la logică template / CostEngine / dossier:

1. [ ] `git status` — working tree curat pe fișiere tracked
2. [ ] Export ZIP cu sursă + **DB local** (`backend/dev.db`)
3. [ ] Exclude: `node_modules`, `.venv`, `.git`, caches, `.env` (secrets)
4. [ ] Include: `.env.example`, `BACKUP_MANIFEST.txt` în ZIP
5. [ ] Output: `exports/workos_clean_snapshot_<YYYYMMDD_HHMM>.zip`
6. [ ] **Nu commita** `exports/` în git

**Exemplu validat:** `exports/workos_clean_snapshot_20260606_1808.zip` (~2 MB, include `dev.db`).

**Restore:** unzip → reinstall deps → DB la path relativ → start backend/frontend.

---

## 26. PASS / FAIL criteria for a new template

### PASS (toate)

- [ ] Active scope corect
- [ ] Pricing rows există sau gaps = warnings intenționate
- [ ] CostEngine calculează liniile așteptate
- [ ] Fără zero silențios
- [ ] QuoteWizard colectează input required
- [ ] Work Intake mapează alegeri business
- [ ] Dossier există (`approved` sau draft documentat)
- [ ] `task_rules_json` populat și validat
- [ ] `output_blocks_json` populat
- [ ] `costengine_mapping_json` populat
- [ ] Readiness state explicabil
- [ ] Teste PASS
- [ ] Smoke PASS
- [ ] Fără quote/order side effects
- [ ] Fără template-uri unrelated modificate

### FAIL (oprire imediată)

- Card ProductSystem fără contract input
- Template fără Pricing Registry pentru linii quote-priced
- Prețuri în CostEngine
- Profil necunoscut prețuit ca profil default
- QC/LASER/ASSEMBLY generic blochează fără decizie owner
- Readiness bypass
- `task_rules_json` sau `output_blocks_json` lipsă
- Template archived modificat
- Smoke „PASS” cu blockers ascunse

---

## 27. Anti-patterns

| Anti-pattern | De ce e greșit |
|--------------|----------------|
| Doar card ProductSystem UI | Template invizibil în costing |
| Template fără Pricing Registry | Rate lipsă sau inventate |
| Pricing fără QuoteWizard inputs | Opțiuni necontrolate |
| Prețuri hardcodate în CostEngine | Imposibil de auditat |
| Hourly ca default | Nealiniat cu unități producție |
| QC intern ca blocker de rate | Blochează simulate fără motiv |
| ASSEMBLY generic duplicat | Cost dublat, sens neclar |
| Zero silențios la input lipsă | Ofertă subestimată |
| Profil necunoscut = preț profil default | Comercial incorect |
| `forex_template` ca `mounting_system` | Amestecă suport cu șablon |
| ACM / produs complex în template greșit | Dimensiuni și prețuri greșite |
| Readiness bypass pentru UI verde | Quote invalid în producție |
| Hard delete template | Pierdere istoric |
| Activare experimental prea devreme | Regresii în scope live |
| **Ignorare ordine task producție** | Execuție atelier incorectă |
| **`task_rules_json` lipsă** | Template „complet” doar pe hârtie |
| **`output_blocks_json` lipsă** | Output quote/producție nedefinit |
| CostEngine operation = task automat | Ordine și condiții greșite |
| Commit `exports/` sau secrets | Risc securitate/repo |

---

## 28. Example appendix: TPL-VOLUMETRIC-LETTERS (illustrative only)

| Aspect | Stare curentă |
|--------|---------------|
| Scope | Singur template activ |
| Baseline | **844.41 EUR** (simulate, no cost blockers) |
| Operations | Unit-based (per letter, ml, mp, buc) |
| Back bevel | Opțional `back_bevel_enabled` |
| Paint | Tuburi întregi `MAT-VOPSEA-RAL` + serviciu `PAINTING` separat |
| Face finish | Oracal / print / laminat — registry |
| Mounting template | Independent `mounting_template_enabled` |
| Premount bars | `width_mm/1000 × 2` sau override; profil `30x30x1.5` prețuit |
| ACM panel | Warning template separat — fără preț aici |
| QC | `internal_only` |
| Dossier | `approved`, seed `fe0be10` |
| quote-ready | **false** — vector/file gate |
| Docs | `TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md`, `TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` |

---

## 29. Final onboarding checklist (pentru Cursor / agent)

Copiază și bifează la fiecare template nou. **Nu copia** conținutul Product 001 — doar pașii procesului (vezi secțiunea 2).

### A. Owner decisions
- [ ] Secțiunea 6 completată cu owner
- [ ] Ce nu e prețuit încă = warnings documentate
- [ ] Ordine producție agreată

### B. Template identity
- [ ] `template_code` canonic ales
- [ ] family/category setat
- [ ] active vs archived clar
- [ ] Scope activ confirmat

### C. Components
- [ ] `components_json` definit
- [ ] Materiale și operații grupate corect

### D. Materials
- [ ] Cod, unitate, formulă per material
- [ ] Registry rows sau gap intenționat
- [ ] Fără preț în CostEngine

### E. Operations
- [ ] Workcenter + basis + formula
- [ ] `quote_priced` / `internal_only` setat
- [ ] Fără duplicate ASSEMBLY inutile

### F. Input contract
- [ ] Document audit creat/actualizat
- [ ] Required/optional/conditional/default
- [ ] Warnings policy

### G. Pricing
- [ ] Materiale `unit_cost` (excl. TVA)
- [ ] Workcenter rates
- [ ] Variante/profiluri
- [ ] Currency din Settings

### H. CostEngine
- [ ] Formule înregistrate
- [ ] Gates condiționale
- [ ] Teste no silent zero

### I. QuoteWizard
- [ ] Câmpuri + validare + helpers
- [ ] Payload builder
- [ ] Teste frontend

### J. Work Intake
- [ ] Mapări safe documentate
- [ ] Fără geometrie inventată

### K. Dossier
- [ ] Seed idempotent
- [ ] `costengine_mapping_json`
- [ ] `output_blocks_json`
- [ ] `task_rules_json`
- [ ] Teste dossier

### L. Task rules
- [ ] Ordine producție definită
- [ ] Condiții pe `quote_input`
- [ ] Internal-only tasks marcate
- [ ] Dependențe explicite

### M. Output blocks
- [ ] Customer + production + internal
- [ ] Teste render preview

### N. Readiness
- [ ] simulate-ready vs quote-ready documentat
- [ ] Fără bypass

### O. Tests
- [ ] Backend suite relevantă
- [ ] Frontend suite relevantă

### P. Smoke
- [ ] API simulate-cost cases
- [ ] Browser QuoteWizard (sau limitare documentată)
- [ ] quotes/orders count unchanged

### Q. Backup
- [ ] ZIP+DB înainte de schimbări majore (dacă build mare)

### R. Commit / report
- [ ] Docs architecture actualizate
- [ ] Commit focalizat (fără exports/unrelated)
- [ ] PASS/FAIL + hash commit raportat

---

## Referințe rapide comenzi (dev)

```bash
# Teste volumetrice (exemplu)
cd backend
.venv/Scripts/python.exe -m unittest tests.test_volumetric_finish_mounting_pricing tests.test_volumetric_quote_input_policy -v
.venv/Scripts/python.exe -m unittest tests.test_tpl_volumetric_letters_dossier -v

# Frontend
cd frontend
npm test -- --run src/lib/volumetricQuoteInput.test.ts

# Seed dossier volumetric
cd backend
.venv/Scripts/python.exe scripts/seed_tpl_volumetric_letters_dossier.py
```

**Documente sursă:**

- `docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md`
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`
- `backend/seeds/seed_tpl_volumetric_letters_dossier.py`
- `backend/services/product_readiness_service.py`

---

*Playbook finalizat din lecțiile `TPL-VOLUMETRIC-LETTERS`. Procesul (secțiunile 1–29) este universal; produsul volumetric este referință ilustrativă — secțiunea 2.*

# TPL-VOLUMETRIC-FACE-BACK-PREP — Template Contract & Implementation Roadmap

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `53173da`  
**Mode:** documentation + logical contract only — **no code, UI, CostEngine, stock, or DB changes**  
**Build label:** `BUILD_TPL_VOLUMETRIC_FACE_BACK_PREP_FULL_CONTRACT_AND_ROADMAP`  
**V1 implemented:** `BUILD_TPL_VOLUMETRIC_FACE_BACK_PREP_V1_CNC_ONLY_COST_DRAFT` — backend cost draft CNC-only (see `docs/qa/BUILD_TPL_VOLUMETRIC_FACE_BACK_PREP_V1_CNC_ONLY_COST_DRAFT.md`)

**Related docs studied:**

| Document | Status |
|----------|--------|
| `docs/audit/INTAKE_V4_OPERATOR_UI_PRODUCT_LOGIC_STUDY.md` | ✓ read |
| `docs/audit/INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md` | ✓ read |
| `docs/qa/BUILD_INTAKE_V4_OPERATOR_UI_TRUST_ALIGNMENT.md` | ✓ read |
| `docs/audit/INTAKE_V4_ALIGNMENT_AUDIT.md` | ✓ read |
| `docs/architecture/INTAKE_V4_REALITY_AND_UI_BOUNDARY.md` | ✓ read |
| `docs/architecture/INTAKE_V4_STEP_BY_STEP_ROADMAP.md` | **missing** — not in repo at audit time |

**Code references (read-only):**

- `backend/services/shared_cnc_operation_model.py` — CNC preview rows (`cnc_face_cutting_plexiglas_3mm`, `cnc_face_bevel_plexiglas_3mm`, …)
- `backend/services/intake_v4_cnc_router_pass_policy_service.py` — pass policy + 1.5 EUR/ml/pass rule
- `backend/services/intake_v4_material_breakdown_service.py` — material registry mapping
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py` — owner material prices
- `backend/seeds/seed_volumetric_workcenter_rates.py` — CNC_ROUTER, PREPRESS, FACE_VINYL_APPLICATION_LABOR
- `frontend/src/lib/intakeV4/intakeV4QuoteGeometry.ts` — client-side geometry fields
- `docs/qa/BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT.md` — CNC/bevel audit baseline

---

## 1. Verdict scurt

**`TPL-VOLUMETRIC-FACE-BACK-PREP`** este un **template parțial** pentru pregătirea fețelor din plexiglas și a spatelui din Forex pentru litere volumetrice.

Nu calculează cant, LED, suport, montaj sau asamblare completă.

Scopul lui este **cost intern de producție pentru față + spate** (materiale + operații CNC + finisaj față opțional + pregătire fișiere), ca **draft operator-review**, nu ofertă client finală.

---

## 2. Ce problemă rezolvă

Nu toate comenzile de litere volumetrice cer produs complet. Uneori trebuie pregătite doar fețele și spatele (debitate, șanfrenate, eventual finisate), fără cant, iluminare sau montaj.

Dacă forțăm template-ul complet **`TPL-VOLUMETRIC-LETTERS`**, sistemul:

- cere date inutile (LED, cant, PSU, lipire, montaj);
- poate calcula greșit (ex. `back_cut` phantom când backing lipsește — documentat în CNC audit);
- supraîncarcă operatorul cu panouri și readiness gates irelevante pentru o comandă parțială.

Acest template permite:

- **comandă parțială** controlată;
- **cost intern mai simplu** (ProductionCostDraft);
- **operații CNC clare** — debitare separată de șanfren/canal;
- **șanfren obligatoriu pe plexiglas**, opțional pe Forex;
- **reutilizare ulterioară** ca modul în template-ul complet de litere volumetrice.

---

## 3. Ce include

- pregătire fișiere CNC;
- pregătire fișiere print, dacă finisajul cere print / Oracal / policromie;
- față plexiglas 3 mm;
- debitare CNC față;
- **șanfren/canal CNC față — obligatoriu**;
- spate Forex 10 mm;
- debitare CNC spate;
- **șanfren/canal CNC spate — opțional**;
- finisaj față: simplu / Oracal / print / print + laminare / policromie (dacă sistemul are datele);
- **cost intern draft** pentru materiale și operații (`ProductionCostDraft`).

---

## 4. Ce exclude

- cant / volum;
- formare cant la utilaj;
- lipire cant pe plexiglas;
- colantare cant;
- LED;
- cabluri;
- surse / trafuri;
- suport;
- montaj;
- asamblare finală;
- test lumină;
- taskuri reale;
- stock consumption;
- quote client final;
- CostEngine final / ExecutionPlan / `tasks_json`.

Acestea aparțin template-ului complet **`TPL-VOLUMETRIC-LETTERS`** sau altor module (montaj, iluminare, cant).

---

## 5. Definiție șanfren (canal CNC)

### Ce este

Șanfrenul este un **canal tehnic frezat CNC** pe conturul piesei, aproape de marginea plexiglasului / Forexului, folosit pentru poziționarea, fixarea și închiderea ansamblului volumetric.

### Ce nu este

- teșire decorativă;
- bizotare;
- simplu finisaj vizual;
- rotunjire muchie.

### Rol în litere volumetrice

- poziționarea cantului / volumului;
- fixarea mai precisă a ansamblului;
- ghidarea pieselor;
- controlul luminii / scăpărilor de lumină;
- repetabilitate la montaj;
- calitate tehnică mai bună.

### Mapare terminologie existentă în cod

| Termen contract | Termen cod existent |
|-----------------|---------------------|
| șanfren / canal CNC | `bevel`, `CncOperationType.BEVEL`, `cnc_face_bevel_plexiglas_3mm` |
| backing șanfren toggle | `forex_10_with_bevel` / `back_bevel_enabled` |

---

## 6. Componente canonice

### 6.1 `FACE_PLEXI`

| Atribut | Valoare |
|---------|---------|
| `component_key` | `FACE_PLEXI` |
| `material` | plexiglas |
| `default_thickness_mm` | 3 |
| `requires_shanfren` | **true** (obligatoriu) |
| `shanfren_type` | `cnc_channel` |
| `finish_options` | `none` \| `oracal` \| `print` \| `print_laminate` \| `policromie` |
| `material_price_source` | `prices_registry` → `MAT-ACP-FATA-LITERE` |

**Operații:**

| Operation key | Descriere | Condiție |
|---------------|-----------|----------|
| `file_preparation_cnc` | Pregătire fișier CNC | mereu când FACE_PLEXI activ |
| `file_preparation_print` | Pregătire fișier print | dacă finisaj = print / print_laminate / policromie |
| `cnc_cut_face_plexi` | Debitare CNC față | obligatoriu |
| `cnc_shanfren_face_plexi` | Șanfren/canal CNC față | **obligatoriu**, tarif separat |
| `face_vinyl_application` | Aplicare Oracal | dacă `face_finish = oracal` |
| `face_print` | Print față | dacă `face_finish = print` |
| `face_lamination` | Laminare | dacă `face_finish = print_laminate` |

**Consumuri:**

- `plexiglas_sqm`
- `cnc_cut_length_ml`
- `cnc_shanfren_length_ml`
- `face_vinyl_sqm` (Oracal)
- `print_sqm` (print)
- `laminate_sqm` (print + laminare)

---

### 6.2 `BACK_FOREX`

| Atribut | Valoare |
|---------|---------|
| `component_key` | `BACK_FOREX` |
| `material` | forex |
| `default_thickness_mm` | 10 |
| `requires_shanfren` | **false** (default) |
| `shanfren_type` | `cnc_channel` (opțional) |
| `mounting_context` | `flat_support` \| `metal_bars` \| `raised_support` \| `manual` |
| `material_price_source` | `prices_registry` → `MAT-SPATE-PVC-LITERE` |

**Operații:**

| Operation key | Descriere | Condiție |
|---------------|-----------|----------|
| `cnc_cut_back_forex` | Debitare CNC spate | obligatoriu când BACK_FOREX activ |
| `cnc_shanfren_back_forex` | Șanfren/canal CNC spate | doar dacă șanfren Forex activ |
| `drill_mounting_holes` | Găuri montaj | dacă există input/flag **și** tarif |

**Consumuri:**

- `forex_sqm`
- `cnc_cut_length_ml`
- `cnc_shanfren_length_ml` (dacă activ)
- `mounting_holes_count` (dacă se taxează)

---

## 7. Reguli operaționale

### 7.1 Față plexiglas

Dacă **`FACE_PLEXI`** este activ:

- plexiglas **3 mm** este material default;
- materialul se preia din **prices / registry** (`MAT-ACP-FATA-LITERE`);
- debitarea CNC este **obligatorie**;
- șanfrenul/canalul CNC este **obligatoriu**;
- șanfrenul este **operație separată** de debitare;
- costul debitării = **1.5 EUR/ml** (regulă fixă confirmată owner);
- costul șanfrenului = **1.5 EUR/ml** — operație separată de debitare, același tarif confirmat owner (V1).

### 7.2 Spate Forex

Dacă **`BACK_FOREX`** este activ:

- Forex **10 mm** este material default;
- materialul se preia din **prices / registry** (`MAT-SPATE-PVC-LITERE`);
- debitarea CNC este **obligatorie**;
- șanfrenul Forex este **opțional**;
- default: **nu** se aplică șanfren Forex;
- șanfren Forex se poate activa manual sau în funcție de context montaj;
- costul debitării = **1.5 EUR/ml**;
- costul șanfrenului, dacă activ, = **1.5 EUR/ml** (operație separată).

**Când se folosește de obicei șanfren Forex:**

- litere montate pe bare metalice;
- litere montate pe suport distanțat;
- risc de lumină prin spate;
- decizie operator tehnică.

**Când de obicei nu este necesar:**

- montaj pe suport plan, spate închis;
- fără LED / fără deschidere spate (context parțial).

### 7.3 Regula montaj pentru șanfren Forex

| `mounting_context` | Șanfren Forex default |
|--------------------|------------------------|
| `flat_support` | **false** |
| `metal_bars` | recommended / operator decision |
| `raised_support` | recommended / operator decision |
| `manual` | operator decide |

---

## 8. CNC passes / operații CNC (contract owner)

Cost CNC = **perimetru vectorial real × număr treceri × 1.5 EUR/ml**.

Modelul folosește **rânduri de operație separate**; fiecare rând poate avea `pass_count` > 1.

### Față plexiglas 3 mm

```txt
P_face = perimetru vectorial CNC al feței
```

| Operație | pass_count | Cost |
|----------|------------|------|
| Debitare contur (`cnc_cut_face_plexi`) | **1** | P_face × 1 × 1.5 EUR |
| Frezare canal șanfren (`cnc_shanfren_face_plexi`) | **1** | P_face × 1 × 1.5 EUR |

**Total față:** P_face × **2** × 1.5 EUR

### Spate Forex 10 mm — fără șanfren

```txt
P_back = perimetru vectorial CNC al spatelui
Forex 10 mm fără șanfren = 3 treceri CNC (ceil(10 mm / 3.5 mm))
```

| Operație | pass_count | Cost |
|----------|------------|------|
| Debitare contur (`cnc_cut_back_forex`) | **3** | P_back × 3 × 1.5 EUR |

### Spate Forex 10 mm — cu șanfren

```txt
trecere adâncime = 3.5 mm
Forex = 10 mm → 3 treceri debitare
șanfren/canal adânc = 7 mm → 2 treceri suplimentare
total = 5 treceri CNC
```

| Operație | pass_count | Cost |
|----------|------------|------|
| Debitare contur | **3** | P_back × 3 × 1.5 EUR |
| Frezare canal șanfren | **2** | P_back × 2 × 1.5 EUR |

**Total spate cu șanfren:** P_back × **5** × 1.5 EUR

**Greșit:** P_back × 1.5 + P_back × 1.5 (1+1 treceri) — nu reflectă grosimea Forex 10 mm.

### Găuri / pocketing / marcaje

Găurile, marcajele și pocketing-ul trebuie tratate ca **operații separate** dacă sistemul le suportă. **Nu se inventează tarif** pentru găuri dacă nu există în registry.

### Notă de aliniere cu codul existent

Pass-count-urile sunt aliniate cu `intake_v4_cnc_router_pass_policy_service.py` (`face_plexi_cnc_passes`, `forex_backing_cnc_passes`) și cu modelul owner din `TPL-VOLUMETRIC-LETTERS` (`FOREX_10MM_CUTTING_PASSES_OWNER = 5`).

---

## 8.1 Vector perimeter is source of truth

**Perimetrul vectorial calculat din traseul CNC este sfânt.**

Nu se înlocuiește cu:

- bbox perimeter;
- nesting placement perimeter;
- simplified polygon perimeter;
- raster/OCR;
- estimated text character length;
- transformed/smoothed/simplified path length;
- perimetru pierdut prin conversie.

Chei acceptate V1:

- față: `cnc_cutting_perimeter_ml`, `face_cutting_perimeter_ml`, `cutting_perimeter_ml`
- spate: `backing_cnc_cutting_perimeter_ml`, `back_cutting_perimeter_ml`

Dacă lipsește perimetrul vectorial pentru o componentă CNC:

```txt
status = manual_required
warning = vector_perimeter_missing_or_low_confidence
```

**Nu se inventează cost numeric din bbox sau fallback față→spate pentru CNC.**

Fallback arie față→spate rămâne permis **doar pentru material** (mp), nu pentru CNC.

---

## 9. Cost CNC — regulă fixă

```
Cost operație CNC = perimetru_vectorial_ml × pass_count × 1.5 EUR
```

Tariful **1.5 EUR/ml** se aplică **per trecere CNC** pe perimetrul vectorial real.

**Nu se aplică pe:**

- arie (mp);
- bbox;
- nesting layout;
- perimetru rescris sau aproximat.
- găuri;
- frezări speciale;
- pocketing;
- print;
- colantare;
- material.

Acestea au **rânduri separate** în `ProductionCostDraft`.

**Sursă în sistem:** workcenter registry `CNC_ROUTER`, `rate_per_linear_meter = 1.5`, `currency = EUR` — `backend/seeds/seed_volumetric_workcenter_rates.py`.

---

## 10. Model cost intern draft

### 10.1 `ProductionCostDraft`

```ts
ProductionCostDraft = {
  templateKey: "TPL-VOLUMETRIC-FACE-BACK-PREP",
  currency: "EUR",
  materials: MaterialCostRow[],
  operations: OperationCostRow[],
  missingPrices: MissingPrice[],
  manualInputsRequired: ManualInput[],
  warnings: CostWarning[],
  confidence: "draft" | "operator_reviewed"
}
```

### 10.2 `MaterialCostRow`

```ts
{
  component: "FACE_PLEXI" | "BACK_FOREX",
  materialKey: string,
  materialLabel: string,
  thicknessMm: number,
  quantity: number,
  unit: "sqm",
  priceSource: "prices_registry" | "manual" | "missing",
  unitPrice: number | null,
  currency: "EUR" | "RON",
  cost: number | null,
  status: "calculated" | "missing_price" | "manual_required"
}
```

### 10.3 `OperationCostRow`

```ts
{
  operationKey: string,
  operationLabel: string,
  component: "FACE_PLEXI" | "BACK_FOREX",
  quantity: number,
  unit: "ml" | "sqm" | "min" | "pcs",
  unitPrice: number | null,
  currency: "EUR" | "RON",
  priceSource: "fixed_rule" | "prices_registry" | "manual" | "missing",
  cost: number | null,
  status: "calculated" | "missing_price" | "manual_required" | "optional"
}
```

### 10.4 Operații default (seed logic)

```ts
[
  {
    operationKey: "cnc_cut_face_plexi",
    operationLabel: "Debitare CNC față plexiglas",
    component: "FACE_PLEXI",
    unit: "ml",
    unitPrice: 1.5,
    currency: "EUR",
    priceSource: "fixed_rule"
  },
  {
    operationKey: "cnc_shanfren_face_plexi",
    operationLabel: "Șanfren/canal CNC față plexiglas",
    component: "FACE_PLEXI",
    unit: "ml",
    unitPrice: 1.5,
    currency: "EUR",
    priceSource: "fixed_rule",
    status: "calculated"
  },
  {
    operationKey: "cnc_cut_back_forex",
    operationLabel: "Debitare CNC spate Forex",
    component: "BACK_FOREX",
    unit: "ml",
    unitPrice: 1.5,
    currency: "EUR",
    priceSource: "fixed_rule"
  },
  {
    operationKey: "cnc_shanfren_back_forex",
    operationLabel: "Șanfren/canal CNC spate Forex",
    component: "BACK_FOREX",
    unit: "ml",
    unitPrice: 1.5,
    currency: "EUR",
    priceSource: "fixed_rule",
    status: "calculated_when_enabled"
  }
]
```

**Operații suplimentare (non-default, condiționate):**

| Operation key | Component | Unit | Price source |
|---------------|-----------|------|--------------|
| `file_preparation_cnc` | both | `pcs` (litere) | registry `PREPRESS` — 2 EUR/literă |
| `file_preparation_print` | FACE_PLEXI | TBD | **missing / owner decision** |
| `face_vinyl_application` | FACE_PLEXI | `sqm` | registry `FACE_VINYL_APPLICATION_LABOR` — 5 EUR/m² |
| `face_print` | FACE_PLEXI | `sqm` | material `MAT-VINYL-PRINT` — 10 EUR/m² |
| `face_lamination` | FACE_PLEXI | `sqm` | material `MAT-VINYL-PRINT-LAMINATED` — 10 EUR/m² (combined row today) |
| `drill_mounting_holes` | BACK_FOREX | `pcs` | **missing** |

---

## 11. Consumuri necesare

### Față plexiglas

| Consum | Unit | Condiție |
|--------|------|----------|
| `plexiglas_sqm` | m² | mereu |
| `cnc_cut_length_ml` | ml | mereu |
| `cnc_shanfren_length_ml` | ml | mereu (obligatoriu) |
| `face_vinyl_sqm` | m² | Oracal |
| `print_sqm` | m² | print |
| `laminate_sqm` | m² | print + laminare |

### Spate Forex

| Consum | Unit | Condiție |
|--------|------|----------|
| `forex_sqm` | m² | mereu când BACK_FOREX activ |
| `cnc_cut_length_ml` | ml | mereu |
| `cnc_shanfren_length_ml` | ml | dacă șanfren Forex activ |
| `mounting_holes_count` | buc | dacă se taxează găuri |

---

## 12. Surse cantități din sistem

| Quantity | Possible source today | Confidence | Needs manual review? |
|----------|----------------------|------------|----------------------|
| Arie față (`plexiglas_sqm`) | `quote_geometry.face_area_m2`; material breakdown row `plexiglas_face`; nesting `selected_quote_sheet_area_sqm` (review floor) | **high** pentru geometry; **medium** pentru sheet allocation | Da — când `requires_manual_review` / footprint override |
| Arie spate (`forex_sqm`) | `backing_area_m2` dacă există; altfel fallback `face_area_m2` (warning în breakdown) | **medium** — fallback documentat | Da — când lipsește backing layer dedicat |
| Selected review area | `sheet_quote_material_candidates.selection.selected_quote_sheet_area_sqm` | **high** (policy) | Da — `is_applied_to_quote=false` |
| Nesting footprint | `nesting_preview` placement bbox / sheet allocation | **medium** — estimare layout | Da — nu e consum stoc |
| Cut length față (`cnc_cut_length_ml`) | `cutting_perimeter_ml`, `face_cutting_perimeter_ml`, `cnc_cutting_perimeter_ml` (persisted `path_geometry_summary`) | **high** | Parțial — include outer + goluri (policy CNC audit) |
| Cut length spate | `backing_cnc_cutting_perimeter_ml` sau fallback `face_cutting_perimeter_ml` | **medium** | Da — fallback la față |
| Contur exterior LED (referință, **exclus** din acest template) | `led_perimeter_ml` | high | Nu — nu se folosește în face/back prep |
| Contur cant (referință, **exclus**) | `return_material_perimeter_ml` | high | Nu |
| Shanfren length candidate | **derived** = același contur ca debitare CNC (outer + goluri) în audit CNC existent; `bevel_perimeter_ml` = `cnc_cutting_perimeter_ml` | **medium** | **Da — operator review obligatoriu** |
| Goluri / interioare count | `inner_holes_count` | high | Informativ |
| Piese producție (vector) | `real_letters_count` | high | Da — nu confunda cu caractere text (OCR interzis) |
| Găuri montaj | layer role `drill` (V3/V4 classification) | **low** — fără tarif | Da |
| Finisaj față area | `letter_group_finishes[].face_area_m2` sau total `face_area_m2` | medium | Da per grup |

**Regulă explicită:**

```
shanfren_length_ml = derived candidate from contour length, requires operator review
```

---

## 13. Surse prețuri

| Price item | Source today | Found? | Notes |
|------------|--------------|--------|-------|
| Plexiglas 3 mm | `MAT-ACP-FATA-LITERE` — `seed_volumetric_owner_confirmed_prices.py` | **Yes** | 16 EUR/m² purchase, excl. TVA |
| Forex 10 mm | `MAT-SPATE-PVC-LITERE` | **Yes** | 16 EUR/m²; cod istoric PVC, display Forex 10 mm |
| Oracal 651 material | `MAT-ORACAL-651` | **Yes** | 5 EUR/m² |
| Oracal aplicare manoperă | `FACE_VINYL_APPLICATION_LABOR` workcenter | **Yes** | 5 EUR/m² |
| Print material | `MAT-VINYL-PRINT` | **Yes** | 10 EUR/m² |
| Print + laminare material | `MAT-VINYL-PRINT-LAMINATED` | **Yes** | 10 EUR/m² combined row (nu laminare separată în registry) |
| Policromie | artwork complexity + print rows | **Partial** | Fără cod material dedicat; flux print/laminare artwork |
| RAL / policromie spray | `MAT-VOPSEA-RAL` + `PAINTING` service | **Yes** | tub 10 EUR + 4 EUR/ml service — **out of scope** finisaj cant; relevant doar dacă owner extinde față simplă vopsită |
| Debitare CNC | `CNC_ROUTER` `rate_per_linear_meter` | **Yes** | **1.5 EUR/ml** per operație debitare (rând separat) |
| Șanfren CNC față | `fixed_rule` (same rate key) | **Yes** | **1.5 EUR/ml** — operație separată, confirmat owner V1 |
| Șanfren CNC spate | `fixed_rule` (same rate key) | **Yes** | **1.5 EUR/ml** când activ — operație separată |
| Găuri montaj | `drilling` op în template complet | **No EUR/pcs** | Operație există în dossier; tarif per gaură nedefinit |
| Pregătire fișier CNC | `PREPRESS` / `vector_prep` | **Yes** | 2 EUR/literă (`letter_count`) — nu pe complexitate |
| Pregătire fișier print | artwork complexity ops | **Partial** | Preview rows în breakdown; tarif fix vs complexitate **nedecis** |

**Reguli:**

- Materialele se iau din **prices / registry**.
- Debitarea CNC = **1.5 EUR/ml** (rând `cnc_cut_*`).
- Șanfrenul/canalul = **1.5 EUR/ml** (rând `cnc_shanfren_*` separat).
- Afișarea cost draft păstrează rânduri separate; pe același contur: debitare + șanfren = **3 EUR/ml** operațional total, dar **nu** agregat într-un singur rând.

---

## 14. Automat vs manual

| Item | Automat | Manual | Motiv |
|------|---------|--------|-------|
| Detectare SVG / analiză | ✓ | | nest2 client analyzer |
| Arie față | ✓ | review | geometry + nesting policy floor |
| Arie spate | parțial | ✓ | fallback la față fără backing layer |
| Selected review area | ✓ | override | policy + operator footprint |
| Cut length | ✓ | review | persisted geometry; include goluri |
| Shanfren length | candidat | ✓ | derived = contour; owner review |
| Șanfren Forex activ/inactiv | default false | ✓ | mounting_context / operator |
| Finisaj față | parțial | ✓ | per letter group / artwork |
| Material preț | ✓ | | registry lookup |
| Preț șanfren | ✓ | review | 1.5 EUR/ml fixed_rule; lungime derived candidate |
| Găuri montaj | detect parțial | ✓ | fără tarif; fără UI dedicat V4 |
| Pregătire fișier CNC | ✓ (count litere) | | PREPRESS per literă |
| Pregătire fișier print | parțial | ✓ | complexitate artwork |

---

## 15. Ambiguități rămase

După regulile confirmate (inclusiv șanfren = 1.5 EUR/ml), următoarele rămân deschise:

1. **Șanfren plexiglas** — contur exterior doar sau și interioare/goluri? (audit CNC existent: **include goluri**, ca debitarea)
2. **Șanfren Forex** — contur exterior doar sau și interioare/goluri?
3. **Găurile de montaj** — taxate separat per bucata sau incluse în debitare?
4. **Pregătirea fișierului CNC** — fix per literă (2 EUR PREPRESS) sau pe complexitate?
5. **Pregătirea fișierului print** — fix sau pe complexitate artwork? *(Faza 2 — finisaje)*
6. **EUR vs RON** — EUR rămâne moneda internă pentru operații CNC sau conversie la raportare?
7. **Reconciliere pass-count Forex** — contract simplu 1.5 EUR/ml debitare vs `FOREX_10MM_CUTTING_PASSES_OWNER=5` în codul volumetric complet.
8. **Template key familie** — `TPL-VOLUMETRIC-FACE-BACK-PREP` vs `TPL-VOLUMETRIC-LETTERS-FACE-BACK-PREP` pentru registry ProductSystem.

---

## 16. Ce nu se face acum

- nu implementăm UI;
- nu legăm CostEngine final;
- nu creăm quote client;
- nu consumăm stock;
- nu creăm taskuri reale;
- nu creăm ExecutionPlan;
- nu folosim AI/OCR;
- nu implementăm template complet de litere volumetrice;
- nu calculăm cant / LED / suport / montaj;
- nu commit / push (acest build).

---

## 17. Plan de implementare propus

### Faza 1 — Contract MD ✓

Document creat și actualizat (șanfren 1.5 EUR/ml, V1 CNC-only).

### Faza 1b — V1 CNC cost draft ✓

Implementat: `tpl_volumetric_face_back_prep_cost_draft_service.py`, endpoint read-only, teste. Finisaje amânate Faza 2.

### Faza 2 — Template registry entry read-only

- Adaugă `TPL-VOLUMETRIC-FACE-BACK-PREP` în ProductSystem / template registry.
- Metadata: componente `FACE_PLEXI`, `BACK_FOREX`; exclude operații cant/LED.
- Nu calculează încă preț.

### Faza 3 — Consumption model face/back only

Construiește consumuri:

- m² materiale (față/spate);
- ml debitare;
- ml șanfren candidate;
- finisaj față condiționat.

Reutilizează `intake_v4_quote_geometry_service` + `shared_cnc_operation_model.build_volumetric_letters_cnc_operation_rows` cu scope redus (fără cant).

### Faza 4 — Production cost draft ✓ (V1 CNC-only)

Calculează material + operații CNC; warnings/manual inputs. Serviciu: `GET .../volumetric-face-back-prep/cost-draft`.

### Faza 4b — Finisaje față (Faza 2 — viitor)

Oracal, print, laminare, policromie, manoperă colantare — **out of V1 scope**.

### Faza 5 — Minimal internal cost table (UI)

UI minim (nu ecran mare):

Material / operație / cantitate / preț / cost / status.

Poate fi panou technical sau step Review dedicat template parțial.

### Faza 6 — Owner review

Owner verifică:

- arii;
- ml debitare;
- șanfren;
- prețuri lipsă;
- coerența formulei vs atelier.

### Faza 7 — Modul în template complet litere volumetrice

`TPL-VOLUMETRIC-FACE-BACK-PREP` devine **modul reutilizabil** în `TPL-VOLUMETRIC-LETTERS`:

- aceleași componente FACE_PLEXI / BACK_FOREX;
- reconciliere pass-count / tarife șanfren;
- fără duplicare logică nesting/geometry.

---

## 18. Template key recomandat

| Opțiune | Recomandare |
|---------|-------------|
| **`TPL-VOLUMETRIC-FACE-BACK-PREP`** | **Primary** — scurt, clar, partial template |
| `TPL-VOLUMETRIC-LETTERS-FACE-BACK-PREP` | Alternativă dacă registry cere prefix familie volumetric |

Motiv: ProductSystem folosește deja `TPL-VOLUMETRIC-LETTERS` ca template complet; sufixul `-FACE-BACK-PREP` semnalează scope parțial fără a implica același dossier/operation count.

---

## 19. Criterii PASS pentru document

| Criteriu | Status |
|----------|--------|
| Definește clar template parțial | ✓ |
| Include ce intră / ce nu intră | ✓ |
| Explică șanfren ca canal CNC | ✓ |
| Șanfren plexiglas obligatoriu | ✓ |
| Șanfren Forex opțional | ✓ |
| Plexiglas 3 mm / Forex 10 mm default | ✓ |
| Debitare 1.5 EUR/ml | ✓ |
| Separă debitare de șanfren | ✓ |
| Nu inventează prețuri lipsă | ✓ |
| Propune ProductionCostDraft | ✓ |
| Listează ambiguități | ✓ |
| Propune faze implementare | ✓ |
| Nu modifică cod | ✓ |

---

## 20. ProductSystem ownership

**Template truth belongs to ProductSystem**, not Intake V4.

| Concern | Owner |
|---------|--------|
| Template key, metadata, components, operations, material intent, draft task order | `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` + `product_templates` seed |
| Operator preview / workspace geometry | Intake V4 cost draft endpoint (consumer) |
| Final commercial pricing | CostEngine (future) |
| Real production tasks | Production handoff (future) |

Intake V4 **`GET …/volumetric-face-back-prep/cost-draft`** reads workspace state and registry material prices, then applies the ProductSystem contract. It is **not** the registry source of truth.

See also: `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_INTEGRATION.md`.

---

## 21. Boundary explicit

This contract document describes product intent. Runtime registry integration is documented in:

- `docs/qa/BUILD_TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_REGISTRY.md`
- `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_INTEGRATION.md`

Still **out of scope** for V1 partial template:

- React / Intake V4 UI changes;
- final CostEngine / Pricing Registry rate wiring;
- stock / inventory consumption;
- quote / order / real tasks / ExecutionPlan / `tasks_json`;
- finishes (Oracal, print, lamination, policromie).

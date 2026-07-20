# WORKOS_ACM_PANEL_PRODUCTION_GEOMETRY_METRICS_AND_PRICING_TRUTH_V1

| Field | Value |
|-------|--------|
| Status | **PLAN — awaiting owner GO** |
| Mode | Plan only — **no implementation in this step** |
| Date | 2026-07-20 |
| Branch baseline | `feature/product-system-active-path-isolation-v1` @ `e203012` |
| Prerequisite | Slice C PASS — `ab514f3` / docs `446fce3` (**do not revert**) |
| Owner DXF | `C:\Users\offic\Desktop\un-pliu.dxf`, `C:\Users\offic\Desktop\2-pliuri-100x30.dxf` |
| Measurement evidence | `docs/audits/_evidence/2026-07-20_acm-panel-production-geometry-metrics/` |
| Figma / 21st.dev | **NOT USED — NOT NEEDED** |

---

## 1. Rezumat

Slice C a corectat bug-ul multi-panel (face din assembly, cut/V din suma perimetrelor panourilor) și a livrat preview provizoriu onest pe fixture `IV6-DB2F86B7`. Acel rezultat (**0.700 mp / 5.4 ml / 5.4 ml**) este valid ca **proxy rectangular single-fold simplificat**, nu ca formulă generală de producție.

DXF-urile owner demonstrează clar:

| Caz | CUT | V L1 | V L2 | V total |
|-----|-----|------|------|---------|
| Single-fold (L2=0) | **5.400000 ml** | **5.400000 ml** | 0 | **5.400000 ml** |
| Double-fold (L1=100, L2=30) | **5.499412 ml** | **5.400000 ml** | **4.600004 ml** | **10.000004 ml** |

Concluzie plan: Pricing trebuie să **consume** metrici de producție (CUT / V L1 / V L2 măsurate), nu să le inventeze din `panel_perimeter` / `fold_sides=all`. Motorul geometric de generare+măsurare **nu există suficient în repo** — este necesar un **preparatory metrics contract** + generator/measurement path înainte de a înlocui Slice C ca truth.

---

## 2. Verdict A/B/C

### **B — Există geometrie / semnale, dar este necesar un preparatory metrics contract**

**Nu A:** Nu există în WorkOS un geometry generator AcmPanel care să emită și să măsoare trasee CUT / V-groove L1 / L2 parametrice. Blueprint L1-P este read-model vizual. `svgPathMetrics` măsoară path-uri SVG pentru litere, nu flat-pattern ACM. nest2 (menționat istoric pe Desktop) **nu este prezent** în mediul curent.

**Nu C:** Nu este cazul să înghețăm permanent Slice C ca singură realitate — owner DXF + `fold_count` / `l1_mm` / `l2_mm` pe instanță + CPP quantity paths oferă o cale clară de remediere. Slice C rămâne valid ca **preview provisional fallback explicit** pentru dreptunghi single-fold / multi-panel fără trasee, până la metrics completeness.

---

## 3. Scope

### In scope (viitor build — nu acum)

1. Contract canonic `AcmPanelProductionGeometryMetrics` (+ agregare assembly).
2. Measurement algorithm pe entități semantice (sau convenție color/layer owner).
3. Generator sau import path care produce metricile din configurație + L1/L2.
4. Wiring Pricing: CPP consumă measured CUT / V (nu inventează).
5. Fallback policy explicită; lipsă metrics → gap / blocked final.
6. Tests pe DXF owner + parametric + multi-panel.
7. UI honesty: quantity source în breakdown.

### Out of scope (acest Plan Mode + viitor build până la GO)

- Modificare / revert Slice C acum
- Rate changes / new rate codes
- Offer / Order / Execution / task_rules / DAG
- Migrations / seeds / Inventory writes
- Employee Mobile / Figma / 21st.dev
- Auto-promovare authority

---

## 4. Current Slice C audit

| Metric | Fișier | Funcție | Formula actuală | Input | Authority | Limită |
|--------|--------|---------|-----------------|-------|-----------|--------|
| `cut_quantity` → `panel_perimeter_m` | `backend/services/acm_commercial_geometry.py` | `compute_acm_commercial_geometry` / `apply_acm_commercial_geometry` | multi: `Σ 2×(pw+ph)/1000`; single: `2×(pw+ph)/1000`; fallback: assembly exterior | panel list / assembly | **Pricing adapter** (nu geometry SoT) | Nu cunoaște L1/L2 / corner relief / blank |
| `v_groove_quantity` → `fold_length_m` | same + `acm_quote_input_helpers._fold_length_mm` | `_fold_length_mm` apoi sumă per panel | `fold_sides=all` → `2×(w+h)` (= perimeter); tb/lr subset | `fold_sides` (default **"all"**) | Pricing adapter | **Egalare automată cu CUT** când `all`; **L2 ignorat** |
| `return_area` → `return_strip_area_m2` | `acm_commercial_geometry` / `derive_acm_casetted_quote_input` | fold_m × (return_depth_mm/1000) | `return_depth` din payload / finished_depth / default 60 | return_depth | Pricing adapter | Nu = blank_area; nu folosește L2 separat |
| `assembly_quantity` → `panel_area_m2` (alias) | `acm_commercial_geometry` | face = `assembly_w×assembly_h/1e6` | assembly keys A+B | assembly extent | Pricing adapter | Corect pentru face comercială multi-panel; nu e blank |
| `panel_perimeter_sum` | `acm_commercial_geometry` | sumă perimetre panouri | panels[] | panels | Observability / cut proxy | **Nu universal** |
| `assembly_exterior_perimeter` | `acm_commercial_geometry` | `2×(aw+ah)/1000` | assembly | Observability | **Nu înlocuiește CUT** |

CPP paths (`backend/data/commercial_rules_volumetric_v2.py`):

- `acm_panel_cut` ← `panel_perimeter_m`
- `acm_v_groove` ← `fold_length_m` (**o singură linie** — nu V L1 + V L2 separate)
- `acm_panel_face_material` / `acm_boxed_assembly` ← `panel_area_m2`
- `acm_return_strip_material` ← `return_strip_area_m2`

### Răspunsuri W1

| Întrebare | Răspuns |
|-----------|---------|
| Formula 5.4 vine din panel perimeter? | **Da**, pe fixture: 2×(1.0+0.35)×2 = 5.4 ml |
| `fold_sides=all` hardcodat? | **Default hard** în `_read_fold_sides` / `derive` dacă lipsește — runtime tipic `all` |
| Distincție single/double fold? | **Nu în Slice C.** Există `fold_count` / `l1_mm` / `l2_mm` pe instanță + Blueprint, **nefolosite** la cantități |
| L2 influențează V-groove? | **Nu** în Slice C |
| Geometry metrics există deja? | **Parțial:** contour dims, assembly extent, Blueprint construction — **nu** CUT/V measured |
| DXF generator calculează lungimi reale? | **Nu în repo** (nest2 absent) |
| SvgAnalyzer poate măsura aceste trasee? | Poate măsura path length SVG general (`svgPathMetrics` / `svg_path_metrics.py`) **dacă** există SVG semantic; **nu** parsează DXF; DXF = `dxf_analysis_not_supported` |
| Blueprint metric truth? | **Vizual / callouts L1-P** — `blueprintReadModel.ts`; **nu** lungimi CUT/V reutilizabile pentru Pricing |

---

## 5. DXF owner analysis

| Fișier | Entități | Layer | Semantică |
|--------|----------|-------|-----------|
| `un-pliu.dxf` | 5× `SPLINE` | toate pe `Layer 1` | **doar culoare ACI** |
| `2-pliuri-100x30.dxf` | 9× `SPLINE` | toate pe `Layer 1` | **doar culoare ACI** |

- `$INSUNITS = 4` → **mm**
- **Nu** există layer names tip CUT / V_GROOVE_L1 / V_GROOVE_L2
- Separarea semantică actuală = **ACI color**
- Tipuri: **doar SPLINE** (fără LINE / LWPOLYLINE în aceste fișiere)
- Corner relief: vizibil pe double-fold ca diferență CUT vs blank perimeter teoretic

### Convenție color observată (propunere de înghețat ca owner convention până la layer rename)

| Color | Rol propus | Single-fold | Double-fold |
|-------|------------|-------------|-------------|
| 256 (ByLayer) / 250 | **CUT** (closed outer) | 256 closed | 250 closed |
| 1 (red) | **V-groove L1** | 4 open | 4 open |
| 242 | **V-groove L2** | — | 4 open |

**Risc:** color-only este fragil. Recomandare plan: fie (1) SVG/DXF cu layer semantics exportate de generator, fie (2) convenție color **documentată + testată** ca interim SoT.

**SVG separat?** Nu obligatoriu dacă generatorul WorkOS emite DXF/SVG cu layers. Pentru import DXF owner raw, **da — necesar contract semantic** (layers sau color map versionat); altfel measurement rămâne heuristically.

---

## 6. Exact measured values

Măsurare: flattening SPLINE `distance=0.01` mm via `ezdxf` (evidence script).  
Fișier: `docs/audits/_evidence/2026-07-20_acm-panel-production-geometry-metrics/dxf-measure-by-color.json`

### Single-fold — `un-pliu.dxf`

| Metric | Exact |
|--------|-------|
| Blank envelope bbox | **2200.000 × 500.000 mm** |
| Active face (blank − 2×L1, L1=100) | **2000 × 300 mm** |
| L1 | **100 mm** (din inset) |
| L2 | **0** |
| CUT (color 256, closed) | **5400.0004 mm = 5.400000 ml** |
| V L1 (color 1, 4 entities) | **5400.0004 mm = 5.400000 ml** |
| V L2 | **0** |
| V total | **5.400000 ml** |
| CUT == V? | **Da, pe acest caz** (nu regulă generală) |

### Double-fold — `2-pliuri-100x30.dxf`

| Metric | Exact |
|--------|-------|
| Blank envelope bbox | **2260.000 × 560.000 mm** |
| Active face (blank − 2×(L1+L2), L1=100, L2=30) | **2000 × 300 mm** |
| L1 / L2 | **100 / 30 mm** |
| CUT (color 250, closed) | **5499.411831 mm = 5.499412 ml** |
| V L1 (color 1) | **5400.0004 mm = 5.400000 ml** |
| V L2 (color 242) | **4600.0036 mm = 4.600004 ml** |
| V total | **10000.004 mm = 10.000004 ml** |
| Blank perimeter teoretic (fără relief) | 2×(2260+560)=5640 mm |
| CUT vs blank perimeter | CUT mai scurt cu **~140.59 mm** → **corner relief / degajări** pe conturul CUT |

Owner expectations: CUT ≈5.5, V total ≈10 — **confirmate exact** (5.499412 / 10.000004).

---

## 7. Current formulas (Slice C — legacy after this plan)

```text
commercial_face_area_m2 = assembly_w_mm * assembly_h_mm / 1e6          # multi-panel OK
commercial_cut_length_m = Σ 2*(panel_w + panel_h) / 1000               # proxy
commercial_fold_length_m = Σ _fold_length_mm(panel, fold_sides) / 1000 # usually == cut
return_strip_area_m2 = fold_m * return_depth_m
assembly_exterior_perimeter_m = 2*(assembly_w + assembly_h)/1000       # observability
```

Default: `fold_sides = "all"` → cut ≡ v_groove pe dreptunghi.

---

## 8. Current risks

1. **Double-fold underpriced / wrong V:** Slice C nu adună V L2 → pe owner DXF ar trebui ~10 ml V, nu 5.4.
2. **CUT ≠ panel perimeter** când există corner relief / blank ≠ face.
3. **Silent equality CUT=V** ascunde double-fold.
4. **CPP are o singură linie `acm_v_groove`** — nu V L1 + V L2 separate; suma poate fi pe o linie, dar sursa trebuie measured total (sau split dacă owner vrea 2 linii — **gate**).
5. **DXF fără layers** — measurement automation fragilă.
6. **Stale uvicorn** (din Slice C) — procese vechi pot servi formule vechi; proof trebuie pe backend fresh.

---

## 9. Geometry ownership

| Adevăr | Owner | Consumer | Interzis |
|--------|-------|----------|----------|
| Active face W×H | AcmPanel instance / geometry | Geometry metrics, Pricing (face area) | Pricing inventează din envelope |
| L1 / L2 / fold_count | AcmPanel configuration + field_authority | Geometry generator | Catalog silent ca final |
| CUT path | Geometry generator / measured import | Pricing, Execution viitor | Panel-perimeter fallback silent |
| V L1 path | Geometry generator | Pricing, Execution viitor | Egalare automată cu CUT |
| V L2 path | Geometry generator | Pricing, Execution viitor | Ignorare L2 |
| Blank / return area | Geometry metrics | Pricing (`return_strip` / material) | Bounding-box-only |
| Rate | Pricing Registry | CPP | Geometry deține rate |
| Operation order | MIXED + OWNER_RULES | Execution viitor | Pricing / Blueprint |
| Product composition | Product Template | Intake | Component stolen identity |
| Component truth | Product System / AcmPanel component | PD, Aggregate, Pricing consumer | |

---

## 10. Proposed metrics contract

### Denumiri existente de evitat ca coliziune

- `AcmPanelGeometry` — contour / panels / joints (păstrat)
- `acm_commercial_geometry` / `acm_commercial_geometry_v1` — Slice C adapter (**devine legacy fallback layer**)
- Blueprint read-model — vizual

### Propunere canonică (schema nouă)

```text
acm_panel_production_geometry_metrics_v1
```

Câmpuri (panel):

```text
AcmPanelProductionGeometryMetrics
  schema: "acm_panel_production_geometry_metrics_v1"
  panel_id
  construction_type          # single_fold | double_fold | …
  active_width_mm
  active_height_mm
  l1_mm
  l2_mm
  active_face_area_m2
  blank_width_mm
  blank_height_mm
  blank_area_m2
  cut_length_ml
  v_groove_l1_ml
  v_groove_l2_ml
  v_groove_total_ml
  fold_l1_count
  fold_l2_count
  corner_relief_count
  source                     # generated | imported_dxf | imported_svg | unavailable
  quantity_completeness      # complete | partial | unavailable
  warnings[]
  entity_trace[]             # optional collapsed: type/layer/color/length
```

Agregare:

```text
AcmPanelAssemblyGeometryMetrics
  schema: "acm_panel_assembly_geometry_metrics_v1"
  assembly_width_mm
  assembly_height_mm
  panel_count
  joint_count
  panels[]                   # AcmPanelProductionGeometryMetrics
  total_active_face_area_m2
  total_blank_area_m2
  total_cut_length_ml
  total_v_groove_l1_ml
  total_v_groove_l2_ml
  total_v_groove_ml
  source
  warnings[]
  quantity_completeness
```

**Alias CPP (fără a distruge Slice C overnight):**

| CPP path azi | Viitor preferred | Note |
|--------------|------------------|------|
| `panel_area_m2` | `total_active_face_area_m2` | păstrează alias |
| `panel_perimeter_m` | `total_cut_length_ml` | **nu** perimeter |
| `fold_length_m` | `total_v_groove_ml` (= L1+L2) | o linie comercială rămâne; split UI optional |
| `return_strip_area_m2` | din blank − face sau strip formula measured | de decis la GO |

---

## 11. Single-fold semantics

- `fold_count = 1` sau `l2_mm = 0`
- O familie V (L1)
- CUT = contur blank (cu reliefuri dacă există)
- V poate = CUT **numai dacă** geometria reală produce egalitate (cazul owner DXF)

**Owner fixture (test, nu constantă):**

```text
face 2000×300, L1=100, L2=0
CUT = 5.400000 ml
V L1 = 5.400000 ml
V L2 = 0
V total = 5.400000 ml
blank = 2200×500
```

---

## 12. Double-fold semantics

- `fold_count = 2`, `l2_mm > 0`
- Două familii V
- CUT ≠ V total; CUT ≠ V L1
- Corner relief modifică CUT față de perimeter teoretic

**Owner fixture:**

```text
face 2000×300, L1=100, L2=30
CUT = 5.499412 ml
V L1 = 5.400000 ml
V L2 = 4.600004 ml
V total = 10.000004 ml
blank = 2260×560
```

**Interzis:** reutilizarea formulei single-fold / panel-perimeter ca truth.

---

## 13. Parametric dimensions

Recalcul la schimbare (generator + measure, nu constante):

| Input change | Affects |
|--------------|---------|
| active W/H | face area, blank, CUT, V L1/L2 |
| L1 | blank, CUT, V L1 (și poziții), return/blank area |
| L2 | blank, CUT, V L2, V total; L2=0 → single-fold |
| panel count | assembly aggregates (sum metrics) |
| unequal panels | per-panel metrics apoi sumă |
| offset panels | assembly extent (A+B) separat de sumă path lengths |

**Nu hardcoda** 2000 / 300 / 100 / 30 / 5.4 / 5.5 / 10 în producție — doar în teste golden DXF.

---

## 14. Multi-panel aggregation

```text
total_cut = Σ panel.cut_length_ml
total_v_l1 = Σ panel.v_groove_l1_ml
total_v_l2 = Σ panel.v_groove_l2_ml
total_v = total_v_l1 + total_v_l2
total_active_face = Σ panel.active_face_area_m2
  OR assembly_w×assembly_h când panourile formează ansamblu fără overlap
```

Reguli:

- Assembly W×H rămâne din A+B (extent), **nu** din blank sum.
- Joint-uri: informational; **fără rată inventată** (Slice C gap rămâne).
- Panouri inegale: metrics per panel, fără a asuma 2× identical.

Fixture WorkOS curent (2×1000×350): până există generator, **nu** pretinde că 5.4 este production CUT truth pentru double-fold catalog.

---

## 15. Entity support

| Entity | Support necesar | În owner DXF |
|--------|-----------------|--------------|
| SPLINE | **Obligatoriu** (aproximează length) | Da |
| LINE | Da | Nu acum |
| LWPOLYLINE / POLYLINE | Da (open/closed) | Nu acum |
| ARC | Da (r·Δθ) | Nu acum |
| CIRCLE | Optional | Nu |
| Closed / open paths | Da | Mix |
| Duplicate entities | Dedup by hash(geom+layer+color) | — |
| Layer names | Preferat | **Absent** |
| Color ACI | Interim semantic | **Folosit** |
| Units | `$INSUNITS` → mm | 4=mm |
| Tolerance | length round 1e-3 mm; compare ±0.05 mm | — |
| Joins | nu dubla colțuri partajate dacă split artificial | — |

**Nu** măsura prin bounding box perimeter.

---

## 16. Measurement algorithm

```text
for each entity in modelspace (or SVG path group):
  if semantic_class(entity) == CUT:
    cut_length_mm += length(entity)
  elif semantic_class == V_L1:
    v_l1_mm += length(entity)
  elif semantic_class == V_L2:
    v_l2_mm += length(entity)

cut_length_ml = cut_length_mm / 1000
v_groove_l1_ml = v_l1_mm / 1000
v_groove_l2_ml = v_l2_mm / 1000
v_groove_total_ml = v_groove_l1_ml + v_groove_l2_ml
```

`length(SPLINE)`: path flattening cu sagitta/distance mică (ex. 0.01 mm), sumă segmente.

`semantic_class`:

1. **Preferred:** layer name map versionat (`CUT`, `V_GROOVE_L1`, `V_GROOVE_L2`)
2. **Interim owner DXF:** color map v1 (256/250→CUT, 1→V_L1, 242→V_L2) — **necesită GO explicit**
3. Altfel: `quantity_unavailable`

---

## 17. Missing geometry behavior

| Situație | Preview | Final | Offer | Execution |
|----------|---------|-------|-------|-----------|
| Metrics `complete` | provisional OK (gates authority rămân) | după authority | după authority | blocked până Execution build |
| Metrics `partial` | provisional_with_warnings + gaps | **blocked** | **blocked** | **blocked** |
| Metrics `unavailable` | unavailable / incomplete | **blocked** | **blocked** | **blocked** |

Fallback panel-perimeter:

- **Interzis silent** pentru double-fold / L2>0 / fold_count=2
- **Permis** doar dacă **toate** sunt adevărate:
  - explicit flag `quantity_source=provisional_rectangular_single_fold_proxy`
  - `fold_count=1` sau `l2_mm=0`
  - panouri dreptunghiulare fără cutouts
  - warning vizibil în preview
  - final/Offer rămân blocate dacă authority o cere (ca Slice C)

---

## 18. Pricing consumer contract

```text
AcmPanel configuration (W,H,L1,L2,fold_count,panels)
  → production geometry (generate or import)
  → AcmPanelProductionGeometryMetrics / Assembly aggregate
  → CPP quantity binding
  → Pricing Registry rates (neschimbate)
  → acm_panel_commercial_preview (Slice C UI contract reused)
```

Pricing consumă:

- face area (active)
- return/blank area
- CUT measured
- V total measured (și opțional L1/L2 în breakdown)
- assembly qty (face)
- fasteners

Pricing **nu** generează DXF și **nu** deține path semantics.

---

## 19. Slice C impact

| Element | Soartă |
|---------|--------|
| Face din assembly multi-panel | **Rămâne valid** |
| Authority gates / provisional UI / copy | **Rămâne valid** |
| 6 rate codes + valori | **Neschimbate** |
| `panel_perimeter` ca CUT | **→ legacy fallback** (single-fold proxy only) |
| `fold_length` din `fold_sides=all` | **→ legacy**; înlocuit de `v_groove_total_ml` |
| Tests care fixează 5.4 pe fixture IV6 ca production truth | **De rescris** ca proxy/fallback sau ca unavailable |
| Fixture IV6 total ~66.52 EUR | **Poate rămâne** cât timp fallback proxy e încă activ; **se schimbă** când metrics complete există |
| Quantity source | **Schimbarea principală** |
| UI | Completare: sursa cantității în breakdown |

**Nu modifica Slice C în acest Plan Mode.** Remediation = build separat după GO.

---

## 20. UI honesty

În `AcmPanelProvisionalPricingBlock` / breakdown expandat:

| Linie | Sursă afișabilă |
|-------|-----------------|
| Față | `geometry.active_face` / assembly |
| Debitare | `CUT measured` \| `provisional rectangular proxy` \| `unavailable` |
| V-groove | `V total measured (L1+L2)` cu detalii L1/L2 collapsed |
| Fallback | badge provisional + warning |
| Unavailable | gap explicit; fără 0 silent |

Nu e obligatoriu expanded by default.

---

## 21. Tests

### Single-fold

- Golden `un-pliu.dxf` exact values (±0.05 mm)
- Dimension change regen/measure
- L2 absent → v_l2=0
- CUT==V doar pe golden, nu assert universal

### Double-fold

- Golden `2-pliuri-100x30.dxf` exact
- V L1, V L2, V total, CUT diferit
- Dimension / L1 / L2 change

### Multi-panel

- 2 egale; 2 inegale; assembly extent separat; sumă metrics

### Measurement

- SPLINE (+ LINE/POLY/ARC fixtures sintetice)
- duplicate prevention; units; tolerance

### Pricing

- metrics consumed; no hardcoded 5.4 in producer; no universal perimeter fallback; 6 rates unchanged; no hourly; gates blocked

### Regression

- Slice C fixture behavior under explicit fallback policy
- Blueprint L1-P; PD; Aggregate; Inventory; Registry; single-panel; Letters-only

---

## 22. Runtime proof plan

| Fixture | Route / API | Expected |
|---------|-------------|----------|
| Owner single-fold DXF | measurement harness / future import API | CUT=5.400000, V=5.400000 |
| Owner double-fold DXF | same | CUT=5.499412, Vtot=10.000004 |
| `IV6-DB2F86B7` | `GET .../priced-quote-dry-run` | până la generator: proxy marcat **sau** unavailable pe cut/V; face 0.700 rămâne |
| UI Review | `/intake-v6/{uuid}/operator` | quantity source honesty |
| Zero writes | expand/collapse | GET-only |
| Stale-process control | backend fresh port; refuse proof pe worker stale | |

---

## 23. Screenshots

La implementare (nu acum): Review breakdown cu surse; double-fold metrics; unavailable gap; Confirm continuity; inspector fără money (neschimbat).

---

## 24. Regression

Nu regresiona: Slice C gates, Blueprint L1-P, PD parity A+B, Inventory SKU, Registry rates, Letters live-calc fără ACM.

---

## 25. Dead pieces

| Piece | Clasificare |
|-------|-------------|
| `acm_commercial_geometry` perimeter cut/fold | **active** → va deveni **dangerous fallback** dacă e lăsat silent |
| `_fold_length_mm` + default `fold_sides=all` | **dangerous** pentru double-fold |
| Blueprint construction L1/L2 | **reusable** (inputs, nu lengths) |
| `svgPathMetrics` / `svg_path_metrics.py` | **reusable** algorithm kinship; nu ACM SoT |
| nest2 DXF export (istoric docs) | **dead / external missing** |
| Orphan ProductSystemPricingPreview | **dead** (deja interzis) |
| Color-only DXF fără contract | **dangerous** până la GO convention |
| Assembly exterior perimeter | **reusable observability** |

Nu șterge în Plan Mode.

---

## 26. Risks

1. Color map vs layer map — greșeala de clasificare ruinează prețul.
2. O singură linie CPP `acm_v_groove` vs dorința de a vedea L1/L2 — UI vs registry.
3. Generator inexistent → tentația de a „îmbunătăți” proxy-ul Slice C fără measurement.
4. Fixture IV6 cu `fold_count` catalog 2 + fără DXF → total se poate schimba la unavailable.
5. SPLINE approximation tolerance vs CAM real.

---

## 27. Implementation recommendation

1. **Freeze** Slice C ca provisional proxy (nemodificat până la GO remediation).
2. **Adopt** metrics contract + color/layer semantic map (owner GO).
3. **Build** measurement module (DXF/SVG entity length) + golden tests pe cele 2 DXF.
4. **Build** parametric generator **sau** import pipeline care umple metrics pe instanță.
5. **Wire** CPP aliases: cut←measured CUT, fold←V total; face rămâne assembly/active.
6. **UI** quantity source; fallback explicit.
7. Abia apoi: retrage silent perimeter pentru double-fold.

---

## 28. Implementation units (după GO)

| Unit | Deliverable |
|------|-------------|
| U1 | Schema + types FE/BE metrics contract |
| U2 | DXF/SVG measurement engine + golden owner DXF tests |
| U3 | Semantic map (layers preferred / color interim) |
| U4 | Generator **or** import→instance metrics persistence (read path first) |
| U5 | CPP/dry-run consume metrics; Slice C proxy gated |
| U6 | UI honesty + runtime proof + worklog |

---

## 29. Files likely touched (viitor — nu acum)

- `backend/services/acm_production_geometry_metrics.py` (**new**)
- `backend/services/acm_dxf_path_measurement.py` (**new**)
- `backend/services/acm_commercial_geometry.py` (fallback gating only)
- `backend/data/commercial_rules_volumetric_v2.py` (quantity_paths alias only — **no rate change**)
- `backend/services/intake_v6_priced_quote_dry_run_service.py` (preview source fields)
- `frontend/src/lib/intakeV6/acmPanel/types.ts` (+ metrics types)
- `frontend/src/components/workos/intake-v6/AcmPanelProvisionalPricingBlock.tsx` (source labels)
- `backend/tests/test_acm_production_geometry_metrics_*.py` (**new**)
- `docs/worklog/realignment/…` + evidence DXF copies (dacă policy permite)

---

## 30. Commit strategy (viitor)

1. `feat(acm-panel): production geometry metrics contract + measurement`
2. `feat(acm-panel): wire CPP quantities to measured CUT/V`
3. `docs(acm-panel): metrics truth worklog + DXF evidence`

Max 3; fără migrations/seeds.

---

## 31. Boundaries

- Fără rate changes / new commercial hourly
- Fără Offer/Order/Execution/task_rules
- Fără revert Slice C în plan
- Fără Inventory writes
- Fără Figma/21st
- Fără a pretinde că panel perimeter = production CUT universal

---

## 32. Owner gates — STOP

Cere GO explicit pentru:

1. **Geometry metrics contract** (nume + câmpuri din §10)
2. **Single-fold truth** (valori §6 + semantics §11)
3. **Double-fold truth** (valori §6 + semantics §12)
4. **Exact DXF measured values** acceptate ca golden
5. **Fallback policy** (§17) — proxy single-fold explicit vs unavailable
6. **Pricing consumer boundary** — o linie `acm_v_groove` = V total (L1+L2) vs split rates (nu propunem rate noi fără GO)
7. **Slice C remediation scope** — ce rămâne proxy vs ce se înlocuiește
8. **Impact preview existent** pe `IV6-DB2F86B7` (rămâne 5.4 proxy marcat **sau** cut/V unavailable)

**Nu implementa** până la GO.

---

## 33. Opinia sinceră

Slice C a fost pasul corect pentru assembly vs envelope. Acum owner DXF arată că **V-groove și CUT sunt familii diferite de trasee**, iar double-fold rupe orice egalitate. Cel mai mare pericol este să „reparăm” din nou din perimetre. Verdictul B e onest: avem semnale (L1/L2 pe instanță, Blueprint, path metrics generice) dar **nu** un motor de producție. Color-only DXF e utilizabil ca golden test, nu ca SoT pe termen lung fără layers.

---

## 34. Roadmap awareness checkpoint

```text
A+B assembly/SKU     ✅
Slice C preview      ✅ (proxy rectangular)
→ Metrics contract   ← YOU ARE HERE (plan)
→ Generator/measure  (next)
→ CPP consume truth
→ Authority → official_ready
→ Offer/Execution    (later, separate)
```

---

## 35. Cât suntem în direcția stabilită: **72/100**

Direcția e clară (geometry owns paths; pricing consumes). Gap-ul generatorului și lipsa layer semantics în DXF owner scad scorul până la GO + U1–U4.

---

## Appendix — interpretive geometry from DXF (for implementers)

**Single-fold blank:** `face + 2·L1` pe ambele axe → 2200×500.  
**Double-fold blank:** `face + 2·(L1+L2)` → 2260×560.  
**V L1 (color 1):** dreptunghi de pliu L1 — pe double-fold: 2200×500 → perimeter 5400.  
**V L2 (color 242):** dreptunghi față 2000×300 → perimeter 4600.  
**CUT:** closed outer blank path; pe double-fold scurtat de corner relief față de 5640 teoretic.

STOP — așteaptă owner GO pe gate-urile din §32.

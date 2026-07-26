# WORKOS_ACM_PANEL_PRICING_PREVIEW_AND_AUTHORITY_GATES_V1

| Field | Value |
|-------|--------|
| Status | **IMPLEMENTED — feature `ab514f3`** |
| Mode | Implementation complete — owner review |
| Date | 2026-07-20 |
| Branch baseline | `feature/product-system-active-path-isolation-v1` @ `e9a502f` (docs after A+B `f2adf6b`) |
| Feature commit | `ab514f32d54af219787bfb4d049242cecfa0c8b1` |
| Prerequisite | A+B PASS — assembly keys + ACM-root PD parity + SKU naming |
| Canonical fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Combines | Slice C — Pricing Preview + authority gates |

---

## 1. Rezumat

Fixture-ul multi-panel are acum `assembly_width_mm=2000` / `assembly_height_mm=350` în PD, dar **derivația comercială activă** (`derive_acm_casetted_quote_input`) citește încă `panel_width_mm` / `panel_height_mm`. Pe workspace-ul Letters-hosted, `panel_width_mm` rămâne **envelope 1000** → CPP poate factura **0.350 mp** în loc de **0.700 mp**.

Rates ACM există și sunt curate (EUR/mp · EUR/ml · EUR/set, fără orar). Authority pe fixture: technical proposed, segmented PROPOSED, construction catalog_default, composition inconsistent → **estimare OK, pret final / Offer / Execution NO**.

Slice C trebuie să:

1. introducă un **commercial geometry contract** distinct (assembly area ≠ cut length ≠ fold length);
2. lege cantitățile CPP de acest contract (nu doar „înlocuiește panel cu assembly peste tot”);
3. marcheze output-ul ca **provisional** în UI-ul live-calc existent (Review);
4. blocheze Offer ferm / pret final / Execution pe starea fixture.

---

## 2. Verdict

### A. Pricing Preview poate fi implementat într-un build izolat

**Verdict ales: A** — cu contract geometric comercial explicit ca prim unit de implementare (nu un build separat B).

**De ce nu B:** A+B a livrat deja cheile `assembly_*`, PD parity și naming. Gap-ul rămas este **wiring + semantics + gates**, nu un contract pregătitor orphan.

**De ce nu C:** Registry/rates nu blochează — cele 6 linii `acm_*` și rates owner există. Lipsesc doar rate pentru **joints / segmentation handling** (gap onest în preview, nu inventare).

---

## 3. Scope

### In scope

1. Commercial geometry adapter: multi-panel overall din `assembly_*`; cut/fold din **sumă per-panel**; interzicere envelope ca overall.
2. Wire adapter în `merge_acm_boxed_mounting_derived_fields` / quote_input înainte de CPP (fără schimbare valori rate).
3. CPP/EIC quantity paths consumă cheile derivate corecte (sau alias stabil).
4. Authority summary + provisional status pe dry-run / live calc.
5. UI honesty în `IntakeV6LiveCalculationSummary` (Review) — warnings compacte.
6. Tests geometry + pricing + runtime zero-write.
7. Docs worklog/QA pentru Slice C.

### Out of scope

- Schimbare valori rate / Pricing Registry rewrite
- Offer/Order writes, Snapshot materialization nouă
- Execution / task_rules / MIXED DAG
- Blueprint L1-P changes
- Inventory writes / migrations
- Rate noi pentru joints / frame / foil
- Hourly commercial lines
- Employee Mobile
- `/inventory/pricing` ca UI operator preview

---

## 4. Capability inventory

| Cap | Status | Note |
|-----|--------|------|
| Repo/code search | **USED** | CPP rules, derive, dry-run, FE Review |
| Browser / runtime read-only | **USED** | FE `:3000` + BE `:8003` healthy |
| API GET | **ALLOWED** (plan) | dry-run / PD / registry — fără write |
| SQL read-only | **ALLOWED** | nu obligatoriu |
| Tests inventory | **USED** | ACM CPP / standalone / assembly extent |
| Git history | **USED** | `f2adf6b`, `e9a502f` |
| Screenshots existente | **USED** | A+B + downstream audit evidence |
| Subagents | **USED** | pricing path · rates · UI placement |
| Figma | **NOT USED — NOT NEEDED** | live-calc UI există |
| 21st.dev | **NOT USED — NOT NEEDED** | |

---

## 5. Runtime routes

| URL | Rol | Slice C |
|-----|-----|---------|
| `http://127.0.0.1:3000/intake-v6/a7b0162b-dc91-467f-aa24-c1279fb3a073/operator` | Intake AcmPanel + Review live calc | **Primary operator surface** |
| `http://127.0.0.1:3000/inventory` | Stock / materials admin | Read-only proof material source |
| `http://127.0.0.1:3000/inventory/pricing` | **Pricing Registry / configuration** | Rate SoT admin — **nu** product preview |
| `GET /api/v1/intake-v6/workspaces/{id}/priced-quote-dry-run` | V6 commercial dry-run | Preview payload |
| `POST /api/v1/product-system/commercial-price-preview/{template}` | CPP 7G | Standalone / linked ACM lines |
| `POST .../estimated-internal-cost-preview/{template}` | EIC 7H | Internal cost (separate) |

### Unde se afișează Pricing Preview (recomandare unică)

**`IntakeV6LiveCalculationSummary` pe Pasul Review** (`IntakeV6ReviewStep` — sticky rail „Rezultat comercial”), alimentat de `priced-quote-dry-run`.

Nu în:

- `/inventory/pricing` (registry);
- AcmPanel inspector (rămâne geometrie/construction);
- Quotes post-offer.

Confirm step poate reutiliza același component pentru consistență, dar **owner surface = Review**.

---

## 6. Pricing input trace

```text
acm_panel_instance (+ segmented panels / assembly_dimensions)
  → ProductDefinition.canonical_values
       (assembly_* inject; panel_* may still be envelope)
  → V6 quote_input_payload (+ mounting_solution.configuration)
  → merge_acm_boxed_mounting_derived_fields
       → derive_acm_casetted_quote_input(panel_*)   ★ BUG multi-panel
       → inject_assembly_extent_keys                (observability only today)
  → CommercialPriceProposalService.build_preview (7G)
       → ACM_STRUCTURA_COMMERCIAL_RULES quantity_paths
  → EstimatedInternalCostService.build_preview (7H)
  → IntakeV6 priced-quote-dry-run
  → FE IntakeV6LiveCalculationSummary
```

**CostEngine formula_handlers:** pe path Aggregate/ops time — **nu** pe dry-run money path V6.

| Transform | File | Function | Input keys | Output keys | Authority | Fallback | Tests |
|-----------|------|----------|------------|-------------|-----------|----------|-------|
| Assembly extent | `acm_assembly_extent.py` | `compute_acm_assembly_extent` / `inject_*` | panels, assembly_dimensions, envelope | `assembly_width_mm`, `assembly_height_mm`, source | proposed geometry | panel extent | `test_acm_assembly_extent.py` |
| PD project | `acm_panel_pd_projection.py` + `product_definition_builder_service.py` | `project_acm_finish_into_canonical` / `_build_canonical_values` | finish + instance | canonical + assembly_* | PD read-only | coalesce nested | PD proposal / cross-template |
| Derive commercial | `acm_quote_input_helpers.py` | `derive_acm_casetted_quote_input` | **panel_width/height** | `panel_area_m2`, `panel_perimeter_m`, `fold_length_m`, `return_strip_area_m2` | none (pure math) | blockers if missing | `acmQuoteInput.test.ts`, standalone offer |
| Merge | same | `merge_acm_boxed_mounting_derived_fields` | payload / mounting / finish | derived + assembly_* | — | client width/height | standalone offer |
| CPP | `commercial_price_proposal_service.py` | `build_preview` / `_build_line` | quantity_paths | `CommercialPriceProposalPreview` | documented EUR | skip if qty missing | owner-rates CPP tests |
| EIC | `estimated_internal_cost_service.py` | `build_preview` | panel_area / return_strip | materials + capacity minutes | internal | — | EIC capacity tests |
| Dry-run | `intake_v6_priced_quote_dry_run_service.py` | `build_intake_v6_priced_quote_dry_run` | workspace quote_input | commercial_totals + traces | V6 official when ready | blocked authority | quote commercial spine tests |
| FE | `IntakeV6LiveCalculationSummary.tsx` | render | dry-run props | UI totals | display | — | Review / spine tests |

### Locuri care încă folosesc `panel_*` pentru bani

- `derive_acm_casetted_quote_input` — **singura sursă** a `panel_area_m2` / perimeter / fold
- `ACM_STRUCTURA_COMMERCIAL_RULES` — `panel_area_m2`, `panel_perimeter_m`, `fold_length_m`, `return_strip_area_m2`
- EIC material qty — `panel_area_m2` / `return_strip_area_m2`
- FE `acmQuoteInput.ts` mirror
- Seed CostEngine ops pe template (nu dry-run money)

### Locuri cu `assembly_*` azi

- PD canonical / geometry_inputs
- merge inject (non-commercial)
- Blueprint L1-P
- **Niciun** `quantity_paths` CPP

---

## 7. Commercial geometry

### Contract propus (chei derivate — nu suprascriu panel dims)

| Key | Multi-panel | Single-panel | Interzis |
|-----|-------------|--------------|----------|
| `assembly_width_mm` / `assembly_height_mm` | obligatoriu din A+B | assembly dacă există, altfel panel | envelope ca overall |
| `commercial_face_area_m2` | `(assembly_w × assembly_h) / 1e6` | idem sau panel area | SVG bbox units |
| `commercial_cut_length_m` | **suma** perimetrelor panourilor (fiecare panou debitat) | perimeter panou | doar exterior assembly când există ≥2 panouri |
| `commercial_fold_length_m` | **suma** fold length per panou (fold_sides pe fiecare) | fold pe panou | assembly 2×(W+H) automat pentru toate ops |
| `commercial_return_strip_area_m2` | `commercial_fold_length_m × (return_depth/1000)` | idem | — |
| `panel_count` | len(panels) | 1 | — |
| `joint_count` | len(joints) | 0 | **fără rate** → gap warning |

`panel_width_mm` / `panel_height_mm` rămân:

- envelope / primary contour / mounting config storage;
- **nu** se suprascriu cu assembly 2000;
- **nu** mai sunt sursa unică a cantităților comerciale multi-panel.

### Alias de tranziție (implementare)

CPP paths actuale pot primi alias:

- `panel_area_m2` ← `commercial_face_area_m2` (după adapter)
- `panel_perimeter_m` ← `commercial_cut_length_m`
- `fold_length_m` ← `commercial_fold_length_m`

sau rules actualizate să citească cheile `commercial_*` explicit (preferat pe termen lung; alias acceptabil în Slice C dacă tests acoperă).

---

## 8. Assembly versus envelope

| Concept | Fixture | Comercial |
|---------|---------|-----------|
| Assembly overall | 2000×350 | **Da** — face area + assembly labor area |
| Envelope contour | 1000×350 | **Nu** ca overall; warning `envelope_ignored` |
| Per-panel | 2× (1000×350) | Cut / fold / return strip |
| Silent fallback 1000 când există 2000 | — | **Interzis** |

Half-price bug actual:

```text
envelope path: 1.000 × 0.350 = 0.350 mp
assembly path: 2.000 × 0.350 = 0.700 mp
```

---

## 9. Existing rates

Exact **6** linii comerciale `acm_*` (nu 5) — din `ACM_STRUCTURA_COMMERCIAL_RULES` + seeds + tests `len(acm_lines)==6`.

| # | code | label | unit | value | owner | source | consumer | status |
|---|------|-------|------|-------|-------|--------|----------|--------|
| 1 | `acm_panel_cut` | Debitare panou ACM | ml | **1.5 EUR** | owner-confirmed | `commercial_rules_volumetric_v2.py` + WC `ACM_PANEL_CUTTING` | CPP ← cut length | active |
| 2 | `acm_v_groove` | Frezare V-groove ACM | ml | **3.0 EUR** | owner-confirmed | same + WC `ACM_V_GROOVE` | CPP ← fold length | active |
| 3 | `acm_panel_face_material` | Material ACM față panou | m2 | **15.0 EUR** | owner-confirmed | same + `MAT-ACM-BOND-3MM` | CPP ← face area | active |
| 4 | `acm_return_strip_material` | Material ACM canturi | m2 | **15.0 EUR** | owner-confirmed | same SKU | CPP ← return strip area | active |
| 5 | `acm_boxed_assembly` | Asamblare suport ACM casetat | m2 | **15.0 EUR**, **min 20 EUR** | owner-confirmed | same + WC `ACM_BOXED_ASSEMBLY` | CPP special min | active |
| 6 | `acm_fasteners` | Suruburi / prinderi | set | **5.0 EUR** | owner-confirmed | `MAT-SURUBURI-GEN` | CPP qty 1 set | active |

Registry UI „5 confirmate” = materiale+workcenters agregate; **linii CPP = 6**.

**Niciun rate orar comercial** (`rate_per_hour=None` pe WC).

---

## 10. Formula ownership

| Formula / line | Owner | Inputs | Uses assembly? | Uses panel data? | Authority gate |
|----------------|-------|--------|----------------|------------------|----------------|
| Face material | Pricing Registry rate + AcmPanel geom | face area | **Yes (area)** | panels for validation | provisional until technical+seg confirmed |
| Return strip material | same | fold length × depth | No (per-panel fold sum) | **Yes** | catalog depth warning |
| Cut | same | cut length | No | **Yes (sum panels)** | provisional |
| V-groove | same | fold length | No | **Yes (sum panels)** | catalog fold warning |
| Assembly labor | same | face area + min 20 | **Yes (area)** | panel_count informational | provisional |
| Fasteners | same | set=1 | No | No | provisional |
| Joints / rost | — | joint_count | — | Yes | **gap — no rate** |
| Operation order | MIXED / OWNER_RULES / seed adapter | — | — | — | Pricing **nu** deține DAG |

---

## 11. Area

### Face area (fixture)

```text
assembly: 2.000 m × 0.350 m = 0.700 mp
```

**Nu** `0.350 mp` (envelope).

Pentru panouri alăturate fără overlap, `Σ panel areas` = `assembly area` pe acest fixture — preferă **assembly** ca SoT overall; validează vs sumă (±1 mm / ±1e-3 mp).

### Assembly labor area

Aceeași `0.700 mp` × 15 EUR = 10.50 → **min 20 EUR** aplicat.

---

## 12. Perimeter

**Nu** folosi automat `2×(assembly_w+assembly_h)` pentru toate operațiile.

| Factor | Formula geometrică | Sursa | Consumer |
|--------|-------------------|-------|----------|
| Assembly exterior perimeter | `2×(Aw+Ah)/1000` | assembly_* | informational / future packing only |
| Cut length | `Σ 2×(pw_i+ph_i)/1000` | panels[] | `acm_panel_cut` |
| Fixture cut | `2×2.7 = 5.4 ml` | 2 panels 1000×350 | cut line |
| Dacă greșit assembly exterior | `2×(2.0+0.35)=4.7 ml` | assembly | **under-cut** — interzis ca cut qty |

---

## 13. Cutting

- Qty = `commercial_cut_length_m` (sumă perimetre panouri).
- Rate = 1.5 EUR/ml (neschimbat).
- Fixture estimate: `5.4 × 1.5 = 8.10 EUR` (provizoriu).
- Gap: nested holes / internal cutouts — out of scope dacă nu există în instance.

---

## 14. V-groove

- Qty = `commercial_fold_length_m` din fold_sides pe **fiecare** panou (default catalog `all` → același 5.4 ml pe fixture).
- Rate = 3.0 EUR/ml.
- Fixture: `5.4 × 3.0 = 16.20 EUR` (provizoriu).
- **Nu** confunda V-groove cu joint length între panouri (fără rate).

---

## 15. Assembly

- Qty area = `commercial_face_area_m2` = 0.700.
- Rate 15 EUR/mp, **min 20 EUR/product** (există în CPP).
- Fixture: max(0.700×15, 20) = **20 EUR**.
- panel_count / joint_count pot apărea ca metadata, nu ca linii noi.

---

## 16. Segmentation

| Factor | Rate există? | Preview behavior |
|--------|--------------|------------------|
| panel_count | Nu linie separată | Informational + complexity note |
| joints / joining | **Nu** | Warning gap: „rosturi neevaluate comercial” |
| extra handling | Nu | Gap |
| per-panel cutting | Da (via cut sum) | Inclus în cut |
| sheet nesting / waste | Nu în CPP | Gap / inventory unknown — nu inventa |

**Nu inventa rate noi.** Gap-urile apar în `warnings[]` / `blockers[]` (blockers doar pentru final/Offer, nu pentru preview).

---

## 17. Construction

| Input | Authority fixture | Rate | Pricing impact | Preview | Final |
|-------|-------------------|------|----------------|---------|-------|
| thickness 3 mm | catalog_default | MAT-ACM-BOND-3MM 15 EUR/mp | face + return | OK provisional + warning | după operator confirm |
| fold_count 2 | catalog_default | via fold length | V-groove / return | provisional | confirm |
| l1 60 / l2 25 | catalog_default | indirect (depth) | return strip | provisional | confirm |
| internal frame | inactive | none | omit | omit | — |
| rear closure | inactive | none | omit | omit | — |
| mounting / PROFILE-SHS | fixing-only | **nu** în ACM CPP | omit | omit | — |
| finishes shell | absent | none | omit | omit | — |

---

## 18. Material binding

| Rule | Decision |
|------|----------|
| Canonical SKU | `MAT-ACM-BOND-3MM` |
| Legacy `MAT-ACP-3MM` | Nu produce a doua linie echivalentă pe ACM boxed |
| Resolver | `MAT-ACM-BOND-PANEL` → thickness 3 → `MAT-ACM-BOND-3MM` |
| Stock null | „necunoscut”, nu zero cost comercial |
| Commercial rate | documented 15 EUR/mp (CPP) |
| Purchase / inventory cost | același ordin de mărime pe seed; **nu** confunda cu authority comercială |
| Waste / sheet size | out of Slice C money lines — gap note ok |

---

## 19. Inventory cost versus commercial rate

| Layer | Meaning | Slice C |
|-------|---------|---------|
| Purchase / inventory unit_cost | Achiziție stoc | Display / EIC material path |
| Internal cost (EIC) | Cost intern + capacity minutes | Separat de Offer |
| Commercial rate (CPP) | Tarif ofertă EUR/mp·ml·set | Preview money |
| Margin / markup | Owner commercial policy | Nu reinventat aici |
| VAT | Downstream quote | Live calc poate arăta estimate-with-VAT existent; nu schimba politica |

---

## 20. Authority gates

| State | Pricing preview | Pret final | Offer ferm | Order | Execution |
|-------|-----------------|------------|------------|-------|-----------|
| detected geom | provisional OK | NO | NO | NO | NO |
| proposed association | provisional OK | NO | NO | NO | NO |
| catalog_default construction | provisional + warning | NO | NO | NO | NO |
| operator_confirmed technical | provisional→stronger | still gated | still gated | NO* | NO |
| technical proposed (fixture) | **provisional OK** | **NO** | **NO** | NO | NO |
| technical confirmed | estimate allowed | needs seg+composition | needs full gate | later | NO until exec gate |
| segmented PROPOSED (fixture) | provisional + warning | NO | NO | NO | NO |
| segmented CONFIRMED | estimate OK | possible if other gates | possible | later | still gated |
| composition inconsistent (fixture) | provisional + warning | NO | NO | NO | NO |
| composition confirmed | clearer estimate | possible | possible | later | NO until ops ready |
| blocked (missing dims) | NO / empty + blocker | NO | NO | NO | NO |

\* Order snapshot mechanism exists; **content** pe fixture rămâne neeligibil pentru fermitate.

### Default pe `IV6-DB2F86B7`

- Pricing Preview: **permis ca estimare provizorie**
- Pret final: **interzis**
- Offer ferm: **interzis**
- Order: **interzis** ca ferm
- Execution: **interzis**

Preview trebuie să explice: catalog defaults, segmentation neconfirmată, composition inconsistent, assembly-based estimate.

---

## 21. Preview output contract

**Nu inventa un tip nou dacă dry-run/CPP acoperă.** Extinde / marchează:

### Preferat (reutilizează)

- `CommercialPriceProposalPreview` + lines
- envelope V6 dry-run: `commercial_totals`, `commercial_line_items`, `commercial_proposal_trace`
- plus câmpuri honesty (sau warnings structurate):

```text
commercial_preview_status: "provisional" | "blocked" | "final_eligible" (final_eligible out of fixture)
authority_summary: { technical, segmented, composition, construction_defaults }
geometry_reference: { assembly_width_mm, assembly_height_mm, face_area_m2, cut_length_m, fold_length_m, panel_count, envelope_ignored }
material_reference: { preferred_sku: MAT-ACM-BOND-3MM, legacy_excluded: [MAT-ACP-3MM] }
rate_version: documented rules hash / seed stamp
warnings[] / blockers[]
```

Fiecare line (deja aproape în CPP):

- factor/code, quantity, unit, rate, amount, source, **provisional|final** flag

Nume conceptual `AcmPanelPricingPreview` = **view/projection** peste CPP+authority, nu neapărat schema DB nouă.

---

## 22. UI placement

### Recomandare unică

**Sticky live-calc pe Pasul Review** — `IntakeV6LiveCalculationSummary` („Rezultat comercial”).

### Prioritate UI

1. Formular / AcmPanel inspector rămân primare.
2. Pretul estimativ: compact, expandabil, nu domină.
3. Warnings scurte: catalog · segmentation · composition · Offer indisponibil.

### Figma / 21st.dev

- Figma: **NOT USED — NOT NEEDED**
- 21st.dev: **NOT USED — NOT NEEDED**

---

## 23. Commercial pricing philosophy

| Rule | Slice C |
|------|---------|
| No hourly commercial lines | Enforce / assert |
| Time = internal (EIC capacity minutes) | Keep separate |
| Commercial units | mp / ml / set only for ACM |
| Operator UI | no „ore × tarif/orar” |
| Internal vs commercial | EIC ≠ CPP |
| Margin | existing owner policy path — nu redesign |
| VAT | downstream / existing live-calc display |

---

## 24. Offer / Order gates (plan only)

Ulterior (nu acum), eligibilitate CommercialPriceProposal → Offer cere:

1. technical_configuration confirmed  
2. segmented CONFIRMED (dacă multi-panel)  
3. composition confirmed / consistent  
4. construction fields operator_confirmed (critical set)  
5. snapshot: rate_version + material_version + geometry_version + authority state  
6. warnings acceptate explicit de operator  

Slice C **nu** implementează Offer.

---

## 25. Execution boundary

- Execution rămâne blocked pe L1-P / PROPOSED / inconsistent.
- Pricing Preview **nu** deblochează task materialization.
- Operation SoT: MIXED + OWNER_RULES + seed partial — **neschimbat**.

---

## 26. Regression impact

| Case | Expect |
|------|--------|
| Single-panel ACM | assembly==panel area; cut/fold pe un panou — fără regresie numerica vs azi |
| Letters without ACM | fără linii acm_* |
| Logo-only | neschimbat |
| Legacy MAT-ACP-3MM | fără dublare pe ACM boxed |
| Non-ACM templates | neschimbat |
| Existing offers | no rewrite |
| CostEngine handlers | nu pe dry-run money; nu activa formule noi |
| Blueprint L1-P | untouched |
| ProductDefinition / Aggregate | assembly_* rămân; commercial adapter separat |
| Execution gates | remain blocked |

---

## 27. Tests

### Geometry

- multi-panel 2000×350 → face **0.700** mp  
- envelope 1000 ignored for overall  
- single panel parity  
- horizontal stacking / offset panels  
- missing assembly keys fallback (documented)  
- mismatch warning assembly_dimensions vs extent  

### Pricing

- rate resolution 6 lines  
- no duplicate legacy material  
- no hourly commercial line  
- provisional status pe fixture  
- authority warnings (catalog, seg, composition)  
- segmentation gap (joints)  
- final price unavailable  
- Offer unavailable  
- Execution blocked  
- cut qty = 5.4 ml (sum), not 4.7 (assembly exterior)  

### Runtime

- `/inventory` material source  
- `/inventory/pricing` registry rates (admin)  
- Intake fixture Review preview  
- dry-run API payload  
- **0 PUT** în timpul inspecției read-only  

---

## 28. Runtime proof (plan)

1. PD Letters + ACM-root: assembly 2000×350 (deja A+B).  
2. Dry-run înainte: documentează half-price dacă panel_*=1000.  
3. Dry-run după implementare: face 0.700; cut/fold pe sumă panouri; status provisional.  
4. Zero writes pe expand/collapse preview.  

---

## 29. Screenshots (matrix viitor)

1. Inventory material source (`MAT-ACM-BOND-3MM`)  
2. Pricing registry ACM rates  
3. AcmPanel inspector (fără bani)  
4. Preview collapsed (Review)  
5. Preview expanded  
6. Calculation lines (6 acm_*)  
7. Input 2000×350  
8. Material qty **0.700 mp**  
9. Provisional warnings  
10. Segmentation warning  
11. Composition warning  
12. Final price unavailable  
13. Offer unavailable  
14. Full-page hierarchy  

---

## 30. Risk matrix

| Risk | Mitigare |
|------|----------|
| Area half-priced from envelope | Adapter forțează assembly face area |
| Perimeter formula misuse | Cut = sum panels, not assembly exterior |
| V-groove length misuse | Fold = sum panels |
| Segmentation cost omitted | Explicit gap warning |
| Material duplicate ACP+BOND | Prefer BOND; assert single face line |
| Inventory cost as commercial | CPP documented rates |
| Catalog defaults as final | provisional + warnings |
| Hourly commercial | assert empty |
| Preview = Offer | UI copy + gates |
| Stale rate version | stamp in preview |
| Registry page as technical owner | UI placement Review only |
| Execution unlocked by estimate | hard boundary |
| Single-panel regression | parity tests |

---

## 31. Implementation units (post-GO)

| Unit | Deliverable |
|------|-------------|
| U1 | `commercial_geometry` adapter (FE mirror optional) — face/cut/fold/return keys |
| U2 | Wire into `merge_acm_boxed_mounting_derived_fields` + Letters quote_input path |
| U3 | CPP/EIC consume new quantities (alias or path update) — **no rate value changes** |
| U4 | Authority summary + provisional/final flags pe dry-run |
| U5 | FE Review live-calc honesty (warnings, Offer unavailable) |
| U6 | Tests + runtime proof + screenshots + worklog |
| U7 | Isolated commit; STOP owner |

---

## 32. Files likely touched

| File | Why |
|------|-----|
| `backend/services/acm_quote_input_helpers.py` | commercial geometry wire |
| new `backend/services/acm_commercial_geometry.py` (likely) | adapter |
| `backend/data/commercial_rules_volumetric_v2.py` | quantity_paths only if needed |
| `backend/services/commercial_price_proposal_service.py` | provisional flags / min assembly unchanged |
| `backend/services/intake_v6_priced_quote_dry_run_service.py` | authority_summary |
| `backend/services/estimated_internal_cost_service.py` | qty parity |
| `frontend/src/lib/acmQuoteInput.ts` | mirror if used |
| `frontend/.../IntakeV6LiveCalculationSummary.tsx` | honesty UI |
| tests: new + update ACM CPP / dry-run | |
| docs worklog/audit Slice C | |

**Nu:** Blueprint, task_rules, Inventory seeds prices, Offer routers.

---

## 33. Commit strategy

1. Un commit feature coerent Slice C (path + gates + UI honesty + tests).  
2. Un commit docs (worklog + audit + hash) — pattern A+B.  
3. Fără amend pe A+B.  
4. STOP pentru owner review înainte de Offer/Exec.

---

## 34. Boundaries

- fără rate value changes  
- fără formula activation CostEngine pe dry-run  
- fără Offer/Order/Execution  
- fără task rules / MIXED rewrite  
- fără Blueprint changes  
- fără Inventory writes / migrations  
- fără Employee Mobile  
- fără a pune preview în `/inventory/pricing`  

---

## 35. Owner gates (înainte de implementare)

1. Acceptă verdict **A** + commercial geometry: face/assembly area din `assembly_*`; cut/fold din **sumă panouri**.  
2. Acceptă că „5 rates registry” = 6 linii CPP (face+return material separate).  
3. Acceptă UI placement: **Review live-calc**, nu inspector, nu registry.  
4. Acceptă pe fixture: preview provisional; final/Offer/Exec blocate.  
5. Acceptă gap joints fără rate nou.  
6. Confirmă că nu se schimbă valorile 1.5 / 3 / 15 / 20 / 5 EUR.  

---

## 36. Opinia sinceră

Slice C este **buildul potrivit acum**. Rates și shell-ul UI există; A+B a eliminat orbirea PD. Riscul real nu e „lipsă tarif”, ci **semantica greșită a lungimilor** dacă cineva mapează naiv `panel_* ← assembly_*` pentru cut/V-groove. Planul forțează matricea face≠cut≠fold. Fără gates oneste, preview-ul va fi citit ca Offer — de aceea UI honesty e obligatorie în același build, nu „mai târziu”.

---

## 37. Cât suntem în direcția stabilită: **74/100**

| Factor | Scor |
|--------|------|
| Geometry truth (A+B) | +18 |
| Rates / no hourly | +16 |
| Money path exists (CPP/dry-run/UI) | +14 |
| Authority honesty still missing | −8 |
| Multi-panel commercial wire missing | −10 |
| Segmentation commercial gaps | −4 |
| Offer/Exec correctly still blocked | +8 |

După Slice C bine executat: țintă ~88/100 (rămân Offer gates + joint rates ca datorie).

---

## STOP

Plan complet. **Nu începe implementarea** până la owner GO pe §35.

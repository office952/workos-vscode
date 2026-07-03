# Pricing / CostEngine Logic Audit — Currency, Rate Basis, QC, Templates

**Date:** 2026-06-05  
**Scope:** Analysis only — no runtime changes in this task.  
**Git baseline:** `685a52e` — clean working tree after Pricing Registry UI polish commit.

---

## Executive summary

| Area | Current state | Target (user intent) | Verdict |
|------|---------------|----------------------|---------|
| Base currency | `moneda_implicita` on Settings → **CostEngine** tab; not wired into simulate/orchestrator defaults | Settings owns one base currency for all costing | **GAP** — mixed EUR/RON rows summed without FX |
| QC | `QC_INSPECTION` workcenter + priced ops in 7 BUILD4 templates | Internal-only, not default quote line | **GAP** — blocks + inflates totals when rate set |
| Rate basis | Only `per_hour` + `per_linear_meter` | Rich unit-based model (mp, ml, buc, set, op, setup, …) | **GAP** — most ops proxy time → hourly |
| Templates | Materials mostly unit-correct; services mostly time→hourly | Unit-first pricing per operation type | **PARTIAL** — volumetric forming/bonding is correct |

**Audit result:** Analysis **PASS** (complete). Pricing logic model vs. business intent: **FAIL** until Phases 1–4 below are approved and implemented.

---

## Phase 0 — Pre-flight

- **Working tree:** clean at audit time (`685a52e`).
- **Unrelated UI polish:** already committed separately; this audit does not mix with it.

---

## Phase 1 — Currency audit

### 1.1 Is there already a base currency in `/settings`?

**Partially yes.**

- **Settings → CostEngine tab** exposes editable `moneda_implicita` (default `RON`), loaded from `GET /api/v1/cost-engine/base-config` and `cost_engine_config` table.
- **Settings → Societate (company) tab** uses mock `companySettings` — **no currency field**.
- User expectation (“base currency from Settings page”) maps to **CostEngine config**, not company profile — but it is **not propagated** to Pricing Registry defaults or simulate/quote flows.

### 1.2 Where is currency stored today?

| Layer | Field | Default / notes |
|-------|--------|-----------------|
| `cost_engine_config` | `moneda_implicita` | `RON` |
| `CostEngineBaseConfigDTO` | `currency` | mirrors `moneda_implicita` |
| `PricingContext` | `currency` | hard default `"RON"` in `product_contracts.py` |
| `inventory_materials` | `currency` per row | required for `active` |
| `workcenter_rates` | `currency` per row | seeded `RON`; volumetric labor `EUR` |
| `commercial_markup_policies` | `currency` | per policy |
| Recurring payments (Settings) | `currency` per payment | overhead input, not product FX |

**No FX conversion layer exists.** `load_material_cost_dict()` returns `{code: unit_cost}` — currency is validated for inclusion but **not passed to CostEngine**. `load_workcenter_rate_dict()` likewise omits currency.

### 1.3 Rows that carry currency manually

**Materials (owner-confirmed / estimated seeds):**

- Volumetric: mostly **EUR** (face, back, LED module, sablon, profile ml, paint estimate, consumables).
- Volumetric PSU variants: **RON** (60/80/100/200 W).
- ACM: **EUR** (3 mm owner-confirmed; 4 mm needs_review).

**Workcenters:**

- Canonical stubs: **RON**, `missing_price`.
- Owner volumetric labor: `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING` → **EUR/ml**.

### 1.4 Does CostEngine assume a currency?

Yes. Output `CostResult.currency = ctx.currency or "RON"`. All line totals are **added arithmetically** with no per-line currency metadata in the v2 bridge.

Doc comment in `CostEngineWithMaterialRates`: *“Rates MUST be in the same currency as PricingContext.currency (base: RON).”* — **not enforced** at load time.

### 1.5 Does Pricing UI allow editing currency per row?

- **Materials:** yes — `MaterialEditDrawer` editable `currency` (defaults `EUR` in form init).
- **Workcenter rates:** displayed read-only in rate drawer; basis editable (`per_hour` / `per_linear_meter` only).

### 1.6 Per-row currency editing — keep or advanced-only?

**Recommendation:** Per-row currency becomes **advanced override only** (supplier invoice currency, import). Default display and new rows inherit `moneda_implicita`. CostEngine must either:

1. Normalize all active registry rows to base currency at calculation time (preferred), or  
2. Block `is_valid` when row currency ≠ base currency (strict, surfaces blockers).

### 1.7 Safest target model

```
Settings.moneda_implicita (CostEngine config)
    ↓ default for new/edited pricing rows
inventory_materials.currency  ──override──► optional, advanced
workcenter_rates.currency     ──override──► optional, advanced
    ↓ normalize at CostEngine boundary (single currency totals)
CostResult.currency = moneda_implicita
```

**Risks if unchanged:** Product 001 preliminary quote can label totals `RON` while summing EUR material lines + RON PSU + EUR/ml services — **materially wrong totals** when blockers clear.

### Implementation plan (currency — not implemented)

1. Wire `QuoteOrchestrator` / simulate to load `moneda_implicita` into `PricingContext`.
2. Pricing Registry UI: hide currency by default; show “Monedă: {base}” + advanced override.
3. Registry write path: default `currency` from config when blank.
4. CostEngine v2: validate or convert row currency vs context (even a hard blocker is safer than silent mix).
5. Owner decision: normalize volumetric registry to **one** currency (likely EUR or RON, not both).

---

## Phase 2 — QC / control calitate audit

### 2.1 Where QC appears

| Location | Reference |
|----------|-----------|
| Workcenter seed | `seed_build4_workcenters.py` → `QC_INSPECTION` |
| Templates (`seed_build4_templates.py`) | Banner, Plexi, Vinyl, Lightbox (×2), Volumetric, Mesh |
| Frontend mocks | `mockData.ts` — same ops |
| Tests | volumetric/productsystem tests expect QC in template JSON |
| Pricing Registry | Listed as operation rate `QC_INSPECTION` when template uses it |

**ACM templates (`seed_acm_template_pack.py`):** **no QC** operations.

### 2.2 Is QC used as a priced operation?

**Yes.** Static ops use `estimated_minutes` → CostEngine v2 applies `rate_basis=per_hour` when a rate exists.

Example volumetric:

```python
_op_static("qc_letters", "QC_INSPECTION", 9, 15, "Control calitate")
```

### 2.3 Templates including QC

1. TPL-BANNER-PVC  
2. TPL-PLEXIGLASS-PANEL  
3. TPL-VINYL-STICKER  
4. TPL-LIGHTBOX-LED (led_testing + qc_lightbox)  
5. **TPL-VOLUMETRIC-LETTERS** (`qc_letters`, 15 min)  
6. TPL-MESH-EXTERNALIZED (`incoming_qc`)

### 2.4 CostEngine behavior

- Contributes to `operation_cost` / `total_cost` when `QC_INSPECTION` has active `rate_per_hour`.
- Today mostly **blocked** (`WORKCENTER_RATE_MISSING`) because stub has no rate — but readiness/registry still **expects** a rate row.
- `estimated_time_minutes` includes QC minutes (calendar duration), separate from pricing unit confusion.

### 2.5 Blocking vs totals

- **Blocking:** yes — missing QC rate is a workcenter blocker in preliminary smoke.
- **Totals:** when rate is set, QC adds `rate_per_hour * (15/60)` per quote.

### 2.6–2.7 Target

- Remove QC from **default quote pricing templates** (or mark `pricing_scope: internal_only`).
- Keep QC as production checklist / execution task / readiness checklist — **not** chargeable registry line unless owner creates explicit paid inspection service later.

### Impact of removal (report only)

- Template JSON ops arrays — 7 templates, 8 QC op lines (lightbox has 2).
- Pricing Registry will stop listing `QC_INSPECTION` for those templates (unless used elsewhere).
- Tests referencing QC op codes need updating.
- No schema migration required if implemented as template + workcenter metadata flag.

---

## Phase 3 — Hourly-rate dependency audit

### 3.1 CostEngine rate_basis support today

`VALID_RATE_BASES = {"per_hour", "per_linear_meter"}` in `workcenter_rates_service.py`.

Operation resolution (`cost_engine_service.py`):

1. Resolve minutes (static or formula: `perimeter_based_time`, `count_based_time`, …).
2. If `per_linear_meter` → `rate_per_linear_meter * linear_meters` (from formula breakdown).
3. Else → `rate_per_hour * (minutes/60)`.

**Time formulas are always converted to hourly billing** unless workcenter uses `per_linear_meter`.

### 3.2 Worker counts

**Not modeled.** `count_based_time` uses `minutes_per_letter`, not team size. Three workers on one job do **not** triple cost — but hourly **duration assumptions** can be wrong if owner thinks “3 people × 1 hour” should mean 3 labor-hours.

### 3.3 TPL-VOLUMETRIC-LETTERS — operation inventory

| Operation | Workcenter | Current basis | Recommended |
|-----------|------------|---------------|-------------|
| vector_prep | PREPRESS | static 45 min → hourly | per_setup or per_template |
| face_cnc_cut | CNC_ROUTER | perimeter_based_time → hourly | **per_cut_meter** or per_operation + setup |
| side_forming | RETURN_PROFILE_MACHINE_FORMING | **per_linear_meter** ✓ | keep |
| return_face_bonding | RETURN_PROFILE_FACE_BONDING | **per_linear_meter** ✓ | keep |
| back_cut | LASER_CUTTING | perimeter_based_time → hourly | per_cut_meter |
| led_install | LED_ASSEMBLY | count_based_time → hourly | **per_letter** or per_led_module (material already per buc) |
| electrical_letters | ELECTRICAL_WIRING | static 30 min → hourly | per_set or per_letter |
| mounting_template_cnc | CNC_ROUTER | perimeter_based_time → hourly | per_cut_meter or per_template mp |
| painting | PAINTING | count_based_time → hourly | **per_set** or per_letter (material already per set) |
| assembly_letters | ASSEMBLY | static 60 min → hourly | per_set / per_letter |
| qc_letters | QC_INSPECTION | static 15 min → hourly | **internal_only** — remove from pricing |
| packaging_letters | PACKAGING | static 20 min → hourly | per_set or included_overhead |

**Materials (good):** mp (face, back, sablon), ml (profile), buc (LED, PSU), set (paint, consumables).

### 3.4 TPL-ACM-CASSETTED-PANEL

| Line | Current | Recommended |
|------|---------|-------------|
| ACM panel face | mp material | keep |
| CUT_ACM_PANEL | static 15 min → hourly | per_operation + per_mp |
| V_GROOVE_ROUTER | fold_length × min/m → hourly | **per_fold_meter** or per_linear_meter |
| FOLD_CASSETTE | static 45 min → hourly | per_fold_meter or per_operation |
| MOUNT_ACM_PANEL | static 30 min → hourly | per_mounting_point or per_set |
| MAT-SURUBURI-GEN | set material | keep |

### 3.5 TPL-CUT-ACM-LETTERS

| Line | Current | Recommended |
|------|---------|-------------|
| ACM sheet | mp from cut_area_m2 | keep |
| CNC_CUT_ACM_LETTERS | cut_perimeter time → hourly | **per_cut_meter** |
| EDGE_CLEANUP | static 20 min → hourly | per_cut_meter or per_operation |

### 3.6 Unreliable estimates today

Any op using **fixed minutes** (PREPRESS, ASSEMBLY, QC, PACKAGING) without owner hourly rates → blocked.  
Any op using **time formulas + hourly rate** conflates machine speed with shop rate — sensitive to team/process but **does not** reflect worker count.  
**CNC_ROUTER** guardrail in `workcenter_rates_service` prefers `per_linear_meter` for CNC/LASER codes — but templates still use time formulas pointing at `CNC_ROUTER`.

### 3.7 Machine vs labor

Not separated in registry — single workcenter rate. Forming/bonding correctly use dedicated workcenter codes with EUR/ml; CNC still hourly-equivalent via time.

---

## Phase 4 — Proposed rate_basis model

| rate_basis | Meaning | Example row | CostEngine today | Action |
|------------|---------|-------------|------------------|--------|
| `per_square_meter` | Area-priced service/material | Print 12 EUR/mp | via material `unit=mp` only | Extend to operations (large format print) |
| `per_linear_meter` | Length-priced | Forming 5 EUR/ml | **Yes** | Keep; use for V-groove, fold, bonding |
| `per_piece` | Per discrete item | LED install 3 EUR/buc | No (hourly proxy) | Add basis + quantity from formula |
| `per_set` | Per job/set | Packaging 25 EUR/set | No | Add basis; static qty=1 or quote_input |
| `per_operation` | Flat per op occurrence | Panel cut 15 EUR/op | No | Add basis; replaces arbitrary minutes |
| `per_setup` | Per file/job setup | Prepress 40 EUR/setup | No | Add basis |
| `per_layer` | Per print/CNC layer pass | UV coat 2nd pass | No | Add basis + passes param |
| `per_template` | Per mounting template | CNC sablon 30 EUR/template | No | Add basis |
| `per_cut_meter` | Cut path length | CNC 2 EUR/ml tăiere | Partial (`per_linear_meter` + cut key) | Rename/clarify + formula contract |
| `per_fold_meter` | Fold/groove length | V-groove 4 EUR/ml pliu | Partial | Same as linear_meter with fold_length_m |
| `per_print_square_meter` | Print area only | Ecosolvent 8 EUR/mp print | No | Add for print ops |
| `per_mounting_point` | Fixings count | 2 EUR/punct | No | Add when quote_input has point count |
| `per_led_module` | Per module installed | (often material) | material buc | Optional labor mirror |
| `per_power_supply` | Per PSU wired | (often material) | material buc | Optional labor mirror |
| `hourly` | True time-based | Rare consulting | **Yes** | Restrict to ops where time is only fair unit |
| `included_overhead` | Absorbed in margin | General QC, office | No | Metadata flag; zero line cost |
| `internal_only` | Never in quote total | QC inspection | No | Template op flag; skip in CostEngine |

**Schema note:** Expanding `VALID_RATE_BASES` requires migration approval for enum/check constraints and CostEngine branch logic — **do not migrate without approval**.

---

## Phase 5 — Template-specific tables

### A. TPL-VOLUMETRIC-LETTERS

| Item | Current basis | Recommended | Price source | Issue | Action |
|------|---------------|-------------|--------------|-------|--------|
| Face material | mp formula | mp | EUR owner-confirmed | Currency mix with RON PSU | Normalize currency |
| Back Forex | mp | mp | EUR owner-confirmed | — | Keep |
| Profile/cant | ml | ml | EUR/ml owner-confirmed | — | Keep |
| LED modules | buc formula | buc | EUR owner-confirmed | — | Keep |
| PSU | buc | buc | **RON** owner-confirmed | EUR/RON mix | Owner: pick base currency |
| Sablon Forex 3mm | mp | mp | EUR owner-confirmed | CNC separate | Keep |
| Profile forming | EUR/ml service | per_linear_meter | workcenter rate | — | Keep |
| Bonding | EUR/ml service | per_linear_meter | workcenter rate | — | Keep |
| Face CNC | time→hourly | per_cut_meter | missing CNC rate | Blocker | Change basis + rate |
| Back laser | time→hourly | per_cut_meter | missing LASER rate | Blocker | Change basis |
| LED assembly | time→hourly | per_letter / per_module | missing rate | Blocker | Owner decision |
| Electrical | static hourly | per_set | missing rate | Blocker | Owner decision |
| Painting | time + set material | per_set | paint needs_review | Estimat | Owner confirm + basis |
| Consumables | set | set | estimated EUR | needs_review | Owner confirm |
| QC | static hourly | internal_only | missing rate | Wrong model | **Remove from pricing** |
| Packaging | static hourly | per_set / overhead | missing rate | — | Owner decision |

### B. TPL-ACM-CASSETTED-PANEL

| Item | Current | Recommended | Source | Issue | Action |
|------|---------|-------------|--------|-------|--------|
| ACM 3mm | mp | mp | EUR owner-confirmed | — | Keep |
| ACM 4mm | mp | mp | EUR needs_review | Not owner-confirmed | Owner confirm |
| Panel cut | hourly static | per_operation | missing PANEL_CUTTING | Blocker | Basis + rate |
| V-groove | time→hourly | per_fold_meter | missing CNC_ROUTER | Blocker | Basis + rate |
| Fold/casette | hourly static | per_fold_meter / op | missing ASSEMBLY | Blocker | Owner decision |
| Rear lip / corners | in quote_input | formula | not separate line | corner_treatment input unused in cost? | Owner: separate line? |
| Fasteners | set material | set | generic | May lack price | Confirm inventory row |
| Mount | hourly static | per_mounting_point | missing ASSEMBLY | Blocker | Owner decision |
| QC | — | — | — | Not in template | OK |

### C. TPL-CUT-ACM-LETTERS

| Item | Current | Recommended | Source | Issue | Action |
|------|---------|-------------|--------|-------|--------|
| Cut area ACM | mp | mp | thickness variant | 4mm needs_review | Owner confirm |
| CNC cut | time→hourly | per_cut_meter | missing CNC_ROUTER | Blocker | Basis + rate |
| Edge finish | hourly static | per_cut_meter / op | missing FINISHING | Blocker | Owner decision |
| Mounting | — | — | — | Not modeled | Add if needed |

---

## Phase 6 — Pricing Registry UI implications (proposal only)

1. **Currency:** Hide on default row card; show base currency from Settings in header; advanced drawer override with warning if ≠ base.
2. **rate_basis:** Prominent label **“Unitate de calcul”** — map `per_hour` → “orar (verifică)”, `per_linear_meter` → “per ml”, etc.
3. **QC / internal:** Filter `internal_only`; hide from “Acoperire quote” stack; badge “Intern — nu facturat”.
4. **Hourly flag:** Badge **“Verifică baza”** on `per_hour` rows used by templates.
5. **Filters:** hourly | unit-based | internal-only | needs rate basis review | missing price.
6. **Rate drawer:** Expand basis dropdown when schema approved; until then show read-only recommended basis from audit.

---

## Phase 7 — Owner decision questions

### Priority 1 — Cross-cutting

1. **Monedă de bază:** EUR sau RON pentru tot registrul de costing? (PSU sunt RON, restul volumetric EUR.)
2. **QC:** Confirmăm că `QC_INSPECTION` este **internal-only** fără linie de pricing în ofertă preliminară?
3. **Conversie valutară:** Există curs fix de referință sau normalizăm manual toate prețurile la o monedă?

### TPL-VOLUMETRIC-LETTERS

4. Vopsire RAL: calcul **per set**, **per literă**, **per mp**, sau inclus în overhead?
5. CNC router (față + șablon): **per ml tăiere**, **per setup**, sau păstrăm derivarea din timp?
6. Laser spate: per ml tăiere sau per operatie?
7. Montaj LED: tarif **per literă**, **per modul**, sau păstrăm minute/literă?
8. Cablaj electric: per set job sau per literă?
9. Asamblare litere: per set (9 litere) sau per literă?
10. Ambalare + șablon: cost separat **per set** sau overhead?
11. Consumabile montaj (5 EUR/set estimat): confirmăm valoarea și unitatea?

### TPL-ACM-CASSETTED-PANEL

12. ACM 4 mm: preț identic cu 3 mm (15 EUR) sau altă valoare owner-confirmed?
13. V-groove: **per ml pliu** la ce tarif?
14. Casetare manuală: inclusă în V-groove/ml sau operatie separată?
15. Colțuri (`corner_treatment`): linie separată sau inclusă în casetare?
16. Prinderi: **per set** sau **per mounting point**?

### TPL-CUT-ACM-LETTERS

17. CNC tăiere litere ACM: **per ml perimetru** sau **per mp**?
18. Finisaj margini: per ml sau per operatie fixă?

---

## Phase 8 — Recommended implementation phases

| Phase | Scope | Touches |
|-------|--------|---------|
| **1 — Currency from Settings** | Wire `moneda_implicita` → `PricingContext`; UI default; currency mismatch blocker | orchestrator, simulate, Pricing UI, optional validation in load_*_dict |
| **2 — QC de-scope** | Remove/mark QC ops `internal_only`; skip in CostEngine costing; registry filter | templates seed, CostEngine op filter, readiness rules, tests |
| **3 — rate_basis model** | Approve schema; extend `VALID_RATE_BASES`; CostEngine branches; formula quantity contracts | workcenter_rates, cost_engine_service, formula_handlers |
| **4 — Template updates** | Per-template basis corrections (volumetric, ACM pack) | seed scripts + template patch migrations |
| **5 — Pricing UI** | Unitate de calcul, filters, currency advanced, hourly warnings | frontend Pricing Registry |

**Do not:** change quote/order snapshots, bypass readiness, fake owner-confirmed values, or commit implementation without explicit approval.

---

## Risk assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Mixed EUR/RON summed as one currency | **Critical** | Phase 1 blocker or normalization |
| QC rate added → customer charged for internal QC | High | Phase 2 before rates filled |
| Hourly rates misrepresent multi-worker jobs | Medium | Unit bases + separate production time tracking |
| CNC time formulas + hourly shop rate | Medium | per_cut_meter + owner rates |
| Removing QC breaks tests/readiness | Low | Update tests; readiness excludes internal ops |
| Schema expansion for rate_basis | Medium | Approved migration + incremental rollout |

---

## PASS/FAIL

- **Audit completeness:** **PASS**
- **Current logic vs. stated business model:** **FAIL** (currency, QC, hourly overuse)
- **Safe to implement without approval:** **NO**

---

## Key file references

- Settings currency: `frontend/src/pages/Settings.tsx`, `backend/services/cost_engine_config.py`
- Pricing Registry: `backend/services/pricing_registry_service.py`, `frontend/src/pages/Pricing.tsx`
- CostEngine v2 ops: `backend/services/cost_engine_service.py` (~L760–915)
- Rate bases: `backend/services/workcenter_rates_service.py`
- Formulas: `backend/services/formula_handlers.py`
- Templates: `backend/seeds/seed_build4_templates.py`, `backend/scripts/seed_acm_template_pack.py`
- Volumetric prices/rates: `backend/seeds/seed_volumetric_owner_confirmed_prices.py`, `backend/seeds/seed_volumetric_workcenter_rates.py`
- QC workcenter: `backend/seeds/seed_build4_workcenters.py`

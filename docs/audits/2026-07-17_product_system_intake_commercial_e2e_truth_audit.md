# WORKOS — Product System → Intake V6 → Commercial Pricing E2E Truth Audit

**Date:** 2026-07-17  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `bbffb19` (`docs(execution): close te2e-028b formula proof`)  
**Scope:** Audit only — **no implementation · no DB mutation · no new fixtures**  
**Priority:** `PRODUCT_SYSTEM_INTAKE_COMMERCIAL_E2E_TRUTH_AUDIT` (residuals paused)

### Owner decision (2026-07-17)

```text
APPROVED BUILD = LETTERS_CANONICAL_PRODUCT_SLICE_V1
TEMPLATE = TPL-VOLUMETRIC-LETTERS_v2
MODULES + GOVERNANCE UPDATES = MANDATORY DOD
```

---

## 1. Verdict

`PRODUCT_SYSTEM_INTAKE_COMMERCIAL_E2E_GATES_READY`

Commercial total for the live Letters same-scenario is **fully reconciled**. Product System participates as **template/module/contract catalog**, not as the sole form renderer. Intake UI is **mixed** (backend modular contract + hardcoded React). CPP 7G money is explained from geometry/finish facts + `commercial_rules_volumetric_v2` (DEV_BRIDGE) + selected Pricing Registry rates — **not** from Aggregate quantity formulas or planned minutes. TE2E-028A/B duration work did **not** alter commercial inputs.

---

## 2. Mini decision

| Question | Proven answer |
|----------|----------------|
| How does Product System participate? | Active template registry, mini-modules, dossier ops/materials/task_rules, formula handlers; form **bindings** partially via modular contract |
| Who creates the Intake form UI? | **Mostly hardcoded React** (`IntakeV6ReviewStep`, `ReturnCantFields`, finish options); contract is awareness/trace, not the primary renderer |
| Who produces commercial inputs? | Workspace `quote_geometry` / `finish_setup` (+ PD enrichment); **not** Aggregate material qty formulas |
| Who calculates money? | **CPP 7G** (`CommercialPriceProposalService` + `commercial_rules_volumetric_v2`) |
| Who produces planned minutes? | Aggregate static (028A) + Aggregate formula duration (028B Letters `vector_prep`); Plan consumes |
| Misalignment | Form source ≠ “PS generates forms”; Aggregate ≠ commercial quantity SoT; Pricing Registry 7I incomplete (DEV_BRIDGE active); Control Center overstates Aggregate→Pricing |

---

## 3. Repository state

| Check | Result |
|--------|--------|
| Remote | `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `bbffb19` — matches expected |
| Ports | FE `:3000` · BE `:8001` — up |
| Staged | none for this audit |
| Dirty tree | large unrelated noise — **not staged** |
| Commit | **NO COMMIT — WAITING FOR OWNER REVIEW** |

### Closed-safety regression (re-checked, not assumed)

| Claim | Runtime re-check |
|--------|------------------|
| CPP 7G commercial authority | Dry-run authority `commercial_price_proposal_7g`; QSN2 lines from 7G rules |
| Legacy hourly `/price` isolated | Prior proof + 7G notes forbid hourly; `forbidden_hourly_usage_detected` empty on QSN2 |
| Minutes ↛ commercial | No `estimated_minutes` in CPP; “not minutes” warnings; TE2E-028B fixture commercial unchanged by design |
| Snapshots frozen | QSN2 + order `92402` totals stable at 3549.1286 |
| Post-Job read-only | Existing TE2E + same-scenario evidence; not re-opened |
| Aggregate duration 028A/B | Code present at HEAD; **972910** is snapshot-only (not this commercial lineage) |

---

## 4. Current active spine

```text
Product System (templates / mini-modules / dossier / formula_handlers)
        ↓ (selection + partial form contract)
Intake V6 workspace (hardcoded UI + SVG analyzer + finish_setup / quote_geometry)
        ↓
ProductDefinitionBuilderService (compiler from form bindings + workspace payload)
        ↓
ProductAggregate (BOM / ops / task_rules / planning minutes; composition graph)
        ↓ (module activation assist only — quantities mostly NOT from Aggregate)
CommercialPriceProposal 7G (commercial_rules_volumetric_v2 + some registry rates)
        ↓
Quote draft (subtotal = commercial; grand_total = +VAT)
        ↓
Quote Snapshot V2 (freeze CPP + PD + Aggregate + geometry)
        ↓
Order Snapshot V2 / Order.total_amount
        ↓
ExecutionPlan V2 ← Aggregate ops/minutes (operational)
        ↓
Execution Reality → Post-Job (read-only)
```

**Live same-scenario lineage (Wave 7 Build 1 — used for commercial reconcile):**

| Stage | ID |
|-------|-----|
| Intake request | `IR-BUILD1-1784237119` |
| Workspace | `e1b8d1e8-0197-4723-882a-037c41c64d35` |
| Quote | `3` / `Q-V6-IV6-FAB19077-1784237120` |
| Quote Snapshot V2 | `QSN2-2026-0002` |
| Order | `92402` / `ORD-IV6-V2-1784237123-3` |
| Plan | `8` |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Commercial net | **3549.1286 RON** |
| Quote grand_total | **4294.45 RON** (= 3549.13 × 1.21 VAT) |

**Not used for commercial lineage:** `972901` (028A minutes), `972910` (028B minutes) — Order Snapshot fixtures without full Intake→quote walk.

---

## 5. Ownership matrix

| System | Owns | Reads | Produces | Writes | Must not own | Runtime proof |
|--------|------|-------|----------|--------|--------------|---------------|
| Product System | Template codes, mini-modules, dossier ops/materials/task_rules, `formula_handlers` | DB templates/dossier | Catalog + technical contracts | Admin/seed | Workspace answers, money, actuals | `/product-system`, seeds, registry |
| Intake V6 | Workspace payload, operator UX | Template + modular contract API | Answers (`client`, `quote_geometry`, `finish_setup`, SVG) | Workspace rows | Authoritative price | `/intake-v6/{id}/operator` |
| ProductDefinition | Compiled product facts/roles/composition | Form bindings + workspace | `geometry_inputs`, modules, operation roles | Preview only (frozen in snapshot) | Money, actuals | QSN2 `product_definition_snapshot` |
| ProductAggregate | Technical structure, ops, task_rules, planning minutes | PD + template/dossier | Ops/materials/task_contract/minutes | Snapshot freeze | Customer price | QSN2 aggregate; Plan 8 |
| Pricing Registry (partial) | Some op rates (print/laminate/install) | DB/settings EUR→RON | Unit rates for selected lines | Registry admin | Product geometry | Linked-logo + `SITE_INSTALLATION_STANDARD` lines |
| CPP 7G | Commercial lines + total | quote_input/geometry/finish (+ PD); module set (may use Aggregate composition) | `commercial_price_lines`, total | Snapshot only | Minutes, inventory stock truth | QSN2 CPP 29 lines |
| Quote Draft | Offer document + VAT | CPP / write path | `subtotal`/`grand_total` | Quote row | Plan minutes | quote `3` |
| Quote Snapshot V2 | Frozen commercial+technical dual | CPP + EIC + PD + Aggregate | Immutable snapshot | Snapshot row | Live reprice | `QSN2-2026-0002` |
| Order Snapshot V2 | Frozen accepted commercial | Quote Snapshot | Order total + plan inputs | Order | Reprice from execution | order `92402` |
| ExecutionPlan | Planned tasks/minutes | Aggregate ops/minutes | Plan/tasks | Plan row | Commercial total | plan `8` |
| Execution Reality | Actual sessions | Plan tasks | Actual minutes | Reality row | Commercial | same-scenario session |
| Post-Job | Reconciliation read model | Plan + Reality | variance / missing | **none** | Write-back | post-job-truth API |
| EIC | Internal cost estimate | Similar facts | Internal total | Snapshot side | Customer price | QSN2 EIC present |
| CostEngine sim | Internal simulate-cost | Formulas/rates | Cost sim | none on spine | Customer offer | Legacy `/price` 410 |

---

## 6. Product System audit

### Registry
- **Active pilot:** `TPL-VOLUMETRIC-LETTERS_v2` (also aliases without `_v2` in places).
- Storage: `product_templates` + dossier JSON + mini-module registry + seeds (`seed_build4_templates`, `seed_tpl_volumetric_letters_*`).
- Intake selection: workspace `template_code` / `selected_template_code`.

### Intake contract classification

| Concern | Status |
|---------|--------|
| Form modules (mini-module registry) | `ACTIVE_CURRENT` (awareness + module list) |
| Field bindings (`VOLUMETRIC_FIELD_BINDINGS`) | `PARTIAL_CURRENT` — code in Intake modular form service, not generated from dossier at runtime |
| Labels/types/visibility in React UI | `HARDCODED_ELSEWHERE` |
| Validation (operator blockers) | `PARTIAL_CURRENT` — readiness services + UI |
| Quantity formulas on ops | `ACTIVE_CURRENT` in template/CostEngine path; **not** CPP SoT |
| Duration formulas | `PARTIAL_CURRENT` — handlers + 028B contract for `vector_prep` |
| Commercial measurement outputs as Aggregate API | `MISSING` / `DEFINED_NOT_CONSUMED` for 7G |

**Plain truth:** Product System is a real catalog + technical graph owner. It does **not** currently “generate” the operator form as a schema-driven UI.

---

## 7. Intake V6 form-generation audit

| # | Answer |
|---|--------|
| 1 Route | `/intake-v6/:workspaceId/operator` → `IntakeV6OperatorWorkspaceApp` |
| 2 UI builder | `IntakeV6OperatorWorkspace` + steps (`SvgAnalyzer`, `ReviewStep`, confirm) — **component-authored** |
| 3 Backend schema | `GET /api/v1/intake-v6/form-contract/{template_code}` (+ workspace template-form-contract) |
| 4 From Product System? | **Partial** — mini-modules + form-system backbone; bindings hardcoded in `intake_v6_modular_form_contract_service.py` |
| 5 Hardcoded in Intake? | **Yes** — majority of controls |
| 6 Mixed sections? | **Yes** — SVG metrics from analyzer; finishes/cant from React; contract panel awareness |
| 7 Duplicated product forms? | Volumetric plugin + legacy V4 aliases; ACM paths separate |
| 8 Labels/options | Frontend catalogs (`intakeV6FaceFinishOptions`, RAL/Oracal UI) + contract labels for bindings |
| 9 Template selection | Workspace template / product plugin registry |
| 10 Version persisted | Workspace `template_code`; form `contract_version` 1.0.0; snapshot `template_code` — **no form-schema hash on order** |
| 11 PS change impact | Dossier/ops changes affect Aggregate/Plan; UI fields do not auto-update from PS |
| 12 Old workspaces | Payload retained; reproducible if DB kept — form UI may drift |

### Form contract (live)

`GET …/form-contract/TPL-VOLUMETRIC-LETTERS_v2` → `field_binding_count=22`, `active_module_count=7`, registry_version `1.0.0`.

### Field table (Letters — contract bindings + primary UI)

| Intake section/field | UI source | Backend source | Product System source | Saved answer path | Downstream consumers | Status |
|----------------------|-----------|----------------|----------------------|-------------------|----------------------|--------|
| SVG file | Analyzer step | workspace upload | geometry_svg module | `svg_source.*` | PD geometry gate, analysis | MIXED |
| width/height mm | Client / analyzer | binding `width_mm`/`height_mm` | module tags | `client.*` / geometry | PD, commercial geometry | MIXED |
| letter_count | Analyzer metrics | binding | geometry_svg | `quote_geometry.letter_count` | PD, 7G LED/count, 028B duration | ACTIVE |
| letter_perimeter_m | Analyzer | binding | geometry | `quote_geometry.letter_perimeter_m` | PD, **7G ml lines**, Aggregate qty formulas (CostEngine path) | ACTIVE |
| letter_face_area_m2 | Analyzer | binding | geometry | `quote_geometry.letter_face_area_m2` | PD, **7G m2 lines** | ACTIVE |
| face_finish_type | **Hardcoded** select | binding | debitare_fata | `finish_setup.face_finish_type` | PD, commercial finish gate | MIXED |
| return_depth / return_finish | **Hardcoded** `ReturnCantFields` | bindings | modelare_cant | `finish_setup.*` | PD, 7G cant | MIXED |
| backing_mode / bevel | Review UI | bindings | debitare_spate | `finish_setup.*` | PD, Aggregate gates | MIXED |
| lighting / LED / PSU | Review UI | bindings | sistem_led | `finish_setup.*` | PD, **7G LED/PSU lines** | MIXED |
| mounting_system / sablon | Review UI | bindings | structura_suport/finisaje | `finish_setup.*` | PD, 7G sablon/install | MIXED |
| letter_group_finishes / artwork | Review / logo UI | partial bindings | linked logo | finish + layers | PD linked segments, **7G logo lines** | MIXED |
| Modular contract panel | Awareness UI | form-contract API | mini-modules | n/a (display) | Diagnostics | DISPLAY |
| Commercial dry-run panel | Review | priced-quote dry-run | — | n/a | Operator preview of 7G | CONSUMED |

---

## 8. Dead-field / consumption audit (grouped)

| Group | Classification | Notes |
|-------|----------------|-------|
| Core geometry (count, perimeter, area, W/H) | `CONSUMED` | PD + 7G + analysis |
| Finish/cant/LED/mounting gates | `CONSUMED` | PD + 7G gating |
| Modular form awareness fields | `DISPLAY_ONLY_JUSTIFIED` | Traceability |
| `finish_setup.commercial_inputs` | `SAVED_NOT_CONSUMED` / explanatory | Documented orphan |
| Emblem lighting / artwork complexity | `PARTIAL` / FUTURE | Orphan audit list |
| Aggregate `formula_id` qty formulas | `PARTIAL` | Used CostEngine/internal paths; **not** CPP line qty |
| Planning minutes | `CONSUMED` by Plan/Post-Job only | Not commercial |

---

## 9. ProductDefinition audit

| Aspect | Truth |
|--------|-------|
| Service | `ProductDefinitionBuilderService` |
| Role | **Active partial compiler** — not a thin answers wrapper |
| Inputs | Form contract bindings + workspace payload (+ composition) |
| Outputs | `geometry_inputs`, `canonical_values`, modules, operation/material roles, composition, validation |
| UI | **No dedicated operator page** — embedded/API |
| Provenance | Entries include form_contract version |

### Important facts (same-scenario)

| Fact | Intake source | Normalization | Owner | Aggregate use | Pricing use | Execution use |
|------|---------------|---------------|-------|---------------|-------------|---------------|
| letter_count=19 | quote_geometry / analyzer | float/int | PD geometry | ops presence | LED counts / gates | task identity |
| letter_perimeter_m=20.9727 | analyzer | float m | PD | qty formulas (tech) | **7G ml × 25/30** | — |
| letter_face_area_m2=1.2638 | analyzer | float m2 | PD | materials | **7G m2 lines** | — |
| width/height | client/analyzer | mm | PD | mounting/sablon | sablon area path | — |
| finish/LED/mount | finish_setup | enums/bools | PD | module activation | line gates | task triggers |
| linked logo segments | composition/layers | confirmed segments | PD | Aggregate composition | **7G logo_* lines** | linked tasks |

---

## 10. ProductAggregate audit

| Aggregate output | Source | Formula/logic | Consumer | Current authority | Risk |
|------------------|--------|---------------|----------|-------------------|------|
| operations list | template/dossier | copy + composition | Plan V2 | Technical SoT | OK |
| estimated_minutes static | seed static | TE2E-028A | Plan | Operational | OK |
| estimated_minutes formula | planning_duration_contract + facts | TE2E-028B `count_based_time` | Plan (when resolved) | Operational | Letters-only |
| materials | template formulas | formula_handlers qty | Cost/BOM paths | Technical | Not CPP SoT |
| task_rules | dossier compile | PA service | Plan V2 | Technical | Proven Wave 7 |
| composition_graph | PD composition | explicit graph | 7G **module activation** only | Assist | Easy to over-read as pricing qty |
| Monetary fields | — | — | — | **None** | — |

**Plain answers:**
- Does Aggregate emit commercial pricing quantities for 7G? **No (not as CPP quantity SoT).**
- Does 7G consume those outputs? **Only for module/composition activation assist; quantities from geometry paths.**
- Does 7G reconstruct quantities independently? **Yes.**
- Commercial vs technical qty duplicated? **Yes — parallel.**
- Aggregate monetary logic? **No.**
- Do minute formulas affect commercial fields? **No.**

---

## 11. Formula taxonomy

| Formula | Category | Owner | Inputs | Output | Active caller | Downstream |
|---------|----------|-------|--------|--------|---------------|------------|
| Analyzer geometry (perimeter/area/count) | Product/geometry | Intake SVG analysis | SVG | m / m² / count | Workspace save | PD + 7G |
| `perimeter_pass_linear_meter` etc. | Quantity | PS `formula_handlers` | perimeter keys | ml | CostEngine / Aggregate BOM | Not CPP |
| `count_based_time` (028B) | Duration | PS + Aggregate contract | letter_count | minutes | Aggregate planning duration | Plan only |
| Static qc/assembly minutes | Duration | PS seed | — | minutes | Aggregate copy | Plan |
| `VOL_V2_*` / ACM_* commercial rules | Commercial pricing | `commercial_rules_volumetric_v2` | geometry paths | RON lines | CPP 7G | Quote/Order |
| Registry LARGE_FORMAT_PRINT / LAMINATION / FACE_VINYL / SITE_INSTALL | Commercial pricing | Pricing Registry + EUR→RON | area/set | RON | Linked logo / install | Quote/Order |
| EIC capacity / internal | Internal-cost | EIC | similar facts | internal total | EIC preview | Snapshot side only |
| Readiness blockers | Readiness | Intake/PD services | payload | pass/fail | Confirm gate | Blocks freeze |

**Ambiguity:** template ops marked `formula_based` mix **quantity** (commercial CostEngine heritage) with **placeholder minutes=0** — TE2E-028A/B correctly treat planning separately.

---

## 12. Pricing Registry truth

| Item | Truth |
|------|--------|
| Official Step 7I registry | **Not fully the CPP SoT** |
| Active CPP rule pack | `backend/data/commercial_rules_volumetric_v2.py` — explicitly **temporary / DEV_BRIDGE** |
| DEV_BRIDGE tariffs used | face 25 RON/ml, cant 30 RON/ml, back 20 RON/m², LED 5 RON/buc, PSU 150, finish 35 RON/m², sablon forex 15 RON/m² |
| True registry rates used | `SITE_INSTALLATION_STANDARD`, `LARGE_FORMAT_PRINT`, `LAMINATION`, `FACE_VINYL_APPLICATION_LABOR` (EUR→RON) |
| Minutes/hours | Forbidden for commercial basis; not used in line math |
| Internal cost | Separate EIC snapshot — not customer total |

---

## 13. CPP 7G exact calculation trace (QSN2-2026-0002)

**Geometry facts:** perimeter 20.9727 ml · area 1.2638 m² · letters 19 · artwork boxes ×2 · workspace `e1b8d1e8-…`

| Commercial line | Pricing key | Qty | Unit | Unit price | Source field | Origin | Subtotal |
|-----------------|-------------|----:|------|------------|--------------|--------|---------:|
| debitare_fata | VOL_V2_FACE_CNC_ML | 20.9727 | ml | 25 | letter_perimeter_m | rules DEV_BRIDGE | 524.3175 |
| modelare_cant_aluminiu | VOL_V2_RETURN_PROFILE_ML | 20.9727 | ml | 30 | letter_perimeter_m | rules | 629.181 |
| debitare_spate | VOL_V2_BACK_CNC_M2_DEV_BRIDGE | 1.2638 | m2 | 20 | letter_face_area_m2 | rules | 25.276 |
| sistem_led_module | VOL_V2_LED_MODULE_PIECE | 84 | buc | 5 | led module count | rules | 420.0 |
| sursa_led | VOL_V2_LED_PSU_PIECE | 1 | buc | 150 | PSU | rules | 150.0 |
| finisaje_colantare_vopsire | VOL_V2_FINISH_M2_OR_MINIMUM | 1.2638 | m2 | 35 | face area | rules | 44.233 |
| sablon_montaj_forex | VOL_V2_SABLON_FOREX_DEV_BRIDGE | 3.0523 | m2 | 15 | sablon area | rules | 45.7845 |
| ambalare | VOL_V2_PACKAGING_PENDING | — | set | — | pending | rules | 0.0 |
| montaj | SITE_INSTALLATION_STANDARD | 1 | locatie | 1000 | site install | **registry EUR→RON** | 1000.0 |
| acm_* (5 lines) | ACM_BOXED_* | … | … | … | ACM scope facts | rules | 41.28 |
| logo_* ×2 segments | VOL_V2_LOGO_* / registry print|lam|app | perimeters/areas/LED | … | logo geometry + registry | rules+registry | 649.0466 |
| **SUM** | | | | | | | **3549.1286** |
| **CPP commercial_total** | | | | | | | **3549.1286** |
| Order total_amount | | | | | | | **3549.1286** |
| Quote grand_total | | | | | | | **4294.45** (= net×1.21) |

**Verdict:** `COMMERCIAL TOTAL = RECONCILED` (exact). No invented tariffs — values from live snapshot + published DEV_BRIDGE constants + registry-mapped lines.

**Minutes in CPP blob:** only explanatory (“not minutes”) / forbidden-hourly notes — **not** line inputs.

---

## 14. Same-fact multi-consumer map

| Fact | Entered | Stored | Compiled | Technical | Commercial | Duration | Duplicate calc? |
|------|---------|--------|----------|-----------|------------|----------|----------------:|
| letter_perimeter_m | Analyzer | workspace quote_geometry | PD geometry | Aggregate qty formulas | 7G ml lines | EIC capacity (parallel) | **Yes** (tech vs commercial paths) |
| letter_face_area_m2 | Analyzer | workspace | PD | materials | 7G m2 | — | Mild |
| letter_count | Analyzer | workspace | PD | ops | LED-related | 028B `count_based_time` | Shared fact OK |
| face_finish | Operator UI | finish_setup | PD | gates | finish line gate | — | No |
| LED count | Derived/UI | finish_setup | PD | materials | 7G piece lines | — | Possible dual derive |
| Planned minutes | Aggregate resolve | Aggregate/Plan | — | Plan/Post-Job | **No** | Yes | No commercial dup |

---

## 15. Commercial vs operational separation

| Data | Product truth | Commercial input | Operational input | Internal-cost |
|------|:---:|:---:|:---:|:---:|
| Dimensions / perimeter / area | yes | yes | sometimes | yes |
| Letter count | yes | yes | duration 028B | yes |
| Finish / LED / mount | yes | yes | task gates | yes |
| Aggregate qty formulas | yes | no (not CPP) | BOM/tech | possible |
| Planned minutes | no money | no | Plan | no customer |
| Actual minutes | no | no | Reality/Post-Job | no |
| CPP total | no geometry | money | no | no |
| EIC total | no | no | no | yes |

**Invariant held:** engines share **facts**, not each other’s **results**. Minutes do not set price; price does not set minutes; EIC is not customer price.

---

## 16. Frontend calculation audit

| Area | Classification |
|------|----------------|
| CPP dry-run display | Display of backend 7G — OK |
| SVG geometry metrics | Authoritative **technical** capture (backend analysis) — OK if server-sourced |
| Local finish option lists | Input assistance / hardcoded catalogs |
| Material breakdown panels | Diagnostic / draft — watch for authoritative feel |
| Quote VAT display | Document-level — OK |
| Frontend inventing commercial totals | **Not found as offer authority** on V6 spine |
| Minute calculation in FE | Display only from plan/Post-Job |

---

## 17. Parallel-system inventory

| Domain | Canonical | Parallel | Reachable | Risk | Recommendation |
|--------|-----------|----------|:---------:|------|----------------|
| Form schema | Modular form contract | Hardcoded Review UI | Yes | High for “PS generates forms” claim | Option A |
| Commercial rules | CPP 7G rules file | Full Pricing Registry 7I | Yes | Medium — DEV_BRIDGE | Owner replace before rollout |
| Quantity | Geometry → 7G | Aggregate/CostEngine formulas | Yes | Medium duplication | Option B |
| Duration | Aggregate planning | EIC capacity; volumetric_execution_dispatch hardcodes | Partial | Low if Plan ignores | Keep Plan-only |
| Quote price | 7G | Legacy `/entities/quotes/price` | **410 isolated** | Contained | Keep isolated |
| Intake versions | V6 | V4 aliases/re-exports | Yes | Low | Leave |
| PreOrder / product truth audit | — | readonly adapters (uncommitted dirty) | Dev | Noise | Out of audit scope |

---

## 18. Versioning / snapshot audit

| Artifact | Version link today | Gap |
|----------|-------------------|-----|
| Template | `template_code` on workspace/snapshot | No immutable template content hash on order |
| Form contract | `contract_version` 1.0.0 in PD provenance | Not stamped on Order row |
| Pricing rules | Implicit in frozen CPP lines/source strings | No registry version id on all DEV_BRIDGE lines |
| Aggregate | Frozen in QSN2/OSN2 JSON | Future Aggregate rebuild won’t mutate freeze |
| Plan | Frozen tasks_json | Future duration formula won’t rewrite plan `8` |
| Quote↔Order | total_amount = commercial net; quote VAT separate | Explainable |

**Can future template/pricing/duration change alter accepted quotes/orders/plans?** Frozen snapshots/plans: **no** if not regenerated. Live dry-run: **yes**.

**VERSIONING = PARTIAL** (safe for frozen money; weak for form/schema archaeology).

---

## 19. Letters complete truth matrix

| Element | Product System | Intake V6 | ProductDefinition | Aggregate | Pricing 7G | Execution | Status |
|---------|----------------|-----------|-------------------|-----------|------------|-----------|--------|
| Template `TPL-VOLUMETRIC-LETTERS_v2` | Registry/dossier | Selected | Compiles | Builds | RULES_BY_TEMPLATE | Tasks | ACTIVE_CONNECTED |
| Form fields | Bindings + modules | **Hardcoded UI** | Consumes bindings | Form contract keys | Geometry/finish paths | — | HARDCODED / MIXED |
| Geometry facts | — | Analyzer+save | geometry_inputs | Uses facts | **Primary qty SoT** | — | ACTIVE_CONNECTED |
| Qty formulas on ops | formula_handlers | — | — | Carries formula_id | **Not used** | — | DEFINED_NOT_USED (for 7G) |
| Duration static | seed | — | — | emits | no | Plan | ACTIVE (028A) |
| Duration formula | count_based_time | letter_count | facts | resolve 028B | no | Plan | ACTIVE_PARTIAL (Letters one op) |
| Commercial lines | — | dry-run UI | enrich | module assist | **SoT money** | no | ACTIVE_CONNECTED |
| Task rules | dossier | — | — | compile | no | Plan | ACTIVE_CONNECTED |
| Snapshots | — | workspace_id | frozen | frozen | frozen CPP | consume | ACTIVE_CONNECTED |

---

## 20. Runtime / UI verification

| Surface | URL / API | Result |
|---------|-----------|--------|
| Intake V6 | workspace `e1b8d1e8-…` API | template Letters_v2; payload geometry+finish present |
| Form contract | `GET …/form-contract/TPL-VOLUMETRIC-LETTERS_v2` | 22 bindings / 7 modules |
| Quote | `GET …/quotes/3` | subtotal ≈ 3549.13; grand 4294.45 (VAT) |
| Snapshot | `GET …/quote-snapshot-v2/QSN2-2026-0002` | CPP total 3549.1286; 29 lines; PD+Aggregate present |
| Order | `GET …/orders/92402` | total_amount 3549.1286 |
| Execution | `http://127.0.0.1:3000/execution/92402` | Plan 8 / Post-Job (Wave 7 evidence) |
| ProductDefinition UI | — | **No dedicated page** (limitation) |
| 028B minutes fixture | `/execution/972910` | Operational proof only — **not** commercial lineage |

---

## 21. Contradiction register

| ID | Claim | Source A | Source B | Runtime truth | Severity | Recommendation | Owner gate |
|----|-------|----------|----------|---------------|----------|----------------|------------|
| C1 | PS generates Intake forms | Narrative / Control Center “contracts consumable by Intake” | Hardcoded Review UI | **MIXED** — contract exists; UI not schema-driven | High | Option A | FORM_SOURCE |
| C2 | Aggregate feeds commercial quantities | Control Center “Aggregate → Pricing” | CPP `_extract_quantity` from geometry paths | Aggregate assists modules only | High | Option B | AGG_TO_7G |
| C3 | Pricing Registry is CPP SoT | Ideal Step 7I | `commercial_rules_volumetric_v2` DEV_BRIDGE | Hybrid DEV_BRIDGE + some registry | High | Owner pricing replace | REGISTRY |
| C4 | formula_based means duration | Template ops | TE2E-028A/B + qty formulas | Ambiguous tag — categories differ | Medium | Taxonomy discipline | FORMULA_TAXONOMY |
| C5 | Quote total = commercial total | Quote grand_total | Order/CPP net | grand = net×VAT; net matches | Low (explainable) | Document VAT | — |
| C6 | 972910 proves commercial spine | 028B fixture | No Intake workspace lineage | Minutes-only fixture | Medium | Don’t use for commercial E2E | — |
| C7 | EIC timing = Plan minutes | EIC capacity | Aggregate/Plan | Parallel; Plan ignores EIC | Medium | Keep split | — |

---

## 22. Current maturity ratings

| Stage | Rating | Evidence |
|-------|--------|----------|
| Product System registry | `ACTIVE_CONNECTED` | Live template Letters_v2 |
| Form contract | `ACTIVE_PARTIAL` | API 22 bindings; UI not driven |
| Intake renderer | `HARDCODED` / `ACTIVE_PARTIAL` | React steps |
| ProductDefinition compiler | `ACTIVE_CONNECTED` | QSN2 PD geometry matches analyzer |
| ProductAggregate resolver | `ACTIVE_PARTIAL` | Tech+minutes strong; commercial qty weak |
| Commercial outputs (Aggregate) | `DEFINED_NOT_USED` for 7G qty | — |
| Pricing Registry | `ACTIVE_PARTIAL` | Partial; DEV_BRIDGE dominant |
| CPP 7G | `ACTIVE_CONNECTED` | Reconciled 3549.1286 |
| Quote/Order snapshots | `ACTIVE_CONNECTED` | Frozen match |
| Execution derivation | `ACTIVE_PARTIAL` | Plan from Aggregate; minutes partial historically |
| Post-Job | `ACTIVE_CONNECTED` | Read-only |

---

## 23. Modules impact (evaluate only — no update)

Control Center **overstates**:
- Aggregate as commercial quantity feeder;
- Product System as if it fully drives Intake forms;
- Pricing input as “Aggregate / context” without naming geometry/DEV_BRIDGE.

**Expected after owner GO:** limitation + evidence updates only (`LIMITATION / EVIDENCE UPDATE`). No new node.

---

## 24. Governance impact (evaluate only)

`BOUNDARY CLARIFICATION, NO POLICY CHANGE` recommended:
- PS owns reusable definitions;
- Intake owns capture UI + answers;
- PD compiles facts;
- Aggregate resolves technical/operational truth;
- 7G owns money from **commercial measurements** (today: geometry paths);
- Execution owns plan/actuals.

---

## 25. Recommended coherent build

### Option A — Product System-driven Intake contract (Letters)
Drive one Letters Review subsection from form-contract bindings (labels/required/module tags).  
**Risk:** UI churn. **Schema:** none if JSON contract enough. **Pricing risk:** low.

### Option B — Aggregate→7G commercial measurement contract
Define explicit commercial measurement outputs (perimeter_ml, area_m2, led_count, …) emitted by Aggregate/PD and **required** by CPP rules instead of ad-hoc path scraping.  
**Risk:** must not change accepted totals for frozen snaps; live dry-run parity tests. **Pricing risk:** medium. **Addresses C2/C3.**

### Option C — Combined Letters canonical slice
A+B in one isolated scenario. Higher coupling; only if owner wants one proof.

### Recommendation: **Option B** first

Commercial money is already explainable, but the **product→price contract** is the architectural hole the owner is probing: Aggregate technical formulas and 7G quantities are parallel. Closing that gap proves Product System / Aggregate are not decorative relative to pricing — without pretending the React form is already PS-generated (that is Option A, second).

Exclusions: no Stock G3, labor $, template breadth, duration expansion, schema migration, DEV_BRIDGE tariff invention.

---

## 26. Owner gates (from proven findings)

```text
PRODUCT SYSTEM → INTAKE V6 = PARTIAL
INTAKE FORM SOURCE = MIXED
PRODUCT DEFINITION = ACTIVE COMPILER
PRODUCT AGGREGATE = PARTIAL
CPP 7G INPUTS = EXPLAINED
COMMERCIAL TOTAL = RECONCILED
MINUTES → COMMERCIAL PRICE = NO
PARALLEL PRODUCT MODEL = PRESENT
VERSIONING = PARTIAL
IMPLEMENTATION = STOP
RECOMMENDED BUILD = OPTION_B_AGGREGATE_TO_7G_MEASUREMENT
FORM_SOURCE_FOLLOWUP = OPTION_A
PRICING_REGISTRY_7I = OWNER_REPLACE_DEV_BRIDGE
TE2E-028C / STOCK_G3 / LABOR = REMAIN_PAUSED
AUDIT COMMIT = DA / NU
```

---

## 27. Files created

| Path |
|------|
| `docs/audits/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md` |
| `docs/worklog/realignment/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md` |

No application code changes. No data mutation.

---

## 28. Commit status

`NO COMMIT — WAITING FOR OWNER REVIEW`

---

## 29. Metodă

1. Locked HEAD `bbffb19`; paused residuals.  
2. Separated product / commercial / internal-cost / operational authorities before judging “correctness.”  
3. Reconciled live QSN2 lines to the cent — no invented tariffs.  
4. Detected mixed form source and Aggregate≠7G quantity SoT as parallel models.  
5. Kept present truth distinct from target architecture.  
6. Confirmed TE2E-028B minutes did not become commercial inputs.  
7. **No implementation.**

---

## 30. Owner conclusion pack

```text
PRODUCT SYSTEM → INTAKE V6 = PARTIAL
INTAKE FORM SOURCE = MIXED
PRODUCT DEFINITION = ACTIVE COMPILER
PRODUCT AGGREGATE = PARTIAL
CPP 7G INPUTS = EXPLAINED
COMMERCIAL TOTAL = RECONCILED
MINUTES → COMMERCIAL PRICE = NO
PARALLEL PRODUCT MODEL = PRESENT
VERSIONING = PARTIAL
IMPLEMENTATION = STOP
```

---

## 31. Next safe step

**Wait for owner review.**  
Do not start TE2E-028C, Stock G3, labor money, or a Product System implementation build until gates are set.

---

## Roadmap awareness checkpoint

| Item | Score / note |
|------|----------------|
| Roadmap awareness | **9/10** |
| Current position | Post TE2E-028B; commercial E2E truth audit complete |
| Cat sunt in directia stabilita | **~85%** — spine real, form/qty contracts partial |
| Dead pieces | Don’t treat Aggregate qty formulas as CPP; don’t treat form-contract as full UI |
| Parallel product-flow | **PRESENT** (UI + qty paths) |
| Parallel commercial-flow | Legacy `/price` isolated; DEV_BRIDGE parallel to full registry |
| Formula-authority | Categories separable; `formula_based` tag ambiguous |
| Wave 7 / UTF-8 / Control Center / UI-TRUTH-01C / TE2E-028A/B / commercial isolation / legacy isolation | Intact (CC accuracy caveats above) |
| Audit explains real system without assumptions | **Yes** — with explicit MIXED/PARTIAL ratings |

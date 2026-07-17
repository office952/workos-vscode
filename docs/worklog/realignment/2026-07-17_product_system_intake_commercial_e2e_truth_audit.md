# Worklog — Product System → Intake V6 → Commercial Pricing E2E Truth Audit

**Date:** 2026-07-17  
**Type:** Audit only (no implementation, no DB mutation)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `bbffb19`  
**Canonical audit:** `docs/audits/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md`

---

## Purpose

Owner-required proof that Product System, Intake V6, ProductDefinition, ProductAggregate and CPP 7G still form one coherent product/commercial flow after operational-minute work (TE2E-028A/B). Residuals (028C, Stock G3, labor $, breadth) paused.

---



## What was done

1. Repo gate: HEAD `bbffb19` match; ports up; no auto branch switch.
2. Traced active code: modular form contract, hardcoded Intake UI, PD builder, Aggregate, CPP 7G + `commercial_rules_volumetric_v2`, snapshots, Plan/Post-Job.
3. Selected live commercial lineage: workspace `e1b8d1e8-…` → quote `3` → `QSN2-2026-0002` → order `92402` (not 972910).
4. Reconciled CPP **29 lines → 3549.1286 RON** exactly; quote grand_total **4294.45** = net × 1.21 VAT.
5. Proved minutes are not commercial inputs; Aggregate does not supply CPP quantities; form source is MIXED.
6. Wrote audit + this worklog only.

---



## Verdict

`PRODUCT_SYSTEM_INTAKE_COMMERCIAL_E2E_GATES_READY`

---



## Owner conclusion pack

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



## Recommended build (after owner GO)

**Option B** — Aggregate/PD → 7G commercial measurement contract (Letters).  
Follow-up: Option A (form contract drives UI).  
DEV_BRIDGE → Pricing Registry 7I remains owner pricing work.

---



## Owner decision (2026-07-17)

```text
APPROVED BUILD = LETTERS_CANONICAL_PRODUCT_SLICE_V1
TEMPLATE = TPL-VOLUMETRIC-LETTERS_v2
MODULES + GOVERNANCE UPDATES = MANDATORY DOD
```

## Commit policy

1. Audit/worklog only: `docs(product): approve letters canonical product slice`
2. Implementation commits follow (max 3) after field matrix.

Do not stage unrelated dirty-tree files.

---

## Implementation section — LETTERS_CANONICAL_PRODUCT_SLICE_V1

**Audit commit:** `10926d2` — `docs(product): approve letters canonical product slice`  
**HEAD baseline before impl:** `bbffb19` → after audit `10926d2`

### Owner decision

```text
APPROVED BUILD = LETTERS_CANONICAL_PRODUCT_SLICE_V1
TEMPLATE = TPL-VOLUMETRIC-LETTERS_v2
MODULES + GOVERNANCE = MANDATORY DOD
```

### Field matrix (canonical Letters)

| Field | Product System contract | Intake UI | Workspace path | ProductDefinition output | Aggregate technical use | Aggregate commercial use | CPP use | Execution use | Decision |
|---|---|---|---|---|---|---|---|---|---|
| vector_file | binding + file | SVG analyzer | svg_source.file_name | vector_file | ops/geometry readiness | — | readiness gate | — | CANONICAL |
| width_mm | binding number/mm | geometry cards | client.width_mm | dimensions.width_mm | form/ops | — | — | duration facts | CANONICAL |
| height_mm | binding number/mm | geometry cards | client.height_mm | dimensions.height_mm | form/ops | — | — | — | CANONICAL |
| letter_count | binding count | geometry / litere | quote_geometry.letter_count | quantity | ops | — | — | formula minutes | CANONICAL |
| letter_perimeter_m | binding m | analyzer metrics | quote_geometry.letter_perimeter_m | letter_perimeter_m | ops | cm.debitare_fata / modelare_cant | qty ml | — | CANONICAL |
| letter_face_area_m2 | binding m2 | analyzer metrics | quote_geometry.letter_face_area_m2 | letter_face_area_m2 | ops | cm.debitare_spate / finisaje | qty m2 | — | CANONICAL |
| face_finish_type | binding enum | Review letter groups (contract label) | finish_setup.face_finish_type | layers/face | components | selector/material gates | material gates | — | CANONICAL |
| return_depth_mm | binding mm | ReturnCantFields (contract label) | finish_setup.return_depth_mm | return_depth_mm | ops | diagnostic | warnings | — | CANONICAL |
| return_finish_type | binding enum | ReturnCantFields (contract label) | finish_setup.return_finish_type | return_finish_type | components | — | — | — | CANONICAL |
| volum_aluminum_module_template_code | binding | Review module select | finish_setup.… | linked_modules | modules.required | — | — | — | CANONICAL |
| backing_mode | binding enum | Review backing (contract label) | finish_setup.backing_mode | backing_mode | components | — | — | — | CANONICAL |
| back_bevel_enabled | binding bool | Review backing | finish_setup.back_bevel_enabled | back_bevel_enabled | components | — | — | — | CANONICAL |
| lighting_system_type | binding enum | Lighting section (contract label) | finish_setup.lighting_system_type | lighting_system_type | modules LED | module gate | module gate | — | CANONICAL |
| led_module_count | binding count | Lighting | finish_setup.led_module_count | led_module_count | components | cm.sistem_led_module | qty buc | — | CANONICAL |
| selected_psu_watts | binding | Lighting | finish_setup.selected_psu_watts | selected_psu_watts | components | cm.sistem_led_psu (fixed) | piece/fixed | — | CANONICAL |
| mounting_system | binding enum | Review montaj (contract label) | finish_setup.mounting_system | mounting_system | module activation | — | — | — | CANONICAL |
| mounting_template_enabled | binding | Review șablon | finish_setup.mounting_template_enabled | mounting_template_enabled | materials | gates sablon lines | gates | — | CANONICAL |
| mounting_template_area_m2 | binding m2 | Review | finish_setup.mounting_template_area_m2 | mounting_template_area_m2 | materials | cm.sablon_* | qty m2 | — | CANONICAL |
| letter_group_finishes | binding | Review groups | finish_setup.letter_group_finishes | letter_group_finishes | finish graph | finisaje line warnings | finisaje | — | CANONICAL |
| metal_support_required | derived binding | not operator field | quote_input (derived) | metal_support_required | module trigger compat | — | — | — | DERIVE_ONCE |
| premount_bar_length_ml | derived | display/compat | quote_input | premount length | ops/materials | structura lines | qty when applicable | — | DERIVE_ONCE |
| bar_material | derived | display/compat | quote_input | bar_material | materials | selector | selector | — | DERIVE_ONCE |

**Trigger alignment:** operator `mounting_system` → derived `metal_support_required` once in PD; module-link DB trigger remains compat (`TRIGGER_FIELD_MISMATCH` documented). No schema migration.

### Parallel model (before → after)

| Area | Before | After (Letters) |
|---|---|---|
| Form labels/required | MIXED hardcoded + contract awareness | Product System contract runtime authority (template-gated) |
| Commercial qty | CPP reconstructed from workspace paths | Aggregate `commercial_measurements` preferred; workspace = explicit COMPATIBILITY |
| Minutes | Operational only | Unchanged — never in commercial measurements |

### Contract / code anchors

- Form contract version: `1.1.0-letters-canonical`, `runtime_authority=true`
- Measurement contract: `letters_commercial_measurement_v1`
- Aggregate field: `ProductAggregate.commercial_measurements`
- CPP: prefers measurement qty; warns `quantity_source=…`
- Template key case: CPP resolves uppercased canonical → declared `TPL-VOLUMETRIC-LETTERS_v2` rules key

### Intake renderer (Letters-gated)

- `resolveLettersCanonicalFieldLabels` + Review wiring for face/cant/spate/lighting/mounting labels from contract
- Section shells remain React composition (COMPATIBILITY_TEMPORARY) — not a global Intake rewrite
- Other templates unchanged / unsupported by runtime_authority

### Tests run (targeted)

```text
pytest tests/test_letters_commercial_measurement_contract.py
pytest tests/test_letters_cpp_measurement_consumption.py
pytest tests/test_intake_v6_modular_form.py
pytest tests/test_commercial_price_proposal_preview.py
pytest tests/test_legacy_quote_price_isolation.py
vitest: lettersCanonicalFormContract, currentTruthControlCenter, ModuleChain, Governance.presentTruth
```

### Master status

```text
LETTERS_CANONICAL_PRODUCT_SLICE_V1 = COMPLETE — PROVEN_CURRENT (Letters-scoped)
SCOPE = TPL-VOLUMETRIC-LETTERS_v2
PRODUCT SYSTEM GLOBAL COVERAGE = PARTIAL
INTAKE V6 GLOBAL PRODUCT CONTRACT = PARTIAL
AGGREGATE → CPP GLOBAL COVERAGE = PARTIAL
```

### Owner conclusion (post-impl)

```text
LETTERS PRODUCT SYSTEM CONTRACT = CANONICAL
LETTERS INTAKE FORM SOURCE = PRODUCT SYSTEM (labels/required; section chrome transitional)
PRODUCT DEFINITION = ACTIVE COMPILER
PRODUCT AGGREGATE TECHNICAL TRUTH = CANONICAL
PRODUCT AGGREGATE COMMERCIAL MEASUREMENTS = CANONICAL
CPP 7G MONETARY AUTHORITY = PRESERVED
COMMERCIAL BASELINE = PRESERVED (read-only lineage unchanged)
MINUTES → COMMERCIAL PRICE = NO
MODULES PRESENT TRUTH = UPDATED
GOVERNANCE PRESENT TRUTH = UPDATED
GLOBAL PRODUCT SYSTEM COVERAGE = PARTIAL
```

### Remaining limitations

- Other templates: PARTIAL / NEVERIFICAT
- Intake section ordering still JSX (not fully dynamic module-section generator)
- Full live Quote→Order→Plan write for a brand-new customer workspace deferred to labeled local fixture policy; Aggregate→CPP write path proven in isolated pytest workspace
- Baseline records 8/9/10/11 and 92402/92403/972901/972910 not mutated

---



## Boundaries respected

- No TE2E-028C / Stock G3 / labor $ / lifecycle / template breadth.
- No mutation of plans 8/9/10 or commercial fixtures.
- No invented commercial formulas.
- TE2E-028A/B and commercial/legacy isolation not reopened without regression proof. Both explore tracks finished and agree with the audit already written:
  - [Find live Letters commercial scenario](f2a99e05-f327-4978-a8af-a67e1134f4fb): Build 1 `92402` / `QSN2-2026-0002` / 3549.1286) is the commercial lineage; 028A/B are snapshot-only.
  - [Explore PS Intake 7G spine](4a69fa6c-c0cb-44e9-8e9b-dde556aeae12): Active spine is real; Intake UI mixed/hardcoded; 7G uses geometry + DEV_BRIDGE rules, not Aggregate qty; minutes stay operational.
  No further action — audit docs remain uncommitted pending owner review.**Verdict:** `PRODUCT_SYSTEM_INTAKE_COMMERCIAL_E2E_GATES_READY`
  Your instinct matches the runtime: minutes did not rewrite commercial. What is incomplete is Product System as the real form/quantity center — not the 7G money math itself.
  ### **Mini decision**

  | **Question**         | **Proven now**                                                                    |
  | -------------------- | --------------------------------------------------------------------------------- |
  | Product System role  | Catalog + mini-modules + dossier/ops/formulas — **not** the React form generator  |
  | Who builds Intake UI | **Mostly hardcoded** Review/analyzer components; modular contract = awareness     |
  | Commercial inputs    | Workspace `quote_geometry` / `finish_setup` (+ PD)                                |
  | Who calculates money | **CPP 7G** + `commercial_rules_volumetric_v2` (DEV_BRIDGE) + some registry rates  |
  | Planned minutes      | Aggregate → Plan only (028A/B)                                                    |
  | Misalignment         | Form MIXED · Aggregate qty ≠ 7G qty · Control Center overstates Aggregate→Pricing |

  ### **Repository**
  HEAD `bbffb19` · branch match · FE/BE up · **NO COMMIT**
  ### **Live commercial reconcile (exact)**
  Lineage: workspace `e1b8d1e8-…` → quote `3` → `QSN2-2026-0002` → order `92402`  
  **29 CPP lines sum = 3549.1286 = snapshot = order**  
  Quote `grand_total` **4294.45** = net × 1.21 VAT  
  `972910` excluded (minutes fixture, no Intake→quote lineage)
  ### **Owner conclusion pack**
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
  ### **Recommended build (after GO)**
  **Option B** — Aggregate/PD commercial measurement contract consumed by 7G (Letters).  
  Then Option A — form-contract-driven UI.  
  DEV_BRIDGE → real Pricing Registry remains owner pricing work.
  ### **Files (uncommitted)**
  - `docs/audits/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md`
  - `docs/worklog/realignment/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md`
  ### **Roadmap checkpoint**
  Awareness **9/10** · direction **~85%** · TE2E-028A/B + commercial/legacy isolation **intact** · parallel form/qty models **present and documented** · residuals remain **paused**
  ### **Next safe step**
  Owner review of gates / `AUDIT COMMIT`. Do not start TE2E-028C, Stock G3, or Product System implementation until then.
  Both explore tracks finished and agree with the audit already written:
  - **[Find live Letters commercial scenario](vscode-file://vscode-app/c:/Users/offic/AppData/Local/Programs/cursor/resources/app/out/vs/code/electron-sandbox/workbench/f2a99e05-f327-4978-a8af-a67e1134f4fb)**: Build 1 (`92402` / `QSN2-2026-0002` / 3549.1286) is the commercial lineage; 028A/B are snapshot-only.
  - **[Explore PS Intake 7G spine](vscode-file://vscode-app/c:/Users/offic/AppData/Local/Programs/cursor/resources/app/out/vs/code/electron-sandbox/workbench/4a69fa6c-c0cb-44e9-8e9b-dde556aeae12)**: Active spine is real; Intake UI mixed/hardcoded; 7G uses geometry + DEV_BRIDGE rules, not Aggregate qty; minutes stay operational.
  No further action — audit docs remain uncommitted pending owner review.**Verdict:** `PRODUCT_SYSTEM_INTAKE_COMMERCIAL_E2E_GATES_READY`
  Your instinct matches the runtime: minutes did not rewrite commercial. What is incomplete is Product System as the real form/quantity center — not the 7G money math itself.
  ### **Mini decision**

  | **Question**         | **Proven now**                                                                    |
  | -------------------- | --------------------------------------------------------------------------------- |
  | Product System role  | Catalog + mini-modules + dossier/ops/formulas — **not** the React form generator  |
  | Who builds Intake UI | **Mostly hardcoded** Review/analyzer components; modular contract = awareness     |
  | Commercial inputs    | Workspace `quote_geometry` / `finish_setup` (+ PD)                                |
  | Who calculates money | **CPP 7G** + `commercial_rules_volumetric_v2` (DEV_BRIDGE) + some registry rates  |
  | Planned minutes      | Aggregate → Plan only (028A/B)                                                    |
  | Misalignment         | Form MIXED · Aggregate qty ≠ 7G qty · Control Center overstates Aggregate→Pricing |

  ### **Repository**
  HEAD `bbffb19` · branch match · FE/BE up · **NO COMMIT**
  ### **Live commercial reconcile (exact)**
  Lineage: workspace `e1b8d1e8-…` → quote `3` → `QSN2-2026-0002` → order `92402`  
  **29 CPP lines sum = 3549.1286 = snapshot = order**  
  Quote `grand_total` **4294.45** = net × 1.21 VAT  
  `972910` excluded (minutes fixture, no Intake→quote lineage)
  ### **Owner conclusion pack**
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
  ### **Recommended build (after GO)**
  **Option B** — Aggregate/PD commercial measurement contract consumed by 7G (Letters).  
  Then Option A — form-contract-driven UI.  
  DEV_BRIDGE → real Pricing Registry remains owner pricing work.
  ### **Files (uncommitted)**
  - `docs/audits/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md`
  - `docs/worklog/realignment/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md`
  ### **Roadmap checkpoint**
  Awareness **9/10** · direction **~85%** · TE2E-028A/B + commercial/legacy isolation **intact** · parallel form/qty models **present and documented** · residuals remain **paused**
  ### **Next safe step**
  Owner review of gates / `AUDIT COMMIT`. Do not start TE2E-028C, Stock G3, or Product System implementation until then.
  Both explore tracks finished and agree with the audit already written:
  - **[Find live Letters commercial scenario](vscode-file://vscode-app/c:/Users/offic/AppData/Local/Programs/cursor/resources/app/out/vs/code/electron-sandbox/workbench/f2a99e05-f327-4978-a8af-a67e1134f4fb)**: Build 1 (`92402` / `QSN2-2026-0002` / 3549.1286) is the commercial lineage; 028A/B are snapshot-only.
  - **[Explore PS Intake 7G spine](vscode-file://vscode-app/c:/Users/offic/AppData/Local/Programs/cursor/resources/app/out/vs/code/electron-sandbox/workbench/4a69fa6c-c0cb-44e9-8e9b-dde556aeae12)**: Active spine is real; Intake UI mixed/hardcoded; 7G uses geometry + DEV_BRIDGE rules, not Aggregate qty; minutes stay operational.
  No further action — audit docs remain uncommitted pending owner review.


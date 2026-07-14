# W2-INT-01 — Product Definition / Aggregate Integration Gate V1

**Task:** `W2-INT-01` / `PRODUCT_DEFINITION_AGGREGATE_E2E_INTEGRATION_GATE_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Accepted HEAD:** `96bea36`  
**Date:** 2026-07-14  
**Verdict:** `W2_INT_01_PASS_WITH_NONBLOCKING_DEBT_CLOSE_WAVE_2`

## Gate question

Does Product Definition → Product Aggregate form one coherent, deterministic composition system for the volumetric mounting spine?

**Answer: YES** for workspace builds (Cases A–D mounting graph). **Partial** for GRADI linked-logo segments (parallel path, preexisting).

## Runtime ownership

| Service | PID | Port | Worktree | HEAD served | Action |
|---------|-----|------|----------|-------------|--------|
| Backend | 21732 | 8000 | `C:\w\psiso` | `96bea36` | Started uvicorn; behavior probe confirms W2-T02 |
| Frontend | — | 3000 | — | n/a | Not required for gate |

Behavior proof (not `--reload` alone):
- Aggregate API returns `composition_graph`
- `active_child_template_codes` = ACM only on IR-MRJS4VIK
- Registry VOLUM/premount modules stripped from workspace compile

## Composition authority (integration answers)

| # | Question | Answer |
|---|----------|--------|
| 1 | PD only composition authority? | **YES** for mounting Cases A–D on workspace path |
| 2 | Aggregate only compiler? | **YES** on workspace path — no Case re-inference |
| 3 | Registry links still insert children? | **NO** on workspace path; **YES** on template-only path (expected) |
| 4 | `compose_from_product_definition()` vs graph? | Logo **adapter** runs after explicit graph; does not alter mounting graph |
| 5 | Logo segments in same graph? | **NO** — `linked_template_runtime_segments`, parallel path |
| 6 | Cases A–D + logo coexist? | **Deterministic** when segments confirmed; logo not in `composition_graph` |
| 7–8 | Node/edge ID stability | **PASS** — tested + live stable |
| 9 | Roles canonical? | **PASS** — `root_product`, `mounting_panel`, `premount_structure`, `volum_aluminum` |
| 10 | Legacy mounting fields change graph? | **NO** when `mounting_solution` present; legacy hydrates with warning only |
| 11 | Finish/cant attached once? | **PASS** — canonical values on PD; graph nodes inherit; cant via Wave 1 `product_truth` |
| 12 | Template defaults overwrite Intake? | **NO** on workspace graph compile |
| 13 | Missing child templates as warnings? | **NO** — `COMPOSITION_CHILD_AGGREGATE_MISSING` error |
| 14 | Volum nonblocking for graph? | **YES** — validated |
| 15 | Downstream consumer of volum field | Cost BOM / quote mapper (`modelare_cant` module activation) |
| 16 | Logo test failures | **Preexisting** — logo aggregate returns 0 components in test fixture |
| 17 | Cost consume frozen graph? | **NOT YET** — uses PD module states; adapter task needed |
| 18 | PD UI required before Wave 3? | **NO** |
| 19 | Vector required before Wave 3? | **NO** for composition spine |
| 20 | Wave 2 close honestly? | **YES with debt** |

## Authority path classification

| Path | Classification |
|------|----------------|
| `product_definition_composition_contract` | **CANONICAL** |
| `apply_explicit_composition_graph` | **CANONICAL** |
| `ProductAggregateService.build()` registry links | **TEMPLATE_ONLY_PATH** |
| `compose_from_product_definition()` logo merge | **READ_ONLY_COMPATIBILITY** / parallel segment adapter |
| Cost `_legacy_structural_active_modules` | **READ_ONLY_COMPATIBILITY** (Wave 3 adapter) |
| `mounting_system` for Case selection | **DEAD_PATH** when `mounting_solution` present |

**Structural re-inference on workspace path: NO**

## Logo composition classification

**`PREEXISTING_TEST_DATA_DEBT_NONBLOCKING`**

- Failures predate W2-T02 (verified: `test_compose` fails without explicit graph file)
- Root cause: logo template aggregate builds 0 components under dossier-isolation test fixture
- Logo segments are **not** graph nodes; `compose_from_product_definition()` is segment adapter, not mounting authority
- Does **not** invalidate IR-MRJS4VIK Case B spine proof
- Separate debt: unify logo segments into composition graph model (**W2-LOGO-COMPOSITION-CORRECTION**, future)

## Volum module gap

**`NONBLOCKING_FOR_WAVE_2_BLOCKS_COST`**

- Owner: **Intake** (`finish_setup.volum_aluminum_module_template_code`)
- Writer: Intake finish save / operator selection
- Consumer: PD graph (optional child), Cost/quote mapper (`modelare_cant`)
- Not required for mounting graph identity on Case B fixture
- Must remain explicit blocker through Cost until Intake persists or operator confirms

## Combined tests

| Category | Count |
|----------|------:|
| Passed | 80 |
| Failed | 8 |
| Skipped | 0 |
| Collection errors | 0 |

Failures: all in `test_product_aggregate_workspace_linked_logo_composition.py` (preexisting).

Core Wave 2 spine: **62/62 PASS** (PD composition + Aggregate graph + identity boundary).

## Live fixture IR-MRJS4VIK

- Case B confirmed
- PD nodes: root + mounting_panel
- AGG `active_child_template_codes`: ACM only
- No volum/premount invented
- `UPSTREAM_TRUTH_MISSING` for volum (honest)
- Repeated builds stable

## Downstream boundary

**`READY_WITH_REQUIRED_ADAPTER_TASK`**

- `AggregateCostBomBuilderService` calls `build_for_workspace()` (gets graph)
- `AggregateCostBomAdapter` activates modules from **PD preview states**, not `composition_graph`
- Wave 3 D-010 must decide: adopt graph as Cost authority vs adapter projection

## Decisions

| Topic | Classification |
|-------|----------------|
| PD UI | `UI_NOT_REQUIRED_BEFORE_WAVE_3` |
| Vector | `NONBLOCKING_FOR_WAVE_3` |
| Wave 3 open | **BLOCKED** until D-010 owner decision |

## Wave 3 recommendation

**`W3-D010-COST-AUTHORITY-DECISION`** (primary)

Nonblocking follow-ups:
- `W2-PREREQUISITE-VOLUM-TRUTH` (Intake persistence)
- `W2-LOGO-COMPOSITION-CORRECTION` (unify linked segments into graph model)

## Temporary debt

**YES** — logo test fixture + logo graph unification + Cost adapter + volum Intake persistence

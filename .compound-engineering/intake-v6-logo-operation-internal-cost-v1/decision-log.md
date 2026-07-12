# INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1 — Decision Log

**Phase:** PLAN  
**Accepted HEAD:** 49896b2

---

## DEC-LOPS-ARCH-01 — Selected architecture

**Problem:** How should logo operation internal cost enter EIC without duplicating letters operations?

**Evidence:**
- `EstimatedInternalCostService.build_preview` loops `bom.costable_operations` but only skips QC codes — **does not map any BOM operation to EIC lines** (lines 624–628).
- Letters operation lines are built exclusively from `RULES_BY_TEMPLATE` via `_build_operation_line` (lines 630–659).
- `bom.costable_operations` already contains **both** letters and logo operations from workspace-composed PA (adapter lines 1034–1095; `_is_aggregate_linked_logo_operation` bypasses module filter at line 307–309).
- Consuming **all** BOM operations would duplicate letters costs alongside `RULES_BY_TEMPLATE`.

**Options:**
| Option | Description |
|---|---|
| A | EIC consumes **only namespaced logo** `costable_operations`; letters stay on `RULES_BY_TEMPLATE` |
| B | EIC consumes **all** BOM operations; retire `RULES_BY_TEMPLATE` letters path |
| C | Thin adapter: BOM logo row → EIC operation contribution (same as A, explicit mapper) |
| D | Defer until PA/BOM carry minutes and internal rates |

**Recommended:** **Option A + C hybrid** — bounded logo BOM consumption via thin mapper in EIC; letters path untouched.

**Risk:** LOW if filter is strict (`source_template_code == TPL-VOLUMETRIC-LOGO_v1` + namespaced `component_ref`).

**Implementation blocked until GO:** NO (architecture)

---

## DEC-LOPS-01 — Internal rate ownership (BLOCKING for numeric values)

**Problem:** Cost BOM operation rows expose `workcenter` + `pricing_availability` from **workcenter_rates** (commercial hourly registry). EIC forbids hourly contamination (`FORBIDDEN_HOURLY_TOKENS`, `scan_hourly_contamination`).

**Evidence:**
- `CostBomCostableOperation` has no `unit_cost` or `minutes` — only `pricing_availability` for workcenter (schema lines 92–104).
- `internal_cost_rules_volumetric_v2.py` has **zero logo operation rules**; letters use fixed `internal_unit_cost` per ml/m2/piece (DEV_BRIDGE_* interim values).
- Logo seed operations have `estimatedMinutes: 0` — time is **not** canonical truth today.

**Options:**
| Option | Description |
|---|---|
| A | Add logo `internal_unit_cost` map in `internal_cost_rules_volumetric_v2` keyed by `operation_code` (parallel letters dev bridge) |
| B | `owner_decision_required` on every logo op until Step 7I official registry |
| C | Borrow `workcenter_rates` from BOM — **REJECT** (hourly commercial contamination) |

**Recommended:** **Option A** for V1 structure with interim dev-bridge constants; missing entries → `INTERNAL_OPERATION_RULE_MISSING` blocker (not zero).

**Risk:** MEDIUM — wrong interim rates mislead operators until 7I.

**Implementation blocked until GO:** **YES** for numeric rate table approval (structure can ship with explicit blockers if owner defers numbers).

---

## DEC-LOPS-02 — Quantity / time truth (DEC-EIC-03 extension)

**Problem:** BOM operation rows carry `formula_id` but no resolved quantity. EIC must not invent minutes or use letter geometry for logo.

**Evidence:**
- Logo template operations use `formula_id`: `logo_area`, `logo_perimeter`, `logo_led_modules`, `logo_psu_count` (seed).
- Material V1 already enriches `artwork_finishes` from `pd.linked_template_runtime_segments` (`_enrich_payload_artwork_finishes_from_pd`).
- `ARTWORK_OWNED_LOGO_MATERIAL_CODES` limits artwork area to print/laminate materials — same boundary must apply to operations.

**Recommended:**
- **Artwork-owned ops** (`logo_face_print`, `logo_face_laminate`, `logo_finish_application`): segment artwork finish area only.
- **Area-based CNC/back/mount** (`logo_face_cnc_cut`, `logo_back_cut`, `logo_mounting_*`): segment geometry from PD linked segment finish metadata — **not** `letter_face_area_m2`.
- **Perimeter ops** (`logo_return_forming`, `logo_return_bonding`): segment perimeter from linked segment — missing → `INTERNAL_GEOMETRY_MISSING`.
- **Piece ops** (`logo_led_install`, `logo_electrical_test`): segment LED module count — missing → blocker.
- **No minutes** in V1 — quantity × `internal_unit_cost` basis (m2/ml/piece), matching letters EIC model.

**Implementation blocked until GO:** NO (boundary mirrors approved material V1)

---

## DEC-LOPS-03 — V1 operation scope

**Problem:** Full `TPL-VOLUMETRIC-LOGO_v1` aggregate exposes ~10+ operations per segment (face, return, back, lighting, finish, mounting).

**Options:**
| Option | Description |
|---|---|
| A | Map **all** namespaced logo rows present in `bom.costable_operations` |
| B | Phase 1: artwork + face CNC only |
| C | Phase 1: artwork ops only |

**Recommended:** **Option A** — consume all BOM-present logo ops; let missing qty/rate produce explicit blockers/partial (consistent with material V1). No fabrication when finish partial omits ops from PA/BOM.

**Implementation blocked until GO:** NO

---

## DEC-LOPS-04 — Shared operation semantics

**Problem:** Could letters and logo share operations that double-count?

**Evidence:**
- PA `_dedupe_operations` key: `operation_code|source_template_code|component_ref|provenance` (composition service lines 85–101).
- Letters ops: `debitare_fata`, `modelare_cant`, etc. — parent template codes, non-namespaced refs.
- Logo ops: `logo_face_*`, `logo_return_*`, etc. — `TPL-VOLUMETRIC-LOGO_v1`, namespaced `comp_*::logo-stanga`.
- No shared `operation_code + component_ref` between letters and logo in composed aggregate.
- `logo_mounting_template_cut` vs letters `sablon_montaj_cnc` — **different codes**, separate EIC lines if both present.

**Recommended:** EIC consumes PA/BOM dedupe result as-is; **no second dedupe layer**. Filter to logo namespaced rows only for new path.

**Implementation blocked until GO:** NO

---

## DEC-LOPS-05 — Partial semantics

**Problem:** Incomplete logo operation truth when materials exist.

**Evidence:** Material V1 sets `status=partial` when `bom.bom_status == "partial"` or finish-partial warning (unless contamination).

**Recommended:** Logo ops missing (finish partial) → no fabricated operation lines; letter ops unchanged; EIC stays `partial`. Per-op missing rate/qty → blockers; partial status if other lines compute.

**Implementation blocked until GO:** NO

---

## Prior task decisions carried forward

- **DEC-EIC-03** (material): artwork area boundary — extends to artwork-owned **operations**.
- **DEC-EIC-04** (material task): logo **material** only was V1 scope — **this task closes operation debt** explicitly authorized by roadmap.

# WORKOS — TE2E-028B Formula Planning-Duration Authority Audit

**Date:** 2026-07-17  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `9761aa6` (`docs(pricing): close legacy pricing authority`)  
**Scope:** Audit + owner gates (approved 2026-07-17) — implementation follows in separate commit  
**Parent:** TE2E-028 remains **OPEN**  
**Protected:** TE2E-028A static minutes · commercial 7G isolation · legacy `/price` isolation · Wave 7 refs · fixture `972901`

### Owner gates applied (2026-07-17)

```text
TE2E-028B = UNPAUSE
FORMULA AUTHORITY = PRODUCT AGGREGATE
ZERO SEMANTICS = EXPLICIT ZERO ONLY
MISSING INPUT = NULL
SOURCE PRECEDENCE = CONTRACT RULE
PROOF SCOPE = LETTERS ONLY
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

Binding: Product System owns formula **definitions**; ProductAggregate **resolves/emits** minutes; Plan consumes; CostEngine/EIC excluded; no schema/migration/permanent seed by default.

---

## 1. Verdict

`TE2E_028B_OWNER_GATES_READY` → implementation closed as `TE2E_028B_FORMULA_DURATION_PASS` (see worklog + master STATUS).

---

## 2. Mini decision

**Why formula ops show zero/missing:** Letters BOM ops marked `formula_based` are seeded with `estimated_minutes: 0` as a **commercial-quantity placeholder**, not a computed duration. TE2E-028A correctly **rejects** `formula_based + 0` for Plan V2 → tasks get **`null`** + `PLANNING_MINUTES_SOURCE_REQUIRED`. True duration formulas (`perimeter_based_time`, `count_based_time`, …) exist in `formula_handlers` and are used by **EIC capacity hints**, not by Aggregate → Plan.

**Who should own the result:**  
- **Product System** owns reusable duration formula definitions / template timing contracts.  
- **ProductAggregate** should emit **resolved** operational minutes + provenance into the snapshot Plan already reads.  
- **ExecutionPlan** consumes only — does not invent product formulas.  
- **CostEngine / EIC** must not become Plan authority (commercial isolation + Plan forbid list).

**Narrow build recommended:** Option A — evaluate/write duration into Aggregate ops (freeze path), one Letters capacity-style op as proof; keep missing as **null**, never coerce.

---

## 3. Repository state

| Check | Result |
|--------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `9761aa6` — matches expected |
| Ports | FE `:3000` · BE `:8001` — up |
| TE2E-028A | Closed / UI verified — not reopened |
| Legacy `/price` | Isolated (410) — not reopened |
| Refs 8/9 · fixture 10 | Read-only verified |
| Commit | Owner approved — audit commit first, then implementation |

---

## 4. Formula inventory (Letters / `TPL-VOLUMETRIC-LETTERS_v2`)

Duration-capable handlers in `formula_handlers.py`: `cnc_time_from_path`, `led_assembly_time`, `perimeter_based_time`, `count_based_time`.

| Formula/field | Product/template | Inputs | Current owner | Evaluated now? | Output | Used downstream? | Status |
|---------------|------------------|--------|---------------|---------------:|--------|-----------------:|--------|
| Static `qc_letters` = 15 | Letters v2 | none | Product System seed → Aggregate | Yes (copy) | minutes | Plan + Post-Job | `ACTIVE_VALID` |
| Static `assembly_letters` = 60 | Letters v2 | none | Product System seed → Aggregate | Yes | minutes | Plan + Post-Job | `ACTIVE_VALID` |
| `_op_formula` seed `estimated_minutes=0` | All build4 formula ops | n/a | Product System seed | Stored only | placeholder 0 | Rejected by Plan | `PLACEHOLDER_ZERO` |
| Letters `face_cnc_cut` → `perimeter_pass_linear_meter` | Letters | perimeter ml | PS / CostEngine qty | CostEngine qty yes; Plan no | **ml** not minutes | Commercial/legacy cost | `PLACEHOLDER_ZERO` (planning) |
| Letters other BOM ops (`letter_perimeter`, `led_module_count`, …) | Letters | qty/m²/count | PS / CostEngine | CostEngine qty | non-time units | Commercial | `PLACEHOLDER_ZERO` (planning) |
| Banner/Plexi/etc. ops with `perimeter_based_time` / `area_based_time` | Non-Letters templates | perimeter/area + speed params in seed | PS seed + formula_handlers | **Not** on Aggregate→Plan | would be minutes | Plan rejects seed 0 | `DEFINED_NOT_CALLED` |
| EIC `perimeter_based_time` / `count_based_time` capacity | Letters/ACM EIC | geometry + rates | EIC + formula_handlers | Yes in EIC only | minutes | Capacity hints only | `DEFINED_NOT_CALLED` (for Plan) |
| `cnc_time_from_path` / `led_assembly_time` | Registry | path/LED params | formula_handlers | Not on Plan path | minutes | — | `DEFINED_NOT_CALLED` |
| Aggregate op map | All | copies `formula_id` + minutes; uses `formula_params` only for `non_priced` | ProductAggregate | Yes (copy) | no duration eval | Plan | `ACTIVE_PARTIAL` |

**Letters proof note:** Letters formula ops are **quantity/commercial formulas**, not duration formulas. A TE2E-028B Letters proof must **add or map** a real duration formula (e.g. `perimeter_based_time`) onto an op — not treat `perimeter_pass_linear_meter` as minutes.

Runtime fixture `972901` / plan `10` (RO): **12** tasks · **11** null planning minutes · **1** present (`Control calitate` = 15, source Aggregate ops).

---

## 5. Current authority map

```text
Product System (template ops + formula_id + seed minutes)
    ↓ copy (no duration eval)
ProductAggregate.operations (formula_id kept; formula_params dropped after non_priced check; minutes copied as seed)
    ↓ TE2E-028A resolve (static keep; formula_based+0 → null)
Plan V2 preview / persist / materialize
    ↓
Post-Job planned_minutes (consumer)

PARALLEL (not Plan authority):
  formula_handlers ← CostEngine (qty/price; minutes coerced 0 unless per_hour)
  formula_handlers ← EIC capacity hints (true minutes; ignored by Plan)
```

| System | Role today | Should own formula *duration*? |
|--------|------------|--------------------------------|
| Product System | Defines formula ids + seed placeholders/static | **Yes — definitions / contracts** |
| ProductDefinition | Operation roles only (no minutes) | No (facts/inputs only) |
| ProductAggregate | Carries template minutes; drops `formula_params` | **Yes — resolve/emit minutes** |
| Plan V2 | Consumes Aggregate minutes | Consume only |
| CostEngine | Qty × rate (legacy internal/commercial sim) | **No** |
| EIC | Capacity minute hints | Parallel estimator — not Plan SoT |
| Frontend | Display | **No** |

---

## 6. Zero and missing semantics

| Case | Current behavior | Classification |
|------|------------------|---------------|
| Seed `formula_based` + `estimated_minutes=0` | Template/Aggregate store `0` | **PLACEHOLDER_ZERO** — not real duration |
| Plan after TE2E-028A | Becomes `null` + warning | **Missing duration source** (correct) |
| Static configured `0` | Would pass resolver as explicit zero | **Explicit real zero** (rare; allowed) |
| CostEngine non-hourly ops | Op detail `estimated_minutes=0.0` | **Coercion / unused field** |
| Pre-TE2E-028A materialize null→0 | Fixed | Historical **coercion** |
| Formula never called for Plan | — | Not “evaluation failure” on Plan path |

**Recommendation for TE2E-028B:**

- Missing / unevaluated → keep **`null`** (not zero).  
- Explicit calculated zero → only when a duration formula returns `0` with provenance.  
- Placeholder seed `formula_based+0` must never become Plan `0`.

---

## 7. Active flow trace (`face_cnc_cut`)

| Stage | Formula / value | Provenance | Null/zero |
|-------|-----------------|------------|-----------|
| Template | `perimeter_pass_linear_meter`, seed minutes **0**, `formula_based` | Product System seed | PLACEHOLDER_ZERO |
| ProductDefinition | Role only | — | no minutes |
| ProductAggregate | Copies `0` + `formula_based`; drops params | Aggregate map | PLACEHOLDER_ZERO |
| Plan preview | `resolve_planning_minutes_from_aggregate_op` → `(None, None)` | — | **null** + warning |
| Persist / materialize | `estimated_time_minutes: null` | — | null kept |
| Post-Job | planned `presence=missing` | — | missing ≠ zero |
| CostEngine (parallel) | Formula → **linear meters** × rate | commercial/qty | minutes field coerced 0 |

Evidence functions:

- `seed_build4_templates._op_formula` / `_op_static`
- `product_aggregate_service._operations_from_rows`
- `execution_plan_v2_preview_service.resolve_planning_minutes_from_aggregate_op`
- `execution_plan_task_parser` (null preserve)
- `post_job_truth_service` (planned presence)

---

## 8. Duplicate-engine result

| Duration logic | Active caller | Same purpose? | Conflicting result? | Recommendation |
|----------------|---------------|--------------:|--------------------:|----------------|
| Aggregate static → Plan | Plan V2 | Operational plan | No | Keep authority |
| Seed formula_based+0 | Template | Placeholder only | Plan nulls them | Do not treat as duration |
| CostEngine + formula_handlers | `/simulate-cost`, legacy (retired `/price`) | Qty/cost | Minutes usually 0 | Keep off Plan |
| EIC capacity + `perimeter_based_time` | EIC preview | Capacity | Parallel minutes | May **inspire** Aggregate rules; do not import EIC into Plan |
| Frontend template calibration copy | UI | Display | No | Non-authority |

**Do not create another formula engine.** Prefer Aggregate emission + shared `formula_handlers` math if needed.

---

## 9. Commercial isolation check

| Invariant | Status |
|-----------|--------|
| 7G does not accept minutes | Intact |
| Legacy `/price` isolated | Intact |
| Plan ignores CostEngine/EIC pricing sources | Intact |
| Formula duration work must not write Quote/Order commercial | Required for any TE2E-028B implementation |

**Commercial isolation remains proven** if Option A stays Aggregate → Plan only.

---

## 10. Schema / API impact

| Need | Required? |
|------|-----------|
| Mapping / JSON snapshot fields | Likely sufficient |
| Carry `formula_params` on Aggregate ops | Probable (currently dropped) |
| New `planning_minutes_source` constant | Probable if not static |
| Alembic / migration | **Not required** for bounded JSON-contract fix |
| Permanent seed / template data update | Likely for duration formula params on proof op |
| Schema change / migration | Mark **OWNER_DECISION_REQUIRED** only if DB columns forced — not recommended |

---

## 11. Candidate options

### Option A — Formula evaluation in ProductAggregate (recommended)

Resolve duration into Aggregate op minutes (+ provenance) at build/freeze; Plan keeps TE2E-028A resolver.

| Dimension | Assessment |
|-----------|------------|
| Authority fit | Best match to current Plan source |
| Touch | Aggregate service, maybe freeze compose, source constant, Letters proof rule |
| Risk | Must not treat qty formulas as minutes |
| Schema | JSON/Pydantic; no migration preferred |
| Commercial risk | Low if CostEngine unused |
| Testability | High (mirror TE2E-028A differential) |

### Option B — Resolve in ProductDefinition

| Dimension | Assessment |
|-----------|------------|
| Authority fit | Poor — PD has no time fields today |
| Risk | Widens Step-6 contract |
| Recommendation | **Reject for now** |

### Option C — Reuse EIC / CostEngine estimator

| Dimension | Assessment |
|-----------|------------|
| Authority fit | Conflicts Plan forbid list / commercial boundary |
| Risk | Parallel engine + isolation regression |
| Recommendation | **Reject as Plan authority**; EIC rules may be **copied/adapted** into Aggregate duration rules under Product System ownership |

---

## 12. Recommended coherent build

**TE2E-028B implementation (after GO):**

1. Product System / Aggregate: for **one** Letters op, attach a **duration** formula (e.g. `perimeter_based_time` pattern aligned with EIC `face_cnc_capacity` inputs — not `perimeter_pass_linear_meter` qty).  
2. Evaluate into Aggregate `estimated_minutes` with provenance distinct from static seed.  
3. Plan V2: accept non-placeholder formula results (extend resolver: `formula_based` + **resolved** minutes allowed; keep rejecting `formula_based+0`).  
4. Post-Job: display planned minutes + source.  
5. Assert commercial totals unchanged; refs 8/9/10 RO; new isolated fixture.  
6. No CostEngine commercial coupling; no schema migration.

**Proof scope:** Letters only — one formula-duration op (+ keep static qc/assembly regression).

---

## 13. Test and runtime proof plan

### Focused tests (future)

1. Formula with all inputs → non-zero minutes + provenance  
2. Missing input → **null**, not zero  
3. Explicit calculated zero remains zero with source  
4. Static vs formula precedence (contract rule)  
5. Preview → persist → materialize → Post-Job consistency  
6. Commercial total invariant  
7. No CostEngine import on Plan/Aggregate planning path  
8. Refs untouched  
9. TE2E-028A static path remains green  

### Runtime proof scenario (future — do not create now)

| Field | Value |
|-------|--------|
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Operation | Face CNC (or equivalent) with **duration** formula |
| Inputs | letter perimeter / speed params from ProductDefinition / workspace facts |
| Expected | Non-zero planned minutes, source Aggregate formula-resolved |
| Display | Plan task + Post-Job Plan vs execuție |
| Commercial | Unchanged vs baseline |
| Retention | NEW isolated LOCAL_TEST_FIXTURE — not Wave 7 |

---

## 14. Modules impact (evaluate only)

Expected after a future GO: **limitation / evidence update** on ProductAggregate + ExecutionPlan (formula duration provenance). **No new system node.**

---

## 15. Governance impact (evaluate only)

Boundaries remain:

- Product System → reusable timing/formula definitions  
- ProductDefinition → product facts / selections  
- ProductAggregate → resolved operational truth  
- ExecutionPlan → consume planned truth  
- Reality / Post-Job → actual / analysis  
- Pricing → separate  

**Conflict today:** EIC capacity minutes exist as a parallel duration evaluator — must stay non-Plan SoT unless Aggregate absorbs equivalent rules under PS ownership.

---

## 16. Files created

| Path | Role |
|------|------|
| `docs/audits/2026-07-17_te2e_028b_formula_planning_duration_authority_audit.md` | This audit |
| `docs/worklog/realignment/2026-07-17_te2e_028b_formula_planning_duration_authority_audit.md` | Worklog |

No application code changes.

---

## 17. Commit status

`NO COMMIT — WAITING FOR OWNER REVIEW`

---

## 18. Owner decision pack

```text
TE2E-028B = UNPAUSE
FORMULA AUTHORITY = PRODUCT AGGREGATE
ZERO SEMANTICS = EXPLICIT ZERO ONLY
MISSING INPUT = NULL
SOURCE PRECEDENCE = CONTRACT RULE
PROOF SCOPE = LETTERS ONLY
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

### Plain-language recommendations

| Gate | Recommendation | Why |
|------|----------------|-----|
| TE2E-028B | **UNPAUSE** | Authority and zero semantics are clear enough for a bounded build |
| FORMULA AUTHORITY | **PRODUCT AGGREGATE** (definitions in Product System) | Matches TE2E-028A Plan source; PD lacks minutes; CostEngine/EIC must not own Plan |
| ZERO SEMANTICS | **EXPLICIT ZERO ONLY** | Placeholder seed `0` is not duration |
| MISSING INPUT | **NULL** | Keep TE2E-028A honesty |
| SOURCE PRECEDENCE | **CONTRACT RULE** | Static configured minutes when present; formula-resolved when evaluated; never invent; reject formula_based+0 |
| PROOF SCOPE | **LETTERS ONLY** | One duration op; static ops remain regression |
| REFERENCE DATA | **NEW TEST DATA** | Do not mutate 8/9/10 |
| AUDIT COMMIT | **DA** | After owner accepts pack |
| IMPLEMENTATION | **GO** only after audit commit + GO confirmation |

**Note:** `FORMULA AUTHORITY = PRODUCT AGGREGATE` means Aggregate **emits resolved minutes**. Product System still owns formula **definitions**. If owner prefers the pack enum literally as Product System only, treat Aggregate as the **resolver/emitter** under PS contracts.

Alternate pack wording if owner wants dual label:

```text
FORMULA AUTHORITY = PRODUCT SYSTEM
```

with Aggregate as mandatory emitter — still Option A.

---

## 19. Metodă

1. Locked HEAD `9761aa6`; did not reopen commercial or TE2E-028A.  
2. Separated **quantity formulas** (commercial CostEngine) from **duration formulas** (EIC / handlers).  
3. Prioritized **current Plan authority** (Aggregate minutes) over ideal redesign.  
4. Classified zero vs missing vs placeholder via TE2E-028A resolver + seeds.  
5. Rejected CostEngine reuse for Plan despite existing time math.  
6. **No implementation** — audit only.

---

## 20. Next safe step

**Wait for owner review.**  
Do not implement TE2E-028B automatically.  
Do not start Stock G3 / labor $ / lifecycle / template breadth.

---

## Roadmap awareness checkpoint

| Item | Score / note |
|------|----------------|
| Roadmap awareness | **9/10** |
| Current position | Post TE2E-028A + commercial isolation + legacy `/price` isolation; TE2E-028B audit ready |
| Cat sunt in directia stabilita | **~90%** on operational planning spine; formula duration still open residual |
| Dead pieces | Do not revive legacy `/price` or null→0 coercion |
| Forbidden scope | No pricing / schema / Stock G3 / labor $ / 028A reopen |
| Parallel-duration-engine | EIC capacity vs Plan Aggregate — conflict noted |
| Commercial-isolation integrity | Intact |
| Wave 7 / UTF-8 / Control Center / UI-TRUTH-01C / TE2E-028A / legacy-pricing | Intact |

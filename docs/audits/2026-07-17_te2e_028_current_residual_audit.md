# TE2E-028 — Current residual audit (present truth)

**Date:** 2026-07-17  
**Mode:** Planning / owner gates only — **no implementation**  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `c6a4c14a659e6e4be892f164cf12e86a0fe93326`  
**Remote:** `https://github.com/office952/workos-vscode.git`  
**Runtime:** frontend `http://127.0.0.1:3000` · backend `http://127.0.0.1:8001`  
**Verdict:** `TE2E_028_OWNER_GATES_READY`  
**Commit policy:** Audit approved for commit; implementation GO under narrow TE2E-028A

---

## Owner decision (2026-07-17 — unpause)

```text
TE2E-028 = UNPAUSE
BUILD = RECONCILIATION
MISSING ACTUAL = KEEP EXPLICIT
TASK LIFECYCLE = DEFER
VARIANCE = CURRENT MODEL
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

**Binding interpretation:** solve planning-minute source integrity only (TE2E-028A). Preserve Post-Job classification, variance model, and explicit `missing_actual`. Do not mutate plans `8`/`9` or orders `92402`/`92403`. Proof uses **new isolated test data**.

**Plan V2 preview clue:** preview may null `planning_minutes_source` (`execution_plan_v2_preview_service.py`). This is an investigation clue — **not yet proven as the sole root cause**. Persistence, task materialization, and Post-Job consumption must be traced before editing.

**Implementation scope:** compile/projection of planned minutes + provenance where contract supports it; tests; new labeled test data; Control Center evidence update if proven.  
**Exclusions:** stock G3 · labor money · lifecycle enforcement · template breadth · frozen reference mutation · arbitrary minute fallbacks · commercial pricing · schema/migration/permanent seed without separate GO.

---

## 1. Canonical definition

| Field | Current truth |
|-------|----------------|
| **ID** | TE2E-028 |
| **Canonical title** | Same-scenario / W7-T02 remaining limitations |
| **Class** | Accepted debt (P2, cross-cutting) |
| **Registry** | `docs/master/workos-e2e/WORKOS_E2E_ISSUE_REGISTRY.md` — status **open** |
| **Upstream** | TE2E-013 **closed** (`SAME_SCENARIO_REQUEST_TO_POST_JOB_PROVEN_V1`) |
| **Owner decision** | D-020 — Wave 7 OWNER_ACCEPTED; TE2E-028 residuals remain open accepted limitations |
| **Original objective** | Consolidate Wave 7 / same-scenario **accepted limitations** that were **not** required for W7-T01/T02 DoD, so they are not silently closed when Wave 7 signed |
| **Current status** | **OPEN** — not resolved by UI-TRUTH-01B/01C or Control Center |
| **DoD (existing)** | None as a single implementation DoD — issue is a **bucket of accepted residuals** after Wave 7 acceptance |
| **Missing DoD** | Owner must choose which residual(s) become a coherent build with explicit DoD |
| **Explicit exclusions (Wave 7)** | Labor money; forced stock when ineligible (G3); universal template proof; treating deterministic fixture as organic customer proof |
| **Scope conflict** | **None** — registry, W7-T03 checklist, D-020, STATUS, and W7-T02 worklog agree on the same five residuals |

### What TE2E-028 is today

TE2E-028 is **not** “Post-Job reconciliation unfinished.” W7-T02 already delivered matched / missing_actual / variance breadth on reference orders. TE2E-028 is the **remaining accepted debt** around planning-minute **source** quality, stock eligibility, labor money exclusion, fixture qualification, and Letters-only template breadth.

---

## 2. Accepted Wave 7 limitations (exact five)

From W7-T03 checklist + D-020 + issue registry:

| # | Residual | Wave 7 treatment |
|---|----------|------------------|
| R1 | Planning-minute **source** often 0 (`PLANNING_MINUTES_SOURCE_REQUIRED`) | PARTIAL_ACCEPTED — mechanics work; source incomplete |
| R2 | Stock G3 not forced when ineligible | PARTIAL_ACCEPTED — deferred |
| R3 | Labor $ excluded from profitability | PARTIAL_ACCEPTED — keep excluded |
| R4 | Deterministic fixture origin (`DETERMINISTIC_LOCAL_SCENARIO`) | PARTIAL_ACCEPTED — qualification, not customer-origin |
| R5 | Limited Letters template breadth | PARTIAL_ACCEPTED — not universal template proof |

---

## 3. Closed work (do not reopen)

Wave 7 · W7-T01 · W7-T02 · W7-T03 · UI-TRUTH-01B · UI-TRUTH-01C · Current Truth Control Center V1 · UTF-8 / G13 · ProductAggregate `task_contract` correction · frozen local snapshot repair.

Reference data **LOCAL_REFERENCE_DATA — DO NOT MUTATE**:

| Scenario | IDs |
|----------|-----|
| Build 1 | IR-BUILD1-1784237119 · WS `e1b8d1e8-0197-4723-882a-037c41c64d35` · Q3 · QSN2-2026-0002 · order `92402` · plan `8` · tasks 18 · commercial `3549.1286` |
| W7-T02 variance | IR-W7T02-1784238040 · order `92403` · plan `9` · variance `0 → 75` min |

---

## 4. Present-truth classification

| Item | Previous status | Current evidence | Classification | Action |
|------|-----------------|------------------|----------------|--------|
| TE2E-013 same-scenario spine | Closed | Lineage live: WS ready_for_quote_preview · quote 3 · order 92402 locked · plan 8 · Post-Job 200 | `RESOLVED_CURRENT` / issue closed | Keep closed; do not reopen as TE2E-028 |
| W7-T02 missing_actual honesty | Proven | Live 92402: `missing_actual_count=17`, sample `actual_minutes.presence=not_captured` (not 0); UI „fără actual” / „neînregistrat” | `RESOLVED_CURRENT` | Keep; regression-protect only |
| W7-T02 variance semantics | Proven | Live 92403: variance=1, planned 0 → actual 75, Δ 75; `write_back_performed=false` | `RESOLVED_CURRENT` | Keep current model unless owner reworks planning source |
| W7-T02 operations UI | Proven | `/execution/92402` + `/execution/92403` show **Plan vs execuție** chips | `RESOLVED_CURRENT` | Keep |
| Post-Job read-only / no commercial write-back | Proven | Both orders `write_back_performed=false`; totals still `3549.1286` | `RESOLVED_CURRENT` | Boundary — do not break |
| R1 Planning-minute source zeros | Accepted open | Plan 92402: `total_estimated_time_minutes=0.0`; all 18 ops `estimated_time_minutes=0.0`; Post-Job marks planned minutes `presence=present` value 0 | `OPEN_CURRENT` | **Primary residual for a coherent build** |
| R2 Stock G3 deferred | Accepted open | `materials.completeness=not_captured`; missing `material_deduction_missing`; order readiness `inventory_mutated=false` | `OPEN_CURRENT` | KEEP EXPLICIT / DEFER unless inventory GO |
| R3 Labor $ excluded | Accepted open | `labor.monetary_cost.presence=excluded` · `labor_money_out_of_scope_g2` | `OPEN_CURRENT` (intentional) | KEEP EXPLICIT — not a defect |
| R4 Deterministic fixture | Accepted open | Workspace title `BUILD1-LETTERS-…`; qualification still Letters fixture clone | `OPEN_CURRENT` | Qualification debt; fixture replacement later |
| R5 Letters-only breadth | Accepted open | Template `TPL-VOLUMETRIC-LETTERS_v2` only on reference spine | `OPEN_CURRENT` | Separate expansion program |
| Quantity produced not_captured | W7 side note | Ops quantity fields `not_captured` | `PARTIAL_CURRENT` / adjacent | Fold into capture/stock lane if owner expands |
| TE2E-021 mock „N critical” | Separate open UX | UI-TRUTH-01C hid mock critical unless mock mode | `OUT_OF_SCOPE` / `DUPLICATE` of shell truth lane | Not TE2E-028 |
| PostJobTruth EN chrome leftovers | UX debt | Page still shows some EN strings („POST-JOB TRUTH”, etc.) alongside RO Plan vs execuție | `OUT_OF_SCOPE` | Not in TE2E-028 five; optional UX later |
| Control Center evidence flags for W7 | Historical category | `stillCurrentRuntime: false` on same-scenario / W7-T02 packs while API still serves 92402/92403 | `PARTIAL_CURRENT` (docs freshness) | `EVIDENCE UPDATE` only if owner wants flags refreshed |

### Classification detail (required fields)

#### R1 — Planning-minute source

- **Code:** Plan V2 preview still nulls minutes / source (`estimated_minutes=None`, `planning_minutes_source=None`, warning `PLANNING_MINUTES_SOURCE_REQUIRED` in `execution_plan_v2_preview_service.py`). Persisted plan `92402` materializes `estimated_time_minutes=0.0` on all ops. `post_job_truth_service` then treats those zeros as `presence=present` (not `missing`).
- **Runtime:** plan `8` / order `92402` — 18/18 zeros; labor `planned_minutes_total` presence `zero`.
- **Tests:** `test_execution_plan_v2_preview.py` asserts partial missing planning minutes without fake values; reference scenario still ships zeros.
- **Limitation:** Variance against planned 0 is mathematically valid but **planned truth incomplete**.
- **Action:** Candidate build = fix/source planning minutes on Letters path without mutating frozen commercial snapshots.

#### R2 — Stock G3

- **Code / runtime:** materials not captured; no forced deduction when ineligible.
- **Tests:** Post-Job materials `not_captured` honesty covered.
- **Action:** Inventory eligibility GO required — not silent force.

#### R3 — Labor $

- **Code / runtime:** explicit `excluded` with G2 note.
- **Action:** Keep excluded unless HR rate authority GO.

#### R4 — Fixture origin

- **Runtime:** continuous local Letters lineage still present; proves continuity, not organic capture.
- **Action:** Replace with automated/customer-origin fixture later; do not mutate retained IDs.

#### R5 — Template breadth

- **Runtime:** Letters only.
- **Action:** Separate template expansion; not one TE2E-028 patch.

---

## 5. Same-scenario continuity (read-only)

| Stage | ID / check | Result |
|-------|------------|--------|
| Intake V6 workspace | `e1b8d1e8-0197-4723-882a-037c41c64d35` → 200 · `TPL-VOLUMETRIC-LETTERS_v2` · `ready_for_quote_preview` | PASS |
| Quote | `3` accepted | PASS |
| Order | `92402` locked · total `3549.1286` · `quote_snapshot_v2_id=2` in readiness | PASS |
| ExecutionPlan | plan id `8` · 18 operational tasks | PASS |
| Execution Reality | GET reality 200 (thin); one completed path via sessions for `vector_prep` | PASS |
| Post-Job | summary matched=1 · missing_actual=17 · variance=0 | PASS |
| Parallel W7-T02 | order `92403` · plan `9` · variance=1 (0→75) · total unchanged | PASS |

**Conclusion:** One current scenario can still be followed on the active spine **without switching unrelated IDs**. Continuity is **current**, not historical-only.

---

## 6. Planned versus actual audit

| Aspect | Current truth |
|--------|----------------|
| Planned tasks | 18 ops on plans 8/9 |
| Actual completion | Build 1: 1 task done (`vector_prep`); 17 never started |
| Actual minutes | Done task: presence `zero` (92402) or `75` present (92403); missing: `not_captured` |
| Post-Job classes | matched / missing_actual / variance — working |
| Incomplete states | Planned-not-started → `missing_actual`; started/incomplete → `partial` (classifier); completed without duration → `zero` actual (distinct from missing) |
| Closed without recon | Not observed as silent healthy close — recon remains derived |

---

## 7. Missing actual and variance semantics

| Rule | Current |
|------|---------|
| Missing ≠ zero | **Holds** — missing uses `not_captured` / UI „neînregistrat” / „fără actual” |
| Variance uses planned + actual | **Holds** — Δ = actual − planned |
| Distinguishes missing from zero | **Holds** for actuals |
| No commercial write-back | **Holds** |
| Read-only Post-Job | **Holds** |
| Caveat | Planned minutes are often **present zeros**, so variance can be „actual − 0” — honest math, weak planned source (R1) |

---

## 8. Frozen-truth boundary result

| Boundary | Result |
|----------|--------|
| Quote / Order commercial total | Unchanged `3549.1286` on 92402/92403 |
| Order locked | Yes |
| ExecutionPlan identity | plan 8 / 9 retained |
| Post-Job write-back | false |
| Any TE2E-028 fix requiring rewrite of frozen snapshots | **Forbidden without OWNER_DECISION_REQUIRED** |
| Forced stock / labor money | **OWNER_DECISION_REQUIRED** |

---

## 9. UI verification map (owner-usable)

| Residual | URL | Page | Section/tab | Test record | Current visible result | Expected (if residual kept) |
|----------|-----|------|-------------|-------------|------------------------|-----------------------------|
| R1 planning minutes | `http://127.0.0.1:3000/execution/92402` | Execuție | Plan vs execuție + task PLANIFICAT | order `92402` · plan `8` | Planned column **0 min** on all ops; total planned 0 | Keep explicit zeros **or** non-zero after planning-source build |
| Missing actual | same | Execuție | Plan vs execuție | `92402` | potrivit: 1 · fără actual: 17 | Same unless new actuals (do not mutate) |
| Variance | `http://127.0.0.1:3000/execution/92403` | Execuție | Plan vs execuție | `92403` · plan `9` | varianță: 1 · vector_prep 0→75 | Same |
| Labor $ | `/execution/92402` | Post-Job Truth | Missing / profitability | `92402` | labor money excluded / materials missing | Keep excluded |
| Stock G3 | `/execution/92402` | Material actuals | MATERIAL ACTUALS (0 DEDUCTED) | `92402` | No stock deduction | Keep deferred unless inventory GO |
| Modules note | `http://127.0.0.1:3000/modules` | Harta sistemelor | Surse și dovezi / Post-Job node | Control Center | TE2E-028 named as residual; W7 evidence under dovezi | Evidence refresh optional |
| Governance | `http://127.0.0.1:3000/governance` | Guvernanță | Ownership / boundaries | G13 | No TE2E-028 policy change required | No policy change |

---

## 10. Runtime and test coverage

| Area | Unit / integration | Live runtime (this audit) | Gap |
|------|--------------------|---------------------------|-----|
| Post-Job classification | `backend/tests/test_post_job_truth.py` (12) | 92402/92403 summaries match W7 | — |
| Panel honesty | `PostJobTruthPanel.test.tsx` (4) | Live Plan vs execuție | Some EN chrome not matrix-gated |
| Planning-minute source | Preview tests for missing minutes | Reference plans all zero | **No Letters source→non-zero proof** |
| Stock force G3 | Honesty tests only | not_captured | No eligibility force |
| Labor money | Explicit excluded in service/tests | excluded | Intentional |
| Same-scenario lineage | Evidence packs + live IDs | Continuity PASS | IR search API path unused; workspace/order path sufficient |

---

## 11. Candidate builds (≤3)

| Candidate | Value | Systems | Risk | Recommendation |
|-----------|-------|---------|------|----------------|
| **A — Planning-minute source integrity** | Makes planned truth meaningful for variance/recon | ProductAggregate / ops contracts → ExecutionPlan minutes → Post-Job consume | Backend service + runtime behavior; **no** frozen commercial rewrite; schema only if minutes field missing (it exists) | **RECOMMENDED** |
| **B — Runtime execution closure** | More tasks leave missing_actual via real session lifecycle | Execution Reality sessions / operator close | Runtime behavior; must use **NEW TEST DATA** (not 92402/92403 mutate) | Secondary — after A or separate GO |
| **C — Combined residual mega-build** | A+B+stock | Cross inventory + plan + reality | High; stock/labor gates; easy scope blow | **Not recommended** as one ship |

### Option A detail (recommended)

- **Problem solved:** R1 planning-minute source incompleteness (zeros presented as planned truth).
- **Systems touched:** ExecutionPlan compile/materialization path; possibly template ops estimated minutes; Post-Job remains consumer (no new recon engine).
- **Visible value:** Non-zero planned minutes where contracts provide them; variance becomes comparable planned vs actual.
- **Risk:** Medium backend; must not rewrite Quote/Order snapshots; must not invent minutes when source absent (prefer `missing` over fake non-zero).
- **DB/schema:** Prefer no migration; use existing `estimated_time_minutes`.
- **Owner gates:** PLANNING SOURCE = GO; STOCK/LABOR = DEFER/KEEP; REFERENCE DATA = READ ONLY; proof on **new** scenario or RO probes.
- **Tests:** plan minutes present when source exists; missing when absent; Post-Job variance regression; freeze protection; no write-back.
- **Runtime proof:** new order/plan OR preview endpoint; never mutate 92402/92403.
- **Exclusions:** stock force, labor $, template expansion, fixture replacement, FLEX-02, UI-TRUTH.

### Option B detail

- Focus task lifecycle / actual capture completeness.
- Does **not** fix planned zeros.
- Requires NEW TEST DATA.

### Option C detail

- Only if owner explicitly wants multi-system residual closure.
- Stock G3 alone requires inventory ownership GO → often `OWNER_DECISION_REQUIRED`.

---

## 12. Implementation risk classification (recommended A)

| Class | Applies? |
|-------|----------|
| Frontend-only | No (optional label polish later) |
| Backend service | Yes |
| API contract | Possibly additive fields/notes only — avoid semantic break |
| Schema/data model | Prefer no |
| Migration | No |
| Frozen truth | **Must not mutate** |
| Runtime behavior | Yes (plan minutes population) |
| Documentation/evidence | Yes (after GO) |

Schema / migration / frozen truth / pricing → separate owner GO (not in recommended A).

---

## 13. Test plan (recommended A)

1. Same-scenario lineage RO regression on 92402/92403 (no writes).
2. When ops contract supplies minutes → plan task `estimated_time_minutes` non-zero.
3. When source absent → presence missing/partial warning — **not** silent fake minutes.
4. Post-Job: missing actual still `not_captured` (not 0).
5. Variance uses current planned + actual.
6. Frozen snapshot / order total unchanged.
7. `write_back_performed=false`.
8. Operator-visible planned minutes on `/execution/:id` Plan vs execuție.
9. Reference record preservation checks.

---

## 14. Runtime plan (post-build; audit was RO only)

| Check | Endpoint / route | ID | Current | Post-build (A) | Mutation |
|-------|------------------|----|---------|----------------|----------|
| Order freeze | GET `/api/v1/entities/orders/92402` | 92402 | total 3549.1286 locked | unchanged | none |
| Plan minutes | GET `/api/v1/execution/plan/92402` | plan 8 | all 0.0 | **unchanged** (reference) | none |
| Post-Job A/B | GET `/api/v1/execution/92402/post-job-truth` | 92402 | m1 / miss17 / v0 | unchanged | none |
| Post-Job C | GET `/api/v1/execution/92403/post-job-truth` | 92403 | v1 · 0→75 | unchanged | none |
| New proof | new order/plan after GO | TBD | n/a | non-zero planned where sourced | create new only |
| UI | `/execution/{new}` | TBD | n/a | planned minutes visible | none on reference |

---

## 15. Modules / Governance impact

| Surface | Expected impact |
|---------|-----------------|
| `/modules` | **EVIDENCE UPDATE** (optional): mark W7 packs still runtime-verifiable; TE2E-028 residual text already present on Post-Job node |
| `/modules` system/handoff statuses | **NO IMPACT** unless planning-source build later changes Post-Job limitation wording |
| `/governance` | **NO IMPACT** / no policy change for audit; stock/labor expansion would be **BOUNDARY CHANGE — OWNER GATE** |

---

## 16. Owner decision pack (exact)

```text
TE2E-028 = UNPAUSE / KEEP OPEN / STOP
BUILD = RECONCILIATION / RUNTIME CLOSURE / COMBINED
MISSING ACTUAL = FIX / KEEP EXPLICIT / DEFER
TASK LIFECYCLE = ENFORCE / REPORT ONLY / DEFER
VARIANCE = CURRENT MODEL / REWORK / DEFER
REFERENCE DATA = READ ONLY / NEW TEST DATA
AUDIT COMMIT = DA / NU
IMPLEMENTATION = GO / STOP
```

### Auditor recommendation (not owner decision)

```text
TE2E-028 = KEEP OPEN
BUILD = RECONCILIATION   # narrow: planning-minute source integrity (Option A)
MISSING ACTUAL = KEEP EXPLICIT   # already honest; do not reopen W7-T02
TASK LIFECYCLE = DEFER           # Option B later
VARIANCE = CURRENT MODEL         # until planning source improves
REFERENCE DATA = READ ONLY
AUDIT COMMIT = DA                # planning docs only, if owner wants
IMPLEMENTATION = STOP            # until owner GO
```

---

## 17. Files for this audit

| File | Role |
|------|------|
| `docs/audits/2026-07-17_te2e_028_current_residual_audit.md` | This audit |
| `docs/worklog/realignment/2026-07-17_te2e_028_current_residual_audit.md` | Worklog |

No application code changed.

---

## 18. Next safe step

Wait for owner decision pack. Do **not** implement TE2E-028 automatically. Do not start FLEX-02 or further UI-TRUTH from this audit.

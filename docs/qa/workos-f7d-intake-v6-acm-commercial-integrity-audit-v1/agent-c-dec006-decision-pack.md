# Agent C — DEC-006 Decision Pack (Planning Minutes Source)

**Status:** READY_FOR_OWNER_RECONFIRMATION · **READ-ONLY** (no implementation)  
**Decision ID:** DEC-006 — authoritative source for `estimated_minutes` / `planning_minutes_source`  
**Fixture evidence:** `880811`/22 and `973019`/21 — all operational tasks `estimated_minutes=null` + `PLANNING_MINUTES_SOURCE_MISSING` (F7C) / historically `PLANNING_MINUTES_SOURCE_REQUIRED` (plan preview)  
**Prior record:** Route doc marks DEC-006 **A — RECORDED (null + warn)** short-term; production scheduling still blocked  
**Related code (evidence only):** `planning_duration_contract.py` (TE2E-028B / Letters `vector_prep` formula only), `resolve_planning_minutes_from_aggregate_op`, dossier `time_assumptions_json`, Machines boundary doc §5 “Estimated time hints”

---

## 1. Decision question

What is the **authoritative, freezeable** source for planning minutes on planned/operational tasks — and what happens when it is missing?

Constraints already locked by architecture:

- Minutes are **operational / capacity** truth — **never** commercial client price input.
- No silent zeros; no invent from rates / salary / CostEngine lei/h.
- Null + explicit warning is acceptable for audit / dry / F7C readiness (capacity warning ≠ commercial blocker).
- Production scheduling GO requires a non-null policy path (route risk #4 HIGH).

---

## 2. Options A–E (evaluate)

| ID | Name | One-line |
|----|------|----------|
| **A** | Null + warning | Keep null; emit warning; no invent |
| **B** | Dossier time assumptions | Use approved `time_assumptions_json` / task-rule planning minutes when populated |
| **C** | Machine / capacity registry | Derive minutes from machine rates, capacity formulas, or utilaje metadata |
| **D** | Planner manual only | Null until human planner enters post-preview / post-materialize |
| **E** | Hybrid (recommended) | Ordered provenance chain with mandatory source stamp + A as terminal fallback |

---

## 3. Comparison matrix

| Dimension | **A** Null + warn | **B** Dossier time | **C** Machine registry | **D** Planner manual | **E** Hybrid |
|-----------|-------------------|--------------------|------------------------|----------------------|--------------|
| **Owner of truth** | “No source” honesty | Product Blueprint Dossier / task rules | Machines/Utilaje (+ capacity contracts) | Human planner role | Explicit chain: Product System duration contract → dossier assumptions → (optional) machine capacity hint → planner override → null |
| **Unit** | n/a | minutes (per op / per letter / etc. as authored) | minutes (must not be lei/h) | minutes | minutes; source tag mandatory when non-null |
| **Formula** | none | Dossier-authored assumptions | Machine throughput / capacity formulas | none (entry) | Product System `PlanningDurationContract` where declared (today: Letters `vector_prep` only); else B/D |
| **Inputs** | none | Dossier JSON + geometry facts | Machine metadata, load, geometry | Planner UI input | Geometry/facts for formulas; dossier items; optional machine hints; planner value |
| **Freeze** | Freeze the *absence* + warning | Freeze dossier version that supplied minutes | Freeze machine registry version + formula id — high churn risk | Freeze planner entry + actor + timestamp | Freeze **resolved minutes + `planning_minutes_source`** at aggregate/plan freeze; live recompute only in DEV |
| **Versioning** | Warning code stable | Dossier version / FREEZE ON | Machine registry + formula catalog version | Audit log of edits | Source enum + version ids on each non-null resolve |
| **Fallback when missing** | Stay null (this *is* the policy) | Fall to A | Danger: silent invent — **forbid** unless Owner allows fallback to A | Stay null until entry | **Always fall to A** — never invent |
| **Commercial isolation** | Strong | Strong if dossier minutes ≠ price formulas | **Weak if** machine hourly leaks into quote — forbidden by Machines boundary | Strong if planner UI labeled “planificare internă” | Strong if each source tagged and Pricing barred |
| **Auditability** | High (honest gap) | High when provenance filled | Medium — need formula + machine id | High (who/when) | **Highest** if source stamp required |
| **Scheduling effect** | **Blocks** production schedule confidence | Enables schedule when populated | Enables load models; risk of false precision | Enables after human pass | Enables when any upstream source resolves; schedule GO only if policy says non-null required |
| **Migration** | Already live | Populate dossiers; wire resolve | Build capacity formulas + maintenance calendar; large | Planner UI + persist path | Extend TE2E-028B contracts per op; keep A for rest |
| **Risk** | Scheduling forever soft | Empty dossiers → still A; wrong assumptions baked | Contaminate commercial; overfit machine h; maintenance unknown | Bottleneck; inconsistent shop standards | Complexity; must forbid silent merge of sources |

---

## 4. Current runtime truth (do not rewrite history)

| Fact | Evidence |
|------|----------|
| DEC-006=A recorded short-term | `21_WORKOS_IMPLEMENTATION_ROUTE.md` §6 |
| Null ×N on fixtures | F7C 880811 (5) + 973019 (18); capacity batches on 92401 |
| Partial Product System path exists | `planning_duration_contract.py` — **only** `vector_prep` COUNT_BASED_TIME; not the F7C five ops |
| Dossier field exists | `time_assumptions_json` — often empty `{}` in seeds |
| F7C treatment | Warning only; never invents minutes; not a commercial blocker |
| Machines boundary | Estimated time hints allowed for planning — **not** commercial price |

---

## 5. Option notes (Owner-facing)

### A — Null + warning

- **Keep** as the **terminal honest state** and as the only allowed behavior when no authored source exists.
- Already accepted for dry / audit / F7C.
- **Insufficient alone** for production scheduling GO.

### B — Dossier time assumptions

- Good for template-level planning standards under FREEZE ON.
- Requires non-empty, validated assumptions (negative times already rejected in dossier validation).
- Must pair with `planning_minutes_source` provenance string.

### C — Machine registry

- Aligns with Utilaje owning capacity / feasibility.
- **Do not** use as primary commercial or as silent default for all ops.
- Safe role: **optional capacity factor / hint** after an operational duration contract exists — never lei/h to client.
- Maintenance/calendar data missing today → any C-based “availability minutes” would be incomplete.

### D — Planner manual

- Correct escape hatch for exceptions and pilot shops without formula coverage.
- Must not become the *only* long-term path (doesn't scale; weak standards).
- Entries must be labeled internal planning, versioned, and never feed quote lines.

### E — Hybrid (Agent C recommendation)

Ordered resolve (first hit wins; always stamp source):

1. **Product System planning duration contract** (template+op) — when `duration_mode` ∈ {static, formula} and inputs complete → minutes + source `product_system_duration_contract:<id>`  
2. Else **dossier / task-rule time assumptions** (approved, frozen) → source `dossier_time_assumptions:<version>`  
3. Else **optional** machine/capacity hint (Owner-gated, never commercial) → source `machine_capacity_hint:<code>:<formula>`  
4. Else **planner manual** override if present → source `planner_entry:<actor>:<ts>`  
5. Else **A** — null + `PLANNING_MINUTES_SOURCE_REQUIRED` / `..._MISSING`

**Blocker policy (recommend):**

| Stage | Null minutes |
|-------|--------------|
| Audit / preview / F7C resource readiness | **WARNING** (current) |
| Materialize (DEC-009) | Owner choice — currently warning-compatible under A |
| Production scheduling / capacity load GO | **BLOCKER** until non-null **or** explicit Owner risk re-accept |

---

## 6. Recommendation (without implementing)

| Item | Stamp |
|------|-------|
| **Primary long-term policy** | **E — Hybrid** |
| **Terminal fallback** | **A — null + warn** (never invent) |
| **Short-term / current stage** | Reconfirm **A** for F7C / dry fixtures (already recorded) |
| **First fill path for Letters ops** | Extend Product System duration contracts (pattern of `vector_prep`) **before** leaning on machine registry |
| **Machine registry (C)** | Secondary hint only; not default authority |
| **Planner (D)** | Override / exception, not sole source |
| **Commercial** | Minutes never enter CommercialPriceProposal / client hourly |
| **Activate code?** | **No** in this F7D audit — Owner stamp + scoped GO later |

---

## 7. Minimum Owner answer format

1. Long-term DEC-006 policy: `A` / `B` / `C` / `D` / **`E`**  
2. Reconfirm short-term A for current fixtures: `YES` / `NO`  
3. Null minutes at materialize: `WARNING` / `BLOCKER`  
4. Null minutes at scheduling GO: `WARNING` / `BLOCKER` (recommend BLOCKER)  
5. Allow machine-registry hints (C) inside hybrid: `YES` / `NO` / `LATER`  
6. Who may enter planner minutes (D): role list  
7. Explicit: no implementation until GO  

---

## 8. Lead summary — DEC-006

| | |
|--|--|
| **Recorded today** | A (null + warn) — still correct for honesty |
| **Open for production** | Real minutes source |
| **Recommend** | **E hybrid** with A fallback; grow Product System duration contracts; dossier second; machine hint optional; planner override; commercial isolation absolute |
| **Do not** | Invent zeros; use CostEngine/rates; treat F7C “ready_with_warnings” as schedule-ready |
| **Depends on** | Owner stamp above before any fill GO |

**Agent C confidence:** High that A must remain fallback; High that E matches existing TE2E-028B direction; Medium on when scheduling becomes BLOCKER (Owner stage call).

# Agent C — Resource Policy Decision Pack (F7D)

**Status:** READY_FOR_OWNER_DECISION · **READ-ONLY** (no code activation)  
**Scope:** Formal `machine_required | machine_optional | workcenter_only | unknown` policy — evaluate only; **DO NOT activate**  
**Fixture:** order `880811` / execution plan `22` (5 operational tasks)  
**Evidence:** F7C `PASS_WITH_WARNINGS` (`fbe1409f` / `43d7a3c5`); live capture `docs/qa/workos-f7c-operational-resource-readiness-v1/live-880811-resource-readiness.json`  
**Sources read:** `operational_resource_readiness_service.py`, `operational_workcenters.py`, F7C QA report, `14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`, `OPERATIONAL_RESOURCE_MAPPING_ARCHITECTURE.md`, `seed_operational_workforce_registry.py`

---

## 1. Verdict for Lead / Owner

F7C correctly **derives** a temporary mode (`orr_allowlist` | `workcenter_only` | `unknown_resource_policy`) from ORR allow-list ∩ `machines.resource_kind`. It does **not** own a formal requirement enum. Activating `machine_required | machine_optional | workcenter_only | unknown` is an **Owner policy stamp**, not an engineering invention.

**Recommendation (evaluate only):** stamp formal modes on the ORR **operation** row (registry `operation_code`, inherited by Product System aliases). Keep allow-list as **eligibility**, not as silent proof of required/optional. Treat empty allow-list as **`unknown`**, never as silent `workcenter_only`.

---

## 2. Layer separation (mandatory honesty)

These must stay distinct. F7C today intersects only (1)+(2)+(partial 3). Layers (4)–(7) are **out of readiness proof** until their data sources exist.

| Layer | Meaning | Current source | Proves? |
|-------|---------|----------------|---------|
| **1. Allow-list eligibility** | Which resource codes *may* be used for this operation | ORR `allowed_resource_codes` | Eligibility only |
| **2. Active registry membership** | Code exists and `is_active=true` | `machines` registry | Candidate exists |
| **3. Available now** | `is_available` / `operational_status` | `machines` (partial) | Soft availability signal — **not** schedule booking |
| **4. Capability fit** | Size / thickness / material / process limits | `capacity_metadata` (partial; UI not full) | Feasibility — **not** ORR mode |
| **5. Material / thickness gate** | Job geometry vs machine limits | ProductAggregate + machine limits | Commercial-adjacent feasibility — **not** price |
| **6. Maintenance conflict** | Downtime windows | **Missing** (F7C `maintenance_conflict` unreachable) | Future blocker only |
| **7. Calendar / load** | Slot, load, assignment | Capacity / ExecutionPlan assignment | Scheduling — **not** F7C readiness |

Architecture boundary (`14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`): Machines own utilaje, capabilities, limits, availability, maintenance, capacity — **never** commercial client price. Capacity warnings must stay separated from commercial blockers.

---

## 3. Clarifying questions — proposed Owner answers

### Q1 — Does ORR machine allow-list mean `machine_required`?

**No.** Allow-list = eligibility set.

| Today (F7C derivation) | Honest formal policy |
|------------------------|----------------------|
| Any allow-list entry of kind `machine`/`tool` → mode `orr_allowlist`; zero active machine/tool candidates → status `machine_required_but_none_compatible` | Formal `machine_required` must be an **explicit ORR field** (or Owner stamp). Presence of MCH-* codes alone must **not** auto-activate required |

**Risk if conflated:** welding (`return_face_bonding`) allow-lists tools + work area with **no default**. F7C treats active tools as enough for `ready_with_warnings`, but the status vocabulary still says “machine_required_but_none_compatible” when tools are inactive — implying required without Owner stamp.

**Owner decision needed:** for each op, whether allow-listed machines/tools are **required**, **optional**, or the op is **workcenter_only** regardless of allow-list content.

---

### Q2 — Can a work-area satisfy `workcenter_only`?

**Yes — when ORR allow-list contains only `work_area` kinds (or Owner stamps `workcenter_only`).**

| Case | F7C today | Proposed formal meaning |
|------|-----------|-------------------------|
| Allow-list = `[WA-ASSEMBLY-01, WA-ASSEMBLY-02]` only | `workcenter_only` | Valid evidence for `workcenter_only` *if* Owner accepts work areas as the WC physical place, not as machines |
| Allow-list empty `[]` | **Also** `workcenter_only` | **Invalid silent proof** — see Q3 |
| Allow-list = tools + WA | `orr_allowlist` | Not `workcenter_only`; tools are machine-like |

Work-area ≠ assigned atelier seat. It proves “a registered place exists under the WC,” not “operator is scheduled there.”

---

### Q3 — Empty allow-list = optional / workcenter_only / unknown?

**Must be `unknown` — must NOT silently prove `workcenter_only`.**

| Empty `allowed_resource_codes` | F7C today | Owner-safe target |
|--------------------------------|-----------|-------------------|
| e.g. ORR `field_installation` seed `[]` | Derives `workcenter_only` (`test_no_resource_codes_is_workcenter_only`) | **`unknown`** until Owner stamps mode + whether WC alone is sufficient |

**Why:** empty list is absence of policy evidence, not positive proof that no machine is needed. Silent `workcenter_only` greenwashes missing ORR authorship.

**Related gap:** codes listed but missing from `machines` registry → F7C correctly uses `unknown_resource_policy` (does not guess `workcenter_only`). Keep that honesty; extend it to empty lists when formal enum is activated.

---

### Q4 — Policy owner: operation vs component vs WC registry vs separate?

| Option | Fit | Risk |
|--------|-----|------|
| **A. ORR operation row** (`operation_resource_requirements.operation_code` + PS aliases) | **Recommended.** Already owns allow-list, WC allow-list, default, skills | Alias collisions (e.g. `painting` → registry `assembly`) inherit assembly resource policy |
| B. Component / module | Wrong layer — modules activate ops; they should not redefine machine policy | Duplicate truths; DEC-004 painting alias pain |
| C. WC registry alone | WC identity only (`operational_workcenters.py`) | WC has many ops with different machine needs |
| D. Separate resource-policy registry | Clean if ORR must stay eligibility-only | Extra system; avoid until ORR cannot carry a mode field |

**Recommend A:** add (later, post-Owner GO) a formal field on ORR, e.g. `resource_requirement_mode`, versioned with the mapping. Product System aliases inherit; do not invent per-component overrides without explicit GO.

**Painting special case:** live `painting` resolves via alias to registry op `assembly` → WA-ASSEMBLY only → F7C `workcenter_only`. Display name still says “Painting module (alias)”. Owner must decide whether **painting** deserves its own ORR row / booth machine policy, or consciously inherits assembly work-area policy.

---

### Q5 — Freeze into operational truth how?

| Stage | What freezes | What stays live |
|-------|--------------|-----------------|
| **ORR DEV version** | Formal mode + allow-list + default when Owner accepts mapping version | Edits in DEV only |
| **FREEZE ON (registry)** | Accepted ORR version immutable | New DEV version for change |
| **Materialize (ExecutionPlan)** | Task keeps frozen `workcenter` + `source_operation_code`; optionally stamp **resolved** mode + allow-list snapshot for audit | Live `is_active` / `is_available` for *current* readiness re-read |
| **F7C read model** | Never writes `machine_code`; never invents mode | Re-derives against current registry until formal field exists |

**Recommended freeze rule:**

1. Formal mode is **authored** on ORR (Owner-accepted version).
2. At materialize, envelope may **copy** `resource_requirement_mode_resolved` + `allowed_resource_codes_frozen` for audit (optional later GO).
3. Readiness re-eval may refresh **active/available** against live registry, but must not rewrite frozen mode without new DEV ORR version.
4. Assignment of concrete `machine_code` remains a **later Execution / scheduling GO** — not F7C, not this pack.

---

## 4. Per-task matrix — 880811 / plan 22

Target enum (evaluate only): `machine_required` | `machine_optional` | `workcenter_only` | `unknown`

| Task | Workcenter | ORR evidence (live) | Candidate type | Proposed formal mode | Confidence | Owner decision |
|------|------------|---------------------|----------------|----------------------|------------|----------------|
| `face_cnc_cut` | `WC_CNC_ROUTING` (resolved) | Registry op `cnc_cutting`; allow `[MCH-CNC-4020]`; default `MCH-CNC-4020`; auth `hybrid`; F7C mode `orr_allowlist`; status `ready_with_warnings` (minutes warn) | **machine** (1 default, active+available) | **`machine_required`** | **High** | `[ ]` Confirm CNC face cut requires a CNC machine (not WC alone) |
| `side_forming` | `WC_LETTER_FORMING` (resolved) | Registry op `cant_modelare`; allow `[MCH-CNC-CANT-LITERE]`; default same; F7C `orr_allowlist` / `ready_with_warnings` | **machine** (1 default) | **`machine_required`** | **High** | `[ ]` Confirm cant forming requires forming CNC |
| `return_face_bonding` | `WC_METAL_FAB` (resolved) | Registry op `welding`; allow `[MCH-WELD-STEEL, MCH-WELD-ALU, WA-WELD-TABLE]`; **no default**; F7C `orr_allowlist` / `ready_with_warnings` (tools active) | **tool** ×2 + **work_area** ×1 | **`machine_optional`** *or* **`machine_required`** (Owner pick) | **Medium** | `[ ]` Are welding tools required, or is WA-WELD-TABLE alone enough? If tools required → `machine_required`. If WC/WA sufficient and tools preferred → `machine_optional` |
| `painting` | `WC_ASSEMBLY` (resolved) | Alias → registry `assembly`; allow `[WA-ASSEMBLY-01, WA-ASSEMBLY-02]` only; no default; F7C `workcenter_only` | **work_area** only (no machine/tool) | **`workcenter_only`** *provisional* — or **`unknown`** if paint booth is real requirement | **Medium-Low** | `[ ]` Stamp: (a) inherit assembly WA policy, or (b) new ORR `painting` / booth machine, or (c) keep `unknown` until booth exists |
| `packaging_letters` | `WC_ASSEMBLY` (resolved) | Registry op `packaging`; allow WA-ASSEMBLY ×2; F7C `workcenter_only` | **work_area** only | **`workcenter_only`** | **High** | `[ ]` Confirm packaging is place-only (no machine) |

**Aggregate fixture note:** top-level F7C `ready=0`, `warning_count=5`, `blocked=0` — all five carry `PLANNING_MINUTES_SOURCE_MISSING` (DEC-006; capacity warning, not commercial blocker).

---

## 5. Formal mode semantics (proposed dictionary — not activated)

| Mode | Meaning | Allow-list expectation | Missing active machine/tool |
|------|---------|------------------------|-----------------------------|
| `machine_required` | At least one compatible active machine/tool from allow-list is needed before resource-ready | Should list ≥1 machine/tool | Block (`machine_required_but_none_compatible` / unavailable) |
| `machine_optional` | Machine/tool may help; WC/work-area can proceed without | May list machines/tools and/or WA | Warn (`machine_optional_no_candidate`) — **not** hard block |
| `workcenter_only` | Operation is place/WC-scoped; machine absence is expected | Empty **only if Owner-stamped**, or WA-only list | Never block for missing machine |
| `unknown` | Policy not authored / empty evidence / unregistered codes | Empty, missing ORR, or ambiguous WC mapping | Block or strong warn — **never** pretend ready |

**Mapping from current F7C derived modes (reference only):**

| F7C `resource_requirement_mode` | Suggested formal successor |
|---------------------------------|----------------------------|
| `orr_allowlist` | Split by Owner stamp → `machine_required` **or** `machine_optional` |
| `workcenter_only` (WA-only list) | `workcenter_only` if Owner confirms |
| `workcenter_only` (empty list) | **`unknown`** (correct F7C later) |
| `unknown_resource_policy` | `unknown` |

---

## 6. What F7C must not keep implying after Owner stamp

1. **`orr_allowlist` ≈ required** — replace with formal mode read.
2. **Empty allow-list ≈ workcenter_only** — reclassify to `unknown` when formal enum activates.
3. **Compatible candidates ≠ assigned / scheduled / atelier booked.**
4. **`is_available=true` ≠ calendar free.**
5. **Work-area list ≠ full capability** (thickness, booth type, welding process).
6. **No `machine_code` write** onto operational tasks from readiness alone.

---

## 7. Minimum Owner answer format

Owner should stamp:

1. Formal mode for each of the 5 ops in the matrix above (or “defer / unknown”).
2. Policy owner = **ORR operation** (confirm or reject).
3. Empty allow-list default = **`unknown`** (confirm — recommended).
4. `return_face_bonding`: tools **required** vs **optional**.
5. `painting`: inherit `assembly` WA policy vs dedicated ORR vs unknown until booth.
6. Freeze rule: mode on ORR version only vs also copy into materialize envelope.
7. Explicit: **do not activate enum in code** until this pack is signed and a scoped GO is opened.

---

## 8. Lead summary — resource policy

| Priority | Recommendation |
|----------|----------------|
| P0 | Do **not** activate formal enum in F7D implementation yet — decision pack only |
| P0 | Treat empty allow-list as **`unknown`**, not silent `workcenter_only` |
| P1 | Stamp `machine_required` for `face_cnc_cut` + `side_forming` |
| P1 | Owner pick on `return_face_bonding` tools required vs optional |
| P1 | Owner pick on `painting` policy ownership (alias vs dedicated) |
| P2 | Keep layers 4–7 (capability / material / maintenance / calendar) out of “ready” until sources exist |
| P2 | Policy lives on ORR operation (+ aliases); WC registry stays identity-only |

**Agent C confidence in this pack:** High on evidence description; Medium on proposed modes for bonding/painting (Owner shop truth required).

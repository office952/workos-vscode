# DEC-003 Owner Packet — RETURN Operation Canonical Path

## 1. Status

**READY_FOR_OWNER_DECISION**

This packet prepares the owner decision for the canonical RETURN operation path on the V2 execution graph.

---

## 2. Decision question

Which operation family is canonical for RETURN / lateral forming on the operational V2 path?

Current duplicate families in the audited chain:

1. parent-level `side_forming`
2. parent-level `return_face_bonding`
3. module-level `RETURN_PROFILE_MACHINE_FORMING`
4. module-level `RETURN_PROFILE_FACE_BONDING`

The system currently exposes both parent intent and module-specific aliases in the broader aggregate/runtime evidence, which is acceptable for read-only truth, but unsafe for materialization until the canonical path is explicit.

---

## 3. Current runtime truth

Validated fixture evidence:

1. order `88002`
2. quote snapshot V2 `id=3`
3. snapshot code `QSN2-2026-0003`
4. execution plan `id=2`
5. `planned_tasks[] = 12`
6. `planned_operations[] = 17`

Relevant parent-path task/runtime items already visible in V2 preview:

1. `return_profile_forming`
2. `return_face_bonding`

Relevant module-path operation/runtime items also present in persisted evidence:

1. `RETURN_PROFILE_MACHINE_FORMING`
2. `RETURN_PROFILE_FACE_BONDING`

Observed risk:

1. preview can truthfully show both semantic layers
2. materialization cannot safely decide alone whether both, one, or neither should become operational tasks

---

## 4. Why this decision matters

Without DEC-003, the system cannot safely answer all of these:

1. which RETURN node becomes the operational task source
2. which node is only a technical/module alias
3. which dependencies should point to the canonical RETURN path
4. which workcenter and minutes policy applies to RETURN
5. whether materialization would duplicate or distort operational truth

This is exactly why POST materialization remains blocked.

---

## 5. Options

### Option A — Parent path canonical, module path alias only

Canonical operational path:

1. `side_forming`
2. `return_face_bonding`

Module entries remain:

1. documentation / aggregate aliases only
2. provenance only
3. never materialized as separate operational tasks

Pros:

1. simpler operational graph
2. cleaner preview-to-materialize mapping
3. preserves module detail as provenance without duplicating runtime tasks

Cons:

1. loses some direct module-specific operational naming in the executable layer
2. requires explicit alias policy in aggregate/task contract

### Option B — Module path canonical, parent path intent-only

Canonical operational path:

1. `RETURN_PROFILE_MACHINE_FORMING`
2. `RETURN_PROFILE_FACE_BONDING`

Parent entries remain:

1. design intent only
2. displayed in aggregate truth
3. not materialized as separate operational tasks

Pros:

1. stronger specificity for production semantics
2. easier future workcenter/utilaj linkage if module path already carries better operational granularity

Cons:

1. requires task contract and preview layer to demote current parent tasks
2. risks mismatch with already visible parent-oriented preview/task naming

### Option C — Hybrid split by semantics

Possible split:

1. one canonical node for machine forming
2. one canonical node for face bonding
3. parent/module entries normalized per sub-step

Pros:

1. most expressive model
2. may preserve both intent and executable precision

Cons:

1. highest implementation complexity
2. easiest path to ambiguity if not specified in exact mapping rules
3. not recommended without a strict mapping table

---

## 6. Implementation impact by area

### If Option A is chosen

Preview:

1. keep parent RETURN tasks visible as canonical
2. mark module RETURN rows as aliases/provenance only

Persist draft:

1. `planned_tasks[]` stay parent-canonical
2. duplicate module semantics remain informational only

Materialization:

1. materialize only parent-canonical RETURN tasks
2. exclude module duplicates from `operational_tasks[]`

### If Option B is chosen

Preview:

1. shift canonical display toward module RETURN path
2. parent rows become intent-only or derived labels

Persist draft:

1. `planned_tasks[]` need remapping toward module-canonical tasks
2. dependency graph must be rewritten around module nodes

Materialization:

1. materialize only module-canonical RETURN tasks
2. parent duplicates never become operational rows

### If Option C is chosen

Preview:

1. exact split rules must be shown explicitly
2. aliases must be labeled aggressively to avoid ambiguity

Persist draft:

1. requires a new normalization table for RETURN sub-steps
2. highest regression risk without fixture regeneration

Materialization:

1. blocked until split rules are exact and tested

---

## 7. Minimum owner answer format

Owner should answer in this exact format:

1. canonical path: `A` or `B` or `C`
2. if `C`, exact canonical node list
3. alias policy: which rows remain provenance-only
4. materialization rule: which rows are forbidden from becoming operational tasks
5. dependency rule: which predecessor/successor chain is canonical

---

## 8. Recommended constraint for implementation

Regardless of chosen option, implementation should obey this constraint:

1. exactly one canonical RETURN path may materialize into `operational_tasks[]`
2. all non-canonical RETURN rows must remain read-only provenance, alias, or excluded items

---

## 9. Blocking effect

Until DEC-003 is answered:

1. upstream task-contract enrichment for RETURN cannot be finalized
2. fresh fixture regeneration cannot prove RETURN materialization semantics
3. `POST /materialize-tasks/{order_id}` should remain blocked for canonical rollout

---

## 10. Verdict

**DEC-003 is a real blocking owner decision, not a cosmetic naming choice.**

The current application can expose the ambiguity read-only, but must not resolve it silently in runtime code.
# DEC-004 Owner Packet — PAINTING Canonical Path

## 1. Status

**READY_FOR_OWNER_DECISION**

This packet prepares the owner decision for the canonical PAINTING path on the V2 execution graph.

---

## 2. Decision question

Which painting family is canonical on the operational V2 path?

Current duplicate painting semantics in the audited chain:

1. parent-level `painting`
2. module-level `PAINTING`

The read-only surfaces can show both today, but materialization must not silently decide whether both are executable tasks or one is only provenance/alias.

---

## 3. Current runtime truth

Validated fixture evidence:

1. order `88002`
2. quote snapshot V2 `id=3`
3. execution plan `id=2`
4. V2 preview shows parent task `painting`
5. persisted plan evidence also carries module-level `PAINTING`

Observed risk:

1. painting may be over-represented in technical truth
2. materialization cannot infer safely whether the module-level entry is canonical or only detailed provenance

---

## 4. Why this decision matters

Without DEC-004, the system cannot safely decide:

1. which PAINTING node is operationally canonical
2. which node owns workcenter and minutes truth
3. whether the parent or module path should drive dependencies
4. whether painting should appear once or multiple times in `operational_tasks[]`

---

## 5. Options

### Option A — Parent painting canonical

Canonical operational path:

1. `painting`

Module `PAINTING` remains:

1. alias/provenance only
2. not materialized separately

### Option B — Module painting canonical

Canonical operational path:

1. `PAINTING`

Parent `painting` remains:

1. intent-only / aggregate label
2. not materialized separately

### Option C — Explicit split by sub-purpose

Possible split:

1. parent path remains business-facing intent
2. module path remains executable painting operation
3. exact mapping rules must be written explicitly

---

## 6. Implementation impact by area

If Option A is chosen:

1. `planned_tasks[]` can keep `painting` as canonical
2. module `PAINTING` becomes alias/provenance only
3. materialization excludes module duplicate

If Option B is chosen:

1. preview/task contract must remap canonical node toward `PAINTING`
2. parent `painting` becomes derived/intention label only
3. materialization excludes parent duplicate

If Option C is chosen:

1. split rules must define exact sub-roles
2. fixture regeneration becomes mandatory before materialization GO

---

## 7. Minimum owner answer format

1. canonical path: `A` or `B` or `C`
2. alias policy: which node remains provenance-only
3. materialization rule: which painting rows are forbidden from operational task creation
4. dependency rule: where painting sits in the canonical chain

---

## 8. Blocking effect

Until DEC-004 is answered:

1. painting canonicalization cannot be finalized in upstream task-contract enrichment
2. materialization remains unsafe for volumetric V2 canonical rollout

---

## 9. Verdict

**DEC-004 is a real operational semantic decision.** It must be answered before safe canonical materialization.
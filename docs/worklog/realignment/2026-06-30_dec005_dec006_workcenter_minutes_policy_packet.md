# DEC-005 / DEC-006 Owner Packet — Workcenter and Estimated Minutes Policy

## 1. Status

**READY_FOR_OWNER_DECISION**

This packet groups the two closely related policies that currently remain null across the validated V2 fixture:

1. workcenter source policy
2. estimated minutes source policy

---

## 2. Current runtime truth

Validated fixture evidence from order `88002` / execution plan `id=2`:

1. all `12` planned tasks are visible in preview
2. all `12` planned tasks show missing workcenter on the current read-only truth layer
3. all `12` planned tasks show `estimated_minutes = null`
4. all `12` planned tasks carry `PLANNING_MINUTES_SOURCE_REQUIRED`

This is acceptable for truth exposure, but not enough for canonical operational materialization.

---

## 3. DEC-005 — Workcenter source policy

### Decision question

What is the authoritative source for `planned_tasks[].machine_requirement.workcenter`?

### Options

#### Option A — Aggregate operation source canonical

1. workcenter comes from canonical aggregate operation mapping
2. task contract inherits from upstream operation truth

Pros:

1. keeps workcenter truth upstream and frozen
2. better fit for snapshot-first architecture

#### Option B — Module/operator alias source canonical

1. workcenter comes from module-specific operational alias rows
2. parent rows may remain intent-only

Pros:

1. can carry finer operational specificity

Risk:

1. increases dependence on duplicate semantics if DEC-003/004 are unresolved

#### Option C — Manual/post-materialize enrichment

1. preview stays null
2. workcenter assigned only after materialization or scheduling layer

Pros:

1. less upstream rewrite

Risk:

1. weakens frozen upstream truth and increases downstream guesswork

### Recommended implementation constraint

1. unknown workcenter must remain null
2. null is preferable to invented defaults
3. materialization GO should define whether null workcenter is blocker or warning

---

## 4. DEC-006 — Estimated minutes source policy

### Decision question

What is the authoritative source for `planned_tasks[].estimated_minutes` and `planning_minutes_source`?

### Options

#### Option A — Dossier/task-rule planning source canonical

1. planning minutes come from explicit task/dossier rules where defined
2. provenance is preserved in `planning_minutes_source`

#### Option B — Capacity formula source canonical

1. planning minutes come from approved capacity formulas
2. remains operational/capacity truth only, never commercial pricing input

#### Option C — Null allowed by policy

1. keep minutes null when authoritative planning source is missing
2. warning remains explicit
3. owner decides whether materialization still allowed under warning-only mode

### Recommended implementation constraint

1. `planning_minutes_source` must be explicit whenever minutes are non-null
2. no silent zero values
3. no hourly commercial contamination

---

## 5. Minimum owner answer format

Owner should answer:

1. DEC-005 source policy: `A`, `B`, or `C`
2. DEC-005 blocker policy: null workcenter is `BLOCKER` or `WARNING`
3. DEC-006 source policy: `A`, `B`, or `C`
4. DEC-006 blocker policy: null minutes is `BLOCKER` or `WARNING`
5. if warning-only, whether materialization may proceed with explicit audit badges

---

## 6. Blocking effect

Until DEC-005 / DEC-006 are answered:

1. workcenter enrichment cannot be finalized
2. minutes enrichment cannot be finalized
3. materialization quality remains below canonical confidence

---

## 7. Verdict

These are not cosmetic fields. They define whether the task graph is operationally placeable and schedulable.
# DEC-007 / DEC-009 Owner Packet — Dependency Policy and Materialization GO

## 1. Status

**READY_FOR_OWNER_DECISION**

This packet combines:

1. the dependency/DAG policy decision
2. the final materialization GO gate

They are grouped because materialization quality depends directly on dependency truth.

---

## 2. Current runtime truth

Validated fixture evidence:

1. V2 preview and persisted draft are working on order `88002`
2. materialization audit GET is working read-only
3. dry-run status is visible
4. POST materialization remains blocked by governance and unresolved semantics

Current dependency model risk:

1. current task chain is effectively a naive linear predecessor model
2. future operational truth may require explicit branch/fan-in semantics
3. materialization should not freeze a naive graph if owner expects richer DAG behavior

---

## 3. DEC-007 — Dependency policy

### Decision question

What dependency model is canonical for V2 operational task materialization?

### Option A — Linear MVP accepted

1. each task depends on a single immediate predecessor where applicable
2. acceptable for pilot materialization

Pros:

1. lowest implementation complexity
2. easiest fixture verification

Risk:

1. may under-model parallelizable branches

### Option B — Structured DAG required before GO

1. explicit fan-in / fan-out allowed
2. dependency semantics defined by task family

Pros:

1. closer to target architecture
2. safer for future operational scheduling

Risk:

1. larger upstream implementation before first materialization GO

### Option C — Linear MVP for pilot, DAG mandatory before broader rollout

1. allow constrained pilot materialization now
2. require later DAG enrichment before scale-up

Pros:

1. balances delivery and rigor

Risk:

1. must be constrained explicitly to avoid silent long-term drift

---

## 4. DEC-009 — Materialization GO

### Decision question

Under what minimum conditions may `POST /materialize-tasks/{order_id}` be exercised on the canonical V2 path?

### Recommended gate checklist

Materialization should require explicit answers for:

1. DEC-003 RETURN canonical path
2. DEC-004 PAINTING canonical path
3. DEC-005 workcenter policy
4. DEC-007 dependency policy

Optional owner tolerance decision:

1. whether DEC-006 null minutes can proceed under warning-only mode

### Negative cases that should still block POST

1. unresolved duplicate canonical families
2. dependency ambiguity beyond owner-accepted pilot rules
3. mixed canonical + alias rows both eligible for operational task creation
4. downstream assumptions that Employee Mobile or sessions are ready

---

## 5. Minimum owner answer format

1. DEC-007 policy: `A`, `B`, or `C`
2. DEC-009 GO state: `BLOCKED` or `APPROVED_FOR_CONTROLLED_FIXTURE_ONLY`
3. if approved, exact constraints on eligible fixture and warning tolerance
4. whether null minutes under DEC-006 are allowed as warning-only for pilot

---

## 6. Blocking effect

Until DEC-007 / DEC-009 are answered:

1. dependency enrichment cannot be finalized
2. POST materialization must remain blocked for canonical rollout
3. sessions / actuals remain downstream-blocked by design

---

## 7. Verdict

**DEC-009 is not a technical toggle.** It is the owner authorization point for turning read-only semantic truth into operational task truth.
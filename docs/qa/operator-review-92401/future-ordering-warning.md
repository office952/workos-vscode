# Future Warning — Operator Task Ordering / SEQ Readability

**Date:** 2026-07-31  
**Scope:** Future UX / order-readability only  
**This GO:** **docs-only** · no product implementation

---

## Owner observation

The task table is **acceptable for now**, but default operator ordering should improve later.

---

## Required future behavior (when chartered)

| Rule | Binding |
|------|---------|
| Default view | Prefer **dependency / topological execution order** |
| Original `sequence_index` / SEQ | Must remain **visible as reference** |
| Remap SEQ to 1..N | **Forbidden** |
| Hardcode fixture UI | **Forbidden** (no 92401/13/MAT-02 productization) |
| Gap/badge product UI | **Forbidden** |

---

## Current state (92401)

- Live ops count **18** with provenance `sequence_index` values that are **not** contiguous 1..18 (gaps e.g. 11–12, 15–23).
- Count is correct; readability suffers when operators assume SEQ = execution rank 1..N.
- Do **not** “fix” by renumbering SEQ in data.

---

## Deferred

Track as a future Owner GO for ops-graph / Execution plan read-model ordering. Not in scope for Accept 92401 / HR park / cant-finish policy recording.

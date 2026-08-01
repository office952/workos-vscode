# Ordering logic — Ops-Graph Topological Display Order

**Module:** `frontend/src/lib/opsGraphDisplayOrder.ts`  
**Consumer:** `MaterializedOpsGraph.tsx` → `sortedTasks`

## Algorithm

1. Build graph from `depends_on_task_ids` (edges only when both ends exist in the task set).  
2. Kahn topological sort.  
3. Ready-set tie-break: original **source** `sequence_index` (from `read_clarity.identity.sequence_index` or `sequence_index`), then `task_id`.  
4. Cycles / leftovers: append by source SEQ (honest fallback).  
5. **Never** rewrite `sequence_index` on task objects.

## UI

- Subtitle + note: `Display order: dependency order · SEQ: original source sequence (not remapped)`  
- Column header: **SEQ** (source), not display rank 1..N  

## Source docs

Named `project_sources/*` pack **missing** on disk. Alignment used Owner `future-ordering-warning.md` + prior execution/ops-graph contracts.

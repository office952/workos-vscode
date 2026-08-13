# PERFORMANCE_BEFORE_AFTER

| Metric | Before (Phase 0) | After (D2) |
|---|---:|---:|
| BEFORE_CLICK_TO_CURRENT_MS | 1842–2798 (discrete concurrent) | — |
| AFTER_CLICK_TO_CURRENT_MS | — | **373 / 412** |
| BEFORE_PQ_WITH_LL_MS | 717–1069 | — |
| AFTER_PQ_WITH_D2_MS | — | **219 / 242** (PQ alone while LL waits) |
| BEFORE_LL_WITH_PQ_MS | 897–1107 | — |
| AFTER_LL_SEQUENTIAL_MS | — | **168 / 174** |
| BEFORE_FULL_FANOUT_GET_COUNT | 7 (live discrete) | — |
| AFTER_FULL_FANOUT_GET_COUNT | — | **7** (same family; LL sequenced) |

## Target

```text
CLICK_TO_CURRENT < 1200 ms typical → PASS
Preferred < 1000 ms → PASS (373–412 ms)
```

## Note

GET count unchanged; win is removal of PQ↔LL SQLite contention on the offer path, not deleting endpoints.

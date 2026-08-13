# BACK_BEVEL_RUNTIME_MATRIX

Owner source `e994927e-…` read-only. Mutations = QA clones only.

| Scenario | Commercial | Execution |
|----------|------------|-----------|
| Backing ON, bevel OFF | no `sanfren_spate`; debitare 4.9475; net 568.64 / gross 688.05 | cut op; no bevel op; 16 production tasks |
| Same config, bevel ON | `sanfren_spate` 22.2525; debitare unchanged; net 590.89 / gross 714.98 | bevel op present; **same 16 tasks**; cut+bevel in one backing CNC task |
| Mixed groups (unit) | qty = ON group perimeters only | still one backing CNC task |

```text
COMMERCIAL_EFFECT = CORRECT
PRODUCTION_TASK_FRAGMENTATION = NONE
EXECUTION_TASK_COUNT_DELTA = 0
OWNER_DEV_DB_MUTATIONS = 0
```

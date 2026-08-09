# Aggregation matrix

| Level | Input | Output | Persisted? |
|-------|-------|--------|------------|
| SESSION | closed session row | minutes + seconds + provenance | session SoT only |
| EMPLOYEE+TASK | sessions for (emp, task) | sum | derived |
| TASK | sessions for task | sum employee-minutes | derived |
| PLAN | all closed on plan | sum | derived |
| ORDER | plan for order (1:1 today) | sum | derived |

```text
employee-minutes = sum of closed session durations
wall-clock overlap between employees is NOT deduplicated
MachineRun minutes NEVER included
active elapsed NEVER finalized
```

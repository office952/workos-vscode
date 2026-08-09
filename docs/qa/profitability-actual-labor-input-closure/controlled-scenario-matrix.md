# Controlled scenario matrix

Command:

```text
cd backend
APP_ENV=test ENVIRONMENT=test
.\.venv\Scripts\python.exe -m pytest tests/test_profitability_actual_labor_input_closure.py -q
→ 19 passed
```

| # | Scenario | Result |
|---|----------|--------|
| 1 | Single closed session 30m | 1 emp / 1 session / 30m / provenance OK |
| 2 | Two sessions same emp/task 20+15 | 35m; session provenance retained |
| 3 | Two employees same task 20+30 | 50 employee-minutes; no wall-clock dedupe |
| 4 | Multiple tasks 20+40 | Plan total 60; task breakdown retained |
| 5 | Order = single plan | Order totals == plan totals |
| 6 | Active + closed | Finals = closed only; active `not_final` |
| 7 | Restart durability | Identical after re-read from DB |
| 8 | Idempotent replay start/end | One factual session; no duplication |
| 9 | Compatibility bridge start + controlled end | Parity; forged client ts ignored |
| 10 | MachineRun declared on task | Labor = sessions only (50); machine excluded |
| 11 | Planned 100 vs actual 12 | Planned unchanged |
| 12 | Incomplete task after END | Labor still queryable; no auto-complete |
| 13 | END then complete rejected; complete stamp no dupe | Minutes stable on replay |
| 14 | Rounding | Banker's half-to-even documented |
| 15 | Timezone absolute | 60m / 3600s from UTC stamps |
| 16 | Malformed fail-closed | Invalid excluded; valid counted |
| 18 | Employee rename | Labor ids/minutes unchanged |
| 19 | Write authority / commercial | controlled authority; commercial_mutated=false |
| 20 | QA untouched | order 880750 count unchanged |

Note on scenario 3: production Phase E reassignment after history remains deferred. Isolated fixture swaps assignment pointer only to author sequential closed sessions for aggregation proof.

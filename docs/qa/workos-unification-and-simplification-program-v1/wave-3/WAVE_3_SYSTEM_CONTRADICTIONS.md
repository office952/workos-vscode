# Wave 3 system contradictions

Initial audit logged six rows. Gap closure **retracts** same-work contradictions that were premature.

| ID | Same truth | Status after gap closure |
|----|------------|--------------------------|
| W3-C1 | Order identity IV6 vs 973024 vs Atelier `ORD-92400` | **RETRACTED as contradiction.** Class: `DIFFERENT_ACTIVE_WORK`. 92400 is another live print job. 973024↔IV6 is code vs DB id of one order (identity split, not vs 92400). |
| W3-C2 | Where work happens | **KEEP as architectural split** (not a false-fact). Atelier = CANONICAL_MONITOR_HOME; actions on COMPAT `/operator` + `/tablet` + hidden employee-app-v2. |
| W3-C3 | `assigned` and `Neatribuit` together | **RETRACTED as contradiction.** Class: `FRONTEND_LABEL_COMPOSITION` of two valid facts (lifecycle queued vs no employee). |
| W3-C4 | Plan 973024 vs Atelier live 92400 | **RETRACTED as contradiction.** Same as C1 — different active work + 973024 filtered out of the live card (no `in_progress`). |
| W3-C5 | Status vocab | **KEEP** — executionTask / mobile Now / MachineRun / schedule / eligibility still differ |
| W3-C6 | Wave 2 money vs production | **KEEP as projection split** — EUR offer vs RON order vs no money on Atelier; not a same-id collision |

Contradiction log updated only where evidence **disproved** contradiction (C1, C3, C4). C2/C5/C6 remain observations, not new contradictions.

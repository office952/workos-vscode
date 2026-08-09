# MachineRun UI state matrix (isolated runtime)

| Status | UI label | Primary | Secondary | Danger | Screenshot |
| ------ | -------- | ------- | --------- | ------ | ---------- |
| HELD | Grupare | Confirmă rularea | Reprogramează · Elimină (when >2) | Anulează | held light/dark |
| RESERVED | Rezervat | Pornește utilajul | Reprogramează · Eliberează | Anulează | reserved dark |
| RUNNING | În lucru pe utilaj | Finalizează lucrul pe utilaj | — | — | running dark |
| COMPLETED | Lucru utilaj finalizat | Eliberează utilajul | hint: rămâne rezervat | — | completed dark |
| RELEASED | Eliberat | — (read-only) | — | — | released light/dark |
| EMPTY | — | — | CREATE deferred | — | empty light/dark (QA) |

CREATE/ADD UI deferred — candidate discovery API missing.

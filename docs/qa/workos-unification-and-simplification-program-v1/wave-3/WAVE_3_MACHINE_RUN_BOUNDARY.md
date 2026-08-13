# Wave 3 — MachineRun boundary

List copy is honest: start/finalize here = machine work, not task/session.

| Check | Result |
|-------|--------|
| MachineRun COMPLETE ≠ session END | Stated in UI/backend comments |
| Session END ≠ task COMPLETE | Code (`derive_task_status_from_sessions`); not proven on a live run |
| Task COMPLETE ≠ order COMPLETE | Execution dashboard vs orders Înghețat |
| Live detail | STATE_NOT_REACHED — GET list `count=0`; create not forced |
| Gap closure | `MACHINERUN_DETAIL_RUNTIME_REACHED=NO`; `MACHINERUN_GAP_RESOLVED=YES` |

**MACHINE_RUN_VS_EMPLOYEE_SESSION_SEPARATION = CLEAR in copy / UNKNOWN in live detail**

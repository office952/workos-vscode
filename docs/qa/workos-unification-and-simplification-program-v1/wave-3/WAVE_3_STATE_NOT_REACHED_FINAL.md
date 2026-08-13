# Wave 3 STATE_NOT_REACHED — final

These were **not** forced. Acceptable for PASS when the blocker is explicit and the boundary is proven.

| # | State | BLOCKER | MUTATION_REQUIRED | WHY_NOT_FORCED |
|---|-------|---------|-------------------|----------------|
| 1 | Generate execution plan | `POST` plan-from-order / V2 materialize | YES | freeze / Owner truth |
| 2 | Task start / complete / pause / block | `POST /api/v1/operator/task-action` | YES | freeze / Owner truth |
| 3 | Assign / unassign employee | operator panel + Ops-Graph picker | YES | freeze / Owner truth |
| 4 | Employee session start / stop | mobile / helper-session APIs | YES | freeze / Owner truth |
| 5 | MachineRun create + detail | list `items=[]` `count=0`; create dialog writes a run | YES | freeze / Owner truth; no safe existing row |
| 6 | Employee-app-v2 Start | `startTask` / helper session POST | YES | freeze / Owner truth |

**STATE_NOT_REACHED_TOTAL = 6**  
**STATE_NOT_REACHED_WITH_EXPLICIT_BLOCKER = 6**

## Reached in gap closure (removed from SNR)

| State | Result |
|-------|--------|
| `/operator` true bottom | FINITE_STATIC; height 75277 stable |
| `/tablet/:stationId` | **REACHABLE** — `/tablet/print` live queue + active `ORD-92400` |
| MachineRun **list** | REACHABLE empty (`GET` 200, count 0) |
| Execution 973024 | already reached in initial Wave 3 |
| Employee-app-v2 **observe** | already reached; **start** remains SNR |

## MachineRun gap (explicit)

```text
MACHINERUN_DETAIL_RUNTIME_REACHED = NO
STATE_NOT_REACHED
BLOCKER = no existing safe MachineRun
MUTATION_REQUIRED = YES
WHY_NOT_FORCED = freeze / Owner truth
MACHINERUN_GAP_RESOLVED = YES
```

Boundary proven without a live detail: list copy (run ≠ task/session), `frontend/src/api/machineRuns.ts`, backend resource-state API, and `backend/tests/test_*machine_run*`.

## Tablet drill

**TABLET_DRILL = REACHABLE**

`/tablet/print` is implemented (`TabletStationQueue`). Live: 1 active (T06 Claim Probe / ORD-92400 / Putaru), queue rows present. Start was **not** pressed.

## Employee / mobile start

```text
EMPLOYEE_APP_ACTION_SURFACE = SPECIALIZED
MOBILE_START_NOT_EXECUTED = YES
MUTATION_REQUIRED = YES
BOUNDARY_PROVEN = YES
```

Proof: `EmployeeMobileV2WorkRoomActionBar` → `startTask` / `startMobileHelperSession`. Observe shot from initial Wave 3 remains sufficient.

# Wave 5 — machine catalog vs execution

| Concern | `/utilaje` |
|---------|------------|
| MACHINE CATALOG | owned (GET /machines) |
| CAPABILITY / WORKCENTER | projected from metadata |
| CAPACITY | diagnostic IMPLEMENTED_INACTIVE |
| RATE | not owned → Pricing / CostEngine |
| EXECUTION / MachineRun | not owned; `currentJobId` null in mapper |

**MACHINE_CATALOG_EXECUTION_BOUNDARY = CLEAR** in code/honesty; **PARTIAL** in UI if util% is read as live occupancy.

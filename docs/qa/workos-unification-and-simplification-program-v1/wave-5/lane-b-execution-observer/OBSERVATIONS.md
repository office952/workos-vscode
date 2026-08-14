# Lane B — execution observer (Wave 5)

HR does **not** own working/session/task complete.

| Concept | Execution (Wave 3) | HR (Wave 5) |
|---------|-------------------|-------------|
| eligible / assignable | operator assignment | `is_assignable` + registry authorizations on `/employees` |
| assigned | task employee_id | not shown as live work |
| working / session | Atelier / operator / MachineRun | **absent** |
| attendance | N/A | pontaj exceptions |
| labor actual | reality observed minutes | CostEngine fields on employee (planned cost, not actuals) |

**ASSIGNMENT_WORKING_SEPARATION = CLEAR** across HR vs Execution (HR does not claim “working”).  
Utilaje catalog does **not** show MachineRun occupancy (`currentJobId: null` in mapper). Boundary **CLEAR** if user reads honesty; **PARTIAL** if they treat util% as live execution.

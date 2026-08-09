# Dead pieces / parallel authorities

| Piece | Classification |
|-------|----------------|
| RoleSkillLaborCostPolicy + ActualLaborCostLine | CANONICAL / SNAPSHOT_SAFE |
| Session role/skill at START | CANONICAL_SNAPSHOT |
| Live employee.role at finalize (legacy fallback) | LIVE_UNSAFE if used for new work; unused when snapshot present |
| employee salary / cost_lunar_firma | LIVE_UNSAFE for job actual labor cost |
| Workcenter labor rates | LEGACY |
| Pricing-linked labor time | LEGACY / commercial boundary |
| ProfitabilityAnalysis hr_labor_cost_missing | ACTIVE_PARTIAL consumer (does not freeze) |

No broad cleanup.

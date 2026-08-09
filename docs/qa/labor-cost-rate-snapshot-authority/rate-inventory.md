# Rate / cost source inventory

| Source | Scope | Mutable? | Historical? | Used by | Classification |
|--------|-------|----------|-------------|---------|----------------|
| `RoleSkillLaborCostPolicy` | role + optional skill, dated | new rows / hostile DB edit | effective_from/to | finalize match | CANONICAL_CURRENT |
| Session `role_code`/`skill_code` | work-time inputs | immutable after START | yes (JSON SoT) | finalize | CANONICAL_SNAPSHOT |
| `ActualLaborCostLine` | frozen money line | insert-once | frozen value | Profitability RM | CANONICAL_SNAPSHOT |
| `employee.role` live | HR role | yes | no | legacy finalize fallback only | UNSAFE_LIVE_RATE (post-snapshot path unused) |
| `cost_lunar_firma` / pay | payroll/CostEngine | yes | n/a | CostEngine / payments | UNSAFE_LIVE_RATE for job actuals |
| Workcenter rates | shop rate | yes | n/a | not used by actual-cost runtime | LEGACY / wrong layer |
| Commercial labor / CPP | client price | yes | commercial snapshot | pricing | LEGACY for internal actual |
| ProfitabilityAnalysis MVP | minutes only money warn | — | — | analysis | ACTIVE_PARTIAL (no HR money) |
| F7I owner rate activation branch context | commercial | — | — | out of this GO | FUTURE / separate |

**Do not invent** employee-specific hourly job rate. Canonical model is role/skill standard internal rate.

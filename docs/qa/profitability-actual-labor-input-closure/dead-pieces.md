# Dead pieces / parallel authorities

| Piece | Classification | Action |
|-------|----------------|--------|
| `build_profitability_actual_labor_input` | CANONICAL | Keep |
| `build_execution_actuals_read_model` | DERIVED (task-level) | Keep; not a second writable authority |
| `ExecutionReality.total_actual_time_minutes` | DERIVED from sessions by reality service | Keep; Profitability prefers session helper |
| `ActualLaborCostLine` | SEPARATE monetary freeze | Not labor-time SoT |
| Operator UI `actual_minutes` | DERIVED display | Audit only; no redesign |
| Dashboard WC actual minutes | LEGACY observability | No broad clean |
| ProfitabilityAnalysis `actual_labor_minutes` from reality total | ACTIVE_PARTIAL consumer | May later prefer labor_input helper |
| Attendance / payroll hours | SEPARATE_TRUTH | Do not merge |
| Speculative profitability UI prototypes in docs | FUTURE / docs | No UI built this GO |

No broad cleanup performed (not required for safety).

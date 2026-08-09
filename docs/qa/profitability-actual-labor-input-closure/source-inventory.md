# Source inventory — profitability / labor actuals

| Item | Location | Classification |
|------|----------|----------------|
| Controlled session writer | `controlled_task_session_service.py` | ACTIVE_CANONICAL |
| Session SoT | `execution_reality.tasks_json` | ACTIVE_CANONICAL |
| ExecutionActuals RM | `build_execution_actuals_read_model` | ACTIVE_PARTIAL (task totals; no full session list) |
| **Labor input helper** | `profitability_actual_labor_input_service.py` | ACTIVE_CANONICAL (this closure) |
| Profitability Actual RM | `profitability_actual_read_model_service.py` | ACTIVE_PARTIAL (embeds labor_input; money fail-closed) |
| ProfitabilityAnalysis MVP | `profitability_analysis_service.py` | ACTIVE_PARTIAL (uses reality total minutes; margin null) |
| PostJobTruth schemas | `schemas/post_job_truth.py` | READ_ONLY_PROJECTION |
| Actual labor cost lines | `ActualLaborCostLine` + runtime freeze | ACTIVE_PARTIAL (monetary freeze; not labor-time SoT) |
| RoleSkillLaborCostPolicy | `actual_cost_policy_*` | CANDIDATE rate authority |
| Operator `actual_minutes` display | `operator_tasks.py` | DERIVED display from session timestamps |
| Dashboard WC actual minutes | `dashboard_stats.py` | LEGACY / observability aggregate |
| Commercial `actual_minutes` on quote | commercial pricing isolation tests | READ_ONLY / commercial-isolated |
| Profitability dashboard UI | — | FUTURE / not built |
| HR attendance hours | employee request attendance | SEPARATE_TRUTH (not job labor) |
| MachineRun runtime | machine_run models/services | SEPARATE_TRUTH |

**Do not assume** a complete Profitability system exists because names appear in docs.
Monetary Profitability remains NOT_AUTHORIZED.

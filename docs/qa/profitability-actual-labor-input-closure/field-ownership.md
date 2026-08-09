# Field ownership matrix

| Field | SOURCE | OWNER | STORED_OR_DERIVED | CANONICALITY |
|-------|--------|-------|-------------------|--------------|
| order_id | Orders / plan | Orders | stored | CANONICAL |
| execution_plan_id | ExecutionPlan | ExecutionPlan | stored | CANONICAL |
| task_id | operational_tasks + session | ExecutionPlan V2 | stored | CANONICAL |
| employee_id | session | controlled writer | stored | CANONICAL |
| session_id | session | controlled writer | stored | CANONICAL |
| started_at | server clock | controlled writer | stored | CANONICAL |
| ended_at | server clock | controlled writer | stored | CANONICAL |
| duration_minutes | ended−started | session SoT | stored | CANONICAL |
| actual_duration_seconds | ended−started | labor input helper | derived | CANONICAL precision |
| workcenter | operational task | plan | projected | FACTUAL if present |
| planned_minutes | estimated_time_minutes | plan | projected | PLANNED only |
| status / role / source | session | writer | stored | FACTUAL |
| salary / rate / money | — | — | — | OUT OF SCOPE |

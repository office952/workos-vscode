# Fallback audit

| Pattern | In F5 call path? | Fabricates actual? | Verdict |
|---------|-----------------:|-------------------:|---------|
| workcenter.rate_per_hour | No | — | clean |
| machine_rate_ron_per_hour | No | — | clean |
| commercial_price as material cost | No | — | clean |
| planned_minutes as actual cost | No (availability only) | No | clean |
| missing → 0 | No | No | clean |
| PostJobTruth inventory unit_cost partial | Separate read model | Explicit non-final | PREEXISTING_UNRELATED |

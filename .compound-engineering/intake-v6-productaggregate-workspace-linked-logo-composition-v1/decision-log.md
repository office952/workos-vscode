# Decision log — ProductAggregate workspace linked logo composition v1

| ID | Decision | Status | Notes |
|---|---|---|---|
| DEC-PA-01 | Two segment instances (namespaced component_id) | **OWNER GO — two instances** | `comp_*::{segment_key}` |
| DEC-PA-02 | Partial aggregate when finish missing | **OWNER GO — partial structure + warnings** | No fabricated qty |
| DEC-PA-03 | Task rule merge owner = composition service | **DEFAULT ACCEPTED** | Override if owner prefers deferral |
| DEC-PA-04 | Optional workspace_id on existing aggregate GET | **DEFAULT ACCEPTED** | Backward compatible |
| DEC-PA-05 | Aggregate preview allowed without Step 3 final confirm | **DEFAULT ACCEPTED** | Handoff blocked separately |

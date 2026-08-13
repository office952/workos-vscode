# LOGICAL_LIST_RESPONSE_PARITY

```text
BACKEND_LOGICAL_LIST_CONTRACT_CHANGED = NO
BACKEND_LOGICAL_LIST_NESTED_PQ_CHANGED = NO
```

Backend `get_gradi_logical_list_read_model` still calls:

1. `get_material_breakdown_for_workspace`
2. `build_intake_v6_priced_quote_dry_run`

No product changes under `backend/services/gradi_logical_list_read_model_service.py`.

D2 only changes **when** the frontend requests the existing endpoint. Response shape and nested computation unchanged.

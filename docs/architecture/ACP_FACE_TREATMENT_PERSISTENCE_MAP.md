# ACP Face Treatment Persistence Map

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Storage | FinishSetup JSON (`svg_component_bindings`) — no DB migration |

## Flow

```text
Operator / API payload
→ normalize_svg_component_bindings (stable binding_id + local_zone_id)
→ validate_bindings_for_new_selection
→ sync_support_selection_from_bindings (SUPPORT_CONTOUR only)
→ dump FinishSetup
→ ProductDefinition: svg_component_instances + face_treatment_instances
→ face_treatment_readiness summary
```

## ProductDefinition

- Letter/logo instances remain separate.
- Shell-local treatments nest under ACM `SUPPORT_CONTOUR` instance as `face_treatment_instances[]`.
- Top-level `face_treatment_instances` + `face_treatment_readiness` for inspection.

## Readiness (V1)

| State | When |
|-------|------|
| `NOT_APPLICABLE` | Legacy binding without treatment |
| `INACTIVE` | Inactive local treatment — **zero warnings** |
| `LOCAL_CONFIGURATION_REQUIRED` | Routed/insert confirmed; module not configured |
| `READY_FOR_AGGREGATION` | Confirmed treatment without required local module |

## Aggregate boundary

No plexiglas/LED/BOM/task_rules projection in this foundation.

## ProductAggregate

Unchanged for process/BOM — identity/readiness available via PD values only.

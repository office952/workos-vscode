# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Risk Register

**Phase:** PLAN  
**Accepted HEAD:** bcdd14d

| Risk | Probability | Impact | Mitigation | Test |
|---|---:|---:|---|---|
| EIC still template-only aggregate/BOM | **HIGH** | **HIGH** | Delegate to `AggregateCostBomBuilderService` | Orchestration tests 1–3 |
| Duplicate material cost (BOM + parallel PA) | MED | HIGH | Remove local `aggregate_svc.build` + adapter.build | No double-build spy |
| Logo materials filtered by letters active_modules | **HIGH** | HIGH | Linked-logo BOM row eligibility helper | Logo material tests |
| Partial treated as complete | MED | HIGH | Propagate BOM partial + no logo lines when finish missing | Partial tests 14–20 |
| Missing rate treated as zero | LOW | CRITICAL | Keep blocker semantics | Missing rate tests |
| Lost segment identity | MED | HIGH | Preserve `component_code=component_ref` | Provenance tests |
| Cost BOM bypassed | MED | HIGH | Single builder call | Integration test |
| Binding/recommendation re-read | LOW | HIGH | No new imports; code review | Source inspection test |
| Accidental CPP coupling | LOW | CRITICAL | No new imports; boundary tests | Boundary tests |
| Logo qty uses letter area (wrong) | **HIGH** | MED | DEC-EIC-03 segment quantity helper | Material qty tests |
| Logo operation cost expected but missing | MED | MED | Document DEC-EIC-04 debt | Explicit test that v1 is material-focused |
| Letters-only regression | MED | HIGH | Parity test vs template-only | Test 7 |
| API break | LOW | MED | workspace_id remains optional | Endpoint tests |
| Provenance lost | MED | MED | Pass workspace_id in input_summary + component_code | Provenance tests |

## Rollback

Revert EIC `build_preview` to direct adapter call + template aggregate. No migration. Endpoint unchanged.

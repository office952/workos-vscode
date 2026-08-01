# ACTIVE_VARIANT_RULE_MATRIX

| Rule | Mechanism | Proof |
|------|-----------|-------|
| Inactive module materials excluded | `filter_aggregate_by_active_scope` before qty apply | existing active-scope tests |
| FACE+CANT adhesive only when both sold | `composition_excluded_materials` | active_scope_resolver |
| Depth profile 30/60/80/100 exclusive | `formula_params.gate.return_depth_mm` match | contract unit test |
| Generic lateral suppressed when depth set | `_GENERIC_LATERAL_PROFILE_CODES` | contract unit test |
| Face Oracal vs print vs laminated exclusive | `_FACE_FINISH_COMPONENT_GATES` | contract unit test |
| Return finish Oracal/paint gated | `formula_params.gate.return_finish_type` | seed gates + filter |
| Same code + different provenance both emit | no code-only dedupe | contract unit test |
| Live template change after freeze | Order snapshot copy — no rebuild | convert service (unchanged) |
| No SVG/DWG for variant/qty | formulas use quote_input numbers only | formula_handlers policy |

## Acceptance

1. Inactive variant → not emitted  
2. Mutual exclusive finishes → one family  
3. Two components → same code OK if provenance differs  
4. Pre-freeze preview rebuilds from current truth  
5. Post-freeze snapshot immutable for historical orders (92401 preserved)

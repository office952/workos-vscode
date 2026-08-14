# Wave 4 — ProductDefinition ownership

Claimed: compose a coherent technical solution.  
Actual: **compiler / preview**, not a stored product.

| Question | Evidence |
|----------|----------|
| List modules or compose? | Compose **preview**: `ProductDefinitionBuilderService.build_preview()` — module state, composition graph, readiness |
| Compatibility / variants / required children | `product_definition_composition_contract.py` + mounting services |
| Persist? | **No** — preview only; Intake stores workspace; Order freezes snapshot |
| UI route | **None.** `/modules` verifyRoute = `/intake-v6` |
| Prices? | Explicitly does not |

**Dependency logic locations (actual):**
- Product System template JSON / mini-module registry
- ProductDefinition composition contract
- ProductAggregate explicit graph (workspace path)
- Intake V6 form contract + finish_setup
- Frontend honesty chips (display)
- Pricing layer (money, not structure)
- Execution mapping from **frozen** task_contract

**PRODUCT_DEFINITION_OWNERSHIP = PARTIAL** — compiles Letters slice; Logo/ACM out of slice; not a user-facing home.
